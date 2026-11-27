$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$python = Join-Path $repo '.venv/Scripts/python.exe'
$unit = 'D5s-argument-pooled-DN'
$relative = "results/phase_2_4_stage_15/raw/r48-backfill-20261127/$unit"
$freeze = [DateTimeOffset]::Parse('2026-11-29T16:00:00Z')
$owner = [Threading.Mutex]::new($false, 'Local\SoundingLineR48RetroOwner')
$lane = [Threading.Mutex]::new($false, 'Local\SoundingLineSparkSealedWeek6')
$owned = $false
try {
    try { $owned = $owner.WaitOne(0) }
    catch [Threading.AbandonedMutexException] { $owned = $true }
    if (-not $owned) { return }
    foreach ($marker in @('COMPLETE','FAILED')) {
        & $python -B tools/codex_watch.py register "$relative/$marker.json"
        if ($LASTEXITCODE) { throw 'Retrospective watcher registration failed' }
    }
    while ([DateTimeOffset]::UtcNow -lt $freeze) {
        if (Test-Path -LiteralPath $relative) { return }
        & $python -B tools/r48_retro.py eligible
        if ($LASTEXITCODE -notin @(0,3)) { throw 'Retro admission inspection failed' }
        if ($LASTEXITCODE -eq 0) {
            $held = $false
            try {
                try { $held = $lane.WaitOne(0) }
                catch [Threading.AbandonedMutexException] { $held = $true }
                if ($held) {
                    & $python -B tools/r48_retro.py eligible
                    if ($LASTEXITCODE -eq 0) {
                        & $python -B tools/r48_retro.py submit
                        if ($LASTEXITCODE -ne 0 -and (Test-Path -LiteralPath $relative)) { throw 'Inspect the retrospective terminal' }
                        if ($LASTEXITCODE -eq 0) { return }
                        throw 'Unsubmitted retrospective admission needs inspection'
                    }
                }
            } finally {
                if ($held) { $lane.ReleaseMutex() }
            }
        }
        Start-Sleep -Seconds 60
    }
} finally {
    $lane.Dispose()
    if ($owned) { $owner.ReleaseMutex() }
    $owner.Dispose()
}
