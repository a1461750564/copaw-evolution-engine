#!/bin/bash
# CoPaw Evolution Engine - Uninstaller
# Usage: bash uninstall.sh

set -e

echo "🗑️  Starting CoPaw Evolution Engine Uninstallation..."

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required."
    exit 1
fi

# 2. Run the safe Python uninstaller
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
python3 "$SCRIPT_DIR/scripts/uninstall_copaw_plugin.py"
