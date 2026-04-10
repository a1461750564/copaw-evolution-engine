__version__ = "3.7.0"

import os
import sys
import asyncio
import subprocess
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError("fastmcp is required. Install with: pip install fastmcp")

from lib import skill_manager, user_modeler


mcp = FastMCP("Evolution-Engine-v3.7.0")


@mcp.tool()
async def check_evolution_status(task_summary: str = "") -> dict:
    """
    Gatekeeper tool with Resilience (Retry Logic) and Zombie Prevention.
    """
    workspace = os.environ.get("COPAW_WORKING_DIR", os.getcwd())
    git_dir = os.path.join(workspace, ".git")

    if not os.path.exists(git_dir):
        return {"status": "🚨 BLOCK", "reason": "Not a git repository."}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "status", "--porcelain",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
                git_changes = stdout.decode().strip()
            except asyncio.TimeoutError:
                # 🚨 Kill zombie and clean up FDs
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
                try:
                    await proc.wait()
                except: pass

                if attempt == max_retries - 1:
                    return {"status": "🚨 BLOCK", "reason": "Git command timed out after 3 retries."}
                await asyncio.sleep(2 ** attempt)
                continue
            break # Success
        except FileNotFoundError:
            return {"status": "🚨 BLOCK", "reason": "Git executable not found."}
        except Exception as e:
            if attempt == max_retries - 1:
                return {"status": "🚨 BLOCK", "reason": f"Git check failed: {str(e)}"}
            await asyncio.sleep(1)

    # Skills check
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
    except: pass # Failsafe

    has_code_changes = bool(git_changes)
    has_skill_changes = bool(skills_changes)

    if has_code_changes and not has_skill_changes:
        return {
            "status": "🚨 BLOCK",
            "reason": "Code changes detected but no new/modified Skills found.",
            "advice": "Create or update a Skill in skills/ directory to match code changes."
        }
    return {"status": "✅ CLEAR", "reason": "Evolution status verified."}


@mcp.tool()
def track_usage(skill: str, success: bool) -> dict:
    return skill_manager.track_usage(skill, success)

@mcp.tool()
def get_skill_stats(skill: Optional[str] = None) -> dict:
    return skill_manager.get_skill_stats(skill)

@mcp.tool()
def audit_skills() -> dict:
    return skill_manager.audit_skills()

@mcp.tool()
def extract_profile(conversation: list) -> dict:
    return user_modeler.update_profile(conversation)

@mcp.tool()
def get_user_profile() -> dict:
    return user_modeler.get_profile()

@mcp.tool()
def reset_user_profile() -> dict:
    return user_modeler.clear_profile()


if __name__ == "__main__":
    mcp.run()
