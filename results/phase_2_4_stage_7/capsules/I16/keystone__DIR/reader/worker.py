"""The capsule entry point (brief §6.2): reads ONE visible-evidence file and ONE task file
from the capsule directory, runs the requested arm, and writes ONE PredictionV1 to the
write-only output location. It has no world object, no oracle, no repository on its path,
and the audit hook installed by the bootstrap (runtime.py writes it) raises on any access
outside the capsule and the loopback endpoint. STDLIB ONLY.

Task keys: arm (U, PERS, DOM, SOL, DIR, KL, SLJ, or a local external name), model (the
endpoint's model id), withheld (factor names the joint arms must propose), seed, targets
(optional subset), probe (the X04 access-attempt mode; writes out/receipt.json instead).

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §5 (a clean exit that wrote no produce is a failure: an arm that
  cannot realize writes an explicit unrealized prediction, never nothing; every error is
  written to out/error.json so the scorer sees the cause), §3 (the capsule never scores:
  the scorer receives PredictionV1 only after this process exits).
gates: none here. bands: none.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback

from . import baselines as B
from . import extra_arms as X
from . import history_reader as HR
from . import joint_reader as J
from . import records_reader as RR
from . import supplied_state as S
from .client import Client
from .contracts import canonical_prediction, evidence_problems, evidence_sha, prediction  # noqa: F401

LOCAL_EXTERNAL = ("weighted_language_hypotheses", "sequential_hypothesis_particles", "adaptive_factor_expansion",
                  "synthesized_agent_model", "known_law_inverse_planning", "epistemic_translation")


def content_sha(ev: dict) -> str:
    """The evidence hash WITHOUT the opaque identifiers and with the option listings in a
    canonical (sorted) order: the seed of every option order and grouping, so relabeling a
    unit or condition (I09) or permuting the option lists (X06) cannot move a readout."""
    ev2 = {k: v for k, v in ev.items() if k not in ("unit_ref", "condition_ref")}
    q = ev2.get("query")
    if isinstance(q, dict) and isinstance(q.get("next_action_options"), list):
        ev2["query"] = dict(q, next_action_options=sorted(q["next_action_options"]))
    oo = ev2.get("objective_options")
    if isinstance(oo, dict):
        ev2["objective_options"] = {k: (sorted(v, key=lambda a: json.dumps(a, sort_keys=True)) if isinstance(v, list) else v)
                                    for k, v in oo.items()}
    elif isinstance(oo, list):
        ev2["objective_options"] = sorted(oo, key=lambda a: json.dumps(a, sort_keys=True))
    return evidence_sha(ev2)


def _read(name: str):
    with open(os.path.join(os.getcwd(), name), encoding="utf-8") as fh:
        return json.load(fh)


def _write(name: str, obj) -> None:
    out_dir = os.path.join(os.getcwd(), "out")
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, sort_keys=True, indent=1)
    os.replace(tmp, os.path.join(out_dir, name))


def _complete(ev: dict, core: dict | None, fallback: dict) -> dict:
    """Every target the query names gets a distribution: the arm's where it has one, the
    fallback's (uniform) otherwise, so partial arms are scored on what they answered and
    on chance where they did not, never silently."""
    q = ev["query"]
    out = {}
    src = core or {}
    ids = q["next_action_options"]
    out["next_action"] = src.get("next_action") or fallback["next_action"]
    out["next_type"] = src.get("next_type") or fallback["next_type"]
    out["next_section"] = src.get("next_section") or fallback["next_section"]
    out["stop"] = src.get("p_stop") if src.get("p_stop") is not None else fallback["p_stop"]
    out["changed_context"] = src.get("changed_context") or fallback.get("changed_context") or {k: 1.0 / len(ids) for k in ids}
    out["invalidation"] = src.get("invalidation") or fallback.get("invalidation") or {k: 1 / 3 for k in q["invalidation_responses"]}
    out["boundary_type"] = src.get("boundary_type") or fallback.get("boundary_type") or {k: 0.25 for k in q["boundary_types"]}
    return out


HISTORY_ARMS = ("HU", "HSTYLE", "HPERS", "HSTACK", "HPROC", "HDIR")
COAUTHOR_ARMS = ("CU", "CPOS", "CPRIOR", "CDIR")
SCHOLA_ARMS = ("SU", "SPERS", "SDIR")


def run_record_task(ev: dict, task: dict) -> dict:
    """History, CoAuthor, and ScholaWrite arms: their own target vocabularies."""
    arm = task["arm"]
    sha = content_sha(ev)
    client = Client(model=task.get("model", ""))
    t0 = time.time()
    iface = (ev.get("history") or {}).get("interface")
    if arm in HISTORY_ARMS:
        r = HR.run(ev, arm, client, sha, task)
        targets = {"change_point": r["boundary"], "change_type": r["type"]}
        conf = max(r["boundary"].values())
        best = max(r["boundary"], key=r["boundary"].get)
        eq = [best]
    elif arm in COAUTHOR_ARMS:
        r = RR.coauthor(ev, arm, client, sha, task)
        targets = {"decision": r["decision"]}
        conf = max(r["decision"].values())
        eq = []
    elif arm in SCHOLA_ARMS:
        r = RR.scholawrite(ev, arm, client, sha, task)
        targets = {"next_category": r["next_category"]}
        conf = max(r["next_category"].values())
        eq = []
    else:
        raise ValueError(arm)
    budget = dict(client.budget)
    budget["wall_s"] = round(time.time() - t0, 3)
    return prediction(ev, targets, equivalence_class=eq, abstain=False, confidence=conf, arm=arm,
                      notes={"interface": iface}, compute=budget)


def run_task(ev: dict, task: dict) -> dict:
    arm = task["arm"]
    if arm in HISTORY_ARMS + COAUTHOR_ARMS + SCHOLA_ARMS:
        return run_record_task(ev, task)
    sha = content_sha(ev)
    client = Client(model=task.get("model", ""))
    t0 = time.time()
    fallback = B.uniform(ev)
    core: dict | None = None
    notes: dict = {}
    eq: list = []
    abstain = False
    conf = 0.5
    withheld = list(task.get("withheld") or [])
    seed = int(task.get("seed", 0))
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
    elif arm == "DIR":
        core = S.direct(ev, client, sha, tuple(task["targets"]) if task.get("targets") else None)
        conf = max(core["next_action"].values()) if core.get("next_action") else 0.5
    elif arm == "DIRS":
        core = X.direct_structured(ev, client, sha, tuple(task["targets"]) if task.get("targets") else None)
        conf = max(core["next_action"].values()) if core.get("next_action") else 0.5
    elif arm == "GBLIND":
        core = X.goal_blind(ev, client)
        if core is None:
            notes["unrealized"] = "the goal-blind mixture needs the other factors executable"
    elif arm in ("POINT", "MIX", "AGG", "ORDERED", "DATED"):
        view = {"POINT": "point", "MIX": "dated", "AGG": "aggregate", "ORDERED": "ordered", "DATED": "dated"}[arm]
        core = X.dated(ev, client, view)
        if core is None:
            notes["unrealized"] = "no demonstrations or the other factors are not executable"
        else:
            notes["fitted_law"] = core.get("fitted_law")
            notes["mixture"] = core.get("mixture")
    elif arm == "KL":
        core = S.known_law_select(ev, client)
        if core is None:
            notes["unrealized"] = "no candidate laws or the other factors are not executable"
        else:
            eq, abstain, conf = core["equivalence_class"], core["abstain"], core["confidence"]
            notes["posterior"] = core["posterior"]
    elif arm == "SLJ":
        res = J.sounding_joint(ev, client, sha, withheld, seed)
        notes["proposals"] = res.get("proposals")
        if res.get("unrealized"):
            notes["unrealized"] = "no solvable proposal set"
        else:
            core = res
            eq, abstain, conf = res["equivalence_class"], res["abstain"], res["confidence"]
            notes["posterior"] = res["posterior"]
            notes["factor_marginals"] = res["factor_marginals"]
            notes["band"] = res["band"]
            notes["candidate_preds"] = res.get("candidate_preds")
    elif arm == "LEARN":
        fit = J.fit_law_from_demos(ev, client)
        if fit is None:
            notes["unrealized"] = "no demonstrations"
        else:
            ev2 = dict(ev)
            sf = dict((ev.get("supplied_factors") or {}))
            factors = dict(sf.get("factors") or {})
            factors["expertise_law"] = fit["law"]
            ev2["supplied_factors"] = {"form": "executable", "factors": factors}
            core = B.solver(ev2)
            notes["fitted_law"] = fit["law"]
            notes["demo_ll"] = fit["demo_ll"]
            if core is None:
                notes["unrealized"] = "the fitted law with the supplied factors is not executable"
    elif arm == "weighted_language_hypotheses":
        res = J.weighted_language_hypotheses(ev, client, sha, seed)
        notes["proposals"] = res.get("proposals")
        core = None if res.get("unrealized") else res
        if core:
            eq, conf = res["equivalence_class"], res["confidence"]
            notes["posterior"] = res["posterior"]
    elif arm == "sequential_hypothesis_particles":
        res = J.sequential_hypothesis_particles(ev, client, sha, withheld, seed)
        notes["receipt"] = res.get("receipt")
        core = None if res.get("unrealized") else res
        if core:
            eq, abstain, conf = res["equivalence_class"], res["abstain"], res["confidence"]
    elif arm == "adaptive_factor_expansion":
        res = J.adaptive_factor_expansion(ev, client, sha, withheld, seed)
        notes["receipt"] = res.get("receipt")
        notes["proposals"] = res.get("proposals")
        core = None if res.get("unrealized") else res
        if core:
            eq, abstain, conf = res["equivalence_class"], res["abstain"], res["confidence"]
            notes["posterior"] = res.get("posterior")
    elif arm == "synthesized_agent_model":
        res = J.synthesized_agent_model(ev, client, sha, seed)
        notes["receipt"] = res.get("receipt")
        core = None if res.get("unrealized") else res
        if core:
            conf = res["confidence"]
    elif arm == "known_law_inverse_planning":
        core = S.known_law_select(ev, client)
        if core is None:
            notes["unrealized"] = "no candidate laws"
        else:
            eq, abstain, conf = core["equivalence_class"], core["abstain"], core["confidence"]
            notes["posterior"] = core["posterior"]
    elif arm == "epistemic_translation":
        res = J.epistemic_translation(ev, client, sha, seed)
        notes["receipt"] = res.get("receipt")
        core = None if res.get("unrealized") else res
        if core:
            conf = res["confidence"]
    else:
        raise ValueError(f"unknown arm {arm}")
    targets = _complete(ev, core, fallback)
    if core and core.get("subjective_ids") is not None:
        notes["subjective_ids"] = core["subjective_ids"]
    budget = dict(client.budget)
    budget["wall_s"] = round(time.time() - t0, 3)
    return prediction(ev, targets, equivalence_class=eq, abstain=abstain or bool(notes.get("unrealized")),
                      confidence=conf, arm=arm, notes=notes, compute=budget)


def probe_forbidden(task: dict) -> dict:
    """X04 / I04: attempt every forbidden access from inside the real reader process and
    record whether each raised. A probe that SUCCEEDS is the defect."""
    attempts = {}

    def attempt(name, fn):
        try:
            fn()
            attempts[name] = {"raised": False}
        except BaseException as e:                                               # noqa: BLE001
            attempts[name] = {"raised": True, "error": type(e).__name__}

    for p in task.get("forbidden_paths", []):
        attempt(f"open:{p}", lambda p=p: open(p, encoding="utf-8").read(64))
        attempt(f"listdir:{p}", lambda p=p: os.listdir(p if os.path.isdir(p) else os.path.dirname(p)))
    for mod in task.get("forbidden_modules", ["runners", "soundingline", "constructor", "scoring", "oracle", "torch", "numpy"]):
        attempt(f"import:{mod}", lambda mod=mod: __import__(mod))
    attempt("socket:other_port", lambda: __import__("socket").create_connection(("127.0.0.1", int(task.get("other_port", 9)) ), timeout=2))
    attempt("socket:external", lambda: __import__("socket").create_connection(("93.184.216.34", 80), timeout=2))
    attempt("subprocess", lambda: __import__("subprocess").run(["cmd", "/c", "echo x"], capture_output=True))
    attempt("os.system", lambda: os.system("echo x"))
    attempt("ctypes", lambda: __import__("ctypes").CDLL("kernel32"))
    attempt("env:oracle", lambda: (_ for _ in ()).throw(KeyError("S7_ORACLE")) if "S7_ORACLE" not in os.environ else None)
    attempt("write:outside", lambda: open(os.path.join(os.getcwd(), "..", "escaped.txt"), "w").write("x"))
    attempt("walk_up", lambda: os.listdir(os.path.join(os.getcwd(), "..", "..")))
    ok = all(v["raised"] for v in attempts.values())
    return {"all_raised": ok, "attempts": attempts, "cwd": os.getcwd(), "sys_path": list(sys.path),
            "env_keys": sorted(os.environ)}


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
