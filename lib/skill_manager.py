__version__ = "4.0.1"

import json
import os
import tempfile
import threading
import time
import atexit
import re
from datetime import datetime
from typing import Optional, Tuple

# --- 核心架构：Write-Behind (内存缓存 + 异步刷盘) ---

_stats_cache = {"skills": {}, "last_updated": None}
_cache_lock = threading.Lock()
_dirty = False
_shutdown_event = threading.Event()

# 路径配置
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS_PATH = os.path.join(PLUGIN_DIR, "data", "usage_stats.json")
DEFAULT_WORKSPACE = os.environ.get("COPAW_WORKING_DIR", os.getcwd())

def _get_workspace() -> str:
    return os.environ.get("COPAW_WORKING_DIR", DEFAULT_WORKSPACE)

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
    global _stats_cache
    if os.path.exists(STATS_PATH):
        try:
            with open(STATS_PATH, "r", encoding="utf-8") as f:
                _stats_cache = json.load(f)
        except:
            _stats_cache = {"skills": {}, "last_updated": None}

def _flush_worker():
    global _dirty
    while not _shutdown_event.wait(5.0):
        if _dirty:
            try:
                with _cache_lock:
                    skills_snapshot = {k: dict(v) for k, v in _stats_cache["skills"].items()}
                    _stats_cache["last_updated"] = datetime.now().isoformat()
                    _dirty = False
                _atomic_write_json(STATS_PATH, {"skills": skills_snapshot, "last_updated": _stats_cache["last_updated"]})
            except Exception:
                _dirty = True
                pass

def _force_flush():
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

# ==========================================
# 🧬 核心能力 II: Skill Lifecycle Management
# ==========================================

def _bump_version(version_str: str, bump_type: str = "patch") -> str:
    """安全地增加语义化版本号"""
    try:
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_str)
        if match:
            major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if bump_type == "major": major += 1; minor = 0; patch = 0
            elif bump_type == "minor": minor += 1; patch = 0
            else: patch += 1
            return f"{major}.{minor}.{patch}"
    except: pass
    return "1.0.0" # 兜底

def create_skill(name: str, description: str, content: str, version: str = "1.0.0") -> dict:
    """创建新技能 SOP (纯净模式：Header + Content)"""
    workspace = _get_workspace()
    skill_dir = os.path.join(workspace, "skills", name)
    file_path = os.path.join(skill_dir, "SKILL.md")
    
    if os.path.exists(file_path):
        return {"status": "error", "reason": f"Skill '{name}' already exists. Use 'update_skill' instead."}
    
    # 纯净 Header 生成
    header = f"""---
name: {name}
description: {description}
version: {version}
---

"""
    
    try:
        os.makedirs(skill_dir, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(header + content)
        return {
            "status": "success", 
            "message": f"Skill '{name}' created.", 
            "path": file_path,
            "version": version
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def update_skill(name: str, content: str, bump_type: str = "patch") -> dict:
    """
    智能更新技能 SOP：
    1. 如果 content 包含 '---' 头：视为完整文件更新，自动 Bump Version。
    2. 如果 content 不包含 '---' 头：视为正文更新，保留旧 Header 并 Bump Version。
    """
    workspace = _get_workspace()
    file_path = os.path.join(workspace, "skills", name, "SKILL.md")
    
    if not os.path.exists(file_path):
        return {"status": "error", "reason": f"Skill '{name}' not found. Use 'create_skill' instead."}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            old_content = f.read()
        
        # 1. 解析旧版本
        old_header_match = re.match(r"^(---\s*\n[\s\S]*?\n---\s*\n)", old_content)
        if not old_header_match:
            return {"status": "error", "reason": "Original file has invalid format (missing header)."}
            
        old_header = old_header_match.group(1)
        ver_match = re.search(r"version:\s*['\"]?(\d+\.\d+\.\d+)['\"]?", old_header)
        old_version = ver_match.group(1) if ver_match else "1.0.0"
        new_version = _bump_version(old_version, bump_type)
        
        # 2. 决定更新策略
        final_content = ""
        is_full_content = content.strip().startswith("---")
        
        if is_full_content:
            # 策略 A: 全量更新 (用户提供完整内容)
            final_content = content
            # 检查是否有版本号
            if re.search(r"version:", final_content):
                # 替换版本号
                final_content = re.sub(
                    r"(version:\s*['\"]?)(\d+\.\d+\.\d+)(['\"]?)", 
                    rf"\g<1>{new_version}\3", 
                    final_content
                )
            else:
                # 用户忘了写版本号，尝试插入到 Header 块中
                close_match = re.search(r"\n---\s*\n", final_content)
                if close_match:
                    # 在最后一个 --- 之前插入
                    idx = close_match.start()
                    final_content = final_content[:idx] + f"\nversion: {new_version}\n" + final_content[idx:]
        else:
            # 策略 B: 仅正文更新 (保留旧 Header)
            # 修改旧 Header 的版本号
            if re.search(r"version:", old_header):
                new_header = re.sub(
                    r"(version:\s*['\"]?)(\d+\.\d+\.\d+)(['\"]?)", 
                    rf"\g<1>{new_version}\3", 
                    old_header
                )
            else:
                # 旧文件也没版本号，插入一个
                close_match = re.search(r"\n---\s*\n", old_header)
                if close_match:
                    idx = close_match.start()
                    new_header = old_header[:idx] + f"\nversion: {new_version}\n" + old_header[idx:]
                else:
                    new_header = old_header
            
            final_content = new_header + "\n" + content
            
        # 3. 写入
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)
            
        return {
            "status": "success", 
            "message": f"Skill '{name}' updated.", 
            "old_version": old_version,
            "new_version": new_version
        }
            
    except Exception as e:
        return {"status": "error", "reason": str(e)}

# ==========================================
# 📊 核心能力 I: Telemetry (Telemetry & Audit)
# ==========================================

def track_usage(skill: str, success: bool) -> dict:
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
            "skill": skill, "total_calls": total, "fail_rate": s["fail_rate"],
            "status": "DEPRECATED ⚠️" if s["fail_rate"] > 30 else "ACTIVE",
        }

def get_skill_stats(skill: Optional[str] = None) -> dict:
    with _cache_lock:
        if skill: return dict(_stats_cache["skills"].get(skill, {}))
        return {k: dict(v) for k, v in _stats_cache["skills"].items()}

def audit_skills() -> dict:
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
