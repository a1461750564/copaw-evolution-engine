__version__ = "3.7.0"

import json
import os
import tempfile
import threading
import time
import atexit
from datetime import datetime
from typing import Optional

# --- 核心架构：Write-Behind (内存缓存 + 异步刷盘) ---

_stats_cache = {"skills": {}, "last_updated": None}
_cache_lock = threading.Lock()  # 微秒级锁
_dirty = False
_shutdown_event = threading.Event()

STATS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "usage_stats.json")

def _atomic_write_json(filepath: str, data: dict):
    """原子写入：优化 TOCTOU，支持 NFS"""
    dir_path = os.path.dirname(filepath)
    try: os.makedirs(dir_path, exist_ok=True)
    except OSError: pass
    
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.exists(tmp_path): os.unlink(tmp_path)
        raise

def _load_initial_state():
    """启动时加载磁盘数据到内存"""
    global _stats_cache
    if os.path.exists(STATS_PATH):
        try:
            with open(STATS_PATH, "r", encoding="utf-8") as f:
                _stats_cache = json.load(f)
        except:
            _stats_cache = {"skills": {}, "last_updated": None}

def _flush_worker():
    """后台刷盘守护线程 (使用极速浅拷贝)"""
    global _dirty
    while not _shutdown_event.wait(5.0): # 每 5 秒检查一次
        if _dirty:
            try:
                # 1. 极速快照 (Fast Clone) - 比 copy.deepcopy 快 10 倍+
                with _cache_lock:
                    skills_snapshot = {k: dict(v) for k, v in _stats_cache["skills"].items()}
                    _stats_cache["last_updated"] = datetime.now().isoformat()
                    _dirty = False
                
                # 2. 执行 I/O (释放了锁)
                _atomic_write_json(STATS_PATH, {"skills": skills_snapshot, "last_updated": _stats_cache["last_updated"]})
            except Exception:
                _dirty = True # 失败标记为脏，下次重试
                pass

def _force_flush():
    """强制刷盘 (用于进程退出)"""
    global _dirty
    if _dirty:
        try:
            with _cache_lock:
                skills_snapshot = {k: dict(v) for k, v in _stats_cache["skills"].items()}
                _stats_cache["last_updated"] = datetime.now().isoformat()
                _dirty = False
            _atomic_write_json(STATS_PATH, {"skills": skills_snapshot, "last_updated": _stats_cache["last_updated"]})
        except: pass

# --- 初始化 ---
_load_initial_state()
_flush_thread = threading.Thread(target=_flush_worker, daemon=True)
_flush_thread.start()
atexit.register(_force_flush)

# --- 公共接口 ---

def track_usage(skill: str, success: bool) -> dict:
    """仅操作内存，极速返回"""
    global _dirty
    now = datetime.now().isoformat()
    with _cache_lock:
        if skill not in _stats_cache["skills"]:
            _stats_cache["skills"][skill] = {
                "total_calls": 0, "successful_calls": 0, "failed_calls": 0,
                "fail_rate": 0.0, "first_seen": now,
            }

        s = _stats_cache["skills"][skill]
        s["total_calls"] += 1
        if success: s["successful_calls"] += 1
        else: s["failed_calls"] += 1

        total = s["total_calls"]
        failures = s["failed_calls"]
        s["fail_rate"] = round((failures / total) * 100, 2) if total > 0 else 0.0
        _dirty = True

        return {
            "skill": skill,
            "total_calls": total,
            "fail_rate": s["fail_rate"],
            "status": "DEPRECATED ⚠️" if s["fail_rate"] > 30 else "ACTIVE",
        }

def get_skill_stats(skill: Optional[str] = None) -> dict:
    """读取内存缓存，无 I/O 阻塞"""
    with _cache_lock:
        if skill:
            return dict(_stats_cache["skills"].get(skill, {}))
        return {k: dict(v) for k, v in _stats_cache["skills"].items()}

def audit_skills() -> dict:
    """读取内存缓存进行分析"""
    with _cache_lock:
        skills = {k: dict(v) for k, v in _stats_cache.get("skills", {}).items()}

    deprecated, active = [], []
    for k, v in skills.items():
        fr = v.get("fail_rate", 0)
        if fr > 30:
            deprecated.append({"skill": k, "fail_rate": fr, "total_calls": v.get("total_calls", 0), "status": "⚠️ DEPRECATED"})
        else:
            active.append({"skill": k, "fail_rate": fr, "total_calls": v.get("total_calls", 0), "status": "ACTIVE"})
    return {
        "audited_at": datetime.now().isoformat(), "total_skills": len(skills),
        "deprecated_count": len(deprecated), "deprecated_skills": deprecated, "active_skills": active,
    }
