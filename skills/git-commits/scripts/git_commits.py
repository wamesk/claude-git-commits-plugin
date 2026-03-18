#!/usr/bin/env python3
"""
Fetch and summarize git commits across all repositories for a date range.
Supports local git repos + optional GitHub/GitLab/Bitbucket API.
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def load_config():
    """Load config.json from the plugin root (two levels up from scripts/)."""
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir.parent.parent.parent / "config.json"
    if not config_path.exists():
        print(f"Error: config.json not found at {config_path}", file=sys.stderr)
        print("Create it with scan_paths, author_email, and author_names.", file=sys.stderr)
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Local git scanning
# ---------------------------------------------------------------------------

def find_git_repos(scan_paths, max_depth=3):
    """Recursively find directories containing .git within scan_paths."""
    repos = []
    for scan_path in scan_paths:
        root = Path(scan_path).expanduser().resolve()
        if not root.exists():
            continue
        _walk_for_git(root, repos, 0, max_depth)
    return repos


def _walk_for_git(directory, repos, depth, max_depth):
    """Walk directory tree looking for .git dirs."""
    if depth > max_depth:
        return
    try:
        git_dir = directory / ".git"
        if git_dir.exists():
            repos.append(directory)
            return  # Don't recurse into git repos (no nested repos)
        for entry in sorted(directory.iterdir()):
            if entry.is_dir() and not entry.name.startswith("."):
                _walk_for_git(entry, repos, depth + 1, max_depth)
    except PermissionError:
        pass


def get_repo_info(repo_path):
    """Extract project name and base URL from git remote origin."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            return parse_remote_url(url)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    # Fallback: use directory name
    return repo_path.name, None


def parse_remote_url(url):
    """Parse git remote URL to extract project name and web base URL.

    Supports:
      - SSH: git@github.com:org/repo.git
      - HTTPS: https://github.com/org/repo.git
    Returns (project_name, web_base_url) or (project_name, None).
    """
    # SSH format: git@host:org/repo.git
    ssh_match = re.match(r"git@([^:]+):(.+?)(?:\.git)?$", url)
    if ssh_match:
        host, path = ssh_match.group(1), ssh_match.group(2)
        return path, f"https://{host}/{path}"

    # HTTPS format
    https_match = re.match(r"https?://([^/]+)/(.+?)(?:\.git)?$", url)
    if https_match:
        host, path = https_match.group(1), https_match.group(2)
        return path, f"https://{host}/{path}"

    return url, None


def build_commit_url(web_base_url, sha, host=None):
    """Build a web URL for a specific commit."""
    if not web_base_url:
        return None
    # GitLab uses /-/commit/, GitHub and Bitbucket use /commit/
    if host and "gitlab" in host:
        return f"{web_base_url}/-/commit/{sha}"
    if host and "bitbucket" in host:
        return f"{web_base_url}/commits/{sha}"
    # Default (GitHub and others)
    return f"{web_base_url}/commit/{sha}"


def detect_host(web_base_url):
    """Detect hosting platform from URL."""
    if not web_base_url:
        return None
    url_lower = web_base_url.lower()
    if "gitlab" in url_lower:
        return "gitlab"
    if "bitbucket" in url_lower:
        return "bitbucket"
    if "github" in url_lower:
        return "github"
    return "other"


def get_local_commits(repo_path, author_email, author_names, since, until):
    """Get commits from a local git repo for the given author and date range."""
    commits = []
    project_name, web_base_url = get_repo_info(repo_path)
    host = detect_host(web_base_url)

    # Build author filter: use email as primary
    author_filter = author_email

    # until needs +1 day because git --until is exclusive
    until_plus = (datetime.strptime(until, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        result = subprocess.run(
            [
                "git", "-C", str(repo_path), "log",
                f"--author={author_filter}",
                f"--since={since}",
                f"--until={until_plus}",
                "--format=%H|%aI|%s",
                "--no-merges",
                "--all",
            ],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return commits

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue
            sha, date_iso, message = parts
            commit_url = build_commit_url(web_base_url, sha, host)
            commits.append({
                "sha": sha,
                "date_iso": date_iso,
                "message": message.strip(),
                "project": project_name,
                "url": commit_url,
                "source": "local",
            })

        # If no results with email, try author names
        if not commits and author_names:
            for name in author_names:
                result2 = subprocess.run(
                    [
                        "git", "-C", str(repo_path), "log",
                        f"--author={name}",
                        f"--since={since}",
                        f"--until={until_plus}",
                        "--format=%H|%aI|%s",
                        "--no-merges",
                        "--all",
                    ],
                    capture_output=True, text=True, timeout=30
                )
                if result2.returncode == 0 and result2.stdout.strip():
                    for line in result2.stdout.strip().split("\n"):
                        if not line:
                            continue
                        parts = line.split("|", 2)
                        if len(parts) < 3:
                            continue
                        sha, date_iso, message = parts
                        commit_url = build_commit_url(web_base_url, sha, host)
                        commits.append({
                            "sha": sha,
                            "date_iso": date_iso,
                            "message": message.strip(),
                            "project": project_name,
                            "url": commit_url,
                            "source": "local",
                        })
                    break  # Found commits with this name, stop trying others

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return commits


def get_file_stats(repo_path, sha):
    """Get file change stats for a commit."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "diff-tree", "--no-commit-id", "--numstat", "-r", sha],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None

        files_changed = 0
        total_changes = 0
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                files_changed += 1
                added = int(parts[0]) if parts[0] != "-" else 0
                deleted = int(parts[1]) if parts[1] != "-" else 0
                total_changes += added + deleted

        if files_changed > 0:
            return {"files": files_changed, "changes": total_changes}
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return None


def get_all_file_stats(repos_with_commits):
    """Fetch file stats for all commits, mapping SHA to repo path."""
    stats = {}
    for repo_path, commits in repos_with_commits:
        for commit in commits:
            s = get_file_stats(repo_path, commit["sha"])
            if s:
                stats[commit["sha"]] = s
    return stats


# ---------------------------------------------------------------------------
# GitHub API
# ---------------------------------------------------------------------------

def github_api_request(endpoint, token=None):
    """Make a GitHub API request."""
    url = f"https://api.github.com{endpoint}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"GitHub API rate limited. Try again later.", file=sys.stderr)
        return None
    except Exception:
        return None


def gh_cli_request(endpoint):
    """Make a GitHub API request via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", endpoint, "-H", "Accept: application/vnd.github+json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return None


def get_github_commits(config, since, until):
    """Fetch commits from GitHub API."""
    api_config = config.get("apis", {}).get("github", {})
    if not api_config.get("enabled", False):
        return []

    # Determine auth method
    token = None
    token_env = api_config.get("token_env", "GITHUB_TOKEN")
    use_gh_cli = False

    # Try gh CLI first
    try:
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, timeout=5)
        if result.returncode == 0:
            use_gh_cli = True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    if not use_gh_cli:
        token = os.environ.get(token_env)
        if not token:
            print(f"GitHub API enabled but no auth found. Set {token_env} or install gh CLI.", file=sys.stderr)
            return []

    # Get username
    if use_gh_cli:
        user_data = gh_cli_request("/user")
    else:
        user_data = github_api_request("/user", token)

    if not user_data or "login" not in user_data:
        print("Could not determine GitHub username.", file=sys.stderr)
        return []

    username = user_data["login"]
    commits = []
    page = 1

    while page <= 10:  # Max 10 pages (1000 results)
        query = f"author:{username}+committer-date:{since}..{until}"
        endpoint = f"/search/commits?q={query}&sort=committer-date&order=asc&per_page=100&page={page}"

        if use_gh_cli:
            data = gh_cli_request(endpoint)
        else:
            data = github_api_request(endpoint, token)

        if not data or "items" not in data:
            break

        for item in data["items"]:
            commit_data = item.get("commit", {})
            repo_name = item.get("repository", {}).get("full_name", "unknown")
            sha = item.get("sha", "")
            html_url = item.get("html_url", "")
            date_iso = commit_data.get("committer", {}).get("date", "")
            message = commit_data.get("message", "").split("\n")[0]

            # File stats from API
            stats_data = None
            if use_gh_cli:
                commit_detail = gh_cli_request(f"/repos/{repo_name}/commits/{sha}")
            else:
                commit_detail = github_api_request(f"/repos/{repo_name}/commits/{sha}", token)
            if commit_detail and "stats" in commit_detail:
                s = commit_detail["stats"]
                files_list = commit_detail.get("files", [])
                stats_data = {
                    "files": len(files_list),
                    "changes": s.get("additions", 0) + s.get("deletions", 0),
                }

            commits.append({
                "sha": sha,
                "date_iso": date_iso,
                "message": message,
                "project": repo_name,
                "url": html_url,
                "source": "github_api",
                "stats": stats_data,
            })

        if len(data["items"]) < 100:
            break
        page += 1

    return commits


# ---------------------------------------------------------------------------
# GitLab API
# ---------------------------------------------------------------------------

def gitlab_api_request(base_url, endpoint, token):
    """Make a GitLab API request."""
    url = f"{base_url}/api/v4{endpoint}"
    req = urllib.request.Request(url)
    req.add_header("PRIVATE-TOKEN", token)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def get_gitlab_commits(config, since, until):
    """Fetch commits from GitLab API."""
    api_config = config.get("apis", {}).get("gitlab", {})
    if not api_config.get("enabled", False):
        return []

    token_env = api_config.get("token_env", "GITLAB_TOKEN")
    token = os.environ.get(token_env)
    if not token:
        print(f"GitLab API enabled but {token_env} not set.", file=sys.stderr)
        return []

    base_url = api_config.get("base_url", "https://gitlab.com").rstrip("/")
    author_email = config.get("author_email", "")

    # Get all projects the user is a member of
    projects = []
    page = 1
    while True:
        data = gitlab_api_request(base_url, f"/projects?membership=true&per_page=100&page={page}", token)
        if not data:
            break
        projects.extend(data)
        if len(data) < 100:
            break
        page += 1

    commits = []
    until_plus = (datetime.strptime(until, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    since_iso = f"{since}T00:00:00Z"

    for project in projects:
        pid = project["id"]
        path = project.get("path_with_namespace", project.get("name", str(pid)))
        web_url = project.get("web_url", "")

        proj_commits = gitlab_api_request(
            base_url,
            f"/projects/{pid}/repository/commits?author={author_email}&since={since_iso}&until={until_plus}&per_page=100",
            token
        )
        if not proj_commits:
            continue

        for c in proj_commits:
            sha = c.get("id", "")
            commits.append({
                "sha": sha,
                "date_iso": c.get("committed_date", ""),
                "message": c.get("title", ""),
                "project": path,
                "url": f"{web_url}/-/commit/{sha}" if web_url else None,
                "source": "gitlab_api",
                "stats": {
                    "files": c.get("stats", {}).get("total", 0) if c.get("stats") else 0,
                    "changes": (c.get("stats", {}).get("additions", 0) + c.get("stats", {}).get("deletions", 0)) if c.get("stats") else 0,
                } if c.get("stats") else None,
            })

    return commits


# ---------------------------------------------------------------------------
# Bitbucket API
# ---------------------------------------------------------------------------

def bitbucket_api_request(endpoint, token):
    """Make a Bitbucket Cloud API request."""
    url = f"https://api.bitbucket.org/2.0{endpoint}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def get_bitbucket_commits(config, since, until):
    """Fetch commits from Bitbucket API."""
    api_config = config.get("apis", {}).get("bitbucket", {})
    if not api_config.get("enabled", False):
        return []

    token_env = api_config.get("token_env", "BITBUCKET_TOKEN")
    token = os.environ.get(token_env)
    if not token:
        print(f"Bitbucket API enabled but {token_env} not set.", file=sys.stderr)
        return []

    author_email = config.get("author_email", "")

    # Get repositories
    repos = []
    url = "/repositories?role=member&pagelen=100"
    while url:
        data = bitbucket_api_request(url, token)
        if not data:
            break
        repos.extend(data.get("values", []))
        url = data.get("next", "").replace("https://api.bitbucket.org/2.0", "") if data.get("next") else None

    commits = []
    for repo in repos:
        full_name = repo.get("full_name", "")
        web_url = repo.get("links", {}).get("html", {}).get("href", "")

        # Bitbucket commits endpoint doesn't filter by author, so we fetch and filter
        repo_commits_url = f"/repositories/{full_name}/commits?pagelen=100"
        data = bitbucket_api_request(repo_commits_url, token)
        if not data:
            continue

        for c in data.get("values", []):
            commit_date = c.get("date", "")
            author_raw = c.get("author", {}).get("raw", "")
            if author_email not in author_raw:
                continue

            # Check date range
            try:
                dt = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
                since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                until_dt = datetime.strptime(until, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
                if not (since_dt <= dt < until_dt):
                    continue
            except ValueError:
                continue

            sha = c.get("hash", "")
            commits.append({
                "sha": sha,
                "date_iso": commit_date,
                "message": c.get("message", "").split("\n")[0].strip(),
                "project": full_name,
                "url": f"{web_url}/commits/{sha}" if web_url else None,
                "source": "bitbucket_api",
            })

    return commits


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def parse_commit_datetime(date_iso):
    """Parse ISO date string to datetime object."""
    try:
        # Handle various ISO formats
        cleaned = date_iso.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def format_delta(seconds):
    """Format time delta between commits."""
    if seconds < 60:
        return f"+{int(seconds)}s"
    minutes = int(seconds / 60)
    if minutes < 60:
        return f"+{minutes}m"
    hours = minutes // 60
    remaining_mins = minutes % 60
    if hours < 24:
        if remaining_mins == 0:
            return f"+{hours}h"
        return f"+{hours}h{remaining_mins}m"
    days = hours // 24
    remaining_hours = hours % 24
    return f"+{days}d{remaining_hours}h"


def format_stats(stats):
    """Format file change stats."""
    if not stats:
        return "—"
    files = stats.get("files", 0)
    changes = stats.get("changes", 0)
    file_word = "file" if files == 1 else "files"
    return f"{files} {file_word} ±{changes}"


def format_output(commits, stats_map, since, until, author_name, source_summary):
    """Format commits as markdown output."""
    if not commits:
        print(f"# Git Commits: {since} — {until}")
        print(f"**Author:** {author_name}")
        print(f"\nNo commits found in this date range.")
        return

    # Sort by datetime (oldest first)
    commits.sort(key=lambda c: c.get("_datetime") or datetime.min.replace(tzinfo=timezone.utc))

    # Group by date
    by_date = defaultdict(list)
    for c in commits:
        dt = c.get("_datetime")
        if dt:
            date_key = dt.strftime("%Y-%m-%d")
            by_date[date_key].append(c)

    total = len(commits)
    print(f"# Git Commits: {since} — {until}")
    print(f"**Author:** {author_name} | **Total commits:** {total}")
    if source_summary:
        print(f"**Sources:** {source_summary}")
    print()
    print("---")
    print()

    # Calculate deltas (across all commits, sorted chronologically)
    prev_dt = None
    for c in commits:
        dt = c.get("_datetime")
        if dt and prev_dt:
            delta_secs = (dt - prev_dt).total_seconds()
            c["_delta"] = format_delta(delta_secs)
        else:
            c["_delta"] = "—"
        if dt:
            prev_dt = dt

    # Output by date (sorted oldest first)
    for date_key in sorted(by_date.keys()):
        day_commits = by_date[date_key]
        dt = datetime.strptime(date_key, "%Y-%m-%d")
        day_name = dt.strftime("%A")
        count = len(day_commits)
        commit_word = "commit" if count == 1 else "commits"

        print(f"## {date_key} ({day_name}) — {count} {commit_word}")
        print()
        print("| Time  | Delta  | Project | Commit | Changes |")
        print("|-------|--------|---------|--------|---------|")

        for c in day_commits:
            cdt = c.get("_datetime")
            time_str = cdt.strftime("%H:%M") if cdt else "??:??"
            delta = c.get("_delta", "—")
            project = c["project"]
            message = c["message"][:80]
            url = c.get("url")
            sha = c["sha"]
            stats = stats_map.get(sha) or c.get("stats")

            # Format commit as link or plain text
            if url:
                commit_str = f"[{message}]({url})"
            else:
                commit_str = message

            changes_str = format_stats(stats)

            print(f"| {time_str} | {delta} | {project} | {commit_str} | {changes_str} |")

        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: git_commits.py <from YYYY-MM-DD> [to YYYY-MM-DD]", file=sys.stderr)
        print("Example: git_commits.py 2026-03-01 2026-03-31", file=sys.stderr)
        print("         git_commits.py 2026-03-01  (until today)", file=sys.stderr)
        sys.exit(1)

    since = sys.argv[1]
    until = sys.argv[2] if len(sys.argv) >= 3 else datetime.now().strftime("%Y-%m-%d")

    # Validate date format
    for d, label in [(since, "from"), (until, "to")]:
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid {label} date '{d}'. Expected format: YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    config = load_config()
    scan_paths = config.get("scan_paths", [])
    author_email = config.get("author_email", "")
    author_names = config.get("author_names", [])
    max_depth = config.get("max_scan_depth", 3)

    if not author_email and not author_names:
        print("Error: Set author_email or author_names in config.json", file=sys.stderr)
        sys.exit(1)

    # Phase 1: Local repos
    all_commits = []
    seen_shas = set()
    repos_with_commits = []
    source_counts = defaultdict(int)

    if scan_paths:
        repos = find_git_repos(scan_paths, max_depth)
        local_repo_count = 0
        for repo_path in repos:
            commits = get_local_commits(repo_path, author_email, author_names, since, until)
            if commits:
                local_repo_count += 1
                repos_with_commits.append((repo_path, commits))
                for c in commits:
                    if c["sha"] not in seen_shas:
                        seen_shas.add(c["sha"])
                        all_commits.append(c)
        if local_repo_count > 0:
            source_counts["local repos"] = local_repo_count

    # Get file stats for local commits
    stats_map = get_all_file_stats(repos_with_commits)

    # Phase 2: API repos (optional)
    for platform, fetch_fn in [
        ("GitHub API", lambda: get_github_commits(config, since, until)),
        ("GitLab API", lambda: get_gitlab_commits(config, since, until)),
        ("Bitbucket API", lambda: get_bitbucket_commits(config, since, until)),
    ]:
        api_commits = fetch_fn()
        new_count = 0
        for c in api_commits:
            if c["sha"] not in seen_shas:
                seen_shas.add(c["sha"])
                all_commits.append(c)
                new_count += 1
                # Store API stats in stats_map
                if c.get("stats"):
                    stats_map[c["sha"]] = c["stats"]
        if new_count > 0:
            source_counts[platform] = new_count

    # Parse datetimes
    for c in all_commits:
        c["_datetime"] = parse_commit_datetime(c["date_iso"])

    # Build source summary
    source_parts = []
    for src, count in source_counts.items():
        source_parts.append(f"{count} {src}")
    source_summary = ", ".join(source_parts) if source_parts else None

    # Determine author display name
    author_display = author_names[0] if author_names else author_email

    # Format and output
    format_output(all_commits, stats_map, since, until, author_display, source_summary)


if __name__ == "__main__":
    main()
