## 你将做出的程序

这一篇把前面的架构缩成可以跑起来的 Python 程序。配套目录 [examples/](examples/) 包含 `agent.py`、一份练习资料、一个报告 skill 和一个明确选择后才加载的示例插件。程序只依赖 Python 标准库，建议 Python 3.10 或以上；默认使用确定性的模拟模型，**不会请求网络，也不需要密钥**。

它演示工具请求 → 校验 → 范围检查 → 执行 → 反馈，以及重复调用检测和 JSONL 轨迹。它不是生产沙箱、完整 MCP 客户端或完整 YAML skill 解析器。模拟模型采用预设步骤，适合理解运行机制；真实模型的调查策略并不是预先写死的。目录中的 `mcp_server.py` 属于下一篇的可选示例，需要额外 MCP SDK，不参与默认练习。

```text
examples/
  agent.py                 # 模拟 / 兼容 Chat Completions 的模型适配
  workspace/notes.md       # 一份练习资料
  skills/research-report/SKILL.md
  plugins/greeting.py      # 示例能力；仅显式参数启用
  test_agent.py            # 边界、错误与轨迹验证
```

进入 `examples` 目录后运行：

```powershell
python agent.py --mock
python agent.py --mock --allow-write
python agent.py --mock --plugin greeting
python -m unittest -v test_agent.py
```

第一条会执行加载 skill、读取资料、提出写报告请求；写入被拒绝后，模拟模型解释拒绝并停止，运行状态为 `needs_input`。第二条显式授权写入固定的 `workspace/output/report.md`，随后读取产物进行验证，最终状态为 `completed`。不传 `--allow-write` 不会创建报告，但宿主程序仍会写自己的运行日志。

## 先约定消息与工具结果

为了方便学习，练习使用兼容 Chat Completions 的消息结构：`system` 表示开发者设定的约束，`user` 表示本次任务，`assistant` 可以包含 `tool_calls`，`tool` 通过 `tool_call_id` 返回结果。这只是一个协议适配，不是所有模型的通用格式。

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [{
    "id": "call_01",
    "type": "function",
    "function": {
      "name": "read_note",
      "arguments": "{\"path\":\"notes.md\"}"
    }
  }]
}
```

注意 `arguments` 在这个协议里是 JSON **字符串**。循环先保存 assistant 消息，再解析并执行所有调用，最后保存与 ID 对应的 tool 消息。遗漏 assistant 工具请求、结果 ID 不匹配或多个请求只返回一个结果，都可能让提供方拒绝后续上下文。

成功和错误都应该规范化，例如：

```json
{"ok":true,"data":{"path":"notes.md","text":"...","truncated":false}}
{"ok":false,"error":{"code":"permission_denied","message":"write not authorized"}}
```

`permission_denied` 不是模型传入的参数错误。模型可以换成被授权的动作，但不能靠重试绕过权限。保留错误分类，模型才能采取正确的下一步。

## 实现有停止权的循环

下面是提炼后的逻辑示意；完整可运行代码在 [agent.py](examples/agent.py)。

```python
for step in range(max_steps):
    reply = provider.generate(messages, registry.schemas())
    # 必须先确认响应完整，不能执行被截断的工具 JSON。
    validate_reply(reply)
    messages.append(reply.message)
    if not reply.calls:
        return verify_or_report_incomplete(reply)
    for call in reply.calls:
        result = dispatch_with_policy(call)
        messages.append(tool_result(call.id, result))
    save_checkpoint(messages, step)
return result(status="budget_exhausted")
```

生产实现通常把每一步拆成可测试的函数：`prepare_request`、`normalize_reply`、`validate_call`、`authorize`、`execute`、`persist`、`verify`。每个函数输入尽量不可变。这样你能通过模拟模型复现错误，无需每次都调用付费 API。

工具请求最多有多少个？一个工具多久必须返回？重复多少次算无进展？用户取消时处于哪个安全点？这些都是循环的职责。练习设置有限步骤、每批调用数、HTTP 超时和重复请求阈值；更精确的进程取消与总成本控制需要后续实现。

如果最终答案承认没有完成，应返回 `needs_input` 或失败状态。不要为了界面看起来顺利，就把所有运行都显示为绿色完成。

## 工具注册表与参数校验

注册表保存“名字 → schema、实现、策略属性”。装载插件时必须检测重名，卸载时必须明确撤销。模型可见 schema 来自同一份注册表，避免出现“能调用却没说明”或“说明了但实现不存在”。

```python
# 示例 schema；练习仅支持这一小部分 JSON Schema 约束。
READ_SCHEMA = {
    "type": "object",
    "properties": {"path": {"type": "string"}},
    "required": ["path"],
    "additionalProperties": False,
}
```

校验顺序应该是：工具存在 → JSON 解析成功 → 类型/必填字段/额外字段正确 → 业务约束 → 权限判定 → 执行。完整 JSON Schema 需要专门的验证库；不要把练习中的轻量检查器当成完整实现。

### 映射到 RIVER-Agent 的工具契约

RIVER 的工具不应把 AIS 明细直接复制进对话，也不应让 LLM 自己计算碰撞风险。一个领域查询工具可返回观测摘要、质量和时间元数据；高容量轨迹或预测结果进入 Result Store，以受控引用供后续专业服务消费。以下是用于讨论契约的伪结构，字段不是已定 API：

```json
{
  "tool": "query_traffic_observations",
  "input": {"area_id": "section-42", "observed_from": "...", "observed_to": "..."},
  "output": {
    "result_ref": "result://...",
    "source": ["ais-feed-a"],
    "observed_at": "...",
    "available_at": "...",
    "quality": {"coverage": "...", "warnings": []}
  }
}
```

下游的轨迹预测或风险评估工具应接收 `result_ref` 和明确预测时域，并回传算法/数据版本、适用范围、有效期、单位与不确定性。验证器检查来源、时效、单位、区域与规则版本；模型负责解释，不负责替代确定性检查。工具实际可用情况、schema 和 dsh `ToolDefinition` 接口都要在选定版本与数据接通后核实。

练习的文件工具将相对路径解析到工作区，拒绝绝对路径、越界路径和过大的非文本文件。输出只能写固定目录中的固定报告文件。这些检查降低误操作，但**不是能抵御恶意并发进程的沙箱**：路径校验后资源仍可能被其他进程替换，实际权限依然属于 Python 进程。生产环境要用隔离文件系统、句柄级访问与操作系统权限补强。

报告写入时计算内容摘要，相同内容可重复确认，不同内容替换使用临时文件与原子发布思路。独立验证检查输出确实存在、位于允许位置、含必需标题与来源。语义真实性仍需更严格的引用和事实核对。

## 真正接入大模型

练习的 `ChatProvider` 通过 HTTP POST 请求 `{AGENT_BASE_URL}/chat/completions`，请求中包含模型、messages 和 tools。它用于提供**该协议且支持工具调用**的服务。使用前核对服务官方说明、账号权限、模型能力和数据处理范围。

```powershell
# 在你自己的终端配置；不要把真实密钥写入教程文件。
$env:AGENT_BASE_URL = "https://api.deepseek.com"
$env:AGENT_MODEL = "<账户支持且具有工具调用能力的模型 ID>"
$env:AGENT_API_KEY = "<你的 API 密钥>"
python agent.py --live --allow-write
```

以上运行会将练习资料与已加载 skill 发给所选提供方。`--live` 不会自动读取环境中的密钥并代替你选择模型：三个变量都必须明确配置。练习支持 HTTPS 服务以及本机 HTTP 推理服务，密钥不会写入请求日志。它没有 OAuth 登录流程，也没有完整的 Responses 适配。

如果使用 OpenAI 支持的 Chat Completions 模型，可将 base URL 设为 `https://api.openai.com/v1`；如果实现 Responses 接口，则应单独映射输入项、函数调用输出和续接状态，不能只改 URL。[OpenAI 函数调用说明](https://developers.openai.com/api/docs/guides/function-calling)。

DeepSeek 的工具调用文档说明了请求和工具结果的回传流程；部分推理模式还要求保留原生推理字段。练习保留响应中的 `reasoning_content`，但不同版本或其他提供方仍需单独验证。[DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)。不要默认所有兼容服务对 strict schema、并行工具与推理字段都采用相同语义。

## 流式接口应该怎么做

练习采用非流式响应，方便你先把闭环做对。引入流式后，要将展示与提交分开：文字 delta 可以立即发给 UI；工具参数 delta 要按调用 ID 或块索引收集；到完整调用边界再解析和校验。不要执行半截参数。

<div class="diagram"><div class="flow"><div class="node">SSE / SDK 流<small>原始提供方事件</small></div><span class="arrow">→</span><div class="node">适配器<small>归一化与累积</small></div><span class="arrow">→</span><div class="node">完整消息<small>校验后提交</small></div><span class="arrow">→</span><div class="node">工具执行<small>门禁和结果</small></div></div><p class="caption">UI 可观察临时 delta，但会话历史使用已完成消息；流断开应记录 attempt，而不是伪造成功。</p></div>

流可能在结尾才给 usage。结束事件收到后要判断是正常结束、工具请求、长度上限、取消还是错误。最终 usage 与完成消息应有明确顺序。使用厂商 SDK 可以减少解析工作，但仍需要验证你的适配器对工具与取消的处理。

取消信号应该传到模型传输、工具执行与长任务。UI 点了“停止”只改变按钮颜色不是取消；执行器必须实际停止等待或终止子进程，并记录哪些副作用已经发生。

## Skill 怎样接进这个小程序

练习启动时只把 `research-report` 的名称与描述放入系统提示，模型通过 `load_skill(name)` 获得全文。工具返回正文和资源根目录，之后模型按照其中的报告流程进行操作。模拟模式也显式走这一步，便于检查轨迹。

`SKILL.md` 的 frontmatter 只接受练习支持的简单 `name:` 和 `description:` 行，完整的规范字段、YAML 多行字符串、目录发现和冲突诊断属于下一阶段。加载正文只增加上下文，绝不改变 `--allow-write`。

自建路由可以先做确定性选择：用户明确指定优先；其次按任务标签筛选；必要时让模型从少量候选里选择。每次记录技能名、正文摘要和版本。没有读取全文之前，不要让模型仅凭描述猜测详细操作。

## 插件怎样接进这个小程序

使用 `--plugin greeting` 会装载随教程附带的 `greeting.py`，调用它的 `register(registry)`，得到一个 `greet` 工具与 disposer。结束时撤销注册。练习只允许该固定插件，不从用户消息导入任意模块。

```python
# plugins/greeting.py 的职责：注册，然后返回清理函数。
def register(registry):
    return registry.register(
        "greet", "Return a local greeting.",
        {"type": "object", "properties": {"name": {"type": "string"}},
         "required": ["name"], "additionalProperties": False},
        lambda args: {"greeting": "Hello, " + args["name"]},
    )
```

这展示生命周期，尚不提供依赖解析、热重载、签名或进程隔离。插件的 Python 代码与宿主权限相同；注册表的工具授权不能阻止插件代码在导入时任意访问文件。生产插件系统需决定哪些代码可信、哪些能力必须进程外运行。

## 会话日志、检查点与恢复

练习每次运行新建 `runs/<run_id>/events.jsonl` 和 `checkpoint.json`，记录步骤、调用、结果与完整消息历史。日志用于学习和排查，可能包含文件正文，所以只能放在合适的目录。没有密钥不等于日志没有敏感内容。

这里没有自动恢复命令。你会看到保存检查点是恢复的前提，但还需要：校验日志版本与完整性、重建消息、核对工具/skill 版本、重新取得授权、处理“动作已发生但结果未落盘”。直接继续最后一个工具调用可能重复副作用。

一个实用的写操作恢复设计是：执行前保存 `intent` 和唯一 operation ID；执行后保存 `receipt`；恢复遇到只有 intent 时，查询目标状态或要求用户确认。支持幂等键的外部服务最好复用同一 operation ID；不支持时要接受无法自动判定的状态。

## 练习的验证范围与下一步

| 验证 | 要证明的行为 | 不代表什么 |
| --- | --- | --- |
| 模拟成功流程 | Skill、读、写、验收、轨迹可连起来 | 不代表真实模型同样成功 |
| 未授权写入 | 报告工具被拒绝，不能声称完成 | 不代表进程本身被沙箱化 |
| 越界路径 | 工具拒绝工作区外路径 | 不代表免疫并发替换攻击 |
| 坏参数与未知工具 | 错误进入规范结果，循环可观察 | 不代表完整 schema 支持 |
| 插件注销 | 注册可以撤销，重名不能覆盖 | 不代表外部插件安全 |
| 重复请求 / 步骤预算 | 无进展和无限循环可被截停 | 不代表完整费用预算 |

接下来把模拟调用替换成真实模型，对同一组用例观察差异；加入有来源的引用校验；然后再考虑流式、恢复与 MCP。网页不会帮你悄悄调用付费服务。你可以阅读全部代码后，在自己的终端启用 `--live`。

<details><summary>练习：让 read_note 支持 offset 和 limit，需要改哪些地方？</summary><p>修改同一份工具 schema 和实现；检查 offset/limit 为正整数并设上限；输出起始行、总行数与截断标志；更新 mock 和验收用例。不要只给提示词加一句“读取少一点”。</p></details>
