#!/usr/bin/env bash
# STAGE 5 under SECOND GEAR (his call, 2026-08-29): the whole machine is the run's until
# the queue is empty (his standing ruling, 2026-08-28: second gear has no time window;
# the contract's 24-hour deadline is accounting, not a stop). This wrapper carries the
# second-gear guards (one loop by Windows pid, mutual exclusion with first gear, the
# startup orphan sweep, PATH for bare launches) around the Stage-5 scheduler, which owns
# the persisted clock, the card order, the GPU lock discipline, the closure block, and the
# final packet. No shards: the scheduler serializes GPU work and runs at most two CPU
# cards beside it (the brief's §8.4 cap while Ghost V14 runs).
#
# Usage:  bash run_stage5.sh            (prepare + run; a restart resumes, clock kept)
# Stop:   taskkill //F //T //PID $(sed -n 2p results/.gear2.lock)
#
# CHAIN: when the scheduler exhausts and returns 0, this wrapper releases its lock and
# EXECS run_second_gear.sh (no cap, until the general queue is empty) under the SAME
# Windows pid. S5_THEN_QUEUE=0 disables the chain.

cd "$(dirname "$0")" || exit 1
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
LOCK="results/.gear1.lock"
GEAR2="results/.gear2.lock"
LOG="results/queue_main.log"
mkdir -p results results/phase_2_4_stage_5

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
  echo "=== STAGE 5 wrapper exiting $(date) ===" >> "$LOG"
  rm -f "$GEAR2"
}
trap cleanup EXIT INT TERM

echo "=== STAGE 5 SECOND GEAR started $(date) msys $$ / winpid $WINPID ===" >> "$LOG"
./.venv/Scripts/python.exe runners/s5_scheduler.py prepare >> results/phase_2_4_stage_5/wrapper.log 2>&1
./.venv/Scripts/python.exe runners/s5_scheduler.py run >> results/phase_2_4_stage_5/wrapper.log 2>&1
RC=$?
echo "=== STAGE 5 scheduler returned $RC $(date) ===" >> "$LOG"
if [ "$RC" = "0" ] && [ "${S5_THEN_QUEUE:-1}" = "1" ]; then
  echo "=== STAGE 5 exhausted; chaining into run_second_gear.sh (until empty) $(date) ===" >> "$LOG"
  trap - EXIT INT TERM
  rm -f "$GEAR2"
  exec bash run_second_gear.sh 0 3
fi
