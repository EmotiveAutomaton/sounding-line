# The operational helper is separate from queue/model processes and the orphan sweep.
param([switch]$Resume)
$ErrorActionPreference = 'Stop'
$repoPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$statePath = Join-Path $repoPath '.agent-state'
$cancelPath = Join-Path $statePath 'watch.cancel'
$scriptPath = Join-Path $PSScriptRoot 'codex_watch.py'
if (Test-Path -LiteralPath $cancelPath) {
    if (-not $Resume) { Write-Output 'Watcher cancelled; use -Resume after an explicit handoff.'; exit 0 }
    & python -B $scriptPath wait-stopped
    if ($LASTEXITCODE -ne 0) { throw 'Watcher has not stopped; cancellation retained.' }
    Remove-Item -LiteralPath $cancelPath
}
$pythonPath = (Get-Command pythonw.exe -ErrorAction Stop).Source
Start-Process -FilePath $pythonPath -ArgumentList @('-B', ('"' + $scriptPath + '"'), 'run') `
    -WorkingDirectory $repoPath -WindowStyle Hidden
Write-Output 'Watcher launch requested; inspect tools/codex_watch.py status for its heartbeat.'
