"""
CoPaw Evolution Engine - Plugin Entry
"""
import os
import json
from copaw.plugins.base import PluginBase

class EvolutionPlugin(PluginBase):
    name = "evolution_engine"
    version = "4.6.0"
    description = "Self-evolving skill engine with MCP tools for creation, feedback, and pruning."

    def on_load(self):
        self.log.info(f"Loading {self.name} v{self.version}...")
        
        # Auto-init workspace
        workspace = os.path.join(self.env.home_dir, "plugins", self.name)
        os.makedirs(os.path.join(workspace, "skills"), exist_ok=True)
        os.makedirs(os.path.join(workspace, "skills", ".archived"), exist_ok=True)
        os.makedirs(os.path.join(workspace, "skills", ".backup"), exist_ok=True)
        
        self.log.info(f"Workspace ready: {workspace}")

    def on_unload(self):
        self.log.info(f"Unloading {self.name}")
        
    def on_mcp_ready(self):
        self.log.info(f"{self.name} MCP server is ready.")
