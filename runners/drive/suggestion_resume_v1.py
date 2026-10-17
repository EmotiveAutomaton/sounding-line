"""One checkpoint recovery of the admitted full suggestion pass.

DESIGN CHECK: LESSONS 3-5 reread October 17. NULL and ALTERNATIVE retain the
same input roster, scorers, precision, exclusions and safety limits. Only an
authenticated consecutive checkpoint prefix is reused. Missing, changed or
out-of-order evidence refuses. Original wall time is conservatively charged to
the original compute allowance; no score or threshold is repaired. Fresh-process
full checkpoint validation is required before COMPLETE. No automatic retry.
"""
import argparse
import gc
import math
import os
import subprocess
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

from . import suggestion_corpus_v4 as base

REPO = base.REPO
SOURCE = base.MAIN
ROOT = base.RAW / "drive-suggestion-main-v5"


def prefix_keys(records, groups):
    expected = [(model, g["session"]) for model in base.ORDER for g in groups if g["cases"]]
    actual = [(row["model"], row["session"]) for row in records]
    if actual != expected[:len(actual)] or len(actual) > len(expected):
        raise ValueError("Retained chunks are not the exact consecutive prefix")
    return actual


def remaining_budget(plan, started, ended):
    charged = math.ceil((datetime.fromisoformat(ended) - datetime.fromisoformat(started)).total_seconds())
    remaining = plan["max_compute_seconds"] - charged
    if charged < 0 or remaining <= 0:
        raise ValueError("Original aggregate computation allowance exhausted")
    return charged, remaining


def totals(rows):
    result = dict(items=0, eligible=0, target_tokens=0, input_tokens=0)
    for row in rows:
        for score in row["scores"]:
            result["items"] += 1
            if score["eligible"]:
                result["eligible"] += 1
                result["target_tokens"] += score["target_tokens"]
                result["input_tokens"] += score["prefix_tokens"] + score["target_tokens"]
    return result


def check_census(observed, census):
    expected = dict(items=sum(census["counts"][c + "_total"] for c in ("c0", "c1", "c2", "c3")),
                    eligible=census["counts"]["eligible"], target_tokens=census["target_tokens"],
                    input_tokens=census["input_tokens"])
    if observed != expected:
        raise ValueError("Complete model census mismatch")


def prepare():
    if datetime.now().astimezone() >= datetime.fromisoformat("2026-10-21T13:00:00+00:00"):
        raise RuntimeError("Campaign no-new-start freeze reached")
    if ROOT.exists():
        raise ValueError("Recovery attempt already exists")
    plan = base.read(SOURCE / "PLAN.json")
    failure, owner = base.read(SOURCE / "FAILED.json"), base.read(SOURCE / "OWNER.json")
    if failure["reason"] != "GPU safety floor" or base.native_identity(owner["native"]["pid"]) == owner["native"]:
        raise ValueError("Original failure or native exit not established")
    base.check_pins(plan["pins"])
    groups = base.read(base.PILOT / "CASES.json")
    records = base.read(SOURCE / "CHUNKS.json")
    prefix_keys(records, groups)
    by_session = {g["session"]: g["cases"] for g in groups}
    source_plan = base.filehash(SOURCE / "PLAN.json")
    for row in records:
        base.load_checkpoint(SOURCE / row["model"] / row["file"], row,
                             by_session[row["session"]], source_plan, row["model"])
    charged, remaining = remaining_budget(plan, owner["at"], failure["at"])
    plan.update(at=base.now(), predecessor_wall_seconds_charged=charged,
                max_compute_seconds=remaining, predecessor_plan_sha256=source_plan,
                predecessor_chunks=len(records), recovery="exact retained prefix, unchanged numerical and safety protocol")
    sources = [SOURCE / n for n in ("PLAN.json", "FAILED.json", "OWNER.json", "CHUNKS.json")]
    sources += [Path(__file__), REPO / "tests/test_drive_suggestion_resume.py"]
    plan["pins"].update(base.pins(sources))
    base.freeze(ROOT / "PLAN.json", plan)
    base.freeze(ROOT / "REUSE.json", records)
    base.freeze(ROOT / "PREPARED.json", dict(at=base.now(), retained_chunks=len(records),
        all_retained_rows_validated=True, reuse_sha256=base.filehash(ROOT / "REUSE.json"),
        plan_sha256=base.filehash(ROOT / "PLAN.json"), charged_seconds=charged))


def verify():
    plan = base.read(ROOT / "PLAN.json")
    base.check_pins(plan["pins"])
    groups = base.read(base.PILOT / "CASES.json")
    cases = {g["session"]: g["cases"] for g in groups}
    records = base.read(ROOT / "CHUNKS.json")
    prefix_keys(records, groups)
    if len(records) != sum(bool(g["cases"]) for g in groups) * len(base.ORDER):
        raise ValueError("Full roster incomplete")
    reuse = {(r["model"], r["session"]): r for r in base.read(ROOT / "REUSE.json")}
    if base.filehash(ROOT / "REUSE.json") != base.read(ROOT / "PREPARED.json")["reuse_sha256"]:
        raise ValueError("Recovery manifest changed")
    combined = {model: dict(items=0, eligible=0, target_tokens=0, input_tokens=0) for model in base.ORDER}
    for row in records:
        key = (row["model"], row["session"])
        old = reuse.get(key)
        if old is not None and row != old:
            raise ValueError("Reused checkpoint record changed")
        expected_plan = plan["predecessor_plan_sha256"] if old else base.filehash(ROOT / "PLAN.json")
        value = base.load_checkpoint(ROOT / row["model"] / row["file"], row, cases[row["session"]], expected_plan, row["model"])
        for name, count in totals(value["rows"]).items():
            combined[row["model"]][name] += count
    census = base.read(base.PILOT / "CENSUS.json")
    for model, counts in combined.items():
        check_census(counts, census[model])
    base.freeze(ROOT / "VERIFIED.json", dict(at=base.now(), verified=True, complete_chunks=len(records),
        reused_chunks=len(reuse), all_rosters_and_reductions_recomputed=True,
        chunks_sha256=base.filehash(ROOT / "CHUNKS.json")))


def run():
    if datetime.now().astimezone() >= datetime.fromisoformat("2026-10-21T13:00:00+00:00"):
        raise RuntimeError("Campaign no-new-start freeze reached")
    base.limits()
    plan = base.read(ROOT / "PLAN.json")
    base.check_pins(plan["pins"])
    if {n: base.importlib.metadata.version(n) for n in base.VERSIONS} != plan["versions"]:
        raise ValueError("Runtime version changed")
    if base.filehash(base.DLL) != plan["nvml_dll_sha256"]:
        raise ValueError("Telemetry library changed")
    base.require_resources(base.resource_snapshot())
    with (ROOT / "ATTEMPT.claim").open("x") as stream:
        stream.write(base.now())
    base.freeze(ROOT / "OWNER.json", dict(at=base.now(), native=base.native_identity(), plan_sha256=base.filehash(ROOT / "PLAN.json")))
    started = time.monotonic(); waited = 0.; owned = False; model = torch = None
    lock = REPO / "results/.gpu.lock"; token = f"{os.getpid()} drive-suggestion-main-v5".encode()
    stopped = threading.Event()
    def deadline():
        if not stopped.wait(plan["max_compute_seconds"] + plan["max_resource_wait_seconds"] + 90):
            base.atomic(ROOT / "FAILED.json", dict(at=base.now(), status="FAILED", reason="hard wall; inspect native identity/lease"))
            os._exit(124)
    threading.Thread(target=deadline, daemon=True).start()
    def guard():
        base.require_resources(base.resource_snapshot())
        if time.monotonic() - started - waited > plan["max_compute_seconds"]:
            raise TimeoutError("Remaining aggregate computation allowance")
    def wait_gpu(floor, acquire=False):
        nonlocal waited, owned
        began = time.monotonic()
        while True:
            snap = base.gpu(); base.require_resources(base.resource_snapshot())
            if snap["free_MiB"] >= floor and snap["temperature_C"] <= plan["maximum_temperature_C"]:
                if not acquire:
                    break
                try:
                    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    try: os.write(fd, token)
                    finally: os.close(fd)
                    owned = True
                    break
                except FileExistsError:
                    pass
            base.atomic(ROOT / "PROGRESS.json", dict(at=base.now(), task="WAITING_RESOURCE", gpu=snap, required_free_MiB=floor))
            if waited + time.monotonic() - began > plan["max_resource_wait_seconds"]:
                raise TimeoutError("Unchanged resource wait allowance")
            time.sleep(30)
        waited += time.monotonic() - began
    def gpu_guard():
        guard(); snap = base.gpu()
        if snap["free_MiB"] < plan["working_floor_MiB"] or snap["temperature_C"] > plan["maximum_temperature_C"]:
            base.freeze(ROOT / "SAFETY_FAILURE.json", dict(at=base.now(), snapshot=snap,
                working_floor_MiB=plan["working_floor_MiB"], maximum_temperature_C=plan["maximum_temperature_C"]))
            raise RuntimeError("GPU safety floor; exact sample retained")
    try:
        while not (ROOT / "MONITOR_READY.json").exists():
            if time.monotonic() - started > 90: raise TimeoutError("Monitor handshake absent")
            time.sleep(.25)
        if base.read(ROOT / "MONITOR_READY.json")["owner_sha256"] != base.filehash(ROOT / "OWNER.json"):
            raise ValueError("Monitor owner mismatch")
        base.freeze(ROOT / "TELEMETRY_START.json", base.crosscheck())
        groups = base.read(base.PILOT / "CASES.json"); census = base.read(base.PILOT / "CENSUS.json")
        reuse_rows = base.read(ROOT / "REUSE.json")
        if base.filehash(ROOT / "REUSE.json") != base.read(ROOT / "PREPARED.json")["reuse_sha256"]:
            raise ValueError("Recovery manifest changed")
        prefix_keys(reuse_rows, groups)
        reuse = {(r["model"], r["session"]): r for r in reuse_rows}
        all_chunks = []; summaries = {}; used_bytes = 0
        for name in base.ORDER:
            base.check_pins(plan["pins"]); guard()
            needed = any(g["cases"] and (name, g["session"]) not in reuse for g in groups)
            if needed:
                if not owned: wait_gpu(plan["cold_floor_MiB"], True)
                if torch is None:
                    import torch as torch_module
                    torch = torch_module; torch.set_num_threads(1)
                    torch.cuda.set_per_process_memory_fraction(plan["allocator_cap_MiB"] * 2**20 / torch.cuda.get_device_properties(0).total_memory)
                base.release_workspace(torch)
                if torch.cuda.memory_allocated() or torch.cuda.memory_reserved(): raise ValueError("Allocator not empty")
                wait_gpu(plan["empty_floor_MiB"])
                from transformers import AutoTokenizer, AutoModelForCausalLM
                path = base.verify_model(base.read(base.MODELS)[name])
                tok = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False, use_fast=True)
                dtype = getattr(torch, plan["dtype_by_model"][name])
                model = AutoModelForCausalLM.from_pretrained(path, local_files_only=True, trust_remote_code=False, torch_dtype=dtype).to("cuda").eval()
                if any(p.device.type != "cuda" or p.dtype != dtype for p in model.parameters()): raise ValueError("Precision/residency mismatch")
                base.freeze(ROOT / name / "TELEMETRY_LOADED.json", base.crosscheck()); gpu_guard()
            count = dict(items=0, eligible=0, target_tokens=0, input_tokens=0); reused = new = 0
            for si, group in enumerate(groups):
                cases = group["cases"]
                if not cases: continue
                guard(); key = (name, group["session"]); old = reuse.get(key)
                base.atomic(ROOT / "PROGRESS.json", dict(at=base.now(), task=name, session=si, total=len(groups), reused_chunks=reused, new_chunks=new))
                if old:
                    source = SOURCE / name / old["file"]
                    value = base.load_checkpoint(source, old, cases, plan["predecessor_plan_sha256"], name)
                    dest = ROOT / name / old["file"]; dest.parent.mkdir(parents=True, exist_ok=True)
                    with dest.open("xb") as stream: stream.write(source.read_bytes())
                    if base.filehash(dest) != old["sha256"]: raise ValueError("Copied checkpoint changed")
                    record = dict(old); rows = value["rows"]; reused += 1
                else:
                    rows = []
                    for case in cases:
                        for condition, context in base.contexts(tok, case["brief"], case["document"]).items():
                            gpu_guard()
                            scores = (base.blocked_score(model, tok, context, case["menu"], torch, block_tokens=32, check=gpu_guard)
                                      if name.startswith("pythia") else base.cached_score(model, tok, context, case["menu"], torch))
                            gpu_guard(); rows.append(dict(key=case["key"], condition=condition, scores=scores, ranks=base.menu_ranks(scores)))
                    payload = dict(model=name, session=group["session"], input_sha256=base.digest(cases), plan_sha256=base.filehash(ROOT / "PLAN.json"), rows=rows)
                    dest = ROOT / name / (base.digest(group["session"])[:20] + ".json.gz")
                    record = base.checkpoint(dest, payload, cases); record.update(session=group["session"], model=name); new += 1
                for field, number in totals(rows).items(): count[field] += number
                used_bytes += record["bytes"]
                if used_bytes > plan["max_output_bytes"]: raise ValueError("Retained byte ceiling")
                all_chunks.append(record); base.atomic(ROOT / "CHUNKS.json", all_chunks)
            check_census(count, census[name])
            summaries[name] = dict(count, reused_chunks=reused, new_chunks=new, original_score_protocol=True)
            base.freeze(ROOT / name / "SUMMARY.json", summaries[name])
            if model is not None:
                del model; model = None; base.release_workspace(torch)
        base.freeze(ROOT / "SUMMARY.json", summaries)
        subprocess.run([str(REPO / ".venv/Scripts/python.exe"), "-X", "utf8", "-B", "-m", "runners.drive.suggestion_resume_v1", "verify"], cwd=REPO, check=True, timeout=1200, creationflags=0x08000000)
        base.check_pins(plan["pins"])
        base.freeze(ROOT / "COMPLETE.json", dict(at=base.now(), status="COMPLETE", fresh_process_verified=True,
            outputs={p.relative_to(ROOT).as_posix(): base.filehash(p) for p in ROOT.rglob("*") if p.is_file() and (p.suffix == ".json" or p.name.endswith(".json.gz")) and p.name not in ("PROGRESS.json", "MONITOR_READY.json")},
            scientific_admission=False, full_P1_complete=False, write_through_required=True))
    except BaseException as exc:
        base.freeze(ROOT / "FAILED.json", dict(at=base.now(), status="FAILED", reason=str(exc), traceback=traceback.format_exc()))
        raise
    finally:
        stopped.set(); model = None; gc.collect()
        try:
            if torch is not None and torch.cuda.is_initialized(): base.release_workspace(torch)
        finally:
            if owned and lock.exists() and lock.read_bytes() == token: lock.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=["prepare", "run", "verify"])
    {"prepare": prepare, "run": run, "verify": verify}[parser.parse_args().action]()
