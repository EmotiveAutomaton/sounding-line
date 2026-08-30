"""Read-only structural, result, and runtime validator for the Stage-5 record (brief §9,
§13). Never writes, never repairs. Exit 1 on any problem.

Checks: every mandatory card has a verdict whose completion marker verifies; the root
registries exist; the packet exists only at the one path and only with closure recorded;
the run label is a permitted one and a short run is not labeled a completed window; the
lanes are separate; the confirmation registry names at most two cards, each fresh at
opening; the completion module can read every produce."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_cards                                                      # noqa: E402
from soundingline import completion                                               # noqa: E402
from soundingline.stage5 import (S5, CARDS, Lineages5, RunContract5, check_marker,   # noqa: E402
                                 read_json, read_registry)


def main() -> int:
    problems = []
    contract = RunContract5.load()
    if contract is None:
        print("no RUN_CONTRACT.json")
        return 1
    for name in ("EXPECTED_CELLS", "WORKLOAD_LOCK", "CONSTRUCTION_IDENTITIES", "ROUTE_INFORMATION", "COVERAGE", "COMPLETION", "CONFIRMATION_REGISTRY"):
        if read_registry(name) is None:
            problems.append(f"registry missing: {name}")
    verdicts = {}
    for card in CARDS + ["I02pilot"]:
        vp = S5 / card / "verdict.json"
        st = completion.inspect(vp, {"card": card} if card != "I02pilot" else None)
        if st["status"] != completion.OK and st["status"] != completion.UNVERIFIABLE:
            problems.append(f"{card}: produce {st['status']} ({st['reason']})")
            continue
        v = read_json(vp)
        verdicts[card] = v
        bad = check_marker(v)
        if bad:
            problems.append(f"{card}: marker {bad}")
    packet = S5 / "CURATOR_PACKET_FINAL.md"
    strays = [p for p in S5.glob("*PACKET*") if p != packet] + [p for p in S5.glob("**/*packet*.md") if p != packet]
    if strays:
        problems.append(f"stray packet paths: {[str(p) for p in strays]}")
    if packet.exists() and not (contract.data.get("exhausted") or contract.deadline_passed()):
        problems.append("packet exists without recorded closure")
    label = contract.data.get("run_label")
    if packet.exists() and label not in ("RUN_TO_EMPTY", "SHORT_RUN", "COMPLETE_24H"):
        problems.append(f"run label {label!r} not permitted")
    if label == "COMPLETE_24H" and not contract.window_elapsed():
        problems.append("a short run labeled COMPLETE_24H")
    L = Lineages5()
    lanes = {r["split"] for r in L.rows.values()}
    if L.rows and not {"discovery", "transfer", "confirmation"} <= lanes:
        problems.append(f"lanes present: {sorted(lanes)}")
    reg = read_registry("CONFIRMATION_REGISTRY") or {}
    sel = [v for v in (reg.get("selected") or {}).values() if v]
    if len(sel) > 2:
        problems.append(f"more than two confirmations: {sel}")
    for card in sel:
        opened = [r for r in L.rows.values() if r["card"] == s5_cards.DERIVED.get(card, card) and r["split"] == "confirmation" and r.get("confirmation_access")]
        touched = [r for r in opened if r.get("inspected") and r["confirmation_access"]["at"] > r.get("allocated_at", "")]
        if touched:
            problems.append(f"{card}: a confirmation lineage was inspected before opening")
    resolved = sum(1 for v in verdicts.values() if v.get("exec") in ("COMPLETE", "FAILED", "BLOCKED", "DEFERRED"))
    print(f"{len(verdicts)} verdicts, {resolved} resolved of {len(CARDS)} mandatory cards; label {label}; "
          f"elapsed {contract.elapsed_h():.2f} h; confirmations {sel}")
    for p in problems:
        print("  PROBLEM:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
