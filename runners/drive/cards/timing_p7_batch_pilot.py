"""Bounded causal-batching comparison against the complete frozen P7 pilot.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-18. NULL and ALTERNATIVE scientific
effects cannot alter this validation sample. Every original native loss must
agree within 1e-4, with exact IDs, crop, coverage and finite nonnegative values.
Changed source/checkpoint or absent fresh verification refuses. Faster execution
does not admit main: the full workload's context lengths need cost coverage.
"""
from __future__ import annotations

from pathlib import Path
import time

from . import timing_p7_admitted as old
from .timing_p7 import CachedScorer
from .timing_p7_batched import compare, prepare, score_many
from .timing_p6 import gzread, gzwrite, write_equal
from .timing_census import read, write, filehash

CONFIG = {"phase": "batch_pilot"}


def reference(inputs, config):
    if config != CONFIG or set(inputs) != {"original_pilot"}:
        raise ValueError("P7 batching admits only the fixed pilot")
    root = Path(inputs["original_pilot"])
    complete, plan = read(root/"COMPLETE.json"), read(root/"PLAN.json")
    if (complete.get("status") != "COMPLETE" or not complete.get("fresh_process_verified")
            or plan.get("module") != "runners.drive.cards.timing_p7_admitted"
            or plan.get("config") != old.CONFIG
            or not read(root/"VERIFIED.json").get("verified")):
        raise ValueError("P7 batching requires the verified original pilot")
    for path, expected in plan["pins"].items():
        if filehash(path) != expected:
            raise ValueError("P7 frozen pilot source changed")
    for name, expected in complete["outputs"].items():
        old.bound_file(root, name, expected)
    binding, roster, p6, model = old.source(plan["inputs"], old.CONFIG)
    index = read(root/"output/P7_INDEX.json")
    units = []
    for unit in binding["units"]:
        matches = [r for r in index if r["domain"] == unit["domain"]]
        if len(matches) != 1:
            raise ValueError("P7 pilot domain coverage changed")
        locations = old.locations(unit, roster, p6, plan["inputs"])
        words = gzread(root/"output"/matches[0]["file"])["words"]
        if len(words) != len(locations) or any(w["index"] != r["index"] for w,r in zip(words,locations)):
            raise ValueError("P7 pilot target coverage changed")
        units.append(dict(domain=unit["domain"], rows=locations, expected=words))
    return dict(original_complete_sha256=filehash(root/"COMPLETE.json"),
                original_plan_sha256=filehash(root/"PLAN.json"), source=old.digest(binding)), units, model, binding["totals"]


def reduction(index):
    return dict(card="P7-batch-pilot", instrument_only=True, scientific_admission=False,
                main_admitted=False, targets=sum(r["targets"] for r in index),
                max_token_error=max(r["max_token_error"] for r in index),
                domains=[r["domain"] for r in index], tolerance=1e-4)


def validate_words(saved, unit, tokenizer=None):
    if len(saved) != len(unit["rows"]):
        raise ValueError("P7 batched saved coverage changed")
    errors = []
    for word, row, expected in zip(saved, unit["rows"], unit["expected"]):
        if word["index"] != row["index"] or word["is_word"] != row["is_word"]:
            raise ValueError("P7 batched target linkage changed")
        errors.append(compare(word, expected))
        if tokenizer is not None:
            native = prepare(tokenizer, row["prefix"], row["target"])
            if (word["prefix_tokens_dropped"] != native["dropped"]
                    or word["native_token_ids"] != [native["ids"][i] for i in native["positions"]]):
                raise ValueError("P7 batched reconstructed source identity changed")
    return max(errors)


def execute(output, inputs, config):
    output = Path(output)
    binding, units, manifest, totals = reference(inputs, config)
    if (output/"BATCH_PRIMARY.json").exists():
        verify(output, inputs, config)
        return read(output/"BATCH_PRIMARY.json")
    write_equal(output/"BINDING.json", binding)
    started = time.monotonic()
    model, tokenizer, torch = old.load_model(manifest)
    loading = time.monotonic() - started
    index = []
    for unit in units:
        name = unit["domain"] + ".json.gz"
        receipt = output/(unit["domain"] + ".receipt.json")
        if receipt.exists():
            row = read(receipt)
            old.bound_file(output, name, row["sha256"])
            saved = gzread(output/name)
            if saved["binding"] != old.digest(binding):
                raise ValueError("P7 batch checkpoint binding changed")
            if validate_words(saved["words"], unit, tokenizer) != row["max_token_error"]:
                raise ValueError("P7 batch checkpoint error changed")
        else:
            begin = time.monotonic()
            scores, cost = score_many(model, tokenizer, torch, unit["rows"])
            elapsed = time.monotonic() - begin
            words = [dict(index=r["index"], is_word=r["is_word"], **s) for r,s in zip(unit["rows"],scores)]
            error = validate_words(words, unit, tokenizer)
            gzwrite(output/name, dict(binding=old.digest(binding), words=words))
            row = dict(domain=unit["domain"], file=name, sha256=filehash(output/name),
                       seconds=elapsed, max_token_error=error, **cost)
            write_equal(receipt, row)
        index.append(row)
        if not (output/"FIRST_TENTH.json").exists():
            write(output/"FIRST_TENTH.json", dict(completed=len(unit["rows"]),
                total=sum(len(u["rows"]) for u in units),
                projected_cpu_seconds=loading + row["seconds"]*2))
        if (output/"YIELD_REQUEST.json").exists():
            return dict(status="yielded", complete_units=len(index), scientific_admission=False)
    primary = reduction(index)
    timing = dict(model_load_seconds=loading, by_domain=index,
                  projected_scoring_seconds=sum(r["seconds"]/r["targets"]*totals[r["domain"]] for r in index),
                  excludes_source_replay_and_verification=True, full_context_cost_coverage=False,
                  main_admitted=False)
    write_equal(output/"BATCH_INDEX.json", index)
    write_equal(output/"BATCH_TIMING.json", timing)
    write_equal(output/"BATCH_PRIMARY.json", primary)
    return primary


def verify(output, inputs, config):
    output = Path(output)
    binding, units, manifest, totals = reference(inputs, config)
    if read(output/"BINDING.json") != binding:
        raise ValueError("P7 batch source binding changed")
    index = read(output/"BATCH_INDEX.json")
    if [r["domain"] for r in index] != [u["domain"] for u in units]:
        raise ValueError("P7 batch domain coverage changed")
    model, tokenizer, torch = old.load_model(manifest)
    direct = CachedScorer(model, tokenizer, torch)
    fresh_errors = []
    for row, unit in zip(index, units):
        old.bound_file(output, row["file"], row["sha256"])
        saved = gzread(output/row["file"])
        if saved["binding"] != old.digest(binding) or row != read(output/(row["domain"]+".receipt.json")):
            raise ValueError("P7 batch checkpoint binding changed")
        words = saved["words"]
        error = validate_words(words, unit, tokenizer)
        if error != row["max_token_error"] or len(words) != row["targets"]:
            raise ValueError("P7 batch saved reduction changed")
        for i in sorted({0, len(words)//2, len(words)-1}):
            source = unit["rows"][i]
            fresh_errors.append(direct.direct_check(source["prefix"], source["target"], words[i]))
    primary = reduction(index)
    timing = read(output/"BATCH_TIMING.json")
    projected = sum(r["seconds"]/r["targets"]*totals[r["domain"]] for r in index)
    if (read(output/"BATCH_PRIMARY.json") != primary or timing["by_domain"] != index
            or timing["projected_scoring_seconds"] != projected or timing["main_admitted"]):
        raise ValueError("P7 batch primary/timing changed")
    return dict(verified=True, all_original_target_losses_compared=True,
                reconstructed_targets=primary["targets"], max_token_error=primary["max_token_error"],
                fresh_direct_checks=len(fresh_errors), fresh_direct_max_error=max(fresh_errors),
                main_admitted=False, scientific_admission=False)
