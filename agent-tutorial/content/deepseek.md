## 定位：一切皆插件的 Agent Harness

[deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) 简称 `dsh`，以 Cordis 为底层组合框架。模型适配器、工具注册表、会话日志乃至 agent loop 都通过插件组装，因此扩展不必始终改一个固定核心。[架构文档](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.zh.md)。这与 RIVER-Agent 的已讨论路线直接相关：优先复用 dsh 通用 Harness，再以领域插件、工具和独立专业服务扩展，不另造第二套主循环。项目集成前仍须锁定并核实 dsh 版本、许可证与具体接口。

它处于开发者预览，接口可能出现破坏兼容的变化。最适合学习的是**组合机制、服务边界、可逆副作用和日志投影**。学习时固定版本；本文基于本次取得的 `master` 分支资料，而不是一个长期稳定的接口承诺。[README](https://github.com/deepseek-ai/deepseek-harness/blob/master/README.zh.md)。

## Cordis：理解五个基本概念

| 概念 | 含义 | 自建 Agent 中的对应 |
| --- | --- | --- |
| Plugin | 向上下文注册行为的模块 | 能力包与生命周期 |
| Context | 服务容器，如 `ctx.tools` | 依赖注入容器 |
| inject | 声明需要的服务 | 启动前依赖检查 |
| Typed Event | 扩展点的输入输出契约 | Hooks / middleware |
| Effect / Dispose | 注册与资源能被撤销 | 注销、清理、热重载 |

`inject = ['tools']` 表示依赖 tools 服务，而不是“模型注入提示词”。Cordis 等待服务就绪，再运行 `apply(ctx)`。插件应该通过服务 key 访问接口，不把自己锁死在某个具体后端上。[Cordis 入门](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/cordis-primer.zh.md)。

有些事件是通知，有些事件是 waterfall 包装，有些需要串行处理。waterfall 监听器通常收到 `next()`，调用它委托后续逻辑，然后可处理返回值；不调用会短路。不同模式的返回值、等待语义和顺序属于契约，不能混用。

## 源码地图与能力 Seam

| 路径 | 角色 | 关注接口 |
| --- | --- | --- |
| [`packages/core/agent`](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/core/agent) | Agent 句柄与注册 | 活跃工作、输入与事件 |
| [`core/agent-loop`](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/core/agent-loop) | 默认驱动器 | turn / step 生命周期 |
| [`core/tools`](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/core/tools) | 工具注册与执行管线 | schema、策略、结果 |
| [`core/session`](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/core/session) | 事件日志 | 从日志派生模型历史 |
| [`llm/llm`](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/llm/llm) | 模型协议抽象 | Adapter 与 StreamChunk |
| [`skill/skill`](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/skill/skill) | Skill 注册表 | 来源与内容渲染 |
| [`skill/tool-skill`](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/skill/tool-skill) | 模型侧 Skill 消费方 | 目录、加载工具与显式调用 |
| [`bundle/base`](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/bundle/base) | 通用组装 | 工具、模型、状态与策略 |
| [`sdk/client`](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/sdk/client) | 进程外调用方 | JSON-RPC 与子进程 |

Seam 是一项可替换能力的连接面，通常由 **接口声明、后端实现、消费方** 三个角色构成。例如文件接口定义 `read`，本地或沙箱后端提供实现，面向模型的读取工具负责调用与反馈。替换后端不必重写模型工具。[能力边界文档](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/capability-seams.zh.md)。

<div class="diagram"><div class="flow"><div class="node">Service Definition<small>定义稳定接口</small></div><span class="arrow">↔</span><div class="node">Provider<small>本地 / 远程 / 沙箱</small></div><span class="arrow">↔</span><div class="node">Consumer<small>模型工具或 UI</small></div></div><p class="caption">把“能力”与“实现位置”分开，才能在同样工具后换执行环境。</p></div>

## Profile 与 Bundle：如何组装一个产品

`profile` 是具名运行组装；`bundle` 提供配置项与挂载代码。当前包含 web、headless、sdk、sdk-minimal、acp 等运行形态。主要 profile 共享 base，再叠加各自应用；sdk-minimal 是独立显式组装的例外。[架构 / Profiles](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.zh.md#profile-与组合包)。

组装按顺序应用 bundle 与 patch，后层能够替换前层配置。先查看实际树，再添加 overlay：

```sh
dsh --profile web --dump-config
```

不要把网页入口、SDK 服务器或模型选项散落在不同启动脚本里。dsh 把运行形态表达为 profile，这可以启发自建 agent 使用“配置组装 → 统一启动器”的模式。

实践时先在已构建源码仓库里创建本地插件，再使用 `--patch` 添加；不要一开始尝试热替换整个 loop。适配器、工具或策略插件是更容易观察的入口。

## 写第一个工具插件

下面是原创问候工具，按照当前 dsh `defineTool` 契约编写。与 Pi 的 `content/details` 返回格式不同，dsh 的 execute 返回声明过的规范值，render 再生成模型内容。[工具开发教程](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/tool.zh.md)。

```typescript
import type { Context } from '@deepseek-ai/cordis';
import { defineTool } from '@deepseek-ai/dsh-tools';

export const name = 'research-greeting';
export const inject = ['tools'];

export function apply(ctx: Context) {
  ctx.tools.register(defineTool({
    name: 'research_greet',
    description: 'Return a local greeting without accessing files or network.',
    parameters: {
      name: { type: 'string', required: true },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value) => [{ type: 'text', text: value }],
    },
    async execute(args) {
      return `Hello, ${args.name}!`;
    },
  }));
}
```

注册是可逆副作用，插件释放时工具也撤销。参数在 execute 前校验，但非空字符串、跨字段等业务规则仍需自己检查；读取网络/文件的工具要遵守 `exec.signal`。错误要按框架规则规范化，不能把不同框架的结果对象混用。[工具编写参考](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/cookbook/adding-a-tool.zh.md)。

源码试验可用当前官方本地 overlay 方式，替换绝对路径：

```yaml
- insert:
    - id: research-greeting
      name: 'E:/path/to/deepseek-harness/scratch-plugin/src/my-plugin.ts'
```

```sh
pnpm dsh web --patch ./scratch-plugin/cordis.yml
```

路径必须是你的实际绝对路径。patch 文件不改变模块解析所在的 profile 目录；相对模块路径不一定按 patch 所在位置解析。[第一个插件](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/index.zh.md)。

## 生命周期：步骤、轮次与日志

在 dsh 的定义中，step 是一次模型请求加相关工具执行；turn 包含零个或多个 step。输入被拒绝时，可能出现有 turn、没有 step 的情况。不要用“用户发了一句”直接推断一定调用过模型。[生命周期文档](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/agent-lifecycle.zh.md)。

职责顺序可简化为：领取输入 → 提示装配 → pre-step 接纳 → 准备模型调用 → 持久记录 → 从日志派生请求 → 流式模型结果 → 工具执行与结果 → 继续或停止。准备阶段取消时不应留下仿佛已提交的用户/系统输入。

`session/event` 保存可回放事实，`agent/*` 负责运行时协调。实时 assistant chunks 用于 UI，完整消息或失败 attempt 在 settlement 后保存。对于自建 agent，最值得学习的是“模型真正看到的信息应能从持久记录重建”，而不是每次任意改一个内存数组。

## 工具管线：策略、执行与结果归一化

<div class="diagram"><div class="flow"><div class="node">pre-execute<small>允许 / 拒绝 / 询问</small></div><span class="arrow">→</span><div class="node">guards<small>最终单调拒绝</small></div><span class="arrow">→</span><div class="node">execute<small>包装与工具主体</small></div><span class="arrow">→</span><div class="node">post / finalize<small>结果处理</small></div><span class="arrow">→</span><div class="node">result<small>不可变终态</small></div></div><p class="caption">简化自官方工具管线；实际还有内容投影、审批、归一化与日志边界。</p></div>

工具策略不必分散写进每个能力实现。可以在前置事件中控制，在 around-dispatch 中加入超时与指标，在后置处理阶段规范化结果。需要不可撤销的拒绝约束时使用 guard 思路，避免后来的监听器再次放行。

规范值、模型可见内容与 UI 展示是不同投影。改变给模型看的文字，不一定删除程序能够访问的结构化值；保密策略必须同时处理真正的数据。工具结束后记录一个权威结果，UI 从持久事实重建，而不是要求工具导入前端组件。[工具流水线](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/tool-execution-pipeline.zh.md)。

PTC（程序化工具调用）使工具可在代码中组合，仍应进入相同执行管线。中间结构化值与最后送入模型的输出不同；成本降低不意味着权限可以跳过，也不意味着进程内存无限。

## Skill 子系统：注册、来源与模型入口

这里的 Skill 不是直接被 Cordis 当作 TypeScript 插件执行。Skill 注册表提供统一目录，文件系统等 provider 供应技能，tool-skill 消费它们并向模型提供目录和加载工具。

当前工具技能包依赖 `ctx.agents`、`ctx.tools` 与 `ctx.skills`。模型可调用技能及精确加载工具可见时，会发布持久目录；模型调用 `skill` 获取全文。用户可以通过对应 `/name` 手势注入可显式调用的 skill，具体语法和可见性按当前版本配置。[tool-skill README](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md)。

目录变更采用完整替换，空目录停用旧名称；已经显式注入正文的技能不应重复加载。这可以启发自建宿主把 skill 目录作为有版本的状态，不只是一段启动时拼接的提示词。

加载层与 provider 分离，也便于将来支持数据库、远端注册表或打包资源。但共享 skill 的内容格式，不代表共享全部生命周期与权限。

## 大模型适配器的契约

dsh 在 `ctx.llm` 上注册适配器。实现不仅要发 HTTP，还要把流归一化到 `StreamChunk`、保持块索引、正确累积工具参数、传递取消信号、报告 usage 与结束原因。`llm-deepseek` 与 `llm-pi-ai` 提供不同接入路线。[LLM 适配器指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/cookbook/adding-an-llm-adapter.zh.md)。

值得直接借鉴的约束：usage 在 finish 前交付；finish 后不再产生内容；工具参数保持原始 JSON 字符串；不支持的选项明确失败；需要续接的原生元数据保留为 replay state。不要在适配器里静默忽略模型不支持的字段。

还要将模型目录与实际请求能力统一。配置里“支持图片”不代表传输一定正确；模型能力解析、请求组装和历史续接必须一起验证。

## SDK 与外部集成

TypeScript/Python SDK 通过进程外 JSON-RPC 驱动完整 dsh 运行时。TypeScript 的 `DeepSeekHarness` 管理子进程，选择 profile 与 patches；低层 `HarnessClient` 提供协议请求与通知。[SDK 客户端](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/sdk/client/README.zh.md)。

```typescript
import { DeepSeekHarness } from '@deepseek-ai/dsh-sdk-client';

const harness = new DeepSeekHarness({ profile: 'sdk' });
try {
  const result = await harness.run('分析 section-42 在 08:00–08:05 的交通态势；仅使用已授权的查询与分析工具，给出证据来源、数据有效时间和局限。');
  console.log(result.finalResponse);
} finally {
  await harness.close();
}
```

需要同版本运行时、有效模型路由和认证；这里省略具体 provider/model 配置以避免绑定某个账户或模型。高层运行收集直到 agent idle，最后助手文本不保证因果上只属于一条输入：steering 与其他排队工作可能参与。服务连接关闭、超时与协议错误要在外层处理。

当前 SDK 文档还注明没有轮次中提示取消方法，放弃执行需关闭运行时；内部 agent 的取消能力不能直接推断为所有 SDK 都有 `cancel()`。学习集成时要核对当前协议，不能编造缺失方法。

## 可以迁移到自己的设计

把服务接口、实现与消费工具分离；注册要可逆；新功能优先挂到合适事件域；从持久日志派生上下文；部署形态通过 profile 与有序配置组装。它们能让自建 agent 更容易扩展，但也引入依赖与生命周期复杂度。

初学者先做一个工具插件，再做一个策略插件，最后替换一个 provider。每一步验证装载、调用、拒绝、卸载与恢复。生产使用前仍需明确安全评估与执行隔离，dsh 的官方安全说明将其定位为实验性软件。[安全说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.zh.md)。

<details><summary>自测：一切皆插件，是不是所有模块都能任意重排？</summary><p>不是。服务依赖、事件顺序、不变量与资源所有权限制组合方式。可替换意味着接口稳定、契约清晰；不是消除模块之间的关系。先通过 dump-config 和文档理解实际组合，再修改 overlay。</p></details>
