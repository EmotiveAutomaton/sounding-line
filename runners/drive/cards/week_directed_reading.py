"""DR1 retrospective full-cohort profile recovery; no population reweighting.

DESIGN CHECK (2026-10-20): LESSONS sections 3-5.
NULL: constant writer fingerprints recover equally in every order.
ALTERNATIVE: a useful record placed early by the metadata policy reduces the
number read; placing it last reverses that contrast. Tied galleries never count
as certain identification. Missing support is censored, not a zero cost.
Source changes and incomplete saved results refuse fresh reconstruction.
"""
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import numpy as np

from .menus_io import read, sha256, write
from .events_d4_sources import bind_completed
from .week_reading_order import make_order
from .timing_pmap_source import ACTIONS

CONFIG = dict(card="DR1", schema_version=1, random_orders=200, bootstrap_draws=2000,
              seed=20261022, minimum_sessions=12, minimum_prompts=3)
CHANNELS = ("style", "rhythm", "lean")


def profile(rows, dictionary):
    words, punctuation, handling = Counter(), Counter(), Counter()
    for row in rows:
        words.update(row["word_counts"]); punctuation.update(row["punctuation_counts"])
        handling.update(row["handling"])
    denominator = sum(words.values()) + sum(punctuation.values())
    total_actions = sum(handling.values())
    timing = [row for row in rows if row["tc_timing_mode"] != "invalid"]
    median = lambda values: float(np.median(values)) if values else None
    return dict(style=[words[k]/denominator if denominator else None for k in dictionary["words"]]
                    + [punctuation[k]/denominator if denominator else None for k in dictionary["punctuation"]],
                lean=[handling[k]/total_actions if total_actions else None for k in ACTIONS],
                rhythm=[median([v for r in timing for v in r["within_intervals"]]),
                        median([v for r in timing for v in r["onset_intervals"]])]
                    + [median([v for r in timing for v in r["bigram_intervals"].get(k, [])])
                       for k in dictionary["character_bigrams"]])


def gallery_model(reference):
    b = np.asarray(reference, dtype=float)
    have = np.isfinite(b).sum(axis=0)
    mean = np.divide(np.nansum(b, axis=0), have, out=np.zeros(b.shape[1]), where=have > 0)
    b = np.where(np.isfinite(b), b, mean)
    scale = b.std(axis=0); keep = (have > 0) & (scale > 1e-12)
    return mean, scale, keep, (b[:, keep]-mean[keep])/scale[keep]


def correct_identification(value, writer_index, gallery):
    a = np.asarray(value, dtype=float)
    if not np.isfinite(a).any():
        return False
    mean, scale, keep, b = gallery
    a = np.where(np.isfinite(a), a, mean)
    distances = np.sum((((a[keep]-mean[keep])/scale[keep])-b)**2, axis=1)
    nearest = np.isclose(distances, distances.min(), atol=1e-12, rtol=1e-12)
    return bool(nearest[writer_index] and nearest.sum() == 1)


def stable_time(flags):
    """n+1 encodes right censoring: recovery not reached within n records."""
    if not flags:
        raise ValueError("Recovery needs a nonempty sequence")
    for index in range(len(flags)):
        if all(flags[index:]):
            return dict(sessions=index+1, censored=False)
    return dict(sessions=len(flags)+1, censored=True)


def first_time(flags):
    """Feature-tolerance endpoint is first entry; identity requires stability."""
    if not flags:
        raise ValueError("Recovery needs a nonempty sequence")
    return next((dict(sessions=i+1, censored=False) for i, good in enumerate(flags) if good),
                dict(sessions=len(flags)+1, censored=True))


def evaluate_order(rows, dictionary, order, reference, deviations, galleries, writer_index):
    by_session = {r["session"]: r for r in rows}
    if len(by_session) != len(rows) or set(by_session) != {s["session"] for s in order["steps"]}:
        raise ValueError("Order is not the complete session population")
    selected = []; curves = {c: dict(identifies=[], within_reference_sd=[]) for c in CHANNELS}
    for step in order["steps"]:
        selected.append(by_session[step["session"]])
        current = profile(selected, dictionary)
        for channel in CHANNELS:
            curves[channel]["identifies"].append(correct_identification(current[channel], writer_index, galleries[channel]))
            value = np.asarray(current[channel], float)
            target, sd = reference[channel], deviations[channel]
            keep = np.isfinite(target) & np.isfinite(sd)
            within = (keep.any() and np.isfinite(value[keep]).all()
                      and np.all(np.abs(value[keep]-target[keep]) <= sd[keep]+1e-12))
            curves[channel]["within_reference_sd"].append(bool(within))
    return {c: dict(identification=stable_time(v["identifies"]),
                    feature_recovery=first_time(v["within_reference_sd"]),
                    identification_curve=v["identifies"], feature_curve=v["within_reference_sd"])
            for c, v in curves.items()}


def contrast(values, seed, draws):
    values = np.asarray(values, float)
    if len(values) < 2 or not np.isfinite(values).all():
        return dict(status="unsupported")
    rng = np.random.default_rng(seed)
    samples = values[rng.integers(0, len(values), (draws, len(values)))].mean(axis=1)
    low, high = np.quantile(samples, [.025, .975])
    return dict(estimate=float(values.mean()), lower=float(low), upper=float(high),
                outcome="fewer records" if high < 0 else "more records" if low > 0 else "unresolved",
                method="Paired writer bootstrap; fixed full-reference gallery; conditional on these writers, sessions and random-order bank")


def study(rows, dictionary, config=CONFIG):
    if config != CONFIG:
        raise ValueError("Frozen DR1 configuration differs")
    if len({r["session"] for r in rows}) != len(rows):
        raise ValueError("Duplicate session identity")
    groups = defaultdict(list)
    for row in rows:
        groups[row["writer"]].append(row)
    eligible, excluded = {}, {}
    for writer, own in sorted(groups.items()):
        if len(own) >= 12 and len({r["prompt"] for r in own}) >= 3:
            eligible[writer] = sorted(own, key=lambda r: r["session"])
        else:
            excluded[writer] = "fewer than twelve sessions or three prompts"
    references = {w: profile(own, dictionary) for w, own in eligible.items()}
    supported = [w for w in eligible if np.isfinite(np.asarray(references[w]["style"], float)).any()]
    for writer in set(eligible)-set(supported):
        excluded[writer] = "no style support in full reference"
    if len(supported) < 2:
        return dict(status="unsupported", excluded=excluded, writers=len(supported),
                    scientific_admission=False), []
    # Same complete style-supported cohort is retained in every channel.
    galleries = {c: gallery_model([references[w][c] for w in supported]) for c in CHANNELS}
    result_rows, ledgers = [], []
    for wi, writer in enumerate(supported):
        own = eligible[writer]
        metadata = [dict(session=r["session"], writer=r["writer"], prompt=r["prompt"],
                         timestamp=r["timestamp"], typed_words=sum(r["word_counts"].values())) for r in own]
        ref = {c: np.asarray(references[writer][c], float) for c in CHANNELS}
        per_session = [profile([r], dictionary) for r in own]
        deviations = {}
        for channel in CHANNELS:
            matrix = np.asarray([p[channel] for p in per_session], float)
            # Sample SD across that writer's sessions; absent or singleton
            # features remain unsupported, never replaced by a zero tolerance.
            counts = np.isfinite(matrix).sum(axis=0)
            mean = np.divide(np.nansum(matrix, axis=0), counts, out=np.zeros(matrix.shape[1]), where=counts > 0)
            centered = np.where(np.isfinite(matrix), matrix-mean, 0)
            variance = np.divide(np.sum(centered**2, axis=0), counts-1,
                                 out=np.full(matrix.shape[1], np.nan), where=counts > 1)
            deviations[channel] = np.sqrt(variance)
        evaluated = {}
        policies = [("chronological", 0), ("directed", 0), ("directed_random20", 0)]
        policies += [("random", i) for i in range(config["random_orders"])]
        for policy, replicate in policies:
            order = make_order(metadata, policy, config["seed"]+wi*1000+replicate)
            values = evaluate_order(own, dictionary, order, ref, deviations, galleries, wi)
            evaluated.setdefault(policy, []).append(values)
            ledgers.append(dict(writer=writer, replicate=replicate, **order, recovery=values))
        comparisons = {}
        for channel in CHANNELS:
            random_times = [v[channel]["identification"]["sessions"] for v in evaluated["random"]]
            directed = evaluated["directed"][0][channel]["identification"]
            comparisons[channel] = dict(
                random_mean_sessions=float(np.mean(random_times)),
                random_censored=sum(v[channel]["identification"]["censored"] for v in evaluated["random"]),
                directed=directed,
                chronological=evaluated["chronological"][0][channel]["identification"],
                mixed=evaluated["directed_random20"][0][channel]["identification"],
                feature_recovery=dict(
                    directed=evaluated["directed"][0][channel]["feature_recovery"],
                    chronological=evaluated["chronological"][0][channel]["feature_recovery"],
                    mixed=evaluated["directed_random20"][0][channel]["feature_recovery"],
                    random_mean_sessions=float(np.mean([v[channel]["feature_recovery"]["sessions"] for v in evaluated["random"]])),
                    random_censored=sum(v[channel]["feature_recovery"]["censored"] for v in evaluated["random"])),
                directed_minus_random=directed["sessions"]-float(np.mean(random_times)))
        feature_support = {c: dict(total=len(ref[c]),
            evaluated=int((np.isfinite(ref[c]) & np.isfinite(deviations[c])).sum()),
            omitted=int((~(np.isfinite(ref[c]) & np.isfinite(deviations[c]))).sum()))
            for c in CHANNELS}
        result_rows.append(dict(writer=writer, sessions=len(own), channels=comparisons,
                                feature_support=feature_support))
    comparisons = {c: contrast([r["channels"][c]["directed_minus_random"] for r in result_rows],
                              config["seed"]+j, config["bootstrap_draws"]) for j, c in enumerate(CHANNELS)}
    return dict(status="complete", writers=len(supported), excluded=excluded, channels=comparisons,
                primary=comparisons["style"], writer_rows=result_rows,
                route="prompt-diverse reading supported by this benchmark" if comparisons["style"]["outcome"] == "fewer records" else "retain chronological default",
                target="Retrospective recovery of full-record profile and identity; overlapping reference, not held-out unseen-work prediction",
                feature_threshold="One sample SD across this writer's session profiles, fixed before policy evaluation; unsupported features omitted with counts in ledger",
                censoring="n+1 is the prespecified failure-to-recover penalty; comparisons are restricted recovery costs, not uncensored mean time",
                population_reweighting=False, scientific_admission=False,
                caveats=["Full-cohort policy benchmark; no outcome used to select records",
                         "One randomized exploration realization per writer; 200 uniform orders",
                         "The original PMAP dictionary and device/context limitations remain",
                         "An unresolved contrast does not establish noninferiority"]), ledgers


def load(inputs):
    if set(inputs) != {"pmap_completion"}:
        raise ValueError("Exact PMAP completion required")
    complete = Path(inputs["pmap_completion"])
    receipt = read(complete)
    root = complete.parent
    names = sorted(n for n in receipt["outputs"] if n.startswith("output/sessions/") and n.endswith(".json.gz"))
    if not names:
        raise ValueError("PMAP session population absent")
    for name in names + ["output/STYLE_DICTIONARY.json", "output/PRIMARY.json"]:
        path = (root/name).resolve()
        path.relative_to(root.resolve())
        bind_completed(complete, path)
    rows = []
    for name in names:
        with gzip.open(root/name, "rt", encoding="utf8") as stream:
            rows.append(json.load(stream))
    if read(root/"output/PRIMARY.json")["source_audit"]["sessions"] != len(rows):
        raise ValueError("PMAP session population incomplete")
    return rows, read(root/"output/STYLE_DICTIONARY.json")


def run(output, inputs, config, verify=False):
    output = Path(output)
    rows, dictionary = load(inputs)
    primary, ledger = study(rows, dictionary, config)
    binding = dict(inputs={k: sha256(v) for k, v in inputs.items()}, config=config)
    values = {"DR1_PRIMARY.json": primary, "DR1_BINDINGS.json": binding}
    if verify:
        for name, expected in values.items():
            if read(output/name) != expected:
                raise ValueError("Fresh DR1 reconstruction differs: "+name)
        with gzip.open(output/"DR1_ORDERS.json.gz", "rt", encoding="utf8") as stream:
            if json.load(stream) != ledger:
                raise ValueError("Fresh DR1 order ledger differs")
        return dict(verified=True, source_reconstructed=True, full_policies_replayed=True)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        return run(output, inputs, config, verify=True)
    for name, value in values.items():
        write(output/name, value)
    with gzip.open(output/"DR1_ORDERS.json.gz", "xt", encoding="utf8") as stream:
        json.dump(ledger, stream, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return dict(status=primary["status"], scientific_admission=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, verify=True)
