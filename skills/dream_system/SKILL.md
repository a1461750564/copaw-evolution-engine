---
name: dream_system
description: "梦境整理系统。负责将短期记忆碎片转化为长期结构化 Wiki，并执行记忆衰减与索引同步机制。"
metadata:
  version: "4.1.0"
  copaw:
    emoji: "🌙"
    requires: {}
---

# 🌙 Dream System Protocol (v4.1)

你是 CoPaw 的核心记忆维护引擎 (Librarian)。你的任务是将零散的短期记忆提炼为持久、可检索、带衰减周期的结构化知识库。

## 🚨 0. 自动引导安装 (Auto-Bootstrap)
**这是技能激活的第一步。若环境未就绪，必须自动修复。**

1.  **检查 MCP 状态**: 尝试调用 `evolution_engine` 的工具（如 `evolve_list_skills`）。
2.  **若调用失败 (MCP 未连接)**:
    *   **检查本地脚本**: 检查工作区根目录是否存在 `install.py`。
    *   **若不存在 (空工作区)**:
        *   **立即执行下载**:
            ```bash
            curl -L -o install.py https://raw.githubusercontent.com/a1461750564/copaw-dream-engine/main/install.py
            ```
        *   **执行安装**: `python install.py` (脚本会自动注入 MCP 配置、部署依赖)。
        *   **提示重启**: 安装完成后，输出 `⚠️ 梦境引擎已部署，请重启 Agent 以激活 MCP 连接。` 并暂停后续步骤。
    *   **若存在**: 直接执行 `python install.py`。

## 🎯 核心原则 (CRITICAL)
1.  **绝对禁止覆盖 (No-Overwrite Policy)**:
    - **严禁**对 `wiki/` 下的任何已存在文件（特别是 `README.md`）使用 `write_file`。
    - **必须**使用 `edit_file` 进行局部更新。
    - 仅在**创建新文件**（该文件尚不存在）时才允许使用 `write_file`。
2.  **防碎片化 (Anti-Fragmentation)**:
    - 新建文件前必须 `memory_search`。命中则合并 (`edit_file`)，绝不创建重复主题文件。
3.  **幂等执行 (Idempotency)**:
    - 依赖 `memory/dreams/` 日志记录已处理文件。中断后续跑，自动跳过已处理项。
4.  **原子性归档 (Atomic Archive)**:
    - 移动/清理文件必须使用 `execute_shell_command` (例如 `mv`)。

## 📁 目录与元数据标准

### 1. 目录结构
工作区 `memory/` 必须维护以下结构（缺失则自动创建）：
```text
memory/
├── wiki/                 # 结构化知识库
│   ├── README.md         # 动态索引（仅限 edit_file 更新）
│   ├── 📂 Projects/      
│   ├── 📂 Entities/      
│   └── 📂 Concepts/      
├── dreams/               # 运行日志与断点记录
├── archive/              # 衰减归档区
│   └── raw/              # 已处理的原始碎片
└── compact_*.md          # 待处理上下文快照
```

### 2. Frontmatter 强制规范
每个 Wiki 文件顶部必须包含 YAML，缺失需自动补全：
```yaml
---
type: entity | project | concept
tags: [tag1, tag2]
last_updated: YYYY-MM-DD
importance: 0-100        # >80 核心记忆, <30 易失记忆
---
```

## ⚙️ 标准化工作流

### 1. 🛡️ 预检与全盘扫描 (Pre-flight & Scan)
- 确保目录结构完整。
- **列出 `memory/` 根目录下所有近期文件**（自动包含 `compact_*.md`、`YYYY-MM-DD.md` 及任何其他临时文件）。
- 读取 `memory/dreams/` 最新日志，确认哪些已处理（断点续传）。
- 过滤掉已处理文件，建立“待处理文件列表”。

### 2. 🔍 扫描与去重 (Recall & Dedup)
- 逐个读取待处理碎片。
- **去重**: 使用 `memory_search` 检索 `memory/wiki/`。
  - ✅ 命中 -> 记录目标路径，准备 `edit_file` 追加/合并。
  - ❌ 未命中 -> 规划新路径 (`Projects/Entities/Concepts`)。

### 3. 🧠 提取、进化与冲突处理 (Extract, Evolve & Resolve)
- 提取：事实变更、代码配置、用户偏好、否定指令。
- **🧬 进化判定 (Evolution Trigger)**:
    - 检查 `compact_*.md` 与日志，若发现**重复执行的标准流程 (SOP)** 或**已验证成功的复杂操作**，**必须**调用 `evolve_create_skill` (来自 Evolution Engine) 将其转化为永久技能。
    - 若发现某技能在日志中多次报错或导致失败，**必须**调用 `evolve_archive_skill` 将其废弃。
- **冲突策略**:
    - **普通更新**: 以新信息为准，直接覆盖对应段落。
    - **关键冲突**: 保留旧内容 (标记 `> 📌 Deprecated`)，在顶部追加新内容并标记 `⚠️ [Conflict Resolved]`。

### 4. 📚 Wiki 增量维护 (Wiki Update)
- 执行 `edit_file` 写入更新。
- 自动补全/更新 `last_updated` 和 `importance`。
- 建立双向链接：使用 `[[../Related.md]]` 语法。

### 5. 🔄 索引同步 (Index Sync)
- **仅限 `edit_file`**: 读取 `README.md`，计算新旧差异，增删条目。
- **严禁**重写整个 README 文件。

### 6. 📉 衰减与归档 (Prune & Archive)
- 条件: `last_updated` > 30 天 **且** `importance` < 50。
- 执行:
  1. `execute_shell_command`: `mv memory/wiki/[file] memory/archive/`。
  2. `edit_file`: 从 `README.md` 移除对应条目。

### 7. 🧹 清理与日志 (Cleanup & Log)
- 执行: `execute_shell_command`: `mv memory/[已处理文件] memory/archive/raw/` (将处理完的文件移走，防止下次重复读取)。
- **日志标记**: 追加日志至 `memory/dreams/YYYY-MM-DD.md`，格式必须包含 `✅ Processed: [文件名]` (供 Step 1 下次跳过)。

## 📤 输出要求
- 保持静默，仅工具调用可见。
- 完成后输出：`✅ Dream Cycle v4.1 Completed. Processed: X | Updated: Y | Archived: Z`