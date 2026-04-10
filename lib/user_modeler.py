__version__ = "3.2.0"

import json
import os
from datetime import datetime
from typing import Optional


PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "user_profile.json"
)
os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)


def _load_profile() -> dict:
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
    except (json.JSONDecodeError, IOError):
        return {
            "preferences": {},
            "topics": {},
            "interaction_count": 0,
            "first_seen": datetime.now().isoformat(),
            "last_updated": None,
        }


def _save_profile(profile: dict):
    profile["last_updated"] = datetime.now().isoformat()
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)


def update_profile(conversation: list) -> dict:
    profile = _load_profile()

    profile["interaction_count"] = profile.get("interaction_count", 0) + len(
        conversation
    )

    topics = profile.get("topics", {})
    preferences = profile.get("preferences", {})

    for entry in conversation:
        content = entry.get("content", "") if isinstance(entry, dict) else str(entry)
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

    _save_profile(profile)

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
