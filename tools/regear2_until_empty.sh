#!/usr/bin/env bash
# Chain second-gear windows until the queue is EMPTY (his order, 2026-08-26): when a
# gear window expires with runnable stages remaining, relaunch another one, so no
# renewal check-in is ever owed by anybody. Extends tools/regear2_when_idle.sh (one
# shot) into a loop with an emptiness test.
#
# Safety, inherited and added:
#   - NEVER relaunches while the gear loop or any stage python is alive: the
#     relaunch's startup sweep would kill live stages mid-epoch (the regear scar).
#   - run_second_gear.sh refuses duplicate loops by winpid, so a race cannot
#     double-launch a lineage.
#   - CANCELLATION IS BY FILE, never by pid: touch results/.regear.cancel. Checked
#     every poll AND immediately before each launch (the 2026-08-14 waiter race).
#   - A relaunch CAP backstops a stage that can never produce keeping the chain
#     alive forever; on cap it logs exactly which stages remained.
#   - One waiter at a time, by winpid lock (results/.regear_until_empty.lock).
#
# Emptiness = tools/queue_pending_count.py prints 0 (every stage's produces file
# exists). The count reads STAGES fresh each poll, so stages queued mid-chain (the
# S07 refresh) extend the chain automatically.
#
# Usage: bash tools/regear2_until_empty.sh [hours] [workers] [cap]   defaults: 24 3 3

cd "$(dirname "$0")/.." || exit 1
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Windows/System32/WindowsPowerShell/v1.0:$PATH"
HOURS="${1:-24}"
WORKERS="${2:-3}"
CAP="${3:-3}"
CANCEL="results/.regear.cancel"
WLOCK="results/.regear_until_empty.lock"
LOG="results/regear_until_empty.log"
PYEXE="./.venv/Scripts/python.exe"

WINPID=$(cat /proc/$$/winpid 2>/dev/null)
alive_win() { [ -n "$1" ] && tasklist //FI "PID eq $1" 2>/dev/null | grep -q " $1 "; }

if [ -f "$WLOCK" ]; then
    OLD=$(sed -n 2p "$WLOCK" | tr -d '\r')
    if alive_win "$OLD"; then
        echo "an until-empty waiter is already running (winpid $OLD). Refusing."
        exit 0
    fi
    rm -f "$WLOCK"
fi
printf '%s\n%s\n' "$$" "$WINPID" > "$WLOCK"
rm -f "$CANCEL"
echo "=== until-empty waiter started $(date) winpid $WINPID — ${HOURS}h x ${WORKERS} shards, cap ${CAP} ===" >> "$LOG"

RELAUNCHES=0
while true; do
    if [ -f "$CANCEL" ]; then
        rm -f "$CANCEL" "$WLOCK"
        echo "=== cancelled by file $(date) ===" >> "$LOG"
        exit 0
    fi
    GEAR_ALIVE=0
    if [ -f results/.gear2.lock ]; then
        G=$(sed -n 2p results/.gear2.lock | tr -d '\r')
        alive_win "$G" && GEAR_ALIVE=1
    fi
    if [ "$GEAR_ALIVE" = 1 ]; then
        sleep 240
        continue
    fi
    # gear is dead: wait for its stages to finish before anything else
    N=$(powershell -NoProfile -File tools/queue_drain_check.ps1 2>/dev/null | tr -d '\r\n ')
    if [ "$N" != "0" ]; then
        sleep 180
        continue
    fi
    PENDING=$("$PYEXE" tools/queue_pending_count.py 2>>"$LOG" | tr -d '\r\n ')
    case "$PENDING" in
        ''|*[!0-9]*) PENDING=-1;;
    esac
    if [ "$PENDING" = "0" ]; then
        rm -f "$WLOCK"
        echo "=== queue EMPTY $(date): chain complete after ${RELAUNCHES} relaunches ===" >> "$LOG"
        exit 0
    fi
    if [ "$RELAUNCHES" -ge "$CAP" ]; then
        rm -f "$WLOCK"
        echo "=== cap ${CAP} reached $(date), ${PENDING} stages still pending: ===" >> "$LOG"
        "$PYEXE" tools/queue_pending_count.py --list >> "$LOG" 2>&1
        exit 0
    fi
    if [ -f "$CANCEL" ]; then
        rm -f "$CANCEL" "$WLOCK"
        echo "=== cancelled at the launch moment $(date) ===" >> "$LOG"
        exit 0
    fi
    rm -f results/.gear2.lock
    powershell -NoProfile -Command "Start-Process -WindowStyle Hidden bash -ArgumentList 'run_second_gear.sh','$HOURS','$WORKERS'"
    RELAUNCHES=$((RELAUNCHES + 1))
    echo "=== relaunch ${RELAUNCHES}/${CAP} fired $(date): ${PENDING} stages were pending ===" >> "$LOG"
    sleep 600
done
