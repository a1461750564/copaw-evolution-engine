# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v3.2.0] - 2026-04-10
**Theme**: "Hermes Parity" - Advanced Memory & Self-Healing
> *Implemented sidecar architecture to bring FTS5 search and skill telemetry to CoPaw.*

### 🚀 Added
- **SQLite FTS5 Hybrid Search**: Real-time indexing of CoPaw `jsonl` logs with precision full-text search + LLM summarization.
- **Skill Telemetry (Self-Healing)**: Tracks `usage_count` and `fail_rate`. Auto-flags skills as `⚠️ DEPRECATED` if failure rate > 30%.
- **User Profile Extractor**: Analyzes conversation history to build a dynamic `user_profile.json`.
- **Modular Architecture**: Refactored monolith `mcp_server.py` into `lib/` package (`memory_crawler`, `skill_manager`, `user_modeler`).

### 🛡️ Security
- **Thread Safety**: Added `threading.Lock()` to all JSON and SQLite operations to prevent data corruption under concurrency.
- **Zero Dependencies**: Achieved Ollama API integration using ONLY Python `urllib` (no pip installs).

## [v3.1.0] - 2026-04-10
**Theme**: "Gatekeeper" & Enforcement
> *Addressed the critical issue where agents complete workflows without persisting SOPs.*

### 🚀 Added
- **Gatekeeper Tool (`check_evolution_status`)**: A new MCP tool that agents MUST call before reporting task completion.
- **Git-Based Heuristic**: The tool now checks `git status`. If code changed but no new Skill was created, it returns `🚨 BLOCK`.
- **SOUL.md Enforcement Hook**: Updated standard prompt instructions to mandate calling the Gatekeeper.

### 🛠️ Changed
- **mcp_server.py**: Refactored to support multiple tools (Create, Update, Check).
- **Install Script**: Improved error handling and added atomic backup logic.

### 🐛 Fixed
- **Silent SOP Loss**: Fixed the bug where complex tasks (like OpenCode integration) finished without creating a reusable Skill.
- **Context Limits**: Optimized tool descriptions to reduce token usage in the context window.

## [v3.0.0] - 2026-04-10 (Initial Release)
- **Framework-Native API**: Uses CoPaw REST API (`POST /skills`) instead of file manipulation.
- **Auto Versioning**: Automatically bumps versions in YAML frontmatter.
- **Zero Dependency**: Pure Python implementation.
