"""Discarded literal model/transport checks; no scientific cohort or scores.

DESIGN CHECK: LESSONS 2-5. Known explicit evidence should be copied correctly;
absent evidence permits uncertainty. Invalid support and private fields must be
refused under either hypothesis. Resume must reuse bytes without a new call.
"""
from __future__ import annotations

import argparse
import copy
import json
from dataclasses import replace
from pathlib import Path

from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock
from .contracts import PublicTask, canonical, choices_for, digest, parse_forecast
from .ghost import envelopes, extract, reference_replay, task_from
from .ollama import call, now, request_for, write_new


def checks(output: Path, archive: Path):
    output.mkdir(parents=True, exist_ok=True)
    task = PublicTask("ac06ee93d636433eadb96fa0614a570a", "interface", "artifact",
                      {"statement": "The record says the displayed token is blue."}, "What color is the displayed token?",
                      choices_for(["blue", "red"], "interface-v1"), "at the displayed record",
                      "known-answer instrument fixture", "discarded interface pilot")
    ids = [key for key, _ in task.choices]
    valid = {"choice": ids[0], "probabilities": dict.fromkeys(ids, .5), "explanation": "Undetermined", "insufficient_evidence": True}
    malformed = []
    for name, edit in [
        ("wrong-option", lambda value: value.update(choice="o_ffffffff")),
        ("missing-support", lambda value: value["probabilities"].pop(ids[0])),
        ("wrong-sum", lambda value: value["probabilities"].update({ids[0]: .4})),
        ("private-field", lambda value: value.update(private_answer="secret")),
        ("boolean-probability", lambda value: value["probabilities"].update({ids[0]: True})),
    ]:
        value = copy.deepcopy(valid); edit(value)
        try:
            parse_forecast(canonical(value), task)
        except (ValueError, TypeError):
            malformed.append(name)
        else:
            raise AssertionError("invalid output accepted: " + name)
    if request_for(task) != request_for(replace(task, task_id="b" * 32, exposure="changed hidden metadata")):
        raise AssertionError("private metadata affects model content")
    public_root = output / "ghost-public"
    extract(archive, public_root)
    rows, inventory = envelopes(public_root)
    selected = [next(row["envelope"] for row in rows if row["envelope"]["declared_context"]["operation"] == op)
                for op in ("reading", "opportunity")]
    bad = copy.deepcopy(selected[0]); bad["private_answer"] = "not allowed"
    try:
        task_from(bad)
    except ValueError:
        malformed.append("private-input-field")
    else:
        raise AssertionError("private public-envelope field accepted")
    frames = [*selected, bad, {"operation": "probe-private", "path": str(Path(__file__).resolve())}]
    replay = reference_replay(public_root, frames, output / "GHOST_REFERENCE.json")
    if not all(row.get("ok") for row in replay[:2]) or any(row.get("ok") for row in replay[2:]):
        raise AssertionError("literal public/private transport result differs")
    acquire_gpu_lock("stage10-discarded-interface-v1")
    try:
        known = call(task, output / "known-answer")
        before = (output / "known-answer/RAW.json").read_bytes()
        resumed = call(task, output / "known-answer")
        if resumed != known or before != (output / "known-answer/RAW.json").read_bytes():
            raise AssertionError("resume changed a saved attempt")
        expected = next(key for key, value in task.choices if value == "blue")
        if known["status"] != "VALID" or known["forecast"]["choice"] != expected:
            raise AssertionError("literal known-answer copy failed")
        noinfo = replace(task, task_id="c" * 32, evidence={"statement": "The token color was not recorded."})
        absent = call(noinfo, output / "no-information")
        if absent["status"] != "VALID" or not absent["forecast"]["insufficient_evidence"]:
            raise AssertionError("missing-evidence uncertainty check failed")
        attempts = [known, absent]
        for frame in selected:
            attempts.append(call(task_from(frame), output / ("ghost-" + frame["declared_context"]["operation"])))
        if any(row["status"] != "VALID" for row in attempts):
            raise AssertionError("literal Ghost forecast did not parse; raw reply retained")
    finally:
        release_gpu_lock()
    summary = {"finished_at": now(), "status": "PASS", "scope": "discarded instrument checks, not research findings",
               "malformed_cases_refused": malformed, "private_metadata_invariance": True,
               "actual_resume_reused_bytes": True, "ghost_public_inventory": inventory,
               "ghost_selected_pilot_tasks": [row["task_id"] for row in selected],
               "model_calls": len(attempts), "wall_seconds": sum(row["wall_seconds"] for row in attempts),
               "generated_tokens": sum(row["cost"]["eval_count"] for row in attempts),
               "attempt_bindings": [row["binding"] for row in attempts]}
    write_new(output / "COMPLETE.json", summary)
    print(canonical(summary), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    try:
        checks(args.output, args.archive)
    except Exception as exc:
        write_new(args.output / "FAILED.json", {"at": now(), "error": repr(exc), "scope": "discarded interface check"})
        raise


if __name__ == "__main__":
    main()
