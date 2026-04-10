#!/usr/bin/env python3
"""
CoPaw Evolution Engine - Safe Installer
Handles injection into agent.json safely without corrupting JSON.
"""

import json
import os
import shutil
import sys
from pathlib import Path

def find_copaw_workspaces():
    """Find all active CoPaw workspaces."""
    base = Path.home() / ".copaw" / "workspaces"
    if not base.exists():
        print("❌ Error: ~/.copaw/workspaces not found. Is CoPaw installed?")
        sys.exit(1)
    
    workspaces = []
    for ws in base.iterdir():
        agent_json = ws / "agent.json"
        if ws.is_dir() and agent_json.exists():
            workspaces.append(ws)
    
    return workspaces

def get_plugin_path():
    """Get absolute path to this plugin directory."""
    # Assumes script is running from the plugin dir or knows its location
    return Path(__file__).parent.parent.absolute()

def install_plugin(workspace_dir):
    """Inject configuration into a specific workspace's agent.json."""
    agent_json = workspace_dir / "agent.json"
    plugin_dir = get_plugin_path()
    mcp_script = plugin_dir / "mcp_server.py"
    
    if not mcp_script.exists():
        print(f"  ❌ Error: mcp_server.py not found at {mcp_script}")
        return False

    print(f"  🛠  Updating {agent_json}...")
    
    try:
        with open(agent_json, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # CoPaw MCP config structure
        mcp_servers = config.get("mcp_servers", {})
        
        # Prepare new config
        new_entry = {
            "enabled": True,
            "command": sys.executable,  # Use current python
            "args": [str(mcp_script)],
            "env": {
                "COPAW_WORKING_DIR": str(workspace_dir),
                "PYTHONPATH": str(plugin_dir)
            }
        }
        
        if "evolution_engine" in mcp_servers:
            print(f"  ⚠️  evolution_engine already exists. Updating...")
        else:
            print(f"  ✨ Injecting evolution_engine configuration...")
            
        mcp_servers["evolution_engine"] = new_entry
        config["mcp_servers"] = mcp_servers
        
        # Backup
        backup = agent_json.with_suffix('.json.bak')
        shutil.copy(agent_json, backup)
        
        # Write
        with open(agent_json, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
        print(f"  ✅ Successfully configured workspace: {workspace_dir.name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to update {agent_json}: {e}")
        return False

def main():
    print("🚀 CoPaw Evolution Engine Installer v3.0")
    print("-" * 40)
    
    # 1. Check CoPaw
    workspaces = find_copaw_workspaces()
    if not workspaces:
        print("No workspaces found. Please run CoPaw at least once.")
        sys.exit(1)
        
    print(f"🔍 Found {len(workspaces)} workspace(s): {[w.name for w in workspaces]}")
    
    # 2. Ask user which workspace
    print("\nSelect workspace to install:")
    for i, ws in enumerate(workspaces):
        print(f"  [{i}] {ws.name}")
    print(f"  [a] All")
    
    choice = input("Choice: ").strip().lower()
    
    selected = []
    if choice == 'a':
        selected = workspaces
    elif choice.isdigit():
        idx = int(choice)
        if 0 <= idx < len(workspaces):
            selected = [workspaces[idx]]
    else:
        print("Invalid choice.")
        sys.exit(1)
        
    # 3. Install
    success_count = 0
    for ws in selected:
        if install_plugin(ws):
            success_count += 1
            
    print("-" * 40)
    if success_count > 0:
        print("✅ Installation complete!")
        print("💡 Please restart CoPaw (`copaw stop && copaw start`) to apply changes.")
        print("📦 Skills will be saved to: ~/.copaw/workspaces/<name>/skills/")
    else:
        print("❌ Installation failed or skipped.")

if __name__ == "__main__":
    main()
