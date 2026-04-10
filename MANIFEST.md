# 🔍 Installation Manifest

This document transparently describes what the **CoPaw Evolution Engine** installer does to your system.

## 📥 What Happens During Install (`bash install.sh`)

The installer **only** reads and writes the following files:

| Action | Target File | Purpose |
|:---|:---|:---|
| **Read** | `~/.copaw/workspaces/*/agent.json` | Detects active workspaces and reads current MCP config. |
| **Write** | `~/.copaw/workspaces/*/agent.json` | Injects `evolution_engine` block into `mcp_servers`. <br> *Does not overwrite other settings.* |
| **Backup** | `~/.copaw/workspaces/*/agent.json.bak` | Creates a backup before modifying JSON. |
| **Write** | `~/.copaw/plugins/copaw-evolution-engine/install.log` | Appends detailed installation log (v3.1+). |

### ❌ What It Does NOT Do
- It does **NOT** download external binaries.
- It does **NOT** modify CoPaw's core `venv` or source code.
- It does **NOT** access your API keys or sensitive data.
- It does **NOT** delete existing skills.

## 🛡️ Post-Install Health Check (v3.1+)

After injecting the configuration, the installer automatically runs health checks:

| Check | Method | Purpose |
|:---|:---|:---|
| **JSON Validation** | `json.load()` on agent.json | Verifies the modified config is parseable. |
| **Entry Verification** | Key lookup in `mcp_servers` | Confirms `evolution_engine` block exists. |
| **Syntax Check** | `subprocess.run(py_compile)` on mcp_server.py | Ensures the MCP server script has no syntax errors. |
| **Tool Load Check** | `subprocess.run` import test on mcp_server.py | Validates that MCP tool schemas load correctly. |

### Automatic Rollback (v3.1+)

If **any** health check fails, the installer automatically:

1. **Validates the backup**: Confirms `.bak` file is valid JSON before restoring.
2. **Atomic restore**: Writes to `.tmp` first, then uses `os.replace()` for atomic swap.
3. **Logs the rollback**: Records rollback status to `install.log`.
4. **Reports status**: Warns the user if rollback succeeded or if manual intervention is needed.

**Rollback guarantee**: The backup file is validated before use, preventing secondary corruption. If the backup itself is corrupt, a CRITICAL log entry is written for manual intervention.

## 🗑️ What Happens During Uninstall (`bash uninstall.sh`)

| Action | Target File | Purpose |
|:---|:---|:---|
| **Read** | `~/.copaw/workspaces/*/agent.json` | Locates the `evolution_engine` configuration block. |
| **Write** | `~/.copaw/workspaces/*/agent.json` | Removes the `evolution_engine` block cleanly. |
| **Optional** | `~/.copaw/workspaces/*/skills/evolved/` | Only deleted if you explicitly choose "y" during uninstall. |

## 🛡️ Security & Trust
- **Open Source**: All code is visible in this repository. You can audit `scripts/install_copaw_plugin.py` to verify the logic.
- **Atomic Writes**: The installer uses Python's standard JSON handling to ensure your `agent.json` is never corrupted.
- **No os.system**: All subprocess calls use `subprocess.run` with explicit argument lists (no shell injection risk).
- **Reversible**: The uninstaller completely removes the plugin's footprint from CoPaw.

## 📋 Log Files

| File | Purpose |
|:---|:---|
| `~/.copaw/plugins/copaw-evolution-engine/install.log` | Detailed installation log including health check results and rollback events. Appended on each install run. |

---

*Last updated: 2026-04-10 (v3.1)*
