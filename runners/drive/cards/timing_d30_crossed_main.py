"""D30.p full crossed-REML texture, preserving the admitted pilot estimator.

DESIGN CHECK: 2000 complete writer-cluster refits for the primary and each fixed
label, writer and outcome shuffle. Bootstrap copies have distinct writer IDs;
globally equal markers remain shared. All variance components are re-estimated.
No failed draw is dropped or retried with different starts/tolerances. Source,
controls and all numerical results rebuild in a fresh process. Shared CI states
remain descriptive; this second pipeline does not erase earlier control flags.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

from . import timing_d30_crossed as pilot
from . import states_v2 as states
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal
from .timing_stats import bind, check_binding
from .timing_d30_outcome import permutation
from runners.stage14.common import atomic, freeze

CONFIG = dict(card="D30.p", bootstrap_draws=2000, seed=20261017, outcome_permutation_seed=20261017)
FORECAST_SECONDS = 6600
CAP_SECONDS = 19800
BLOCK = 25
ARMS = ("primary", "label_shuffle", "writer_shuffle", "outcome_shuffle")


class InsufficientMarkerSupport(ValueError):
    """A shuffled label population lacks the original minimum support."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def design(rows, mode):
    labels, evidence = pilot.original.classify_markers(rows)
    eligible = [dict(r, **labels[r["writer"], r["marker"]]) for r in rows
                if (r["writer"], r["marker"]) in labels and r["pause_seconds"] is not None
                and r["pause_seconds"] > 0 and r["population_surprisal"] is not None
                and (mode != "per_character" or r["first_delta_characters"] == 1)]
    classes = defaultdict(set)
    for r in eligible: classes[r["writer"]].add(r["label"])
    supported = {w for w, values in classes.items() if values == {"pervasive", "local"}}
    eligible = [r for r in eligible if r["writer"] in supported]
    if len(supported) < 3:
        raise InsufficientMarkerSupport("fewer than three writers with both marker classes")
    matrix = dict(x=[[int(r["label"] == "local"), r["length"], r["population_log_frequency"],
                     int(r["sentence_start"]), int(r["after_punctuation"]), r["population_surprisal"], r["own_count"]]
                    for r in eligible],
                  y=[math.log(r["pause_seconds"]) for r in eligible], writers=[r["writer"] for r in eligible],
                  markers=[r["marker"] for r in eligible])
    return matrix, eligible, evidence


def controls(rows, mode, primary):
    matrix, eligible, evidence = design(rows, mode)
    if matrix != primary:
        raise ValueError("crossed primary differs from frozen pilot occurrence design")
    rng = np.random.default_rng(CONFIG["seed"])
    labels = pilot.original.shuffle_marker_labels(eligible, rng)
    shuffled_x = [[int(label == "local")] + x[1:] for label, x in zip(labels, matrix["x"])]
    sessions = sorted({r["session"] for r in rows})
    owner = {r["session"]: r["writer"] for r in rows}
    assignment = dict(zip(sessions, rng.permutation([owner[s] for s in sessions]).tolist()))
    invalid_controls = {}
    try:
        writer_matrix, _, writer_evidence = design([dict(r, writer=assignment[r["session"]]) for r in rows], mode)
    except InsufficientMarkerSupport as exc:
        writer_matrix, writer_evidence = None, None
        invalid_controls["writer_shuffle"] = str(exc)
    indices = permutation(matrix["writers"], CONFIG["outcome_permutation_seed"])
    matrices = dict(primary=matrix, label_shuffle=dict(matrix, x=shuffled_x), writer_shuffle=writer_matrix,
                    outcome_shuffle=dict(matrix, y=[matrix["y"][i] for i in indices]))
    inside, onset = defaultdict(list), defaultdict(list)
    for r in rows:
        if r["marker"].startswith("word:"):
            inside[r["writer"]].extend(t for t in r["within_intervals"] if t > 0)
            if r["pause_seconds"] is not None and r["pause_seconds"] > 0:
                onset[r["writer"]].append(r["pause_seconds"])
    differences = [dict(writer=w, difference=float(np.mean(onset[w])-np.mean(inside[w])))
                   for w in sorted(inside) if inside[w] and onset[w]]
    return matrices, dict(marker_evidence=evidence, writer_shuffle_marker_evidence=writer_evidence,
        session_writer_assignment=assignment, shuffled_marker_labels=labels, outcome_permutation=indices,
        timing_control_writer_differences=differences, timing_mode=mode, invalid_controls=invalid_controls)


def source(inputs, config):
    if (config != CONFIG or set(config) != set(CONFIG) or any(type(config[k]) is not type(v) for k,v in CONFIG.items())
            or set(inputs) != {"primary_completion", "extension_completion", "pilot_completion"}):
        raise ValueError("exact crossed-main inputs and configuration required")
    source_inputs = {k:v for k,v in inputs.items() if k != "pilot_completion"}
    terminal = Path(inputs["pilot_completion"]); root = terminal.parent
    complete, plan = read(terminal), read(root/"PLAN.json")
    if (complete.get("status") != "COMPLETE" or complete.get("fresh_process_verified") is not True
            or plan["module"] != "runners.drive.cards.timing_d30_crossed" or plan["config"] != pilot.CONFIG
            or plan["inputs"] != source_inputs):
        raise ValueError("verified original crossed pilot required")
    for name in ("PLAN.json", "VERIFIED.json", "output/CROSSED_PRIMARY.json", "output/CROSSED_DESIGN.json", "output/TIMING_BINDINGS.json", "output/CROSSED_TIMING.json"):
        if complete["outputs"].get(name) != filehash(root/name):
            raise ValueError("crossed pilot completion binding changed")
    for name, expected in plan["pins"].items():
        if filehash(name) != expected: raise ValueError("crossed pilot source pin changed")
    check_binding(root/"output", source_inputs, pilot.CONFIG)
    report = read(root/"output/CROSSED_PRIMARY.json")
    if report["state"] != "positive" or not report["instrument_only"] or len(report["fits"]) != 6 or not all(r["converged"] for r in report["fits"]):
        raise ValueError("crossed pilot failed execution admission")
    if read(root/"VERIFIED.json").get("verified") is not True:
        raise ValueError("crossed pilot fresh verification absent")
    prior = max(read(root/"output/CROSSED_TIMING.json")["wall_seconds"],
                (datetime.fromisoformat(complete["at"])-datetime.fromisoformat(plan["at"])).total_seconds())
    if not math.isfinite(prior) or prior < 0 or prior >= CAP_SECONDS:
        raise ValueError("crossed cumulative allowance unavailable")
    primary = pilot.source(source_inputs, pilot.CONFIG)
    if primary != read(root/"output/CROSSED_DESIGN.json"):
        raise ValueError("crossed design differs from admitted pilot")
    retained = gzread(Path(inputs["extension_completion"]).parent/"output/D30_INTERMEDIATES.json.gz")
    if retained["timing_mode"] not in {"per_character", "per_word"}:
        raise ValueError("crossed pause model requires valid timing")
    matrices, evidence = controls(retained["rows"], retained["timing_mode"], primary)
    evidence.update(charged_pilot_seconds=prior, pilot_point=report["fits"][0],
                    forecast_basis=dict(slowest_pilot_fit_seconds=max(report["fit_seconds"]),
                                        pilot_source_seconds=report["source_seconds"], full_refit_arms=4))
    return matrices, evidence


def contrast(point, samples, n, observations):
    values = np.asarray(samples, float)
    if not math.isfinite(point) or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("invalid complete crossed bootstrap")
    low, high = np.quantile(values,[.025,.975]).tolist()
    se = float(values.std(ddof=1)); z = point/se if se > 0 else None
    return dict(effect=point, ci_low=low, ci_high=high, bootstrap_se=se, z=z,
        wald_p_two_sided=math.erfc(abs(z)/math.sqrt(2)) if z is not None else None,
        state=states.contrast_state(point,low,high,1), expected_direction=1, writers=n,
        observations=observations, bootstrap_draws=len(values),
        interval="writer-cluster percentile bootstrap; crossed REML variance components refitted in every draw",
        p_reference="descriptive two-sided normal Wald; CI state unchanged")


def writer_groups(matrix):
    groups = defaultdict(list)
    for index, writer in enumerate(matrix["writers"]):groups[writer].append(index)
    return [groups[w] for w in sorted(groups)]


def resample(matrix, selected, groups):
    """Exact frozen resample lists, using once-built source index groups."""
    indices, copies = [], []
    for copy, selection in enumerate(selected):
        rows = groups[int(selection)]
        indices.extend(rows)
        copies.extend([f"copy-{copy}"]*len(rows))
    return dict(x=[matrix["x"][i] for i in indices],y=[matrix["y"][i] for i in indices],writers=copies,
                markers=[matrix["markers"][i] for i in indices])


def fit_series(matrices, config, output=None, checkpoint=None):
    active = tuple(name for name in ARMS if matrices[name] is not None)
    if "primary" not in active:raise ValueError("primary crossed design unavailable")
    points = {name: pilot.fit(**matrices[name]) if name in active else None for name in ARMS}
    fits = {name:[] for name in ARMS}
    groups = {name:writer_groups(matrices[name]) for name in active}
    counts = {name:len(groups[name]) for name in active}
    rngs = {name:np.random.default_rng(config["seed"]) for name in active}
    binding = digest(dict(matrices=matrices,config=config))
    if output:
        existing=sorted((Path(output)/"draws").glob("block-*.json"))
        existing=[p for p in existing if not p.name.endswith(".receipt.json")]
        expected=[f"block-{i:05d}.json" for i in range(0,config["bootstrap_draws"],BLOCK)]
        if [p.name for p in existing]!=expected[:len(existing)]:raise ValueError("crossed checkpoint sequence differs")
        receipts={p.name for p in (Path(output)/"draws").glob("*.receipt.json")}
        if receipts!={p.with_suffix(".receipt.json").name for p in existing}:raise ValueError("crossed checkpoint receipt coverage differs")
    for start in range(0,config["bootstrap_draws"],BLOCK):
        stop = min(start+BLOCK,config["bootstrap_draws"])
        path = Path(output)/"draws"/f"block-{start:05d}.json" if output else None
        retained = None
        if path is not None and path.exists():
            if read(path.with_suffix(".receipt.json"))["sha256"] != filehash(path):
                raise ValueError("crossed main draw checkpoint changed")
            retained = read(path)
            if retained["binding"] != binding or retained["start"] != start or retained["stop"] != stop:
                raise ValueError("crossed main draw binding differs")
            if set(retained["fits"])!=set(ARMS) or any(len(retained["fits"][name])!=(stop-start if name in active else 0) for name in ARMS):
                raise ValueError("crossed checkpoint complete arm coverage differs")
        block = {name:[] for name in ARMS}
        for draw in range(start,stop):
            for name in active:
                selected = rngs[name].integers(0,counts[name],counts[name])
                value = retained["fits"][name][draw-start] if retained is not None else pilot.fit(**resample(matrices[name],selected,groups[name]))
                if not value.get("converged") or not math.isfinite(value["effect"]):
                    raise ValueError("invalid retained crossed fit")
                block[name].append(value)
        if path is not None:
            freeze(path,dict(binding=binding,start=start,stop=stop,fits=block))
            freeze(path.with_suffix(".receipt.json"),dict(sha256=filehash(path)))
        for name in ARMS:fits[name].extend(block[name])
        if checkpoint is not None:checkpoint(stop)
    return points, fits


def summarize(matrices, evidence, points, fits, config):
    summaries = {name:contrast(points[name]["effect"],[r["effect"] for r in fits[name]],
                              len(set(matrices[name]["writers"])),len(matrices[name]["y"])) if matrices[name] is not None
                 else dict(state="invalid",reason=evidence["invalid_controls"][name],bootstrap_draws=0) for name in ARMS}
    differences = [r["difference"] for r in evidence["timing_control_writer_differences"]]
    if len(differences) >= 3:
        rng = np.random.default_rng(config["seed"]); values = np.asarray(differences)
        samples = [float(values[rng.integers(0,len(values),len(values))].mean()) for _ in range(config["bootstrap_draws"])]
        timing = contrast(float(values.mean()),samples,len(values),len(values))
    else:timing = dict(state="invalid",reason="fewer than three timing-control writers")
    result = dict(summaries.pop("primary"),card="D30.p",descriptive=True,scientific_admission=False,
        raw_contrast="local minus pervasive log pause, own-count-adjusted crossed writer/marker REML",
        controls=dict(summaries,timing_positive_control=timing),
        controls_definition="one fixed writer-marker label shuffle; session writer identities shuffled then markers reclassified; raw log pauses permuted within writer; onset-minus-within-word timing",
        prior_control_warning="Earlier positive shuffled controls remain; second-pipeline texture does not establish automaticity or causal person-location",
        timing_mode=evidence["timing_mode"],estimator=points["primary"]["estimator"],
        fixed_seed=config["seed"],outcome_permutation_seed=config["outcome_permutation_seed"],
        global_marker_identity="equal marker strings share one random intercept across writer-bootstrap copies")
    return result


class Yield(Exception):pass


def execute(output:Path, inputs:dict, config:dict)->dict:
    output=Path(output);start=time.monotonic()
    if (output/"TIMING_BINDINGS.json").exists():return verify(output,inputs,config)["primary"]
    freeze(output/"RUN_BINDINGS.json",dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},source_sha256=filehash(__file__)))
    matrices,evidence=source(inputs,config)
    prior=read(output/"PROGRESS.json")["active_seconds"] if (output/"PROGRESS.json").exists() else evidence["charged_pilot_seconds"]
    elapsed=lambda:prior+time.monotonic()-start
    preparation=elapsed();fit_start=time.monotonic()
    def checkpoint(done):
        active=elapsed();atomic(output/"PROGRESS.json",dict(completed_draws_per_arm=done,total_draws_per_arm=config["bootstrap_draws"],active_seconds=active))
        if done>=math.ceil(config["bootstrap_draws"]/10) and not (output/"FIRST_TENTH.json").exists():
            projected=evidence["charged_pilot_seconds"]+2*(preparation-evidence["charged_pilot_seconds"])+2*(time.monotonic()-fit_start)*config["bootstrap_draws"]/done
            freeze(output/"FIRST_TENTH.json",dict(completed_draws_per_arm=done,arms=4,active_seconds=active,
                projected_cpu_seconds=projected,forecast_cpu_seconds=FORECAST_SECONDS,includes_control_refits_and_fresh_reconstruction=True))
            if projected>2*FORECAST_SECONDS:atomic(output/"YIELD_REQUEST.json",dict(reason="first_tenth_projection_exceeds_twice_forecast"))
        if active>CAP_SECONDS:raise RuntimeError("crossed main cumulative threefold cap exceeded")
        if (output/"YIELD_REQUEST.json").exists():raise Yield("saved complete interleaved writer-refit block")
    try:points,fits=fit_series(matrices,config,output,checkpoint)
    except Yield as exc:return dict(status="yielded",card="D30.p",reason=str(exc))
    if points["primary"]!=evidence["pilot_point"]:raise ValueError("crossed main point differs from frozen pilot estimator")
    result=summarize(matrices,evidence,points,fits,config)
    gzip_equal(output/"DESIGNS.json.gz",dict(matrices=matrices,evidence=evidence))
    freeze(output/"FITS.json",dict(points=points,bootstrap=fits))
    freeze(output/"PRIMARY.json",result)
    freeze(output/"TIMING.json",dict(cumulative_seconds=elapsed(),charged_pilot_seconds=evidence["charged_pilot_seconds"],forecast_cpu_seconds=FORECAST_SECONDS,cap_seconds=CAP_SECONDS))
    bind(output,inputs,config,["DESIGNS.json.gz","FITS.json","PRIMARY.json","TIMING.json"])
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);start=time.monotonic();check_binding(output,inputs,config)
    matrices,evidence=source(inputs,config)
    if gzread(output/"DESIGNS.json.gz")!=dict(matrices=matrices,evidence=evidence):raise ValueError("crossed designs/controls do not reconstruct")
    points,fits=fit_series(matrices,config)
    if read(output/"FITS.json")!=dict(points=points,bootstrap=fits):raise ValueError("crossed refits do not reconstruct")
    result=summarize(matrices,evidence,points,fits,config)
    if read(output/"PRIMARY.json")!=result:raise ValueError("crossed full primary does not reconstruct")
    if read(output/"TIMING.json")["cumulative_seconds"]+time.monotonic()-start>CAP_SECONDS:
        raise RuntimeError("crossed execute/verify cumulative cap exceeded")
    arms=sum(matrices[name] is not None for name in ARMS)
    return dict(verified=True,primary=result,fresh_refitted_arms=arms,fresh_bootstrap_refits=arms*config["bootstrap_draws"])
