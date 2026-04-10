"""Evolution Monitor Script (v2.0).

CLI interface for the CoPaw Evolution Engine.
Uses the same robust logic as the MCP Server (Atomic writes, Strict Schema).
"""
import sys
import json
import os
import uuid
import time
import shutil
import re
from datetime import datetime, timezone
from pathlib import Path

# --- Constants ---
COPAW_SCHEMA_VERSION = "workspace-skill-manifest.v1"
SKILL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

# --- Utils ---
class AtomicDirLock:
    def __init__(self, lock_path, timeout=5.0):
        self.lock_path = lock_path
        self.timeout = timeout

    def __enter__(self):
        start_time = time.time()
        while True:
            try:
                os.mkdir(self.lock_path)
                return self
            except FileExistsError:
                if time.time() - start_time > self.timeout:
                    raise TimeoutError(f"Lock timeout: {self.lock_path}")
                time.sleep(0.1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            os.rmdir(self.lock_path)
        except (FileNotFoundError, OSError):
            pass

def get_copaw_timestamp():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

def ensure_dirs(base_dir):
    (base_dir / "memory" / "evolution").mkdir(parents=True, exist_ok=True)
    (base_dir / "skills" / "evolved").mkdir(parents=True, exist_ok=True)

def register_skill(base_dir, name, desc, is_update=False):
    skill_json_path = base_dir / "skill.json"
    lock_dir = skill_json_path.with_suffix('.lock.d')
    
    timestamp = get_copaw_timestamp()
    version = "2.0.0" if is_update else "1.0.0"
    commit_text = "auto-updated" if is_update else "auto-evolved"
    
    new_skill_entry = {
        "enabled": True,
        "channels": ["all"],
        "source": "customized",
        "metadata": {
            "name": name,
            "description": desc,
            "version_text": version,
            "commit_text": commit_text,
            "signature": "",
            "source": "customized",
            "protected": False,
            "requirements": { "require_bins": [], "require_envs": [] }
        },
        "requirements": { "require_bins": [], "require_envs": [] },
        "updated_at": timestamp,
        "config": {}
    }

    try:
        with AtomicDirLock(str(lock_dir)):
            if skill_json_path.exists():
                try:
                    content = skill_json_path.read_text(encoding="utf-8")
                    data = json.loads(content) if content.strip() else {}
                except json.JSONDecodeError:
                    skill_json_path.rename(skill_json_path.with_suffix('.json.corrupt'))
                    data = {}
            else:
                data = {"schema_version": COPAW_SCHEMA_VERSION}

            if "schema_version" not in data:
                data["schema_version"] = COPAW_SCHEMA_VERSION
            if "skills" not in data:
                data["skills"] = {}

            data["skills"][name] = new_skill_entry
            data["version"] = int(time.time() * 1000)

            tmp_path = skill_json_path.with_suffix('.json.tmp')
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(str(tmp_path), str(skill_json_path))
        return True
    except Exception as e:
        raise e

def cmd_init():
    workspace = os.environ.get("COPAW_WORKING_DIR", os.getcwd())
    base_dir = Path(workspace)
    ensure_dirs(base_dir)
    print(f"✅ Evolution Engine initialized in {workspace}.")

def cmd_skill(name, desc, instructions_file=None, commands_file=None):
    workspace = os.environ.get("COPAW_WORKING_DIR", os.getcwd())
    base_dir = Path(workspace)
    ensure_dirs(base_dir)

    # Validation
    if not SKILL_NAME_PATTERN.match(name):
        print("❌ Invalid skill name. Use only letters, numbers, hyphens, and underscores.")
        sys.exit(1)

    skill_dir = base_dir / "skills" / "evolved" / name
    is_update = skill_dir.exists()

    # Create Directory
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # Skill ID
    skill_id_path = skill_dir / ".skill_id"
    if not skill_id_path.exists():
        skill_id_path.write_text(str(uuid.uuid4()), encoding="utf-8")
    
    skill_id = skill_id_path.read_text(encoding="utf-8").strip()

    # Write SKILL.md
    md_content = instructions_file
    if not md_content:
        md_content = f"# {name}\n\n> {desc}\n\n"
        if commands_file:
            md_content += "## Commands\n\n" + commands_file
    (skill_dir / "SKILL.md").write_text(md_content, encoding="utf-8")

    # Register
    try:
        register_skill(base_dir, name, desc, is_update)
        mode = "Updated" if is_update else "Created"
        print(f"✅ Skill '{name}' {mode} and registered in skill.json.")
    except Exception as e:
        print(f"❌ Failed to register: {e}")
        if not is_update: shutil.rmtree(skill_dir)

def cmd_error(error_type, message, context_json=None):
    workspace = os.environ.get("COPAW_WORKING_DIR", os.getcwd())
    base_dir = Path(workspace)
    ensure_dirs(base_dir)
    
    log_file = base_dir / "memory" / "evolution" / "errors.jsonl"
    entry = {
        "timestamp": get_copaw_timestamp(),
        "type": error_type,
        "message": message,
        "context": context_json or {}
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print("✅ Error logged.")

def cmd_experience(action, result, tags=None, metadata_json=None):
    workspace = os.environ.get("COPAW_WORKING_DIR", os.getcwd())
    base_dir = Path(workspace)
    ensure_dirs(base_dir)
    
    log_file = base_dir / "memory" / "evolution" / "experiences.jsonl"
    entry = {
        "timestamp": get_copaw_timestamp(),
        "action": action,
        "result": result,
        "tags": tags or [],
        "metadata": metadata_json or {}
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print("✅ Experience logged.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CoPaw Evolution Monitor CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Init
    subparsers.add_parser("init")

    # Skill
    p_skill = subparsers.add_parser("skill", aliases=["create_skill"])
    p_skill.add_argument("name")
    p_skill.add_argument("description")
    p_skill.add_argument("--instructions", type=str, help="Path to MD file or raw string")
    p_skill.add_argument("--commands", type=str, help="JSON commands array")

    # Error
    p_err = subparsers.add_parser("log_error")
    p_err.add_argument("type")
    p_err.add_argument("message")
    p_err.add_argument("--context", type=str)

    # Exp
    p_exp = subparsers.add_parser("log_experience")
    p_exp.add_argument("action")
    p_exp.add_argument("result")
    p_exp.add_argument("--tags", type=str)
    p_exp.add_argument("--metadata", type=str)

    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command in ["skill", "create_skill"]:
        instructions = None
        commands = None
        if args.instructions:
            if os.path.exists(args.instructions):
                instructions = Path(args.instructions).read_text()
            else:
                instructions = args.instructions
        if args.commands:
            commands = args.commands
            instructions = instructions or ""
            instructions += f"\n## Commands\n{commands}"
        cmd_skill(args.name, args.description, instructions)
    elif args.command == "log_error":
        ctx = json.loads(args.context) if args.context else {}
        cmd_error(args.type, args.message, ctx)
    elif args.command == "log_experience":
        tags = args.tags.split(",") if args.tags else []
        meta = json.loads(args.metadata) if args.metadata else {}
        cmd_experience(args.action, args.result, tags, meta)
    else:
        parser.print_help()
