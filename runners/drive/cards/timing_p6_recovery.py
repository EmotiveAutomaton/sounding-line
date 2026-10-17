"""P6's one exact-arithmetic recovery, retaining every original score.

DESIGN CHECK: LESSONS 3-5 reread, 2026-10-17. Under NULL and ALTERNATIVE
scientific scores are identical to the retained original. Verification uses
the producer's left-to-right addition, not Python 3.13's compensated sum.
Changed sources, scores, counts or totals fail exact equality; no tolerance is
introduced. This admits an instrument only and cannot change a family verdict.
"""
from __future__ import annotations

import math
from pathlib import Path

from . import timing_p6 as original
from .timing_census import read, write, filehash


def replay_scores(output):
    output = Path(output)
    index = read(output / "P6_INDEX.json")
    for row in index:
        path = output / row["file"]
        path.resolve().relative_to(output.resolve())
        if filehash(path) != row["sha256"]:
            raise ValueError("P6 score hash changed")
        record = original.gzread(path)
        total, count = 0., 0
        for word in record["words"]:
            probability = word["population_probability"]
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError("P6 invalid saved probability")
            surprisal = -math.log(probability) if probability else None
            if surprisal != word["population_surprisal"]:
                raise ValueError("P6 token surprisal changed")
            if probability:
                total += surprisal
                count += 1
        computed = dict(row, word_count=len(record["words"]),
                        scored_count=count, total_nll=total)
        if computed != row:
            raise ValueError("P6 exact sequential reduction mismatch")
    result = original.summary(index)
    if result != read(output / "P6_PRIMARY.json"):
        raise ValueError("P6 original primary changed")
    return result


def source_binding(inputs, config):
    if config or set(inputs) != {"original_plan", "original_failure", "diagnosis"}:
        raise ValueError("P6 recovery has fixed scope")
    plan_path = Path(inputs["original_plan"])
    root = plan_path.parent
    if Path(inputs["original_failure"]).resolve() != (root / "FAILED.json").resolve():
        raise ValueError("P6 failure belongs to another attempt")
    plan, failed, diagnosis = (read(inputs[k]) for k in
                                ("original_plan", "original_failure", "diagnosis"))
    if plan["module"] != "runners.drive.cards.timing_p6" or plan["config"]:
        raise ValueError("P6 unsupported original plan")
    if failed["status"] != "FAILED" or "verify child exited 1" not in failed["error"]:
        raise ValueError("P6 unsupported original failure")
    if not diagnosis["native_ended"] or not diagnosis["sequential_reductions_exact"]:
        raise ValueError("P6 recovery lacks owner diagnosis")
    if diagnosis["failure_sha256"] != filehash(inputs["original_failure"]):
        raise ValueError("P6 diagnosis binding changed")
    for path, expected in plan["pins"].items():
        if filehash(path) != expected:
            raise ValueError("P6 original source changed")
    output = root / "output"
    binding = read(output / "P6_BINDINGS.json")
    if binding["config"] != plan["config"] or binding["inputs"] != {
        k: filehash(v) for k, v in plan["inputs"].items() if k != "repo_root"
    } or binding["repo_root"] != str(Path(plan["inputs"]["repo_root"]).resolve()):
        raise ValueError("P6 original input binding changed")
    if binding["index_sha256"] != filehash(output / "P6_INDEX.json"):
        raise ValueError("P6 original index changed")
    paths = [output / name for name in ("P6_INDEX.json", "P6_PRIMARY.json", "P6_BINDINGS.json")]
    paths += [output / row["file"] for row in read(output / "P6_INDEX.json")]
    for path in paths:
        path.resolve().relative_to(output.resolve())
    return output, dict(inputs={k: filehash(v) for k, v in inputs.items()},
        source_files={p.relative_to(output).as_posix(): filehash(p) for p in paths},
        policy="exact producer-order replay; byte-identical score reuse; no tolerance or refit")


def execute(output, inputs, config):
    output = Path(output)
    source, binding = source_binding(inputs, config)
    result = replay_scores(source)
    for name, expected in binding["source_files"].items():
        target = output / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write((source / name).read_bytes())
        if filehash(target) != expected:
            raise ValueError("P6 copied evidence changed")
    original.write_equal(output / "RECOVERY_BINDING.json", binding)
    original.write_equal(output / "SUMMARY.json", result)
    if replay_scores(output) != result:
        raise ValueError("P6 copied primary changed")
    return result


def verify(output, inputs, config):
    output = Path(output)
    _, binding = source_binding(inputs, config)
    if binding != read(output / "RECOVERY_BINDING.json"):
        raise ValueError("P6 recovery binding changed")
    for name, expected in binding["source_files"].items():
        if filehash(output / name) != expected:
            raise ValueError("P6 recovered evidence changed")
    result = replay_scores(output)
    if result != read(output / "SUMMARY.json"):
        raise ValueError("P6 recovered primary changed")
    return dict(verified=True, primary=result, exact_original_scores=True,
                reused_files=len(binding["source_files"]))
