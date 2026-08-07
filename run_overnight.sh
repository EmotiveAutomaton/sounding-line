#!/usr/bin/env bash
# OVERNIGHT — use the whole machine. Nobody is watching, so every safety here is load-bearing.
#
# The daytime loop (run_forever.sh) runs one job at a time so the machine stays responsive. This one
# does not care about lag. What it cares about is the failure that actually happened on 2026-08-07:
# four loops running at once, each respawning a queue, each queue launching a duplicate of the same
# GPU job, every result written twice, and nobody there to notice.
#
# FOUR GUARDS, and none of them is optional:
#
#   1. ONE LOOP.        A pid lock at the shell level. A second launch refuses and exits.
#   2. MUTUAL EXCLUSION. Refuses to start while the daytime loop holds its lock, and vice versa.
#                        Two loops with different names is the same bug wearing a hat.
#   3. NO SHARED STAGES. Workers are SHARDS, not copies. Stage i is owned by shard i % N, decided by
#                        arithmetic before anything starts, so two workers can never pick the same
#                        stage. No claim files, no races, no partial writes landing on each other.
#   4. A DEADLINE.      It stops on its own. An unattended loop with no end is how a machine is found
#                        at 100% three days later.
#
# Usage:  bash run_overnight.sh [hours] [workers]
#         defaults: 10 hours, 3 workers
#
# WORKER COUNT IS A MEMORY DECISION, not a speed one. Three concurrent readers on a 12 GB card used
# 11.3 GB. Four would have failed. Raise it only after checking `nvidia-smi` headroom for the models
# actually in the queue.

cd "$(dirname "$0")" || exit 1
HOURS="${1:-10}"
WORKERS="${2:-3}"
LOCK="results/.loop.lock"
NIGHT="results/.overnight.lock"
LOG="results/queue_main.log"
mkdir -p results

alive() { [ -n "$1" ] && kill -0 "$1" 2>/dev/null; }

# Guard 2 — the daytime loop and this one are mutually exclusive.
if [ -f "$LOCK" ] && alive "$(cat "$LOCK" 2>/dev/null)"; then
  echo "the daytime loop is running as pid $(cat "$LOCK"). Stop it first:  kill $(cat "$LOCK")"
  exit 1
fi

# Guard 1 — one overnight loop.
if [ -f "$NIGHT" ]; then
  OLD=$(cat "$NIGHT" 2>/dev/null)
  if alive "$OLD"; then
    echo "an overnight loop is already running as pid $OLD. Refusing to start a second."
    exit 0
  fi
  echo "clearing a stale overnight lock from pid $OLD"
fi
echo $$ > "$NIGHT"

# Guard 4 — a deadline, and a trap that takes the whole worker group down with the parent.
DEADLINE=$(( $(date +%s) + HOURS * 3600 ))
cleanup() {
  echo "=== overnight stopping, killing workers ===" >> "$LOG"
  pkill -P $$ 2>/dev/null
  rm -f "$NIGHT" results/.queue.*of*.lock
}
trap cleanup EXIT INT TERM

echo "=== OVERNIGHT started $(date) as pid $$ — ${HOURS}h deadline, ${WORKERS} workers ===" >> "$LOG"
echo "started. ${HOURS}h deadline, ${WORKERS} shards. Stop early with:  kill $$"

PASS=0
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  PASS=$((PASS + 1))
  echo "=== pass $PASS begins $(date) ===" >> "$LOG"

  # Guard 3 — shards, not copies. Each worker owns a disjoint slice of the stage list.
  pids=()
  for i in $(seq 0 $((WORKERS - 1))); do
    ./.venv/Scripts/python.exe runners/run_queue.py --shard "$i" --shards "$WORKERS" \
      >> "results/queue_shard${i}.log" 2>&1 &
    pids+=($!)
    sleep 5   # stagger model loading so N processes do not hit the card in the same instant
  done
  for pid in "${pids[@]}"; do wait "$pid"; done

  echo "=== pass $PASS complete $(date) ===" >> "$LOG"

  # Every stage carries an output guard, so a pass with nothing left to do returns instantly.
  # Sleeping between passes stops that becoming a spin loop.
  sleep 60
done

echo "=== OVERNIGHT deadline reached $(date), ${PASS} passes ===" >> "$LOG"
echo "deadline reached after ${PASS} passes."
