#!/usr/bin/env bash
# FIRST GEAR — the curator is using the machine. One job at a time, forever, and the GPU is
# the bigger threat to his use (games), so heavy GPU arms belong in second gear; first gear
# keeps things reasonable: part of the CPU, the card only briefly and one stage at a time.
# (Renamed from run_forever_day.sh 2026-08-12; gears replace day/night as the standard.)
#
# HISTORY, because every guard here is a scar. On 2026-08-07 four copies of the previous loop ran
# at once, each respawning a queue. The lock then stored the MSYS pid, which no other session and
# no Task Manager can see, so every lock-based kill hit nothing and the loop survived two days
# (the "immortal loop"). And killing a queue left its running STAGE alive, which is why mornings
# kept finding orphaned python processes. Fixed 2026-08-10 (G121, implemented at last):
#
#   * the lock records the WINDOWS pid (line 2); liveness checks use tasklist on that pid
#   * every kill is a WINDOWS PROCESS TREE kill (taskkill //T), so stages die with their queue
#   * startup sweeps for orphans: any run_queue.py python not belonging to a live recorded loop
#     is killed by tree before this loop starts
#
# Stop this loop with:   taskkill //F //T //PID $(sed -n 2p results/.gear1.lock)

cd "$(dirname "$0")" || exit 1
# launched bare (Start-Process) there is no PATH; every external tool needs these
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
LOCK="results/.gear1.lock"
GEAR2="results/.gear2.lock"
# legacy lock paths from the day/night era; checked so a still-running old loop is never missed
LEGACY_SELF="results/.loop.lock"
LEGACY_OTHER="results/.overnight.lock"
LOG="results/queue_main.log"
mkdir -p results

WINPID=$(cat /proc/$$/winpid 2>/dev/null)
[ -z "$WINPID" ] && WINPID=$(ps -p $$ 2>/dev/null | awk 'NR==2{print $4}')

alive_win() { [ -n "$1" ] && tasklist //FI "PID eq $1" 2>/dev/null | grep -q " $1 "; }
lock_winpid() { sed -n 2p "$1" 2>/dev/null; }

# ── mutual exclusion with second gear (and any legacy loop), by WINDOWS pid
for other in "$GEAR2" "$LEGACY_OTHER"; do
  if [ -f "$other" ] && alive_win "$(lock_winpid "$other")"; then
    echo "second gear is running (winpid $(lock_winpid "$other") via $other). Stop it first:"
    echo "  taskkill //F //T //PID $(lock_winpid "$other")"
    exit 1
  fi
done

# ── one first-gear loop, by WINDOWS pid
for self in "$LOCK" "$LEGACY_SELF"; do
  if [ -f "$self" ]; then
    OLDWIN=$(lock_winpid "$self")
    if alive_win "$OLDWIN"; then
      echo "a first-gear loop is already running (winpid $OLDWIN). Refusing to start a second."
      exit 0
    fi
    echo "clearing a stale lock $self (winpid $OLDWIN is dead)"
    rm -f "$self"
  fi
done
printf '%s\n%s\n' "$$" "$WINPID" > "$LOCK"

# ── startup orphan sweep: kill any queue/stage python that no live loop owns
powershell -NoProfile -File tools/orphan_sweep.ps1 -Keep "$WINPID" 2>/dev/null

QPID=""
cleanup() {
  if [ -n "$QPID" ]; then
    QWIN=$(cat /proc/$QPID/winpid 2>/dev/null)
    [ -n "$QWIN" ] && taskkill //F //T //PID "$QWIN" >/dev/null 2>&1
  fi
  rm -f "$LOCK"
}
trap cleanup EXIT INT TERM

echo "=== FIRST GEAR started $(date) as msys $$ / winpid $WINPID ===" >> "$LOG"
while true; do
  ./.venv/Scripts/python.exe runners/run_queue.py >> "$LOG" 2>&1 &
  QPID=$!
  wait "$QPID"
  QPID=""
  echo "=== pass complete $(date) ===" >> "$LOG"
  sleep 30
done
