"""
CoPaw Evolution Engine MCP Server (v3.1)
Features:
- Framework-Native API (POST /skills, PUT /skills/save)
- Auto Version Bumping
- Gatekeeper Audit Tool (Check evolution status before task completion)
"""

import os
import sys
import json
import http.client
import subprocess
import re
import time
import uuid
from mcp.server.fastmcp import FastMCP

# --- Constants ---
COPAW_API_BASE = "http://127.0.0.1:8088"
WORKING_DIR = os.environ.get("COPAW_WORKING_DIR", os.getcwd())

# Initialize MCP Server
mcp = FastMCP("evolution-engine")

def get_agent_id():
    """Extract Agent ID from working dir path."""
    # Expected format: .../workspaces/<AgentID>/
    match = re.search(r"workspaces/([^/]+)", WORKING_DIR)
    return match.group(1) if match else "default"

def get_api_headers():
    return {
        "Content-Type": "application/json",
        "X-Agent-Id": get_agent_id()
    }

# --- Tools ---

@mcp.tool()
def create_skill(name: str, description: str, content: str) -> str:
    """Create a new skill via CoPaw API.
    
    Args:
        name: Skill name (e.g., 'pdf-processing-sop')
        description: Short summary
        content: Full Markdown content (must start with YAML frontmatter)
    """
    payload = {
        "name": name,
        "description": description,
        "content": content
    }
    
    try:
        conn = http.client.HTTPConnection("127.0.0.1", 8088)
        conn.request("POST", "/api/skills", json.dumps(payload), get_api_headers())
        res = conn.getresponse()
        body = res.read().decode()
        
        if res.status == 200 or res.status == 201:
            return f"✅ Skill '{name}' created successfully."
        else:
            return f"❌ Failed to create skill: {res.status} {body}"
    except Exception as e:
        return f"❌ API Error: {e}"

def bump_version(content: str) -> str:
    """Auto-increment version in YAML frontmatter."""
    version_pattern = re.compile(r"(version:\s*)(\d+\.\d+\.\d+)")
    
    if not version_pattern.search(content):
        # Inject v1.0.0 if missing
        frontmatter_end = content.find("---", 1) # Skip first ---
        if frontmatter_end != -1:
            content = content[:frontmatter_end] + "\nversion: 1.0.0" + content[frontmatter_end:]
        return content

    def replacer(match):
        prefix = match.group(1)
        version = match.group(2)
        parts = list(map(int, version.split('.')))
        parts[-1] += 1  # Bump Patch
        return f"{prefix}{'.'.join(map(str, parts))}"
        
    return version_pattern.sub(replacer, content)

@mcp.tool()
def update_skill(name: str, content: str) -> str:
    """Update an existing skill. Auto-bumps version.
    
    Args:
        name: Skill name to update
        content: New Markdown content
    """
    # 1. Bump Version
    new_content = bump_version(content)
    
    payload = {
        "name": name,
        "content": new_content
    }
    
    try:
        conn = http.client.HTTPConnection("127.0.0.1", 8088)
        conn.request("PUT", "/api/skills/save", json.dumps(payload), get_api_headers())
        res = conn.getresponse()
        body = res.read().decode()
        
        if res.status == 200:
            return f"✅ Skill '{name}' updated. Version bumped."
        else:
            return f"❌ Failed to update skill: {res.status} {body}"
    except Exception as e:
        return f"❌ API Error: {e}"

@mcp.tool()
def check_evolution_status(task_summary: str = "") -> str:
    """[Gatekeeper] Check if evolution requirements are met before finishing a task.
    
    Call this tool to verify if you need to create a skill based on recent changes.
    
    Args:
        task_summary: Brief summary of what was done in this session.
    """
    if not task_summary:
        return "⚠️ WARN: Please provide a summary of what you did to perform the check."

    # 1. Heuristic Check: Does this sound like an SOP?
    triggers = ["fix", "bug", "sop", "workflow", "install", "script", "config", "update"]
    is_sop_candidate = any(t in task_summary.lower() for t in triggers)

    if not is_sop_candidate:
        return f"✅ Audit Passed: Task '{task_summary}' seems routine, no SOP required."

    # 2. Check Skill Inventory
    skills_dir = os.path.join(WORKING_DIR, "skills")
    has_new_skill = False
    try:
        # Check if skills dir was modified recently (last 5 mins)
        if os.path.exists(skills_dir):
            stat = os.stat(skills_dir)
            if (time.time() - stat.st_mtime) < 300:
                has_new_skill = True
    except:
        pass

    # 3. Check Git Status
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=WORKING_DIR, capture_output=True, text=True, timeout=5
        )
        has_changes = bool(result.stdout.strip())
    except:
        has_changes = False

    # Logic: If it's an SOP task AND we made changes BUT no new skill detected
    if is_sop_candidate and has_changes and not has_new_skill:
        return (
            f"🚨 BLOCK: Evolution Requirement Not Met!\n"
            f"- Task: {task_summary}\n"
            f"- Status: Code changes detected, but NO new/updated skills found in `skills/`.\n"
            f"- Action: You MUST call `create_skill` or `update_skill` before finishing."
        )
    
    return f"✅ Audit Passed: Evolution requirements satisfied."

# --- Start ---
if __name__ == "__main__":
    mcp.run()