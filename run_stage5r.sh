#!/usr/bin/env bash
# STAGE 5, SECOND CONTRACT (design 2; his order 2026-08-29: rerun everything needed, gear 2 until
# empty): the Stage-5 program re-run under S5_DESIGN=2 with every post-run repair (the 96-item
# reader gate that admits SmolLM2, the two track gates, the fixed-order bridge, the repaired
# future-choice question, the goal-restated preference question, P02's format, P01's prior
# features, A02's twin pairing, R02's fluency-checked rendering, R01's per-world route rendering,
# a forensic step that sometimes pays, a second episode with a higher ceiling, equifinal plan
# worlds) on its own root, results/phase_2_4_stage_5r. The closed first contract is untouched.
#
# Usage:  bash run_stage5r.sh            (prepare + run; a restart resumes, clock kept)
# Stop:   taskkill //F //T //PID $(sed -n 2p results/.gear2.lock)
# CHAIN: on exit 0 this wrapper EXECS run_second_gear.sh (no cap, until the general queue is
# empty) under the SAME Windows pid. S5_THEN_QUEUE=0 disables the chain.

cd "$(dirname "$0")" || exit 1
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
export S5_ROOT="$(pwd -W 2>/dev/null || pwd)/results/phase_2_4_stage_5r"
export S5_STAGE="phase_2_4_stage_5r"
export S5_DESIGN="2"
LOCK="results/.gear1.lock"
GEAR2="results/.gear2.lock"
LOG="results/queue_main.log"
mkdir -p results results/phase_2_4_stage_5r

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
  echo "=== STAGE 5R wrapper exiting $(date) ===" >> "$LOG"
  rm -f "$GEAR2"
}
trap cleanup EXIT INT TERM

echo "=== STAGE 5R (design 2) SECOND GEAR started $(date) msys $$ / winpid $WINPID root $S5_ROOT ===" >> "$LOG"
./.venv/Scripts/python.exe runners/s5_scheduler.py prepare >> results/phase_2_4_stage_5r/wrapper.log 2>&1
./.venv/Scripts/python.exe runners/s5_scheduler.py run >> results/phase_2_4_stage_5r/wrapper.log 2>&1
RC=$?
echo "=== STAGE 5R scheduler returned $RC $(date) ===" >> "$LOG"
if [ "$RC" = "0" ] && [ "${S5_THEN_QUEUE:-1}" = "1" ]; then
  echo "=== STAGE 5R exhausted; chaining into run_second_gear.sh (until empty) $(date) ===" >> "$LOG"
  trap - EXIT INT TERM
  rm -f "$GEAR2"
  unset S5_ROOT S5_STAGE S5_DESIGN
  exec bash run_second_gear.sh 0 3
fi
