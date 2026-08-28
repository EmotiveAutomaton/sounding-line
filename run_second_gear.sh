#!/usr/bin/env bash
# SECOND GEAR — use the whole machine. As much CPU and GPU as the work can take, loaded with
# about a day's worth of analyses ahead of time. Nobody is watching, so every safety here is
# load-bearing. (Renamed from run_forever_night.sh 2026-08-12; gears replace day/night as the
# standard. First gear is for when the curator wants the machine; this one uses everything.)
#
# The failures these guards answer: 2026-08-07, four loops respawning duplicate queues; and
# repeatedly since, ORPHANED STAGE PROCESSES surviving the death of their queue, because the old
# cleanup (pkill -P) killed children but never grandchildren, and the locks stored MSYS pids that
# no other session could check or kill.
#
# FIVE GUARDS (G121 implemented 2026-08-10), none optional:
#
#   1. ONE LOOP.         Lock stores msys pid (line 1) AND Windows pid (line 2); liveness is
#                        checked with tasklist on the winpid, which works from ANY session.
#   2. MUTUAL EXCLUSION. Refuses while first gear's winpid is alive, and vice versa.
#   3. NO SHARED STAGES. Workers are SHARDS: stage i is owned by shard i % N by arithmetic.
#   4. RUNS UNTIL EMPTY. Second gear has NO time window (his standing ruling 2026-08-28): it
#                        ends when the queue has no pending stage (tools/queue_pending_count.py
#                        reads 0). An hours argument is an optional cap, never a default.
#   5. TREE KILLS + ORPHAN SWEEP. Every worker is killed as a WINDOWS PROCESS TREE (taskkill //T)
#                        so its stage dies with it; startup kills any queue/stage python that no
#                        live recorded loop owns. No more processes found in the morning.
#
# Usage:  bash run_second_gear.sh [hours] [workers]      defaults: no cap (until empty), 3 workers
# Stop early with:   taskkill //F //T //PID $(sed -n 2p results/.gear2.lock)
#
# WORKER COUNT IS A MEMORY DECISION, not a speed one. Three concurrent readers on a 12 GB card
# used 11.3 GB. Heavy 3B-class models need workers=2 or first gear instead (G120).

cd "$(dirname "$0")" || exit 1
# launched bare (Start-Process) there is no PATH; every external tool needs these
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
HOURS="${1:-0}"          # 0 = no cap: run until the queue is empty (his ruling 2026-08-28)
WORKERS="${2:-3}"
LOCK="results/.gear1.lock"
GEAR2="results/.gear2.lock"
# legacy lock paths from the day/night era; checked so a still-running old loop is never missed
LEGACY_GEAR1="results/.loop.lock"
LEGACY_GEAR2="results/.overnight.lock"
LOG="results/queue_main.log"
mkdir -p results

WINPID=$(cat /proc/$$/winpid 2>/dev/null)
[ -z "$WINPID" ] && WINPID=$(ps -p $$ 2>/dev/null | awk 'NR==2{print $4}')
alive_win() { [ -n "$1" ] && tasklist //FI "PID eq $1" 2>/dev/null | grep -q " $1 "; }
lock_winpid() { sed -n 2p "$1" 2>/dev/null; }

# Guard 2 — mutual exclusion with first gear (and any legacy loop), by WINDOWS pid.
for other in "$LOCK" "$LEGACY_GEAR1"; do
  if [ -f "$other" ] && alive_win "$(lock_winpid "$other")"; then
    echo "first gear is running (winpid $(lock_winpid "$other") via $other). Stop it first:"
    echo "  taskkill //F //T //PID $(lock_winpid "$other")"
    exit 1
  fi
done

# Guard 1 — one second-gear loop, by WINDOWS pid.
for self in "$GEAR2" "$LEGACY_GEAR2"; do
  if [ -f "$self" ]; then
    OLDWIN=$(lock_winpid "$self")
    if alive_win "$OLDWIN"; then
      echo "a second-gear loop is already running (winpid $OLDWIN). Refusing."
      exit 0
    fi
    echo "clearing a stale lock $self (winpid $OLDWIN is dead)"
    rm -f "$self"
  fi
done
printf '%s\n%s\n' "$$" "$WINPID" > "$GEAR2"

# Guard 5a — startup orphan sweep, shared with first gear.
powershell -NoProfile -File tools/orphan_sweep.ps1 -Keep "$WINPID" 2>/dev/null

# Guard 4 — run until the queue is empty (an hours cap only if one was given);
# Guard 5b — cleanup kills every worker's WINDOWS TREE.
DEADLINE=$(( $(date +%s) + HOURS * 3600 ))
capped() { [ "$HOURS" -gt 0 ] && [ "$(date +%s)" -ge "$DEADLINE" ]; }
pending() { ./.venv/Scripts/python.exe tools/queue_pending_count.py 2>/dev/null | tail -1; }
WORKER_WINPIDS=()
cleanup() {
  echo "=== second gear stopping, killing worker trees ===" >> "$LOG"
  for w in "${WORKER_WINPIDS[@]}"; do
    [ -n "$w" ] && taskkill //F //T //PID "$w" >/dev/null 2>&1
  done
  rm -f "$GEAR2" results/.queue.*of*.lock
}
trap cleanup EXIT INT TERM

WINDOW_TXT="until the queue is empty"; [ "$HOURS" -gt 0 ] && WINDOW_TXT="capped at ${HOURS}h"
echo "=== SECOND GEAR started $(date) msys $$ / winpid $WINPID — ${WINDOW_TXT}, ${WORKERS} shards ===" >> "$LOG"
echo "started. ${WINDOW_TXT}, ${WORKERS} shards. Stop early with:"
echo "  taskkill //F //T //PID $WINPID"

PASS=0
while ! capped; do
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
  left="$(pending)"
  if [ "$left" = "0" ]; then
    echo "=== SECOND GEAR queue empty $(date) after ${PASS} passes ===" >> "$LOG"
    echo "queue empty after ${PASS} passes."
    exit 0
  fi
  echo "=== ${left} stages still pending; next pass in 60s ===" >> "$LOG"
  sleep 60
done

echo "=== SECOND GEAR hours cap reached $(date), ${PASS} passes ===" >> "$LOG"
echo "hours cap reached after ${PASS} passes."
