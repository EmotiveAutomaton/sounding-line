"""D30.p with the October 18 repeated and paired control contract.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-6 reread October 19. A planted
local-marker slowing must remain positive and a reversed effect negative.
Identical paired designs must give exactly zero own-minus-fake, including its
interval; unsupported controls are invalid, never null. The 200 within-writer
outcome permutations must have finite complete coverage; absolute mean > .25 SD
flags pipeline bias regardless of the primary. Positive bias is not a pass under
the alternative. No failed fit/draw is discarded. All source, row, checkpoint,
native replay and budget gates fail closed. No scientific extension is licensed.
"""
from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np

from . import timing_d30_crossed_main as legacy
from . import timing_d30_crossed as pilot
from . import crossed_reml_stable as stable
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal
from .timing_stats import bind, check_binding
from runners.stage14.common import atomic, freeze

CONFIG = dict(card="D30.p-week", bootstrap_draws=2000, permutations=200,
              seed=20261017, permutation_seed=20261018)
FORECAST_SECONDS = legacy.FORECAST_SECONDS
CAP_SECONDS = legacy.CAP_SECONDS
ARMS = ("primary", "label_shuffle", "paired_own", "paired_fake")
BLOCK = 25


def paired_designs(rows, mode, primary):
    """Freeze nuisance covariates and real writer/marker intercept identities.

    Only the target classification is rebuilt from reassigned session histories.
    Pair by original occurrence index, never token text or sorted marker strings.
    Classification unsupported after reassignment is an explicit population gap.
    """
    indexed = [dict(r, source_index=i) for i, r in enumerate(rows)]
    matrix, eligible, _ = legacy.design(indexed, mode)
    if matrix != primary:
        raise ValueError("primary differs from admitted crossed design")
    rng = np.random.default_rng(CONFIG["seed"])
    shuffled = pilot.original.shuffle_marker_labels(eligible, rng)
    sessions = sorted({r["session"] for r in rows})
    owner = {r["session"]: r["writer"] for r in rows}
    if any(owner[r["session"]] != r["writer"] for r in rows):
        raise ValueError("one session has multiple real owners")
    assignment = dict(zip(sessions, rng.permutation([owner[s] for s in sessions]).tolist()))
    labels, evidence = pilot.original.classify_markers(
        [dict(r, writer=assignment[r["session"]]) for r in rows])
    keep = [i for i, r in enumerate(eligible) if (assignment[r["session"]], r["marker"]) in labels]
    own = {k: [v[i] for i in keep] for k, v in primary.items()}
    fake = dict(own, x=[[int(labels[assignment[eligible[i]["session"]], eligible[i]["marker"]]["label"] == "local")]
                       + primary["x"][i][1:] for i in keep])
    invalid = None
    try:
        # Structural support checks only. A numerical failure later is not rescued.
        pilot.prepare(**own)
        pilot.prepare(**fake)
    except ValueError as exc:
        invalid = str(exc)
    matrices = dict(primary=primary,
        label_shuffle=dict(primary, x=[[int(label == "local")] + x[1:] for label, x in zip(shuffled, primary["x"])]),
        paired_own=None if invalid else own, paired_fake=None if invalid else fake)
    return matrices, dict(session_writer_assignment=assignment, fake_marker_evidence=evidence,
        primary_source_indices=[r["source_index"] for r in eligible], paired_primary_indices=keep,
        primary_occurrences=len(eligible), paired_occurrences=len(keep), dropped_occurrences=len(eligible)-len(keep),
        paired_real_writers=len(set(own["writers"])), paired_invalid_reason=invalid,
        frozen_nuisance="original covariates including own-marker count and real writer/marker intercept identities",
        changed_field="local/pervasive indicator rebuilt from the fixed reassigned session histories")


def source(inputs, config):
    if config != CONFIG or any(type(config.get(k)) is not type(v) for k, v in CONFIG.items()):
        raise ValueError("exact week crossed configuration required")
    old, original_evidence = legacy.source(inputs, legacy.CONFIG)
    saved = gzread(Path(inputs["extension_completion"]).parent / "output/D30_INTERMEDIATES.json.gz")
    matrices, evidence = paired_designs(saved["rows"], saved["timing_mode"], old["primary"])
    if matrices["label_shuffle"] != old["label_shuffle"]:
        raise ValueError("fixed label control changed")
    evidence.update(charged_pilot_seconds=original_evidence["charged_pilot_seconds"],
                    pilot_point=original_evidence["pilot_point"],
                    timing_mode=original_evidence["timing_mode"],
                    timing_control_writer_differences=original_evidence["timing_control_writer_differences"])
    return matrices, evidence


def checked_fit(matrix):
    value = stable.fit(**matrix)
    if not value.get("converged") or not math.isfinite(value["effect"]):
        raise ValueError("incomplete/nonfinite crossed fit")
    return value


def reference(point, values):
    a = np.asarray(values, float)
    if len(a) < 2 or not np.isfinite(a).all() or not math.isfinite(point):
        raise ValueError("incomplete permutation reference")
    mean, sd = float(a.mean()), float(a.std(ddof=1))
    low, high = np.quantile(a, [.025, .975]).tolist()
    return dict(permutations=len(a), upper_tail_permutation_p=(1+int(np.count_nonzero(a >= point)))/(1+len(a)),
        mean=mean, sd=sd, ci_low=low, ci_high=high, bias_flag=abs(mean) > .25*sd,
        bias_rule="absolute permutation mean greater than one quarter of sample SD; exact zero/zero passes",
        exchangeability_limit="raw outcome shuffle destroys nuisance associations too; descriptive, not causal")


def compute(matrices, config, output=None, checkpoint=None, fit_function=None):
    fitter = checked_fit if fit_function is None else fit_function
    active = tuple(name for name in ARMS if matrices[name] is not None)
    if "primary" not in active or (("paired_own" in active) != ("paired_fake" in active)):
        raise ValueError("incomplete paired arm coverage")
    if "paired_own" in active:
        own, fake = matrices["paired_own"], matrices["paired_fake"]
        if any(own[k] != fake[k] for k in ("y", "writers", "markers")) or any(a[1:] != b[1:] for a, b in zip(own["x"], fake["x"])):
            raise ValueError("paired rows or nuisance covariates differ")
    points = {name: fitter(matrices[name]) if name in active else None for name in ARMS}
    samples = {name: [] for name in ARMS}
    groups = {name: legacy.writer_groups(matrices[name]) for name in active}
    rngs = {name: np.random.default_rng(config["seed"]) for name in active}
    binding = legacy.digest(dict(matrices=matrices, config=config))

    def blocks(phase, count, generate):
        directory = Path(output) / phase if output else None
        if directory:
            expected = [f"block-{i:05d}.json" for i in range(0, count, BLOCK)]
            existing = sorted(p.name for p in directory.glob("block-*.json") if not p.name.endswith(".receipt.json"))
            receipts = {p.name for p in directory.glob("*.receipt.json")}
            if existing != expected[:len(existing)] or receipts != {n.replace(".json", ".receipt.json") for n in existing}:
                raise ValueError("checkpoint sequence/receipt coverage differs")
        for start in range(0, count, BLOCK):
            stop = min(start+BLOCK, count)
            path = directory / f"block-{start:05d}.json" if directory else None
            retained = None
            if path and path.exists():
                if read(path.with_suffix(".receipt.json"))["sha256"] != filehash(path):
                    raise ValueError("checkpoint bytes changed")
                retained = read(path)
                if (retained.get("binding") != binding or retained.get("phase") != phase
                        or retained.get("start") != start or retained.get("stop") != stop or len(retained.get("values", [])) != stop-start):
                    raise ValueError("checkpoint binding/coverage differs")
            values = []
            for j in range(start, stop):
                # Generate sample indices even for retained blocks, preserving RNG.
                values.append(generate(None if retained is None else retained["values"][j-start]))
            record = dict(binding=binding, phase=phase, start=start, stop=stop, values=values)
            if path:
                freeze(path, record)
                freeze(path.with_suffix(".receipt.json"), dict(sha256=filehash(path)))
            if checkpoint:
                checkpoint(phase, stop, count)
            yield values

    def bootstrap(retained):
        values = {}
        if retained is not None and set(retained) != set(active):
            raise ValueError("retained bootstrap arm coverage differs")
        for name in active:
            chosen = rngs[name].integers(0, len(groups[name]), len(groups[name]))
            fit = retained[name] if retained is not None else fitter(legacy.resample(matrices[name], chosen, groups[name]))
            if not fit.get("converged") or not math.isfinite(fit["effect"]):
                raise ValueError("invalid saved fit")
            values[name] = fit
        return values

    for block in blocks("bootstrap", config["bootstrap_draws"], bootstrap):
        for row in block:
            for name in active:
                samples[name].append(row[name])
    rng = np.random.default_rng(config["permutation_seed"])
    primary = matrices["primary"]
    def permute(retained):
        indices = list(range(len(primary["y"])))
        for group in groups["primary"]:
            for i, j in zip(group, rng.permutation(group).tolist()):
                indices[i] = j
        if retained is not None:
            if retained["indices_sha256"] != legacy.digest(indices) or not retained["fit"].get("converged") or not math.isfinite(retained["fit"]["effect"]):
                raise ValueError("saved permutation differs")
            return retained
        return dict(indices_sha256=legacy.digest(indices), fit=fitter(dict(primary, y=[primary["y"][i] for i in indices])))
    permutations = [row for block in blocks("permutations", config["permutations"], permute) for row in block]
    return dict(points=points, bootstrap=samples, permutations=permutations)


def summarize(matrices, evidence, fitted, config):
    points, samples = fitted["points"], fitted["bootstrap"]
    reports = {name: legacy.contrast(points[name]["effect"], [r["effect"] for r in samples[name]],
        len(set(matrices[name]["writers"])), len(matrices[name]["y"])) for name in ARMS if matrices[name] is not None}
    if matrices["paired_own"] is None:
        paired = dict(state="invalid", reason=evidence["paired_invalid_reason"], bootstrap_draws=0)
    else:
        # Difference first: identical arms remain exactly zero in every draw.
        paired = legacy.contrast(points["paired_own"]["effect"]-points["paired_fake"]["effect"],
            [a["effect"]-b["effect"] for a,b in zip(samples["paired_own"], samples["paired_fake"])],
            evidence["paired_real_writers"], evidence["paired_occurrences"])
        paired.update(interval="paired real-writer percentile bootstrap; identical rows, covariates and random-intercept identities",
                      own=reports.pop("paired_own"), fake=reports.pop("paired_fake"))
    timing = evidence["timing_control_writer_differences"]
    if len(timing) >= 3:
        vals = np.asarray([r["difference"] for r in timing]); rng = np.random.default_rng(config["seed"])
        draws = [float(vals[rng.integers(0,len(vals),len(vals))].mean()) for _ in range(config["bootstrap_draws"])]
        positive = legacy.contrast(float(vals.mean()),draws,len(vals),len(vals))
    else:
        positive = dict(state="invalid",reason="fewer than three timing-control writers")
    primary = reports.pop("primary")
    return dict(primary,card=config["card"],descriptive=True,scientific_admission=False,
        controls=dict(reports, paired_own_minus_fake=paired, timing_positive_control=positive,
                      repeated_outcome=reference(primary["effect"],[r["fit"]["effect"] for r in fitted["permutations"]])),
        paired_support={k:evidence[k] for k in ("primary_occurrences","paired_occurrences","dropped_occurrences","paired_real_writers")},
        raw_contrast="local minus pervasive log pause; original own-count-adjusted crossed REML",
        limitation="Exposed descriptive second pipeline; no automaticity, attention or person-location admission")


class Yield(Exception):
    pass


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); started = time.monotonic()
    if (output/"TIMING_BINDINGS.json").exists():
        return verify(output,inputs,config)["primary"]
    freeze(output/"RUN_BINDINGS.json",dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},source_sha256=filehash(__file__)))
    matrices,evidence = source(inputs,config)
    prior = read(output/"PROGRESS.json")["cumulative_seconds"] if (output/"PROGRESS.json").exists() else evidence["charged_pilot_seconds"]
    elapsed = lambda: prior + time.monotonic()-started
    setup = elapsed(); fit_start = time.monotonic()
    def checkpoint(phase,done,total):
        atomic(output/"PROGRESS.json",dict(phase=phase,done=done,total=total,cumulative_seconds=elapsed()))
        if phase=="bootstrap" and done>=math.ceil(total/10) and not (output/"FIRST_TENTH.json").exists():
            active = sum(matrices[n] is not None for n in ARMS)
            all_fits = active*config["bootstrap_draws"]+config["permutations"]
            projection = evidence["charged_pilot_seconds"]+2*(setup-evidence["charged_pilot_seconds"])+2*(time.monotonic()-fit_start)*all_fits/(done*active)
            freeze(output/"FIRST_TENTH.json",dict(projected_cpu_seconds=projection,forecast_cpu_seconds=FORECAST_SECONDS,
                projected_seconds=projection-evidence["charged_pilot_seconds"],
                completed_draws_per_arm=done,includes_all_controls_and_fresh_replay=True))
        if elapsed()>CAP_SECONDS:
            raise RuntimeError("crossed cumulative ceiling exceeded")
        if (output/"YIELD_REQUEST.json").exists():
            raise Yield("saved complete crossed block")
    try:
        fitted = compute(matrices,config,output,checkpoint)
    except Yield as exc:
        return dict(status="yielded",card=config["card"],reason=str(exc))
    if abs(fitted["points"]["primary"]["effect"]-evidence["pilot_point"]["effect"]) > 1e-6:
        raise ValueError("stable crossed point differs materially from frozen pilot")
    result = summarize(matrices,evidence,fitted,config)
    gzip_equal(output/"DESIGNS.json.gz",dict(matrices=matrices,evidence=evidence))
    freeze(output/"FITS.json",fitted)
    freeze(output/"PRIMARY.json",result)
    freeze(output/"TIMING.json",dict(cumulative_seconds=elapsed(),charged_pilot_seconds=evidence["charged_pilot_seconds"],cap_seconds=CAP_SECONDS))
    bind(output,inputs,config,["DESIGNS.json.gz","FITS.json","PRIMARY.json","TIMING.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output=Path(output); started=time.monotonic(); check_binding(output,inputs,config)
    matrices,evidence=source(inputs,config)
    if gzread(output/"DESIGNS.json.gz")!=dict(matrices=matrices,evidence=evidence):
        raise ValueError("source and paired control do not reconstruct")
    fitted=compute(matrices,config)
    if fitted != read(output/"FITS.json"):
        raise ValueError("full independent refits do not reconstruct")
    result=summarize(matrices,evidence,fitted,config)
    if result!=read(output/"PRIMARY.json"):
        raise ValueError("complete report differs")
    if read(output/"TIMING.json")["cumulative_seconds"]+time.monotonic()-started>CAP_SECONDS:
        raise RuntimeError("combined execution/replay ceiling exceeded")
    return dict(verified=True,primary=result,full_uncached_replay=True)
