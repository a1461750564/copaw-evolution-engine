#!/usr/bin/env python3
"""
Dream System Auto-Installer (v4.2)
Sets up the Evolution Engine MCP and deploys the Dream System skill to a CoPaw Agent workspace.
"""
import json
import os
import shutil
import sys
import glob
from pathlib import Path

def find_venv_python():
    """Try to find the CoPaw venv python."""
    candidates = [
        os.path.expanduser("~/.copaw/venv/bin/python3"),
        os.path.expanduser("~/.copaw/venv/bin/python"),
        sys.executable # Fallback to current
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return "python3"

def main():
    print("🌙 Dream System Installer v4.2")
    
    # 1. Determine Plugin Path (Where this script is running from)
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if we are in the actual plugin directory
    mcp_script = script_dir / "mcp_server.py"
    if not mcp_script.exists():
        print("❌ Error: mcp_server.py not found. Please run this script from the plugin directory.")
        sys.exit(1)
        
    print(f"📂 Plugin detected at: {script_dir}")
    
    # 2. Find Python Interpreter
    python_path = find_venv_python()
    print(f"🐍 Using Python: {python_path}")

    # 3. Determine Workspace
    copaw_home = Path(os.path.expanduser("~/.copaw"))
    workspace_dir = copaw_home / "workspaces"
    
    # Auto-detect logic
    # If we are running inside a workspace (unlikely for install script but possible), use it
    # Or use the first workspace found if only one exists
    
    target_agent_dir = None
    if os.environ.get("COPAW_WORKING_DIR"):
        target_agent_dir = Path(os.environ["COPAW_WORKING_DIR"])
    elif workspace_dir.exists():
        agents = list(workspace_dir.iterdir())
        if len(agents) == 1:
            target_agent_dir = agents[0]
            print(f"🤖 Auto-detected Agent: {target_agent_dir.name}")
        elif len(agents) > 1:
            print("Multiple agents found. Please select one:")
            for i, a in enumerate(agents):
                print(f"  [{i}] {a.name}")
            try:
                idx = int(input("Index: "))
                target_agent_dir = agents[idx]
            except:
                print("Invalid input.")
                sys.exit(1)
    
    if not target_agent_dir or not (target_agent_dir / "agent.json").exists():
        print("❌ Could not find a valid CoPaw Agent workspace with agent.json.")
        sys.exit(1)

    print(f"🎯 Targeting Agent: {target_agent_dir.name}")
    
    # 4. Patch agent.json
    agent_json_path = target_agent_dir / "agent.json"
    with open(agent_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    mcp_config = config.get("mcp", {})
    clients = mcp_config.get("clients", {})
    
    # Construct the MCP entry
    new_mcp = {
        "name": "evolution_engine",
        "description": "CoPaw Evolution Engine MCP Server (v4.6.1)",
        "enabled": True,
        "transport": "stdio",
        "url": "",
        "headers": {},
        "command": python_path,
        "args": [str(mcp_script)],
        "cwd": str(script_dir)
    }
    
    # Check if exists and matches
    if "evolution_engine" in clients:
        existing = clients["evolution_engine"]
        # Simple check
        if existing.get("cwd") == str(script_dir):
            print("✅ MCP config already up-to-date.")
        else:
            print("🔄 Updating existing MCP config...")
            clients["evolution_engine"] = new_mcp
            # Write back
            config["mcp"] = {"clients": clients} # Preserve structure
            with open(agent_json_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print("✅ Updated agent.json")
    else:
        print("🔌 Injecting MCP config...")
        clients["evolution_engine"] = new_mcp
        config["mcp"] = {"clients": clients}
        
        # Backup
        shutil.copy2(agent_json_path, agent_json_path.with_suffix(".json.bak"))
        with open(agent_json_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print("✅ Injected into agent.json (Backup saved)")

    # 5. Deploy Skill
    skill_src = script_dir / "skills" / "dream_system"
    if skill_src.exists():
        skill_dst = target_agent_dir / "skills" / "dream_system"
        if skill_dst.exists():
            shutil.rmtree(skill_dst)
        shutil.copytree(skill_src, skill_dst)
        print(f"✅ Installed Skill: dream_system (v4.2)")
    else:
        print("⚠️  Skill source 'skills/dream_system' not found. Skipping.")

    print("\n🎉 All Done!")
    print("1. Restart your CoPaw Agent.")
    print("2. Wait for MCP 'evolution_engine' to connect.")
    print("3. Trigger '/dream' to test.")

if __name__ == "__main__":
    main()
