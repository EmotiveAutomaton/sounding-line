"""The Stage 8 capsule entry point (brief §11): the Stage 7 worker's contract (one evidence
file, one task file, one PredictionV1, no world object, no oracle, the audit hook of the
bootstrap) with the Stage 8 arms: the Stage 7 baselines and solver (U, PERS, DOM, SOL), the
untrained direct reader DIR0 (the Stage 7 DIR), the forward-model family (FM; FMP with a
supplied or proposed purpose; FMN with earlier artifacts; FMC with a true or false context;
FMS with supplied state lines; FMB, the base weights through the same generative readout),
the proposal and recall readouts (PUR, PULL, LAWR, RESR), and the generation gate (GEN).
STDLIB ONLY.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §5 (a clean exit that wrote no produce is a failure: an arm that
  cannot realize writes an explicit unrealized prediction, never nothing; every error to
  out/error.json), §3 (the capsule never scores; unasked targets are filled uniform and
  marked, never silently).
gates: none here. bands: none.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback

from . import baselines as B
from . import forward_model as FM
from . import supplied_state as S
from .client8 import Client8
from .contracts import canonical_prediction, evidence_problems, prediction
from .worker7 import _complete, _read, _write, content_sha, probe_forbidden       # the Stage 7 worker, copied beside as worker7.py

FM_ARMS = ("FM", "FMP", "FMN", "FMC", "FMS", "FMB", "FMPT")


def run_task(ev: dict, task: dict) -> dict:
    arm = task["arm"]
    sha = content_sha(ev)
    client = Client8(model=task.get("model", ""))
    t0 = time.time()
    fallback = B.uniform(ev)
    core: dict | None = None
    notes: dict = {}
    eq: list = []
    abstain = False
    conf = 0.5
    targets_extra: dict = {}
    if arm == "U":
        core = fallback
    elif arm == "PERS":
        core = B.persistence(ev)
    elif arm == "DOM":
        core = B.dom(ev)
        if core is None:
            notes["unrealized"] = "no frozen DOM parameters in the capsule"
    elif arm == "SOL":
        core = B.solver(ev)
        if core is None:
            notes["unrealized"] = "the supplied state is incomplete or not executable"
    elif arm == "DIR0":
        core = S.direct(ev, client, sha, tuple(task["targets"]) if task.get("targets") else ("next_action", "stop", "changed_context"))
        conf = max(core["next_action"].values()) if core.get("next_action") else 0.5
    elif arm in FM_ARMS:
        t = dict(task)
        if arm == "FMB":
            t["adapter"] = False
        if arm == "FMN":
            t["earlier"] = True
        if arm == "FMPT":
            t["goal_line"] = t.get("goal_line_true") or t.get("goal_line")
        if arm == "FMP" and t.get("propose"):
            pd = FM.purpose_distribution(ev, client, sha, t["purpose_candidates"], weights=t.get("proposal_weights", "adapted"))
            notes["proposal"] = pd
            top = max(pd["purpose"], key=pd["purpose"].get) if pd["purpose"] else None
            t["goal_line"] = top
            eq, abstain, conf = pd["equivalence_class"], pd["abstain"], pd["confidence"]
            targets_extra["purpose"] = pd["purpose"]
        core = FM.predict(ev, client, t)
        notes.update(core.pop("notes", {}))
        if core.get("next_action"):
            conf = max(core["next_action"].values())
    elif arm == "PUR":
        pd = FM.purpose_distribution(ev, client, sha, task["purpose_candidates"], weights=task.get("proposal_weights", "adapted"))
        notes["proposal"] = pd
        eq, abstain, conf = pd["equivalence_class"], pd["abstain"], pd["confidence"]
        targets_extra["purpose"] = pd["purpose"]
        core = None
    elif arm in ("PULL", "LAWR", "RESR"):
        cands = task.get("candidates") if arm != "RESR" else (task.get("candidates_resr") or task.get("candidates"))
        rd = FM.recall_distribution(ev, client, sha, task["question"], cands, arm.lower(), weights=task.get("proposal_weights", "adapted"))
        notes["recall"] = rd
        targets_extra[arm.lower()] = rd["dist"]
        conf = rd["confidence"]
        core = None
    elif arm == "GEN":
        g = FM.generate_log(ev, client, task)
        notes["generated"] = g
        core = None
    else:
        raise ValueError(f"unknown arm {arm}")
    targets = _complete(ev, core, fallback)
    if core is None and arm in ("PUR", "PULL", "LAWR", "RESR", "GEN"):
        notes["fill"] = "the process targets are uniform fills; this arm answers its own target"
    targets.update(targets_extra)
    if core and core.get("subjective_ids") is not None:
        notes["subjective_ids"] = core["subjective_ids"]
    budget = dict(client.budget)
    budget["wall_s"] = round(time.time() - t0, 3)
    return prediction(ev, targets, equivalence_class=eq, abstain=abstain or bool(notes.get("unrealized")),
                      confidence=conf, arm=arm, notes=notes, compute=budget)


def main() -> int:
    try:
        task = _read("task.json")
        if task.get("probe"):
            _write("receipt.json", probe_forbidden(task))
            return 0
        ev = _read("evidence.json")
        probs = evidence_problems(ev)
        if probs:
            _write("error.json", {"evidence_problems": probs})
            return 2
        pred = run_task(ev, task)
        pred["canonical_sha"] = __import__("hashlib").sha256(canonical_prediction(pred)).hexdigest()[:16]
        _write("prediction.json", pred)
        return 0
    except Exception as e:                                                        # noqa: BLE001
        _write("error.json", {"error": repr(e), "trace": traceback.format_exc()[-3000:]})
        return 1


if __name__ == "__main__":
    sys.exit(main())
