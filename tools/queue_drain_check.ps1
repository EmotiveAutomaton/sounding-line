# Prints the number of live python processes owned by the queue or its stage runners.
# Used by tools/regear2_when_idle.sh to know when a gear lineage has fully drained;
# counting the parent alone is not enough because stage processes outlive a dead parent
# and a relaunch's startup sweep would kill them mid-epoch.
try {
  $n = (Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction Stop |
        Where-Object { $_.CommandLine -match 'run_queue|runners[/\\]run_' } |
        Measure-Object).Count
} catch { $n = 0 }
$n
