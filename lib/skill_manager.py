__version__ = "4.4.0"

import json
import os
import tempfile
import threading
import time
import atexit
import re
import shutil
import yaml
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

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
    """原子写入 JSON"""
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

def _atomic_write_text(filepath: str, content: str):
    """原子写入文本 (防止多 Agent 并发写入导致的数据损坏)"""
    dir_path = os.path.dirname(filepath)
    try: os.makedirs(dir_path, exist_ok=True)
    except OSError: pass
    
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
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
# 🧬 核心能力 II: Skill Lifecycle Management (v4.4.0 State-Consistent)
# ==========================================

def _validate_skill_name(name: str) -> str:
    """🔒 安全校验：防止路径穿越 (SEALED)"""
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        return "Invalid skill name. Only alphanumeric, dash, and underscore allowed."
    if len(name) > 50:
        return "Skill name too long."
    return ""

def _parse_yaml_frontmatter(content: str) -> Tuple[Dict[str, Any], str, str]:
    """
    🛡️ 使用 PyYAML 解析 (100% Robust)
    返回: (metadata_dict, raw_header_string, body_string)
    """
    match = re.match(r"^---\s*\r?\n([\s\S]*?)\r?\n---\s*\r?\n", content)
    if not match:
        return {}, "", content
    
    raw_header = match.group(0)
    body = content[match.end():]
    header_content = match.group(1)
    
    try:
        metadata = yaml.safe_load(header_content)
        if not isinstance(metadata, dict): metadata = {}
    except yaml.YAMLError:
        return {}, raw_header, body
        
    return metadata, raw_header, body

def _build_yaml_header(metadata: Dict[str, Any]) -> str:
    """将字典重新构建为 YAML Header (PyYAML)"""
    lines = ["---"]
    for key, val in metadata.items():
        # Use yaml.dump for safe quoting of strings with colons/special chars
        val_str = yaml.dump({key: val}, default_flow_style=False, allow_unicode=True).strip()
        lines.append(val_str)
    lines.append("---")
    lines.append("") 
    return "\n".join(lines)

def _bump_version(version_str: str, bump_type: str = "patch") -> str:
    """安全地增加语义化版本号"""
    match = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", str(version_str))
    if match:
        major, minor = int(match.group(1)), int(match.group(2))
        patch = int(match.group(3)) if match.group(3) else 0
        
        if bump_type == "major": major += 1; minor = 0; patch = 0
        elif bump_type == "minor": minor += 1; patch = 0
        else: patch += 1
        return f"{major}.{minor}.{patch}"
    return "1.0.0"

def create_skill(name: str, description: str, content: str, version: str = "1.0.0") -> dict:
    """创建新技能 SOP (带安全校验 + 原子写入)"""
    err = _validate_skill_name(name)
    if err: return {"status": "error", "reason": err}
    
    workspace = _get_workspace()
    skill_dir = os.path.join(workspace, "skills", name)
    file_path = os.path.join(skill_dir, "SKILL.md")
    
    if os.path.exists(file_path):
        return {"status": "error", "reason": f"Skill '{name}' already exists."}
    
    metadata = {"name": name, "description": description, "version": version}
    header = _build_yaml_header(metadata)
    
    try:
        os.makedirs(skill_dir, exist_ok=True)
        _atomic_write_text(file_path, header + "\n" + content)
        return {"status": "success", "message": f"Skill '{name}' created.", "path": file_path}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def update_skill(name: str, content: str, bump_type: str = "patch", force: bool = False) -> dict:
    """
    🛡️ 智能更新 (v4.4.0 Robust)
    1. PyYAML 解析
    2. 原子写入
    3. 版本化备份 (Versioned Backups)
    """
    err = _validate_skill_name(name)
    if err: return {"status": "error", "reason": err}
    
    workspace = _get_workspace()
    file_path = os.path.join(workspace, "skills", name, "SKILL.md")
    
    if not os.path.exists(file_path):
        return {"status": "error", "reason": f"Skill '{name}' not found."}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            old_content = f.read()
        
        # 解析旧内容
        _, _, old_body = _parse_yaml_frontmatter(old_content)
        
        # 软拦截: 仅在 content 看起来像完整文件时进行激进检查
        new_is_full = content.strip().startswith("---")
        if new_is_full and len(content) < len(old_content) * 0.2 and not force:
            return {"status": "warning", "reason": "Content significantly shorter. Pass force=True to bypass.", "data": {"new_content": content}}

        metadata, _, _ = _parse_yaml_frontmatter(old_content)
        old_version = metadata.get("version", "1.0.0")
        
        # 解析新内容
        new_metadata = {}
        new_body = content
        if content.strip().startswith("---"):
            new_metadata, _, new_body = _parse_yaml_frontmatter(content)
        
        metadata.update(new_metadata)
        
        # 版本化备份 (解决 .bak 被覆盖问题)
        safe_version = str(old_version).replace(" ", "_")
        backup_name = f"SKILL_{safe_version}.md"
        backup_path = os.path.join(workspace, "skills", name, backup_name)
        try: 
            if not os.path.exists(backup_path):
                shutil.copy2(file_path, backup_path)
        except: pass
        
        # 自动升级版本号
        new_version = _bump_version(metadata.get("version", "1.0.0"), bump_type)
        metadata["version"] = new_version
        
        # 构建最终内容
        final_header = _build_yaml_header(metadata)
        final_content = final_header + new_body
        
        # 🔒 原子写入
        _atomic_write_text(file_path, final_content)
            
        return {
            "status": "success", 
            "message": f"Skill '{name}' updated.", 
            "old_version": old_version,
            "new_version": new_version
        }
            
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def rollback_skill(name: str, target_version: str = None) -> dict:
    """
    🔄 回滚技能 (Roll-Forward Logic)
    为了避免版本冲突，我们不降版本号，而是将旧版本的内容应用到新版本号上。
    例如: 从 v1.0.2 回滚到 v1.0.0 的内容 -> 实际保存为 v1.0.3
    """
    err = _validate_skill_name(name)
    if err: return {"status": "error", "reason": err}
    
    workspace = _get_workspace()
    skill_dir = os.path.join(workspace, "skills", name)
    file_path = os.path.join(skill_dir, "SKILL.md")
    
    if not os.path.exists(file_path):
        return {"status": "error", "reason": "Skill not found."}

    # 找到要回滚的内容
    if target_version:
        safe_version = str(target_version).replace(" ", "_")
        backup_name = f"SKILL_{safe_version}.md"
        backup_path = os.path.join(skill_dir, backup_name)
        
        if not os.path.exists(backup_path):
            return {"status": "error", "reason": f"Backup for v{target_version} not found."}
            
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_content = f.read()
            
        # 提取备份内容中的 Body，去掉旧 Header
        _, _, old_body = _parse_yaml_frontmatter(backup_content)
    else:
        # Fallback: Find most recent backup
        backups = [f for f in os.listdir(skill_dir) if f.startswith("SKILL_") and f.endswith(".md")]
        if not backups: return {"status": "error", "reason": "No backups found."}
        
        backups.sort()
        latest_backup = backups[-1]
        backup_path = os.path.join(skill_dir, latest_backup)
        
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_content = f.read()
        _, _, old_body = _parse_yaml_frontmatter(backup_content)
        
        target_version = "latest"

    # Roll-Forward: 获取当前文件的元数据，并增加版本号
    with open(file_path, "r", encoding="utf-8") as f:
        current_content = f.read()
    
    current_metadata, _, _ = _parse_yaml_frontmatter(current_content)
    current_version = current_metadata.get("version", "1.0.0")
    
    # 增加版本号，避免冲突 (v1.0.2 -> v1.0.3)
    new_version = _bump_version(current_version, "patch")
    current_metadata["version"] = new_version
    
    final_header = _build_yaml_header(current_metadata)
    final_content = final_header + old_body
    
    try:
        _atomic_write_text(file_path, final_content)
        return {
            "status": "success", 
            "message": f"Rolled back content of {target_version} to new version {new_version}.",
            "new_version": new_version
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def archive_skill(name: str) -> dict:
    """🗑️ 归档/删除技能 (带纳秒时间戳防止覆盖)"""
    err = _validate_skill_name(name)
    if err: return {"status": "error", "reason": err}
    
    workspace = _get_workspace()
    skill_dir = os.path.join(workspace, "skills", name)
    
    # 使用纳秒时间戳确保绝对唯一
    timestamp = time.time_ns()
    archive_dir = os.path.join(workspace, "skills", ".archived", f"{name}_{timestamp}")
    
    if not os.path.exists(skill_dir):
        return {"status": "error", "reason": f"Skill '{name}' not found."}
        
    try:
        os.makedirs(os.path.dirname(archive_dir), exist_ok=True)
        shutil.move(skill_dir, archive_dir)
        return {"status": "success", "message": f"Skill '{name}' archived to {name}_{timestamp}."}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def list_skills() -> dict:
    """👁️ 获取工作区内所有已安装的技能列表 (排除 .archived)"""
    workspace = _get_workspace()
    skills_dir = os.path.join(workspace, "skills")
    
    if not os.path.exists(skills_dir):
        return {"status": "success", "skills": []}
        
    skills = []
    for item in os.listdir(skills_dir):
        if item.startswith("."): continue # Skip hidden folders
        
        skill_file = os.path.join(skills_dir, item, "SKILL.md")
        if os.path.isdir(os.path.join(skills_dir, item)) and os.path.exists(skill_file):
            try:
                with open(skill_file, "r", encoding="utf-8") as f:
                    content = f.read()
                metadata, _, _ = _parse_yaml_frontmatter(content)
                metadata["path"] = skill_file
                skills.append(metadata)
            except:
                continue
    return {"status": "success", "count": len(skills), "skills": skills}

def read_skill(name: str) -> dict:
    """📖 读取指定技能的完整内容"""
    err = _validate_skill_name(name)
    if err: return {"status": "error", "reason": err}
    
    workspace = _get_workspace()
    file_path = os.path.join(workspace, "skills", name, "SKILL.md")
    
    if not os.path.exists(file_path):
        return {"status": "error", "reason": f"Skill '{name}' not found."}
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return {"status": "success", "content": f.read()}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

# ==========================================
# 📊 核心能力 I: Telemetry
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
