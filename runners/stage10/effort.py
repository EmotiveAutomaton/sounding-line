"""R5 development-only benefit/cost controller and bounded route driver.

DESIGN CHECK: LESSONS sections 3-5; READER_HEURISTICS sections 4, 5, 10.
NULL: no measured improvement buys no extra work. ALTERNATIVE: consistent
development improvement may buy work even for confidently wrong first replies.
Unknown strata, one-group strata and nonpositive leave-one-group-out utility
stop at R0. This conservative rule is not a significance test. Invalid attempts
receive worst bounded loss and retain costs. Evaluation labels cannot enter fit.
All policies pay for the initial observation; no per-item outcome oracle exists.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from collections import defaultdict
from pathlib import Path

from .contracts import PublicTask, canonical, digest, parse_forecast
from .ollama import now, write_new
from .reader import from_record

VERSION = "stage10.effort.1"
CONFIG = {
    "initial_generated_tokens": 256,
    "additional_generated_tokens": 512,
    "maximum_generated_tokens": 768,
    "confidence_threshold": 0.8,
    "brier_loss_per_second": 0.001,
    "minimum_groups": 2,
    "fixed_route": "R1",
    "candidate_routes": ["R1", "R3"],
}
INVALID = {"INVALID", "MISMATCH", "EXECUTOR_INVALID"}
COST_KEYS = {"wall_seconds", "model_calls", "input_tokens", "output_tokens",
             "executor_evaluations", "reasoning_tokens", "reasoning_tokens_status"}


def source_identity():
    names = ("effort.py", "contracts.py", "ollama.py", "reader.py")
    return {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in names}


def check_cost(cost):
    if set(cost) != COST_KEYS:
        raise ValueError("cost fields must be complete, including unknown reasoning cost")
    for key in COST_KEYS - {"reasoning_tokens", "reasoning_tokens_status"}:
        value = cost[key]
        if type(value) not in {int, float} or not math.isfinite(value) or value < 0:
            raise ValueError("cost must be finite and nonnegative")
        if key != "wall_seconds" and type(value) is not int:
            raise ValueError("token and operation counts must be integers")
    if cost["reasoning_tokens"] is None:
        if cost["reasoning_tokens_status"] != "not separately exposed":
            raise ValueError("unknown reasoning cost needs its explicit status")
    elif type(cost["reasoning_tokens"]) is not int or cost["reasoning_tokens"] < 0 or cost["reasoning_tokens_status"] != "measured":
        raise ValueError("invalid reasoning cost")


def check_attempt(task, attempt, allowance):
    if set(attempt) != {"status", "forecast", "cost", "maximum_generated_tokens", "evidence_sha256"}:
        raise ValueError("unexpected or missing route fields")
    if attempt["maximum_generated_tokens"] != allowance or attempt["evidence_sha256"] != digest(task.public()):
        raise ValueError("route evidence or requested allowance changed")
    check_cost(attempt["cost"])
    if attempt["cost"]["output_tokens"] > allowance:
        raise ValueError("route exceeded output allowance")
    if attempt["status"] == "VALID":
        parse_forecast(canonical(attempt["forecast"]), task)
    elif attempt["status"] not in INVALID or attempt["forecast"] is not None:
        raise ValueError("invalid route must remain explicitly without a forecast")


def stratum(task, initial):
    check_attempt(task, initial, CONFIG["initial_generated_tokens"])
    confidence = (max(initial["forecast"]["probabilities"].values()) if initial["status"] == "VALID" else 0.)
    bucket = "invalid" if initial["status"] != "VALID" else ("high" if confidence >= CONFIG["confidence_threshold"] else "low")
    return canonical([task.family, task.evidence_view, len(task.choices), bucket]), confidence


def loss(task, attempt, truth):
    if truth not in {key for key, _ in task.choices}:
        raise ValueError("outcome outside the declared task support")
    if attempt["status"] != "VALID":
        return 1.0
    return .5 * sum((attempt["forecast"]["probabilities"][key] - float(key == truth)) ** 2 for key, _ in task.choices)


def fit(bundle):
    """Fit an inspectable table; caller must verify the original complete producers.

    Input is a private, source-bound development manifest, never an evaluator
    file discovered by this module. No loading or inference occurs here.
    """
    if set(bundle) != {"schema", "phase", "complete", "producers", "rows"} or bundle["schema"] != "stage10.effort-development.1":
        raise ValueError("undeclared development bundle")
    if bundle["phase"] != "development" or bundle["complete"] is not True or not bundle["rows"]:
        raise ValueError("only complete nonempty development may fit the selector")
    if not bundle["producers"] or any(not isinstance(k, str) or not isinstance(v, str) or len(v) != 64 or any(c not in "0123456789abcdef" for c in v) for k, v in bundle["producers"].items()):
        raise ValueError("original producer hashes required")
    table = defaultdict(lambda: defaultdict(list))
    task_ids, groups, public_hashes = set(), set(), set()
    for row in bundle["rows"]:
        if set(row) != {"task", "group", "truth", "routes"} or not isinstance(row["group"], str) or not row["group"]:
            raise ValueError("invalid development row")
        task = from_record(row["task"])
        if task.task_id in task_ids:
            raise ValueError("duplicate development task")
        task_ids.add(task.task_id); groups.add(row["group"]); public_hashes.add(digest(task.public()))
        routes = row["routes"]
        if set(routes) != {"R0", *CONFIG["candidate_routes"]}:
            raise ValueError("all declared route outcomes required; no survivor selection")
        for name, attempt in routes.items():
            check_attempt(task, attempt, CONFIG["initial_generated_tokens"] if name == "R0" else CONFIG["additional_generated_tokens"])
        key, _ = stratum(task, routes["R0"])
        base = loss(task, routes["R0"], row["truth"])
        for name in CONFIG["candidate_routes"]:
            gain = base - loss(task, routes[name], row["truth"])
            cost = routes[name]["cost"]["wall_seconds"]
            table[(key, name)][row["group"]].append((gain, cost))
    cells = []
    for (key, route), group_rows in sorted(table.items()):
        means = [(sum(v[0] for v in rows)/len(rows), sum(v[1] for v in rows)/len(rows)) for _, rows in sorted(group_rows.items())]
        n = len(means)
        gain = sum(v[0] for v in means) / n
        seconds = sum(v[1] for v in means) / n
        utilities = [g - CONFIG["brier_loss_per_second"] * c for g, c in means]
        worst_leave_one_out = min((sum(utilities)-v)/(n-1) for v in utilities) if n > 1 else None
        cells.append({"stratum": key, "route": route, "group_count": n,
                      "mean_gain": gain, "mean_additional_seconds": seconds,
                      "mean_net_benefit": sum(utilities)/n,
                      "worst_leave_one_group_out_net_benefit": worst_leave_one_out,
                      "admitted": n >= CONFIG["minimum_groups"] and worst_leave_one_out > 0})
    payload = {"schema": VERSION, "config": CONFIG, "sources": source_identity(),
               "development_sha256": digest(bundle), "producer_hashes": bundle["producers"],
               "development_task_ids": sorted(task_ids), "development_groups": sorted(groups),
               "development_public_sha256": sorted(public_hashes), "cells": cells,
               "loss": "half multiclass Brier, range zero to one; invalid output loss one",
               "scope": "development-fitted heuristic; no generalization or calibration acceptance"}
    return {"policy_sha256": digest(payload), "policy": payload}


def verify_policy(frozen):
    if set(frozen) != {"policy", "policy_sha256"} or digest(frozen["policy"]) != frozen["policy_sha256"]:
        raise ValueError("policy bytes changed")
    policy = frozen["policy"]
    if policy["schema"] != VERSION or policy["config"] != CONFIG or policy["sources"] != source_identity():
        raise ValueError("policy protocol or implementation changed")
    return policy


def select(frozen, task, initial, available, *, mode="benefit-cost", group=None):
    policy = verify_policy(frozen)
    if not isinstance(group, str) or not group:
        raise ValueError("routing requires the declared evaluation group")
    if task.task_id in policy["development_task_ids"] or digest(task.public()) in policy["development_public_sha256"] or group in policy["development_groups"]:
        raise ValueError("development task/group cannot be reported as held-out routing")
    if not set(available) <= set(CONFIG["candidate_routes"]):
        raise ValueError("undeclared additional route")
    key, confidence = stratum(task, initial)
    chosen, reason = "R0", "no admitted positive benefit in this observed stratum"
    if mode in {"fixed", "confidence-only"}:
        if CONFIG["fixed_route"] in available and (mode == "fixed" or confidence < CONFIG["confidence_threshold"]):
            chosen, reason = CONFIG["fixed_route"], mode
        else:
            reason = "fixed route unavailable or confidence-only stop"
    elif mode == "benefit-cost":
        candidates = [c for c in policy["cells"] if c["stratum"] == key and c["route"] in available and c["admitted"]]
        if candidates:
            best = sorted(candidates, key=lambda c: (-c["mean_net_benefit"], c["mean_additional_seconds"], c["route"]))[0]
            chosen, reason = best["route"], "positive development gain after measured cost; leave-one-group-out sign stable"
    else:
        raise ValueError("unknown effort policy")
    return {"route": chosen, "mode": mode, "reason": reason, "stratum": key,
            "initial_confidence": confidence, "policy_sha256": frozen["policy_sha256"]}


def combined_cost(initial, extra, controller_seconds):
    costs = [initial["cost"]] + ([extra["cost"]] if extra else [])
    result = {key: sum(c[key] for c in costs) for key in COST_KEYS - {"reasoning_tokens", "reasoning_tokens_status"}}
    known = all(c["reasoning_tokens"] is not None for c in costs)
    result["reasoning_tokens"] = sum(c["reasoning_tokens"] for c in costs) if known else None
    result["reasoning_tokens_status"] = "measured" if known else "not separately exposed"
    result["wall_seconds"] += controller_seconds
    return result


def run(task: PublicTask, output: Path, frozen, initial_reader, additional_readers, *, mode="benefit-cost", group=None, reader_sources):
    """Drive budget-aware callbacks; completed replay never invokes a callback.

    Callbacks save their literal requests/raw replies and return the normalized
    attempt above. Their pinned source closure is supplied by the actual adapter.
    A transport failure propagates, with no automatic retry or output substitution.
    """
    verify_policy(frozen)
    if not reader_sources or any(not isinstance(v, str) or len(v) != 64 for v in reader_sources.values()):
        raise ValueError("reader source closure required")
    binding = digest({"task": task.public(), "policy": frozen, "mode": mode,
                      "group": group, "available": sorted(additional_readers), "reader_sources": reader_sources})
    terminal = output / "COMPLETE.json"
    if terminal.exists():
        saved = json.loads(terminal.read_text(encoding="utf-8"))
        if saved["binding"] != binding:
            raise ValueError("completed adaptive route binding changed")
        for relative, expected in saved["files"].items():
            path = output / relative
            if not path.resolve().is_relative_to(output.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("completed adaptive route lost or changed retained evidence")
        return json.loads((output / "ROUTE.json").read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / "INPUT.json", {"binding": binding, "public_task": task.public(), "policy": frozen, "reader_sources": reader_sources})
    try:
        initial = initial_reader(task, output / "initial", CONFIG["initial_generated_tokens"])
        check_attempt(task, initial, CONFIG["initial_generated_tokens"])
        start = time.perf_counter()
        decision = select(frozen, task, initial, additional_readers, mode=mode, group=group)
        controller_seconds = time.perf_counter() - start
        write_new(output / "DECISION.json", decision)
        extra = None
        if decision["route"] != "R0":
            extra = additional_readers[decision["route"]](task, output / "additional", CONFIG["additional_generated_tokens"])
            check_attempt(task, extra, CONFIG["additional_generated_tokens"])
        final = extra if extra else initial
        result = {"at": now(), "binding": binding, "decision": decision, "initial": initial, "additional": extra,
                  "status": final["status"], "forecast": final["forecast"], "controller_wall_seconds": controller_seconds,
                  "cost": combined_cost(initial, extra, controller_seconds), "maximum_generated_tokens": CONFIG["maximum_generated_tokens"]}
        write_new(output / "ROUTE.json", result)
        files = {str(p.relative_to(output)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob("*") if p.is_file()}
        write_new(terminal, {"at": now(), "binding": binding, "files": files})
        return result
    except Exception as exc:
        write_new(output / "FAILED.json", {"at": now(), "binding": binding, "error": repr(exc)})
        raise
