"""Stage 6 prospective scoring (brief §7, §14.1): one arm's adapted predictions against
one world's hidden targets, the cheap comparators beside it, and the aggregation helpers
the engines share. Held-out log score is the primary; Brier, calibration, risk-coverage,
hazard, span, and oracle-gap closure ride along. No card passes on retrospective label
accuracy (the posterior over the latent grid is reported as a description, never as the
primary).

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (blind floors follow the truth's label marginal: every score is
  reported beside its world's own cheap comparator, computed from the visible prefix
  only; magnitude and signed forms dissociate: log score and accuracy both written;
  every statistic a verdict rests on is written to the output file), §5 (aggregation
  clusters at the world; row duplication cannot move a unit-level mean).
gates: none here; the engines own the bands.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage6 import worlds as W                                             # noqa: E402
from soundingline.stage6 import brier                                              # noqa: E402

FLOOR = 1e-9


def _ls(dist: dict, truth: str) -> float | None:
    if not dist or truth is None:
        return None
    return math.log(max(float(dist.get(truth, 0.0)), FLOOR))


def score_predictions(world: dict, pred: dict) -> dict:
    """Every prospective endpoint of one prediction record against the world's hidden
    targets: next-edit type/section (log + Brier), the exact next action when predicted,
    the stop decision at the next opportunity (Bernoulli log score; None when the world
    offers no future opportunity), and the changed-context choice."""
    hid = world["hidden"]
    out = {}
    out["next_edit_type_ls"] = _ls(pred.get("next_edit_type"), hid["next_edit_type"])
    out["next_edit_type_brier"] = brier(pred.get("next_edit_type") or {}, hid["next_edit_type"]) if hid["next_edit_type"] else None
    out["next_edit_type_correct"] = (max(pred["next_edit_type"], key=pred["next_edit_type"].get) == hid["next_edit_type"]) if pred.get("next_edit_type") and hid["next_edit_type"] else None
    out["next_section_ls"] = _ls(pred.get("next_section"), hid["next_section"])
    nxt = hid.get("next_edit")
    out["next_action_ls"] = _ls(pred.get("next_edit"), f"{nxt['type']}:{nxt['section']}:{nxt['slot']}") if nxt and pred.get("next_edit") else None
    if hid["n_future_stop_opportunities"] > 0 and pred.get("p_stop") is not None:
        p = min(max(float(pred["p_stop"]), FLOOR), 1 - FLOOR)
        out["stop_ls"] = math.log(p if hid["stops_at_next_opportunity"] else 1 - p)
        out["stop_truth"] = hid["stops_at_next_opportunity"]
        out["stop_conf"] = p if hid["stops_at_next_opportunity"] else 1 - p
    else:
        out["stop_ls"] = None
    cc = hid["changed_context"]["choice"]
    out["changed_context_ls"] = _ls(pred.get("changed_context"), cc)
    out["changed_context_correct"] = (max(pred["changed_context"], key=pred["changed_context"].get) == cc) if pred.get("changed_context") else None
    out["abstained"] = bool(pred.get("abstain"))
    out["confidence"] = max((pred.get("next_edit_type") or {"x": 0.0}).values())
    # the description, never the primary: posterior mass on the true latent's tag
    post = pred.get("posterior") or {}
    truth_tag = (world["truth"].get("controller")
                 or (f"value:{world['truth']['value']}" if "value" in world["truth"] else None)
                 or (f"forage:{world['truth']['forage']}" if "forage" in world["truth"] else None))
    if truth_tag is None and "history_law" in world["truth"]:
        truth_tag = next((t for t in post if t.startswith(f"hist:{world['truth']['history_law']}")), None)
    out["posterior_on_truth"] = float(post.get(truth_tag, 0.0)) if truth_tag else None
    return out


def score_baselines(world: dict) -> dict:
    """The declared cheap comparators on the same targets (prefix-only; §5.1)."""
    base = W.cheap_baselines(world)
    return score_predictions(world, {"next_edit_type": base["next_edit_type"],
                                     "next_section": base["next_section"],
                                     "next_edit": {}, "changed_context": base["changed_context"],
                                     "p_stop": base["p_stop"], "posterior": {}, "abstain": False})


def score_oracle(world: dict) -> dict:
    from runners.stage6.architectures import run_arm                               # noqa: PLC0415
    return score_predictions(world, run_arm("OR", None, None, world)["predictions"])


PRIMARY_ENDPOINTS = ("next_edit_type_ls", "next_section_ls", "stop_ls", "changed_context_ls")


def combined_primary(scores: dict) -> float | None:
    """The card-level primary when one number is needed: the mean of the defined
    endpoint log scores (type, section, stop, changed context), each present or absent
    identically across the arms being contrasted (the engines assert this)."""
    vals = [scores[k] for k in PRIMARY_ENDPOINTS if scores.get(k) is not None]
    return (sum(vals) / len(vals)) if vals else None


def unit_diffs(rows_a: list[dict], rows_b: list[dict], key: str = "primary_score") -> dict:
    """Per-unit paired differences for arms a minus b, keyed on unit_id."""
    ma: dict = {}
    mb: dict = {}
    for r in rows_a:
        ma.setdefault(r["unit_id"], []).append(r[key])
    for r in rows_b:
        mb.setdefault(r["unit_id"], []).append(r[key])
    out = {}
    for u in ma:
        if u in mb:
            va = [x for x in ma[u] if x is not None]
            vb = [x for x in mb[u] if x is not None]
            if va and vb:
                out[u] = sum(va) / len(va) - sum(vb) / len(vb)
    return out


def _selftest() -> list[str]:
    fails = []
    w = W.make_process_world("P01|essay|s0|w0004|discovery", "essay", track="C")
    so = score_oracle(w)
    sb = score_baselines(w)
    if so["next_edit_type_ls"] is None or sb["next_edit_type_ls"] is None:
        fails.append("scores undefined")
    if combined_primary(so) is None:
        fails.append("combined primary undefined")
    # over a handful of worlds the oracle beats the cheap baseline on the combined primary
    diffs = []
    for i in range(10):
        wi = W.make_process_world(f"P01|essay|s0|w{i:04d}|discovery", "essay", track="C")
        a, b = combined_primary(score_oracle(wi)), combined_primary(score_baselines(wi))
        if a is not None and b is not None:
            diffs.append(a - b)
    if not diffs or sum(diffs) / len(diffs) <= 0.0:
        fails.append(f"oracle does not beat cheap baselines on average: {sum(diffs) / max(1, len(diffs)):.3f}")
    return fails


if __name__ == "__main__":
    f = _selftest()
    print("prediction self-tests:", "ALL OK" if not f else f)
    sys.exit(1 if f else 0)
