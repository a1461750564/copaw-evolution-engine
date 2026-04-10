# 🔍 Installation Manifest

This document transparently describes what the **CoPaw Evolution Engine** installer does to your system.

## 📥 What Happens During Install (`bash install.sh`)

The installer **only** reads and writes the following files:

| Action | Target File | Purpose |
|:---|:---|:---|
| **Read** | `~/.copaw/workspaces/*/agent.json` | Detects active workspaces and reads current MCP config. |
| **Write** | `~/.copaw/workspaces/*/agent.json` | Injects `evolution_engine` block into `mcp_servers`. <br> *Does not overwrite other settings.* |
| **Backup** | `~/.copaw/workspaces/*/agent.json.bak` | Creates a backup before modifying JSON. |

### ❌ What It Does NOT Do
- It does **NOT** download external binaries.
- It does **NOT** modify CoPaw's core `venv` or source code.
- It does **NOT** access your API keys or sensitive data.
- It does **NOT** delete existing skills.

## 🗑️ What Happens During Uninstall (`bash uninstall.sh`)

| Action | Target File | Purpose |
|:---|:---|:---|
| **Read** | `~/.copaw/workspaces/*/agent.json` | Locates the `evolution_engine` configuration block. |
| **Write** | `~/.copaw/workspaces/*/agent.json` | Removes the `evolution_engine` block cleanly. |
| **Optional** | `~/.copaw/workspaces/*/skills/evolved/` | Only deleted if you explicitly choose "y" during uninstall. |

## 🛡️ Security & Trust
- **Open Source**: All code is visible in this repository. You can audit `scripts/install_copaw_plugin.py` to verify the logic.
- **Atomic Writes**: The installer uses Python's standard JSON handling to ensure your `agent.json` is never corrupted.
- **Reversible**: The uninstaller completely removes the plugin's footprint from CoPaw.
