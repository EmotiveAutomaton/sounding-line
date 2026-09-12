"""Native procedure induction and bounded concrete memory for Ghost reading.

DESIGN CHECK: LESSONS2-5; reader priors1/traversal3 and reconstruction bridge2.
NULL: unrepeated or uncompressible traces admit no procedure. ALTERNATIVE:
repeated successful reconstructions may save description length after definition
cost. Reconstructed routes are reader inventions, not historical training traces.
R1/R4 share all training sources, two-episode memory and a 6000-byte storage cap.
"""
from __future__ import annotations
import hashlib
import importlib.util
import math
from pathlib import Path
import sys
import time
import types

from .contracts import canonical, digest
from .queue import read
from .reader import from_record, tokens
from .reading_source import native_world

STORE_BYTES = 6000
MAX_EXAMPLES = 2
NATIVE_MOTIFS = ((0, 1), (2, 3))


def native_learning(root):
    world = native_world(root)
    path = root / "public/consumer/v16_reference/learning.py"
    expected = read(root / "PUBLIC_MANIFEST.json")["consumer_sources"]["v16_reference/learning.py"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("exported native learner changed")
    name = "stage10_exported_craft"
    package = types.ModuleType(name)
    package.__path__ = [str(path.parent)]
    sys.modules[name] = package
    sys.modules[name + ".world"] = world
    spec = importlib.util.spec_from_file_location(name + ".learning", path)
    learning = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = learning
    spec.loader.exec_module(learning)
    return world, learning


def joined(training, answers):
    truth = {row["task_id"]: row for row in answers}
    if len(truth) != len(answers) or set(truth) != {row["task_id"] for row in training} or len(training) != len(truth):
        raise ValueError("training evidence and answers do not join uniquely")
    for row in training:
        task = from_record(row)
        if task.family != "ghost-reading" or truth[task.task_id]["correct_choice"] not in dict(task.choices):
            raise ValueError("wrong training family or answer support")
    return truth


def examples(task, training, answers, *, reserved_bytes=0):
    truth = joined(training, answers)
    if task.family != "ghost-reading" or task.task_id in truth:
        raise ValueError("target is not an out-of-training reading task")
    query = tokens(task.evidence)
    ranked = []
    for row in training:
        source = from_record(row)
        count = tokens(source.evidence)
        norm = math.sqrt(sum(v*v for v in query.values()) * sum(v*v for v in count.values()))
        similarity = sum(v*count.get(k, 0) for k, v in query.items()) / norm if norm else 0
        ranked.append((-similarity, source.task_id, source))
    selected, ids = [], []
    for _, identifier, source in sorted(ranked):
        example = {"evidence_view": source.evidence_view, "evidence": source.evidence,
                   "question": source.question, "observed_outcome": dict(source.choices)[truth[identifier]["correct_choice"]]}
        if len(canonical(selected + [example]).encode("utf8")) + reserved_bytes > STORE_BYTES:
            continue
        selected.append(example); ids.append(identifier)
        if len(selected) == MAX_EXAMPLES:
            break
    if not selected:
        raise ValueError("no complete training episode fits common memory bound")
    return selected, {"method": "word-count cosine with ID tie-break; shared reading-family pool across accurately labelled source views",
                      "selected_ids": ids, "training_sha256": digest(training), "answers_sha256": digest(answers),
                      "maximum_examples": MAX_EXAMPLES, "common_store_bytes": STORE_BYTES,
                      "actual_store_bytes": len(canonical(selected).encode("utf8")) + reserved_bytes}


def induce(root, training, answers, *, prior_observations=(), prior_group=None):
    started = time.perf_counter()
    truth = joined(training, answers)
    world, learning = native_learning(root)
    observations, seen = [], set()
    for row in training:
        task = from_record(row); group = truth[task.task_id]["case_id"]
        evidence = task.evidence
        future = {"artifact": int(dict(task.choices)[truth[task.task_id]["correct_choice"]]),
                  "target": evidence["target_request"]["future_target"], "prefix": [],
                  "feasible": evidence["target_request"].get("feasible", list(range(8)))}
        for obs in [evidence["declared_context"]["current_observation"], *evidence["permitted_prior_artifacts"], future]:
            key = digest([group, obs])
            if key not in seen:
                seen.add(key); observations.append((group, obs))
    if prior_observations and not prior_group:
        raise ValueError("prior observations require an explicit source group")
    for obs in prior_observations:
        if set(obs) != {"artifact", "target", "prefix", "feasible"}:
            raise ValueError("undeclared prior observation fields")
        key = digest([prior_group, obs])
        if key not in seen:
            seen.add(key); observations.append((prior_group, obs))
    traces, targets, provenance = [], [], []
    calls = 0
    for group, obs in observations:
        chosen = None
        for program in world.histories(3):
            if list(program[:len(obs["prefix"])]) != obs["prefix"]:
                continue
            result = world.execute(program, feasible=tuple(obs["feasible"]), budget=3)
            calls += 1
            if result.legal and result.artifact == obs["artifact"]:
                chosen = program; break  # shortest length, then primitive lexical order
        if chosen is not None:
            traces.append(chosen); targets.append(obs["artifact"])
            provenance.append({"source_group": group, "observation": obs, "reader_reconstruction": list(chosen)})
    acquired = learning.learn(traces, targets, capacity=2, min_saving=1)
    calls += len(traces)  # learner checks every trace with the native executor
    selected = [m for m in acquired.library if m in NATIVE_MOTIFS]
    procedures = []
    for motif in selected:
        uses = [r for r in provenance if any(tuple(r["reader_reconstruction"][i:i+2]) == motif for i in range(len(r["reader_reconstruction"])-1))]
        procedures.append({"id": "p_" + digest(list(motif))[:8], "definition": list(motif),
                           "description": "Set board cells " + " then ".join(map(str, motif)) + "; reconstructed use in permitted training artifacts.",
                           "training_observations": len(uses), "training_groups": len({r["source_group"] for r in uses})})
    return {"schema": "stage10.native-memory.1", "training_sha256": digest(training), "answers_sha256": digest(answers),
            "procedures": procedures, "reconstructions": provenance,
            "method": "native fragment learner on shortest reader-reconstructed training artifacts; only existing native motifs retained",
            "omitted_non_native_fragments": [list(m) for m in acquired.library if m not in NATIVE_MOTIFS],
            "training_execution_calls": calls, "wall_seconds": time.perf_counter()-started,
            "scope": "LILO-inspired representation adaptation, not LILO replication; no historical route or personal-library claim"}


def representation(library, naming):
    if naming not in {"opaque", "grounded"}:
        raise ValueError("unknown procedure naming condition")
    return [{k: v for k, v in row.items() if naming == "grounded" or k != "description"} for row in library["procedures"]]
