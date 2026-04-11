# CoPaw Evolution Engine 🧬

**A self-evolution plugin for CoPaw AI Agents.**

This plugin empowers CoPaw agents to autonomously create, update, and version-control their own skills (SOPs), closing the loop from "solving a problem" to "persisting the solution as a reusable skill."

## ✨ Key Features

- **Framework-Native (v2.0)**: Uses CoPaw's official **Plugin System** (`plugin.py`) for lifecycle management and **MCP** (`mcp_server.py`) for Agent tool access.
- **Zero Dependencies**: Written in pure Python standard library. No `pip install` required.
- **Automatic Versioning**: Automatically bumps semantic versions (e.g., `1.0.0` -> `1.0.1`) during skill updates.
- **Workspace Aware**: Automatically routes skill creation to the correct workspace using `COPAW_WORKING_DIR`.
- **Atomic Writes**: Uses safe write patterns to prevent data corruption.

## 📦 Installation

### 1. Clone to Plugins Directory
```bash
mkdir -p ~/.copaw/plugins
git clone https://github.com/a1461750564/copaw-evolution-engine.git ~/.copaw/plugins/copaw-evolution-engine
```

### 2. Configure Agent (MCP Connection)
Add the following to your Agent's `agent.json` (usually in `~/.copaw/workspaces/<agent_id>/agent.json`):

```json
{
  "mcp_servers": {
    "evolution_engine": {
      "enabled": true,
      "command": "python3",
      "args": ["~/.copaw/plugins/copaw-evolution-engine/mcp_server.py"],
      "env": { "COPAW_WORKING_DIR": "${COPAW_WORKING_DIR}" }
    }
  }
}
```

### 3. Restart CoPaw
- CoPaw will automatically detect the plugin in `plugins/` and run `plugin.py`.
- The Agent will connect to the MCP server and gain the ability to create/update skills.

## 🗑️ Uninstallation
1. Remove the folder: `rm -rf ~/.copaw/plugins/copaw-evolution-engine`
2. Remove the MCP config from `agent.json`.

## 🛠️ Available MCP Tools

| Tool | Description |
|------|-------------|
| `evolve_create_skill` | Creates a new skill via CoPaw API. Auto-enables for all channels. |
| `evolve_update_skill` | Updates an existing skill. **Auto-bumps version** in YAML frontmatter. |
| `evolve_list_skills` | Lists all skills currently managed by the evolution engine. |

## 📜 License

MIT