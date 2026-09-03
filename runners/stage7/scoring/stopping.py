"""Stopping scores (brief §16.1): the discrete-time hazard with censoring over a sequence
of boundaries, the matched progress/length baselines K15 and P05 compare against, and
the boundary-type posterior score with equivalence abstention (P06).

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (match length and section-position stopping base rates across
  factor levels before reading a stopping gain; the stop law must be able to vary with
  the maker state: the constructor asserts the oracle's hazard gap), §5.
gates: none here. bands: none.
"""

from __future__ import annotations

import math

FLOOR = 1e-9


def hazard_sequence_ls(p_stop_seq: list[float], stop_flags: list[bool]) -> float:
    """Summed log likelihood of the observed continue/stop sequence; censored when the
    maker continued past the last scored boundary."""
    total = 0.0
    for p, stopped in zip(p_stop_seq, stop_flags):
        p = min(max(float(p), FLOOR), 1 - FLOOR)
        if stopped:
            return total + math.log(p)
        total += math.log(1 - p)
    return total


def progress_baseline(prefix_len: int, n_initial: int, done: int, table: dict | None = None) -> float:
    """A matched progress/length hazard: the frozen DOM stop table by progress bucket and
    over-length flag; a flat 0.15 without one."""
    if not table:
        return 0.15
    progress = done / max(1, n_initial)
    b = "early" if progress < 0.34 else ("mid" if progress < 0.67 else "late")
    over = "over" if prefix_len > float(table.get("mean_len", 12.0)) else "under"
    return float(table.get("stop", {}).get(f"{b}|{over}", table.get("stop", {}).get("all", 0.15)))


def boundary_type_ls(dist: dict, truth: str, equivalent_ok: bool = True) -> float | None:
    """The boundary-type posterior score; when the truth is 'equivalent' (two terms tied)
    the abstention option carries the credit."""
    if truth in (None, "none"):
        return None
    return math.log(max(float(dist.get(truth, 0.0)), FLOOR))
