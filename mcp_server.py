__version__ = "3.5.1"

import os
import sys
import asyncio
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError("fastmcp is required. Install with: pip install fastmcp")

from lib import skill_manager, user_modeler


mcp = FastMCP("Evolution-Engine-v3.5.1")


@mcp.tool()
async def check_evolution_status(task_summary: str = "") -> dict:
    """
    Gatekeeper tool. Check if code changes match skill updates.
    Agent must call this before finishing complex tasks.
    Now fully async to prevent blocking the MCP event loop.
    """
    workspace = os.environ.get("COPAW_WORKING_DIR", os.getcwd())
    git_dir = os.path.join(workspace, ".git")

    if not os.path.exists(git_dir):
        return {"status": "no_git", "reason": "Not a git repository"}

    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        git_changes = stdout.decode().strip()
    except (asyncio.TimeoutError, subprocess.SubprocessError):
        return {"status": "ERROR", "reason": "Git command failed or timed out"}

    skills_changes = ""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain", "skills/",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        skills_changes = stdout.decode().strip()
    except (asyncio.TimeoutError, subprocess.SubprocessError):
        pass

    has_code_changes = bool(git_changes)
    has_skill_changes = bool(skills_changes)

    if has_code_changes and not has_skill_changes:
        return {
            "status": "🚨 BLOCK",
            "reason": "Code changes detected but no new/modified Skills found.",
            "advice": "Create or update a Skill in skills/ directory to match code changes."
        }
    elif not has_code_changes and not has_skill_changes:
        return {"status": "✅ CLEAR", "reason": "No code or skill changes detected"}
    elif has_code_changes and has_skill_changes:
        return {"status": "✅ CLEAR", "reason": "Both code and skill changes detected"}
    else:
        return {"status": "✅ CLEAR", "reason": "Skill changes only"}


@mcp.tool()
def track_usage(skill: str, success: bool) -> dict:
    """
    Track skill usage and success/failure.
    """
    return skill_manager.track_usage(skill, success)


@mcp.tool()
def get_skill_stats(skill: Optional[str] = None) -> dict:
    """
    Get statistics for a specific skill or all skills.
    """
    return skill_manager.get_skill_stats(skill)


@mcp.tool()
def audit_skills() -> dict:
    """
    Audit all skills - mark those with fail_rate > 30% as DEPRECATED.
    """
    return skill_manager.audit_skills()


@mcp.tool()
def extract_profile(conversation: list) -> dict:
    """
    Extract user profile from conversation history.
    """
    return user_modeler.update_profile(conversation)


@mcp.tool()
def get_user_profile() -> dict:
    """
    Get current user profile.
    """
    return user_modeler.get_profile()


@mcp.tool()
def reset_user_profile() -> dict:
    """
    Reset user profile to default.
    """
    return user_modeler.clear_profile()


if __name__ == "__main__":
    mcp.run()
