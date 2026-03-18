#!/usr/bin/env bash
set -euo pipefail

# Claude Code Plugin: git-commits — uninstaller

PLUGIN_NAME="git-commits"
PLUGINS_DIR="$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins"
TARGET_DIR="$PLUGINS_DIR/$PLUGIN_NAME"

echo "=== git-commits plugin uninstaller ==="
echo ""

if [ ! -e "$TARGET_DIR" ]; then
    echo "Plugin is not installed."
    exit 0
fi

if [ -L "$TARGET_DIR" ]; then
    rm "$TARGET_DIR"
    echo "Symlink removed: $TARGET_DIR"
else
    echo "Warning: $TARGET_DIR is not a symlink. Remove it manually."
    exit 1
fi

echo ""
echo "Plugin uninstalled. Restart Claude Code session for changes to take effect."
echo "Note: Your config.json was preserved in the plugin directory."
