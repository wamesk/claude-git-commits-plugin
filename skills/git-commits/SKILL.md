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

4. **Output formatting — follow this EXACTLY:**

   The script outputs raw markdown tables. You MUST reformat the output into the structure below. Use the user's preferred language (from CLAUDE.md) for your own text. Keep commit messages, file names, project names, and URLs unchanged.

   **For EACH day, output in this exact order:**

   **a) Day heading:**
   ```
   ## 2026-03-02 (Monday) — 8 commits
   ```

   **b) Day summary (1-2 sentences BEFORE the table):**
   Analyze all commit messages and changed file paths for that day. Write a brief paragraph describing what was worked on. Example:
   > Active day focused on catalog performance optimization in bosp-shoes/b2b (4 commits fixing query speed), auth redirect improvements, and a composer dependency update.

   **c) Markdown table with ALL of these columns:**

   | Time | Delta | Project | Message | AI Summary | Changes | Link |
   |------|-------|---------|---------|------------|---------|------|
   | 09:11 | — | org/backend | FIX(auth): Redirect web requests to login | Auth redirect fix for web routes | 1 file ±16 | [link](url) |

   Column details:
   - **Time** — commit time (HH:MM)
   - **Delta** — time since previous commit that day ("—" for first commit of each day)
   - **Project** — repository name (e.g. org/repo)
   - **Message** — the ORIGINAL commit message text, unchanged
   - **AI Summary** — YOU generate this: a 5-10 word description analyzing the changed FILE NAMES to explain what the commit actually did. Examples: "Auth redirect fix for web routes", "Catalog PDF generation with summary view", "Nova admin panel catalog fields update"
   - **Changes** — file count and line changes (e.g. "3 files ±42")
   - **Link** — clickable link to the commit URL: `[link](url)`

   **IMPORTANT:** Do NOT skip any columns. Do NOT merge Message and AI Summary. Do NOT put the summary at the end — it goes under the day heading, before the table.

5. If the script fails:
   - If config.json is missing: tell the user to run `python3 <script_path> --init` to create config.json, then edit it with their settings. Config is stored persistently at `~/.claude/plugins/data/git-commits-wamesk/config.json` and survives plugin updates.
   - If no commits found: suggest checking the date range and config settings.
   - If API auth fails: suggest setting the appropriate token environment variable or installing `gh` CLI.

## Configuration

The config file is stored at `~/.claude/plugins/data/git-commits-wamesk/config.json` (persistent, survives plugin updates).

Key settings:
- `scan_paths`: directories to scan for git repos (e.g., `["~/WAME", "~/Projects"]`)
- `excluded_repos`: repository folder names to skip (e.g., `["old-project", "archived-app"]`)
- `author_email`: git author email to filter commits
- `author_names`: alternative author names to try
- `apis.github/gitlab/bitbucket.enabled`: enable API fetching for remote-only repos
