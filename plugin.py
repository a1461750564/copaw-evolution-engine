"""
CoPaw Evolution Engine - Plugin Entry (v4.6.0)
Refactored to match CoPaw's official plugin interface.
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

class EvolutionPlugin:
    """
    Official CoPaw Plugin Definition.
    Must expose a 'register(api)' method.
    """
    name = "evolution_engine"
    version = "4.6.0"
    description = "Self-evolving skill engine with MCP tools for creation, feedback, and pruning."

    def register(self, api):
        """
        Called by CoPaw loader.
        
        Args:
            api: PluginApi instance (provides env, config, log, etc.)
        """
        self.api = api
        logger.info(f"Registering {self.name} v{self.version}...")
        
        # Auto-init workspace using PluginApi environment
        # api.env.home_dir is usually ~/.copaw
        workspace = os.path.join(api.env.home_dir, "plugins", self.name)
        
        try:
            os.makedirs(os.path.join(workspace, "skills"), exist_ok=True)
            os.makedirs(os.path.join(workspace, "skills", ".archived"), exist_ok=True)
            os.makedirs(os.path.join(workspace, "skills", ".backup"), exist_ok=True)
            logger.info(f"[{self.name}] Workspace ready: {workspace}")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to init workspace: {e}")

# Mandatory export for CoPaw loader
plugin = EvolutionPlugin()
