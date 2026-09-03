"""Stage 7 fresh-clone and provenance verifier (brief §15.30, X24): from the results tree
alone, re-hash every landed verdict's completion marker against the files on disk, check
that the substantive questions carry rows and prediction references that exist, that the
oracle bundles referenced by rows exist outside every capsule, that no packet exists at a
forbidden path, that the source manifest's clone heads still match the reference
workspace, and that the confirmation inputs were untouched lineages. Nothing is trusted
from memory.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §5 (markers are checked against data, never a bare exists(); the
  repository-level half stays with tools/verify_locks.py).
bands: a report dict with `ok`; X24 turns it into the attack verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage7 import cards as C                                              # noqa: E402
from soundingline.stage7 import S7, read_json, read_jsonl, read_registry, sha256_file  # noqa: E402


def verify(max_cards: int | None = None) -> dict:
    problems = []
    n_checked = 0
    for c in (list(C.QUESTIONS) + list(C.ATTACKS))[:max_cards]:
        vp = S7 / c / "verdict.json"
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
        # a confirmation cell (B01-B03) runs its source card in the confirmation lane: its rows
        # live under <source>/confirmation/, checked below against the frozen registry
        if spec.get("gpu") and spec["unit"] in ("world", "world_pair", "history", "session") and c not in ("B01", "B02", "B03")                 and not (S7 / c / "cases.jsonl").exists():
            problems.append(f"{c}: substantive question without cases.jsonl")
        if (S7 / c / "cases.jsonl").exists():
            rows = read_jsonl(S7 / c / "cases.jsonl")
            for r in rows[:50]:
                if r.get("pred_ref") and not Path(r["pred_ref"]).exists():
                    problems.append(f"{c}: prediction reference missing {r['pred_ref']}")
                    break
                if r.get("truth_ref") and not Path(r["truth_ref"]).exists() and r.get("valid"):
                    problems.append(f"{c}: oracle bundle missing {r['truth_ref']}")
                    break
    for stray in S7.rglob("CURATOR_PACKET*.md"):
        if stray != S7 / "CURATOR_PACKET_FINAL.md":
            problems.append(f"forbidden packet path: {stray}")
    for cap in (S7 / "capsules").rglob("*.json") if (S7 / "capsules").exists() else []:
        if "oracle" in cap.name.lower():
            problems.append(f"oracle-named file inside a capsule: {cap}")
    src = read_registry("SOURCE_MANIFEST") or {}
    from runners.stage7.conformance import sources as SRC                          # noqa: PLC0415
    for k, s in (src.get("sources") or {}).items():
        rec = s.get("clone_receipt") or {}
        if rec.get("present"):
            live = SRC.clone_receipt(s["clone"])
            if live.get("head") != rec.get("head"):
                problems.append(f"source {k}: clone head moved {rec.get('head')} -> {live.get('head')}")
    conf = read_registry("CONFIRMATION_REGISTRY") or {}
    for s in conf.get("selected") or []:
        d = S7 / s["card"] / "confirmation" / "cases.jsonl"
        if d.exists():
            for r in read_jsonl(d)[:200]:
                if "|confirmation" not in r["unit_id"] and "confirmation" not in r["unit_id"]:
                    problems.append(f"confirmation {s['card']}: a non-confirmation lineage {r['unit_id']}")
                    break
    ok = not problems
    return {"ok": ok, "n_verdicts_checked": n_checked, "problems": problems[:40], "summary": f"{n_checked} verdicts re-hashed; {len(problems)} problems"}


if __name__ == "__main__":
    rep = verify()
    print(rep["summary"])
    for p in rep["problems"]:
        print(" -", p)
    sys.exit(0 if rep["ok"] else 1)
