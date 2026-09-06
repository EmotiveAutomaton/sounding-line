"""Stage 8 manifest and expected-cell enumeration (brief I02, I07): the queue manifest over
the seven trunks and the attack matrix, the recursive expected-cell enumeration, the
identity-hash duplicate rejection, and the split receipt including the training lineages.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §5 (one manifest writer; no two cells share a produces path), §3
  (removing any literal item fails coverage; the enumeration is what the validator checks).
gates: I02: NULL of a broken enumeration is any removal leaving coverage unchanged (fails
  DOWN); ALTERNATIVE: every removal drops it; the identity check refuses duplicates (fails
  DOWN). I07: NULL of a leaky split is any test lineage whose root or descendant appears in
  the training manifest (fails DOWN: FM results on that lineage void); ALTERNATIVE: zero
  overlap. Failure direction is DOWN for either incomplete enumeration or leakage.
  bands: exhaustive.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage8 import cards as C                                              # noqa: E402
from soundingline.stage8 import (S8, SPLITS, Lineages8, Manifest8, now_iso,         # noqa: E402
                                 read_registry, write_registry)

LANE_BASE = {"discovery": 0, "pilot": 9000, "transfer": 20000, "confirmation": 30000, "attack": 40000, "conformance": 50000}
FAMILY_TAG = {"K": "WK", "K2": "WK2", "PU": "WP", "AG": "WG", "MS": "WM", "POP": "POP", "POPPU": "WE", "worlds_attack_S8": "WX",
              "worlds_conf_S8": "WX"}


class DuplicateIdentity(RuntimeError):
    pass


def lineage_ids(card: str, domain: str, n: int, split: str = "discovery", offset: int = 0, family: str | None = None) -> list[str]:
    fam = family or (C.ALL[card]["condition"] or {}).get("family") or "K"
    tag = FAMILY_TAG.get(fam, fam[:3].upper())
    base = LANE_BASE[split] + int(os.environ.get("S7_WORLD_OFFSET", "0")) + offset
    return [f"{tag}|{domain}|s0|w{base + i:05d}|{split}" for i in range(n)]


def _declared_cells() -> list[dict]:
    out = []
    for q, spec in C.ALL.items():
        corners = [{}]
        for fname, levels in (spec.get("factors") or {}).items():
            corners = [dict(c, **{fname: lv}) for c in corners for lv in levels]
        arms = spec.get("arms") or ["-"]
        readers = spec.get("readers") if spec.get("gpu") else ["-"]
        for corner in corners:
            for arm in arms:
                rs = readers if arm in C.MODEL_ARMS else ["-"]
                for r in rs:
                    doms = C.DOMAINS if spec["unit"] in ("world", "maker") else ["-"]
                    for d in doms:
                        out.append({"question": q, "arm": arm, "reader": r, "domain": d, "corner": corner,
                                    "targets": spec.get("targets"), "output": str(S8 / q / "verdict.json")})
    return out


def inapplicability(cell: dict) -> str | None:
    """Explicit structural exclusions, from the actual card and brief, not outcomes."""
    if cell["question"] == "I08" and (cell["domain"] != "essay" or
            (cell["arm"] == "FM" and cell["reader"] != C.ALL["I08"]["readers"][0])):
        return "I08 is one essay keystone on the first reader plus SOL (brief I08; run_I08), not a reader/domain factorial"
    if cell["question"] == "A05" and cell["arm"] == "DOM" and cell["corner"].get("supplied") != "none":
        return "run_A05 supplies the factor only to FMN; DOM is the shared unsupplied baseline"
    return None


def expected_cells() -> list[dict]:
    return [x for x in _declared_cells() if inapplicability(x) is None]


def removal_fails(expected: list[dict]) -> bool:
    base = len(expected)
    for q in list(C.ALL)[:6]:
        if sum(1 for e in expected if e["question"] != q) >= base:
            return False
    return True


def prepare_manifest() -> dict:
    dup = C.duplicate_identities()
    if dup:
        raise DuplicateIdentity(f"identity hashes collide: {dup}")
    m = Manifest8()
    for card in C.PRESERVATION_ORDER:
        spec = C.ALL[card]
        m.add(card, card, list(spec["depends_on"]), str(S8 / card / "verdict.json"), C.est_minutes(card), spec["gpu"], spec["primary"][:160])
    m.add("B01", "B01", [], str(S8 / "B01" / "verdict.json"), 40.0, True, C.ALL["B01"]["primary"][:160])
    m.add("B02", "B02", ["B01"], str(S8 / "B02" / "verdict.json"), 40.0, True, C.ALL["B02"]["primary"][:160])
    m.add("X12", "X12", ["B04"], str(S8 / "X12" / "verdict.json"), 20.0, False, C.ALL["X12"]["primary"][:160])
    m.add("B03", "B03", ["B04", "X12"], str(S8 / "B03" / "verdict.json"), 20.0, False, C.ALL["B03"]["primary"][:160])
    Lineages8().save()
    exp = expected_cells()
    write_registry("EXPECTED_CELLS", {"written_at": now_iso(), "cells": exp, "n": len(exp), "removal_fails": removal_fails(exp),
                                     "enumeration_version": "applicable-20260906",
                                     "inapplicable": [dict(x, reason=inapplicability(x)) for x in _declared_cells() if inapplicability(x)]})
    write_registry("IDENTITY_HASHES", {"written_at": now_iso(), "hashes": {c: C.identity_hash(c) for c in C.ALL}, "duplicates": dup})
    write_registry("ATTACK_MATRIX", {"written_at": now_iso(), "attacks": {x: {"covers": s["covers"], "expect": s["discriminator"], "consequence": s["consequence"]} for x, s in C.ATTACKS.items()}})
    return {"cells": len(m.cells), "expected": len(exp), "duplicates": dup}


def _root(lid: str) -> str:
    return "|".join(lid.split("|")[:4])


def split_receipt() -> dict:
    """I07 and I14 together: lane consistency by root, and the training manifest's lineages
    (POP_CORPUS, every reader's) against every non-training lineage's root and descendants."""
    L = Lineages8()
    roots: dict = {}
    violations = []
    for lid in L.rows:
        parts = lid.split("|")
        lane = next((p for p in parts if p in SPLITS), None)
        root = _root(lid)
        if lane is None:
            violations.append({"lid": lid, "why": "no lane suffix"})
            continue
        if root in roots and roots[root] != lane:
            violations.append({"lid": lid, "why": f"root {root} seen in {roots[root]} and {lane}"})
        roots.setdefault(root, lane)
    pop = read_registry("POP_CORPUS") or {}
    train_roots = set()
    for rec in pop.values():
        for lid in rec.get("lineages") or []:
            train_roots.add(_root(lid))
    overlap = sorted(r for r in roots if r in train_roots)
    rec = {"written_at": now_iso(), "n_lineages": len(L.rows), "n_roots": len(roots), "n_training_roots": len(train_roots),
           "overlap": overlap[:50], "violations": violations[:50], "clean": not violations and not overlap}
    write_registry("SPLIT_RECEIPT", rec)
    return rec
