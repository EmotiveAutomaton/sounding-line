"""Bounded P7 batch-tokenizer feasibility; no model forward or main admission.

DESIGN CHECK: fixed work-count strata from saved census units, never outcomes.
Full native IDs/offsets, target positions, 1024-token crop, grouping and cache
work must equal frozen scalar preparation exactly. Whole-unit costs include
unchanged raw replay. Old checkpoints and the 2700-second census cap remain.
The measured sample is a conditional cost forecast, not whole-corpus coverage.
"""
from __future__ import annotations

import math
import os
import time
from datetime import datetime
from pathlib import Path

from . import timing_p7_work_census as original
from .timing_p7_batched import prepare
from .timing_census import read, write, filehash
from .timing_p6 import write_equal

CONFIG = dict(phase="tokenizer_batch_feasibility", sample_units=8, batch_size=64,
              max_batch_characters=262144, threads=2)
FORECAST_SECONDS = 120
CAP_SECONDS = 360
EXTRA_INPUTS = {"census_plan", "census_paused"}


def prepared_encoding(tokenizer, encoded, prefix, target):
    full = [tokenizer.eos_token_id] + encoded["input_ids"]
    dropped = max(0, len(full)-1024)
    positions = [i+1-dropped for i, (a, b) in enumerate(encoded["offset_mapping"])
                 if b > len(prefix) and a < len(prefix+target)]
    if not positions or min(positions) <= 0:
        raise ValueError("P7 target missing or exceeds context")
    return dict(ids=full[dropped:], positions=positions, dropped=dropped)


def prepare_many(tokenizer, rows, config=CONFIG):
    """Only the tokenizer call is batched; each original full string is intact."""
    if config != CONFIG or any(type(config[k]) is not type(v) for k, v in CONFIG.items()):
        raise ValueError("exact tokenizer feasibility configuration required")
    prepared, encodings, offset = [], [], 0
    while offset < len(rows):
        end, characters = offset, 0
        while end < len(rows) and end-offset < config["batch_size"]:
            length = len(rows[end]["prefix"])+len(rows[end]["target"])
            if end > offset and characters+length > config["max_batch_characters"]:
                break
            characters += length
            end += 1
        texts = [r["prefix"]+r["target"] for r in rows[offset:end]]
        batch = tokenizer(texts, add_special_tokens=False, return_offsets_mapping=True,
                          padding=False, truncation=False)
        if len(batch["input_ids"]) != len(texts) or len(batch["offset_mapping"]) != len(texts):
            raise ValueError("batched tokenizer changed input cardinality")
        for j, row in enumerate(rows[offset:end]):
            encoded = dict(input_ids=batch["input_ids"][j], offset_mapping=batch["offset_mapping"][j])
            prepared.append(prepared_encoding(tokenizer, encoded, row["prefix"], row["target"]))
            encodings.append(encoded)
        offset = end
    return prepared, encodings


def select_units(saved, count=8):
    ordered = sorted(saved, key=lambda pair: (
        sum(x["tokens"]*x["count"] for x in pair[1]["census"]["context_lengths"]), pair[0]))
    if len(ordered) < count:
        raise ValueError("insufficient saved units for fixed cost strata")
    return sorted(ordered[round(i*(len(ordered)-1)/(count-1))][0] for i in range(count))


def reference(inputs, config):
    if config != CONFIG or set(config) != set(CONFIG) or any(type(config[k]) is not type(v) for k,v in CONFIG.items()):
        raise ValueError("exact tokenizer feasibility configuration required")
    source = {k:v for k,v in inputs.items() if k not in EXTRA_INPUTS}
    plan_path, paused_path = Path(inputs["census_plan"]), Path(inputs["census_paused"])
    plan, paused = read(plan_path), read(paused_path)
    if (set(inputs) != set(source)|EXTRA_INPUTS or plan_path.name != "PLAN.json"
            or paused_path != plan_path.parent/"PAUSED.json" or paused["status"] != "PAUSED"
            or plan["module"] != "runners.drive.cards.timing_p7_work_census"
            or plan["config"] != original.CONFIG or plan["inputs"] != source or plan["max_wall_seconds"] != 2700):
        raise ValueError("original paused census identity differs")
    for name, expected in plan["pins"].items():
        if filehash(name) != expected:
            raise ValueError("paused census source pin changed")
    binding, units, roster, p6_output, model = original.reference(source, original.CONFIG)
    old = plan_path.parent/"output"
    if read(old/"BINDING.json") != binding:
        raise ValueError("paused census binding changed")
    paths = sorted(p for p in (old/"units").glob("*.json") if not p.name.endswith(".receipt.json"))
    saved, saved_hashes = [], {}
    for i, path in enumerate(paths):
        if path.name != f"{i:05d}.json":
            raise ValueError("paused census coverage is not a contiguous prefix")
        _, row = original.checkpoint(old, i, original.old.digest(binding), units[i])
        saved.append((i,row))
        saved_hashes[path.name] = filehash(path)
        saved_hashes[path.with_suffix(".receipt.json").name] = filehash(path.with_suffix(".receipt.json"))
    projection = read(old/"FIRST_TENTH.json")
    prior = max(sum(r["seconds"] for _,r in saved),
                (datetime.fromisoformat(paused["at"])-datetime.fromisoformat(plan["at"])).total_seconds())
    if (not math.isfinite(prior) or not 0 <= prior < 2700 or projection["total_units"] != len(units)
            or not math.isfinite(projection["projected_cpu_seconds"]) or projection["projected_cpu_seconds"] <= 0):
        raise ValueError("invalid prior census cost")
    identity = dict(source_binding=binding, saved_hashes=saved_hashes, total_units=len(units),
        saved_units=len(saved), selection=select_units(saved, config["sample_units"]),
        charged_prior_seconds=prior, scalar_census_projection_seconds=projection["projected_cpu_seconds"],
        census_plan_sha256=filehash(plan_path), census_paused_sha256=filehash(paused_path),
        first_tenth_sha256=filehash(old/"FIRST_TENTH.json"), config=config)
    return identity, units, dict(saved), source, roster, p6_output, model


def tokenizer_only(model):
    # Limit the fast-tokenizer Rayon pool as well as the ordinary numeric pools.
    os.environ["RAYON_NUM_THREADS"] = "2"
    os.environ["TOKENIZERS_PARALLELISM"] = "true"
    return original.tokenizer_only(model)


def compare_unit(number, unit, saved, source, roster, p6_output, tokenizer, batched_tokenizer=None):
    tick = time.monotonic()
    rows = original.old.locations(unit, roster, p6_output, source)
    source_seconds = time.monotonic()-tick
    tick = time.monotonic()
    scalar = [prepare(tokenizer,r["prefix"],r["target"]) for r in rows]
    scalar_seconds = time.monotonic()-tick
    tick = time.monotonic()
    batched, encoded = prepare_many(batched_tokenizer if batched_tokenizer is not None else tokenizer, rows)
    batched_seconds = time.monotonic()-tick
    if batched != scalar:
        raise ValueError("P7 batched IDs/positions/crop differ from scalar prepare")
    tick = time.monotonic()
    for row, actual in zip(rows, encoded):
        scalar_encoded = tokenizer(row["prefix"]+row["target"], add_special_tokens=False, return_offsets_mapping=True)
        if (actual["input_ids"] != scalar_encoded["input_ids"]
                or actual["offset_mapping"] != scalar_encoded["offset_mapping"]):
            raise ValueError("P7 full native IDs/offsets differ")
    identity_seconds = time.monotonic()-tick
    tick = time.monotonic()
    census = dict(domain=unit["domain"], identity=unit["identity"],
        locations_sha256=original.old.digest(rows), native_sha256=original.old.digest(batched), **original.work(batched))
    work_seconds = time.monotonic()-tick
    tick = time.monotonic()
    if census != saved["census"] or original.work(scalar) != original.work(batched):
        raise ValueError("P7 saved census/cache-work summary differs")
    identity_seconds += time.monotonic()-tick
    return dict(unit_index=number, census=census, full_native_ids_offsets_sha256=original.old.digest(encoded),
        timings=dict(source_seconds=source_seconds, scalar_prepare_seconds=scalar_seconds,
                     batched_prepare_seconds=batched_seconds, cache_work_and_digest_seconds=work_seconds,
                     identity_validation_seconds=identity_seconds))


def summarize(records, binding, pilot_seconds):
    ratios = []
    for row in records:
        t = row["timings"]
        if any(not math.isfinite(v) or v < 0 for v in t.values()):
            raise ValueError("invalid tokenizer comparison timing")
        common = t["source_seconds"]+t["cache_work_and_digest_seconds"]
        denominator = common+t["scalar_prepare_seconds"]
        if denominator <= 0:
            raise ValueError("undefined whole-unit speed ratio")
        ratios.append((common+t["batched_prepare_seconds"])/denominator)
    ratio = max(ratios)
    # Charge retained execution, this complete comparison plus independent
    # verification, and remaining census execution + full fresh verification.
    fraction = ((binding["total_units"]-binding["saved_units"])/binding["total_units"]+1)/2
    projected = binding["charged_prior_seconds"]+2*pilot_seconds+binding["scalar_census_projection_seconds"]*fraction*ratio
    return dict(state="positive", instrument_only=True, model_forwards_executed=0, main_admitted=False,
        exact_scalar_native_and_work_parity=True, sampled_units=len(records),
        sampled_domains=sorted({r["census"]["domain"] for r in records}),
        worst_observed_whole_unit_batched_over_scalar_ratio=ratio,
        projected_cumulative_census_seconds=projected, original_census_cap_seconds=2700,
        conditionally_fits_census_cap=projected <= 2700,
        limitation="Conditional forecast from eight saved source-work strata, with worst observed whole-unit ratio; unseen units and unrepresented domains remain uncertain. No full P7 six-hour admission.")


def execute(output, inputs, config):
    output = Path(output)
    start = time.monotonic()
    binding, units, saved, source, roster, p6_output, model = reference(inputs, config)
    write_equal(output/"BINDING.json", binding)
    if (output/"PRIMARY.json").exists():
        return verify(output,inputs,config)["primary"]
    prior = read(output/"PROGRESS.json")["active_seconds"] if (output/"PROGRESS.json").exists() else 0.
    elapsed = lambda: prior+time.monotonic()-start
    # Independent native instances prevent the scalar pass from warming the
    # batched arm's internal BPE cache. Both see the same fixed unit order.
    tokenizer, batched_tokenizer, records = tokenizer_only(model), tokenizer_only(model), []
    for number in binding["selection"]:
        path=output/"units"/f"{number:05d}.json"
        if path.exists():
            if read(path.with_suffix(".receipt.json"))["sha256"] != filehash(path):
                raise ValueError("tokenizer pilot checkpoint changed")
            record=read(path)
        else:
            record=compare_unit(number,units[number],saved[number],source,roster,p6_output,tokenizer,batched_tokenizer)
            write(path,record);write(path.with_suffix(".receipt.json"),dict(sha256=filehash(path)))
        records.append(record)
        from runners.stage14.common import atomic
        atomic(output/"PROGRESS.json",dict(completed_units=len(records),total_units=len(binding["selection"]),active_seconds=elapsed()))
        if not (output/"FIRST_TENTH.json").exists():
            projection=2*elapsed()*len(binding["selection"])/len(records)
            write(output/"FIRST_TENTH.json",dict(completed_units=len(records),total_units=len(binding["selection"]),
                elapsed_seconds=elapsed(),projected_cpu_seconds=projection,forecast_cpu_seconds=FORECAST_SECONDS))
            if projection > 2*FORECAST_SECONDS:
                atomic(output/"YIELD_REQUEST.json",dict(reason="first_tenth_projection_exceeds_twice_forecast"))
        if elapsed()>CAP_SECONDS:raise RuntimeError("bounded tokenizer comparison cap exceeded")
        if (output/"YIELD_REQUEST.json").exists():return dict(status="yielded",completed_units=len(records),model_forwards_executed=0)
    timing=dict(wall_seconds=elapsed(),forecast_cpu_seconds=FORECAST_SECONDS,cap_seconds=CAP_SECONDS)
    result=summarize(records,binding,timing["wall_seconds"])
    write(output/"TIMING.json",timing);write(output/"RECORDS.json",records);write(output/"PRIMARY.json",result)
    return result


def verify(output, inputs, config):
    output=Path(output);start=time.monotonic()
    binding,units,saved,source,roster,p6_output,model=reference(inputs,config)
    if read(output/"BINDING.json")!=binding:raise ValueError("tokenizer comparison binding changed")
    records=read(output/"RECORDS.json");tokenizer,batched_tokenizer=tokenizer_only(model),tokenizer_only(model)
    if [r["unit_index"] for r in records]!=binding["selection"]:raise ValueError("tokenizer comparison coverage changed")
    for record in records:
        number=record["unit_index"];actual=compare_unit(number,units[number],saved[number],source,roster,p6_output,tokenizer,batched_tokenizer)
        if {k:v for k,v in actual.items() if k!="timings"}!={k:v for k,v in record.items() if k!="timings"}:
            raise ValueError("tokenizer comparison fresh source reconstruction differs")
        path=output/"units"/f"{number:05d}.json"
        if read(path)!=record or read(path.with_suffix(".receipt.json"))["sha256"]!=filehash(path):
            raise ValueError("tokenizer comparison retained checkpoint differs")
    timing=read(output/"TIMING.json")
    if not math.isfinite(timing["wall_seconds"]) or timing["wall_seconds"]<0 or timing["wall_seconds"]+time.monotonic()-start>CAP_SECONDS:
        raise RuntimeError("bounded tokenizer execute/verify cap exceeded")
    primary=summarize(records,binding,timing["wall_seconds"])
    if primary!=read(output/"PRIMARY.json"):raise ValueError("tokenizer comparison summary differs")
    return dict(verified=True,primary=primary,fresh_source_reconstruction=True,main_admitted=False)
