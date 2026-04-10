# 🛠️ Task Spec: v3.1 Health Check & Safe Rollback

**Assignee**: OpenCode Build Agent
**Reviewer**: OpenCode Code-Reviewer
**QA Sign-off**: CoPaw QA Agent

## 1. 背景
当前的 `install_copaw_plugin.py` 仅负责写入 `agent.json`。若写入后 MCP Server 无法启动或 JSON 格式损坏，会导致 Agent 启动失败。

## 2. 开发需求
请修改 `scripts/install_copaw_plugin.py` 实现以下功能：

1.  **自动健康检查 (Health Check)**:
    -   在修改 `agent.json` 并保存后，自动尝试验证新配置的有效性。
    -   验证逻辑：验证 JSON 是否能被 Python 标准库 `json.load` 成功读取且不包含语法错误。
2.  **原子回滚机制 (Atomic Rollback)**:
    -   如果健康检查失败，**必须**立即自动从 `.bak` 备份文件恢复 `agent.json`。
    -   恢复后再次验证，确保环境回到安全状态。
3.  **日志记录 (Logging)**:
    -   所有操作（备份、写入、检查、回滚）必须输出到 `~/.copaw/plugins/copaw-evolution-engine/install.log`。
    -   日志格式：`[TIMESTAMP] [LEVEL] Message`。

## 3. QA 红线 (Blocking Issues)
-   ❌ **禁止** 使用 `os.system` 或 `eval`，必须使用 `subprocess.run` 并设置 `timeout=10`。
-   ❌ **禁止** 在健康检查失败时退出而不回滚（必须保证环境一致性）。
-   ✅ 代码必须符合 PEP8，无未使用的 Import。

## 4. 交付物
-   更新后的 `scripts/install_copaw_plugin.py`。
-   更新后的 `MANIFEST.md`（增加日志路径说明）。
-   Git Commit & Push 到 `main` 分支。
