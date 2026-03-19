# Claude Code Plugin: git-commits — Windows Uninstaller

$PluginName = "git-commits"
$PluginsDir = Join-Path $env:USERPROFILE ".claude\plugins"
$TargetDir = Join-Path $PluginsDir $PluginName

Write-Host "=== git-commits plugin uninstaller (Windows) ===" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $TargetDir)) {
    Write-Host "Plugin is not installed."
    exit 0
}

$item = Get-Item $TargetDir -Force
if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
    Remove-Item $TargetDir -Force
    Write-Host "Symlink removed: $TargetDir" -ForegroundColor Green
} else {
    Write-Host "Warning: $TargetDir is not a symlink." -ForegroundColor Yellow
    $reply = Read-Host "Remove entire directory? (y/N)"
    if ($reply -eq "y" -or $reply -eq "Y") {
        Remove-Item $TargetDir -Recurse -Force
        Write-Host "Directory removed." -ForegroundColor Green
    } else {
        Write-Host "Aborted."
        exit 0
    }
}

Write-Host ""
Write-Host "Plugin uninstalled. Restart Claude Code session for changes to take effect." -ForegroundColor Yellow
Write-Host "Note: Your config.json was preserved in the plugin directory."
