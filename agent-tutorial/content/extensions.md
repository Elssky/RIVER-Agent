## 扩展系统的三个层次

一个成熟扩展系统至少有三个层次：**说明层**告诉模型如何完成任务，**能力层**提供真实操作，**组装层**管理安装、配置、依赖和生命周期。它们对应 skill、工具/服务与插件，但名称在不同框架中可能变化。

例如 RIVER 的“航段冲突分析”扩展可以组合分析流程 skill、航道知识检索、交通观测查询和专业风险服务适配器。它也可以只有 skill：若宿主已提供领域工具，就不必重复实现。反过来，一个 MCP 服务可以只暴露数据或计算接口，不一定需要 skill。所有专业数值计算仍属于可单独验证的服务，不因此成为另一个 LLM Agent。

| 需要做的事 | 首选机制 | 判断标准 |
| --- | --- | --- |
| 规定交通分析顺序与证据核对步骤 | Skill | 缺的是流程知识 |
| 加一个航段观测或规则查询接口 | Tool / MCP tool | 缺的是可调用动作 |
| 监听运行事件、改上下文 | Extension / Hook | 缺的是运行时行为 |
| 替换文件系统或模型后端 | Service Provider | 缺的是接口实现 |
| 统一分发这些内容 | Plugin / Package | 缺的是装载与版本管理 |

## 写出一份有效的 SKILL.md

Agent Skills 规范以目录中的 `SKILL.md` 为基本单元，头部包含名称与描述，正文提供流程，其他文件按需访问。[Agent Skills 规范](https://agentskills.io/specification)。下面是原创教学技能：

```markdown
---
name: inland-traffic-analysis
description: 分析用户指定内河水域与时间窗的交通态势。用于调用已授权的观测、预测、风险和规则工具并核对证据；不用于控制船舶或发布约束性航行指令。
---

# 内河交通态势与冲突分析
1. 确认水域、观测时间、预测时域、输出要求与当前授权；歧义会改变结论时先澄清。
2. 查询可用观测和航道上下文，记录来源、观测时间、进入系统时间、覆盖与质量警告。
3. 按需将大型结果保存到受控 Result Store；后续工具使用 `result_ref`，不要转写高精度轨迹。
4. 只在工具可用且输入满足要求时调用轨迹、流量或冲突风险服务；保留服务版本、单位、有效期和不确定性。
5. 检索适用航行规则与通告，检查空间和时间有效性；无法确定时明确标记。
6. 对证据时间、来源、质量、权限和规则适用性做独立验证。缺证据时给有条件结论或停止，不补造数据。
7. 输出结论、关键证据引用、数据局限和待确认事项；任何航行安全建议均为岸基辅助信息。

工具字段应结合本教程“动手实现”篇中的领域工具契约示意，并在项目接口确定后更新。
```

描述负责**触发条件**，正文负责**执行方法**。不要写“这是一个非常强大的万能 skill”。写清用户意图、适用输入和不适用场景。正文不要堆满重复的安全口号，应该包含真正的操作顺序、决策点、错误处理和成功标准。

Skill 中的 `scripts/` 是工具辅助资源，不是自动执行入口；`references/` 适合放详细格式与领域知识；`assets/` 放模板与静态文件。所有相对引用从 skill 目录解析，文件缺失要有诊断，不应让模型随意猜另一条路径。

## 渐进加载：目录、正文、资源

<div class="diagram"><div class="flow"><div class="node">扫描<small>name / description / path</small></div><span class="arrow">→</span><div class="node">选择<small>用户指定或任务匹配</small></div><span class="arrow">→</span><div class="node">加载正文<small>SKILL.md + 版本</small></div><span class="arrow">→</span><div class="node">按需资源<small>reference / script / asset</small></div></div><p class="caption">加载粒度越细，越能避免把大量不相关内容放进模型请求。</p></div>

自建宿主的完整流程建议如下：扫描可信根目录 → 校验 frontmatter → 建立稳定 skill ID → 检查重名 → 生成短目录 → 记录选中原因 → 读取正文 → 标记资源基准路径 → 执行时仍走门禁。缓存以内容摘要和版本为键，而不是“曾经读过一次”就永远复用。

用户显式指定 skill 时通常应优先，但不能因此提升权限。自动选择时可以用规则、关键词、向量检索或模型路由；先从简洁目录与明确描述开始。使用一个错误的 skill 往往比没有 skill 更糟，因为它会把整个任务引向错误流程。

同一个任务命中两个 skill，要先检查是否互补。一个负责报告，一个负责事实核验通常能组合；两个互相冲突的输出格式要明确选择。可信开发者策略与用户约束优先级不应由 skill 自己决定。

## Skill 的兼容性与测试

“都支持 SKILL.md”不等于“执行结果相同”。不同宿主的扫描目录、显式调用语法、可用工具、脚本环境、frontmatter 扩展字段与资源读取方法各不相同。

| 适配维度 | 要检查什么 | 做法 |
| --- | --- | --- |
| 发现 | user/project 根目录、祖先查找、重名规则 | 宿主适配层生成明确目录 |
| 触发 | 自动选择与显式调用语法 | 提供调用示例，并测未触发场景 |
| 工具 | 读写、网络、shell 名字与能力 | 用领域动作描述，必要时映射工具 |
| 环境 | Python/Node、依赖、路径、操作系统 | 声明兼容性并做启动检查 |
| 权限 | 写入、执行、外部账号 | 在宿主策略中校验 |
| 产物 | 文件路径、格式、验证规则 | 按宿主资源接口返回 |

测试 skill 不只检查文件存在。至少包含：应该匹配、应该不匹配、用户显式调用、工具缺失、依赖缺失、权限拒绝、资源路径含空格、产物不合格。对比“开 skill”与“关 skill”的相同任务，才能判断技能是否改善结果。

## 自建插件契约

下面是**教学自定义 manifest**，不是 Codex、Pi 或 dsh 的安装格式。它表达宿主应管理的信息：

```json
{
  "id": "river-traffic-analysis",
  "version": "0.1.0",
  "hostApi": "^1.0",
  "entry": "./dist/plugin.js",
  "skills": ["./skills/research-report"],
  "requires": ["river.observations", "river.navigation_knowledge", "river.result_store"],
  "requestedCapabilities": ["observations.read", "predictions.read", "risk.assess", "knowledge.read"],
  "configSchema": "./config.schema.json"
}
```

`requestedCapabilities` 是请求声明，不是授权结果。宿主把安装者身份、来源、配置和权限合并后才决定是否装载。工具命名可以带插件前缀，或者注册唯一 ID 后再映射模型可见名；冲突必须报错，不能悄悄覆盖。

路径要限制在包根目录内，版本要锁定，依赖要防止循环，配置要校验，密钥用引用而非正文。资源接口最好可注入，让插件代码依赖 `Files`、`Search`、`Artifacts` 等稳定服务，而不是到处导入宿主内部对象。

## 生命周期与热重载

一个可靠装载器采用：解析 → 校验 → 解析依赖 → 挂载 → 注册能力 → 激活 → 运行 → 排空/取消 → 注销 → 清理。失败时回滚已经注册的部分。

```typescript
// 自建插件接口示意。
type Dispose = () => void | Promise<void>;
async function activate(host: Host): Promise<Dispose> {
  const removers: Dispose[] = [];
  try {
    removers.push(host.tools.register(reportTool));
    removers.push(host.skills.register(reportSkill));
    removers.push(host.events.on("turn.completed", audit));
  } catch (error) {
    for (const remove of removers.reverse()) await remove();
    throw error;
  }
  return async () => {
    for (const remove of removers.reverse()) await remove();
  };
}
```

卸载不仅要移除菜单。后台任务、监听器、计时器、网络连接与模型可见 schema 也必须清理。热重载时不应让已发出的调用突然绑定到新版本实现：可以让活跃调用保留旧实例，排空后切换；或者取消并明确返回失败。

持久会话保存插件版本与 schema 摘要。恢复发现版本不兼容时，应该迁移、保持旧环境或要求明确处理，而不是混用新实现与旧轨迹。插件状态迁移与会话历史迁移是不同的职责。

## 接入 MCP 的正确位置

MCP 客户端位于工具/资源适配层。它维护连接、协商能力、发现工具、将外部 schema 注册到宿主、调用服务并转换结果。模型不直接持有外部服务器连接或密钥。

<div class="diagram"><div class="flow"><div class="node">模型请求<small>一个可见工具</small></div><span class="arrow">→</span><div class="node">宿主注册表<small>校验 + 策略</small></div><span class="arrow">→</span><div class="node">MCP 客户端<small>协议与身份</small></div><span class="arrow">→</span><div class="node">外部服务<small>数据与动作</small></div></div><p class="caption">返回方向同样需要处理结构化结果、内容块、错误和超时。</p></div>

常见步骤是初始化与能力协商 → `tools/list` → 生成宿主工具描述 → `tools/call` → 规范化结果。工具目录可能分页、变化或失效；不要把第一次发现的列表当成永久真相。传输可采用 stdio 或规范定义的 HTTP 方式，具体认证流程依部署而定。[MCP 官方工具规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)。

MCP 工具的 annotations 是服务声明的提示，不应作为可信授权依据。外部工具说自己“只读”，宿主仍需核验服务来源和实际能力。`resources` 是可读取资料，`prompts` 是可选提示模板；客户端是否暴露它们给模型要分别设计。

工具结果中既有模型可读内容，也可能有结构化数据。你应保留程序用的数据，不要反向解析一句“创建成功，编号 123”。当服务不可用时，回传清晰错误；不要让模型重新编造数据。

## 把领域函数包装成 MCP 服务

配套的 [mcp_server.py](examples/mcp_server.py) 是一个可选服务示例，复用已有 Workspace 读取边界。它与默认标准库练习分开，需要安装 MCP Python SDK **v2**；这里没有安装或端到端验证该依赖。当前官方 v2 使用 `MCPServer`，旧 v1 示例使用的 `FastMCP` 不能直接当成相同 API。[官方 Python SDK](https://github.com/modelcontextprotocol/python-sdk)。

```python
from mcp.server import MCPServer
from agent import BASE, Workspace, check_args, object_schema

mcp = MCPServer("Workspace Research")
workspace = Workspace(BASE / "workspace", allow_write=False)

@mcp.tool()
def read_workspace_note(path: str) -> dict:
    """Read bounded text from the fixed teaching workspace."""
    check_args(object_schema(path=True), {"path": path})
    return workspace.read({"path": path})

if __name__ == "__main__":
    mcp.run()  # v2 默认 stdio；不能向 stdout 输出调试文字。
```

在自己的虚拟环境中选择 `mcp>=2,<3`，再让宿主以 Python 子进程启动该文件。它启动后等待协议输入，不是交互终端程序；没有输出不代表挂死。宿主会发现 `read_workspace_note`，参数类型从函数签名生成，但业务路径限制仍由实现负责。[官方运行说明](https://py.sdk.modelcontextprotocol.io/run/)。

验证顺序：工具发现 → 读取 notes.md → 越界拒绝 → 结果截断 → 断开清理。先用 MCP Inspector 或对应版本客户端测试，再连接 Codex 等宿主。Pi 的进程内工具与 dsh 的工具 DSL 可以复用相同领域读取逻辑，但各自的注册与结果映射仍要单独实现。

## 权限与隔离：插件不能自行授权

进程内 extension 最容易开发，但它拥有宿主进程的权限。工具调用门禁只约束通过门禁的调用；无法约束插件在初始化时直接读文件、请求网络或偷取凭据。因此需要区分**可信代码扩展**与**受限能力服务**。

可信插件可以进程内运行；第三方或高风险能力优先进程外，通过窄接口访问沙箱服务。不同租户与工作区应隔离凭据与状态。密钥最好由外部服务在自己的边界内使用，只向模型返回必要结果。

策略应该在所有入口一致执行：模型 tool call、用户命令、插件内二次调用、程序化工具调用与恢复重试。如果某个旁路直接访问能力服务，必须同样有权限检查；不要把它当成“内部调用所以默认可信”。

## 为三个框架写适配器

先把“报告生成与证据验证”写成不依赖宿主的领域函数。然后分别包装：Codex 可通过 MCP 暴露工具并配置 skill；Pi 用 `registerTool` / extension 注册；dsh 用 Cordis `apply`、服务注入与 `ctx.tools.register`。

| 公共领域逻辑 | Codex 适配 | Pi 适配 | dsh 适配 |
| --- | --- | --- | --- |
| 查询资料 | MCP 服务中的工具 | Extension tool | Cordis tool consumer |
| 报告流程 | Skill | Skill + `/skill:name` | Skill registry/provider + 加载工具 |
| 执行授权 | 宿主权限/MCP 服务授权 | 自定义门禁与外部沙箱 | 策略事件、guard、能力后端 |
| 运行事件 | SDK/App Server 事件消费 | `subscribe` / `pi.on` | `session/event` / `agent/*` |
| 包装分发 | 按当前插件文档 | Pi package | profile / bundle / plugin |

这张表是适配建议，不承诺接口完全一致。后面各项目篇章给出当前源码的具体入口。OpenAI 插件包装规范正在演进，应以安装目标版本的官方文档与 schema 为准；不要把这里的自定义 manifest 复制过去。[OpenAI 插件包装文档](https://developers.openai.com/plugins/build/plugins)。

## 一个完整插件的验收清单

验证装载、重名、依赖缺失、注销、取消、配置错误、权限拒绝、并行调用、恢复与版本变化。工具和 skill 应共同测试：skill 是否选择了正确工具？工具结果是否足够支持它的验收？卸载后是否仍会被模型看到？

用“先挂载一次、调用一次、卸载一次、再调用一次”的契约测试最容易发现残留。最后一次应该明确不可用，而不是继续调用缓存中的旧对象。增加进程外服务时，再验证连接断开、重连、目录变化与账号切换。

<details><summary>练习：给 agent 增加 GitHub 项目调查能力，Skill 应该负责认证吗？</summary><p>认证由宿主或服务管理。Skill 描述调查顺序、检索策略、来源记录和失败处理。实际 GitHub 工具只接受受控的查询参数，并使用已授权身份。Skill 不读取 token，也不告诉模型如何绕过审批。</p></details>
