# git-commits — Claude Code Plugin

A Claude Code CLI skill that fetches and summarizes your git commits across **all repositories** for a given date range.

Works with any git hosting — GitHub, GitLab, Bitbucket, self-hosted, or local-only repos.

## Features

- Scans local git repos across multiple directories
- Groups commits by date with formatted markdown tables
- Shows time, delta between commits, project name, commit message (with link), and file change stats
- Optional API integration for GitHub, GitLab, and Bitbucket (for repos not cloned locally)
- Deduplicates commits found both locally and via API
- Can also run standalone without Claude Code

## Example Output

```
# Git Commits: 2026-03-01 — 2026-03-18
Author: John Doe | Total commits: 24
Sources: 4 local repos

---

## 2026-03-02 (Monday) — 3 commits

| Time  | Delta  | Project          | Commit                              | Changes      |
|-------|--------|------------------|-------------------------------------|--------------|
| 09:11 | —      | org/backend      | fix: resolve race condition (link)  | 3 files ±42  |
| 09:31 | +19m   | org/frontend     | feat: add webhook retry (link)      | 5 files ±128 |
| 14:47 | +5h16m | org/tools        | update: prompt config (link)        | 6 files ±714 |
```

## Requirements

- **Python 3.6+** (uses only stdlib, no pip dependencies)
- **Git** installed and available in PATH
- **Claude Code CLI** (for `/git-commits` slash command usage)

## Installation

### 1. Clone the repo

```bash
git clone <repo-url> ~/claude-git-commits-plugin
cd ~/claude-git-commits-plugin
```

### 2. Run the installer

**macOS / Linux:**
```bash
./install.sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

> **Windows note:** Creating symlinks on Windows requires either Administrator privileges or Developer Mode enabled (Settings > For developers > Developer Mode).

The installer will:
- Create a symlink from `~/.claude/plugins/.../git-commits/` to this directory
- If an existing (non-symlink) plugin directory is found, it backs up `config.json` and replaces it
- Create `config.json` from the template
- Auto-detect your git name/email and offer to pre-fill the config

### 3. Edit config.json

```bash
nano config.json
# or
code config.json
```

Set your values:

```json
{
  "scan_paths": ["~/Work", "~/Projects"],
  "author_email": "your.email@company.com",
  "author_names": ["Your Name"],
  "max_scan_depth": 3
}
```

### 4. Restart Claude Code

The skill appears after restarting your Claude Code session. Check with `/help`.

## Usage

### In Claude Code CLI

```
/git-commits 2026-03-01 2026-03-31     # specific date range
/git-commits 2026-03-01                 # from date until today
```

### Standalone (without Claude)

```bash
python3 skills/git-commits/scripts/git_commits.py 2026-03-01 2026-03-31
python3 skills/git-commits/scripts/git_commits.py 2026-03-01
```

## Configuration

### scan_paths

Directories to recursively scan for git repositories. Uses `~` expansion.

```json
"scan_paths": ["~/Work", "~/Projects", "~/Personal"]
```

### author_email / author_names

Used to filter `git log`. The script first tries `author_email`, then falls back to `author_names`.

```json
"author_email": "john@company.com",
"author_names": ["John Doe", "johndoe"]
```

### max_scan_depth

How deep to recurse into `scan_paths` looking for `.git` directories. Default: `3`.

### APIs (optional)

Enable API fetching to also find commits in repos you don't have cloned locally.

#### GitHub

Set `enabled: true` and either:
- Install [GitHub CLI](https://cli.github.com/) and run `gh auth login`, or
- Create a [personal access token](https://github.com/settings/tokens) and set `GITHUB_TOKEN` env var

```json
"apis": {
  "github": {
    "enabled": true,
    "token_env": "GITHUB_TOKEN"
  }
}
```

#### GitLab

Create a [personal access token](https://gitlab.com/-/user_settings/personal_access_tokens) with `read_api` scope.

```json
"apis": {
  "gitlab": {
    "enabled": true,
    "token_env": "GITLAB_TOKEN",
    "base_url": "https://gitlab.com"
  }
}
```

For self-hosted GitLab, change `base_url` to your instance URL.

#### Bitbucket

Create an [app password](https://bitbucket.org/account/settings/app-passwords/) with repository read permissions.

```json
"apis": {
  "bitbucket": {
    "enabled": true,
    "token_env": "BITBUCKET_TOKEN"
  }
}
```

## Uninstall

**macOS / Linux:**
```bash
./uninstall.sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File uninstall.ps1
```

Removes the symlink only. Your config.json and the plugin directory remain intact.

## Project Structure

```
claude-git-commits-plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── skills/
│   └── git-commits/
│       ├── SKILL.md             # Skill definition (triggers, instructions)
│       └── scripts/
│           └── git_commits.py   # Main Python script
├── config.example.json          # Configuration template
├── config.json                  # Your local config (gitignored)
├── install.sh                   # Installer (macOS/Linux)
├── install.ps1                  # Installer (Windows)
├── uninstall.sh                 # Uninstaller (macOS/Linux)
├── uninstall.ps1                # Uninstaller (Windows)
└── README.md
```

## License

MIT
