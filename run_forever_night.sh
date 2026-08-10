#!/usr/bin/env bash
# NIGHT — use the whole machine. Nobody is watching, so every safety here is load-bearing.
#
# The daytime loop (run_forever_day.sh) runs one job at a time so the machine stays responsive.
# This one does not care about lag. It cares about the failures that actually happened: 2026-08-07,
# four loops respawning duplicate queues; and repeatedly since, ORPHANED STAGE PROCESSES surviving
# the death of their queue, because the old cleanup (pkill -P) killed children but never
# grandchildren, and the locks stored MSYS pids that no other session could check or kill.
#
# FIVE GUARDS (G121 implemented 2026-08-10), none optional:
#
#   1. ONE LOOP.         Lock stores msys pid (line 1) AND Windows pid (line 2); liveness is
#                        checked with tasklist on the winpid, which works from ANY session.
#   2. MUTUAL EXCLUSION. Refuses while the day loop's winpid is alive, and vice versa.
#   3. NO SHARED STAGES. Workers are SHARDS: stage i is owned by shard i % N by arithmetic.
#   4. A DEADLINE.       Stops on its own.
#   5. TREE KILLS + ORPHAN SWEEP. Every worker is killed as a WINDOWS PROCESS TREE (taskkill //T)
#                        so its stage dies with it; startup kills any queue/stage python that no
#                        live recorded loop owns. No more processes found in the morning.
#
# Usage:  bash run_forever_night.sh [hours] [workers]      defaults: 10 hours, 3 workers
# Stop early with:   taskkill //F //T //PID $(sed -n 2p results/.overnight.lock)
#
# WORKER COUNT IS A MEMORY DECISION, not a speed one. Three concurrent readers on a 12 GB card
# used 11.3 GB. Heavy 3B-class models need workers=2 or the day loop instead (G120).

cd "$(dirname "$0")" || exit 1
# launched bare (Start-Process) there is no PATH; every external tool needs these
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
HOURS="${1:-10}"
WORKERS="${2:-3}"
LOCK="results/.loop.lock"
NIGHT="results/.overnight.lock"
LOG="results/queue_main.log"
mkdir -p results

WINPID=$(cat /proc/$$/winpid 2>/dev/null)
[ -z "$WINPID" ] && WINPID=$(ps -p $$ 2>/dev/null | awk 'NR==2{print $4}')
alive_win() { [ -n "$1" ] && tasklist //FI "PID eq $1" 2>/dev/null | grep -q " $1 "; }
lock_winpid() { sed -n 2p "$1" 2>/dev/null; }

# Guard 2 — mutual exclusion with the day loop, by WINDOWS pid.
if [ -f "$LOCK" ] && alive_win "$(lock_winpid "$LOCK")"; then
  echo "the day loop is running (winpid $(lock_winpid "$LOCK")). Stop it first:"
  echo "  taskkill //F //T //PID $(lock_winpid "$LOCK")"
  exit 1
fi

# Guard 1 — one overnight loop, by WINDOWS pid.
if [ -f "$NIGHT" ]; then
  OLDWIN=$(lock_winpid "$NIGHT")
  if alive_win "$OLDWIN"; then
    echo "an overnight loop is already running (winpid $OLDWIN). Refusing."
    exit 0
  fi
  echo "clearing a stale overnight lock (winpid $OLDWIN is dead)"
fi
printf '%s\n%s\n' "$$" "$WINPID" > "$NIGHT"

# Guard 5a — startup orphan sweep, shared with the day loop.
powershell -NoProfile -File tools/orphan_sweep.ps1 -Keep "$WINPID" 2>/dev/null

# Guard 4 — a deadline; Guard 5b — cleanup kills every worker's WINDOWS TREE.
DEADLINE=$(( $(date +%s) + HOURS * 3600 ))
WORKER_WINPIDS=()
cleanup() {
  echo "=== overnight stopping, killing worker trees ===" >> "$LOG"
  for w in "${WORKER_WINPIDS[@]}"; do
    [ -n "$w" ] && taskkill //F //T //PID "$w" >/dev/null 2>&1
  done
  rm -f "$NIGHT" results/.queue.*of*.lock
}
trap cleanup EXIT INT TERM

echo "=== NIGHT started $(date) msys $$ / winpid $WINPID — ${HOURS}h, ${WORKERS} shards ===" >> "$LOG"
echo "started. ${HOURS}h deadline, ${WORKERS} shards. Stop early with:"
echo "  taskkill //F //T //PID $WINPID"

PASS=0
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  PASS=$((PASS + 1))
  echo "=== pass $PASS begins $(date) ===" >> "$LOG"

  # Guard 3 — shards, not copies; record each worker's WINDOWS pid the moment it exists.
  pids=()
  WORKER_WINPIDS=()
  for i in $(seq 0 $((WORKERS - 1))); do
    ./.venv/Scripts/python.exe runners/run_queue.py --shard "$i" --shards "$WORKERS" \
      >> "results/queue_shard${i}.log" 2>&1 &
    pids+=($!)
    WORKER_WINPIDS+=("$(cat /proc/$!/winpid 2>/dev/null)")
    sleep 5   # stagger model loading
  done
  for pid in "${pids[@]}"; do wait "$pid"; done
  WORKER_WINPIDS=()

  echo "=== pass $PASS complete $(date) ===" >> "$LOG"
  sleep 60
done

echo "=== NIGHT deadline reached $(date), ${PASS} passes ===" >> "$LOG"
echo "deadline reached after ${PASS} passes."
