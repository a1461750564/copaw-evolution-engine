__version__ = "3.2.0"

import json
import os
import threading
from datetime import datetime
from typing import Optional

_stats_lock = threading.RLock()


STATS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "usage_stats.json")
os.makedirs(os.path.dirname(STATS_PATH), exist_ok=True)


def _load_stats() -> dict:
    with _stats_lock:
        if not os.path.exists(STATS_PATH):
            return {"skills": {}, "last_updated": None}
        try:
            with open(STATS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"skills": {}, "last_updated": None}


def _save_stats(stats: dict):
    with _stats_lock:
        stats["last_updated"] = datetime.now().isoformat()
        with open(STATS_PATH, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)


def track_usage(skill: str, success: bool) -> dict:
    stats = _load_stats()

    if skill not in stats["skills"]:
        stats["skills"][skill] = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "fail_rate": 0.0,
            "first_seen": datetime.now().isoformat(),
        }

    skill_stats = stats["skills"][skill]
    skill_stats["total_calls"] += 1
    if success:
        skill_stats["successful_calls"] += 1
    else:
        skill_stats["failed_calls"] += 1

    total = skill_stats["total_calls"]
    failures = skill_stats["failed_calls"]
    skill_stats["fail_rate"] = round((failures / total) * 100, 2) if total > 0 else 0.0

    _save_stats(stats)

    return {
        "skill": skill,
        "total_calls": total,
        "fail_rate": skill_stats["fail_rate"],
        "status": "DEPRECATED ⚠️" if skill_stats["fail_rate"] > 30 else "ACTIVE",
    }


def get_skill_stats(skill: Optional[str] = None) -> dict:
    stats = _load_stats()
    if skill:
        return stats["skills"].get(skill, {"error": "Skill not found"})
    return stats["skills"]


def audit_skills() -> dict:
    stats = _load_stats()
    skills = stats.get("skills", {})

    deprecated = []
    active = []

    for skill_name, skill_data in skills.items():
        fail_rate = skill_data.get("fail_rate", 0)
        if fail_rate > 30:
            deprecated.append(
                {
                    "skill": skill_name,
                    "fail_rate": fail_rate,
                    "total_calls": skill_data.get("total_calls", 0),
                    "status": "⚠️ DEPRECATED",
                }
            )
        else:
            active.append(
                {
                    "skill": skill_name,
                    "fail_rate": fail_rate,
                    "total_calls": skill_data.get("total_calls", 0),
                    "status": "ACTIVE",
                }
            )

    return {
        "audited_at": datetime.now().isoformat(),
        "total_skills": len(skills),
        "deprecated_count": len(deprecated),
        "deprecated_skills": deprecated,
        "active_skills": active,
    }
