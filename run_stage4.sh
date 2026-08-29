#!/usr/bin/env bash
# STAGE 4 under SECOND GEAR (his call, 2026-08-27): the whole machine is the run's until the
# queue is empty (his standing ruling, 2026-08-28: second gear has no time window; the
# contract's 24-hour deadline is accounting, not a stop). This wrapper carries the second-gear guards (one loop by Windows pid, mutual
# exclusion with first gear, the startup orphan sweep, PATH for bare launches) around the
# Stage-4 scheduler, which owns the persisted 24-hour deadline, the card order, the GPU
# lock discipline, and the final packet. No shards: the scheduler serializes GPU work and
# runs at most two CPU cards beside it.
#
# Usage:  bash run_stage4.sh            (prepare + run; a restart resumes, deadline kept)
# Stop:   taskkill //F //T //PID $(sed -n 2p results/.gear2.lock)
#
# CHAIN (2026-08-28, his order to keep second gear running to its natural end): when the
# Stage-4 scheduler exhausts and returns 0, this wrapper releases its lock and EXECS
# run_second_gear.sh (no cap, until the general queue is empty) under the SAME Windows
# pid, so the stop command above still stops everything and no second loop is needed.
# S4_THEN_QUEUE=0 disables the chain.

cd "$(dirname "$0")" || exit 1
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
LOCK="results/.gear1.lock"
GEAR2="results/.gear2.lock"
LOG="results/queue_main.log"
mkdir -p results

WINPID=$(cat /proc/$$/winpid 2>/dev/null)
[ -z "$WINPID" ] && WINPID=$(ps -p $$ 2>/dev/null | awk 'NR==2{print $4}')
alive_win() { [ -n "$1" ] && tasklist //FI "PID eq $1" 2>/dev/null | grep -q " $1 "; }
lock_winpid() { sed -n 2p "$1" 2>/dev/null; }

if [ -f "$LOCK" ] && alive_win "$(lock_winpid "$LOCK")"; then
  echo "first gear is running (winpid $(lock_winpid "$LOCK")). Stop it first."
  exit 1
fi
if [ -f "$GEAR2" ]; then
  OLDWIN=$(lock_winpid "$GEAR2")
  if alive_win "$OLDWIN"; then
    echo "a second-gear loop is already running (winpid $OLDWIN). Refusing."
    exit 0
  fi
  rm -f "$GEAR2"
fi
printf '%s\n%s\n' "$$" "$WINPID" > "$GEAR2"
powershell -NoProfile -File tools/orphan_sweep.ps1 -Keep "$WINPID" 2>/dev/null

cleanup() {
  echo "=== STAGE 4 wrapper exiting $(date) ===" >> "$LOG"
  rm -f "$GEAR2"
}
trap cleanup EXIT INT TERM

echo "=== STAGE 4 SECOND GEAR started $(date) msys $$ / winpid $WINPID ===" >> "$LOG"
./.venv/Scripts/python.exe runners/s4_scheduler.py prepare >> results/phase_2_4_stage_4/wrapper.log 2>&1
./.venv/Scripts/python.exe runners/s4_scheduler.py run >> results/phase_2_4_stage_4/wrapper.log 2>&1
RC=$?
echo "=== STAGE 4 scheduler returned $RC $(date) ===" >> "$LOG"
if [ "$RC" = "0" ] && [ "${S4_THEN_QUEUE:-1}" = "1" ]; then
  echo "=== STAGE 4 exhausted; chaining into run_second_gear.sh (until empty) $(date) ===" >> "$LOG"
  trap - EXIT INT TERM
  rm -f "$GEAR2"
  exec bash run_second_gear.sh 0 3
fi
