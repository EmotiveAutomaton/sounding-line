# Gear one, live: lower the priority class and pin the CPU affinity of the whole Stage 8
# process tree (the wrapper bash and every descendant). Children inherit both, so cells the
# scheduler starts from now on come up throttled. No process is stopped; no file is touched.
param([int]$Root, [int64]$Mask = 0xFF0000, [string]$Prio = "BelowNormal")
$all = Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name
$byParent = @{}
foreach ($p in $all) { if (-not $byParent.ContainsKey([int]$p.ParentProcessId)) { $byParent[[int]$p.ParentProcessId] = @() }; $byParent[[int]$p.ParentProcessId] += [int]$p.ProcessId }
$queue = New-Object System.Collections.Queue
$queue.Enqueue($Root)
$tree = @()
while ($queue.Count -gt 0) {
  $pid0 = $queue.Dequeue()
  $tree += $pid0
  if ($byParent.ContainsKey($pid0)) { foreach ($c in $byParent[$pid0]) { $queue.Enqueue($c) } }
}
foreach ($pid0 in $tree) {
  try {
    $proc = Get-Process -Id $pid0 -ErrorAction Stop
    $proc.PriorityClass = $Prio
    $proc.ProcessorAffinity = [IntPtr]$Mask
    $proc = Get-Process -Id $pid0
    "{0,8} {1,-14} prio={2,-12} affinity=0x{3:X}" -f $pid0, $proc.ProcessName, $proc.PriorityClass, [int64]$proc.ProcessorAffinity
  } catch { "{0,8} skipped: {1}" -f $pid0, $_.Exception.Message }
}
