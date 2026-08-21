#!/usr/bin/env bash
# Wake watcher — the gear engines run DETACHED, so the agent harness gets no completion
# signal from them (found 2026-08-21 afternoon: two verdicts sat unreported for hours).
# This script runs as a HARNESS-TRACKED background task and exits the moment any watched
# produce appears or changes, which re-invokes the agent. Relaunched by the agent each
# pass with a fresh snapshot; a max-wait deadline keeps it from hanging forever.
#
#   tools/wake_watcher.sh <max_wait_seconds> <path> [<path> ...]
export PATH=/usr/bin:/bin:$PATH
cd "$(dirname "$0")/.." || exit 1
MAX=${1:-28800}; shift
declare -A SNAP
for p in "$@"; do
  if [ -e "$p" ]; then SNAP[$p]=$(stat -c %Y "$p" 2>/dev/null || echo 0); else SNAP[$p]=absent; fi
done
START=$(date +%s)
while :; do
  for p in "$@"; do
    if [ -e "$p" ]; then
      NOW_M=$(stat -c %Y "$p" 2>/dev/null || echo 0)
      if [ "${SNAP[$p]}" = "absent" ] || [ "$NOW_M" != "${SNAP[$p]}" ]; then
        echo "WAKE: $p (was ${SNAP[$p]}, now $NOW_M)"
        exit 0
      fi
    fi
  done
  if [ $(( $(date +%s) - START )) -ge "$MAX" ]; then
    echo "WAKE: deadline after ${MAX}s, no produce changed"
    exit 0
  fi
  sleep 120
done
