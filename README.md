# 🌙 CoPaw Dream Engine

**Version:** 4.6.2 (Systematized Release)
**Type:** CoPaw Plugin + Skill Bundle
**Inspired by:** NousResearch Hermes Agent (Self-improving Agents) & Karpathy's LLM Wiki.

一个用于 CoPaw 智能体的**自进化梦境系统**。它不仅允许 Agent 自动整理碎片记忆、更新结构化 Wiki，还能在运行时将 SOP 转化为永久技能 (Skill)，实现“记忆 -> 知识 -> 能力”的闭环。

---

## 🚀 一键安装 (One-Click Install)

为了让任何 Agent 都能立刻拥有这套系统，我们提供了一键配置脚本。

### 1. 克隆到插件目录
```bash
# 进入 CoPaw 插件目录
cd ~/.copaw/plugins
git clone https://github.com/a1461750564/copaw-dream-engine.git
```

### 2. 运行安装脚本
进入项目目录并运行安装脚本。脚本会自动：
1.  **寻找 Agent**: 自动检测当前工作区。
2.  **配置 MCP**: 将 `evolution_engine` 注入 `agent.json`。
3.  **部署技能**: 将 `dream_system` 技能复制到工作区。

```bash
cd ~/.copaw/plugins/copaw-evolution-engine
/Users/jiaye/.copaw/venv/bin/python3 install.py
```

> **注意**：请使用 CoPaw 环境下的 Python (`~/.copaw/venv/bin/python3`) 运行脚本，以确保路径正确。

---

## ✨ 核心特性

1.  **自动梦境整理 (Dream Cycle)**: 
    *   扫描 `compact_*.md` (系统摘要) 和 `*.md` (Agent 笔记)。
    *   自动提炼知识，更新 `memory/wiki/` (Markdown 知识库)。
    *   **双信源机制**: 结合客观事实与主观决策，避免遗忘。

2.  **技能自进化 (Self-Evolution)**:
    *   Agent 在整理记忆时，若发现重复成功的流程 (SOP)，会自动调用 MCP 工具将其转化为**新技能**。
    *   支持技能使用统计与自动归档 (失败率高的技能会被淘汰)。

3.  **原生兼容**:
    *   基于 `compact_*.md` (CoPaw 原生压缩摘要)，无需修改底层源码。
    *   基于 CoPaw Cron (`0 3 * * *`) 定时触发，安全且省电。
    *   **优雅降级**: 即使 MCP 未连接，梦境系统仍可作为纯文本整理器工作，不会报错崩溃。

---

## 🛠️ 架构与文件

| 文件 | 作用 |
| :--- | :--- |
| **`install.py`** | **入口脚本**。自动配置环境，打通 MCP 与 Skill。 |
| **`plugin.py`** | 插件生命周期入口 (符合 CoPaw 规范)。 |
| **`mcp_server.py`** | 基于 `FastMCP` 的标准服务，提供 `evolve_*` 工具。 |
| **`lib/`** | 核心逻辑库 (技能管理、统计)。 |
| **`skills/dream_system/`** | 内置技能定义 (包含 v4.2 完整协议)。 |

---

## 📖 使用指南

### 手动触发
在 Agent 对话中输入：
```
/dream
```
Agent 将立即执行一次梦境整理，提取记忆并更新 Wiki。

### 自动运行
系统默认配置了每日凌晨 03:00 的 Cron 任务。Agent 会在空闲时自动“做梦”。

### 查看结果
- **Wiki 索引**: `memory/wiki/README.md`
- **梦境日志**: `memory/dreams/YYYY-MM-DD.md`
- **归档区**: `memory/archive/`

---

## 📝 版本历史

- **v4.6.2 (Current)**: 系统化重构。内置一键安装脚本，升级 Skill 至 v4.2 (增加降级策略)，完善项目结构。
- **v4.6.1**: 文档补全，代码清理，修复 MCP 协议兼容性。
- **v4.6.0**: 引入 Usage Tracking 和 Archive 机制。

---

**License:** MIT
