#!/usr/bin/env python3
"""
CoPaw Evolution Engine - Safe Installer v3.1
Handles injection into agent.json safely, with post-install health check
and automatic configuration rollback on failure.

Changes in v3.1:
  - Added logging to install.log
  - Post-install health check (agent.json validation + mcp_server.py syntax check)
  - Automatic rollback on health check failure
  - Uses subprocess.run exclusively (no os.system)
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

# --- Logging Setup ---
LOG_DIR = Path(__file__).parent.parent
LOG_FILE = LOG_DIR / "install.log"

def setup_logger():
    """Configure logger to write to both install.log and stderr."""
    logger = logging.getLogger("evolution_installer")
    logger.setLevel(logging.DEBUG)

    # File handler (install.log)
    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    # Console handler (stderr for interactive use)
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    return logger

logger = setup_logger()


def find_copaw_workspaces():
    """Find all active CoPaw workspaces."""
    base = Path.home() / ".copaw" / "workspaces"
    if not base.exists():
        logger.error("Error: ~/.copaw/workspaces not found. Is CoPaw installed?")
        sys.exit(1)

    workspaces = []
    for ws in base.iterdir():
        agent_json = ws / "agent.json"
        if ws.is_dir() and agent_json.exists():
            workspaces.append(ws)

    return workspaces


def get_plugin_path():
    """Get absolute path to this plugin directory."""
    return Path(__file__).parent.parent.absolute()


def rollback_agent_json(workspace_dir, agent_json, log_prefix=""):
    """
    Atomically restore agent.json from its .bak backup.

    Args:
        workspace_dir: Path to workspace
        agent_json: Path to agent.json
        log_prefix: Optional prefix for log messages

    Returns:
        True if rollback succeeded, False otherwise
    """
    backup = agent_json.with_suffix(".json.bak")
    prefix = f"[{log_prefix}] " if log_prefix else ""

    if not backup.exists():
        logger.error(f"{prefix}Rollback FAILED: backup file {backup} not found")
        return False

    try:
        # Validate backup is valid JSON before restoring (prevent secondary corruption)
        with open(backup, "r", encoding="utf-8") as f:
            json.load(f)  # Validate structure

        # Atomic-ish restore: write to temp, then rename
        temp_file = agent_json.with_suffix(".json.tmp")
        shutil.copy2(backup, temp_file)
        os.replace(str(temp_file), str(agent_json))  # Atomic on POSIX

        logger.info(f"{prefix}Rollback OK: {agent_json} restored from backup")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"{prefix}Rollback ABORTED: backup is corrupt ({e})")
        return False
    except Exception as e:
        logger.error(f"{prefix}Rollback FAILED: {e}")
        return False


def health_check(workspace_dir, mcp_server_path):
    """
    Run post-installation health checks.

    Checks:
      1. agent.json is valid JSON and parseable
      2. mcp_server.py has valid Python syntax
      3. mcp_server.py can be imported without error (tool schema check)

    Returns:
        (bool, str): (passed, detail_message)
    """
    agent_json = workspace_dir / "agent.json"

    # Check 1: agent.json is valid JSON
    try:
        with open(agent_json, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"agent.json parse error: {e}"
    except Exception as e:
        return False, f"agent.json read error: {e}"

    # Check 2: evolution_engine entry exists in mcp_servers
    mcp_servers = config.get("mcp_servers", {})
    if "evolution_engine" not in mcp_servers:
        return False, "evolution_engine entry missing from mcp_servers"

    # Check 3: mcp_server.py syntax validation via py_compile (subprocess, not os.system)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(mcp_server_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, f"mcp_server.py syntax error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "mcp_server.py syntax check timed out (10s)"
    except Exception as e:
        return False, f"mcp_server.py syntax check failed: {e}"

    # Check 4: Verify mcp_server.py can load tool schema
    # Run a lightweight import check via subprocess
    check_script = (
        f"import sys; sys.path.insert(0, {str(mcp_server_path.parent)!r}); "
        f"from mcp_server import TOOLS; "
        f"assert len(TOOLS) > 0, 'TOOLS is empty'; "
        f"print(f'OK: {len(TOOLS)} tools loaded')"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", check_script],
            capture_output=True,
            text=True,
            timeout=15,
            env={**os.environ, "COPAW_WORKING_DIR": str(workspace_dir)},
        )
        if result.returncode != 0:
            return False, f"mcp_server.py tool load failed: {result.stderr.strip()}"
        if "OK:" not in result.stdout:
            return False, f"mcp_server.py unexpected output: {result.stdout.strip()}"
    except subprocess.TimeoutExpired:
        return False, "mcp_server.py tool load timed out (15s)"
    except Exception as e:
        return False, f"mcp_server.py tool load check failed: {e}"

    return True, "All health checks passed"


def install_plugin(workspace_dir):
    """Inject configuration into a specific workspace's agent.json."""
    agent_json = workspace_dir / "agent.json"
    plugin_dir = get_plugin_path()
    mcp_script = plugin_dir / "mcp_server.py"

    if not mcp_script.exists():
        logger.error(f"mcp_server.py not found at {mcp_script}")
        return False

    logger.info(f"Updating {agent_json}...")

    try:
        with open(agent_json, "r", encoding="utf-8") as f:
            config = json.load(f)

        # CoPaw MCP config structure
        mcp_servers = config.get("mcp_servers", {})

        # Prepare new config
        new_entry = {
            "enabled": True,
            "command": sys.executable,
            "args": [str(mcp_script)],
            "env": {
                "COPAW_WORKING_DIR": str(workspace_dir),
                "PYTHONPATH": str(plugin_dir),
            },
        }

        if "evolution_engine" in mcp_servers:
            logger.warning("evolution_engine already exists. Updating...")
        else:
            logger.info("Injecting evolution_engine configuration...")

        mcp_servers["evolution_engine"] = new_entry
        config["mcp_servers"] = mcp_servers

        # Backup (before writing)
        backup = agent_json.with_suffix(".json.bak")
        shutil.copy2(agent_json, backup)
        logger.info(f"Backup created: {backup}")

        # Write
        with open(agent_json, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully configured workspace: {workspace_dir.name}")

        # --- v3.1: Post-install health check ---
        ws_name = workspace_dir.name
        logger.info(f"Running post-install health check for [{ws_name}]...")
        passed, detail = health_check(workspace_dir, mcp_script)

        if passed:
            logger.info(f"Health check PASSED for [{ws_name}]: {detail}")
            return True
        else:
            logger.error(f"Health check FAILED for [{ws_name}]: {detail}")
            logger.info(f"Triggering automatic rollback for [{ws_name}]...")
            rollback_ok = rollback_agent_json(workspace_dir, agent_json, log_prefix=ws_name)
            if rollback_ok:
                logger.warning(f"Rollback completed for [{ws_name}]. Installation reverted.")
            else:
                logger.critical(
                    f"CRITICAL: Rollback FAILED for [{ws_name}]! "
                    f"agent.json may be corrupted. Manual intervention required."
                )
            return False

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse {agent_json}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to update {agent_json}: {e}")
        return False


def main():
    logger.info("=" * 50)
    logger.info("CoPaw Evolution Engine Installer v3.1")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 50)

    # 1. Check CoPaw
    workspaces = find_copaw_workspaces()
    if not workspaces:
        logger.error("No workspaces found. Please run CoPaw at least once.")
        sys.exit(1)

    logger.info(f"Found {len(workspaces)} workspace(s): {[w.name for w in workspaces]}")

    # 2. Determine target workspaces
    # Check for --all flag
    if "--all" in sys.argv or "-a" in sys.argv:
        selected = workspaces
        logger.info(f"Flag --all detected. Targeting all {len(selected)} workspaces.")
    elif "--yes" in sys.argv or "-y" in sys.argv:
        # Default to first one if --yes but not --all (for quick install)
        selected = [workspaces[0]]
        logger.info(f"Flag --yes detected. Targeting default workspace: {selected[0].name}")
    else:
        # Interactive mode
        print("\nSelect workspace to install:")
        for i, ws in enumerate(workspaces):
            print(f"  [{i}] {ws.name}")
        print(f"  [a] All")

        choice = input("Choice: ").strip().lower()

        selected = []
        if choice == "a":
            selected = workspaces
        elif choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(workspaces):
                selected = [workspaces[idx]]
        else:
            logger.error("Invalid choice.")
            sys.exit(1)

    # 3. Install
    success_count = 0
    for ws in selected:
        if install_plugin(ws):
            success_count += 1

    logger.info("-" * 40)
    if success_count > 0:
        logger.info("Installation complete!")
        logger.info("Please restart CoPaw (`copaw stop && copaw start`) to apply changes.")
        logger.info(f"Skills will be saved to: ~/.copaw/workspaces/<name>/skills/")
    else:
        logger.warning("Installation failed or was rolled back for all selected workspaces.")

    logger.info(f"Full log: {LOG_FILE}")


if __name__ == "__main__":
    main()
