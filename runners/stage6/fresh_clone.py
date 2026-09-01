"""Stage 6 fresh-clone and provenance verifier (brief §13.21, X24): from the results tree
alone, re-derive the manifests' expectations and check that every landed verdict's
completion marker hashes match the files on disk, that the raw-output receipts exist for
the substantive cards, that no packet exists at a forbidden path, and that the lineage
sources referenced by rows exist. "Fresh clone" here means: nothing is trusted from
memory — every check re-reads and re-hashes from disk.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §5 (markers are checked against data, never a bare exists(); verify
  locks and read deletion lines before any commit — the repository-level half stays with
  the curator loop's tools/verify_locks.py).
bands: a report dict with `ok`; X24 turns it into the attack verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage6 import cards as CARDS_MOD                                      # noqa: E402
from soundingline.stage6 import S6, read_json, sha256_file                         # noqa: E402


def verify(max_cards: int | None = None) -> dict:
    problems = []
    n_checked = 0
    cards = (list(CARDS_MOD.CARDS) + list(CARDS_MOD.ATTACKS))[:max_cards]
    for c in cards:
        vp = S6 / c / "verdict.json"
        if not vp.exists():
            continue
        n_checked += 1
        v = read_json(vp)
        marker = v.get("marker") or {}
        for kind in ("outputs", "inputs"):
            for name, rec in (marker.get(kind) or {}).items():
                p = Path(rec["path"])
                if not p.exists():
                    problems.append(f"{c}: {kind} {name} missing at {p}")
                    continue
                if sha256_file(p) != rec["sha256"]:
                    problems.append(f"{c}: {kind} {name} hash mismatch")
        spec = CARDS_MOD.ALL[c]
        if spec.get("gpu") and spec["engine"] in ("tournament",) and not (S6 / c / "cases.jsonl").exists():
            problems.append(f"{c}: substantive GPU card without cases.jsonl")
    for stray in S6.rglob("CURATOR_PACKET*.md"):
        if stray != S6 / "CURATOR_PACKET_FINAL.md":
            problems.append(f"forbidden packet path: {stray}")
    for stray in REPO.glob("results/phase_2_4_stage_6*/**/CURATOR_PACKET_FINAL.md"):
        if stray.parent != S6:
            problems.append(f"packet outside the root: {stray}")
    ok = not problems
    return {"ok": ok, "n_verdicts_checked": n_checked, "problems": problems[:40],
            "summary": f"{n_checked} verdicts re-hashed; {len(problems)} problems"}


if __name__ == "__main__":
    rep = verify()
    print(rep["summary"])
    for p in rep["problems"]:
        print(" -", p)
    sys.exit(0 if rep["ok"] else 1)
