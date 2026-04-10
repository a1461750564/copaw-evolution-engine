__version__ = "4.0.0"

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
# 默认工作区路径 (如果没有环境变量兜底)
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

# ==========================================
# 🧬 核心能力 II: Skill Lifecycle Management
# ==========================================

def _parse_version(version_str: str) -> Tuple[int, int, int]:
    """解析语义化版本号 v1.2.3 -> (1, 2, 3)"""
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_str)
    if match: return int(match.group(1)), int(match.group(2)), int(match.group(3))
    return 0, 0, 0

def _bump_version(version_str: str, bump_type: str = "patch") -> str:
    """版本号自增"""
    major, minor, patch = _parse_version(version_str)
    if bump_type == "major": major += 1; minor = 0; patch = 0
    elif bump_type == "minor": minor += 1; patch = 0
    else: patch += 1
    return f"{major}.{minor}.{patch}"

def create_skill(name: str, description: str, content: str, version: str = "1.0.0") -> dict:
    """创建新技能 SOP"""
    workspace = _get_workspace()
    skill_dir = os.path.join(workspace, "skills", name)
    file_path = os.path.join(skill_dir, "SKILL.md")
    
    if os.path.exists(file_path):
        return {"status": "error", "reason": f"Skill '{name}' already exists. Use 'update_skill' instead."}
    
    # 自动生成 YAML Frontmatter + 内容
    header = f"""---
name: {name}
description: {description}
version: {version}
---

# 🧬 {name}

{content}
"""
    
    try:
        os.makedirs(skill_dir, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(header)
        return {
            "status": "success", 
            "message": f"Skill '{name}' created.", 
            "path": file_path,
            "version": version
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def update_skill(name: str, content: str, bump_type: str = "patch") -> dict:
    """更新现有技能 SOP (自动 Bump 版本)"""
    workspace = _get_workspace()
    file_path = os.path.join(workspace, "skills", name, "SKILL.md")
    
    if not os.path.exists(file_path):
        return {"status": "error", "reason": f"Skill '{name}' not found. Use 'create_skill' instead."}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
        
        # 解析旧版本
        version_match = re.search(r"version:\s*['\"]?(\d+\.\d+\.\d+)['\"]?", original_content)
        old_version = version_match.group(1) if version_match else "1.0.0"
        new_version = _bump_version(old_version, bump_type)
        
        # 替换版本号
        new_content = re.sub(r"(version:\s*['\"]?)(\d+\.\d+\.\d+)(['\"]?)", rf"\g<1>{new_version}\3", original_content)
        
        # 替换内容 (保留头部，替换 Markdown Body)
        # 这里简单策略：直接重写整个文件，保留头部版本信息，覆盖正文
        # 更好的做法是只替换 --- 之后的内容，但重写更稳健
        # 重新构建文件结构：
        
        header_match = re.match(r"(---[\s\S]*?---)", new_content)
        if header_match:
            final_header = header_match.group(1)
            # 更新 header 里的 version 字段
            final_header = re.sub(r"(version:\s*['\"]?)(\d+\.\d+\.\d+)(['\"]?)", rf"\g<1>{new_version}\3", final_header)
            
            # 写入新文件
            final_file = f"{final_header}\n\n# 🧬 {name}\n\n{content}\n"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_file)
            
            return {
                "status": "success", 
                "message": f"Skill '{name}' updated.", 
                "old_version": old_version,
                "new_version": new_version
            }
        else:
            return {"status": "error", "reason": "Invalid skill format (missing YAML header)."}
            
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
