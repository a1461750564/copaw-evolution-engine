__version__ = "3.2.0"

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError("fastmcp is required. Install with: pip install fastmcp")

from lib import memory_crawler, skill_manager, user_modeler


mcp = FastMCP("Hermes-Features-v3.2.0")


@mcp.tool()
def hybrid_search(query: str, limit: int = 10) -> dict:
    """
    Hybrid search combining FTS5精准匹配 + LLM摘要.
    """
    return memory_crawler.search_hybrid(query, limit)


@mcp.tool()
def index_session(path: str) -> dict:
    """
    Index a CoPaw jsonl log session into FTS5.
    """
    return memory_crawler.index_session(path)


@mcp.tool()
def get_index_stats() -> dict:
    """
    Get FTS5 index statistics.
    """
    return memory_crawler.get_stats()


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
