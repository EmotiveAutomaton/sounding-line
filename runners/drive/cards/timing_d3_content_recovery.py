"""D3 content companion's separate canonical-source recovery.

DESIGN CHECK: source-excluded repeated API spans remain excluded. Frozen
content scalars, native cosine, standardized-latency model, bootstrap and SVG
are unchanged. Fully joined source sessions now form safe checkpoints, so the
first-tenth forecast measures raw replay plus actual content joining together.
The original failed extraction produced no content checkpoints. Its time still
counts against the original 1800-second cap; no scoring or tolerance change.
"""
from __future__ import annotations
import hashlib
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from . import timing_d3_content as legacy
from . import timing_events as original
from . import timing_events_recovery as recovery
from .timing_census import read, filehash
from .timing_stats import bind, check_binding
from runners.stage9.coauthor import units
from runners.stage14.common import atomic, freeze

CONFIG, INPUTS = legacy.CONFIG, legacy.INPUTS
FORECAST_SECONDS = legacy.FORECAST_SECONDS

def extract(inputs, config, output=None, elapsed=None, charged_prior=0.):
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
    session_lookup = {s["session"]: s for s in sessions}
    if len(session_lookup) != len(sessions) or set(session_lookup) != {r["session"] for r in read(inputs["session_index"])}:
        raise ValueError("content and source session coverage differs")
    rows, excluded, raw_exclusions = [], Counter(), []
    for done, (index, raw_rows, source_excluded) in enumerate(recovery.source_units(source), 1):
        session = session_lookup[index["session"]]
        raw_exclusions.extend(source_excluded)
        unit = []
        for row in raw_rows:
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
                projection = charged_prior + 2 * (elapsed()-charged_prior) * len(sessions) / done + 60
                freeze(output / "FIRST_TENTH.json", dict(completed_sessions=done, total_sessions=len(sessions), elapsed_seconds=elapsed(),
                       charged_prior_seconds=charged_prior, projected_cpu_seconds=projection, forecast_cpu_seconds=FORECAST_SECONDS, includes_fresh_source_replay=True))
                if projection > 2 * FORECAST_SECONDS:
                    atomic(output / "YIELD_REQUEST.json", dict(reason="first_tenth_projection_exceeds_twice_forecast"))
            if elapsed() > 3 * FORECAST_SECONDS:
                raise RuntimeError("D3 content threefold time ceiling")
            if (output / "YIELD_REQUEST.json").exists():
                raise original.CooperativeYield("saved source-authenticated content session")
    order = {s["session"]: i for i, s in enumerate(sessions)}
    rows.sort(key=lambda r: (order[r["session"]], r["ordinal"]))
    return rows, dict(excluded), raw_exclusions


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    started = time.monotonic()
    source, old, identity = recovery.failure_identity(inputs, config, legacy, "CONTENT")
    if (output / "TIMING_BINDINGS.json").exists():
        return verify(output, inputs, config)["primary"]
    recovery.restore(output, old, identity)
    freeze(output / "RECOVERY_RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(__file__),
           inputs={k: str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k, v in inputs.items()}))
    prior = read(output / "CONTENT_PROGRESS.json")["active_seconds"] if (output / "CONTENT_PROGRESS.json").exists() else identity["charged_prior_seconds"]
    elapsed = lambda: prior + time.monotonic() - started
    try:
        rows, excluded, raw_exclusions = extract(source, config, output, elapsed, identity["charged_prior_seconds"])
    except original.CooperativeYield as exc:
        return dict(status="yielded", card="D3-content", reason=str(exc))
    result, details = legacy.summarize(rows, excluded, config)
    if elapsed() > 3 * FORECAST_SECONDS:
        raise RuntimeError("D3 content cumulative threefold ceiling")
    artifacts = {"CONTENT_ROWS.json": dict(rows=rows, exclusions=excluded), "CONTENT_PRIMARY.json": result,
                 "CONTENT_DETAILS.json": details, "SOURCE_EXCLUSIONS.json": raw_exclusions}
    for name, value in artifacts.items():
        freeze(output / name, value)
    svg, graph = legacy.curve_svg(details), output / "LATENCY_CURVE.svg"
    if graph.exists() and graph.read_text(encoding="utf-8") != svg:
        raise ValueError("immutable latency curve changed")
    graph.write_text(svg, encoding="utf-8", newline="\n")
    freeze(output / "CONTENT_TIMING.json", dict(cumulative_seconds=elapsed(),
           charged_prior_seconds=identity["charged_prior_seconds"], cap_seconds=3 * FORECAST_SECONDS))
    bind(output, inputs, config, list(artifacts) + ["CONTENT_TIMING.json", "RECOVERY_SOURCE.json", "LATENCY_CURVE.svg"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    started = time.monotonic()
    source, _, identity = recovery.failure_identity(inputs, config, legacy, "CONTENT")
    check_binding(output, inputs, config)
    if read(output / "RECOVERY_SOURCE.json") != identity:
        raise ValueError("content recovery identity changed")
    rows, excluded, raw_exclusions = extract(source, config)
    result, details = legacy.summarize(rows, excluded, config)
    artifacts = {"CONTENT_ROWS.json": dict(rows=rows, exclusions=excluded), "CONTENT_PRIMARY.json": result,
                 "CONTENT_DETAILS.json": details, "SOURCE_EXCLUSIONS.json": raw_exclusions}
    if any(read(output / name) != value for name, value in artifacts.items()):
        raise ValueError("D3 content recovered source/output does not reconstruct")
    if (output / "LATENCY_CURVE.svg").read_text(encoding="utf-8") != legacy.curve_svg(details):
        raise ValueError("D3 content recovered curve does not reconstruct")
    if read(output / "CONTENT_TIMING.json")["cumulative_seconds"] + time.monotonic() - started > 3 * FORECAST_SECONDS:
        raise RuntimeError("D3 content execute/verify cumulative cap exceeded")
    return dict(verified=True, primary=result, excluded_api_insertions=len(raw_exclusions),
                preserved_checkpoint_files=len(identity["retained_files"]))

