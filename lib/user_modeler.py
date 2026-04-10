__version__ = "3.7.0"

import json
import os
import tempfile
import threading
import time
import shutil
from datetime import datetime

_profile_lock = threading.RLock()
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "user_profile.json")

# --- 核心 I/O 辅助函数 (容灾增强) ---

def _atomic_write_json(filepath, data):
    """原子写入"""
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
    隔离与重置策略 (Quarantine & Reset)
    1. 文件不存在 -> 返回默认空配置
    2. 文件损坏 -> 备份为 .corrupted.bak，返回默认空配置 (不中断服务)
    3. I/O 错误 (权限/NFS) -> 抛出异常 (需人工干预)
    """
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None # 正常缺失
    except json.JSONDecodeError:
        # 灾难恢复：隔离损坏文件
        backup_path = f"{PROFILE_PATH}.corrupted.{int(time.time())}"
        try:
            shutil.copy2(PROFILE_PATH, backup_path)
        except: pass
        return "CORRUPTED" # 标记为损坏
    except OSError as e:
        # 严重系统级错误
        raise RuntimeError(f"Critical I/O error reading profile: {e}")

def _get_default_profile():
    return {
        "preferences": {}, 
        "topics": {}, 
        "interaction_count": 0,
        "first_seen": datetime.now().isoformat(), 
        "last_updated": None
    }

# --- 重型计算逻辑 (移出锁) ---

def _analyze_conversation(conversation):
    """纯 CPU 计算"""
    topics = {}
    prefs = {}
    for entry in conversation:
        content = entry.get("content", "") if isinstance(entry, dict) else str(entry)
        cl = content.lower()
        
        if "code" in cl or "python" in cl or "debug" in cl:
            topics["coding"] = topics.get("coding", 0) + 1
        elif "write" in cl or "blog" in cl or "document" in cl:
            topics["writing"] = topics.get("writing", 0) + 1
            
        if "short" in cl or "concise" in cl: prefs["response_length"] = "short"
        elif "detailed" in cl or "explain" in cl: prefs["response_length"] = "detailed"
    return topics, prefs

# --- 公共接口 ---

def update_profile(conversation):
    # 1. 无锁计算
    new_topics, new_prefs = _analyze_conversation(conversation)
    
    with _profile_lock:
        raw = _load_profile_or_quarantine()
        
        if raw is None:
            profile = _get_default_profile()
        elif raw == "CORRUPTED":
            profile = _get_default_profile() # 重置
        else:
            profile = raw
        
        # 2. 极速合并
        profile["interaction_count"] = profile.get("interaction_count", 0) + len(conversation)
        
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
