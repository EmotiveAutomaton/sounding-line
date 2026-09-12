"""Freeze the small Ghost reconstruction cohort before reading training truth.

DESIGN CHECK: LESSONS2-5, retained complete reading; reconstruction theory2.
Under NULL or ALTERNATIVE, source identities, case separation and actual future
execution must agree. A reference forecast is never truth. Only allocated
training records are opened. Existing selected V16 cases remain descriptive.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from .contracts import digest
from .ghost import envelopes, task_from
from .ollama import now, write_new
from .queue import read
from .reader import from_record

PILOT_CASE = "bf1690a65f214c978ebf6d5a1020d3e5"
SCOPE = "previously exposed V16 reconstruction; case-separated descriptive screen, not independent constructors"


def public_sources(root):
    manifest = read(root / "PUBLIC_MANIFEST.json")
    archive = read(root / "ARCHIVE_MEMBER_MANIFEST.json")["files"]
    if hashlib.sha256((root / "PUBLIC_MANIFEST.json").read_bytes()).hexdigest() != archive["PUBLIC_MANIFEST.json"]["sha256"]:
        raise ValueError("public manifest changed")
    rows, _ = envelopes(root)
    selected = []
    for row in rows:
        env = row["envelope"]
        if env["declared_context"]["operation"] != "reading":
            continue
        relative = "public/observations/" + env["task_id"] + ".json"
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != manifest["observations"][relative]:
            raise ValueError("original reading envelope changed")
        selected.append(row)
    return manifest, selected


def allocate(root, output):
    manifest, rows = public_sources(root)
    unique = {}
    for row in sorted(rows, key=lambda r: r["envelope"]["task_id"]):
        task = task_from(row["envelope"])
        key = (row["case_id"], digest([task.evidence, task.question, task.evidence_view]))
        unique.setdefault(key, row)
    cases = sorted({r["case_id"] for r in unique.values()} - {PILOT_CASE},
                   key=lambda c: digest(["stage10-reading-allocation-v1", c]))
    if len(cases) != 7:
        raise ValueError("reviewed source case roster changed")
    lanes = {"train": cases[:2], "development": cases[2:4], "evaluation": cases[4:]}
    allocation = {"schema": "stage10.reading-allocation.1", "scope": SCOPE,
                  "source_public_manifest_sha256": digest(manifest), "excluded_pilot_cases": [PILOT_CASE],
                  "order": "fixed case-hash rank; no temporal-order claim", "tasks": [],
                  **{lane + "_cases": values for lane, values in lanes.items()}}
    public, frames = {}, {}
    for lane, values in lanes.items():
        chosen = [r for r in unique.values() if r["case_id"] in values]
        public[lane] = {"tasks": [asdict(task_from(r["envelope"])) for r in chosen]}
        frames[lane] = {"envelopes": [r["envelope"] for r in chosen], "scope": SCOPE}
        allocation["tasks"] += [{"case_id": r["case_id"], "task_id": r["envelope"]["task_id"], "lane": lane} for r in chosen]
    # This write precedes every call that can open a private training record.
    persist(output / "ALLOCATION.json", allocation)
    for lane in lanes:
        persist(output / (lane + "-public.json"), public[lane])
        persist(output / (lane + "-envelopes.json"), frames[lane])
    return allocation


def persist(path, value):
    if path.exists():
        if digest(read(path)) != digest(value):
            raise ValueError("immutable prepared record changed: " + path.name)
    else:
        write_new(path, value)


def native_world(root):
    path = root / "public/consumer/v16_reference/world.py"
    manifest = read(root / "PUBLIC_MANIFEST.json")
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["consumer_sources"]["v16_reference/world.py"]:
        raise ValueError("native world source changed")
    name = "stage10_exported_training_world"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def target_from_record(data, case, task, members, world):
    if data["case_id"] != case or set(data["task_ids"]) != members:
        raise ValueError("reading training task/case membership differs")
    # Reading's outer hidden_continuations is null. The original nested record
    # retains the actual sampled future construction, separately from forecasts.
    future = data["true_production_record"]["hidden_continuations"]
    if type(future["artifact"]) is not int or future["artifact"] not in range(16):
        raise ValueError("future artifact is outside the four-cell board")
    requested = task.evidence["target_request"]
    if future["target"] != requested["future_target"] or future["feasible"] != requested.get("feasible", list(range(8))):
        raise ValueError("recorded future task differs from requested target")
    program = future["program"]
    if not isinstance(program, list) or len(program) > 3 or any(type(a) is not int or a not in range(8) for a in program):
        raise ValueError("recorded future program is malformed")
    execution = world.execute(program, feasible=tuple(future["feasible"]), budget=3)
    if not execution.legal or execution.artifact != future["artifact"]:
        raise ValueError("original native execution does not reproduce recorded future")
    return next(key for key, value in task.choices if value == str(execution.artifact))


def prepare(root, export, output):
    allocation = allocate(root, output)
    manifest = read(root / "PUBLIC_MANIFEST.json")
    members = {c["case_id"]: set(c["tasks_in_recorded_order"]) for c in manifest["cases"]}
    training = read(output / "train-public.json")
    tasks = {t["task_id"]: from_record(t) for t in training["tasks"]}
    raw = read(export / "RAW_MANIFEST.json")
    world = native_world(root)
    labels, sources = [], {}
    for case in allocation["train_cases"]:
        relative = "private/" + case + "-evaluation.json"
        payload = (export / relative).read_bytes()
        sha = hashlib.sha256(payload).hexdigest()
        if sha != raw["files"][relative]:
            raise ValueError("original training evaluator changed")
        data = json.loads(payload)
        for row in allocation["tasks"]:
            if row["case_id"] == case:
                if row["lane"] != "train":
                    raise ValueError("training case crosses allocation")
                task = tasks[row["task_id"]]
                labels.append({"task_id": task.task_id, "correct_choice": target_from_record(data, case, task, members[case], world),
                               "case_id": case, "target_source": "true_production_record.hidden_continuations.artifact; native replay verified"})
        sources[case] = sha
    answers = {"targets": labels}
    frozen = {"scope": SCOPE, "allocation_sha256": digest(allocation),
              "public_sha256": {lane: digest(read(output / (lane + "-public.json"))) for lane in ("train", "development", "evaluation")},
              "evaluator_sha256": {"train": digest(answers)}, "training_source_sha256": sources,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "counts": {lane: len(read(output / (lane + "-public.json"))["tasks"]) for lane in ("train", "development", "evaluation")}}
    persist(output / "train-evaluator.json", answers)
    persist(output / "FROZEN.json", frozen)
    return frozen


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for name in ("public-root", "export", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.public_root, a.export, a.output)["counts"]))
