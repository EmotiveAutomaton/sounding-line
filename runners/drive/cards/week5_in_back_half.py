"""IN5--IN7, isolated November 11 extension; original IN source stays immutable.

DESIGN CHECK: disjoint profile maps, paired writer resamples, writer-owned
intensity, and untouched-prompt transmission are distinct comparisons. Each
saved draw is bound to the complete inputs, configuration and implementation.
"""
from pathlib import Path
import hashlib
import json
import os
import time

for _key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "2"
import numpy as np
import pandas as pd
from . import week5_in as old

SEED = 20261107
MAPPED = ("fear", "anger", "sadness", "disgust")
PROFILES = {
    "H": dict(old.PROFILES["fear"]),
    "U": {"predict_event": -1, "self_control": -1, "suddenness": 1},
    "G": {"urgency": 1, "attention": 1},
    "RAGE": dict(old.PROFILES["anger"]),
    "PANIC_GRIEF": dict(old.PROFILES["sadness"]),
    "DISGUST": dict(old.PROFILES["disgust"]),
}
UNIQUE = {
    "H": {"predict_conseq": 1}, "U": {"predict_event": -1, "suddenness": 1},
    "G": {"attention": 1}, "RAGE": {"other_control": 1},
    "PANIC_GRIEF": {"accept_conseq": -1},
    "DISGUST": {"standards": 1, "social_norms": 1, "not_consider": 1},
}
STYLE = ("familiarity", "goal_relevance", "chance_responsblt", "self_responsblt", "chance_control", "effort")
OWN = {"H": "fear", "RAGE": "anger", "PANIC_GRIEF": "sadness", "DISGUST": "disgust"}
NAMED = ("accept_conseq", "not_consider", "familiarity")
OTHER_STANCE = ("predict_event", "goal_relevance", "predict_conseq", "goal_support", "standards")
EVENT = ("suddenness", "self_responsblt", "other_responsblt", "chance_responsblt", "urgency", "other_control", "chance_control", "social_norms")
UNCLASSED = ("self_control", "attention", "effort", "pleasantness", "unpleasantness")
NEGATIVE = frozenset(("anger", "boredom", "disgust", "fear", "guilt", "sadness", "shame"))
POSITIVE = frozenset(("joy", "pride", "relief"))
SOURCE_PINS = {
    "generation": "196fe2a4f72b36ae91516ee5caf762cb3ba04f7d69b6da4e53958587d44c1638",
    "validation": "8c13fabfc8b08667763dd9049d5bf78337689fa17283b88a4e3dbd6a75426242",
}


class YieldRequested(Exception):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf8")


def sealed(path, value):
    raw = canonical(value)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("immutable IN back-half checkpoint changed")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(raw)
        temporary.replace(path)


def requested(output):
    return any((p / "YIELD_REQUEST.json").exists() or (p / "STOP_REQUEST.json").exists()
               for p in (output, output.parent, output.parent.parent))


def index(frame, profile):
    items = list(profile)
    return old.standardize((old.standardize(frame[items].to_numpy(float)) * np.array(list(profile.values()))).mean(axis=1))


def fit_design(frame, profile, joint=False):
    """Within-prompt normalization frozen before every resample."""
    labels = sorted(frame.emotion.unique())
    pieces = []
    for label in labels:
        d = frame.loc[frame.emotion.eq(label)]
        prediction = (old.standardize(d[list(profile)].to_numpy(float)) * np.array(list(profile.values()))
                      if joint else index(d, profile)[:, None])
        controls = old.standardize(np.column_stack((d.unpleasantness, d.confidence, d[list(STYLE)].mean(axis=1))))
        intercepts = np.column_stack([np.full(len(d), float(label == k)) for k in labels])
        pieces.append((np.column_stack((intercepts, prediction, controls)),
                       old.standardize(d.intensity.to_numpy(float)), d.prolific_id.to_numpy()))
    x, y, clusters = [np.concatenate([p[i] for p in pieces]) for i in range(3)]
    c = np.eye(x.shape[1])[len(labels):len(labels) + (len(profile) if joint else 1)]
    return x, y, clusters, c


def sufficient(design, universe):
    x, y, clusters, contrast = design
    lookup = {str(k): i for i, k in enumerate(universe)}
    code = np.array([lookup[str(k)] for k in clusters])
    xx = np.zeros((len(universe), x.shape[1], x.shape[1]))
    xy = np.zeros((len(universe), x.shape[1]))
    np.add.at(xx, code, x[:, :, None] * x[:, None, :])
    np.add.at(xy, code, x * y[:, None])
    return xx, xy, contrast, len(np.unique(clusters)), len(y)


def solve(stat, counts):
    xx, xy, contrast, _, _ = stat
    a, b = np.einsum("i,ijk->jk", counts, xx), counts @ xy
    if np.linalg.matrix_rank(a, tol=1e-10) < a.shape[0]:
        return None
    value = contrast @ np.linalg.solve(a, b)
    return value.tolist() if np.isfinite(value).all() else None


def resample_counts(n, draw, stream):
    rng = np.random.default_rng(np.random.SeedSequence([SEED, stream, draw]))
    return np.bincount(rng.integers(0, n, n), minlength=n)


def draw_blocks(output, binding, group, draws, evaluate, config):
    """Global draw indices never depend on chunk boundaries or continuation."""
    block_size = 32
    values = []
    started = time.process_time()
    new_blocks = 0
    for start in range(0, draws, block_size):
        if requested(output):
            raise YieldRequested()
        end = min(draws, start + block_size)
        path = output / "checkpoints" / group / f"{start:05d}-{end:05d}.json"
        if path.exists():
            block = json.loads(path.read_text("utf8"))
            seal = json.loads(path.with_suffix(".seal.json").read_text("utf8"))
            if old.digest(path) != seal["sha256"] or block["binding"] != binding or block["range"] != [start, end]:
                raise ValueError("IN back-half checkpoint provenance mismatch")
            part = block["values"]
            if len(part) != end - start:
                raise ValueError("IN back-half checkpoint coverage mismatch")
        else:
            if new_blocks >= config.get("max_new_blocks", 10**9):
                raise YieldRequested()
            t = time.process_time()
            part = [evaluate(i) for i in range(start, end)]
            sealed(path, {"binding": binding, "range": [start, end], "values": part})
            sealed(path.with_suffix(".seal.json"), {"sha256": old.digest(path)})
            # The first completed block is the in-run cost probe, not a new campaign.
            probe = output / "COST_PROBE.json"
            if not probe.exists():
                sealed(probe, {"binding": binding, "group": group, "draw_range": [start, end],
                               "measured_block_cpu_seconds": time.process_time() - t,
                               "forecast_cpu_seconds": None,
                               "scope": "first actual inference block; preparation and replay not extrapolated"})
            new_blocks += 1
        values.extend(part)
        old.write_json(output / "PROGRESS.json", {"group": group, "completed_draws": end, "requested_draws": draws,
                                                  "current_call_cpu_seconds": time.process_time() - started})
    return values


def model_bank(models, output, binding, group, draws, stream, config):
    universe = sorted({str(k) for d in models.values() for k in d[2]})
    stats = {name: sufficient(d, universe) for name, d in models.items()}
    points = {name: solve(s, np.ones(len(universe))) for name, s in stats.items()}
    def one(i):
        counts = resample_counts(len(universe), i, stream)
        return {name: solve(s, counts) for name, s in stats.items()}
    samples = draw_blocks(output, binding, group, draws, one, config)
    return points, samples, stats


def estimate(point, samples, bar=.1, clusters=None, record_kind="claim", theory_tags=(), by_construction=False):
    result = {"record_kind": record_kind, "theory_tags": list(theory_tags), "by_construction": by_construction,
              "bar": bar, "clusters": clusters, "draws": len(samples)}
    if point is None or any(v is None or not np.isfinite(v) for v in samples):
        return {**result, "status": "design cannot test", "reason": "rank or correlation undefined; no redraw or omission", "estimate": point}
    if clusters is not None and clusters < 2:
        return {**result, "status": "below floor, descriptive", "estimate": float(point),
                "interval": None, "bootstrap_se": None, "sees": None, "supports_at": None,
                "interpretation": "below floor, descriptive"}
    values = np.asarray(samples, float)
    interval = np.quantile(values, [.025, .975]).tolist()
    se = float(values.std(ddof=1)) if len(values) > 1 else None
    result.update(status="ok", estimate=float(point), interval=interval, bootstrap_se=se,
                  sees=None if se is None else 2.8 * se, supports_at=None if se is None else bar + 2.8 * se,
                  sensitivity_approximation="normal approximation, slightly optimistic; from these same resamples")
    if by_construction:
        result["interpretation"] = "scale report, fixed partly by construction"
    elif record_kind == "claim" and len(samples) >= 2000 and (clusters is None or clusters >= 20):
        result["outcome"] = old.classify(point, interval, bar)
    else:
        result["interpretation"] = "below floor, descriptive" if clusters is not None and clusters < 20 else "descriptive texture"
    if se is not None and bar > 0 and 2.8 * se > bar:
        result["first_line"] = f"limited sensitivity: sees effects of about {2.8 * se:.3f} or more; the bar is {bar:g}"
    return result


def component(points, samples, name, column=0, **kwargs):
    point = None if points[name] is None else points[name][column]
    values = [None if d[name] is None else d[name][column] for d in samples]
    return estimate(point, values, **kwargs)


def difference(points, samples, a, b, **kwargs):
    def diff(d):
        return None if d[a] is None or d[b] is None else d[a][0] - d[b][0]
    return estimate(diff(points), [diff(d) for d in samples], **kwargs)


def in5(generation, output, binding, config):
    d = generation.loc[generation.emotion.isin(MAPPED)].copy()
    fear = d.loc[d.emotion.eq("fear")]
    other = d.loc[~d.emotion.eq("fear")]
    models = {name: fit_design(fear, PROFILES[name]) for name in ("H", "U", "G")}
    fear_items = {k: v for p in ("H", "U", "G") for k, v in PROFILES[p].items()}
    joint_profiles = {"fear": fear_items, "anger": PROFILES["RAGE"], "sadness": PROFILES["PANIC_GRIEF"], "disgust": PROFILES["DISGUST"]}
    models["joint_fear"] = fit_design(fear, fear_items, joint=True)
    points, samples, stats = model_bank(models, output, binding, "in5-fear", config["draws"], 510, config)
    common = {"theory_tags": ("H12-T1",)}
    full = {name: component(points, samples, name, clusters=stats[name][3], **common) for name in ("H", "U", "G")}
    contrasts = {"U_minus_" + name: difference(points, samples, "U", name, bar=0., clusters=len(fear.prolific_id.unique()), **common) for name in ("H", "G")}
    joint = {"fear": {item: {"signed_direction": fear_items[item], **component(points, samples, "joint_fear", i,
                             clusters=stats["joint_fear"][3], **common)} for i, item in enumerate(fear_items)}}
    for ordinal, label in enumerate(("anger", "sadness", "disgust")):
        profile = joint_profiles[label]
        jp, js, jt = model_bank({label: fit_design(d.loc[d.emotion.eq(label)], profile, joint=True)},
                               output, binding, "in5-joint-" + label, config["draws"], 512 + ordinal, config)
        joint[label] = {item: {"signed_direction": profile[item], **component(jp, js, label, i,
                               clusters=jt[label][3], **common)} for i, item in enumerate(profile)}
    models = {}
    # All six profiles receive the declared specificity contrast, not just winners.
    for name, profile in UNIQUE.items():
        models["specific_fear_" + name] = fit_design(fear, profile)
        models["specific_other_" + name] = fit_design(other, profile)
    points, samples, stats = model_bank(models, output, binding, "in5-specificity", config["draws"], 515, config)
    specificity = {name: difference(points, samples, "specific_fear_" + name, "specific_other_" + name,
                    bar=0., clusters=len(d.prolific_id.unique()), **common) for name in UNIQUE}
    maps = {f"{version}/{name}/{label}": fit_design(d.loc[d.emotion.eq(label)], profile)
            for version, profiles in (("full", PROFILES), ("unique", UNIQUE)) for name, profile in profiles.items() for label in MAPPED}
    mp, ms, st = model_bank(maps, output, binding, "in5-map", config["texture_draws"], 511, config)
    map_results = {name: component(mp, ms, name, clusters=st[name][3], record_kind="texture",
                                   by_construction=name.startswith("full/"), **common) for name in maps}
    summary = {}
    for version in ("full", "unique"):
        own_keys = [f"{version}/{name}/{label}" for name, label in OWN.items()]
        cross_keys = [f"{version}/{name}/{label}" for name, own in OWN.items() for label in MAPPED if label != own]
        def contrast(bank):
            if any(bank[k] is None for k in own_keys + cross_keys):
                return None
            return float(np.mean([bank[k][0] for k in own_keys]) - np.mean([bank[k][0] for k in cross_keys]))
        summary[version] = estimate(contrast(mp), [contrast(s) for s in ms], bar=0., clusters=len(d.prolific_id.unique()),
                                    record_kind="texture", by_construction=version == "full", **common)
    def supports(r):
        return r.get("status") == "ok" and r["interval"][0] > .1 and (r.get("clusters") or 0) >= 20
    chosen = None
    uh = contrasts["U_minus_H"].get("interval")
    if supports(full["U"]) and uh and uh[0] > 0:
        reading, chosen = "Unresolved fits best", "U"
    elif supports(full["U"]) and uh and uh[0] <= 0 <= uh[1]:
        reading, chosen = "Unresolved fits, not shown to fit better", "U"
    elif supports(full["G"]) and not supports(full["U"]):
        reading, chosen = "Urgent fits", "G"
    elif all(r.get("status") == "ok" for r in full.values()) and not any(supports(r) for r in full.values()):
        reading = "None fits"
    else:
        reading = "unlisted combination or untestable comparison; report all registered estimates"
    if chosen and specificity[chosen].get("interval", [-1])[0] > 0:
        reading += "; FEAR's own"
    first_line = full["U"].get("first_line", reading)
    return {"card": "IN5", "exploratory": True, "theory_tags": ["H12-T1"], "fear_reports": len(fear),
            "primary": full["U"], "profiles_in_fear": full, "paired_contrasts": contrasts, "joint_item_models": joint,
            "unique_item_specificity": specificity, "map": map_results, "map_summary": summary,
            "reading": reading, "first_line": first_line, "style_items": list(STYLE), "normalization": "fixed within-prompt sample z scores",
            "scope": "third look at the same prompted reports; support is an exploratory lead, not a new confirmatory claim"}


def panels(generation, validation):
    if generation.text_id.duplicated().any():
        raise ValueError("duplicate writer text")
    writers = generation.set_index("text_id")
    rows = []
    for text, readers in validation.groupby("text_id", sort=True):
        if text not in writers.index or len(readers) != 5 or readers.prolific_id.nunique() != 5:
            raise ValueError("incomplete or duplicate five-reader panel")
        writer = writers.loc[text]
        if not readers.original_emotion.eq(writer.emotion).all():
            raise ValueError("writer/reader prompt mismatch")
        rows.append((text, writer, readers))
    return rows


def in6_designs(generation, validation):
    panel = [p for p in panels(generation, validation) if p[1].emotion in MAPPED]
    reader_parts, text_parts = [], []
    for label in MAPPED:
        selected = [p for p in panel if p[1].emotion == label]
        if not selected:
            raise ValueError("missing mapped prompt")
        readers = pd.concat([p[2] for p in selected], ignore_index=True)
        primary = PROFILES[next(k for k, v in OWN.items() if v == label)]
        for variant in ("primary", "U", "G"):
            profile = PROFILES[variant] if label == "fear" and variant != "primary" else primary
            readers["fit_" + variant] = index(readers, profile)
        writer_keys = {p[0]: p[1].prolific_id for p in selected}
        readers["writer_cluster"] = readers.text_id.map(writer_keys)
        readers["emotion"] = label
        readers["y"] = old.standardize(readers.intensity.to_numpy(float))
        readers["control"] = old.standardize(readers.unpleasantness.to_numpy(float))
        reader_parts.append(readers)
        means = readers.groupby("text_id", sort=True)[["fit_primary", "fit_U", "fit_G", "intensity", "unpleasantness"]].mean()
        selected_writers = generation.set_index("text_id").loc[means.index]
        frame = pd.DataFrame({"emotion": label, "writer_cluster": selected_writers.prolific_id,
                              "y": old.standardize(selected_writers.intensity.to_numpy(float)),
                              "control": old.standardize(means.unpleasantness.to_numpy(float))}, index=means.index)
        for name in ("primary", "U", "G"):
            frame["fit_" + name] = old.standardize(means["fit_" + name].to_numpy(float))
        frame["attributed"] = old.standardize(means.intensity.to_numpy(float))
        text_parts.append(frame)
    texts, readers = pd.concat(text_parts), pd.concat(reader_parts)
    def design(frame, predictor):
        x = np.column_stack([frame.emotion.eq(label).to_numpy(float) for label in MAPPED] + [frame[predictor], frame.control])
        return x, frame.y.to_numpy(float), frame.writer_cluster.to_numpy(), np.eye(x.shape[1])[[len(MAPPED)]]
    models = {name: design(texts, "fit_" + name) for name in ("primary", "U", "G")}
    models["intensity_transmission"] = design(texts, "attributed")
    models["same_rater"] = design(readers, "fit_primary")
    return models, len(texts), {str(k): int(v) for k, v in texts.emotion.value_counts().items()}


def in6(generation, validation, output, binding, config):
    models, count, counts = in6_designs(generation, validation)
    points, samples, stats = model_bank(models, output, binding, "in6", config["draws"], 610, config)
    fits = {name: component(points, samples, name, clusters=stats[name][3], by_construction=name == "same_rater") for name in models}
    first_line = fits["primary"].get("first_line", "writer-owned intensity on the five-reader mean trigger fit")
    return {"card": "IN6", "theory_tags": [], "analyst_addition": "engine backward-run magnitude, not a new H12 theory claim",
            "first_line": first_line,
            "texts": count, "reader_rows": count * 5, "channel_counts": counts, "primary": fits.pop("primary"),
            "secondary": fits, "cluster_unit": "original generation writer, never reader or text",
            "normalization": "within-prompt reader-item/index z, five-reader mean, text predictor/outcome/control z; frozen across resamples",
            "same_rater_scope": "scale only; same writer clusters; not a reader-population generalization"}


def in7_arrays(generation, validation):
    rows, writer_values, reader_means, excess = [], [], [], []
    for text, writer, readers in panels(generation, validation):
        if writer.emotion in MAPPED:
            continue
        values = readers[old.APPRAISALS].to_numpy(float)
        target = writer[old.APPRAISALS].to_numpy(float)
        rr = np.mean([np.abs(values[i] - values[j]) for i in range(5) for j in range(i + 1, 5)], axis=0)
        rows.append({"text": text, "emotion": str(writer.emotion),
                     "group": "negative" if writer.emotion in NEGATIVE else "positive" if writer.emotion in POSITIVE else "other"})
        writer_values.append(target)
        reader_means.append(values.mean(axis=0))
        excess.append(np.abs(values - target).mean(axis=0) - rr)
    if not rows:
        raise ValueError("no untouched validation prompts")
    return pd.DataFrame(rows), np.array(writer_values), np.array(reader_means), np.array(excess)


def correlation_z(x, y):
    a, b = x - x.mean(axis=0), y - y.mean(axis=0)
    denom = np.sqrt((a * a).sum(axis=0) * (b * b).sum(axis=0))
    result = []
    for numerator, scale in zip((a * b).sum(axis=0), denom):
        if scale <= 1e-12:
            result.append(None)
        else:
            r = float(numerator / scale)
            # Finite Fisher z is undefined at exact +/-1. Do not invent clipping.
            result.append(float(np.arctanh(r)) if abs(r) < 1 - 1e-14 else None)
    return result


def in7_statistics(x, y, excess, groups):
    pos = {k: i for i, k in enumerate(old.APPRAISALS)}
    mean = excess.mean(axis=0)
    z = correlation_z(x, y)
    def contrast(a, b):
        return float(mean[[pos[k] for k in a]].mean() - mean[[pos[k] for k in b]].mean())
    used = [pos[k] for k in EVENT + NAMED + OTHER_STANCE]
    transmission = None if any(z[i] is None for i in used) else float(np.mean([z[pos[k]] for k in EVENT]) - np.mean([z[pos[k]] for k in NAMED + OTHER_STANCE]))
    result = {"named_minus_event": contrast(NAMED, EVENT), "other_minus_event": contrast(OTHER_STANCE, EVENT),
              "transmission_event_minus_stance_z": transmission,
              **{"excess/" + k: float(mean[i]) for i, k in enumerate(old.APPRAISALS)},
              **{"transmission_z/" + k: z[i] for i, k in enumerate(old.APPRAISALS)}}
    for group in ("negative", "positive", "other"):
        keep = groups == group
        e = excess[keep].mean(axis=0) if keep.any() else None
        for name, items in (("named", NAMED), ("other", OTHER_STANCE)):
            result[f"group/{group}/{name}_minus_event"] = None if e is None else float(e[[pos[k] for k in items]].mean() - e[[pos[k] for k in EVENT]].mean())
    return result


def in7(generation, validation, output, binding, config):
    frame, x, y, excess = in7_arrays(generation, validation)
    groups = frame.group.to_numpy()
    point = in7_statistics(x, y, excess, groups)
    def one(i):
        rng = np.random.default_rng(np.random.SeedSequence([SEED, 710, i]))
        selected = rng.integers(0, len(frame), len(frame))
        return in7_statistics(x[selected], y[selected], excess[selected], groups[selected])
    samples = draw_blocks(output, binding, "in7", config["draws"], one, config)
    results = {}
    for name, value in point.items():
        is_primary = name == "named_minus_event"
        clusters = int((groups == name.split("/")[1]).sum()) if name.startswith("group/") else len(frame)
        results[name] = estimate(value, [s[name] for s in samples], bar=0. if "transmission" in name else .1,
                                 clusters=clusters, record_kind="claim" if is_primary or name == "other_minus_event" else "texture",
                                 theory_tags=("H12-T3",))
    primary = results.pop("named_minus_event")
    transmission = results["transmission_event_minus_stance_z"]
    first = primary.get("first_line", "untouched-prompt stance comparison")
    if point["named_minus_event"] > 0 and transmission.get("estimate") is not None and transmission["estimate"] <= 0:
        first = "spread, not transmission; " + first
    per_item = {k: {"class": "named_stance" if k in NAMED else "other_stance" if k in OTHER_STANCE else "event" if k in EVENT else "unclassed",
                    "excess_error": results.pop("excess/" + k), "transmission_fisher_z": results.pop("transmission_z/" + k)} for k in old.APPRAISALS}
    for row in per_item.values():
        z = row["transmission_fisher_z"].get("estimate")
        row["transmission_correlation"] = None if z is None else float(np.tanh(z))
    return {"card": "IN7", "theory_tags": ["H12-T3"], "first_line": first, "texts": len(frame),
            "prompt_counts": {str(k): int(v) for k, v in frame.emotion.value_counts().items()},
            "prompt_groups": {str(k): str(v) for k, v in frame.groupby("emotion")["group"].first().items()},
            "mapped_prompts_excluded": list(MAPPED), "primary": primary, "secondary": results, "per_item": per_item,
            "transmission_stance_definition": list(NAMED + OTHER_STANCE),
            "selection_disclosure": "three named items selected from mapped prompts; those texts are excluded here",
            "class_reading": results["other_minus_event"].get("outcome", results["other_minus_event"].get("status")),
            "cluster_unit": "text, preserving complete five-reader panel"}


def load_inputs(inputs, config):
    for key in ("generation", "validation"):
        expected = config.get("fixture_source_pins", SOURCE_PINS)[key]
        if old.digest(Path(inputs[key])) != expected:
            raise ValueError("IN source pin mismatch")
    g, v = pd.read_parquet(inputs["generation"]), pd.read_parquet(inputs["validation"])
    if config.get("constructed_fixture", False):
        if not all(frame[key].astype(str).str.startswith("constructed-").all()
                   for frame in (g, v) for key in ("text_id", "prolific_id")):
            raise ValueError("fixture settings require constructed identities")
    for frame in (g, v):
        values = frame[old.APPRAISALS + ["intensity", "confidence"]].to_numpy(float)
        if not np.isfinite(values).all() or (values < 1).any() or (values > 5).any():
            raise ValueError("invalid source rating scale")
    if not config.get("constructed_fixture", False):
        if "fixture_source_pins" in config or config.get("draws") != 2000 or config.get("texture_draws") != 200:
            raise ValueError("human run cannot relax source or draw contract")
        if len(g) != 6558 or len(v) != 5955 or int(g.emotion.eq("fear").sum()) != 547:
            raise ValueError("qualified source census changed")
    panels(g, v)
    return g, v


def execute(output: Path, inputs: dict, config: dict):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    phase = config["phase"]
    if phase not in ("IN5", "IN6", "IN7"):
        raise ValueError("uncommissioned back-half phase")
    g, v = load_inputs(inputs, config)
    semantic = {k: value for k, value in config.items() if k != "max_new_blocks"}
    binding = hashlib.sha256(canonical({"inputs": {k: old.digest(Path(inputs[k])) for k in ("generation", "validation")},
                                       "module": old.digest(Path(__file__)), "original": old.digest(Path(old.__file__)), "config": semantic})).hexdigest()
    sealed(output / "BINDING.json", {"binding": binding, "phase": phase})
    try:
        if phase == "IN5":
            result = in5(g, output, binding, config)
        elif phase == "IN6":
            result = in6(g, v, output, binding, config)
        else:
            result = in7(g, v, output, binding, config)
    except YieldRequested:
        return {"status": "yielded", "complete_card": False, "reason": "sealed global-draw checkpoint or resource request"}
    result["source_binding"] = binding
    result["complete_card"] = True
    sealed(output / "RESULT.json", result)
    return result


def verify(output: Path, inputs: dict, config: dict):
    # The replay reads the source again and reconstructs every normalization,
    # panel and draw. It never treats execution checkpoints as verification.
    replay_config = {k: v for k, v in config.items() if k != "max_new_blocks"}
    result = execute(Path(output) / "independent-replay", inputs, replay_config)
    if result.get("status") == "yielded":
        return {**result, "verified": False}
    if canonical(result) != (Path(output) / "RESULT.json").read_bytes():
        raise ValueError("complete IN back-half replay mismatch")
    return {"verified": True, "full_source_and_draw_replay": True, "phase": config["phase"]}
