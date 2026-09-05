"""Stage 8 fresh-clone verifier (X12): from the results tree alone, re-hash every landed
verdict's completion marker against the files on disk, check that substantive cells carry
rows and prediction references that exist, that oracle bundles referenced by rows exist
outside every capsule, that no packet exists at a forbidden path, that the adapter hashes
still match the registry, that the testbed clone heads still match their receipts, and that
the confirmation inputs were untouched lineages.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §5 (markers are checked against data, never a bare exists()).
gates: NULL of a drifted tree is any mismatch (fails DOWN: the packet is blocked);
  ALTERNATIVE: none. bands: a report dict with `ok`.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage8 import cards as C                                              # noqa: E402
from soundingline.stage8 import S8, adapter_hash, read_json, read_jsonl, read_registry, sha256_file  # noqa: E402


def verify(max_cards: int | None = None) -> dict:
    problems = []
    n_checked = 0
    for c in (list(C.QUESTIONS) + list(C.ATTACKS))[:max_cards]:
        vp = S8 / c / "verdict.json"
        if not vp.exists():
            continue
        n_checked += 1
        v = read_json(vp)
        for kind in ("outputs", "inputs"):
            for name, rec in ((v.get("marker") or {}).get(kind) or {}).items():
                p = Path(rec["path"])
                if not p.exists():
                    problems.append(f"{c}: {kind} {name} missing at {p}")
                elif sha256_file(p) != rec["sha256"]:
                    problems.append(f"{c}: {kind} {name} hash mismatch")
        spec = C.ALL[c]
        if spec.get("gpu") and spec["unit"] in ("world", "maker") and c not in ("B01", "B02") and v.get("outcome") not in ("NOT_RUN",) and not (S8 / c / "cases.jsonl").exists():
            problems.append(f"{c}: substantive question without cases.jsonl")
        if (S8 / c / "cases.jsonl").exists():
            for r in read_jsonl(S8 / c / "cases.jsonl")[:50]:
                if r.get("pred_ref") and not Path(r["pred_ref"]).exists():
                    problems.append(f"{c}: prediction reference missing {r['pred_ref']}")
                    break
                if r.get("truth_ref") and r.get("valid") and not Path(r["truth_ref"]).exists():
                    problems.append(f"{c}: oracle bundle missing {r['truth_ref']}")
                    break
    for stray in S8.rglob("CURATOR_PACKET*.md"):
        if stray != S8 / "CURATOR_PACKET_FINAL.md":
            problems.append(f"forbidden packet path: {stray}")
    for cap in (S8 / "capsules").rglob("*.json") if (S8 / "capsules").exists() else []:
        if "oracle" in cap.name.lower():
            problems.append(f"oracle-named file inside a capsule: {cap}")
    for name, rec in (read_registry("ADAPTERS") or {}).items():
        p = Path(rec.get("path", ""))
        if not p.exists():
            problems.append(f"adapter {name} missing at {p}")
        elif adapter_hash(p) != rec.get("sha"):
            problems.append(f"adapter {name} hash drifted")
    from runners.stage8.testbed import clones as CL                               # noqa: PLC0415
    for name, rec in ((read_registry("TESTBED_SOURCES") or {}).get("clones") or {}).items():
        r0 = rec.get("receipt") or {}
        if r0.get("present"):
            live = CL.receipt(name)
            if live.get("head") != r0.get("head"):
                problems.append(f"clone {name}: head moved {r0.get('head')} -> {live.get('head')}")
    conf = read_registry("CONFIRMATION_REGISTRY") or {}
    for s in conf.get("selected") or []:
        d = S8 / s["card"] / "confirmation" / "cases.jsonl"
        if d.exists():
            for r in read_jsonl(d)[:200]:
                if "confirmation" not in r["unit_id"]:
                    problems.append(f"confirmation {s['card']}: a non-confirmation lineage {r['unit_id']}")
                    break
    return {"ok": not problems, "n_verdicts_checked": n_checked, "problems": problems[:40], "summary": f"{n_checked} verdicts re-hashed; {len(problems)} problems"}


if __name__ == "__main__":
    rep = verify()
    print(rep["summary"])
    for p in rep["problems"]:
        print(" -", p)
    sys.exit(0 if rep["ok"] else 1)
