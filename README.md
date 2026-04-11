# 🧬 CoPaw Evolution Engine

**Version:** 4.6.1  
**Type:** CoPaw Plugin + MCP Server  
**Inspired by:** NousResearch Hermes Agent (Self-improving Agents)

一个用于 CoPaw 智能体的**自进化引擎**。它不仅允许 Agent 在运行时创建和更新技能（Skills），还引入了**使用反馈**和**自然选择（归档）**机制，让 Agent 的知识库能够像生物一样优胜劣汰。

---

## 🌟 核心特性

1.  **自动进化 (Skill Evolution)**: Agent 可以在解决新问题后，调用 `evolve_create_skill` 将经验固化为永久技能。
2.  **反馈闭环 (Feedback Loop)**: 通过 `evolve_report_usage` 记录技能的成功率，让 Agent 知道哪个工具好用。
3.  **自然选择 (Pruning)**: 失败率高的技能会被自动标记或归档，防止“劣币驱逐良币”。
4.  **无缝集成**: 符合 CoPaw 官方插件规范，通过 MCP 协议提供工具调用。

---

## 📦 安装 (CoPaw 插件)

### 1. 克隆插件到本地

```bash
# 进入 CoPaw 插件目录
mkdir -p ~/.copaw/plugins
cd ~/.copaw/plugins

# 克隆仓库
git clone https://github.com/a1461750564/copaw-evolution-engine.git
```

### 2. 配置 Agent

在你的 CoPaw Agent 配置文件（通常是 `agent.json`）中添加 MCP 客户端配置：

```json
"mcp": {
  "clients": {
    "evolution_engine": {
      "name": "evolution_engine",
      "description": "CoPaw Evolution Engine MCP Server",
      "enabled": true,
      "transport": "stdio",
      "command": "/Users/jiaye/.copaw/venv/bin/python3",  // 请替换为你的 venv 路径
      "args": [
        "/Users/jiaye/.copaw/plugins/copaw-evolution-engine/mcp_server.py"
      ],
      "cwd": "/Users/jiaye/.copaw/plugins/copaw-evolution-engine"
    }
  }
}
```

### 3. 重启 CoPaw
重启后，Agent 的工具列表中会出现 `evolve_*` 系列工具。

---

## 🛠️ MCP 工具列表

Agent 可以调用以下工具来实现自我进化：

| 工具名称 | 描述 |
| :--- | :--- |
| **`evolve_create_skill`** | 从内容创建新技能。Agent 学习新 SOP 后调用。 |
| **`evolve_update_skill`** | 更新现有技能（自动处理版本控制）。 |
| **`evolve_report_usage`** | **反馈**。报告技能调用的成功/失败情况。 |
| **`evolve_archive_skill`** | **淘汰**。归档过时或高频失败的技能。 |
| **`evolve_list_skills`** | 列出当前管理的所有技能及其状态。 |
| **`evolve_get_stats`** | 查看技能的使用统计（成功率、调用次数）。 |

---

## 🏗️ 架构说明

本项目遵循 CoPaw 官方规范：
*   **`plugin.json`**: 插件元数据。
*   **`plugin.py`**: 插件生命周期入口（负责目录初始化）。
*   **`mcp_server.py`**: 基于 `FastMCP` 构建的标准 MCP 服务。
*   **`lib/`**: 核心逻辑库（原子写入、版本控制、冲突解决）。

---

## 📝 版本历史

- **v4.6.1**: 文档补全，代码清理，使用 FastMCP 协议，修复插件 API 兼容性。
- **v4.6.0**: 引入 Usage Tracking 和 Archive 机制。
- **v4.5.1**: 初始核心库迁移 (Skill Manager)。

---

**License:** MIT
