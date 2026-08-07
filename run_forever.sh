#!/usr/bin/env bash
# One job at a time, forever. Lives in the repo rather than /tmp so there is exactly one copy.
#
# On 2026-08-07 FOUR copies of the previous loop were running at once, each respawning a queue after
# every pass, each queue launching a duplicate of the same GPU job. Memory hit 11.3 of 12.3 GB and
# every result was being written twice. The queue's own pid lock stopped duplicate queues from doing
# work but did nothing about the shells, and killing a queue just made its shell start another.
#
# So this script takes its own lock, at the shell level, before the queue takes one.
cd "$(dirname "$0")" || exit 1
LOCK="results/.loop.lock"
mkdir -p results

if [ -f "$LOCK" ]; then
  OLD=$(cat "$LOCK" 2>/dev/null)
  if [ -n "$OLD" ] && kill -0 "$OLD" 2>/dev/null; then
    echo "a loop is already running as pid $OLD. Refusing to start a second."
    exit 0
  fi
  echo "clearing a stale loop lock from pid $OLD"
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT INT TERM

echo "=== loop started $(date) as pid $$ ===" >> results/queue_main.log
while true; do
  ./.venv/Scripts/python.exe runners/run_queue.py >> results/queue_main.log 2>&1
  echo "=== pass complete $(date) ===" >> results/queue_main.log
  sleep 30
done
