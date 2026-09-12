"""Read-only bridge to the reviewed Ghost public transfer, without private answers.

DESIGN CHECK: LESSONS 2-5. Both NULL and ALTERNATIVE must preserve public bytes,
source identities and finite task support. Archive traversal, changed members,
extra input fields and private file reads must fail, independently of predictions.
The reference consumer is a transport/executor check, not a historical answer key.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from .contracts import PublicTask, canonical, choices_for, digest
from .ollama import write_new

ARCHIVE_SHA256 = "622f999635657a5d13509809624bdc81aaeca35232d50b3258dae6c5e5771299"
OUTER_FIELDS = {"task_id", "schema_version", "lineage_id", "access_tier", "final_artifact", "declared_context",
                "permitted_prior_artifacts", "permitted_query_descriptions", "query_costs", "target_request", "reader_action_budget"}


def extract(archive: Path, destination: Path) -> dict:
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("Ghost public archive differs from the reviewed transfer")
    with zipfile.ZipFile(archive) as source:
        inventory = json.loads(source.read("ARCHIVE_MEMBER_MANIFEST.json"))
        expected = inventory["files"]
        names = source.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected) | {"ARCHIVE_MEMBER_MANIFEST.json"}:
            raise ValueError("archive member inventory differs")
        root = destination.resolve()
        for member in source.infolist():
            name = member.filename
            parts = PurePosixPath(name)
            target = root.joinpath(*parts.parts)
            if parts.is_absolute() or ".." in parts.parts or "\\" in name or ":" in name or not target.resolve().is_relative_to(root):
                raise ValueError("unsafe archive path")
            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError("archive symlink is not permitted")
            payload = source.read(name)
            if name in expected and (len(payload) != expected[name]["bytes"] or hashlib.sha256(payload).hexdigest() != expected[name]["sha256"]):
                raise ValueError("archive content differs")
            if target.exists():
                if target.read_bytes() != payload:
                    raise ValueError("existing public extraction changed")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(payload)
    return json.loads((destination / "PUBLIC_MANIFEST.json").read_text(encoding="utf-8"))


def envelopes(root: Path) -> tuple[list[dict], dict]:
    manifest = json.loads((root / "PUBLIC_MANIFEST.json").read_text(encoding="utf-8"))
    membership = {task: (case["case_id"], case["lineage_id"]) for case in manifest["cases"] for task in case["tasks_in_recorded_order"]}
    rows = []
    counts = Counter()
    for path in sorted((root / "public/observations").glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        if set(row) != OUTER_FIELDS or row["schema_version"] != "v16.transfer.1":
            raise ValueError("unexpected public envelope")
        if row["task_id"] not in membership or row["lineage_id"] != membership[row["task_id"]][1]:
            raise ValueError("public task is not in the recorded source case")
        context = row["declared_context"]
        if set(context) != {"operation", "reader_options", "observation"}:
            raise ValueError("undeclared context fields")
        counts[context["operation"]] += 1
        rows.append({"case_id": membership[row["task_id"]][0], "envelope": row})
    if len(rows) != manifest["n_tasks"]:
        raise ValueError("incomplete public envelope roster")
    return rows, {"cases": len(manifest["cases"]), "tasks": len(rows), "operations": dict(counts)}


def task_from(envelope: dict) -> PublicTask:
    if set(envelope) != OUTER_FIELDS:
        raise ValueError("unexpected public task fields")
    context = envelope["declared_context"]
    if set(context) != {"operation", "reader_options", "observation"}:
        raise ValueError("unexpected public context fields")
    op, obs = context["operation"], context["observation"]
    if op == "reading":
        allowed = {"schema_version", "task_id", "lineage_id", "access_tier", "final_artifact", "declared_context",
                   "permitted_prior_artifacts", "permitted_query_descriptions", "query_costs", "target_request", "reader_action_budget"}
        if set(obs) != allowed:
            raise ValueError("unexpected reconstruction observation fields")
        evidence = {key: obs[key] for key in ("final_artifact", "declared_context", "permitted_prior_artifacts",
                    "permitted_query_descriptions", "query_costs", "target_request", "reader_action_budget")}
        evidence["public_world"] = (
            "A four-cell board is an integer bitmask 0..15, initially 0. Actions 0..3 set the corresponding bit; "
            "actions 4..7 clear bit action modulo 4. Routes have at most three actions. Artifact distance is the "
            "number of differing bits. The construction target is a desired bitmask, not the future observed answer. "
            "Current and prior observations are completed separate constructions. The future target is for a NEW "
            "construction starting from 0, not continuation of the current artifact. "
            "The maker may reuse acquired two-action motifs (0,1) and (2,3). The maker's acquired motifs and actual route are hidden.")
        values = [str(i) for i in range(16)]
        question = "Forecast the maker's future artifact bitmask for the public future target, from these allowed observations."
        view = "earlier-artifacts" if obs["permitted_prior_artifacts"] else "artifact"
    elif op == "opportunity":
        allowed = {"schema_version", "task_id", "access_tier", "final_artifact", "observations", "allowed_causes", "target_probe", "query_cost", "reader_search_budget"}
        if set(obs) != allowed:
            raise ValueError("unexpected opportunity observation fields")
        evidence = {key: obs[key] for key in allowed - {"schema_version", "task_id", "access_tier"}}
        evidence["public_world"] = (
            "The maker chooses option 0 (do nothing) or option 1 (set the first board bit). Causes concern physical availability, knowledge, "
            "consideration, purpose, search budget, or a false affordance. Reminder adds action 1 to consideration; "
            "demonstration reveals whether option 1 is actually available and considers both options; tool makes option 1 "
            "available, known and considered; retarget sets purpose to 1; search increases search budget to 2; higher-reward "
            "sets reward to 2. The artifact is 1 when option 1 is successfully enacted, and 0 otherwise. "
            "Utility is reward times matching the purpose minus action cost times the option. Only considered options "
            "within the search budget and believed available are evaluated, with ties favoring 0. "
            "Action cost is one of 0.1, 0.5, 1.25; nonbaseline motor lapse probability is one of 0.02, 0.08, 0.2. "
            "The cause, action cost and lapse probability are hidden.")
        values = ["0", "1"]
        question = "Forecast the artifact after the declared target probe, using only the observed prior probes."
        view = "process-record"
    else:
        raise ValueError("operation not yet implemented as a Stage 10 reader task")
    return PublicTask(envelope["task_id"], "ghost-" + op, view, evidence, question,
                      choices_for(values, envelope["task_id"]), "the declared future target or probe",
                      "constructed maker in the exported Ghost world", "previously exposed V16; descriptive")


def reference_replay(root: Path, frames: list[dict], output: Path) -> list[dict]:
    consumer = root / "public/consumer"
    command = [sys.executable, "-s", "-B", "-u", "-m", "consumer"]
    payload = "".join(canonical(frame) + "\n" for frame in [*frames, {"operation": "shutdown"}])
    completed = subprocess.run(command, input=payload, text=True, encoding="utf-8", capture_output=True,
                               cwd=consumer, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    receipt = {"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    write_new(output, receipt)
    if completed.returncode:
        raise RuntimeError("public reference consumer failed; receipt retained")
    replies = [json.loads(line) for line in completed.stdout.splitlines()]
    expected = {str(path.relative_to(consumer)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [consumer / "consumer.py", *sorted((consumer / "v16_reference").glob("*.py"))]}
    if len(replies) != len(frames) + 1 or replies[0].get("ready") is not True or replies[0].get("sources") != expected or replies[0].get("ghostscale_imports") != []:
        raise ValueError("reference consumer source or frame receipt differs")
    return replies[1:]
