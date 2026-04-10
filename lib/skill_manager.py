__version__ = "3.5.1"

import json
import os
import tempfile
import threading
from datetime import datetime
from typing import Optional

_stats_lock = threading.RLock()


STATS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "usage_stats.json")
# ⚠️ REMOVED top-level os.makedirs: moved to _atomic_write_json for lazy initialization


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


def _load_stats() -> dict:
    with _stats_lock:
        if not os.path.exists(STATS_PATH):
            return {"skills": {}, "last_updated": None}
        try:
            with open(STATS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted stats file: {e}") from e
        except OSError as e:
            raise IOError(f"Failed to read stats file: {e}") from e


def _save_stats(stats: dict):
    with _stats_lock:
        stats["last_updated"] = datetime.now().isoformat()
        _atomic_write_json(STATS_PATH, stats)


def track_usage(skill: str, success: bool) -> dict:
    with _stats_lock:
        stats = _load_stats()  # Lock re-entry safe (RLock)

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
        skill_stats["fail_rate"] = (
            round((failures / total) * 100, 2) if total > 0 else 0.0
        )

        _save_stats(stats)  # Lock re-entry safe (RLock)

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
