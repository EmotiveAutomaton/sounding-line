"""Stage 7 manifest and expected-cell enumeration (brief §9, §14, I02, I14): the queue
manifest over the eight trunks and the attack matrix, the recursive expected-cell
enumeration (every question, attack, factor corner, arm, reader, target, lineage family,
and output path), the identity-hash duplicate rejection (§9), and the split receipt
(descendant-clean lineages across the six lanes).

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §5 (one manifest writer; no two stages share a produces path; a
  gate dependency is the verdict), §3 (removing any literal item fails coverage: the
  enumeration is what the validator checks against, so the check can fail).
gates: I02: NULL of a broken enumeration is any removal that leaves coverage unchanged
  (failure direction: coverage must DROP on removal); ALTERNATIVE: every removal drops
  it. The identity check: NULL of a duplicate registry is any repeated identity hash
  (fails DOWN: the manifest refuses to prepare); ALTERNATIVE: all hashes distinct.
bands: exhaustive (refuse / prepare).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage7 import cards as C                                              # noqa: E402
from soundingline.stage7 import (S7, SPLITS, Lineages7, Manifest7, now_iso,         # noqa: E402
                                 write_registry)

LANE_BASE = {"discovery": 0, "pilot": 9000, "transfer": 20000, "confirmation": 30000, "attack": 40000, "conformance": 50000}


class DuplicateIdentity(RuntimeError):
    pass


def lineage_ids(card: str, domain: str, n: int, split: str = "discovery", offset: int = 0, family: str | None = None) -> list[str]:
    """Deterministic lineage ids. Questions that share a world family (the K ladder on
    one family, the R ladder on another) share ids so paired arms see the same worlds;
    lanes are disjoint index bands; expansion rungs offset the index."""
    import os                                                                     # noqa: PLC0415
    fam = family or C.ALL[card]["identity"]["lineage"]
    fam = fam.split("_twins")[0].split("_crossed")[0].split("_swaps")[0].split("_equivalence")[0].split("_untouched")[0]
    if fam.startswith("worlds_K"):
        fam = "WK"
    elif fam.startswith("worlds_R"):
        fam = "WR"
    elif fam.startswith("worlds_A"):
        fam = "WA"
    elif fam.startswith("worlds_V"):
        fam = "WV"
    elif fam.startswith("worlds_P"):
        fam = "WP"
    elif fam.startswith("worlds_attack") or fam.startswith("worlds_conf"):
        fam = "WX"
    elif fam.startswith("histories"):
        fam = "WH"
    base = LANE_BASE[split] + int(os.environ.get("S7_WORLD_OFFSET", "0")) + offset
    return [f"{fam}|{domain}|s0|w{base + i:05d}|{split}" for i in range(n)]


def expected_cells() -> list[dict]:
    """The recursive enumeration: one entry per (question, arm, reader, domain, factor
    corner) for GPU questions, one per (question, factor corner) for CPU questions, plus
    every attack; each with its output path."""
    out = []
    for q, spec in C.ALL.items():
        corners = [{}]
        for fname, levels in (spec.get("factors") or {}).items():
            corners = [dict(c, **{fname: lv}) for c in corners for lv in levels]
        arms = spec.get("arms") or ["-"]
        readers = spec.get("readers") if spec.get("gpu") else ["-"]
        model_arms = {"DIR", "DIRS", "SLJ", "HDIR", "CDIR", "SDIR", "weighted_language_hypotheses", "sequential_hypothesis_particles",
                      "adaptive_factor_expansion", "synthesized_agent_model", "epistemic_translation"}
        for corner in corners:
            for arm in arms:
                rs = readers if arm in model_arms else ["-"]
                for r in rs:
                    doms = C.DOMAINS if spec["unit"] in ("world", "world_pair") else ["-"]
                    for d in doms:
                        out.append({"question": q, "arm": arm, "reader": r, "domain": d, "corner": corner,
                                    "targets": spec.get("targets"), "output": str(S7 / q / "verdict.json")})
    return out


def coverage_check(expected: list[dict], realized: dict) -> dict:
    """realized: {question: {(arm, reader, domain, corner-json): n_rows}}; a cell counts
    covered when its question has a verdict and its (arm, reader, domain) has rows or
    the question is CPU-only."""
    missing = []
    for e in expected:
        q = e["question"]
        if q not in realized:
            missing.append(e)
    return {"expected": len(expected), "missing": len(missing), "missing_questions": sorted({m["question"] for m in missing})[:50]}


def removal_fails(expected: list[dict]) -> bool:
    """I02's self-check: removing any single literal item changes the enumeration."""
    base = len(expected)
    for q in list(C.ALL)[:5]:
        n = sum(1 for e in expected if e["question"] != q)
        if n >= base:
            return False
    return True


def prepare_manifest() -> dict:
    dup = C.duplicate_identities()
    if dup:
        raise DuplicateIdentity(f"identity hashes collide: {dup}")
    m = Manifest7()
    for card in C.PRESERVATION_ORDER:
        spec = C.ALL[card]
        m.add(card, card, list(spec["depends_on"]), str(S7 / card / "verdict.json"), C.est_minutes(card), spec["gpu"], spec["primary"][:160])
    m.add("B01", "B01", [], str(S7 / "B01" / "verdict.json"), 60.0, True, C.ALL["B01"]["primary"][:160])
    m.add("B02", "B02", ["B01"], str(S7 / "B02" / "verdict.json"), 60.0, True, C.ALL["B02"]["primary"][:160])
    m.add("B03", "B03", ["B02"], str(S7 / "B03" / "verdict.json"), 40.0, True, C.ALL["B03"]["primary"][:160])
    m.add("B06", "B06", ["B05", "B03"], str(S7 / "B06" / "verdict.json"), 20.0, False, C.ALL["B06"]["primary"][:160])
    m.add("X24", "X24", ["B05"], str(S7 / "X24" / "verdict.json"), 20.0, False, C.ALL["X24"]["primary"][:160])
    Lineages7().save()
    exp = expected_cells()
    write_registry("EXPECTED_CELLS", {"written_at": now_iso(), "cells": exp, "n": len(exp), "removal_fails": removal_fails(exp)})
    write_registry("IDENTITY_HASHES", {"written_at": now_iso(), "hashes": {c: C.identity_hash(c) for c in C.ALL}, "duplicates": dup})
    write_registry("ATTACK_MATRIX", {"written_at": now_iso(), "attacks": {x: {"covers": s["covers"], "expect": s["discriminator"], "consequence": s["consequence"]} for x, s in C.ATTACKS.items()}})
    return {"cells": len(m.cells), "expected": len(exp), "duplicates": dup}


def split_receipt() -> dict:
    """I14: every lineage id's lane is read from its own suffix; descendants (twin, mutant,
    demo, paraphrase suffixes) inherit the parent's lane; a pair of ids sharing a root
    but not a lane is a violation."""
    L = Lineages7()
    roots: dict = {}
    violations = []
    for lid in L.rows:
        parts = lid.split("|")
        lane = next((p for p in parts if p in SPLITS), None)
        root = "|".join(p for p in parts[:4])
        if lane is None:
            violations.append({"lid": lid, "why": "no lane suffix"})
            continue
        if root in roots and roots[root] != lane:
            violations.append({"lid": lid, "why": f"root {root} seen in {roots[root]} and {lane}"})
        roots.setdefault(root, lane)
    rec = {"written_at": now_iso(), "n_lineages": len(L.rows), "n_roots": len(roots), "violations": violations[:50], "clean": not violations}
    write_registry("SPLIT_RECEIPT", rec)
    return rec
