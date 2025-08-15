#!/bin/bash
# Fabric Pattern Studio launcher (PR-1)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🎭 Starting Fabric Pattern Studio (Modular Architecture)"
echo "----------------------------------------"
echo "Entry point: app/main.py"
echo "Logs: ~/.config/fabric/logs/"
echo ""

streamlit run app/main.py "$@"