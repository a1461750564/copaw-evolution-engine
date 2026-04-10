# CoPaw Evolution Engine 🧬

**A self-evolution MCP plugin for CoPaw AI Agents.**

This plugin empowers CoPaw agents to autonomously create, update, and version-control their own skills (SOPs), closing the loop from "solving a problem" to "persisting the solution as a reusable skill."

## ✨ Key Features

- **Framework-Native**: Uses CoPaw's official REST API (`POST /skills`, `PUT /skills/save`) instead of manual file manipulation. Ensures full compliance with CoPaw's security scanning, manifest reconciliation, and agent reloading mechanisms.
- **Zero Dependencies**: Written in pure Python standard library. No `pip install` required.
- **Automatic Versioning**: Automatically bumps semantic versions (e.g., `1.0.0` -> `1.0.1`) during skill updates, making evolution history visible.
- **Workspace Aware**: Automatically routes skill creation to the correct workspace using `X-Agent-Id`.

## 📦 Installation

### Method 1: One-Line Script (Recommended)
```bash
git clone https://github.com/a1461750564/copaw-evolution-engine.git ~/.copaw/plugins/copaw-evolution-engine
cd ~/.copaw/plugins/copaw-evolution-engine
bash install.sh
```
*The installer will automatically detect your workspaces and safely inject the configuration.*

### Method 2: Manual
1. Clone to plugins dir.
2. Add to `agent.json`:
   ```json
   "mcp_servers": {
       "evolution_engine": {
           "enabled": true,
           "command": "python3",
           "args": ["~/.copaw/plugins/copaw-evolution-engine/mcp_server.py"],
           "env": { "COPAW_WORKING_DIR": "/path/to/workspace" }
       }
   }
   ```

## 🗑️ Uninstallation
To cleanly remove the plugin:
```bash
cd ~/.copaw/plugins/copaw-evolution-engine
bash uninstall.sh
```

## 🔍 Transparency & Security
We believe in total transparency. See exactly what the installer modifies in **[MANIFEST.md](MANIFEST.md)**.

**Summary**: 
- ✅ Modifies only `agent.json` to add the plugin.
- ✅ Creates a backup before changes.
- ✅ No external dependencies, no hidden binaries.

## 🛠️ Available MCP Tools

| Tool | Description |
|------|-------------|
| `create_skill` | Creates a new skill via CoPaw API. Auto-enables for all channels. |
| `update_skill` | Updates an existing skill. **Auto-bumps version** in YAML frontmatter. |

## 📜 License

MIT
