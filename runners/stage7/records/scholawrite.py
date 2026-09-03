"""ScholaWrite (brief §7.4, D09, P14): keystroke-level revision records with project and
author columns, kept under leave-project-out AND leave-author-out grouping, against the
strong previous-label baseline. The useful target is a SWITCH the persistence baseline
cannot win by default: whether the high-level revision category changes at the next
event (the moment) and to which category (the direction), scored only on switch-eligible
positions with persistence's own base rate written beside every score.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §2 (read the format from the data; unparseable rows ledgered), §3
  (a paired contrast on the estimand's own per-item quantity; the previous-label baseline
  is the frozen rival, and the switch-conditioned score is the estimand so persistence
  cannot win by construction; blind floors follow the truth marginal: the switch rate is
  printed), §5 (the independent unit is the project lineage; both protocols keep every
  descendant on one side).
gates: none here; the P engine states the band. bands: none.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

SCHOLA_DIR = REPO / "results" / "scholawrite" / "dataset"
CATEGORIES = ("Planning", "Implementation", "Revision")


def _split_hash(key: str, salt: str = "s7split") -> float:
    return int(hashlib.md5(f"{salt}|{key}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def lane_of(key: str, salt: str = "s7split") -> str:
    h = _split_hash(key, salt)
    return "discovery" if h < 0.50 else ("transfer" if h < 0.65 else ("confirmation" if h < 0.90 else "attack"))


def _category(high: str, label: str) -> str:
    h = (high or "").strip().lower()
    for c in CATEGORIES:
        if c.lower() in h:
            return c
    low = (label or "").lower()
    if "plan" in low or "idea" in low or "outline" in low:
        return "Planning"
    if "revis" in low or "edit" in low or "fix" in low or "clarity" in low or "coherence" in low:
        return "Revision"
    return "Implementation"


def sessions(max_sessions: int | None = None, protocol: str = "leave_project_out", lane: str | None = None,
             min_events: int = 8) -> list[dict]:
    """One session = one (project, author) pair's rows in time order, segmented at gaps over
    30 minutes. The split key follows the protocol: the project (leave-project-out) or the
    author (leave-author-out); both keep every descendant on one side."""
    from datasets import load_from_disk                                           # noqa: PLC0415
    ds = load_from_disk(str(SCHOLA_DIR))["all_sorted"]
    by_pa: dict = {}
    for r in ds:
        by_pa.setdefault((str(r["project"]), str(r["author"])), []).append(
            {"t": int(r["timestamp"]), "label": r["label"], "high": r["high-level"],
             "before": r["before text"] or "", "after": r["after text"] or ""})
    out = []
    for (proj, auth), rows in sorted(by_pa.items()):
        rows.sort(key=lambda x: x["t"])
        seg: list = []
        segs = [seg]
        for r in rows:
            if seg and r["t"] - seg[-1]["t"] > 30 * 60 * 1000:
                seg = []
                segs.append(seg)
            seg.append(r)
        for k, s in enumerate(segs):
            if len(s) < min_events:
                continue
            key = f"sw|{proj}" if protocol == "leave_project_out" else f"sw|author|{auth}"
            evs = [{"i": i, "category": _category(r["high"], r["label"]), "label": r["label"],
                    "len_delta": len(r["after"]) - len(r["before"]),
                    "view": event_view(r)} for i, r in enumerate(s)]
            switches = [i for i in range(1, len(evs)) if evs[i]["category"] != evs[i - 1]["category"]]
            out.append({"corpus": "scholawrite", "session_id": f"sw|{proj}|{auth}|{k}", "unit_key": key,
                        "project": proj, "author": auth, "protocol": protocol, "lane": lane_of(key),
                        "n_events": len(evs), "events": evs, "switch_positions": switches,
                        "switch_rate": len(switches) / max(1, len(evs) - 1)})
    if lane:
        out = [s for s in out if s["lane"] == lane]
    out.sort(key=lambda s: s["session_id"])
    return out[:max_sessions] if max_sessions else out


def event_view(r: dict, max_chars: int = 240) -> dict:
    """What a reader may see of one event: the local neighborhood and the delta, NEVER the
    label or category."""
    b, a = r["before"], r["after"]
    i = next((j for j, (x, y) in enumerate(zip(b, a)) if x != y), min(len(b), len(a)))
    lo = max(0, i - max_chars // 2)
    return {"before": b[lo:lo + max_chars], "after": a[lo:lo + max_chars], "len_delta": len(a) - len(b)}


def switch_items(session: dict, context: int = 4) -> list[dict]:
    """P14 items: every position with at least `context` prior events; the target is the
    next event's category and whether it differs from the current one."""
    evs = session["events"]
    items = []
    for i in range(context, len(evs) - 1):
        items.append({"pos": i, "context": [dict(e["view"], category=e["category"]) for e in evs[i - context:i + 1]],
                      "current": evs[i]["category"], "next": evs[i + 1]["category"],
                      "switch": evs[i + 1]["category"] != evs[i]["category"]})
    return items
