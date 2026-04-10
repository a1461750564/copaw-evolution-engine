#!/bin/bash
# CoPaw Evolution Engine - Installer
# Usage: bash install.sh

set -e

echo "🚀 Starting CoPaw Evolution Engine Installation..."

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required."
    exit 1
fi

# 2. Run the safe Python installer
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
python3 "$SCRIPT_DIR/scripts/install_copaw_plugin.py"
