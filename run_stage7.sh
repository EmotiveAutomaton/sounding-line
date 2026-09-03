#!/usr/bin/env bash
# STAGE 7 (his order 2026-09-02: build the whole thing and set it to run in gear two).
# One immutable 72-hour ceiling starts at the discarded pilot; the scheduler runs the 100
# questions and 24 attacks under the Ghost V15 coexistence governor (CPU cap 2 while the
# Ghost heartbeat is fresh), the integrity block first, then the scientific lock (which
# waits on the signed keystone), then the ladder to closure. Restarts resume the same
# clock and queue.
#
# Usage:  bash run_stage7.sh            (prepare once; pilot once, starting the clock; run)
# Stop:   taskkill //F //T //PID $(sed -n 2p results/.gear2.lock)
# CHAIN: on exit this wrapper EXECS run_second_gear.sh (until empty, 2 workers) so anything
# queued in the general queue afterward still runs. S7_THEN_QUEUE=0 disables the chain.

cd "$(dirname "$0")" || exit 1
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
LOCK="results/.gear1.lock"
GEAR2="results/.gear2.lock"
LOG="results/queue_main.log"
S7ROOT="results/phase_2_4_stage_7"
PY="./.venv/Scripts/python.exe"
mkdir -p results "$S7ROOT"

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
  echo "=== STAGE 7 wrapper exiting $(date) ===" >> "$LOG"
  rm -f "$GEAR2"
}
trap cleanup EXIT INT TERM

echo "=== STAGE 7 SECOND GEAR started $(date) msys $$ / winpid $WINPID (72-hour ceiling; ghost-governed CPU cap) ===" >> "$LOG"
"$PY" runners/stage7/scheduler.py prepare >> "$S7ROOT/wrapper.log" 2>&1

STARTED=$("$PY" -c "import sys; sys.path.insert(0,'.'); from soundingline.stage7 import RunContract7; c=RunContract7.load(); print(1 if (c and c.data.get('execution_start')) else 0)")
if [ "$STARTED" != "1" ]; then
  echo "=== STAGE 7 discarded pilot begins (THE CLOCK STARTS) $(date) ===" >> "$LOG"
  "$PY" runners/stage7/scheduler.py pilot >> "$S7ROOT/wrapper.log" 2>&1
  RCP=$?
  echo "=== STAGE 7 pilot returned $RCP $(date) ===" >> "$LOG"
  if [ "$RCP" != "0" ]; then
    echo "pilot failed; not entering the run loop (repair, then relaunch)" >> "$LOG"
    exit 1
  fi
fi

"$PY" runners/stage7/scheduler.py run >> "$S7ROOT/wrapper.log" 2>&1
RC=$?
echo "=== STAGE 7 scheduler returned $RC $(date) ===" >> "$LOG"
if [ "${S7_THEN_QUEUE:-1}" = "1" ]; then
  echo "=== STAGE 7 closed; chaining into run_second_gear.sh (until empty, 2 workers) $(date) ===" >> "$LOG"
  trap - EXIT INT TERM
  rm -f "$GEAR2"
  exec bash run_second_gear.sh 0 2
fi
