# git-commits — Claude Code Plugin

A Claude Code plugin that fetches and summarizes your git commits across **all repositories** for a given date range.

Scans local git repos, groups commits by day, and uses AI to generate summaries of what was worked on — based on commit messages and changed file names.

Works with any git hosting — GitHub, GitLab, Bitbucket, self-hosted, or local-only repos.

## Features

- Scans local git repos across multiple directories
- Groups commits by date with formatted markdown tables
- **AI-generated summary per commit** — analyzes changed files to describe what was done
- **AI-generated day summary** — overview of the day's work placed before each table
- Shows time, delta between commits, project, original commit message, AI summary, changes, and link
- Exclude specific repositories from scanning
- Optional API integration for GitHub, GitLab, and Bitbucket (for repos not cloned locally)
- Deduplicates commits found both locally and via API
- Config stored persistently — survives plugin updates

## Example Output

```
# Git Commits: 2026-03-03 — 2026-03-04
Author: John Doe | Total commits: 4
Sources: 2 local repos

---

## 2026-03-03 (Tuesday) — 3 commits

Focused on bosp-shoes/b2b: catalog performance fix, auth redirect
improvement for web routes, and package-lock sync.

| Time  | Delta | Project        | Message                                              | AI Summary                        | Changes     | Link          |
|-------|-------|----------------|------------------------------------------------------|-----------------------------------|-------------|---------------|
| 22:46 | —     | bosp-shoes/b2b | FIX(catalog): Fix catalog speed                      | Catalog speed fix in README        | 1 file ±2   | [link](url)   |
| 23:05 | +18m  | bosp-shoes/b2b | FIX(auth): Redirect web requests to login instead... | Auth redirect fix for web routes   | 1 file ±16  | [link](url)   |
| 23:09 | +3m   | bosp-shoes/b2b | FIX: Update package-lock.json to sync with package   | NPM dependency lock sync           | 1 file ±304 | [link](url)   |

## 2026-03-04 (Wednesday) — 1 commit

Single commit on catalog PDF generation with service provider
and auth config updates in bosp-shoes/b2b.

| Time  | Delta   | Project        | Message                         | AI Summary                              | Changes     | Link        |
|-------|---------|----------------|---------------------------------|-----------------------------------------|-------------|-------------|
| 20:56 | —       | bosp-shoes/b2b | FIX(catalog): Fix catalog speed | Catalog speed fix with provider & config | 7 files ±105 | [link](url) |
```

## Requirements

- **Python 3.6+** (uses only stdlib, no pip dependencies)
- **Git** installed and available in PATH
- **Claude Code CLI** (for `/git-commits` slash command usage)

## Installation

### Via Marketplace (recommended)

First, add the `wamesk` marketplace (one-time):

```
/plugin marketplace add wamesk/claude-code
```

Then install the plugin:

```
/plugin install git-commits@wamesk
```

### Manual

```bash
git clone git@github.com:wamesk/claude-git-commits-plugin.git
```

Then in Claude Code:

```
claude --plugin-dir ~/path/to/claude-git-commits-plugin
```

### Configuration

On first run, if no config exists, the plugin will ask for your settings and create the config automatically.

Config is stored at `~/.claude/plugins/data/git-commits-wamesk/config.json` — this location **survives plugin updates**.

You can also create it manually or run:

```bash
python3 skills/git-commits/scripts/git_commits.py --init
```

## Usage

### In Claude Code CLI

```
/git-commits                             # current month (1st to today)
/git-commits 2026-03-01 2026-03-31       # specific date range
/git-commits 2026-03-01                  # from date until today
```

### Standalone (without Claude)

```bash
python3 skills/git-commits/scripts/git_commits.py                       # current month
python3 skills/git-commits/scripts/git_commits.py 2026-03-01 2026-03-31 # specific range
python3 skills/git-commits/scripts/git_commits.py 2026-03-01            # from date until today
```

## Configuration Reference

### scan_paths

Directories to recursively scan for git repositories. Uses `~` expansion.

```json
"scan_paths": ["~/Work", "~/Projects", "~/Personal"]
```

### excluded_repos

Repository folder names to skip during scanning.

```json
"excluded_repos": ["old-project", "archived-app", "test-repo"]
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

#### GitLab

Create a [personal access token](https://gitlab.com/-/user_settings/personal_access_tokens) with `read_api` scope.
For self-hosted GitLab, change `base_url` to your instance URL.

#### Bitbucket

Create an [app password](https://bitbucket.org/account/settings/app-passwords/) with repository read permissions.

## Uninstall

In Claude Code:

```
/plugin uninstall git-commits@wamesk
```

Config at `~/.claude/plugins/data/git-commits-wamesk/config.json` is preserved.

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
└── README.md
```

## License

MIT
