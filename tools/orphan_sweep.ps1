# Orphan sweep (G121). Kill, by Windows process tree, every queue or stage python whose root
# loop is not one of the live recorded loops. Called by both gear scripts at startup with
# -Keep <winpid-of-the-launching-loop>; the recorded lock winpids (line 2 of each lock file)
# are added to the keep set automatically. Legacy day/night lock paths stay in the list so a
# loop from before the 2026-08-12 gear rename is never swept-and-doubled.
# CAUTION (LESSONS §5): this kills legitimate standalone arms too — a long training that is not
# a queue stage needs its winpid passed via -Keep, or checkpoint-resume, or queue membership.
param([string[]]$Keep = @())

$keep = @($Keep)
foreach ($f in @('results/.gear1.lock', 'results/.gear2.lock',
                 'results/.loop.lock', 'results/.overnight.lock')) {
    if (Test-Path $f) {
        $l = @(Get-Content $f)
        if ($l.Count -ge 2) { $keep += [string]$l[1] }
    }
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$repositoryPattern = [regex]::Escape($repositoryRoot.Replace('/', '\')) + '(?:\\|["\s])'
$procs = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match 'python' -and
    $_.CommandLine -match 'run_queue\.py|runners[\\/]run_' -and
    $_.CommandLine.Replace('/', '\') -match $repositoryPattern
}
foreach ($p in $procs) {
    # walk to the root of the bash/python ancestry so the whole lineage is judged at its loop
    $root = $p
    while ($true) {
        $parent = Get-CimInstance Win32_Process -Filter "ProcessId = $($root.ParentProcessId)" `
            -ErrorAction SilentlyContinue
        if ($null -eq $parent -or $parent.Name -notmatch 'bash|python') { break }
        $root = $parent
    }
    $rootId = [string]$root.ProcessId
    $selfId = [string]$p.ProcessId
    if ($keep -notcontains $rootId -and $keep -notcontains $selfId) {
        # A relative command with no repository identity is deliberately not a target.
        # Recheck creation time so PID reuse cannot turn this inspection into another kill.
        $currentProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($p.ProcessId)" `
            -ErrorAction SilentlyContinue
        if ($null -eq $currentProcess -or $currentProcess.CreationDate -ne $p.CreationDate) { continue }
        Write-Host "orphan sweep: killing tree $selfId ($($p.Name), root $rootId)"
        taskkill /F /T /PID $p.ProcessId | Out-Null
    }
}
