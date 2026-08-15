#!/usr/bin/env bash
# Wait for the current second-gear lineage to drain, then relaunch second gear detached.
# The wake-and-decide rule as a tool: a deadline exit must never leave the machine idle
# because nobody was watching (the seven-hour idle gap of 2026-08-13).
#
# Drain means BOTH: the recorded parent winpid is dead, AND no queue or stage python is
# alive. The second half matters because stages outlive a dead parent, and the relaunch's
# own startup sweep would kill them as orphans mid-epoch, losing hours of training.
#
# Usage: bash tools/regear2_when_idle.sh [hours] [workers]     defaults: 24, 3

cd "$(dirname "$0")/.." || exit 1
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
HOURS="${1:-24}"
WORKERS="${2:-3}"

while true; do
    ALIVE=0
    if [ -f results/.gear2.lock ]; then
        WPID=$(sed -n 2p results/.gear2.lock | tr -d '\r')
        if [ -n "$WPID" ] && tasklist //FI "PID eq $WPID" 2>/dev/null | grep -q "$WPID"; then
            ALIVE=1
        fi
    fi
    if [ "$ALIVE" = 0 ]; then
        N=$(powershell -NoProfile -File tools/queue_drain_check.ps1 2>/dev/null | tr -d '\r\n ')
        [ "$N" = "0" ] && break
    fi
    sleep 180
done

rm -f results/.gear2.lock
powershell -NoProfile -Command "Start-Process -WindowStyle Hidden bash -ArgumentList 'run_second_gear.sh','$HOURS','$WORKERS'"
echo "second gear relaunched detached: ${HOURS}h, ${WORKERS} workers"
