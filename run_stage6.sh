#!/usr/bin/env bash
# STAGE 6 (his order 2026-08-30: build front to back, continuous gear 2 through the week).
# One immutable 168-hour clock starts at the discarded pilot; the scheduler runs the 104
# cards and 24 attacks to the window under the Ghost V14 coexistence governor (CPU cap 2
# while Ghost's heartbeat is fresh). Restarts resume the same clock and the same queue.
#
# Usage:  bash run_stage6.sh            (prepare once; pilot once, starting the clock; run)
# Stop:   taskkill //F //T //PID $(sed -n 2p results/.gear2.lock)
# CHAIN: on exit this wrapper EXECS run_second_gear.sh (until empty, 2 workers) so anything
# queued in the general queue afterward still runs. S6_THEN_QUEUE=0 disables the chain.

cd "$(dirname "$0")" || exit 1
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
LOCK="results/.gear1.lock"
GEAR2="results/.gear2.lock"
LOG="results/queue_main.log"
S6ROOT="results/phase_2_4_stage_6"
PY="./.venv/Scripts/python.exe"
mkdir -p results "$S6ROOT"

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
  echo "=== STAGE 6 wrapper exiting $(date) ===" >> "$LOG"
  rm -f "$GEAR2"
}
trap cleanup EXIT INT TERM

echo "=== STAGE 6 SECOND GEAR started $(date) msys $$ / winpid $WINPID (168-hour window; ghost-governed CPU cap) ===" >> "$LOG"
"$PY" runners/stage6/scheduler.py prepare >> "$S6ROOT/wrapper.log" 2>&1

STARTED=$("$PY" -c "import sys; sys.path.insert(0,'.'); from soundingline.stage6 import RunContract6; c=RunContract6.load(); print(1 if (c and c.data.get('execution_start')) else 0)")
if [ "$STARTED" != "1" ]; then
  echo "=== STAGE 6 discarded pilot begins (THE CLOCK STARTS) $(date) ===" >> "$LOG"
  "$PY" runners/stage6/scheduler.py pilot >> "$S6ROOT/wrapper.log" 2>&1
  RCP=$?
  echo "=== STAGE 6 pilot returned $RCP $(date) ===" >> "$LOG"
  if [ "$RCP" != "0" ]; then
    echo "pilot failed; not entering the run loop (repair, then relaunch)" >> "$LOG"
    exit 1
  fi
fi

"$PY" runners/stage6/scheduler.py run >> "$S6ROOT/wrapper.log" 2>&1
RC=$?
echo "=== STAGE 6 scheduler returned $RC $(date) ===" >> "$LOG"
if [ "${S6_THEN_QUEUE:-1}" = "1" ]; then
  echo "=== STAGE 6 closed; chaining into run_second_gear.sh (until empty, 2 workers) $(date) ===" >> "$LOG"
  trap - EXIT INT TERM
  rm -f "$GEAR2"
  exec bash run_second_gear.sh 0 2
fi
