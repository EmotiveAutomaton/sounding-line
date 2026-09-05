"""The maker series (brief §5 MS): makers with four artifacts each under one law and residue,
with purposes varying across artifacts, beliefs drawn per artifact, and a per-artifact
reveal parameter (how much the maker's residue is expressed in that artifact: low scales the
habit to a third and drops the maintained intention; high leaves it whole) declared in the
oracle and never visible. The earlier artifacts enter the reader's context as whole logs in
the one grammar; the scored artifact is the last, cut as any world is.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (count the construction's identity space: a maker id seeds the law
  and residue once and every artifact draws its own document, purpose, and belief, so no
  two artifacts of a maker are twins; the reveal parameter must be able to move what it
  claims to move: the guard suite checks the low-reveal artifact's habit is scaled), §5.
gates: none here (A01 to A05 own the bands). bands: none.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runners.stage7.constructor import worlds as W                                 # noqa: E402
from runners.stage8.constructor.purpose import PURPOSES, make_pu_world             # noqa: E402
from runners.stage8.reader import logfmt as LF                                     # noqa: E402

REVEALS = ("low", "high")
REVEAL_SCALE = {"low": 0.3, "high": 1.0}


def maker_series(mid: str, domain: str, n_artifacts: int = 4, reveal_plan: list[str] | None = None,
                 shape: str = "essay") -> dict:
    """One maker: law, residue, tendency drawn once from the maker id; per artifact a
    purpose, a belief, a document, and a reveal level."""
    r = W._rng(mid, "maker")
    law = W.LAW_NAMES[r.randrange(len(W.LAW_NAMES))]
    residue = W.RESIDUES[1 + r.randrange(len(W.RESIDUES) - 1)]          # a maker with a residue to reveal
    tendency = W.TENDENCIES[r.randrange(2)]
    arts = []
    for k in range(n_artifacts):
        rk = W._rng(mid, f"art{k}")
        purpose = PURPOSES[rk.randrange(len(PURPOSES))]
        belief = W.BELIEFS[rk.randrange(len(W.BELIEFS))]
        reveal = (reveal_plan[k] if reveal_plan and k < len(reveal_plan) else REVEALS[rk.randrange(2)])
        lid = f"{mid}|art{k}"
        last = k == n_artifacts - 1
        w = make_pu_world(lid, domain, purpose=purpose, shape=shape, law_name=law, belief=belief, residue=residue,
                          tendency=tendency, residue_scale=REVEAL_SCALE[reveal], finish=last, salt=f"art{k}")
        w["reveal"] = reveal
        w["maker"] = mid
        w["artifact_index"] = k
        arts.append(w)
    return {"maker": mid, "law": law, "residue": residue, "tendency": tendency, "artifacts": arts,
            "reveal": [a["reveal"] for a in arts]}


def artifact_log(world: dict, with_goal: bool = False) -> str:
    """A whole earlier artifact as a log in the one grammar (its purpose withheld unless asked)."""
    c = world["state"]["external_context"]
    head = LF.header(world["doc"]["topic"], c["audience"], c["tools"], c["deadline"], world["doc"]["sections"],
                     goal=world["purpose"] if with_goal else None)
    steps = [{"i": s["i"], "type": s["type"], "section": s["section"], "slot": s["slot"], "outcome": s["outcome"]} for s in world["trajectory"]["steps"]]
    stopped = world["trajectory"].get("stop_kind") == "hazard"
    return LF.render_log(head, steps, stopped)


def earlier_demonstrations(series: dict, n: int) -> list[dict]:
    """The first n artifacts as evidence demonstrations (whole logs, purposes withheld)."""
    out = []
    for k in range(min(n, len(series["artifacts"]) - 1)):
        w = series["artifacts"][k]
        out.append({"episode_ref": f"earlier-{k + 1}", "topic": w["doc"]["topic"],
                    "sections": [s["name"] for s in w["doc"]["sections"]],
                    "events": [{"step": s["i"], "type": s["type"], "section": s["section"], "slot": s["slot"], "outcome": s["outcome"]} for s in w["trajectory"]["steps"]],
                    "text": artifact_log(w)})
    return out


def _selftest() -> list[str]:
    fails = []
    s = maker_series("S8M|essay|s0|m00001|pilot", "essay", reveal_plan=["low", "high", "low", "high"])
    if len(s["artifacts"]) != 4:
        fails.append("series has not four artifacts")
    low = s["artifacts"][0]["state"]["history_residue"].get("habit") or {}
    high = s["artifacts"][1]["state"]["history_residue"].get("habit") or {}
    if s["residue"] in ("habit_check", "habit_write") and not all(low[k] < high[k] for k in high):
        fails.append("the low reveal did not scale the habit")
    if s["artifacts"][-1]["degenerate"] is None and not s["artifacts"][-1].get("hidden"):
        fails.append("the scored artifact has no hidden targets")
    txt = artifact_log(s["artifacts"][0])
    if "goal:" in txt:
        fails.append("the earlier log leaks its purpose")
    return fails
