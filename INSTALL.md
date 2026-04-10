# 🚀 Installation Guide

## 1. Single Agent / Fresh Install (Interactive)
For a standard installation on a single workspace:
```bash
bash install.sh
```
*Follow the prompts to select your workspace.*

## 2. Multi-Agent Support (Automatic)
If you have multiple workspaces (agents) and want to enable Evolution Engine for **ALL** of them at once:
```bash
bash install.sh --all
```
*This script iterates through `~/.copaw/workspaces/*` and injects the MCP config into every `agent.json` safely.*

## 3. Silent / Scripted Install
For CI/CD or non-interactive setups:
```bash
bash install.sh --all --yes
```

## 🛡️ Safety Features
- **Backup**: Automatically creates `agent.json.bak` before modification.
- **Validation**: Checks JSON syntax after injection.
- **Rollback**: Reverts changes automatically if the injection fails validation.
