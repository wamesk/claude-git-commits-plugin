# Claude Code Plugin: git-commits — Windows Installer
# Run: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

$PluginName = "git-commits"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PluginsDir = Join-Path $env:USERPROFILE ".claude\plugins"
$TargetDir = Join-Path $PluginsDir $PluginName

Write-Host "=== git-commits plugin installer (Windows) ===" -ForegroundColor Cyan
Write-Host ""

# Check if Claude Code plugins directory exists
$ClaudeDir = Join-Path $env:USERPROFILE ".claude\plugins"
if (-not (Test-Path $ClaudeDir)) {
    Write-Host "Error: ~/.claude/plugins directory not found." -ForegroundColor Red
    Write-Host "Make sure Claude Code CLI is installed first."
    exit 1
}

# Create marketplace directory if needed
if (-not (Test-Path $PluginsDir)) {
    New-Item -ItemType Directory -Path $PluginsDir -Force | Out-Null
}

# Check if already installed
if (Test-Path $TargetDir) {
    $item = Get-Item $TargetDir -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        Write-Host "Plugin already installed (symlink exists)."
        Write-Host "  $TargetDir -> $($item.Target)"
        $reply = Read-Host "Reinstall? (y/N)"
        if ($reply -ne "y" -and $reply -ne "Y") {
            Write-Host "Aborted."
            exit 0
        }
        Remove-Item $TargetDir -Force
    } else {
        Write-Host "Existing plugin directory found at $TargetDir" -ForegroundColor Yellow
        $reply = Read-Host "Replace with symlink to this repo? Existing directory will be removed. (y/N)"
        if ($reply -ne "y" -and $reply -ne "Y") {
            Write-Host "Aborted."
            exit 0
        }
        Remove-Item $TargetDir -Recurse -Force
    }
}

# Create symlink (requires admin or Developer Mode enabled)
try {
    New-Item -ItemType SymbolicLink -Path $TargetDir -Target $ScriptDir | Out-Null
    Write-Host "Symlink created: $TargetDir -> $ScriptDir" -ForegroundColor Green
} catch {
    Write-Host "Failed to create symlink. Try one of:" -ForegroundColor Red
    Write-Host "  1. Run PowerShell as Administrator"
    Write-Host "  2. Enable Developer Mode in Windows Settings > For developers"
    Write-Host ""
    Write-Host "Alternative: copy files instead of symlink? (y/N)"
    $reply = Read-Host
    if ($reply -eq "y" -or $reply -eq "Y") {
        Copy-Item -Path $ScriptDir -Destination $TargetDir -Recurse
        Write-Host "Files copied to $TargetDir" -ForegroundColor Green
        Write-Host "Note: Changes to the repo won't auto-sync. Re-run installer after updates." -ForegroundColor Yellow
    } else {
        exit 1
    }
}

# Handle config.json
$ConfigFile = Join-Path $ScriptDir "config.json"
if (-not (Test-Path $ConfigFile)) {
    Copy-Item (Join-Path $ScriptDir "config.example.json") $ConfigFile
    Write-Host ""
    Write-Host "Created config.json from template." -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Edit config.json with your settings:" -ForegroundColor Yellow
    Write-Host "  $ConfigFile"
    Write-Host ""
    Write-Host "  1. Set scan_paths to directories where your git repos are"
    Write-Host "  2. Set author_email to your git email"
    Write-Host "  3. Set author_names to your name(s) used in git commits"
    Write-Host ""

    # Try to auto-detect git user info
    $GitEmail = ""
    $GitName = ""
    try {
        $GitEmail = (git config --global user.email 2>$null)
        $GitName = (git config --global user.name 2>$null)
    } catch {}

    if ($GitEmail -or $GitName) {
        Write-Host "Detected git config:"
        if ($GitEmail) { Write-Host "  email: $GitEmail" }
        if ($GitName) { Write-Host "  name:  $GitName" }
        Write-Host ""
        $reply = Read-Host "Auto-fill config.json with these values? (Y/n)"
        if ($reply -ne "n" -and $reply -ne "N") {
            $config = Get-Content $ConfigFile | ConvertFrom-Json
            if ($GitEmail) { $config.author_email = $GitEmail }
            if ($GitName) { $config.author_names = @($GitName) }
            $config | ConvertTo-Json -Depth 10 | Set-Content $ConfigFile -Encoding UTF8
            Write-Host "Config updated with git user info." -ForegroundColor Green
        }
    }
} else {
    Write-Host "config.json already exists, skipping."
}

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Usage in Claude Code CLI:"
Write-Host "  /git-commits 2026-03-01 2026-03-31    # specific range"
Write-Host "  /git-commits 2026-03-01               # from date until today"
Write-Host ""
Write-Host "Standalone usage:"
Write-Host "  python $ScriptDir\skills\git-commits\scripts\git_commits.py 2026-03-01 2026-03-31"
Write-Host ""
Write-Host "NOTE: Restart your Claude Code session for the skill to appear in /help." -ForegroundColor Yellow
