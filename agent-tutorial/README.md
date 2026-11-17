# RIVER-Agent Tutorial

本教程以 RIVER-Agent 当前设计路线为贯穿案例：dsh Harness、单一中央 Agent、默认 ReAct、专业航运工具/服务、证据与时效验证。这里介绍的是架构目标与通用工程方法，不代表项目中相应服务已经接入。

双击 [index.html](index.html) 开始学习。8 篇静态教程、可点击目录、全文搜索、流程演示与上下文预算实验均可离线使用，无需 npm 安装或 Web 服务。

外部来源链接需要网络。真实模型练习需要你在本地终端配置自己的服务与 API 密钥；默认模拟版本无需密钥。

## 运行练习

需要 Python 3.10 或以上，仅使用标准库：

```powershell
cd examples
python agent.py --mock                  # 写入被拒绝，exit code 2 表示未完成
python agent.py --mock --allow-write    # 完成报告，exit code 0
python agent.py --mock --plugin greeting --allow-write
python -m unittest -v test_agent.py
```

报告写入 `examples/workspace/output/report.md`，每次运行的轨迹在 `examples/runs/`。这个小程序使用工作区报告任务演示通用 Agent Loop，不是 RIVER-Agent 的可运行实现，也不是操作系统沙箱；完整能力与限制见第二篇。`examples/mcp_server.py` 是独立的可选 MCP SDK v2 示例，需要额外依赖，未做端到端集成验证，不影响默认练习。

## 修改教程

正文源文件在 `content/`，公共样式/交互在 `assets/`。`build_site.py` 将 Markdown 预渲染成独立 HTML 和本地搜索索引。仅重新生成网页时需要 Python 的 `markdown` 与 `beautifulsoup4` 包；阅读与运行 agent 练习无需这两个依赖。

资料研究快照保存在 `research/`，不运行其代码。`research/source-manifest.json` 记录主要引用文件的摘要。教程交付压缩包仅包含页面、资源、正文、构建器、练习与来源摘要，不包含整份研究源码快照或运行日志。

内容按 2026-09-27 获取的公开资料撰写，具体接口请核对所用版本。本教程不是三个框架的完整审计，也没有验证付费模型调用。
