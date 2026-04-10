#!/usr/bin/env python3
"""
CoPaw Evolution Engine - Safe Uninstaller
Removes configuration from agent.json cleanly.
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
        return []
    
    workspaces = []
    for ws in base.iterdir():
        agent_json = ws / "agent.json"
        if ws.is_dir() and agent_json.exists():
            workspaces.append(ws)
    return workspaces

def uninstall_plugin(workspace_dir, remove_skills=False):
    """Remove configuration from a specific workspace's agent.json."""
    agent_json = workspace_dir / "agent.json"
    
    print(f"  🧹 Cleaning {agent_json}...")
    
    try:
        with open(agent_json, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        mcp_servers = config.get("mcp_servers", {})
        
        if "evolution_engine" in mcp_servers:
            del mcp_servers["evolution_engine"]
            config["mcp_servers"] = mcp_servers
            
            # Write back
            with open(agent_json, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"  ✅ Removed evolution_engine config.")
        else:
            print(f"  ℹ️  evolution_engine config not found. Nothing to remove.")
            
        # Optionally remove evolved skills
        if remove_skills:
            skills_dir = workspace_dir / "skills" / "evolved"
            if skills_dir.exists():
                shutil.rmtree(skills_dir)
                print(f"  🗑  Deleted evolved skills: {skills_dir}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to update {agent_json}: {e}")
        return False

def main():
    print("🗑️  CoPaw Evolution Engine Uninstaller")
    print("-" * 40)
    
    workspaces = find_copaw_workspaces()
    if not workspaces:
        print("No workspaces found.")
        sys.exit(1)
        
    # Check if config exists
    configured_workspaces = []
    for ws in workspaces:
        try:
            with open(ws / "agent.json") as f:
                data = json.load(f)
                if "evolution_engine" in data.get("mcp_servers", {}):
                    configured_workspaces.append(ws)
        except:
            pass
            
    if not configured_workspaces:
        print("ℹ️  Evolution Engine is not installed in any workspace.")
        sys.exit(0)
        
    print(f"🔍 Found installation in: {[w.name for w in configured_workspaces]}")
    
    choice = input("Remove from all? (y/n): ").strip().lower()
    if choice != 'y':
        print("Aborted.")
        sys.exit(0)
        
    remove_skills = input("Do you also want to DELETE all evolved skills? (y/n, default: n): ").strip().lower() == 'y'
    
    success_count = 0
    for ws in configured_workspaces:
        if uninstall_plugin(ws, remove_skills):
            success_count += 1
            
    print("-" * 40)
    if success_count > 0:
        print("✅ Uninstallation complete!")
        print("💡 Please restart CoPaw to finalize.")
    else:
        print("❌ Uninstallation failed.")

if __name__ == "__main__":
    main()
