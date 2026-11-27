param([Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9-]+$')][string]$Unit)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$python = Join-Path $repo '.venv/Scripts/python.exe'
$mutex = [Threading.Mutex]::new($false, 'Local\SoundingLineSparkSealedWeek6')
$held = $false
try {
    try { $held = $mutex.WaitOne(30000) }
    catch [Threading.AbandonedMutexException] { $held = $true }
    if (-not $held) { throw 'Another Spark submission holds the shared lane.' }
    foreach ($marker in @('COMPLETE', 'FAILED')) {
        & $python -B tools/codex_watch.py register "results/phase_2_4_stage_15/raw/drive-week8-20261127/$Unit/$marker.json"
        if ($LASTEXITCODE -ne 0) { throw 'Watcher registration failed.' }
    }
    & $python -B tools/week8_sealed.py $Unit
    exit $LASTEXITCODE
} finally {
    if ($held) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
