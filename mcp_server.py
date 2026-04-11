#!/usr/bin/env python3
"""
CoPaw Evolution Engine - MCP Server v2.0
Exposes tools for agents to create, track, and prune skills.
"""
import sys
import os
import json

# Add project root to path to import lib
sys.path.append(os.path.dirname(__file__))

try:
    from lib.skill_manager import (
        create_skill, update_skill, list_skills, 
        track_usage, archive_skill, get_skill_stats
    )
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
        "name": "evolve_report_usage",
        "description": "Report whether a skill execution was successful or failed. Critical for evolutionary feedback loop."
    },
    {
        "name": "evolve_archive_skill",
        "description": "Archive a skill that is outdated or useless. (Natural Selection)."
    },
    {
        "name": "evolve_list_skills",
        "description": "List all skills currently managed by the evolution engine."
    },
    {
        "name": "evolve_get_stats",
        "description": "Get usage statistics and success rates for skills."
    }
]

# ============================================================
# Tool Handlers
# ============================================================
def handle_create_skill(args):
    name = args.get("name", "").lower().replace(" ", "-")
    description = args.get("description", "Auto-evolved skill.")
    content = args.get("content", "")
    
    if not name: raise ValueError("Skill 'name' is required")
    if not content: raise ValueError("Skill 'content' is required")
        
    return create_skill(name=name, description=description, content=content)

def handle_update_skill(args):
    name = args.get("name", "").lower().replace(" ", "-")
    content = args.get("content", "")
    
    if not name: raise ValueError("Skill 'name' is required")
    if not content: raise ValueError("Skill 'content' is required")
        
    return update_skill(name=name, content=content)

def handle_report_usage(args):
    name = args.get("name", "").lower().replace(" ", "-")
    success = args.get("success", True)
    
    if not name: raise ValueError("Skill 'name' is required")
    
    return track_usage(skill=name, success=success)

def handle_archive_skill(args):
    name = args.get("name", "").lower().replace(" ", "-")
    
    if not name: raise ValueError("Skill 'name' is required")
    
    return archive_skill(name=name)

def handle_list_skills(args):
    return list_skills()

def handle_get_stats(args):
    skill = args.get("name", "")
    return get_skill_stats(skill=skill if skill else None)

TOOL_MAP = {
    "evolve_create_skill": handle_create_skill,
    "evolve_update_skill": handle_update_skill,
    "evolve_report_usage": handle_report_usage,
    "evolve_archive_skill": handle_archive_skill,
    "evolve_list_skills": handle_list_skills,
    "evolve_get_stats": handle_get_stats
}

# ============================================================
# MCP Server Loop
# ============================================================
def handle_request(req: dict) -> dict:
    method = req.get("method", "")
    req_id = req.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0", 
            "id": req_id, 
            "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}}
        }
    
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    
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
    print("[EvolutionEngine] MCP Server v2.0 Started.", file=sys.stderr)
    for line in sys.stdin:
        try:
            req = json.loads(line.strip())
            resp = handle_request(req)
            if resp:
                print(json.dumps(resp), flush=True)
        except Exception as e:
            print(f"[MCP Error] {e}", file=sys.stderr)