#!/usr/bin/env bash
set -euo pipefail

# Claude Code Plugin: git-commits
# Installs the plugin by symlinking into ~/.claude/plugins/

PLUGIN_NAME="git-commits"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins"
TARGET_DIR="$PLUGINS_DIR/$PLUGIN_NAME"

echo "=== git-commits plugin installer ==="
echo ""

# Check if Claude Code plugins directory exists
if [ ! -d "$HOME/.claude/plugins" ]; then
    echo "Error: ~/.claude/plugins directory not found."
    echo "Make sure Claude Code CLI is installed first."
    exit 1
fi

# Create marketplace directory if needed
mkdir -p "$PLUGINS_DIR"

# Check if already installed
if [ -e "$TARGET_DIR" ]; then
    if [ -L "$TARGET_DIR" ]; then
        echo "Plugin already installed (symlink exists)."
        echo "  $TARGET_DIR -> $(readlink "$TARGET_DIR")"
        read -p "Reinstall? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 0
        fi
        rm "$TARGET_DIR"
    else
        echo "Existing plugin directory found at $TARGET_DIR (not a symlink)."
        echo "This will be replaced with a symlink to this repo."
        # Preserve config.json if it exists
        if [ -f "$TARGET_DIR/config.json" ]; then
            echo "Backing up existing config.json..."
            cp "$TARGET_DIR/config.json" "$SCRIPT_DIR/config.json"
        fi
        read -p "Replace with symlink? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 0
        fi
        rm -rf "$TARGET_DIR"
    fi
fi

# Create symlink
ln -s "$SCRIPT_DIR" "$TARGET_DIR"
echo "Symlink created: $TARGET_DIR -> $SCRIPT_DIR"

# Handle config.json
CONFIG_FILE="$SCRIPT_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    cp "$SCRIPT_DIR/config.example.json" "$CONFIG_FILE"
    echo ""
    echo "Created config.json from template."
    echo ""
    echo "IMPORTANT: Edit config.json with your settings:"
    echo "  $CONFIG_FILE"
    echo ""
    echo "  1. Set scan_paths to directories where your git repos are"
    echo "  2. Set author_email to your git email"
    echo "  3. Set author_names to your name(s) used in git commits"
    echo ""

    # Try to auto-detect git user info
    GIT_EMAIL=$(git config --global user.email 2>/dev/null || echo "")
    GIT_NAME=$(git config --global user.name 2>/dev/null || echo "")

    if [ -n "$GIT_EMAIL" ] || [ -n "$GIT_NAME" ]; then
        echo "Detected git config:"
        [ -n "$GIT_EMAIL" ] && echo "  email: $GIT_EMAIL"
        [ -n "$GIT_NAME" ] && echo "  name:  $GIT_NAME"
        echo ""
        read -p "Auto-fill config.json with these values? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            if command -v python3 &>/dev/null; then
                python3 -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
if '$GIT_EMAIL':
    config['author_email'] = '$GIT_EMAIL'
if '$GIT_NAME':
    config['author_names'] = ['$GIT_NAME']
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
    f.write('\n')
"
                echo "Config updated with git user info."
            else
                echo "Python3 not found, please edit config.json manually."
            fi
        fi
    fi
else
    echo "config.json already exists, skipping."
fi

echo ""
echo "Installation complete!"
echo ""
echo "Usage in Claude Code CLI:"
echo "  /git-commits 2026-03-01 2026-03-31    # specific range"
echo "  /git-commits 2026-03-01               # from date until today"
echo ""
echo "Standalone usage:"
echo "  python3 $SCRIPT_DIR/skills/git-commits/scripts/git_commits.py 2026-03-01 2026-03-31"
echo ""
echo "NOTE: Restart your Claude Code session for the skill to appear in /help."
