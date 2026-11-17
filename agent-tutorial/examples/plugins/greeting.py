"""Trusted bundled example, loaded ONLY with --plugin greeting."""
def register(registry):
    return registry.register(
        "greet", "Return a local greeting without files or network.",
        {"type": "object", "properties": {"name": {"type": "string"}},
         "required": ["name"], "additionalProperties": False},
        lambda args: {"greeting": "Hello, " + args["name"]},
    )
