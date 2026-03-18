---
name: git-commits
description: "Use when the user asks to 'show my commits', 'list my commits', 'git commits', 'commit summary', 'commit log', 'what did I commit', 'show my work log', 'zoznam commitov', 'čo som commitol', or wants a summary of their git commit activity across repositories for a date range. Invoked as /git-commits with date parameters in YYYY-MM-DD format."
argument-hint: <from YYYY-MM-DD> [to YYYY-MM-DD]
allowed-tools: [Bash, Read]
---

# Git Commits Summary

Fetch and display a summary of all git commits across repositories for a date range.

## Arguments

The user invoked this with: $ARGUMENTS

Expected format: `<from_date> [to_date]` where dates are in `YYYY-MM-DD` format.
If only one date is provided, it is used as the start date and today is used as the end date.

Examples:
- `/git-commits 2026-03-01 2026-03-31` — specific range
- `/git-commits 2026-03-01` — from March 1st until today
- `/git-commits 2026-01-01 2026-12-31` — full year

## Instructions

1. Parse `$ARGUMENTS` to extract two dates in `YYYY-MM-DD` format.
   - If no arguments provided, default to the current month (first day to today).
   - If only one date provided, use it as start date with today as end date.

2. Determine the path to this skill's scripts directory. Use the appropriate home directory path:
   - **macOS/Linux**: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/git-commits/skills/git-commits/scripts/git_commits.py`
   - **Windows**: `%USERPROFILE%\.claude\plugins\marketplaces\claude-plugins-official\plugins\git-commits\skills\git-commits\scripts\git_commits.py`

3. Run the script (use `python3` on macOS/Linux, `python` on Windows):
   ```bash
   python3 ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/git-commits/skills/git-commits/scripts/git_commits.py <from_date> <to_date>
   ```

4. Present the script output directly to the user as markdown. The output is already formatted as a markdown table grouped by date.

5. If the script fails:
   - If config.json is missing: tell the user to configure `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/git-commits/config.json` with their `scan_paths` and `author_email`.
   - If no commits found: suggest checking the date range and config settings.
   - If API auth fails: suggest setting the appropriate token environment variable or installing `gh` CLI.

## Configuration

The config file is at `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/git-commits/config.json`.

Key settings:
- `scan_paths`: directories to scan for git repos (e.g., `["~/WAME", "~/Projects"]`)
- `author_email`: git author email to filter commits
- `author_names`: alternative author names to try
- `apis.github/gitlab/bitbucket.enabled`: enable API fetching for remote-only repos
