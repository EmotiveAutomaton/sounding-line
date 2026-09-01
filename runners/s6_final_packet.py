"""Stage 6 packet waiter (2026-09-01). The locked ladder exhausts far below the lock's
forecast, so the scheduler closes SHORT and exits days before hour 168; the reporter refuses
any packet before the deadline (§11.1), and nothing else would write it. This stage waits
for the contract deadline, then validates and writes the one packet. It holds no GPU lock
and runs beside the other queued work.

DESIGN CHECK (2026-09-01)
lessons read: LESSONS §5 (a deadline exit with no successor idles the machine silently: this
  is the successor for the packet; a long-lived waiter honors a cancel file checked every
  poll and again immediately before its action; every stage carries a produces guard: the
  packet path itself).
expectations: not a measurement. Under normal operation the waiter sleeps to the deadline,
  validation passes, and CURATOR_PACKET_FINAL.md appears once; if the scheduler wrote the
  packet itself (a run that reached the deadline live) the reporter refuses the second
  write and the waiter exits 0 on finding the file. Failure direction: a packet written
  early — impossible here, the reporter's own deadline check is the guard and this stage
  never forces it.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
from soundingline.stage6 import S6, RunContract6                                    # noqa: E402

CANCEL = S6 / "CANCEL_PACKET_WAIT"
PACKET = S6 / "CURATOR_PACKET_FINAL.md"


def main() -> int:
    contract = RunContract6.load()
    if contract is None or not contract.data.get("execution_start"):
        print("no started contract; nothing to wait for")
        return 2
    last_note = 0.0
    while not contract.deadline_passed():
        if CANCEL.exists():
            print("cancel file present; leaving without a packet")
            return 3
        if time.time() - last_note > 3600:
            print(f"waiting: elapsed {contract.elapsed_h():.1f} h of {contract.data['run_hours']}; deadline {contract.data['deadline']}", flush=True)
            last_note = time.time()
        time.sleep(600)
        contract = RunContract6.load()
    if CANCEL.exists():
        print("cancel file present at the deadline; leaving without a packet")
        return 3
    from runners.stage6.validate import validate                                   # noqa: PLC0415
    from runners.stage6 import report as REP                                       # noqa: PLC0415
    cov = validate(write=True)
    print("validation:", {k: v for k, v in cov.items() if k != "cells"})
    if PACKET.exists():
        print("packet already written by the scheduler:", PACKET)
        return 0
    try:
        p = REP.write_final_packet()
        print("final packet written:", p)
    except Exception as e:                                                        # noqa: BLE001
        print("packet refused or failed:", e)
        return 0 if PACKET.exists() else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
