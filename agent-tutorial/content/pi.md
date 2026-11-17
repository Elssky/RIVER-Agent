## 定位：把模型、循环与应用拆开

[earendil-works/pi](https://github.com/earendil-works/pi) 把统一模型 API、agent runtime 与编码 CLI 分成多个包。它适合学习如何把小而明确的边界组合成可嵌入 agent，也适合用 TypeScript extension 扩展运行行为。

本次源码中的 npm 包使用 `@earendil-works/*`，不要盲目沿用旧文章中的其他命名空间。当前 coding-agent 包版本文件为 `0.87.1`；这是本次抓取观察，不保证未来安装得到相同版本。建议按你选定的 release/commit 锁定依赖。[package.json](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/package.json)。

## 分层架构与源码地图

<div class="diagram"><div class="layers"><div class="layer"><b>pi-coding-agent</b><small>CLI、会话、资源发现、Skill、Extension、交互</small></div><div class="layer"><b>pi-agent-core</b><small>Agent 状态、循环、队列、工具执行、事件</small></div><div class="layer"><b>pi-ai</b><small>提供方、模型目录、认证、流式协议、使用量</small></div><div class="layer"><b>其他支撑包</b><small>TUI、durable、telemetry、chord 等，按需要阅读</small></div></div><p class="caption">先理解前三层，再进入更复杂的持久化与组合运行时。</p></div>

| 路径 | 核心问题 |
| --- | --- |
| [`packages/ai/README.md`](https://github.com/earendil-works/pi/blob/main/packages/ai/README.md) | 多提供方怎样共用消息与流式接口？ |
| [`packages/agent/README.md`](https://github.com/earendil-works/pi/blob/main/packages/agent/README.md) | Agent 如何执行工具、管理队列和发布事件？ |
| [`coding-agent/docs/sdk.md`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/sdk.md) | 完整编码会话怎样嵌入 Node/Bun？ |
| [`docs/extensions.md`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md) | 可执行扩展怎样注册与清理？ |
| [`docs/skills.md`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md) | 技能如何发现与按需加载？ |
| [`docs/packages.md`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md) | 扩展与资源如何分发？ |
| [`src/core/session-manager.ts`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/session-manager.ts) | 轨迹树与活跃分支怎样决定上下文？ |
| [`src/core/extensions/types.ts`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/extensions/types.ts) | 精确事件与工具类型是什么？ |

## pi-ai：统一模型接口并保留差异

`pi-ai` 提供多提供方模型集合、认证解析、工具调用与事件流。当前 API 通过模型集合注册提供方，再取得模型并调用集合上的方法。旧代码里的全局函数写法可能已迁移。[pi-ai README](https://github.com/earendil-works/pi/blob/main/packages/ai/README.md)。

统一接口不意味着忽略提供方差异。能力、推理参数、图片、原生历史字段和认证仍要正确映射。自建时可以学习它如何将 transport 的事件转换为模型无关消息，以及如何记录 usage 与 stop reason。

选一个提供方，追踪请求构建 → stream 解析 → block/delta → 完整 assistant message，再观察工具参数校验。尤其要确认部分 JSON 不会提前执行、错误和取消有不同结束语义。为适配器编写固定流片段测试，比靠真实 API 随机验证更稳定。

## agent-core：状态、循环与消息转换

agent-core 在 pi-ai 之上维护状态与工具执行。它区分应用自己的 `AgentMessage` 和模型支持的消息：先通过 `transformContext` 筛选/注入，再通过 `convertToLlm` 转换。UI 专用消息不必全部进入模型上下文。[agent-core README](https://github.com/earendil-works/pi/blob/main/packages/agent/README.md)。

```text
AgentMessage[]
  → transformContext（剪枝或注入）
  → convertToLlm（去除 UI 专用类型，映射消息）
  → Provider 请求
  → Assistant + ToolResult
  → 下一次上下文
```

当前核心支持工具并行或串行策略，以及执行前后钩子。并行模式中工具结束事件可以按完成顺序到达，而结果历史保持 assistant 请求顺序。可借鉴的原则是：**执行调度与持久消息顺序是不同问题**。

steering 与 follow-up 区分“在当前工作中途修正”与“当前运行结束后再处理”。不要简单把所有新消息追加到正在执行的请求里；明确它们在哪个边界进入下一次决策。

## SDK：嵌入完整编码会话

以下示例来自当前 SDK 形态，需要已配置的模型与认证。它会使用工作目录中的资源，具备实际工具能力；可先在一次性工作区尝试。

```typescript
import { createAgentSession } from "@earendil-works/pi-coding-agent";

const { session } = await createAgentSession({
  cwd: "/absolute/path/to/scratch-workspace",
});
const unsubscribe = session.subscribe((event) => {
  if (event.type === "message_update" &&
      event.assistantMessageEvent.type === "text_delta") {
    process.stdout.write(event.assistantMessageEvent.delta);
  }
});
try {
  await session.prompt("阅读 README，给出项目概览。");
  console.log(session.getLastAssistantText());
} finally {
  unsubscribe();
  session.dispose();
}
```

`createAgentSession` 提供完整会话；只用 agent-core 时，需要自己管理资源和持久化。完整 SDK 可以注入 `sessionManager`、`resourceLoader`、模型和工具。宿主希望不写会话文件时，可使用 `SessionManager.inMemory()`，但这并不自动禁止工具读写。

`SessionManager` 是最终上下文的权威来源，修改 `agent.state.messages` 不等于修改持久上下文。会话切换会替换 session，对旧 session 的订阅要重新绑定。清理时调用 `dispose()`，不能只丢弃对象引用。[SDK 文档](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/sdk.md)。

## Extension：增加可执行行为

extension 是默认导出工厂的 TypeScript 模块，接收 `ExtensionAPI`。可以注册工具、命令、事件、提供方与 UI。下面是根据仓库最小工具例子编写的教学变体：

```typescript
import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI }
  from "@earendil-works/pi-coding-agent";

const greet = defineTool({
  name: "research_greet",
  label: "Research greeting",
  description: "Return a local greeting; no files or network are accessed.",
  parameters: Type.Object({ name: Type.String() }),
  async execute(_id, args, _signal, _update, _ctx) {
    return {
      content: [{ type: "text", text: `Hello, ${args.name}!` }],
      details: { greeted: args.name },
    };
  },
});
export default function (pi: ExtensionAPI) {
  pi.registerTool(greet);
}
```

可保存为 `hello.ts` 后通过 `pi --extension ./hello.ts` 试用。精确签名以当前类型声明为准。[原始 hello 示例](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/extensions/hello.ts)。

Pi 工具结果需要模型可见的 `content` 与用于结构化状态/展示的 `details`。不要把 UI 字符串当成唯一业务结果。执行失败按约定抛异常；普通返回对象并不会自动变成错误。文件修改要遵守宿主的写入协调机制。[Extension 文档](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md)。

工厂里不要立即启动长生命周期进程或监听器：某些调用只加载扩展，不启动完整会话。会话资源在 `session_start` 或具体命令中启动，在 `session_shutdown` 做幂等清理。事件的返回值是否生效取决于事件类型，不要假设所有监听器都能阻止执行。

## Skill 与 Package

Pi 支持 Agent Skills 规范，启动时向模型展示技能名称与描述，匹配任务后加载全文。用户可以用 `/skill:name` 显式调用。配置支持 `.pi` 与 Agent Skills 相关位置，但项目资源受信任设置影响。[Skills 文档](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md)。

package 可以同时携带 extensions、skills、prompts 与 themes。当前 `package.json` 可通过 `pi` 字段列出资源路径：

```json
{
  "name": "my-research-package",
  "keywords": ["pi-package"],
  "pi": {
    "extensions": ["./extensions/research.ts"],
    "skills": ["./skills"],
    "prompts": ["./prompts/*.md"]
  }
}
```

这是 Pi 格式，不是 Codex 插件 manifest。可通过 `pi install ./local-package` 管理。扩展导入的宿主包与依赖应按包文档处理，避免把另一份宿主运行时打包进去导致重复类和注册表。[Pi Packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md)。

## 会话、分支与上下文压缩

Pi 的完整会话管理保留历史树与活跃叶子，fork/分支不要求删除其他历史。上下文重建选择活跃分支并应用压缩。扩展重建任务状态时，要从活跃分支读取，而不是把每个历史分支的动作都合在一起。[Session format](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/session-format.md)。

分支很适合比较调查策略：同一初始资料，一条路径先查入口，另一条先看测试，再对照证据与成本。但是文件和外部副作用不会因为消息分支切换自动回滚，所以实验工作区应隔离，或明确记录修改。

事件结束也要按层理解：低层 `agent_end` 后可能还有自动恢复或队列工作，完整集成需要判断 `agent_settled` 等终态边界。不要在第一条 agent_end 就关闭连接或宣布最终完成。

## 权限与 MCP 适配边界

Pi README 明确表示没有内置限制文件、进程、网络或凭据访问的权限系统，默认继承启动进程权限。[Pi README](https://github.com/earendil-works/pi#permissions--containerization)。项目 trust 管理“是否加载项目资源”，不能代替操作系统隔离。

extension 与宿主进程拥有相同权限，因而“拦截 tool_call”不能防止恶意扩展绕过工具访问文件。需要强边界时使用容器、micro-VM 或策略控制的外部执行环境。[Containerization 文档](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/containerization.md)。

若要接入 MCP，可以在扩展层编写桥接：建立 MCP 客户端、发现外部工具、注册 Pi tool、规范化结果，并在生命周期中关闭连接。这里是适配设计建议，不表示 Pi 的每个安装都有内置完整 MCP 集成。仔细验证权限和结果类型后再扩大工具集合。

## 从 Pi 带走的设计经验

最值得迁移的是：统一模型层、独立 agent core、应用消息到模型消息的转换、事件接口、活跃分支状态、资源按需发现。用最小 extension 开始，增加一个只读工具与一个报告 skill，再用 SDK 把它们嵌进自己的界面。

<details><summary>练习：扩展只在终端模式有对话框，RPC 和无 UI 模式怎么办？</summary><p>工具与事件逻辑应独立于界面。按 ctx.mode 与 ctx.hasUI 判断是否能交互；不能审批时应返回明确状态，不能默认同意。只有渲染部分使用终端 UI，实际能力保持可测试。</p></details>
