"""Mixed-control history units (brief §7.3, §7.5): the controlled histories as lineage-
keyed units per lane, their visible evidence in the two interfaces §16.4 reports apart
(process-aware: the actor-blind event log; final-only: the final text per section, no
events), and their oracle bundles.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (count the construction's identity space against the unit
  count: every history hashes its content onto its lineage; the final-only interface can
  never borrow logged actor identity), §5 (the history is the independent unit).
gates: none here. bands: none.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runners.stage7.constructor import histories as H                              # noqa: E402
from soundingline.stage7 import EVIDENCE_VERSION                                   # noqa: E402

LANE_BASE = {"discovery": 0, "pilot": 9000, "transfer": 20000, "confirmation": 30000, "attack": 40000, "conformance": 50000}
MIN_SEG = 3


def history_ids(card: str, kind: str, n: int, split: str = "discovery", offset: int = 0) -> list[str]:
    base = LANE_BASE[split] + offset
    return [f"{card}|{kind}|h{base + i:05d}|{split}" for i in range(n)]


def unit(hid: str, kind: str, n_events: int = 24) -> dict:
    return H.make_history(hid, kind, n_events)


def final_text(h: dict) -> dict:
    """The final-only interface: the last text per section (events folded), no log."""
    out: dict = {}
    for e in h["events"]:
        if e["reverted"]:
            continue
        out.setdefault(e["section"], [])
        if e["op"] == "replace" and out[e["section"]]:
            out[e["section"]][-1] = e["text"]
        else:
            out[e["section"]].append(e["text"])
    return {s: " ".join(t) for s, t in out.items()}


def visible_evidence(h: dict, interface: str = "process", unit_ref: str = "u", condition_ref: str = "c") -> dict:
    n = h["n"]
    options = [str(k) for k in range(MIN_SEG, n - MIN_SEG + 1)] + ["none"]
    ev = {"version": EVIDENCE_VERSION, "unit_ref": unit_ref, "condition_ref": condition_ref,
          "domain": "revision_history", "regime": "cold", "render": "log",
          "query": {"boundary_options": options, "change_types": ["proposal", "selection", "none"], "n_events": n}}
    if interface == "process":
        ev["history"] = {"interface": "process", "events": H.visible_history(h), "sections": ["sec1", "sec2", "sec3"]}
    else:
        ev["history"] = {"interface": "final_only", "final": final_text(h), "sections": ["sec1", "sec2", "sec3"]}
    return ev


def oracle_bundle(h: dict, interface: str) -> dict:
    return {"version": "OracleBundleV1", "hid": h["hid"], "kind": h["kind"], "interface": interface,
            "truth": h["truth"], "n": h["n"], "oracle_posterior": H.oracle_posterior(H.visible_history(h), MIN_SEG)}
