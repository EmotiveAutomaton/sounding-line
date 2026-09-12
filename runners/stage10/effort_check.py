"""Known-answer controller checks; constructed responses, no model inference.

DESIGN CHECK: LESSONS3-5. Confidence-only must fail a confidently wrong fixture;
benefit/cost must stop under zero gain and excessive cost. Malformed acquired
answers retain loss and cost, never fall back to the previously correct answer.
Replay cannot call a reader, and missing saved evidence must refuse replay.
"""
from __future__ import annotations

import argparse
import copy
import json
from dataclasses import asdict, replace
from pathlib import Path

from . import effort
from .contracts import PublicTask, choices_for, digest
from .ollama import now, write_new


def task_for(number):
    return PublicTask(digest(["effort-fixture", number])[:32], "fixture", "artifact",
                      {"observation": "constructed effort fixture", "case": number}, "Which recorded outcome follows?",
                      choices_for(["blue", "red"], "effort-fixture"), "after observation", "constructed fixture", "discarded")


def attempt(task, allowance, *, good=False, seconds=10., invalid=False):
    ids = [key for key, _ in task.choices]
    probabilities = {ids[0]: .01 if good else .99, ids[1]: .99 if good else .01}
    return {"status": "INVALID" if invalid else "VALID",
            "forecast": None if invalid else {"choice": max(probabilities, key=probabilities.get), "probabilities": probabilities,
                                               "explanation": "constructed fixture", "insufficient_evidence": False},
            "cost": {"wall_seconds": seconds, "model_calls": 1, "input_tokens": 20, "output_tokens": 10,
                     "executor_evaluations": 0, "reasoning_tokens": None, "reasoning_tokens_status": "not separately exposed"},
            "maximum_generated_tokens": allowance, "evidence_sha256": digest(task.public())}


def bundle():
    rows = []
    for index in range(4):
        task = task_for(index)
        rows.append({"task": asdict(task), "group": "development-"+str(index//2), "truth": task.choices[1][0],
                     "routes": {"R0": attempt(task, 256), "R1": attempt(task, 512, seconds=2), "R3": attempt(task, 512, good=True)}})
    return {"schema": "stage10.effort-development.1", "phase": "development", "complete": True,
            "producers": {"constructed-fixture-only": "a"*64}, "rows": rows}


def checks(output):
    output.mkdir(parents=True, exist_ok=False)
    passed = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        passed.append(name)
    def refuses(name, fn):
        try:
            fn()
        except (ValueError, FileNotFoundError):
            passed.append(name)
        else:
            raise AssertionError("did not refuse: "+name)
    source = bundle()
    frozen = effort.fit(source)
    target = task_for(100)
    initial = attempt(target, 256)
    def choose(policy=frozen, task=target, first=initial, mode="benefit-cost", available=("R1", "R3")):
        return effort.select(policy, task, first, available, mode=mode, group="evaluation-only")
    check("confidently_wrong_benefit_buys_useful_route", choose()["route"] == "R3")
    check("confidence_only_misses_confident_error", choose(mode="confidence-only")["route"] == "R0")
    check("fixed_effort_uses_predeclared_route", choose(mode="fixed")["route"] == "R1")
    null = copy.deepcopy(source)
    for row in null["rows"]:
        task = effort.from_record(row["task"])
        row["routes"]["R3"] = attempt(task, 512)
    check("no_gain_stops", choose(effort.fit(null))["route"] == "R0")
    costly = copy.deepcopy(source)
    for row in costly["rows"]:
        row["routes"]["R3"]["cost"]["wall_seconds"] = 10000.
    check("gain_below_cost_stops", choose(effort.fit(costly))["route"] == "R0")
    single = copy.deepcopy(source)
    for row in single["rows"]:
        row["group"] = "single"
    check("single_group_stops", choose(effort.fit(single))["route"] == "R0")
    unstable = copy.deepcopy(source)
    for row in unstable["rows"][:2]:
        row["routes"]["R3"] = attempt(effort.from_record(row["task"]), 512, invalid=True)
    check("unstable_group_benefit_stops", choose(effort.fit(unstable))["route"] == "R0")
    other = replace(target, family="unseen")
    check("unseen_stratum_stops", choose(task=other, first=attempt(other, 256))["route"] == "R0")
    check("unavailable_good_route_no_oracle_substitution", choose(available=("R1",))["route"] == "R0")
    check("unknown_reasoning_count_retained", initial["cost"]["reasoning_tokens"] is None)
    refusals = []
    for name, mutate in [
        ("evaluation_answers_cannot_fit", lambda b: b.update(phase="evaluation")),
        ("partial_producer_cannot_fit", lambda b: b.update(complete=False)),
        ("missing_route_cannot_fit", lambda b: b["rows"][0]["routes"].pop("R3")),
        ("wrong_budget_cannot_fit", lambda b: b["rows"][0]["routes"]["R3"].update(maximum_generated_tokens=768)),
        ("negative_cost_cannot_fit", lambda b: b["rows"][0]["routes"]["R3"]["cost"].update(wall_seconds=-1)),
        ("undeclared_answer_cannot_fit", lambda b: b["rows"][0].update(truth="hidden")),
    ]:
        value = copy.deepcopy(source); mutate(value)
        refuses(name, lambda value=value: effort.fit(value))
    changed = copy.deepcopy(frozen); changed["policy"]["config"]["confidence_threshold"] = .1
    refuses("changed_frozen_policy_refused", lambda: choose(changed))
    refuses("development_group_refused", lambda: effort.select(frozen, target, initial, ("R1",), group="development-0"))
    twin = task_for(0)
    refuses("development_public_twin_refused", lambda: choose(task=replace(twin, task_id="e"*32), first=attempt(twin, 256)))
    check("known_correct_brier_zero", effort.loss(target, {"status":"VALID", "forecast":{"probabilities":{target.choices[0][0]:0., target.choices[1][0]:1.}}}, target.choices[1][0]) == 0.)
    check("invalid_worst_loss_one", effort.loss(target, attempt(target, 512, invalid=True), target.choices[1][0]) == 1.)
    calls = []
    def callback(good=False, invalid=False):
        def reader(task, path, allowance):
            calls.append((path.name, allowance))
            path.mkdir(parents=True)
            result = attempt(task, allowance, good=good, invalid=invalid)
            write_new(path / "REQUEST.json", {"fixture": True, "task": task.public(), "allowance": allowance})
            write_new(path / "RAW.json", {"fixture": True, "response": result})
            return result
        return reader
    readers = {"R1": callback(), "R3": callback(good=True)}
    run_kwargs = {"group": "evaluation-only", "reader_sources": {"fixture": "b"*64}}
    route = effort.run(target, output / "route", frozen, callback(), readers, **run_kwargs)
    check("actual_driver_reserves_256_plus_512", calls == [("initial", 256), ("additional", 512)])
    check("both_calls_and_controller_charged", route["cost"]["model_calls"] == 2 and route["cost"]["wall_seconds"] >= 20. and route["cost"]["output_tokens"] == 20)
    def unavailable(*args):
        raise AssertionError("replay called reader")
    resumed = effort.run(target, output / "route", frozen, unavailable, dict.fromkeys(readers, unavailable), **run_kwargs)
    check("completed_replay_no_calls", resumed == route)
    # Fixture corruption only; preserve original bytes beside the intentionally damaged raw.
    raw = output / "route/additional/RAW.json"
    write_new(output / "saved-fixture-raw.json", json.loads(raw.read_text(encoding="utf-8")))
    raw.write_text("{}\n", encoding="utf-8")
    refuses("changed_raw_refuses_replay", lambda: effort.run(target, output / "route", frozen, unavailable, dict.fromkeys(readers, unavailable), **run_kwargs))
    failed_extra = effort.run(target, output / "invalid-extra", frozen, callback(good=True), {"R1":callback(invalid=True)}, mode="fixed", **run_kwargs)
    check("failed_refinement_not_replaced_by_correct_initial", failed_extra["forecast"] is None and failed_extra["status"] == "INVALID" and failed_extra["cost"]["model_calls"] == 2)
    write_new(output / "DEVELOPMENT_FIXTURE.json", source)
    write_new(output / "POLICY_FIXTURE.json", frozen)
    result = {"at": now(), "status": "PASS", "checks": passed, "check_count": len(passed), "sources": effort.source_identity(),
              "model_calls": 0, "fixture_callback_calls": len(calls), "scope": "constructed controller/driver validation only; no scientific fit or real model adapter"}
    write_new(output / "COMPLETE.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = checks(args.output)
        print(json.dumps({k: result[k] for k in ("status", "check_count", "model_calls")}))
    except Exception as exc:
        write_new(args.output / "FAILED.json", {"at": now(), "error": repr(exc)})
        raise
