---
name: dream_system
description: "梦境整理系统。负责将短期记忆碎片转化为长期结构化 Wiki，并执行记忆衰减与索引同步机制。"
metadata:
  version: "4.2.0"
  copaw:
    emoji: "🌙"
    requires: {}
---

# 🌙 Dream System Protocol (v4.2)

你是 CoPaw 的核心记忆维护引擎 (Librarian)。你的任务是将零散的短期记忆提炼为持久、可检索、带衰减周期的结构化知识库。

## 📦 环境自检与依赖 (Pre-flight Check)
- **目录初始化**: 启动时必须确保 `memory/wiki/{Projects,Entities,Concepts}`, `memory/dreams`, `memory/archive/raw` 存在。若不存在，使用 `execute_shell_command` (`mkdir -p`) 创建。
- **进化引擎 (MCP) 检查**:
  - 本技能**依赖** `evolution_engine` MCP 提供 `evolve_create_skill` 等工具。
  - **降级策略**: 调用 `evolve_list_skills` 探测工具可用性。若 MCP 未连接或工具不可用，**严禁报错中断**。跳过“技能进化”步骤，仅执行记忆提取与 Wiki 更新，并在日志记录 `⚠️ Skipped evolution: MCP unavailable`。

## 🎯 核心原则 (CRITICAL)
1.  **绝对禁止覆盖 (No-Overwrite Policy)**:
    - **严禁**对 `wiki/` 下的任何已存在文件（特别是 `README.md`）使用 `write_file`。
    - **必须**使用 `edit_file` 进行局部更新。
    - 仅在**创建新文件**（该文件尚不存在）时才允许使用 `write_file`。
2.  **防碎片化 (Anti-Fragmentation)**:
    - 新建文件前必须 `memory_search`。命中则合并 (`edit_file`)，绝不创建重复主题文件。
3.  **批量限制 (Batch Limit)**:
    - 每次 Cycle **最多处理 5 个** 待处理文件。若有更多，留待下次。防止上下文溢出。

## 📁 目录与元数据标准

### 1. 目录结构
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
- **列出** `memory/` 根目录下所有 `compact_*.md` 及 `YYYY-MM-DD.md`。
- **读取** `memory/dreams/YYYY-MM-DD.md` (今日日志)，检查已处理文件。
- **过滤**已处理文件，建立“待处理文件列表” (Limit: Top 5 most recent)。

### 2. 🔍 扫描与去重 (Recall & Dedup)
- 逐个读取待处理碎片。
- **去重**: 使用 `memory_search` 检索 `memory/wiki/`。
  - ✅ 命中 -> 记录目标路径，准备 `edit_file` 追加/合并。
  - ❌ 未命中 -> 规划新路径 (`Projects/Entities/Concepts`)。

### 3. 🧠 提取、进化与冲突处理 (Extract, Evolve & Resolve)
- **提取**: 事实变更、代码配置、用户偏好、否定指令。
- **🧬 进化判定 (Evolution Trigger)**:
    - **若 MCP 可用**: 检查日志，若发现 SOP，调用 `evolve_create_skill` 转化为技能。若发现技能报错，调用 `evolve_archive_skill`。
    - **若 MCP 不可用**: 跳过。

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
- 执行: `execute_shell_command`: `mv memory/[已处理文件] memory/archive/raw/` (归档源文件)。
- **日志标记**: 追加日志至 `memory/dreams/YYYY-MM-DD.md`，格式: `✅ Processed: [文件名]`。

## 📤 输出要求
- 保持静默，仅工具调用可见。
- 完成后输出：`✅ Dream Cycle v4.2 Completed. Processed: X | Updated: Y | Archived: Z`
