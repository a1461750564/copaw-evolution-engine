__version__ = "3.5.1"

import json
import os
import tempfile
import threading
from datetime import datetime
from typing import Optional

_profile_lock = threading.RLock()


PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "user_profile.json"
)
# ⚠️ REMOVED top-level os.makedirs: moved to _atomic_write_json


def _atomic_write_json(filepath: str, data: dict):
    """Atomic write: Create dir if needed, write to tmp, then replace."""
    dir_path = os.path.dirname(filepath)
    # Lazy directory creation
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _load_profile() -> dict:
    with _profile_lock:
        if not os.path.exists(PROFILE_PATH):
            return {
                "preferences": {},
                "topics": {},
                "interaction_count": 0,
                "first_seen": datetime.now().isoformat(),
                "last_updated": None,
            }
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted profile file: {e}") from e
        except OSError as e:
            raise IOError(f"Failed to read profile file: {e}") from e


def _save_profile(profile: dict):
    with _profile_lock:
        profile["last_updated"] = datetime.now().isoformat()
        _atomic_write_json(PROFILE_PATH, profile)


def update_profile(conversation: list) -> dict:
    with _profile_lock:
        profile = _load_profile()  # Lock re-entry safe

        profile["interaction_count"] = profile.get("interaction_count", 0) + len(
            conversation
        )

        topics = profile.get("topics", {})
        preferences = profile.get("preferences", {})

        for entry in conversation:
            content = (
                entry.get("content", "") if isinstance(entry, dict) else str(entry)
            )
            content_lower = content.lower()

            topic_keywords = {
                "coding": [
                    "code",
                    "python",
                    "javascript",
                    "programming",
                    "function",
                    "debug",
                ],
                "writing": ["write", "article", "blog", "document", "draft"],
                "research": ["research", "search", "find", "analyze", "investigate"],
                "data": ["data", "database", "sql", "query", "analytics"],
                "devops": ["deploy", "docker", "cloud", "ci/cd", "pipeline"],
            }

            for topic, keywords in topic_keywords.items():
                if any(kw in content_lower for kw in keywords):
                    topics[topic] = topics.get(topic, 0) + 1

            if "prefer_short" in content_lower or "concise" in content_lower:
                preferences["response_length"] = "short"
            elif "detailed" in content_lower or "explain" in content_lower:
                preferences["response_length"] = "detailed"

        profile["topics"] = topics
        profile["preferences"] = preferences

        _save_profile(profile)  # Lock re-entry safe

        return profile


def get_profile() -> dict:
    return _load_profile()


def clear_profile() -> dict:
    default_profile = {
        "preferences": {},
        "topics": {},
        "interaction_count": 0,
        "first_seen": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
    }
    _save_profile(default_profile)
    return {"status": "Profile cleared", "profile": default_profile}
