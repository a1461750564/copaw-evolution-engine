# CoPaw Evolution Engine 🧬

**A self-evolution MCP plugin for CoPaw AI Agents.**

This plugin empowers CoPaw agents to autonomously create, update, and version-control their own skills (SOPs), closing the loop from "solving a problem" to "persisting the solution as a reusable skill."

## ✨ Key Features

- **Framework-Native**: Uses CoPaw's official REST API (`POST /skills`, `PUT /skills/save`) instead of manual file manipulation. Ensures full compliance with CoPaw's security scanning, manifest reconciliation, and agent reloading mechanisms.
- **Zero Dependencies**: Written in pure Python standard library. No `pip install` required.
- **Automatic Versioning**: Automatically bumps semantic versions (e.g., `1.0.0` -> `1.0.1`) during skill updates, making evolution history visible.
- **Workspace Aware**: Automatically routes skill creation to the correct workspace using `X-Agent-Id`.

## 🚀 Installation

1. Copy the `copaw-evolution-engine` folder to your CoPaw plugins directory:
   ```bash
   cp -r copaw-evolution-engine ~/.copaw/plugins/
   ```
2. Add to your `agent.json` MCP configuration:
   ```json
   "evolution_engine": {
     "enabled": true,
     "command": "/path/to/python3",
     "args": ["~/.copaw/plugins/copaw-evolution-engine/mcp_server.py"],
     "env": {
       "COPAW_WORKING_DIR": "/path/to/your/workspace"
     }
   }
   ```
3. Restart CoPaw. The agent will now have `create_skill` and `update_skill` tools.

## 📂 Architecture

Inspired by advanced agent frameworks like [Hermes Agent](https://github.com/NousResearch/hermes-agent), this plugin adopts a **"Framework-First"** philosophy:
- Instead of hacking files directly, it delegates to the CoPaw Core API.
- This guarantees that every evolved skill is scanned, indexed, and reloaded exactly as if it were installed from the official skill hub.

## 🛠️ Available MCP Tools

| Tool | Description |
|------|-------------|
| `create_skill` | Creates a new skill via CoPaw API. Auto-enables for all channels. |
| `update_skill` | Updates an existing skill. **Auto-bumps version** in YAML frontmatter. |

## 📜 License

MIT
