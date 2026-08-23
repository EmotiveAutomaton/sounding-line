"""Stage-2 Tree-H Wave 2 (discovery lane): the CoAuthor action tree. Scouts E24-H02b
(event ontology extraction) and E24-H03 (prospective accept-versus-dismiss baselines).

The target is objective behavior only (Stage-2 brief section 9): at each moment a
suggestion is shown, predict whether the writer takes it or dismisses it. Token share is
never a target; acceptance is never read as agreement.

Event ontology from the raw logs: suggestion-open marks a shown suggestion; the writer's
next suggestion-terminal action decides the outcome (suggestion-select = TAKEN,
suggestion-close = DISMISSED); reopens without a select in between stay part of the same
decision episode.

DESIGN CHECK (2026-08-23, discovery lane). Lessons read at build time: section 3 (floors
follow the truth's marginal, so the headline is the margin over the majority rate, and the
majority baseline is computed on the same split; fixed label set in every averaged score;
denominators are declared opportunities, here shown-suggestion episodes), section 5
(produces guards; this is a CPU parse, no lock). Failure directions: a session whose events
cannot be paired open-to-terminal is counted and skipped, never silently dropped; if
skipped sessions exceed 10 percent the extraction is INSTRUMENT-FAILED. Split is by
SESSION (writer metadata is not in the event logs; the session-as-writer approximation is
recorded as a limitation in the output, not hidden).

Baselines, all mechanical: global majority; per-session rate (fitted on that session's
first half, applied to its second half, so nothing crosses the prediction boundary);
previous-outcome repetition; session-position (early versus late half rate). A model
reader is NOT run here; after the prospective-reader boundary (L161) any model arm on this
tree needs its own validated instrument first.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "results" / "scouts"
SRC = REPO / "corpora" / "coauthor" / "coauthor-v1.0"

TERMINAL = {"suggestion-select": "taken", "suggestion-close": "dismissed"}


def session_episodes(path: Path):
    """Yield (outcome, position_frac, prev_outcome) per decision episode in one session."""
    try:
        events = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    except Exception:                                                            # noqa: BLE001
        return None
    episodes = []
    open_pending = False
    prev = None
    for ev in events:
        name = ev.get("eventName")
        if name == "suggestion-open":
            open_pending = True
        elif name in TERMINAL and open_pending:
            episodes.append((TERMINAL[name], prev))
            prev = TERMINAL[name]
            open_pending = False
    n = len(episodes)
    return [(out, i / max(1, n - 1) if n > 1 else 0.0, pv)
            for i, (out, pv) in enumerate(episodes)]


def arm_events() -> int:
    sessions = sorted(SRC.glob("*.jsonl"))
    per, skipped = {}, 0
    for p in sessions:
        eps = session_episodes(p)
        if eps is None:
            skipped += 1
            continue
        if eps:
            per[p.stem] = eps
    total = sum(len(v) for v in per.values())
    outcomes = Counter(o for v in per.values() for o, _, _ in v)
    skip_frac = skipped / max(1, len(sessions))
    status = "INSTRUMENT-FAILED" if skip_frac > 0.10 else "PROMISING"
    print(f"{len(per)} sessions with episodes, {skipped} unreadable ({skip_frac:.3f}), "
          f"{total} decision episodes, outcomes {dict(outcomes)}")
    (OUT / "h_coauthor_events.json").write_text(json.dumps(
        {"scout": "E24-H02b", "status": status, "n_sessions": len(per),
         "n_skipped": skipped, "n_episodes": total, "outcomes": dict(outcomes),
         "limitation": "session approximates writer; writer metadata absent from logs",
         "per_session": {k: [[o, round(f, 4), pv] for o, f, pv in v]
                         for k, v in per.items()}}, indent=1),
        encoding="utf-8", newline="\n")
    return 0 if status == "PROMISING" else 1


def arm_baselines() -> int:
    data = json.loads((OUT / "h_coauthor_events.json").read_text(encoding="utf-8"))
    per = {k: [(o, f, pv) for o, f, pv in v] for k, v in data["per_session"].items()}
    episodes = [(s, o, f, pv) for s, v in per.items() for o, f, pv in v]
    n = len(episodes)
    majority = Counter(o for _, o, _, _ in episodes).most_common(1)[0][0]

    def acc(pred_fn) -> float:
        hits = valid = 0
        for s, o, f, pv in episodes:
            p = pred_fn(s, f, pv)
            if p is None:
                continue
            valid += 1
            hits += p == o
        return hits / valid if valid else 0.0, valid

    res = {}
    res["global_majority"] = acc(lambda s, f, pv: majority)
    # per-session rate: majority of the session's FIRST half predicts its second half
    first_half = {s: Counter(o for o, f, _ in v if f < 0.5) for s, v in per.items()}
    res["per_session_firsthalf"] = acc(
        lambda s, f, pv: (first_half[s].most_common(1)[0][0]
                          if f >= 0.5 and first_half[s] else None))
    res["previous_outcome"] = acc(lambda s, f, pv: pv)
    # session-position: global rate for early vs late half
    early = Counter(o for _, o, f, _ in episodes if f < 0.5).most_common(1)[0][0]
    late = Counter(o for _, o, f, _ in episodes if f >= 0.5).most_common(1)[0][0]
    res["session_position"] = acc(lambda s, f, pv: early if f < 0.5 else late)

    table = {k: {"accuracy": round(a, 4), "n_scored": v} for k, (a, v) in res.items()}
    base_rate = Counter(o for _, o, _, _ in episodes)[majority] / n
    print(f"{n} episodes; majority outcome {majority} at {base_rate:.3f}")
    for k, v in table.items():
        print(f"  {k}: {v}")
    best_margin = max(v["accuracy"] for k, v in table.items()
                      if k != "global_majority") - base_rate
    status = "PROMISING" if best_margin > 0.02 else "QUIET"
    (OUT / "h_coauthor_baselines.json").write_text(json.dumps(
        {"scout": "E24-H03", "status": status, "n_episodes": n,
         "majority_outcome": majority, "majority_rate": base_rate,
         "baselines": table, "best_margin_over_majority": best_margin,
         "note": "mechanical floors for any later reader; a model arm requires its own "
                 "validated instrument after the L161 prospective boundary"}, indent=1),
        encoding="utf-8", newline="\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["events", "baselines"])
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rc = {"events": arm_events, "baselines": arm_baselines}[a.arm]()
    print(f"{a.arm} in {(time.time() - t0) / 60:.0f} min")
    return rc


if __name__ == "__main__":
    sys.exit(main())
