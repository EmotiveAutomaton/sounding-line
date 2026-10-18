"""Full native-context work census for the frozen P7 hybrid; no model forwards.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-18 for P7. Scientific NULL and
ALTERNATIVE cannot affect this input-only census. Exact coverage, source hashes,
native token positions and independent replay must agree; changed/missing input
or checkpoint refuses. A complete census is not a timing or scientific admission.
Original scorers, pilot outputs, context length and loss tolerance remain frozen.
"""
from collections import Counter
import math
from pathlib import Path
import time

from . import timing_p7_admitted as old
from .timing_census import read, write, filehash
from .timing_p6 import write_equal
from .timing_p7_batched import prepare, groups

CONFIG = {"phase": "native_work_census"}


def reference(inputs, config):
    if config != CONFIG:
        raise ValueError("Only the fixed P7 native-work census is supported")
    binding, roster, p6_output, model = old.source(inputs, old.CONFIG)
    typed = read(p6_output / "P6_INDEX.json")
    jokes = read(inputs["jester_texts"])
    units = [dict(domain="typed", identity=r["session"], source=r)
             for r in sorted(typed, key=lambda r: r["session"])]
    units += [dict(domain="jester", identity=str(r["joke_id"]), source=r)
              for r in sorted(jokes, key=lambda r: r["joke_id"])]
    binding = dict(config=config, source_binding=binding,
                   units_sha256=old.digest(units), units=len(units))
    return binding, units, roster, p6_output, model


def tokenizer_only(model):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model["tokenizer_path"],
        local_files_only=True, use_fast=True, trust_remote_code=False)
    if not tokenizer.is_fast or tokenizer.eos_token_id is None:
        raise ValueError("P7 census needs the authenticated fast tokenizer")
    return tokenizer


def work(prepared):
    """Simulate exact cache identity transitions, not GPU/CPU elapsed time."""
    batches = groups(prepared)
    previous = []
    shapes, lengths = Counter(), Counter()
    forwards = tokens = reused = 0
    for batch in batches:
        ids = batch["ids"]
        common = 0
        for before, after in zip(previous, ids):
            if before != after:
                break
            common += 1
        if previous and common == len(ids):
            reused += 1
        else:
            reuse = max(0, common - 1) if previous else 0
            fresh = len(ids) - reuse
            forwards += 1
            tokens += fresh
            shapes[(len(ids), fresh)] += 1
        previous = ids
    for row in prepared:
        if (not row["positions"] or min(row["positions"]) <= 0
                or max(row["positions"]) >= len(row["ids"]) or len(row["ids"]) > 1024
                or row["dropped"] < 0):
            raise ValueError("P7 census invalid native target")
        lengths[len(row["ids"])] += 1
    return dict(targets=len(prepared), groups=len(batches), forwards=forwards,
        no_forward_groups=reused, forward_tokens=tokens,
        cropped_targets=sum(r["dropped"] > 0 for r in prepared),
        max_dropped_tokens=max((r["dropped"] for r in prepared), default=0),
        native_target_tokens=sum(len(r["positions"]) for r in prepared),
        shapes=[dict(context=n, new_tokens=k, count=v) for (n,k),v in sorted(shapes.items())],
        context_lengths=[dict(tokens=n, count=v) for n,v in sorted(lengths.items())])


def unit_census(unit, rows, tokenizer):
    prepared = [prepare(tokenizer, r["prefix"], r["target"]) for r in rows]
    return dict(domain=unit["domain"], identity=unit["identity"],
                locations_sha256=old.digest(rows), native_sha256=old.digest(prepared),
                **work(prepared))


def reduce_units(records):
    domains = {}
    for domain in sorted({r["domain"] for r in records}):
        rows = [r for r in records if r["domain"] == domain]
        shapes, lengths = Counter(), Counter()
        for r in rows:
            shapes.update({(s["context"],s["new_tokens"]):s["count"] for s in r["shapes"]})
            lengths.update({s["tokens"]:s["count"] for s in r["context_lengths"]})
        domains[domain] = dict(units=len(rows), **{k:sum(r[k] for r in rows) for k in
            ("targets","groups","forwards","no_forward_groups","forward_tokens","cropped_targets","native_target_tokens")},
            max_dropped_tokens=max(r["max_dropped_tokens"] for r in rows),
            shapes=[dict(context=n,new_tokens=k,count=v) for (n,k),v in sorted(shapes.items())],
            context_lengths=[dict(tokens=n,count=v) for n,v in sorted(lengths.items())])
    return dict(instrument_only=True, main_admitted=False, model_forwards_executed=0,
                units=len(records), targets=sum(r["targets"] for r in records), domains=domains,
                limitation="Native work counts are not wall-clock estimates or scientific scores")


def checkpoint(output, number, binding_hash, unit):
    path = output / "units" / f"{number:05d}.json"
    if not path.exists():
        return path, None
    receipt = read(path.with_suffix(".receipt.json"))
    if filehash(path) != receipt["sha256"]:
        raise ValueError("P7 census checkpoint hash changed")
    saved = read(path)
    if (saved["binding"] != binding_hash or saved["unit_sha256"] != old.digest(unit)
            or saved["census"]["identity"] != unit["identity"]
            or saved["census"]["domain"] != unit["domain"]
            or not math.isfinite(saved["seconds"]) or saved["seconds"] < 0):
        raise ValueError("P7 census checkpoint binding changed")
    return path, saved


def execute(output, inputs, config):
    output = Path(output)
    start = time.monotonic()
    binding, units, roster, p6_output, model = reference(inputs, config)
    write_equal(output / "BINDING.json", binding)
    if (output / "CENSUS.json").exists():
        return verify(output, inputs, config)["primary"]
    tokenizer = tokenizer_only(model)
    overhead = time.monotonic() - start
    records, index, charged = [], [], 0.
    for i, unit in enumerate(units):
        path, saved = checkpoint(output, i, old.digest(binding), unit)
        if saved is None:
            tick = time.monotonic()
            rows = old.locations(unit, roster, p6_output, inputs)
            census = unit_census(unit, rows, tokenizer)
            saved = dict(binding=old.digest(binding), unit_sha256=old.digest(unit),
                         census=census, seconds=time.monotonic()-tick)
            write(path, saved)
            write(path.with_suffix(".receipt.json"), dict(sha256=filehash(path)))
        charged += saved["seconds"]
        records.append(saved["census"])
        index.append(dict(file=path.relative_to(output).as_posix(), sha256=filehash(path)))
        if len(records) >= math.ceil(len(units)/10) and not (output / "FIRST_TENTH.json").exists():
            write(output / "FIRST_TENTH.json", dict(completed_units=len(records), total_units=len(units),
                projected_cpu_seconds=2*(overhead+charged*len(units)/len(records)),
                basis="Sorted source units; projected complete census plus fresh full reconstruction, not model execution"))
        if (output / "YIELD_REQUEST.json").exists():
            return dict(status="yielded", completed_units=len(records), model_forwards_executed=0)
    result = reduce_units(records)
    write(output / "INDEX.json", index)
    write(output / "CENSUS.json", result)
    return result


def verify(output, inputs, config):
    output = Path(output)
    binding, units, roster, p6_output, model = reference(inputs, config)
    if read(output / "BINDING.json") != binding:
        raise ValueError("P7 census input binding changed")
    index = read(output / "INDEX.json")
    if len(index) != len(units) or len(list((output/"units").glob("[0-9]*.json"))) != 2*len(units):
        raise ValueError("P7 census unit coverage changed")
    tokenizer, records = tokenizer_only(model), []
    for i, (unit, entry) in enumerate(zip(units, index)):
        path, saved = checkpoint(output, i, old.digest(binding), unit)
        if saved is None or entry != dict(file=path.relative_to(output).as_posix(),sha256=filehash(path)):
            raise ValueError("P7 census index changed")
        actual = unit_census(unit, old.locations(unit, roster, p6_output, inputs), tokenizer)
        if actual != saved["census"]:
            raise ValueError("P7 census fresh source reconstruction changed")
        records.append(actual)
    primary = reduce_units(records)
    if primary != read(output / "CENSUS.json"):
        raise ValueError("P7 census primary changed")
    return dict(verified=True, primary=primary, fresh_source_reconstruction=True,
                reconstructed_units=len(units), main_admitted=False)
