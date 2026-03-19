---
name: git-commits
description: "Use when the user asks to 'show my commits', 'list my commits', 'git commits', 'commit summary', 'commit log', 'what did I commit', 'show my work log', 'zoznam commitov', 'čo som commitol', or wants a summary of their git commit activity across repositories for a date range. Invoked as /git-commits with date parameters in YYYY-MM-DD format."
argument-hint: [from YYYY-MM-DD] [to YYYY-MM-DD]
allowed-tools: [Bash, Read]
---

# Git Commits Summary

Fetch and display a summary of all git commits across repositories for a date range.

## Arguments

The user invoked this with: $ARGUMENTS

Expected format: `[from_date] [to_date]` where dates are in `YYYY-MM-DD` format.
- If no arguments provided, default to the current month (1st day to today).
- If only one date provided, use it as start date with today as end date.

Examples:
- `/git-commits` — current month (1st to today)
- `/git-commits 2026-03-01 2026-03-31` — specific range
- `/git-commits 2026-03-01` — from March 1st until today
- `/git-commits 2026-01-01 2026-12-31` — full year

## Instructions

1. Parse `$ARGUMENTS` to extract two dates in `YYYY-MM-DD` format.
   - If no arguments provided, default to the current month (first day to today).
   - If only one date provided, use it as start date with today as end date.

2. Find the script. The script is located relative to this SKILL.md file:
   ```
   scripts/git_commits.py
   ```
   To find it dynamically, use this approach:
   ```bash
   # Find the plugin install directory (works regardless of marketplace install path)
   PLUGIN_DIR=$(find ~/.claude/plugins -path "*/git-commits/skills/git-commits/scripts/git_commits.py" -print -quit 2>/dev/null | head -1)
   ```

3. Run the script (use `python3` on macOS/Linux, `python` on Windows):
   ```bash
   python3 "$(find ~/.claude/plugins -path '*/git-commits/skills/git-commits/scripts/git_commits.py' -print -quit 2>/dev/null)" <from_date> <to_date>
   ```

4. **Output rules:**
   - The script output is raw data. You will reformat it for the user.
   - Use the user's preferred language (from their CLAUDE.md or conversation context) for all your text (summaries, headers, labels). Keep commit messages, file names, project names, and URLs unchanged.
   - Present the output as a **markdown table** for each day with these columns: **Time**, **Delta**, **Project**, **Message** (commit message — use the original text, do NOT replace with a summary), **Summary** (AI-generated 5-10 word description based on changed file names — e.g. "Auth redirect fix for web routes", "Catalog PDF generation with summary view"), **Changes** (file count ± lines), **Link** (commit URL)
   - **AI Summary per day**: Immediately below each day's heading (e.g., `## 2026-03-02 (Monday) — 8 commits`), add a 1-2 sentence summary analyzing the commit messages and changed file paths to describe what was worked on that day. Place this summary BEFORE the table.
   - Do NOT add a separate summary section at the end.

5. If the script fails:
   - If config.json is missing: tell the user to run `python3 <script_path> --init` to create config.json, then edit it with their settings.
   - If no commits found: suggest checking the date range and config settings.
   - If API auth fails: suggest setting the appropriate token environment variable or installing `gh` CLI.

## Configuration

The config file is located next to the script (auto-detected by the script itself).

Key settings:
- `scan_paths`: directories to scan for git repos (e.g., `["~/WAME", "~/Projects"]`)
- `excluded_repos`: repository folder names to skip (e.g., `["old-project", "archived-app"]`)
- `author_email`: git author email to filter commits
- `author_names`: alternative author names to try
- `apis.github/gitlab/bitbucket.enabled`: enable API fetching for remote-only repos
