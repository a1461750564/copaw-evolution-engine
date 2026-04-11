#!/usr/bin/env python3
"""
CoPaw Evolution Engine - Plugin Entry Point
This module is loaded by CoPaw at startup.
"""
import sys
import os
from pathlib import Path

# Ensure 'lib' is in path for imports
sys.path.append(str(Path(__file__).parent))

class EvolutionPlugin:
    """Plugin entry point for CoPaw."""

    async def register(self, api):
        """
        Register the plugin with CoPaw.
        
        Args:
            api (PluginApi): The plugin API interface.
        """
        print("[EvolutionEngine] Initializing Plugin...", file=sys.stderr)
        
        # 1. Workspace Initialization Hook
        async def on_startup():
            try:
                # Determine workspace
                ws_env = os.environ.get("COPAW_WORKING_DIR")
                if ws_env:
                    ws = Path(ws_env)
                else:
                    # Fallback logic usually not needed inside CoPaw context
                    ws = Path.cwd()

                # Create necessary directories
                dirs = [
                    ws / "memory" / "evolution",
                    ws / "skills" / "evolved"
                ]
                for d in dirs:
                    d.mkdir(parents=True, exist_ok=True)
                    print(f"[EvolutionEngine] Directory ready: {d}", file=sys.stderr)
                
                print("[EvolutionEngine] Plugin initialized successfully.", file=sys.stderr)
            except Exception as e:
                print(f"[EvolutionEngine] Error during init: {e}", file=sys.stderr)

        # Register the hook with high priority
        api.register_startup_hook("init_evolution_engine", on_startup, priority=10)

# Required export for CoPaw loader
plugin = EvolutionPlugin()