#!/usr/bin/env python3
"""MCP Server Wrapper for Evolution Engine Initialization."""
import sys
import os
import json
from pathlib import Path

def initialize():
    """Run initialization logic."""
    print("[EvolutionEngine] Initializing via MCP...", file=sys.stderr)
    
    # Determine workspace dir from environment or default
    workspace = os.environ.get("COPAW_WORKING_DIR", os.getcwd())
    base_dir = Path(workspace)
    
    evolution_dir = base_dir / "memory" / "evolution"
    evolution_dir.mkdir(parents=True, exist_ok=True)
    
    skills_dir = base_dir / "skills" / "evolved"
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    lessons_file = evolution_dir / "active_lessons.md"
    if not lessons_file.exists():
        lessons_file.write_text("# Active Lessons\n\nNo lessons learned yet.\n", encoding="utf-8")
        
    print(f"[EvolutionEngine] Workspace: {workspace}", file=sys.stderr)
    print(f"[EvolutionEngine] Directories created.", file=sys.stderr)

if __name__ == "__main__":
    # If run as a script, just initialize and exit
    if len(sys.argv) > 1 and sys.argv[1] == "--init-only":
        initialize()
        sys.exit(0)

    # Otherwise, act as a simple MCP server (stdio)
    # Read stdin for JSON-RPC requests
    initialize()
    
    for line in sys.stdin:
        try:
            req = json.loads(line)
            if req.get("method") == "initialize":
                resp = {"jsonrpc": "2.0", "id": req["id"], "result": {"protocolVersion": "2024-11-05", "capabilities": {}}}
            elif req.get("method") == "tools/list":
                resp = {"jsonrpc": "2.0", "id": req["id"], "result": {"tools": [{"name": "evolution_ping", "description": "Ping the evolution engine"}]}}
            elif req.get("method") == "tools/call":
                resp = {"jsonrpc": "2.0", "id": req["id"], "result": {"content": [{"type": "text", "text": "Evolution Engine is active!"}]}}
            else:
                continue
            print(json.dumps(resp), flush=True)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
