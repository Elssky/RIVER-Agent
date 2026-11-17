## 定位：一个完整编码 Agent 的开放实现

[openai/codex](https://github.com/openai/codex) 提供本地 Codex CLI 的开源实现。学习时应分清：仓库里的 CLI 与协议代码、官方 SDK、App Server，以及桌面/云端产品的部署与服务能力。读到某个客户端或功能开关，并不代表所有安装环境都能使用同样能力。

当前仓库主要运行逻辑在 Rust 工作区 `codex-rs`，还有 CLI 包装、TypeScript SDK、协议与执行相关组件。最有价值的学习问题是：一个模型提出的文件/命令动作，如何被变成可取消、可审计、受权限限制的真实执行？[仓库 README](https://github.com/openai/codex/blob/main/README.md)。

**建议阅读顺序**：SDK 使用方式 → 工具路由 → 核心会话与任务 → 执行与沙箱 → Skill/插件 → App Server。先从一个完整外部请求理解边界，再进入内部模块，避免一开始就在大量 Rust crate 中迷路。

## 源码地图：按职责查找

下表依据本次获取的 `main` 分支文件结构。仓库正在重构；旧文章里将技能放在 `core/src/skills` 的路径，在本次快照中应关注 `ext/skills`。未来阅读以实际检出目录为准。

| 路径 | 看什么 | 带着什么问题读 |
| --- | --- | --- |
| [`sdk/typescript`](https://github.com/openai/codex/tree/main/sdk/typescript) | 宿主如何调用 CLI | 线程怎样续接，事件怎样暴露？ |
| [`codex-rs/core/src/session`](https://github.com/openai/codex/tree/main/codex-rs/core/src/session) | 会话、步骤上下文 | 哪些信息跨步骤保存？ |
| [`codex-rs/core/src/tasks`](https://github.com/openai/codex/tree/main/codex-rs/core/src/tasks) | 运行任务 | 如何启动、停止与切换工作？ |
| [`core/src/tools/router.rs`](https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/router.rs) | 模型可见工具与路由 | schema 与实际实现如何一致？ |
| [`core/src/tools/registry.rs`](https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/registry.rs) | 工具执行运行时 | 如何统一结果与执行状态？ |
| [`core/src/unified_exec`](https://github.com/openai/codex/tree/main/codex-rs/core/src/unified_exec) | 进程执行 | 会话进程、输出和 stdin 怎么管理？ |
| [`core/src/compact.rs`](https://github.com/openai/codex/blob/main/codex-rs/core/src/compact.rs) | 上下文压缩 | 历史怎样缩减并继续任务？ |
| [`codex-rs/ext/skills/src`](https://github.com/openai/codex/tree/main/codex-rs/ext/skills/src) | 技能目录、提供方、选择、加载 | 技能来源与模型可见内容如何分离？ |
| [`codex-rs/core-plugins/src`](https://github.com/openai/codex/tree/main/codex-rs/core-plugins/src) | 插件存储与同步 | 包身份、资源与安装状态怎么管理？ |
| [`codex-rs/app-server`](https://github.com/openai/codex/tree/main/codex-rs/app-server) | 客户端协议接入 | 交互 UI 如何驱动会话？ |

读源码时，把三列记在自己的笔记中：输入、输出、不变量。例如 `ToolRouter` 的模型可见 specs 与 registry 需要来自同一 finalized plan；这个约束能直接迁移到自建工具系统，而无需照搬 Rust 实现。

## 一次任务怎样经过系统

<div class="diagram"><div class="flow"><div class="node">CLI / 客户端<small>提交输入与配置</small></div><span class="arrow">→</span><div class="node">会话 / 任务<small>上下文与模型请求</small></div><span class="arrow">→</span><div class="node">工具路由<small>识别调用与实现</small></div><span class="arrow">→</span><div class="node">执行运行时<small>策略、沙箱、进程</small></div><span class="arrow">→</span><div class="node">结果与事件<small>继续模型和更新 UI</small></div></div><p class="caption">这是职责级教学图，不代表仓库中每个函数调用的精确顺序。</p></div>

关注工具“可见”与工具“可执行”的联系：构建请求时有哪些工具被公布？返回的调用怎样解析？执行器收到的上下文包含哪些权限与取消信息？失败怎样回到模型？这些边界比单独一份系统提示更能解释 agent 行为。

在 `unified_exec` 中，可以研究持久进程的管理与输出窗口；在压缩相关文件中，可以研究剩余输入预算与历史转换。理解时应沿一次可观察轨迹，遇到重要类型再跳到定义，避免把全部抽象一次性记住。

## 用 SDK 嵌入 Codex

Codex TypeScript SDK 包装 CLI 子进程，并通过 stdin/stdout 交换 JSONL 事件。它适合“我的程序要调用一个完整编码 agent”，不同于直接请求一个 LLM API。[SDK README](https://github.com/openai/codex/blob/main/sdk/typescript/README.md)。

```typescript
import { Codex } from "@openai/codex-sdk";

const codex = new Codex();
const thread = codex.startThread({
  workingDirectory: "/absolute/path/to/project",
  sandboxMode: "read-only",
});
const turn = await thread.run("阅读项目，列出入口与待验证问题。不要修改文件。");
console.log(turn.finalResponse);
console.log(turn.items);
```

这是根据当前 SDK 编写的集成示例；需要安装 SDK、可用 CLI 运行环境与认证。工作目录示例要换成你的绝对路径。默认 Git 仓库检查、配置发现和权限行为需要按 SDK 版本确认，不建议为了省事直接关闭所有检查。

流式消费使用 `runStreamed()` 返回的事件序列。不要只收集最后一句文本：item 可以包含命令、文件变更等证据，turn completion 提供使用量。复用同一个 thread 可继续会话；跨进程使用 `resumeThread(id)`，并保留正确环境与权限。[官方 Codex SDK 文档](https://developers.openai.com/codex/sdk)。

```typescript
const { events } = await thread.runStreamed("继续调查配置来源。");
for await (const event of events) {
  if (event.type === "item.completed") console.log(event.item);
  if (event.type === "turn.completed") console.log(event.usage);
}
```

集成到产品时，由你的后台进程管理工作区与线程，前端只接收适当事件。不要把 CLI 凭据或任意工作目录直接暴露给浏览器用户。

## App Server：为交互客户端提供协议

App Server 是更丰富的客户端接入层，适合 UI 需要管理线程、流式状态与审批等交互。官方文档说明初始化、线程与轮次方法，以及通知与请求处理。[App Server 文档](https://developers.openai.com/codex/app-server)。

概念流程是：启动服务器传输 → initialize/initialized → thread/start 或恢复 → turn/start → 消费线程与轮次通知 → 响应需要客户端处理的请求 → 根据终态更新 UI。SDK 和 App Server 是不同接口路径，不要把一种的事件名直接拿到另一种里使用。

```text
客户端                         App Server
initialize  ------------------>
            <----------------- initialize response
initialized ------------------>
thread/start ----------------->
            <----------------- thread identity / notifications
turn/start ------------------->
            <----------------- item and turn notifications
            <----------------- approval request（如适用）
approval decision ------------>
            <----------------- turn completed / failed
```

上面只展示顺序，省略实际 JSON-RPC 参数。开发时用对应版本的协议类型生成客户端；客户端要处理断开、未知通知、失败轮次、审批拒绝与取消，不要只实现成功聊天路径。

## Skill、项目指令与插件

项目指令文件帮助 agent 理解仓库约定；Skill 提供某类工作流程与资源；插件负责包装能力与连接。它们不是同一层。比如 `AGENTS.md` 可以说明测试命令，报告 skill 可以说明证据核对，MCP 服务可以提供内部知识查询。[官方 Skill 文档](https://developers.openai.com/codex/skills)。

当前技能源码包括 catalog、provider、loader、selection 与 render 等模块。阅读时重点追踪：不同来源怎样形成目录？何时加载全文？资源在哪个执行环境读取？持久提示如何识别？这比记住一个目录路径更有迁移价值。

给 Codex 增加领域能力，优先尝试“Skill + MCP 服务”这条外部扩展路径；不必先修改核心。插件包装要核对目标版本：当前官方文档描述根 `plugin.json` 与可选 `mcp.json`、skills，旧 `.codex-plugin/plugin.json` 仍有兼容用途。不同接口的示例存在版本差异，不能据此推断任意 manifest 都有效。[插件包装规范](https://developers.openai.com/plugins/build/plugins)。

本地试验可以先放一份项目 skill，无需先打包插件：

```text
your-project/
  .agents/
    skills/
      research-report/
        SKILL.md
        references/
          report-example.md
```

当前官方说明中，仓库 skill 沿工作目录到仓库根的 `.agents/skills` 发现；个人 skill 可放在 `~/.agents/skills`。同名项的处理要按宿主规则核对，不能套用 Pi 的“首项保留”行为。将前面原创 skill 放入后，在新会话中显式要求使用 `research-report` 并检查是否加载全文。

如果采用当前便携插件布局，一个最小仅含 skill 的教学包可以是：

```text
research-plugin/
  plugin.json
  skills/research-report/SKILL.md
```

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "research-plugin",
  "version": "0.1.0",
  "description": "Evidence-based workspace research workflows."
}
```

这是当前文档的便携形态示例；本地 marketplace 的安装入口与 OpenAI 专有覆盖项需按目标 CLI/桌面版本配置。不要仅重命名旧 `.mcp.json`：便携 MCP 格式还声明 transport 类型。

自建 agent 可以吸收渐进加载与资源来源管理，但应明确自己的扫描目录、冲突策略和可信边界。不要复制“忽略宿主约束”的 skill；真正权限只来自宿主执行策略。

## MCP 与配置适配

Codex 提供 MCP 连接配置。为内部知识库编写服务时，先用小工具验证工具发现、认证、查询、错误结果，再添加报告 skill。工具要有窄输入与明确输出，限制账号和工作区范围。[官方 MCP 文档](https://developers.openai.com/codex/mcp)。

例如将可选练习 `examples/mcp_server.py` 暴露给 Codex，配置里的解释器与脚本都换成实际绝对路径：

```toml
# 放入目标 Codex 环境的 config.toml；这是连接示例，不会自动安装 MCP SDK。
[mcp_servers.workspace_research]
command = "python"
args = ["E:/Codes/AgentTutorial/examples/mcp_server.py"]
enabled_tools = ["read_workspace_note"]
startup_timeout_sec = 20
tool_timeout_sec = 30
```

该服务默认只读取随教程附带的工作区。若要适配你自己的目录，请在服务端显式修改范围，并保留边界检查。不要把范围参数交给模型任意扩大。

模型提供方、运行行为与权限通过配置管理；配置文件与命令行、项目设置的优先关系要依据当前官方说明。[配置基础](https://developers.openai.com/codex/config-basic)。不要在教程里硬编码一套永远有效的全部字段；学习时从当前版本支持的最小配置开始。

如果你只是调用 Codex SDK，你复用的是完整 harness；如果你自己实现 loop，就需要自己的 provider 适配与工具执行。这两条路线可以组合，但应避免在外层重复运行另一套工具循环，造成双重执行或无法解释的预算。

## 执行、审批与沙箱

Codex 的权限与执行层值得单独阅读。审批与沙箱分别管理授权和实际访问边界；具体行为取决于配置、平台和运行模式。不要把 `read-only`、`workspace-write` 等标签理解为所有环境的相同底层实现。[Agent 审批与安全说明](https://developers.openai.com/codex/sandbox)。

源码的核心 README 描述了不同平台的沙箱依赖与支持限制，可以据此理解“策略必须由后端真实执行，否则应失败”的思想。[core README](https://github.com/openai/codex/blob/main/codex-rs/core/README.md)。自建时也应验证文件、网络与进程范围确实生效，不能只在 UI 里显示一个安全模式。

不要从教程示例中选择“最大权限”解决所有失败。先找到失败在哪一层：工具参数、配置、认证、审批、实际系统权限还是模型行为。给错误分类，是 agent 可以安全修复的前提。

## 用 Codex 思路改进自己的 Agent

可以借鉴四件事：模型可见工具与执行实现来自同一计划；长期进程有专门管理器；客户端通过事件而非抓取终端文字理解结果；权限与执行器在真实系统边界实现。然后用自己的任务集验证是否有效。

阅读练习：选择一个读取或命令工具，画出从 schema 到路由到实现再到结果的路径；找到取消信号从哪里来；找到一条失败测试；最后把同样职责补到自己的最小 agent。你不需要复刻整个 Codex 才能学到这一点。

<details><summary>自测：Codex SDK 是不是普通 OpenAI API SDK 的另一个名称？</summary><p>不是。Codex SDK 驱动完整 Codex CLI agent；普通 API SDK 用于请求模型和平台接口。前者复用 harness 与工具执行，后者让你自行构建循环与运行时。</p></details>
