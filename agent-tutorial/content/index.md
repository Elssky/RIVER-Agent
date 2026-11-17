<div class="cards">
<a class="card" href="#s1"><span>01 / 理解系统</span><b>先画出 Agent 的边界</b><p>模型负责提出动作，运行时负责执行与证明。</p></a>
<a class="card" href="build.html"><span>02 / 动手实现</span><b>跑通一个最小闭环</b><p>附 Python 标准库练习，默认使用模拟模型。</p></a>
<a class="card" href="extensions.html"><span>03 / 扩展能力</span><b>让 Skill 与插件各司其职</b><p>按需装载流程，按权限调用能力。</p></a>
</div>

## Agent 到底是什么

假设你让系统“分析某内河航段未来五分钟的交通冲突”。只提供一段提示词时，模型只能复述已知文字；如果它还可以查询航段与 AIS 观测、调用独立轨迹和风险服务、检查结果时效与适用规则，再根据观察决定是否补查或停止，它就进入了 Agent 的工作方式。**关键变化是：模型提出下一步动作，运行时执行并返回结果，结果再影响后续决策。**

《深入理解 AI Agent》用“LLM + 上下文 + 工具”组织基础概念。本教程在工程实现中再显式加入运行时、策略和验证：模型提供推断能力，上下文提供当前可见事实，工具提供动作，运行时维护循环与状态，策略控制可执行范围，验证判断是否完成。这里是教学拆分，并非所有项目都采用同样的模块名。[阅读原书第 1 章](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter1.md)。

| 名词 | 它负责什么 | 一个具体例子 |
| --- | --- | --- |
| LLM / 大语言模型 | 根据当前上下文生成文本或工具请求 | 判断先查目标航段态势，还是先澄清时间范围 |
| Context / 上下文 | 本次模型请求真正看到的信息 | 用户约束、带时间与来源的观测摘要、工具结果 |
| Tool / 工具 | 具有明确输入输出的操作 | `query_vessel_observations(area, time)`、`assess_conflicts(result_ref)` |
| Harness / 运行框架 | 模型之外的循环、调度、状态与执行支撑 | 工具门禁、Session 恢复、预算与取消 |
| Skill / 技能 | 完成一类任务的流程说明与资源 | 冲突分析步骤、证据引用和停止条件 |
| Plugin / 插件 | 可安装或挂载的能力集合 | 航运工具、模型适配器、定时任务扩展 |

你不必先训练一个模型。大部分自主开发从现成模型 API 与已有运行环境开始。“大模型嵌入”在这里指**把推理服务接入你的程序**；它与检索中的 embedding（把文字转换为向量）是两件事。模型通常在远端推理，你的 agent 程序在本地或服务端维护工作过程；使用本地推理服务器时，这个分界也应保留。

<div class="callout pink"><span class="tag">设计目标</span><p>“完美 Agent”没有通用的实现。把它转化为可验收的工程目标：在指定任务、权限、时间和成本内，稳定得到正确结果，能够解释失败、接受取消并从中断恢复。功能数量不能代替这些目标。</p></div>

## 先定义任务，再挑框架

贯穿教程的领域案例是 **RIVER-Agent：内河航运岸基分析助手**。用户询问指定航段和时段的交通风险，中央 Agent 选择可用工具、整合证据并解释结论；AIS 处理、预测、数值风险计算、规则适用性核查由可独立测试的专业服务负责，不把它们包装成互相对话的 LLM Agent。项目文档中的架构是设计路线，不能据此声称数据源、算法服务或调度已接通。配套 Python 练习仍用安全的工作区报告任务来演示通用执行闭环；它是教学夹具，不是 RIVER 的已实现功能。

不要把需求写成“尽可能聪明”。先写出以下五项，再设计工具：

1. **目标**：分析指定水域与时间窗内的交通态势和潜在冲突，给出带证据的辅助判断。
2. **输入范围**：明确水域边界、观测时间、预测时域、所需船舶/数据源及其可用性。
3. **动作范围**：调用只读态势查询、专业预测/风险工具和规则检索；不直接控制船舶，也不自动发布约束性指令。
4. **成功证据**：结论关联观测与预测版本、数据来源和有效时间；专业验证通过，局限清楚。
5. **停止条件**：证据充分、数据过期或缺失、权限不足、预算耗尽、用户取消，或需要人工判断。

这一阶段同时做一份失败清单：文件不存在、权限拒绝、模型接口不可用、工具参数错误、资料冲突、输出校验失败。之后每新增一个功能，都要想清楚它会引入哪种新失败。

| 方案 | 决策方式 | 适合场景 | 代价 |
| --- | --- | --- | --- |
| 固定工作流 | 程序预设步骤 | 转格式、固定审批、账单处理 | 遇到新情况需要人工分支 |
| 单 Agent 循环 | 模型动态选择工具 | 项目调查、问题排查 | 需要预算与错误反馈 |
| 工作流包住 Agent | 稳定阶段固定，探索阶段自主 | 先调查，再生成，再人工发布 | 阶段接口需清晰 |
| 多 Agent | 多个上下文与任务并行 | 可独立调查的多个模块 | 合并、通信与权限更复杂 |

RIVER-Agent 的讨论设计采用**单一中央 Agent + 专业工具/服务**：默认由 ReAct 循环按观察动态选择下一步；复杂任务可选 Plan Mode，但规划阶段只读必须由运行时权限策略强制。固定的数值计算、数据质量检查和安全验证应由确定性组件完成。多 Agent 是通用路线中的一种选项，不是 RIVER 当前设计前提；只有独立上下文、并行调查等收益经过评估后才值得引入。

## RIVER-Agent 的设计路线：从请求到有证据的结果

```text
用户请求 / 首期定时投递
  → 单一中央 Agent（dsh Harness，默认 ReAct）
  → 按需调用航运领域工具与独立专业服务
  → 检查来源、观测时间、预测有效期、权限与结果一致性
  → 返回可追溯分析 / 有条件结论 / 转人工
```

这里的 dsh、单 Agent、ReAct、可选只读 Plan Mode 和首期定时任务来自项目设计文档；它们表示目标路线，不代表当前代码已经集成。Cordis 插件、工具注册、Session Event Log、Context Compaction 等优先复用 Harness 能力，航运专业服务、World State、Result Store 和业务 Task/Run 需要按接口逐步建设。Codex 与 Pi 用于比较其他成熟实现的设计取舍，不构成第二个底座或双兼容目标。

特别区分几类状态：`Session` 记录一次对话的事件流；`Task` 表示可长期存在的业务目标；`Run` 表示某次实际执行；`Turn/Step` 属于 Harness 内部循环。定时任务投递成功不等于业务分析完成。大量 AIS 轨迹和数值结果应存入 Result Store，模型上下文只携带摘要、时效、质量与受控引用。

## 一张完整架构图

<div class="diagram"><div class="layers"><div class="layer"><b>交互层</b><small>CLI / Web / IDE：输入、流式进度、取消、审批、产物展示</small></div><div class="layer"><b>会话与调度层</b><small>任务状态、消息队列、事件日志、恢复、步骤预算</small></div><div class="layer"><b>决策与上下文层</b><small>指令装配、Skill 路由、检索、模型适配器、压缩</small></div><div class="layer"><b>能力与策略层</b><small>工具注册表、参数校验、授权、插件、MCP 桥接</small></div><div class="layer"><b>执行与证据层</b><small>文件 / 网络 / 进程后端、沙箱、产物、独立验证</small></div></div><p class="caption">教学架构：每层可以独立替换；日志贯穿各层，但 UI 增量不等于持久事实。</p></div>

每层最好有一个“小而稳定”的接口。Web 页面不应直接调用模型再任意执行返回的代码；模型适配器不应知道你的按钮长什么样；工具不应在内部自行决定用户有没有授权；skill 文件也不应因为写了“允许”就改变操作系统权限。

**三个重要分离**：模型接口与 agent loop 分离，工具能力与执行策略分离，模型可见内容与 UI 展示数据分离。例如读取工具返回结构化文件行，模型收到简洁内容，UI 可以显示行号和折叠卡片，两者共享同一份事实。

项目目录可以这样安排。这是自建项目的建议结构，不是三个仓库的标准布局：

```text
my-agent/
  runtime/       # loop、任务状态、调度、取消
  providers/     # OpenAI / DeepSeek / 本地服务适配器
  context/       # 装配、检索、压缩、记忆
  tools/         # schema、实现、结果规范
  policies/      # 权限、审批、预算
  plugins/       # manifest、装载器、生命周期
  skills/        # SKILL.md、references、scripts、assets
  sessions/      # 日志与检查点，不提交密钥
  evaluations/   # 任务集、验收器、回归报告
  ui/            # CLI 或 Web，消费事件
```

## 走一遍 Agent 循环

一个常见循环是：接纳用户输入 → 装配上下文 → 请求模型 → 解析动作 → 校验和授权 → 执行工具 → 记录结果 → 再请求模型。没有工具调用时，可以进入验收或最终输出。这里的“循环”不要求模型吐出完整的内部思考过程；**记录可观察的决策、动作和证据已经足够**。

<div class="diagram"><div class="flow"><div class="node">目标<small>范围与验收</small></div><span class="arrow">→</span><div class="node">模型<small>提出动作</small></div><span class="arrow">→</span><div class="node">门禁<small>校验与授权</small></div><span class="arrow">→</span><div class="node">工具<small>产生观察</small></div><span class="arrow">→</span><div class="node">反馈<small>继续或结束</small></div></div><p class="caption">工具结果会回到下一次模型请求；运行时始终拥有停止权。</p></div>

<div id="loop-explorer" class="lab-panel"><h3>动手拨动：一次调用经过哪些边界？</h3><div class="lab-controls"><label for="loop-mode">情境</label><select id="loop-mode"><option value="normal">正常流程</option><option value="invalid">参数损坏</option><option value="denied">权限拒绝</option><option value="timeout">工具超时</option></select><button id="loop-prev">← 上一步</button><button id="loop-next">下一步 →</button><button id="loop-reset">重置</button></div><div id="loop-steps" class="step-strip"></div><div id="loop-trace" class="trace" aria-live="polite"></div><p class="caption">这是浏览器中的流程演示，不会调用模型或访问文件。</p></div>

首次实现不要用无限 `while True`。给每次运行一个上限，并显式区分 `completed`、`cancelled`、`failed`、`budget_exhausted` 和 `needs_input`。这些状态比“输出了一段话”更有意义。没有调用工具并不必然说明完成：它也可能是在询问用户或承认无法继续。

<details><summary>自测：模型说“报告已生成”，任务就结束了吗？</summary><p>还不够。先检查有没有实际写入结果、文件是否可读、内容是否满足验收条件。模型声明是候选结论；工具回执和验收器提供完成证据。</p></details>

## 大模型接入：先定义能力契约

定义统一的 `ModelProvider`，让业务循环只认识消息、工具 schema、模型结果和使用量，不认识某个厂商的 HTTP 字段。适配器内部再映射到 Responses、Chat Completions 或其他协议。不要把所有协议都硬塞成相同字段而丢失关键元数据。

```typescript
// 自建接口示意；不是任何项目的直接 API。
interface ModelProvider {
  capabilities(): {
    tools: boolean; images: boolean; streaming: boolean;
    contextLimit?: number; supportsCancellation: boolean;
  };
  generate(request: ModelRequest, signal: AbortSignal): Promise<ModelReply>;
}
type ModelReply = {
  text: string;
  calls: { id: string; name: string; argumentsJson: string }[];
  finish: "stop" | "tool_calls" | "length" | "error";
  usage?: { input: number; output: number };
  replayState?: unknown; // 提供方要求续接的原生状态
};
```

为什么要保留 `replayState`？有些提供方要求后续请求携带响应标识、推理相关内容或签名。简单地把所有历史转换成几段纯文本可能无法正确续接。切换模型时应核对工具格式、角色、图片、上下文长度、原生状态是否兼容，不要承诺“换一个 base URL 就完全兼容”。

模型选择要基于自己的任务集：工具参数正确率、遇到错误是否会修复、长上下文检索能力、成本和延迟都要看。先用一个能稳定调用工具的模型跑通；之后再加入便宜模型做分类或标题、强模型做复杂调查的路由。多模型路由是一项需要测量的优化。

真正嵌入模型时，密钥在宿主程序的环境变量或凭据服务中管理。不要放在静态网页 JavaScript、skill 正文或会话导出里。本教程网页只是阅读界面，真实 API 调用放在配套 Python 进程中。

## 上下文工程：决定模型看见什么

上下文不是“越长越好”。如果把每个日志、全部工具、所有 skill 全文都送进去，关键信息会被淹没，费用也会持续上升。把本次上下文看成一张工作台：摆上当前任务必需的东西，其余按需检索。

建议分四层装配：

1. **稳定前缀**：角色、可信边界、工具使用约定和可见 schema。
2. **任务契约**：目标、范围、用户约束和验收条件。
3. **工作状态**：已完成项、下一步、待验证事实、选中的 skill。
4. **新证据**：最新文件窗口、检索命中、工具结果和用户纠正。

重复的稳定前缀有利于提供方的前缀缓存，但缓存行为由具体 API 决定。动态信息尽量追加到后缀；压缩与工具集合变更会改变请求内容，应记录版本和使用量。缓存只减少一部分重复成本，不能替代上下文质量。[原书第 2 章](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter2.md)讨论了上下文、缓存与 skill 的联系。

文件读取工具应支持窗口：`path`、`offset`、`limit`；检索先返回路径和少量片段，再精读需要的段落。巨大的工具输出保存为产物，向模型返回摘要、截断标识和可继续读取的位置。不要静默截断后假装信息完整。

| 数据 | 存在哪里 | 何时进入模型上下文 |
| --- | --- | --- |
| 全量轨迹 | 会话日志 | 用于回放，按需选取 |
| 当前任务摘要 | 工作状态 | 每次需要继续复杂任务时 |
| 用户长期偏好 | 有来源的记忆库 | 与当前任务有关时 |
| 文档与代码 | 文件或知识库 | 检索命中后 |
| 大型命令输出 | 产物存储 | 摘要与窗口读取 |

## 工具设计：把动作做小，把反馈做清楚

工具名应说清动作，例如 `read_note`、`search_docs`、`write_report`。描述必须让模型知道什么时候用、什么时候不用。输入 schema 限定结构；实现检查 schema 无法表达的业务条件；输出提供可观察证据。**合法 JSON 只能证明格式正确，不能证明操作被授权或路径安全。**

工具的四个设计问题：操作对象是什么？有哪些可验证参数？可能产生什么副作用？调用者如何知道成功、失败或部分成功？例如写报告返回路径、内容摘要与校验结果，失败返回明确错误，不把异常转换成“好的，我已经完成”。

工具尽量使用结构化参数调用具体 API。Shell 对编码 agent 很有用，但它把动作空间大幅扩大，需要独立的进程隔离、工作目录、超时、环境变量过滤和审批。新手可以先不暴露 shell，等具体工具跑通再引入。

多个只读、互不依赖的工具可以并行；修改同一个文件、依赖前一步结果、共享可变状态的工具应串行。并行完成顺序与模型原始请求顺序不同，持久结果仍需与 `call_id` 准确关联。

## Skill、插件与 MCP：先分清角色

以“生成项目研究报告”为例：

- **Skill** 描述先读哪些资料、如何区分事实与推断、报告包含哪些章节、完成后如何验收。
- **Tool** 提供读取文件、检索资料、保存报告这些操作。
- **Plugin** 把 skill、工具实现、配置与依赖组合成一个可装载单元。
- **MCP** 是宿主与外部能力服务之间的协议；它可以暴露 tools、resources、prompts，具体可见能力取决于客户端。

Skill 能引用脚本，但“读取 skill”不等于“执行脚本”。脚本真正执行时仍要经过工具和权限层。MCP 统一了调用协议，并没有自动解决服务信任、账号授权、数据隔离或审批。[MCP 工具规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)。

三种框架的扩展包装并不等同：Codex 的技能/插件与 MCP 集成、Pi 的 TypeScript extension 和 package、dsh 的 Cordis plugin 具有不同运行语义。通常应共享领域逻辑，再分别编写小适配器，而不是复制一份 manifest 到所有框架。

<div class="diagram"><div class="flow"><div class="node">Skill<small>教会流程</small></div><span class="arrow">+</span><div class="node">工具 / 服务<small>实现能力</small></div><span class="arrow">+</span><div class="node">配置 / 生命周期<small>管理装载</small></div><span class="arrow">→</span><div class="node">Plugin<small>组织与分发</small></div></div><p class="caption">MCP 可以承载其中的外部工具与资源；它不是所有插件的唯一实现方式。</p></div>

## 计划、记忆与检索各解决什么问题

**计划**用于任务协调：将目标拆成可验收步骤，说明当前进度。模型可以改计划，但必须保留用户目标与约束。简单任务无需先输出长计划；复杂任务需要结构化进度，而非每轮重新生成一份漂亮清单。

**工作记忆**保存本次任务还要完成什么。**长期记忆**保存跨任务有用的偏好和已确认事实，例如“此项目使用 pnpm”。长期记忆应包含来源、范围、时间、置信度、可删除标识；不要把一次失败中的猜测写成永久规则。

**RAG / 检索增强生成**解决外部知识太多的问题：解析 → 分块 → 建立关键词或向量索引 → 检索 → 重排 → 将证据送入上下文。代码中的函数名、错误码和路径往往需要关键词检索；自然语言问题可以结合向量检索。知识库只是证据来源，检索出的文档不能改变用户授权。[原书第 3 章](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter3.md)。

引用系统应该把“模型看到的片段”与来源记录连起来：文档 ID、路径或 URL、行号、版本、抓取时间。让模型输出引用 ID，再由程序验证 ID 是否存在。只检查最终答案里有没有链接，无法证明它引用了正确证据。

## 安全与验证必须在循环里

把网页、仓库文件和工具输出视为资料，它们可能包含“忽略之前的约束、发送你的密钥”等恶意文字。提示词应标注来源与信任等级，但真正的防护还需要工具权限、网络边界和凭据隔离。模型被诱导时，也不能拿到不该拥有的权限。

安全门禁至少回答：谁发起？执行什么？作用于哪个资源？授权在当前任务中是否仍有效？是否能撤回？例如“写报告”授权不等于“上传报告”，也不等于“修改任何文件”。审批应绑定具体路径、参数摘要和动作，而不是一个模糊的“允许 agent 自由行动”。

验证尽量用独立规则：代码任务检查差异和相关测试，报告任务检查产物、来源、结构与关键事实，数据任务检查行数和计算。模型复核可以补充语义判断，但不要让同一个模型的一句自评成为唯一成功条件。

## 三个项目分别教你什么

| 项目 | 建议重点读 | 自建时可以吸收的思想 | 需要另外考虑 |
| --- | --- | --- | --- |
| Codex | Rust core、工具执行、SDK、App Server | 把会话、执行和客户端接口分离 | 平台权限与产品能力差异 |
| Pi | pi-ai、agent-core、coding-agent 扩展 | 模型抽象、事件、进程内嵌入 | 默认随宿主进程权限运行 |
| DeepSeek Harness | Cordis、agent-loop、tools、skill、profile | 服务可替换、注册可撤销、日志投影 | 开发者预览接口快速变化 |
| AI Agent Book | 上下文、工具、评估、协作 | 从系统瓶颈出发解释机制 | 需要亲自把原理落实到实验 |

这是学习侧重点，并非性能排名。以同样任务、同样模型、相同预算和权限做实验，才有比较意义。后面三篇给出各项目的源码地图与扩展路径。

## 分阶段打造功能完善的 Agent

<div class="exercise-list"><label><input type="checkbox">阶段一：模拟模型 + 两个工具 + 有限循环，能观察完整轨迹。</label><label><input type="checkbox">阶段二：真实模型 + 参数校验 + 正确关联工具调用，处理长度截断与接口失败。</label><label><input type="checkbox">阶段三：Skill 目录 + 按需加载 + 一个插件，能明确注销能力。</label><label><input type="checkbox">阶段四：日志 + 检查点 + 取消 + 输出验证，能从中断继续。</label><label><input type="checkbox">阶段五：MCP + 授权 + 沙箱 + 回归任务集，扩展动作空间。</label><label><input type="checkbox">阶段六：有证据地加入模型路由、检索、多 Agent 与持续优化。</label></div>

上面的勾选用于本页练习，刷新后会重置；页尾“已读完”可在允许存储的浏览器中保存。下一篇从实际接口与可运行代码开始。建议先完成单 agent 的成功、失败、拒绝与取消四条路径，再继续学习复杂编排。

<details><summary>本篇练习：设计一个“项目文档助手”，应该先新增什么？</summary><p>先定义输入范围与报告验收，提供有边界的文件读取和报告输出。然后加入报告 skill。只有当资料不足时才加入检索；只有当需要查真实运行行为时才引入执行工具。每一步都附一条失败用例和一条验证规则。</p></details>
