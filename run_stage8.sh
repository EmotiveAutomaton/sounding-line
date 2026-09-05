#!/usr/bin/env bash
# STAGE 8 (his order 2026-09-04: build it, set it up, start running; gear two, a day or two).
# One immutable 48-hour ceiling starts at the discarded pilot (which trains the smallest
# reader's adapter for one epoch to measure cost); the scheduler runs the 44 questions and
# 12 attacks under the Ghost V15 coexistence governor, the integrity block and the training
# first, then the scientific lock (the mechanical keystone), the gates, the trunks, the
# re-locked ladder, the freeze, the closure tail in reading order, one packet. Restarts
# resume the same clock and queue.
#
# Usage:  bash run_stage8.sh            (prepare once; pilot once, starting the clock; run)
# Stop:   taskkill //F //T //PID $(sed -n 2p results/.gear2.lock)
# CHAIN: on exit this wrapper EXECS run_second_gear.sh (until empty, 2 workers).
# S7_THEN_QUEUE=0 disables the chain.

cd "$(dirname "$0")" || exit 1
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
export S7_STAGE="phase_2_4_stage_8"
export S7_RUN_HOURS="48"
export S7_CLOSURE_HOUR="40"
LOCK="results/.gear1.lock"
GEAR2="results/.gear2.lock"
LOG="results/queue_main.log"
S8ROOT="results/phase_2_4_stage_8"
PY="./.venv/Scripts/python.exe"
mkdir -p results "$S8ROOT"

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
  echo "=== STAGE 8 wrapper exiting $(date) ===" >> "$LOG"
  rm -f "$GEAR2"
}
trap cleanup EXIT INT TERM

GEAR=$(cat results/.gear 2>/dev/null | tr -d '[:space:]')
echo "=== STAGE 8 started in gear ${GEAR:-two} $(date) msys $$ / winpid $WINPID (48-hour ceiling; ghost-governed CPU cap) ===" >> "$LOG"
if [ "$GEAR" = "one" ]; then
  # gear one: the whole tree below normal priority on eight cores; children inherit both
  powershell -NoProfile -File tools/gear1_throttle.ps1 -Root "$WINPID" >> "$S8ROOT/wrapper.log" 2>&1
fi
"$PY" runners/stage8/scheduler.py prepare >> "$S8ROOT/wrapper.log" 2>&1

STARTED=$("$PY" -c "import sys; sys.path.insert(0,'.'); from soundingline.stage8 import RunContract8; c=RunContract8.load(); print(1 if (c and c.data.get('execution_start')) else 0)")
if [ "$STARTED" != "1" ]; then
  echo "=== STAGE 8 discarded pilot begins (THE CLOCK STARTS) $(date) ===" >> "$LOG"
  "$PY" runners/stage8/scheduler.py pilot >> "$S8ROOT/wrapper.log" 2>&1
  RCP=$?
  echo "=== STAGE 8 pilot returned $RCP $(date) ===" >> "$LOG"
  if [ "$RCP" != "0" ]; then
    echo "pilot failed; not entering the run loop (repair, then relaunch)" >> "$LOG"
    exit 1
  fi
fi

"$PY" runners/stage8/scheduler.py run >> "$S8ROOT/wrapper.log" 2>&1
RC=$?
echo "=== STAGE 8 scheduler returned $RC $(date) ===" >> "$LOG"
if [ "${S7_THEN_QUEUE:-1}" = "1" ]; then
  echo "=== STAGE 8 closed; chaining into run_second_gear.sh (until empty, 2 workers) $(date) ===" >> "$LOG"
  trap - EXIT INT TERM
  rm -f "$GEAR2"
  unset S7_STAGE S7_RUN_HOURS S7_CLOSURE_HOUR
  exec bash run_second_gear.sh 0 2
fi
