# Prints the number of live python processes owned by THIS repo's queue or its stage runners.
# Used by tools/regear2_when_idle.sh and tools/regear2_until_empty.sh to know when a gear
# lineage has fully drained; counting the parent alone is not enough because stage processes
# outlive a dead parent and a relaunch's startup sweep would kill them mid-epoch.
#
# Scoped to this repository's path (2026-08-27): the earlier pattern matched any project's
# runners\run_*.py, and a ghost-scale-sim run held the until-empty waiter open for good.
try {
  $n = (Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction Stop |
        Where-Object { $_.CommandLine -match 'sounding-line' -and
                       $_.CommandLine -match 'run_queue|runners[/\\]run_' } |
        Measure-Object).Count
} catch { $n = 0 }
$n
