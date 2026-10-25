"""WB1 S4 continuation: copy completed bytes, then replay the original verifier.

DESIGN CHECK: LESSONS 3-5 read 2026-10-25. NULL: a changed source, altered
checkpoint, unfinished execution, non-cost failure, different configuration or
changed scientific producer refuses continuation. ALTERNATIVE: complete saved
execution survives exactly, and the unchanged verifier reconstructs all original
raw/P2 sessions in a fresh counted process. No partial verification is credited.
This allocates remaining original-card CPU; it is neither healing nor science.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import shutil

from runners.drive.cards import week3_pieces_input as original
from runners.drive.cards import week3_pieces_input_recovery as recovery
from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_p6 import write_equal

MODULE = "runners.drive.cards.week3_pieces_input_recovery"
RECEIPTS = dict(previous_plan="PLAN.json", previous_failure="FAILED.json",
                previous_result="RESULT.json", previous_progress="PROGRESS.json",
                execute_usage="EXECUTE_JOB_USAGE.json", verify_usage="VERIFY_JOB_USAGE.json")
AGGREGATES = ("WB1_INPUT_INDEX.json", "WB1_WRITER_SPLIT.json", "WB1_BIN_EDGES.json", "WB1_INPUT_RESULT.json")
RUNTIME = {"runners/drive/cards/batch_runtime.py", "runners/drive/cards/batch_runtime_v5.py",
           "runners/drive/cards/states.py", "runners/drive/cards/states_v2.py",
           "runners/drive/cards/week3_policy.py", "runners/drive/native_job.py",
           "runners/drive/week3_launch.py"}
CODE_ROOT = Path(__file__).resolve().parents[3]


def finite_nonnegative(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid CPU accounting")
    return float(value)


def inspect(inputs, config):
    original.validate_config(config)
    if set(inputs) != set(RECEIPTS):
        raise ValueError("exact continuation receipt inputs required")
    root = Path(inputs["previous_plan"]).resolve().parent
    for key, name in RECEIPTS.items():
        if Path(inputs[key]).resolve() != root / name:
            raise ValueError("mixed predecessor receipts")
    if (root / "COMPLETE.json").exists():
        raise ValueError("already completed predecessor")
    plan, failed, result, progress, execution, replay = [read(inputs[k]) for k in RECEIPTS]
    if plan.get("module") != MODULE or plan["config"] != config:
        raise ValueError("different frozen producer or configuration")
    if failed.get("status") != "FAILED" or failed.get("failure_class") != "cost" or progress.get("phase") != "verify":
        raise ValueError("only verify-phase cost interruption may continue")
    if execution.get("exit_code") != 0 or not execution.get("includes_all_descendants_and_exited_processes") or not replay.get("includes_all_descendants_and_exited_processes"):
        raise ValueError("complete execution and counted descendant usage required")
    spent = finite_nonnegative(failed["cpu_seconds"])
    if abs(spent - finite_nonnegative(execution["cpu_seconds"]) - finite_nonnegative(replay["cpu_seconds"])) > 1e-7:
        raise ValueError("CPU receipts disagree")
    prior = finite_nonnegative(plan["prior_cpu_seconds_charged"]) + spent
    ceiling = finite_nonnegative(plan["original_cpu_ceiling_seconds"])
    if prior >= ceiling:
        raise ValueError("original card CPU exhausted")
    # Capsules prove the actual old program; current scientific code must agree.
    # Runtime may evolve separately, but cannot replace the frozen scientific code.
    producer_root = Path(plan["inputs"]["repo_root"]).resolve()
    code = {}
    for name, digest in plan["pins"].items():
        path = Path(name)
        if not path.is_absolute():
            path = producer_root / path
        try:
            rel = path.resolve().relative_to(producer_root).as_posix()
        except ValueError:
            continue
        if not rel.startswith("runners/") or not rel.endswith(".py"):
            continue
        if rel in RUNTIME:
            # Launch-time validation tools are pinned but need not be imports
            # in the executed child capsule. Only scientific imports continue.
            continue
        if filehash(root / "source_capsule" / rel) != digest:
            raise ValueError("predecessor source capsule changed")
        if filehash(CODE_ROOT / rel) != digest:
            raise ValueError("frozen scientific producer changed")
        code[rel] = digest
    for name in ("week3_pieces_input.py", "week3_pieces_input_recovery.py"):
        if "runners/drive/cards/" + name not in code:
            raise ValueError("scientific producer absent from predecessor pins")
    output = root / "output"
    if read(output / "WB1_INPUT_RESULT.json") != result or result["sessions"] != config["expected_sessions"]:
        raise ValueError("completed execution aggregate disagrees")
    checkpoint = read(output / "PROGRESS.json")
    if checkpoint.get("sessions_completed") != config["expected_sessions"]:
        raise ValueError("incomplete execution census")
    index = read(output / "WB1_INPUT_INDEX.json")
    if len(index) != config["expected_sessions"] or len({r["session"] for r in index}) != len(index):
        raise ValueError("duplicate or incomplete session census")
    files = {name: filehash(output / name) for name in AGGREGATES}
    for row in index:
        expected = "sessions/" + hashlib.sha256(row["session"].encode()).hexdigest() + ".json.gz"
        if row["file"] != expected or filehash(output / expected) != row["sha256"]:
            raise ValueError("saved session identity or bytes changed")
        files[expected] = row["sha256"]
    if {p.relative_to(output).as_posix() for p in (output / "sessions").iterdir()} != set(files) - set(AGGREGATES):
        raise ValueError("unexpected saved session files")
    binding = dict(schema="week3-wb1-verification-continuation-v1", previous_root=str(root),
                   receipt_hashes={key:filehash(inputs[key]) for key in RECEIPTS},
                   scientific_code=code, unchanged_output_files=files,
                   prior_cpu_seconds_charged=prior, original_cpu_ceiling_seconds=ceiling,
                   original_configuration=config, source_bindings=result["source_bindings"],
                   replay="full original raw/P2 reconstruction; interrupted replay earns no credit",
                   scientific_admission=False)
    return output, plan, result, binding


def verify_copies(output, binding):
    for name, digest in binding["unchanged_output_files"].items():
        if filehash(Path(output) / name) != digest:
            raise ValueError("continued output bytes changed")
    if read(Path(output) / "CONTINUATION.json") != binding:
        raise ValueError("continuation receipt changed")


def execute(output, inputs, config):
    previous, _, result, binding = inspect(inputs, config)
    output = Path(output).resolve()
    if output == previous.resolve() or previous.resolve() in output.parents:
        raise ValueError("predecessor must remain immutable")
    for name, digest in binding["unchanged_output_files"].items():
        target = output / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(previous / name, target)
        if filehash(target) != digest:
            raise ValueError("continued output bytes changed")
    write_equal(output / "CONTINUATION.json", binding)
    verify_copies(output, binding)
    return result


def verify(output, inputs, config):
    _, plan, _, binding = inspect(inputs, config)
    verify_copies(output, binding)
    result = recovery.verify(output, plan["inputs"], config)
    # Recheck both immutable output and all source receipts after the replay.
    _, _, _, after = inspect(inputs, config)
    if after != binding:
        raise ValueError("predecessor changed during fresh replay")
    verify_copies(output, binding)
    return dict(**result, continuation="byte-preserving S4 cost continuation",
                prior_cpu_seconds_charged=binding["prior_cpu_seconds_charged"])
