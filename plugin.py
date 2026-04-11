"""
CoPaw Evolution Engine - Plugin Entry (v4.6.0)
Refactored to strictly follow PluginApi definition.
"""
import os
import logging

logger = logging.getLogger(__name__)

class EvolutionPlugin:
    """
    Official CoPaw Plugin Definition.
    Implements register(api) method.
    """
    name = "evolution_engine"
    version = "4.6.0"
    description = "Self-evolving skill engine with MCP tools."

    def register(self, api):
        """
        Called by CoPaw loader.
        
        Args:
            api: PluginApi instance.
                 Available attributes: plugin_id, config, manifest, runtime
        """
        logger.info(f"[{self.name}] Registering plugin via PluginApi...")
        
        # Safe way to get home dir (No 'env' attribute in PluginApi)
        home_dir = os.path.expanduser('~')
        workspace = os.path.join(home_dir, ".copaw", "plugins", self.name)
        
        try:
            # Init workspace directories
            os.makedirs(os.path.join(workspace, "skills"), exist_ok=True)
            os.makedirs(os.path.join(workspace, "skills", ".archived"), exist_ok=True)
            os.makedirs(os.path.join(workspace, "skills", ".backup"), exist_ok=True)
            logger.info(f"[{self.name}] Workspace ready: {workspace}")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to init workspace: {e}")

# Mandatory export for CoPaw loader
plugin = EvolutionPlugin()
