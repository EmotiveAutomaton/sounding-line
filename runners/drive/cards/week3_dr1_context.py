"""Separate DR1 fixed-roster identification diagnostic using approved WA0.h1.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-29.
NULL: identical or prompt-only features cannot beat independent prompt context.
ALTERNATIVE: stable person fingerprints can clear both rebuilt references.
No donor overlaps a scored gallery; missing fixed support refuses admission.
This session-mean, disjoint-prompt diagnostic is not DR1's overlapping pooled
endpoint. The legacy leave-writer-out construction is retained as diagnostic.
"""
from pathlib import Path
import time

import numpy as np
from threadpoolctl import threadpool_limits

from . import week3_identification as base
from . import week3_identification_crossfit as crossfit
from . import week3_dr1_ranks as ranks
from . import week_directed_reading as original
from .events_d4_sources import bind_completed
from .menus_io import read, sha256, write
from .timing_p6 import gzip_equal, gzread, progress

CONFIG = dict(card="DR1-week3-context", schema=1, seed=20261026,
              permutations=1000, bootstrap_draws=2000, context_folds=3)
CONFIGS = {mode:dict(CONFIG, mode=mode, permutations=100 if mode == "cost" else 1000)
           for mode in ("constructed", "cost", "human")}


def feature_rows(rows, dictionary, writers):
    if writers != sorted(set(writers)) or len(writers) < 6:
        raise ValueError("Fixed original eligible roster required")
    result = [dict(session=r["session"], writer=r["writer"], prompt=r["prompt"],
                   timestamp=r["timestamp"], features={"style":original.profile([r], dictionary)["style"]})
              for r in sorted(rows, key=lambda r:r["session"]) if r["writer"] in writers]
    if {r["writer"] for r in result} != set(writers):
        raise ValueError("Original population missing")
    return result


def analyze(rows, writers, config, checkpoint=lambda *args:None):
    if sorted({r["writer"] for r in rows}) != writers:
        raise ValueError("Fixed roster differs")
    result, detail = crossfit.analyze_group(rows, config, {"style":writers}, checkpoint)
    # The specified old construction is retained, without endorsing its logic.
    x, slices = base.feature_matrix(rows)
    ww, groups, _, _ = base.split(rows)
    literal_profiles = base.means(base.context_rows(rows, x), groups, ww)
    literal = base.identify(literal_profiles, ww, writers, slices["style"])
    return dict(independent_context=result["style"],
                literal_leave_writer_out_diagnostic=literal,
                literal_licenses_claim=False, writers=len(writers), sessions=len(rows),
                operator="session-mean style; distinct from original pooled DR1",
                scope="all original eligible writers; disjoint prompt halves; three fixed donor/probe/gallery roles",
                routing_claim=False), detail


def constructed_rows(kind):
    if kind not in ("constant", "prompt", "person"):
        raise ValueError("Unknown construction")
    rows = []
    for wi in range(12):
        for prompt in range(4):
            for repetition in range(2):
                values = np.zeros(16)
                if kind == "constant": values[0] = 1
                else:
                    values[12+prompt] = 1
                    if kind == "person": values[wi] = 10
                rows.append(dict(session=f"w{wi:02}-p{prompt}-{repetition}", writer=f"w{wi:02}",
                                 prompt=f"p{prompt}", timestamp=prompt*2+repetition,
                                 features={"style":values.tolist()}))
    return rows


def calibration(config, checkpoint):
    results = {}; details = {}
    for kind in ("constant", "prompt", "person"):
        rows = constructed_rows(kind); writers = sorted({r["writer"] for r in rows})
        results[kind], details[kind] = analyze(rows, writers, config,
            lambda fold, done, total:checkpoint(kind+"-fold-"+str(fold), done, total))
    gates = dict(constant_no_person_claim=not results["constant"]["independent_context"]["pass_both"],
                 prompt_no_person_claim=not results["prompt"]["independent_context"]["pass_both"],
                 person_detected=results["person"]["independent_context"]["pass_both"],
                 complete_null_banks=all(r["independent_context"].get("permutation", {}).get("state") == "complete"
                                         for r in results.values()))
    return dict(passed=all(gates.values()), gates=gates, worlds=results,
                permutations=config["permutations"], human_claim=False), details


def bound_summary(completion, name):
    complete = Path(completion)
    bind_completed(complete, complete.parent/"output"/name)
    return read(complete.parent/"output"/name)


def load(inputs, config):
    expected = {"dr1_completion", "calibration_completion"}
    if config["mode"] == "human": expected |= {"cost_completion", "cost_landing"}
    if set(inputs) != expected: raise ValueError("Complete frozen input set required")
    cal = bound_summary(inputs["calibration_completion"], "SUMMARY.json")
    if not cal["passed"] or cal["permutations"] != 1000:
        raise ValueError("Full passing context calibration required")
    if config["mode"] == "human":
        admission = read(inputs["cost_landing"])
        if (not admission["full_write_through"] or not admission["admitted"]
                or admission["completion_sha256"] != sha256(inputs["cost_completion"])):
            raise ValueError("Complete measured cost admission required")
        bound_summary(inputs["cost_completion"], "FORECAST.json")
    rows, dictionary, primary, _ = ranks.load_original(inputs["dr1_completion"])
    writers = [r["writer"] for r in primary["writer_rows"]]
    return feature_rows(rows, dictionary, writers), writers


def run(output, inputs, config, verification=False):
    if config not in CONFIGS.values(): raise ValueError("Frozen context configuration required")
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    started = time.process_time()
    def checkpoint(phase, done, total):
        if (output.parent/"STOP").exists() or (output/"YIELD_REQUEST.json").exists():
            raise InterruptedError("Context stop/yield requested")
        if done % 25 == 0 or done == total:
            progress(output/"PROGRESS.json", dict(phase=("verify-" if verification else "")+str(phase), done=done, total=total))
    with threadpool_limits(limits=2):
        if config["mode"] == "constructed":
            if inputs: raise ValueError("Constructed mode accepts no human input")
            result, detail = calibration(config, checkpoint)
        else:
            rows, writers = load(inputs, config)
            result, detail = analyze(rows, writers, config,
                lambda fold, done, total:checkpoint("fold-"+str(fold), done, total))
            if config["mode"] == "cost":
                # Timing artifacts are not scientific verdicts; retain raw detail privately.
                result = dict(mode="cost", writers=len(writers), sessions=len(rows),
                              permutations=config["permutations"], scientific_admission=False)
    binding = dict(config=config, inputs={k:sha256(v) for k, v in inputs.items()})
    for name, value in (("SUMMARY.json", result), ("BINDINGS.json", binding)):
        if verification:
            if read(output/name) != value: raise ValueError("Fresh context replay differs: "+name)
        else: write(output/name, value)
    if verification:
        if gzread(output/"DETAIL.json.gz") != detail: raise ValueError("Fresh context detail differs")
    else: gzip_equal(output/"DETAIL.json.gz", detail)
    elapsed = time.process_time()-started
    write(output/("VERIFY_TIMING.json" if verification else "EXECUTE_TIMING.json"), dict(cpu_seconds=elapsed))
    if verification and config["mode"] == "cost":
        slower = max(elapsed, read(output/"EXECUTE_TIMING.json")["cpu_seconds"])
        write(output/"FORECAST.json", dict(full_cpu_seconds=2*3*10*slower+120,
              both_passes=True, safety_factor=3, complete_references=1000,
              rule="slower full-gallery 100-draw pass times ten, execution and replay, factor three, plus120"))
    return dict(verified=True, full_fresh_replay=True) if verification else dict(status="complete")


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
