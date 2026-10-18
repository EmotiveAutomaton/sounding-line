"""D3 original-method companion: standardized latency and content adjustment.

DESIGN CHECK: preserve the frozen quintile primary and its route. This separate
descriptive model uses within-writer raw-latency z and z squared, with accepted
text length, novel-word fraction and context cosine covariates. Known fast,
middle and constant reversal patterns check direction. Whole-writer bootstrap
retains paired curve coefficients. It is a linear probability association,
not causal adjustment or a calibrated probability. The displayed curve is a
partial change from z=0; extrapolation support is explicit.
"""
from __future__ import annotations

import hashlib
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from runners.drive.cards import states_v2 as states
from runners.drive.cards import timing_events as original
from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_stats import sufficient, bind, check_binding
from runners.stage14.common import atomic, freeze
from runners.stage9.coauthor import units

CONFIG = dict(card="D3-content", bootstrap_draws=2000, seed=20261017)
INPUTS = {"session_index", "foundation_complete", "foundation_plan", "repo_root", "raw_roster", "prepared_sessions", "content_complete"}
FORECAST_SECONDS = 600


def extract(inputs, config, output=None, elapsed=None):
    if set(inputs) != INPUTS or config != CONFIG or set(config) != set(CONFIG) or any(type(config[k]) is not type(v) for k, v in CONFIG.items()):
        raise ValueError("exact D3 content configuration and inputs required")
    root = Path(inputs["repo_root"]).resolve()
    prepared = Path(inputs["prepared_sessions"]).resolve()
    if read(inputs["foundation_plan"])["pins"].get(prepared.relative_to(root).as_posix()) != filehash(prepared):
        raise ValueError("prepared metadata not authenticated by foundation")
    terminal = Path(inputs["content_complete"])
    complete = read(terminal)
    if complete.get("status") != "COMPLETE":
        raise ValueError("completed content features required")
    for name in ("RECORDS.json", "PLAN.json"):
        if complete["outputs"].get(name) != filehash(terminal.parent / name):
            raise ValueError("content feature completion changed")
    if read(terminal.parent / "PLAN.json")["pins"].get(prepared.relative_to(root).as_posix()) != filehash(prepared):
        raise ValueError("content features use different prepared metadata")
    records = read(terminal.parent / "RECORDS.json")
    content = {r["key"]: r for r in records}
    sessions = read(prepared)
    metadata = {(s["session"], r["ordinal"]): r for s in sessions for r in s["rows"]}
    if len(content) != len(records) or len(metadata) != sum(len(s["rows"]) for s in sessions) or set(content) != {r["key"] for r in metadata.values()}:
        raise ValueError("content/prepared decision identity coverage differs")
    source = {k: inputs[k] for k in INPUTS - {"prepared_sessions", "content_complete"}}
    by_session = defaultdict(list)
    for row in original.extract_rows(source, "D3"):
        by_session[row["session"]].append(row)
    rows, excluded = [], Counter()
    for done, session in enumerate(sessions, 1):
        unit = []
        for row in by_session.pop(session["session"], []):
            meta = metadata[(row["session"], row["ordinal"])]
            features = content[meta["key"]]
            if meta["writer"] != row["writer"] or meta["session"] != row["session"] or features["writer"] != row["writer"] or features["session"] != row["session"] or len(features["cosine"]) != len(meta["menu"]) or len(features["scalars"]) != len(meta["menu"]):
                raise ValueError("content/source writer or menu identity differs")
            matches = [i for i, text in enumerate(meta["menu"]) if text == meta["inserted"]]
            if not matches:
                excluded["accepted text absent from prepared menu"] += 1
                continue
            text = meta["inserted"]
            if len(units(text)) != row["original_utf16"]:
                raise ValueError("accepted source span and prepared text length differ")
            prior = set(meta["document"].lower().split())
            novelty = len(set(text.lower().split()) - prior) / max(1, len(set(text.lower().split())))
            expected = [len(text), len(text.split()), novelty]
            for index in matches:
                if len(features["scalars"][index]) != 4 or any(not math.isclose(float(a), b, rel_tol=0, abs_tol=1e-12) for a, b in zip(features["scalars"][index][:3], expected)):
                    raise ValueError("content scalar features do not reconstruct from source text")
            cosines = [features["cosine"][i] for i in matches]
            if not all(math.isfinite(c) and -1.000001 <= c <= 1.000001 for c in cosines) or any(c != cosines[0] for c in cosines):
                raise ValueError("ambiguous or invalid selected content cosine")
            unit.append(dict(row, key=meta["key"], log_characters=math.log1p(len(text)), log_words=math.log1p(len(text.split())),
                             novel_word_fraction=novelty, context_cosine=cosines[0], duplicate_identical_candidates=len(matches)))
        rows.extend(unit)
        if output is not None:
            checkpoint = output / "sessions" / (hashlib.sha256(session["session"].encode()).hexdigest() + ".json")
            freeze(checkpoint, dict(session=session["session"], rows=unit))
            atomic(output / "CONTENT_PROGRESS.json", dict(completed_sessions=done, total_sessions=len(sessions), active_seconds=elapsed()))
            if done == math.ceil(len(sessions)/10) and not (output / "FIRST_TENTH.json").exists():
                projection = 2 * elapsed() * len(sessions) / done + 60
                freeze(output / "FIRST_TENTH.json", dict(completed_sessions=done, total_sessions=len(sessions), elapsed_seconds=elapsed(),
                       projected_cpu_seconds=projection, forecast_cpu_seconds=FORECAST_SECONDS, includes_fresh_source_replay=True))
                if projection > 2 * FORECAST_SECONDS:
                    atomic(output / "YIELD_REQUEST.json", dict(reason="first_tenth_projection_exceeds_twice_forecast"))
            if elapsed() > 3 * FORECAST_SECONDS:
                raise RuntimeError("D3 content threefold time ceiling")
            if (output / "YIELD_REQUEST.json").exists():
                raise original.CooperativeYield("saved source-authenticated content session")
    if by_session:
        raise ValueError("accepted source sessions absent from prepared metadata")
    return rows, dict(excluded)


def coefficients(groups):
    xx, xy = sum(g["xx"] for g in groups), sum(g["xy"] for g in groups)
    keep = np.flatnonzero(np.diag(xx) > 1e-10)
    if not {0, 1} <= set(keep):
        raise ValueError("linear/quadratic standardized latency not supported")
    scale = np.sqrt(np.diag(xx)[keep])
    a = xx[np.ix_(keep, keep)] / np.outer(scale, scale)
    if np.linalg.matrix_rank(a, tol=1e-9) != len(keep):
        raise ValueError("adjusted latency design not identifiable")
    beta = np.zeros(len(xy))
    beta[keep] = np.linalg.solve(a, xy[keep]/scale)/scale
    return beta


def contrast(effect, samples, writers, config):
    low, high = np.quantile(samples, [.025, .975]).tolist()
    se = float(np.std(samples, ddof=1))
    z = effect/se if se > 0 else None
    return dict(effect=float(effect), ci_low=low, ci_high=high, bootstrap_se=se, z=z,
                wald_p_two_sided=math.erfc(abs(z)/math.sqrt(2)) if z is not None else None,
                p_reference="approximate two-sided normal Wald; descriptive; state remains percentile-CI based",
                state=states.contrast_state(effect, low, high), writers=writers, expected_direction=1,
                bootstrap_draws=config["bootstrap_draws"], seed=config["seed"], interval="whole-writer percentile bootstrap, jointly retained curve coefficients")


def summarize(rows, exclusions, config):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["writer"]].append(row)
    observations, summaries, unsupported = [], [], []
    for writer in sorted(grouped):
        records = sorted(grouped[writer], key=lambda r: (r["session"], r["ordinal"]))
        latency = np.array([r["latency"] for r in records])
        scale = float(latency.std(ddof=0))
        if scale == 0:
            unsupported.append(writer)
            continue
        z = (latency-latency.mean())/scale
        quintiles = np.minimum(4, np.floor(5*(rankdata(latency, method="average")-.5)/len(latency)).astype(int))
        summaries.append(dict(writer=writer, z_min=float(z.min()), z_max=float(z.max()),
                              quintile_counts=[int(sum(quintiles == q)) for q in range(5)],
                              quintile_rates=[float(np.mean([r["reversed"] for r, k in zip(records, quintiles) if k == q])) if np.any(quintiles == q) else None for q in range(5)]))
        for row, value in zip(records, z):
            observations.append(dict(row, z=float(value)))
    details = dict(writer_summaries=summaries, source_exclusions=exclusions, constant_latency_writers=unsupported,
                   curve_scope="Partial probability change relative to each writer's mean latency; not absolute probabilities; points outside writer observed z range are extrapolations")
    if len(summaries) < 3:
        return dict(state="invalid", card="D3-content", reason="fewer than three supported writers", descriptive_only=True), details
    x = [[r["z"], r["z"]**2, r["log_characters"], r["log_words"], r["novel_word_fraction"], r["context_cosine"]] for r in observations]
    y, writers = [float(r["reversed"]) for r in observations], [r["writer"] for r in observations]
    groups = sufficient(x, y, writers, within=True)
    rng = np.random.default_rng(config["seed"])
    try:
        beta = coefficients(groups)
        samples = np.array([coefficients([groups[i] for i in rng.integers(0, len(groups), len(groups))]) for _ in range(config["bootstrap_draws"])])
        shuffled = np.array(y)
        for writer in sorted(set(writers)):
            ix = np.flatnonzero(np.array(writers) == writer)
            shuffled[ix] = rng.permutation(shuffled[ix])
        null_groups = sufficient(x, shuffled, writers, within=True)
        null_beta = coefficients(null_groups)
        null_samples = np.array([coefficients([null_groups[i] for i in rng.integers(0, len(groups), len(groups))]) for _ in range(config["bootstrap_draws"])])
    except ValueError as exc:
        return dict(state="invalid", card="D3-content", reason=str(exc), descriptive_only=True), details
    result = contrast(-beta[0]+beta[1], -samples[:, 0]+samples[:, 1], len(groups), config)
    result.update(card="D3-content", descriptive_only=True, ladder_update=False,
                  contrast="content-adjusted reversal change at one within-writer latency standard deviation faster than the mean",
                  standardized_latency="raw observed seconds, within-writer population mean/standard deviation",
                  content_covariates=["log1p accepted characters", "log1p accepted whitespace words", "novel-word fraction relative to preceding document", "context MiniLM cosine"],
                  long_latency=contrast(beta[0]+beta[1], samples[:, 0]+samples[:, 1], len(groups), config),
                  quadratic=contrast(beta[1], samples[:, 1], len(groups), config),
                  controls=dict(within_writer_reversal_shuffle=contrast(-null_beta[0]+null_beta[1], -null_samples[:, 0]+null_samples[:, 1], len(groups), config)),
                  observations=len(observations), route="Companion only; original shortest/middle and longest/middle quintile routes remain unchanged")
    details.update(coefficients=beta.tolist(), bootstrap_coefficients=samples.tolist(), design=x, outcomes=y, writers=writers,
                   curve=[dict(latency_z=z, **contrast(beta[0]*z+beta[1]*z*z, samples[:, 0]*z+samples[:, 1]*z*z, len(groups), config),
                               writers_covering_location=sum(r["z_min"] <= z <= r["z_max"] for r in summaries)) for z in (-2, -1, 0, 1, 2)])
    return result, details


def curve_svg(details):
    if "curve" not in details:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="120"><text x="20" y="60">Adjusted curve invalid; see retained report.</text></svg>\n'
    curve = details["curve"]
    bound = max(.05, max(abs(r[k]) for r in curve for k in ("effect", "ci_low", "ci_high"))) * 1.15
    xp = lambda z: 70 + (z+2)*125
    yp = lambda y: 200 - y/bound*140
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="640" height="410" viewBox="0 0 640 410">',
                '<rect width="640" height="410" fill="white"/>',
                '<text x="35" y="28" font-family="sans-serif" font-size="16">D3: adjusted reversal change from mean latency</text>',
                '<path d="M70 60V340H570" stroke="black" fill="none"/>',
                f'<path d="M70 {yp(0)}H570" stroke="gray" stroke-dasharray="4 4"/>']
    for row in curve:
        x = xp(row["latency_z"])
        elements.append(f'<path d="M{x} {yp(row["ci_low"])}V{yp(row["ci_high"])}" stroke="#31688e" stroke-width="2"/>')
        elements.append(f'<circle cx="{x}" cy="{yp(row["effect"])}" r="4" fill="#31688e"/>')
        elements.append(f'<text x="{x-7}" y="360" font-family="sans-serif" font-size="12">{row["latency_z"]}</text>')
    points = ' '.join(f'{xp(r["latency_z"])},{yp(r["effect"])}' for r in curve)
    elements.extend([f'<polyline points="{points}" fill="none" stroke="#31688e"/>',
                     '<text x="120" y="388" font-family="sans-serif" font-size="13">Within-writer latency standard deviations</text>',
                     '<text x="120" y="405" font-family="sans-serif" font-size="10">Bars: 95% writer bootstrap. Extrapolation support is retained in the report.</text>',
                     f'<text x="8" y="64" font-size="11">+{bound:.3f}</text>',
                     f'<text x="8" y="340" font-size="11">-{bound:.3f}</text>', '</svg>\n'])
    return ''.join(elements)


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    if (output / "TIMING_BINDINGS.json").exists():
        return verify(output, inputs, config)["primary"]
    freeze(output / "CONTENT_RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(__file__),
           inputs={k: str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k, v in inputs.items()}))
    prior = read(output / "CONTENT_PROGRESS.json")["active_seconds"] if (output / "CONTENT_PROGRESS.json").exists() else 0.
    started = time.monotonic()
    elapsed = lambda: prior + time.monotonic()-started
    try:
        rows, exclusions = extract(inputs, config, output, elapsed)
    except original.CooperativeYield as exc:
        return dict(status="yielded", card="D3-content", reason=str(exc))
    result, details = summarize(rows, exclusions, config)
    if elapsed() > 3 * FORECAST_SECONDS:
        raise RuntimeError("D3 content threefold time ceiling")
    freeze(output / "CONTENT_ROWS.json", dict(rows=rows, exclusions=exclusions))
    freeze(output / "CONTENT_PRIMARY.json", result)
    freeze(output / "CONTENT_DETAILS.json", details)
    svg = curve_svg(details)
    graph = output / "LATENCY_CURVE.svg"
    if graph.exists() and graph.read_text(encoding="utf-8") != svg:
        raise ValueError("immutable latency curve changed")
    graph.write_text(svg, encoding="utf-8", newline="\n")
    freeze(output / "CONTENT_TIMING.json", dict(wall_seconds=elapsed(), forecast_cpu_seconds=FORECAST_SECONDS))
    bind(output, inputs, config, ["CONTENT_ROWS.json", "CONTENT_PRIMARY.json", "CONTENT_DETAILS.json", "LATENCY_CURVE.svg"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    check_binding(output, inputs, config)
    rows, exclusions = extract(inputs, config)
    result, details = summarize(rows, exclusions, config)
    if read(Path(output) / "CONTENT_ROWS.json") != dict(rows=rows, exclusions=exclusions) or read(Path(output) / "CONTENT_PRIMARY.json") != result or read(Path(output) / "CONTENT_DETAILS.json") != details:
        raise ValueError("D3 content outputs do not reconstruct")
    if (Path(output) / "LATENCY_CURVE.svg").read_text(encoding="utf-8") != curve_svg(details):
        raise ValueError("D3 content curve does not reconstruct")
    return dict(verified=True, primary=result)
