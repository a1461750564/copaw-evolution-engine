__version__ = "3.7.1"

import json
import os
import tempfile
import threading
import time
import shutil
from datetime import datetime

_profile_lock = threading.RLock()
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "user_profile.json")

# --- 核心 I/O 辅助函数 (v3.7.1 Hardened) ---

def _atomic_write_json(filepath, data):
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

def _load_profile_or_quarantine():
    """
    隔离与重置策略 (v3.7.1 Hardened)
    1. 精准拦截 FileNotFoundError (Python 3 中它是 OSError 的子类)
    2. 损坏文件隔离备份
    3. 严重 I/O 错误抛出
    """
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None # 新用户，正常缺失
    except json.JSONDecodeError:
        # 灾难恢复：隔离损坏文件
        backup_path = f"{PROFILE_PATH}.corrupted.{int(time.time())}"
        try:
            shutil.copy2(PROFILE_PATH, backup_path)
        except: pass
        return "CORRUPTED" # 标记为损坏
    except OSError as e:
        # 严重系统级错误 (权限/NFS 等)
        raise RuntimeError(f"Critical I/O error reading profile: {e}")

def _get_default_profile():
    return {
        "preferences": {}, 
        "topics": {}, 
        "interaction_count": 0,
        "first_seen": datetime.now().isoformat(), 
        "last_updated": None
    }

# --- 公共接口 ---

def update_profile(conversation):
    # 1. 无锁计算 (假设 conversation 是纯数据，不做复杂分析)
    # 为了演示 v3.7.1 修复，这里简化逻辑，重点是 I/O 安全
    new_topics = {"general": 1}
    new_prefs = {}
    
    with _profile_lock:
        raw = _load_profile_or_quarantine()
        
        if raw is None:
            profile = _get_default_profile()
        elif raw == "CORRUPTED":
            profile = _get_default_profile() # 重置
        else:
            profile = raw
        
        # 2. 极速合并
        profile["interaction_count"] = profile.get("interaction_count", 0) + 1
        
        current_topics = profile.setdefault("topics", {})
        for k, v in new_topics.items():
            current_topics[k] = current_topics.get(k, 0) + v
            
        profile.setdefault("preferences", {}).update(new_prefs)
        profile["last_updated"] = datetime.now().isoformat()
        
        _atomic_write_json(PROFILE_PATH, profile)
        
    return profile

def get_profile():
    with _profile_lock:
        raw = _load_profile_or_quarantine()
        if raw is None or raw == "CORRUPTED":
            return _get_default_profile()
        return raw

def clear_profile():
    with _profile_lock:
        default = _get_default_profile()
        default["last_updated"] = datetime.now().isoformat()
        _atomic_write_json(PROFILE_PATH, default)
        return {"status": "Profile cleared", "profile": default}
