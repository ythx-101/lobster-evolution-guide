# Lobster Evolution Guide / 龙虾进化手册

**v1.0.1** | 2026-11-12

龙虾进化手册是一份面向 [OpenClaw](https://github.com/openclaw/openclaw) / Claude Code 等 AI agent 开发者的中文实战指南：用六个核心素养（心跳、记忆、子 agent 调度、想法农场、自愈、反思）把一个无状态聊天机器人升级成持续运行、能记事、能自我修复的 agent 系统。

*A hands-on Chinese guide to six architecture patterns for long-running AI agents (OpenClaw, Claude Code): heartbeat polling loop, three-layer memory (NOW.md + memory files + Git), parallel sub-agents, idea farm with decay, fallback chains & self-healing, and scheduled reflection.*

> 让你的 agent 从聊天机器人变成一个活的系统。

示例代码用 Claude Code CLI（`claude`）作为子 agent / LLM 的调用方式，你可以换成自己的 LLM 调用。

## 六大核心素养

| # | 素养 | 一句话 |
|---|---|---|
| 1 | [**心跳**](docs/lobster-guide-cn.md#1-心跳我活着) | 永不停歇的轮询循环，主动检查任务 |
| 2 | [**外挂海马体**](docs/lobster-guide-cn.md#2-外挂海马体我记得) | 三层记忆架构（NOW.md + 记忆文件 + Git） |
| 3 | [**工蜂调度**](docs/lobster-guide-cn.md#3-工蜂调度我会分活) | 拆任务、派子 agent、并行干活 |
| 4 | [**农场**](docs/lobster-guide-cn.md#4-农场我会种田) | 想法是种子，衰减是筛选器，浇水是关注 |
| 5 | [**自检与故障回流**](docs/lobster-guide-cn.md#5-自检与故障回流我能自愈) | 降级链 + 进度日志 + 防抖检查 |
| 6 | [**冥想与白日梦**](docs/lobster-guide-cn.md#6-冥想与白日梦我会反思) | 定时反思 + 随机联想，灵感种进农场 |

## 快速开始

- 不用安装，直接读 [docs/lobster-guide-cn.md](docs/lobster-guide-cn.md)。
- 环境：Python 3.9+（示例用了 `list[float]` 这种写法），只用标准库；第 3、5 节需要装好 `claude` CLI；第 2 节需要 Gemini API key（环境变量 `GEMINI_API_KEY`）。
- 5 分钟体验：从文档第 4 节复制 `farm_demo.py`，跑文中那 6 条命令：

```bash
python3 farm_demo.py plant "做一个把 git 历史转成播客脚本的 CLI"
python3 farm_demo.py plant "给记忆系统加个过期自动清理"
python3 farm_demo.py list
python3 farm_demo.py water 0
python3 farm_demo.py decay
python3 farm_demo.py list
```

## 怎么用

根据你的阶段挑对应部分看：

- **完全没概念** → 从心跳开始
- **agent 会失忆** → 看外挂海马体
- **干活太慢** → 看工蜂调度
- **想法太多** → 看农场
- **老出错** → 看自检与故障回流
- **想更聪明** → 看冥想与白日梦

每节都附 Python 示例代码（标准库为主）、踩坑表格和练习题。

## 适用场景 / 不适用场景

**适用**：

- 想让 agent 长期运行，而不是每次对话从零开始
- 想让 agent 跨 session 有记忆
- 个人或小团队自建 agent

**不适用**：

- 想要现成的框架或 SDK：这是方法论 + 示例代码，不是库
- 需要生产级分布式任务队列：示例用的是 JSONL 文件 inbox

概念对比：本手册用「NOW.md + 记忆文件 + Git」三层记忆，而不是单纯依赖上下文窗口；用「文件 inbox + 轮询」作为消息队列的轻量替代。

## FAQ

**OpenClaw 是什么？这份手册和 OpenClaw 官方是什么关系？**
OpenClaw 项目见 [openclaw/openclaw](https://github.com/openclaw/openclaw)。这份手册基于作者自己搭的 OpenClaw 系统整理，不是官方文档。

**必须用 Claude 吗？**
不必须。示例里的 `claude` CLI 调用可以换成任何 LLM。

**怎么让 agent 重启后不失忆？**
用三层记忆：NOW.md（当前工作状态）+ 记忆文件（结构化长期知识）+ Git 历史（完整审计记录），见第 2 节。

**记忆文件多了怎么搜？**
超过 20 个左右加向量搜索，并用文件 mtime 做增量索引，只重新 embed 变化过的文件，见第 2 节。

**什么时候该派子 agent？**
第 3 节有决策表：独立、不需要后续跟进的任务派工蜂；需要当前完整上下文的、很小的任务自己干。

**想法太多怎么筛？**
用农场：想法是种子，每天自动衰减，只有被反复浇水（关注）的才能活下来被收获，见第 4 节。

**agent 挂了怎么自动恢复？**
进程层面用 systemd `Restart=always` 或 launchd `KeepAlive` 保活；调用层面用降级链（方法 A 挂了用 B）加进度日志，见第 1、5 节。

## 文档

- [龙虾进化手册（中文完整版）](docs/lobster-guide-cn.md)
- 代码块语法检查（只编译、不执行）：`python3 scripts/check_code_blocks.py`

## 关于

基于林月（Lin Yue）构建的 OpenClaw 系统整理。

龙虾在进化。

## License

[MIT](LICENSE)
