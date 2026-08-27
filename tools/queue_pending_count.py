"""How many queue stages still have work to do? Prints the count of stages whose
produces file does not exist; 0 means the queue is EMPTY and the gear chain may end.

Used by tools/regear2_until_empty.sh to decide between relaunching another gear
window and declaring the queue drained. Reads the live STAGES list fresh on every
invocation, so stages added later (the S07 refresh, anything else queued mid-chain)
are counted automatically. A stage that can never produce (a permanently failed
runner) keeps the count above zero forever — that is what the waiter's relaunch cap
backstops, and why dead stages must be removed from STAGES rather than left to fail
each pass (the M02 lesson, 2026-08-26).

Usage: queue_pending_count.py [--list]   (--list prints the pending stage names)
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    spec = importlib.util.spec_from_file_location(
        "rq_for_count", REPO / "runners" / "run_queue.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    missing = []
    for s in mod.STAGES:
        if s.get("produces") is None:
            # maintenance stages (the multiplicity re-correct) re-run by design
            # and never count as pending work
            continue
        p = Path(s["produces"])
        if not p.is_absolute():
            p = REPO / p
        if not p.exists():
            missing.append(s["name"])
    if "--list" in sys.argv:
        for n in missing:
            print(n)
    else:
        print(len(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
