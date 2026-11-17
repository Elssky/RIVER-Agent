## 如何使用这份教程

推荐先读前四篇，完成最小循环与模拟练习，再按自己的目标读源码。对照本仓库 RIVER-Agent 的路线，应优先读 DeepSeek Harness（dsh）的插件组合、Agent Loop、工具管线、Session 与 Schedule；Codex 和 Pi 用来横向比较完整产品运行时及可嵌入 SDK 的不同取舍，AI Agent Book 补充通用原理。RIVER 的设计不以同时支持三个框架为目标。这些是阅读路线建议，不是产品优劣排名。

## 把通用知识落到 RIVER-Agent

项目文档已经确定的是设计原则，不是已交付功能：以 dsh 为 Harness 底座，使用单一中央 Agent 和默认 ReAct；复杂任务可以进入由 Runtime 强制只读的 Plan Mode；航运算法由独立专业服务承担；大结果外置并以受控引用传递；首期优先定时任务，事件触发后续再议。教程后续章节围绕这些边界举例，但不会把 AIS、预测、风险或规则工具表中的规划项误写成当前已接通能力。

阅读源码时建议按此顺序追踪：

1. dsh Agent Loop 与工具执行管线：弄清一次观察—行动循环在哪些点可以暂停、拒绝或结束。
2. dsh Session 与 Persistence：弄清事件日志如何成为可恢复会话事实。
3. dsh Cordis、Profile 与 Bundle：弄清 RIVER 扩展怎样装配并可逆卸载。
4. dsh Schedule：区分定时投递回执与 RIVER 业务 Run 完成状态。
5. 再设计领域工具契约：从观测查询、结果引用、专业计算、时空有效性验证构成低风险切片。

具体 dsh 接口须以最终锁定版本核实。尤其是工具发现、Plan Mode 的只读强制能力、Host Schedule 的实际行为和会话恢复策略，不能只凭架构概念假设 API 已具备。

全站正文、样式、搜索索引与交互都在本地。双击 `index.html` 即可阅读，不需要服务器或网络；外部原始文档与真实模型调用需要网络。复制按钮在部分本地浏览器中会采用兼容方式；阅读完成状态受浏览器本地存储策略影响。

正文中的代码分三类：标注“示意”的片段用于理解设计；框架示例需要相应依赖、版本与认证；`examples/agent.py` 是实际可运行练习。不要把概念接口当成项目已发布的 API。

## 《深入理解 AI Agent》的阅读地图

[bojieli/ai-agent-book](https://github.com/bojieli/ai-agent-book) 是李博杰《深入理解 AI Agent：设计原理与工程实践》的开源主仓库，提供正文与配套实验。本次获取的正文组织为 10 章。这里提供原创的阅读映射，不复制整书内容。[在线阅读入口](https://bojieli.github.io/ai-agent-book/)。

| 原书章节 | 要回答的问题 | 对应本教程练习 |
| --- | --- | --- |
| [1 · AI Agent 入门](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter1.md) | Agent 与 harness 分别提供什么？ | 画出任务边界与完整循环 |
| [2 · 上下文工程](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter2.md) | 每次请求放什么，怎样压缩？ | 比较全量上下文与按需加载 |
| [3 · 用户记忆和知识库](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter3.md) | 记忆与检索怎样参与决策？ | 给证据加来源与时间 |
| [4 · 工具](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter4.md) | 动作空间怎样设计与限制？ | 为工具定义 schema 与错误结果 |
| [5 · 代码相关内容](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter5.md) | 代码执行如何增强能力？ | 用隔离执行器代替任意 shell |
| [6 · 交互](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter6.md) | 观察与动作空间如何扩展？ | 做流式进度、中途修正与取消 |
| [7 · Agent 的评估](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter7.md) | 如何区分真实改进与波动？ | 建立成功断言与故障任务集 |
| [8 · 模型后训练](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter8.md) | 何时需要改变模型本身？ | 先测 harness 瓶颈，再考虑训练 |
| [9 · Agent 的持续进化](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter9.md) | 怎样用轨迹推动迭代？ | 将失败案例变成回归评估 |
| [10 · 多 Agent 协作](https://github.com/bojieli/ai-agent-book/blob/main/book/chapter10.md) | 拆分何时更有效？ | 三个独立调查任务与证据合并 |

第 5 章在表中使用主题描述而非引用完整章名。章号以本次正文为准，旧版 PDF 的组织可能不同；后续请核对仓库最新目录。

阅读原书时，每章记下一个原理、一个失败模式和一个可执行实验。比如读完上下文工程，不必背所有压缩方法，先验证“只保留新证据 + 摘要旧调查”是否减少费用且不丢关键事实。

## 一条可执行的学习路线

| 阶段 | 要做什么 | 交付证据 |
| --- | --- | --- |
| 第一轮 · 看懂 | 前四篇 + 原书 1/2/4 章 | RIVER 逻辑架构图与一个领域工具契约 |
| 第二轮 · 做出 | 跑通 Python 教学闭环，再写 AIS 查询的模拟工具契约 | 成功、拒绝、坏参数和过期数据轨迹 |
| 第三轮 · 接入 | 在锁定版本中接 dsh 与模型适配 | 插件注册、工具调用、Session 恢复记录 |
| 第四轮 · 扩展 | 一个航运 Skill + 一个专业服务适配 | 证据引用、工具授权与结果时效验证 |
| 第五轮 · 稳定 | 原书 3/7/9 章与任务恢复设计 | 领域回归任务集、成本和失败分类 |
| 第六轮 · 比较 | 评估多 Agent 或模型路由等扩展 | 与单中央 Agent 同预算基线的对比结果 |

不要把“通读所有源码”当成前置条件。围绕一个真实问题追踪请求路径，找到相关测试，再实现一个小变化。这样更容易建立结构化理解。

## 四个项目的来源与版本范围

本教程于 **2026-09-27** 获取公开文档与源码资料。Codex、Pi、AI Agent Book 使用当时 `main`，DeepSeek Harness 使用 `master`。分支 URL 会随项目更新；它们不代表固定 release。本次主要阅读的本地文件摘要记录在 [research/source-manifest.json](research/source-manifest.json)，便于核对所用内容。

| 项目 | 原始入口 | 本教程覆盖范围 |
| --- | --- | --- |
| Codex | [openai/codex](https://github.com/openai/codex) | README、SDK、工具路由、会话/任务目录、技能扩展与插件目录、官方配置/集成文档 |
| Pi | [earendil-works/pi](https://github.com/earendil-works/pi) | 模型 API、Agent core、SDK、Skill、Extension、Package、会话与容器文档 |
| dsh | [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | 架构、Cordis、生命周期、工具管线、工具开发、LLM 适配、Skill 与 SDK |
| 原书 | [bojieli/ai-agent-book](https://github.com/bojieli/ai-agent-book) | 原理、上下文、检索/记忆、工具、评估与协作主题 |

这不是逐行审计全仓库，也没有运行三个框架的所有测试或调用付费模型。框架代码示例基于所读接口；可运行 Python 练习与网页交互另行本地验证。具体安装、模型、配额、权限与发布策略以使用时官方资料为准。

## 规范与官方资料

- [Agent Skills Specification](https://agentskills.io/specification)：Skill 的目录、元数据与渐进加载约定。
- [MCP 工具规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)：工具发现、调用与结果结构。
- [OpenAI Function Calling](https://developers.openai.com/api/docs/guides/function-calling)：模型提出函数调用，应用执行并返回结果。
- [DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)：兼容接口与工具结果回传，核对推理模式要求。
- [Codex SDK](https://developers.openai.com/codex/sdk) 与 [App Server](https://developers.openai.com/codex/app-server)：完整 agent 的宿主集成路径。
- [OpenAI Skills](https://developers.openai.com/plugins/concepts/skills) 与 [插件包装](https://developers.openai.com/plugins/build/plugins)：流程层与安装包的边界。

各篇中还附有具体源码文件、模块文档与示例链接，便于直接继续阅读。教程里的图表、设计建议与模拟数字是原创教学材料，不是原项目性能数据。

## 常见问题速查

**一定要训练模型吗？** 不需要。先使用支持工具调用的模型，完善 harness 与评估。只有证据表明模型行为是瓶颈时，再考虑训练或换模型。

**Skill 会给 Agent 增加新工具吗？** Skill 主要提供指令与资源。新工具需要宿主、插件或服务注册；skill 只能指导使用已有能力。

**工具可以直接执行模型生成代码吗？** 可以设计这样的执行器，但需要权限、隔离、超时与资源限制。最小练习没有任意代码执行工具。

**MCP 能代替插件系统吗？** 它解决宿主与服务的协议连接。安装包、依赖、生命周期、版本迁移与本地代码扩展仍需宿主设计。

**为什么模型说成功还要验证？** 因为语言声明不是外部世界的事实。执行回执、产物检查与业务断言才能证明结果。

**三个项目该选哪个？** 先判断复用完整 harness 还是自己组合 loop，然后按集成语言、权限、扩展方式与版本稳定性选择。用自己的任务验证，不按星数或工具数量决定。

## 毕业练习：设计你自己的 Agent

写一份 1–2 页设计说明，包含目标与非目标、输入/输出、工具表、模型适配、Skill 加载、插件生命周期、权限、日志、恢复和评估。再实现三个任务：正常成功、缺少必要信息、工具被拒绝。

验收时检查 agent 是否诚实报告状态：真正完成才称完成，无法继续就给未完成项；拒绝不会被解释成成功；轨迹能解释每次动作由什么证据触发。做到这些，再逐步扩大能力，你已经拥有了可以继续迭代的工程基础。
