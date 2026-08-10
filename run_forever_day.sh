#!/usr/bin/env bash
# One job at a time, forever. Lives in the repo rather than /tmp so there is exactly one copy.
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
# Stop this loop with:   taskkill //F //T //PID $(sed -n 2p results/.loop.lock)

cd "$(dirname "$0")" || exit 1
# launched bare (Start-Process) there is no PATH; every external tool needs these
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
LOCK="results/.loop.lock"
NIGHT="results/.overnight.lock"
LOG="results/queue_main.log"
mkdir -p results

WINPID=$(cat /proc/$$/winpid 2>/dev/null)
[ -z "$WINPID" ] && WINPID=$(ps -p $$ 2>/dev/null | awk 'NR==2{print $4}')

alive_win() { [ -n "$1" ] && tasklist //FI "PID eq $1" 2>/dev/null | grep -q " $1 "; }
lock_winpid() { sed -n 2p "$1" 2>/dev/null; }

# ── mutual exclusion with the night loop, by WINDOWS pid
if [ -f "$NIGHT" ] && alive_win "$(lock_winpid "$NIGHT")"; then
  echo "the night loop is running (winpid $(lock_winpid "$NIGHT")). Refusing."
  exit 1
fi

# ── one day loop, by WINDOWS pid
if [ -f "$LOCK" ]; then
  OLDWIN=$(lock_winpid "$LOCK")
  if alive_win "$OLDWIN"; then
    echo "a loop is already running (winpid $OLDWIN). Refusing to start a second."
    exit 0
  fi
  echo "clearing a stale loop lock (winpid $OLDWIN is dead)"
fi
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

echo "=== loop started $(date) as msys $$ / winpid $WINPID ===" >> "$LOG"
while true; do
  ./.venv/Scripts/python.exe runners/run_queue.py >> "$LOG" 2>&1 &
  QPID=$!
  wait "$QPID"
  QPID=""
  echo "=== pass complete $(date) ===" >> "$LOG"
  sleep 30
done
