import json
from pathlib import Path
import tempfile
import unittest
from agent import (AgentError, BASE, Registry, Workspace, Skills, MockProvider,
                   Recorder, call, make_registry, run)


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.work = self.root / "work"
        self.work.mkdir()
        (self.work / "notes.md").write_text("A bounded loop with explicit permissions.", encoding="utf-8")
        self.skills = Skills(BASE / "skills")

    def tearDown(self):
        self.temp.cleanup()

    def execute(self, allow=True, provider=None, max_steps=10):
        ws = Workspace(self.work, allow)
        rec = Recorder(self.root / "runs")
        result = run(provider or MockProvider(), make_registry(ws, self.skills), ws, self.skills, rec, max_steps)
        events = [json.loads(x) for x in (rec.path / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        return result, events

    def test_completed_run_and_receipts(self):
        result, events = self.execute()
        self.assertEqual(result["status"], "completed")
        self.assertTrue((self.work / "output/report.md").is_file())
        intents = [e["callId"] for e in events if e["kind"] == "tool_intent"]
        results = [e["callId"] for e in events if e["kind"] == "tool_result"]
        self.assertEqual(intents, results)
        self.assertEqual(len(intents), 4)
        checkpoint = json.loads((Path(result["log"]) / "checkpoint.json").read_text(encoding="utf-8"))
        self.assertEqual(checkpoint["messages"][-1]["role"], "assistant")

    def test_write_denied_never_completed(self):
        result, events = self.execute(allow=False)
        self.assertEqual(result["status"], "needs_input")
        self.assertFalse((self.work / "output/report.md").exists())
        self.assertTrue(any(e.get("result", {}).get("error", {}).get("code") == "permission_denied" for e in events))

    def test_arguments_and_unknown_tool(self):
        registry = make_registry(Workspace(self.work), self.skills)
        for name, args, code in [("read_note", "{", "invalid_arguments"),
                                 ("read_note", '{"path":3}', "invalid_arguments"),
                                 ("read_note", '{"path":"notes.md","extra":1}', "invalid_arguments"),
                                 ("missing", "{}", "unknown_tool")]:
            with self.subTest(name=name, args=args):
                self.assertEqual(registry.dispatch(name, args)["error"]["code"], code)

    def test_outside_path(self):
        registry = make_registry(Workspace(self.work), self.skills)
        result = registry.dispatch("read_note", json.dumps({"path": "../secret.md"}))
        self.assertEqual(result["error"]["code"], "path_denied")
        result = registry.dispatch("read_note", json.dumps({"path": str(self.root / "secret.md")}))
        self.assertEqual(result["error"]["code"], "path_denied")

    def test_large_read_is_explicitly_truncated(self):
        (self.work / "big.txt").write_text("a" * 40000)
        result = Workspace(self.work).read({"path": "big.txt"})
        self.assertTrue(result["truncated"])
        self.assertLessEqual(len(result["text"]), 32768)

    def test_plugin_lifetime_and_duplicate_registration(self):
        from plugins.greeting import register
        registry = Registry()
        dispose = register(registry)
        self.assertTrue(registry.dispatch("greet", '{"name":"Ada"}')["ok"])
        with self.assertRaises(AgentError):
            register(registry)
        dispose()
        dispose()
        self.assertEqual(registry.dispatch("greet", '{"name":"Ada"}')["error"]["code"], "unknown_tool")

    def test_repeated_calls_stop(self):
        class Repeater:
            def __init__(self): self.n = 0
            def generate(self, *_):
                self.n += 1
                return {"message": {"role": "assistant", "tool_calls": [call("read_note", {"path":"notes.md"}, self.n)]}, "finish":"tool_calls"}
        result, _ = self.execute(provider=Repeater())
        self.assertEqual(result["error"], "no_progress")

    def test_budget_is_a_distinct_state(self):
        result, _ = self.execute(max_steps=1)
        self.assertEqual(result["status"], "budget_exhausted")

    def test_incomplete_response_does_not_execute(self):
        class Truncated:
            def generate(self, *_):
                return {"message":{"role":"assistant", "tool_calls":[call("write_report", {"text":"bad"}, 1)]}, "finish":"length"}
        result, events = self.execute(provider=Truncated())
        self.assertEqual(result["error"], "incomplete_response")
        self.assertFalse(any(e["kind"] == "tool_intent" for e in events))

    def test_cancellation_is_recorded(self):
        class Cancelled:
            def generate(self, *_): raise KeyboardInterrupt
        result, events = self.execute(provider=Cancelled())
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(events[-1]["status"], "cancelled")

    def test_duplicate_batch_ids_are_rejected_before_execution(self):
        class BadBatch:
            def generate(self, *_):
                c = call("write_report", {"text":"bad"}, 1)
                return {"message":{"role":"assistant", "tool_calls":[c,c]}, "finish":"tool_calls"}
        result, events = self.execute(provider=BadBatch())
        self.assertEqual(result["error"], "provider_protocol_error")
        self.assertFalse(any(e["kind"] == "tool_intent" for e in events))

if __name__ == "__main__":
    unittest.main()
