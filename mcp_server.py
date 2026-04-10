#!/usr/bin/env python3
"""
CoPaw Evolution Engine - MCP Server (v3.0 Framework-Native)

This server provides tools for AI agents to evolve skills within the CoPaw framework.
Instead of manipulating files directly, it uses CoPaw's official REST API to ensure
full compliance with the framework's lifecycle (validation, security scanning, manifest reconciliation).

Zero external dependencies. Uses only Python standard library.
"""

import json
import logging
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, Optional, List

# --- Configuration ---
COPAW_API_BASE = os.environ.get("COPAW_API_BASE", "http://127.0.0.1:8088/api")
COPAW_WORKING_DIR = os.environ.get("COPAW_WORKING_DIR", "")

def get_agent_id() -> str:
    """Infer Agent ID from the workspace directory name."""
    if COPAW_WORKING_DIR:
        return Path(COPAW_WORKING_DIR).name
    return "default"

logger = logging.getLogger("evolution_engine")
logger.setLevel(logging.DEBUG)

# --- Schema Definitions ---
TOOLS = [
    {
        "name": "create_skill",
        "description": "Create a new skill in the CoPaw workspace using the official API. The skill content MUST include valid YAML frontmatter with 'name' and 'description' fields.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The skill name (e.g., 'pdf-processing-sop')."
                },
                "description": {
                    "type": "string",
                    "description": "Short summary of what this skill does."
                },
                "content": {
                    "type": "string",
                    "description": "The full Markdown content for SKILL.md. MUST start with YAML frontmatter containing 'name' and 'description'."
                }
            },
            "required": ["name", "description", "content"]
        }
    },
    {
        "name": "update_skill",
        "description": "Update an existing skill's content via the official API.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the skill to update."
                },
                "content": {
                    "type": "string",
                    "description": "The new Markdown content for SKILL.md."
                }
            },
            "required": ["name", "content"]
        }
    }
]

def call_copaw_api(method: str, path: str, payload: Optional[Dict[str, Any]] = None, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Make a request to the CoPaw REST API."""
    url = f"{COPAW_API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    # Inject Agent ID for workspace routing
    req.add_header("X-Agent-Id", get_agent_id())
    
    if extra_headers:
        for k, v in extra_headers.items():
            req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return {"error": True, "status": e.code, "message": body}
    except Exception as e:
        return {"error": True, "message": str(e)}

def bump_version(content: str) -> str:
    """Automatically increments the semantic version in YAML frontmatter."""
    # Regex for version: major.minor.patch
    ver_re = re.compile(r'^version:\s*"?(\d+)\.(\d+)\.(\d+)"?\s*$', re.MULTILINE)
    match = ver_re.search(content)
    
    if match:
        major, minor, patch = map(int, match.groups())
        patch += 1
        new_ver = f"{major}.{minor}.{patch}"
        new_content = ver_re.sub(f'version: "{new_ver}"', content)
        return new_content
    else:
        # If no version found, add it after description
        # Look for description line
        desc_re = re.compile(r'^(description:\s*.*\n)', re.MULTILINE)
        match_desc = desc_re.search(content)
        if match_desc:
            insert_pos = match_desc.end()
            return content[:insert_pos] + 'version: "1.0.0"\n' + content[insert_pos:]
        else:
            # Fallback: just return content, API might fail or use default
            return content

def validate_frontmatter(content: str) -> bool:
    """Basic check to ensure content has valid frontmatter with name and description."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return False
    fm = match.group(1)
    has_name = bool(re.search(r'^name:\s*.+', fm, re.MULTILINE))
    has_desc = bool(re.search(r'^description:\s*.+', fm, re.MULTILINE))
    return has_name and has_desc

def tool_create_skill(arguments: Dict[str, Any]) -> Dict[str, Any]:
    name = arguments.get("name", "")
    description = arguments.get("description", "")
    content = arguments.get("content", "")
    
    if not name or not description:
        return {"error": "Name and description are required."}
    if not validate_frontmatter(content):
        return {"error": "SKILL.md content must start with YAML frontmatter containing 'name' and 'description'."}
        
    # Ensure frontmatter matches provided name/description
    # CoPaw API will use frontmatter, so we must guarantee consistency
    # (In a real scenario, we'd parse and patch, but for simplicity we trust the agent to provide correct content)

    payload = {
        "name": name,
        "content": content,
        "enable": True,  # Automatically enable the evolved skill
        "channels": ["all"]
    }
    
    result = call_copaw_api("POST", "/skills", payload)
    
    if result.get("error"):
        return {"status": "failed", "detail": result}
    
    return {
        "status": "success",
        "message": f"Skill '{name}' created and enabled via CoPaw API.",
        "api_response": result
    }

def tool_update_skill(arguments: Dict[str, Any]) -> Dict[str, Any]:
    name = arguments.get("name", "")
    content = arguments.get("content", "")
    
    if not name:
        return {"error": "Skill name is required."}
    
    # --- AUTO-EVOLUTION LOGIC ---
    # Automatically bump version to make evolution visible
    evolved_content = bump_version(content)
    
    payload = {
        "name": name,
        "content": evolved_content
    }
    
    # Call API with Agent ID routing
    result = call_copaw_api("PUT", "/skills/save", payload)
    
    if result.get("error"):
        return {"status": "failed", "detail": result}
        
    return {
        "status": "success",
        "message": f"Skill '{name}' updated to new version via CoPaw API.",
        "api_response": result
    }

# --- MCP Server Loop ---
def main():
    logger.info("Evolution Engine MCP Server v3.0 starting...")
    
    # Send initialization response
    init_response = {
        "jsonrpc": "2.0",
        "id": 0,  # Will be overwritten by actual request ID
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "copaw-evolution-engine",
                "version": "3.0.0"
            }
        }
    }
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            method = request.get("method")
            req_id = request.get("id")
            
            if method == "initialize":
                # Respond to initialization
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "copaw-evolution-engine", "version": "3.0.0"}
                    }
                }
                print(json.dumps(response), flush=True)
                
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS}
                }
                print(json.dumps(response), flush=True)
                
            elif method == "tools/call":
                tool_name = request["params"]["name"]
                arguments = request["params"].get("arguments", {})
                
                if tool_name == "create_skill":
                    result = tool_create_skill(arguments)
                elif tool_name == "update_skill":
                    result = tool_update_skill(arguments)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                    
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                    }
                }
                print(json.dumps(response), flush=True)
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")

if __name__ == "__main__":
    main()
