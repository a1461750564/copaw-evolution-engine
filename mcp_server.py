#!/usr/bin/env python3
"""
CoPaw Evolution Engine - MCP Server
Exposes tools for agents to create and update skills.
"""
import sys
import os
import json

# Add project root to path to import lib
sys.path.append(os.path.dirname(__file__))

try:
    from lib.skill_manager import create_skill, update_skill, list_skills
except ImportError as e:
    print(f"[MCP Error] Failed to import lib: {e}", file=sys.stderr)
    sys.exit(1)

# ============================================================
# Tool Definitions
# ============================================================
TOOLS = [
    {
        "name": "evolve_create_skill",
        "description": "Create a new CoPaw skill from scratch. Used when an Agent learns a new capability."
    },
    {
        "name": "evolve_update_skill",
        "description": "Update an existing skill. Automatically handles versioning (v1.0.0 -> v1.0.1) and backups."
    },
    {
        "name": "evolve_list_skills",
        "description": "List all skills currently managed by the evolution engine."
    }
]

# ============================================================
# Tool Handlers
# ============================================================
def handle_create_skill(args):
    name = args.get("name", "").lower().replace(" ", "-")
    description = args.get("description", "Auto-evolved skill.")
    content = args.get("content", "")
    
    if not name:
        raise ValueError("Skill 'name' is required")
    if not content:
        raise ValueError("Skill 'content' is required")
        
    return create_skill(name=name, description=description, content=content)

def handle_update_skill(args):
    name = args.get("name", "").lower().replace(" ", "-")
    content = args.get("content", "")
    
    if not name:
        raise ValueError("Skill 'name' is required")
    if not content:
        raise ValueError("Skill 'content' is required")
        
    return update_skill(name=name, content=content)

def handle_list_skills(args):
    return list_skills()

TOOL_MAP = {
    "evolve_create_skill": handle_create_skill,
    "evolve_update_skill": handle_update_skill,
    "evolve_list_skills": handle_list_skills
}

# ============================================================
# MCP Server Loop
# ============================================================
def handle_request(req: dict) -> dict:
    method = req.get("method", "")
    req_id = req.get("id")
    
    # Initialization handshake
    if method == "initialize":
        return {
            "jsonrpc": "2.0", 
            "id": req_id, 
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}}
            }
        }
    
    # List available tools
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    
    # Execute tool
    if method == "tools/call":
        tool_name = req["params"].get("name")
        tool_args = req["params"].get("arguments", {})
        
        if tool_name in TOOL_MAP:
            try:
                result = TOOL_MAP[tool_name](tool_args)
                return {
                    "jsonrpc": "2.0", 
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0", 
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {str(e)}"}], 
                        "isError": True
                    }
                }
        else:
            return {
                "jsonrpc": "2.0", 
                "id": req_id, 
                "error": {"code": -32601, "message": f"Tool {tool_name} not found"}
            }
    
    return None

if __name__ == "__main__":
    print("[EvolutionEngine] MCP Server Started. Waiting for requests...", file=sys.stderr)
    for line in sys.stdin:
        try:
            req = json.loads(line.strip())
            resp = handle_request(req)
            if resp:
                print(json.dumps(resp), flush=True)
        except Exception as e:
            print(f"[MCP Error] {e}", file=sys.stderr)