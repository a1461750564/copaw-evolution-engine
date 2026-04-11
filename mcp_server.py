#!/usr/bin/env python3
"""
CoPaw Evolution Engine - MCP Server (FastMCP Implementation)
Uses the standard FastMCP library to ensure compatibility with CoPaw.
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

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("EvolutionEngine")

@mcp.tool()
def evolve_create_skill(name: str, description: str = "", content: str = "") -> str:
    """Create a new CoPaw skill from scratch. Used when an Agent learns a new capability."""
    name = name.lower().replace(" ", "-")
    if not name or not content:
        return json.dumps({"status": "error", "reason": "name and content are required"})
    return json.dumps(create_skill(name=name, description=description, content=content))

@mcp.tool()
def evolve_update_skill(name: str, content: str) -> str:
    """Update an existing skill. Automatically handles versioning."""
    name = name.lower().replace(" ", "-")
    if not name or not content:
        return json.dumps({"status": "error", "reason": "name and content are required"})
    return json.dumps(update_skill(name=name, content=content))

@mcp.tool()
def evolve_report_usage(name: str, success: bool = True) -> str:
    """Report whether a skill execution was successful or failed."""
    name = name.lower().replace(" ", "-")
    if not name:
        return json.dumps({"status": "error", "reason": "name is required"})
    return json.dumps(track_usage(skill=name, success=success))

@mcp.tool()
def evolve_archive_skill(name: str) -> str:
    """Archive a skill that is outdated or useless."""
    name = name.lower().replace(" ", "-")
    if not name:
        return json.dumps({"status": "error", "reason": "name is required"})
    return json.dumps(archive_skill(name=name))

@mcp.tool()
def evolve_list_skills() -> str:
    """List all skills currently managed by the evolution engine."""
    return json.dumps(list_skills())

@mcp.tool()
def evolve_get_stats(name: str = "") -> str:
    """Get usage statistics and success rates for skills."""
    return json.dumps(get_skill_stats(skill=name if name else None))

if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run()
