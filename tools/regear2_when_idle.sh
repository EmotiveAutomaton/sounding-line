#!/usr/bin/env bash
# Wait for the current second-gear lineage to drain, then relaunch second gear detached.
# The wake-and-decide rule as a tool: a deadline exit must never leave the machine idle
# because nobody was watching (the seven-hour idle gap of 2026-08-13).
#
# Drain means BOTH: the recorded parent winpid is dead, AND no queue or stage python is
# alive. The second half matters because stages outlive a dead parent, and the relaunch's
# own startup sweep would kill them as orphans mid-epoch, losing hours of training.
#
# CANCELLATION IS BY FILE, NOT BY PID: `touch results/.regear.cancel`. A harness or session
# kill of this process can hit a wrapper while the msys child survives (2026-08-14: a waiter
# reported killed fired its relaunch thirty seconds later, colliding a fresh second-gear
# lineage into a first-gear shift — the immortal-loop scar in a new coat). The cancel file is
# checked every poll AND immediately before the launch, closing that race.
#
# Usage: bash tools/regear2_when_idle.sh [hours] [workers]     defaults: 24, 3

cd "$(dirname "$0")/.." || exit 1
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
HOURS="${1:-24}"
WORKERS="${2:-3}"
CANCEL="results/.regear.cancel"
rm -f "$CANCEL"

while true; do
    if [ -f "$CANCEL" ]; then
        rm -f "$CANCEL"
        echo "cancelled by file; no relaunch"
        exit 0
    fi
    ALIVE=0
    if [ -f results/.gear2.lock ]; then
        WPID=$(sed -n 2p results/.gear2.lock | tr -d '\r')
        if [ -n "$WPID" ] && tasklist //FI "PID eq $WPID" 2>/dev/null | grep -q " $WPID "; then
            ALIVE=1
        fi
    fi
    if [ "$ALIVE" = 0 ]; then
        N=$(powershell -NoProfile -File tools/queue_drain_check.ps1 2>/dev/null | tr -d '\r\n ')
        [ "$N" = "0" ] && break
    fi
    sleep 180
done

if [ -f "$CANCEL" ]; then
    rm -f "$CANCEL"
    echo "cancelled by file at the launch moment; no relaunch"
    exit 0
fi
rm -f results/.gear2.lock
powershell -NoProfile -Command "Start-Process -WindowStyle Hidden bash -ArgumentList 'run_second_gear.sh','$HOURS','$WORKERS'"
echo "second gear relaunched detached: ${HOURS}h, ${WORKERS} workers"
