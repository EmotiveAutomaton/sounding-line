"""D24 single provenance-schema repair; frozen primary and pilot remain intact.

DESIGN CHECK: unusable raw menu insertions remain non-typed API provenance and
are excluded from P2-eligible accepted closure/rates. Each omission must be
reproduced by the canonical source extractor, not inferred from absence alone.
Canonical append, final document, duration and eligible decision coverage stay
mandatory. Saved scored sessions remain byte-identical; previous elapsed time
counts against the original threefold cap. No scoring or statistical change.
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

from runners.drive.cards import timing_closure as original
from runners.drive.cards import timing_closure_measure as measure
from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_events import source_sessions, session_words, CooperativeYield
from runners.drive.cards.timing_stats import bind, check_binding
from runners.stage14.common import atomic, freeze
from runners.stage9.coauthor import units, text_of, delta_ops, apply_delta, replay as canonical_replay
from runners.drive.cards.timing_closure_measure import nonprompt_words, SENTENCE

FORECAST_SECONDS = original.FORECAST_SECONDS
SOURCE_INPUTS = original.SOURCE_INPUTS
EXTRA_INPUTS = {"failed_plan", "failed_record"}

def replay(events, timeline):
    if not events or events[0]["eventName"] != "system-initialize":
        raise ValueError("D24 initialization absent")
    times = [float(e["eventTimestamp"]) for e in events]
    if not all(math.isfinite(t) for t in times) or times != sorted(times):
        raise ValueError("D24 chronology invalid")
    doc = units(events[0]["currentDoc"])
    owners = [("prompt", 0)] * len(doc)
    pending = current = None
    accepted = {d["ordinal"] for d in timeline["decisions"] if d["handling"] in {"accept", "edit"}}
    found, entries, requests = set(), [], []
    exclusions, canonical = [], None
    for ordinal, event in enumerate(events):
        name, source = event["eventName"], event.get("eventSource")
        seconds = (times[ordinal] - times[0]) / 1000
        if name == "suggestion-get":
            requests.append(seconds)
        if name == "suggestion-open":
            current = ordinal
        if name == "suggestion-select":
            pending = current
        delta = event.get("textDelta")
        if delta in (None, ""):
            continue
        before, old_owners = text_of(doc), owners
        kind = "typed" if source == "user" else "accepted" if pending is not None else "api_unknown"
        owner = (kind, ordinal)
        doc, owners, _ = apply_delta(doc, owners, delta, insertion_owner=owner)
        after = text_of(doc)
        texts = []
        if kind == "accepted":
            if source != "api" or pending in found or not before.endswith("\n") or not after.startswith(before[:-1]) or not after.endswith("\n"):
                raise ValueError("D24 accepted insertion lacks canonical P2 correspondence")
            extra = len(doc) - len(old_owners)
            if extra <= 0:
                raise ValueError("empty accepted insertion")
            owners = old_owners[:-1] + [owner] * extra + old_owners[-1:]
            if pending in accepted:
                texts.append(after[len(before)-1:-1])
                found.add(pending)
            else:
                # P2 retains the document from excluded menus but its decision
                # table contains only source-supported, usable decisions.
                if canonical is None:
                    checked = canonical_replay(events)
                    if not checked["reconstructed"] or checked["final_document"] != timeline["final_document"]:
                        raise ValueError("D24 excluded API provenance does not reconstruct")
                    canonical = {d["ordinal"]: d for d in checked["events"]}
                decision = canonical.get(pending)
                if decision is None or decision["usable"] or not decision["exclusion"]:
                    raise ValueError("D24 omitted API decision has no authenticated canonical exclusion")
                owner = ("api_excluded", ordinal)
                owners = old_owners[:-1] + [owner] * extra + old_owners[-1:]
                exclusions.append(dict(menu_ordinal=pending, insertion_ordinal=ordinal,
                                       reason=decision["exclusion"], inserted_utf16=extra))
            pending = None
        elif kind == "typed" and any(any(c in op.get("insert", "") for c in ".!?\n") for op in delta_ops(delta)):
            # A typed sentence is emitted only when this delta supplies its
            # terminal punctuation/newline, avoiding repeated partial drafts.
            offsets, at = [0], 0
            for char in after:
                at += len(units(char))
                offsets.append(at)
            for match in SENTENCE.finditer(after):
                text = match.group()
                nonspace = [j for j in range(match.start(), match.end()) if not after[j].isspace()]
                if not nonspace:
                    continue
                terminal = max(j for j in range(match.start(), match.end()) if after[j] in ".!?\n")
                span_owners = owners[offsets[match.start()]:offsets[match.end()]]
                wholly_typed = all(owners[k][0] == "typed" for j in nonspace for k in range(offsets[j], offsets[j+1]))
                if wholly_typed and owner in owners[offsets[terminal]:offsets[terminal+1]] and any(o == owner for o in span_owners):
                    texts.append(text)
        if texts:
            length = nonprompt_words(doc, owners)
            entries.extend(dict(kind=kind, ordinal=ordinal, seconds=seconds, words_at_event=length, text=text) for text in texts if text.strip())
    if text_of(doc) != timeline["final_document"] or found != accepted:
        raise ValueError("D24 raw/P2 replay correspondence failed")
    duration = (times[-1] - times[0]) / 1000
    if duration != timeline["duration_seconds"]:
        raise ValueError("D24 raw/P2 duration differs")
    return dict(entries=entries, requests=requests, duration_seconds=duration, excluded_api_insertions=exclusions)


def score_rows(inputs, encoder, output=None, elapsed=None):
    by_writer = defaultdict(list)
    source = {k: inputs[k] for k in SOURCE_INPUTS}
    for index, timeline, _ in source_sessions(source, "raw_roster"):
        by_writer[index["writer"]].append(session_words(timeline))
    medians = {w: float(np.median(v)) for w, v in by_writer.items()}
    total = len(read(inputs["session_index"]))
    sessions, exclusions = [], []
    for done, (index, timeline, metadata) in enumerate(source_sessions(source, "raw_roster"), 1):
        raw_path = (Path(inputs["repo_root"]) / metadata["path"]).resolve()
        with raw_path.open(encoding="utf-8") as stream:
            raw = [json.loads(line) for line in stream]
        replayed = replay(raw, timeline)
        exclusions.extend(dict(session=index["session"], **r) for r in replayed["excluded_api_insertions"])
        session = dict(session=index["session"], writer=index["writer"], final_words=session_words(timeline),
                       median_final_words=medians[index["writer"]], duration_seconds=replayed["duration_seconds"],
                       requests=replayed["requests"], accepted_times=[r["seconds"] for r in replayed["entries"] if r["kind"] == "accepted"], entries=[])
        checkpoint = output / "sessions" / (hashlib.sha256(index["session"].encode()).hexdigest() + ".json") if output else None
        source_binding = dict(p2=index["sha256"], raw=metadata["source_sha256"])
        saved = None
        if checkpoint is not None and checkpoint.exists():
            saved = read(checkpoint)
            if saved["sources"] != source_binding or read(checkpoint.with_suffix(".receipt.json"))["sha256"] != filehash(checkpoint):
                raise ValueError("D24 scored session checkpoint changed")
        for entry in replayed["entries"]:
            median = session["median_final_words"]
            location = (entry["words_at_event"] - median) / median if median > 0 else None
            # All accepted event times remain for rates, even when no closure
            # score is needed. Score the fixed union of all registered windows.
            eligible = session["duration_seconds"] > 600 and (abs(entry["seconds"] - 600) <= 180 or location is not None and abs(location) <= .2)
            if eligible:
                record = dict(entry, median_location=location)
                if saved is not None:
                    position = len(session["entries"])
                    stored = saved["session"]["entries"][position]
                    if {k: stored[k] for k in record} != record:
                        raise ValueError("D24 checkpoint text/identity differs from raw source")
                    record["score"] = stored["score"]
                else:
                    record["score"] = encoder.score(entry["text"])
                session["entries"].append(record)
        if saved is not None and saved["session"] != session:
            raise ValueError("D24 checkpoint source reconstruction differs")
        if checkpoint is not None:
            freeze(checkpoint, dict(sources=source_binding, session=session))
            freeze(checkpoint.with_suffix(".receipt.json"), dict(sha256=filehash(checkpoint)))
        sessions.append(session)
        if output is not None:
            active = elapsed()
            atomic(output / "CLOSURE_PROGRESS.json", dict(completed_scored_sessions=done, total_sessions=total, active_seconds=active))
            overshoot = False
            if done == math.ceil(total / 10) and not (output / "FIRST_TENTH.json").exists():
                projection = 2 * active * total / done + 120
                overshoot = projection > 2 * FORECAST_SECONDS
                freeze(output / "FIRST_TENTH.json", dict(completed_scored_sessions=done, total_sessions=total,
                       elapsed_seconds=active, projected_cpu_seconds=projection, forecast_cpu_seconds=FORECAST_SECONDS,
                       includes_fresh_source_and_encoder_verification=True, reserved_statistics_seconds=120))
            if active > 3 * FORECAST_SECONDS:
                raise RuntimeError("D24 threefold active-time ceiling")
            if overshoot or (output / "YIELD_REQUEST.json").exists():
                if overshoot and not (output / "YIELD_REQUEST.json").exists():
                    atomic(output / "YIELD_REQUEST.json", dict(reason="first_tenth_projection_exceeds_twice_forecast"))
                raise CooperativeYield("saved fully scored source-bound session")
    return sessions, exclusions


def failure_identity(inputs, config):
    """Authenticate the one failed original attempt and its reusable bytes."""
    source = {k: v for k, v in inputs.items() if k not in EXTRA_INPUTS}
    original.validate(source, config)
    if config != original.config_for("primary") or set(inputs) != set(source) | EXTRA_INPUTS:
        raise ValueError("exact primary recovery inputs and configuration required")
    plan_path, failed_path = Path(inputs["failed_plan"]), Path(inputs["failed_record"])
    if plan_path.name != "PLAN.json" or failed_path != plan_path.parent / "FAILED.json":
        raise ValueError("original failure identity paths differ")
    plan, failed = read(plan_path), read(failed_path)
    if plan["module"] != "runners.drive.cards.timing_closure" or plan["config"] != config or plan["inputs"] != source:
        raise ValueError("original failed source/configuration differs")
    if failed.get("status") != "FAILED" or failed.get("engineering_retry_available") is not True:
        raise ValueError("single engineering recovery unavailable")
    for name, expected in plan["pins"].items():
        if filehash(name) != expected:
            raise ValueError("original failed source pin changed")
    old = plan_path.parent / "output"
    expected = dict(config=config, source_sha256=filehash(original.__file__), measure_sha256=filehash(measure.__file__),
                    inputs={k: str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k, v in source.items()})
    if read(old / "CLOSURE_RUN_BINDINGS.json") != expected:
        raise ValueError("failed D24 run bindings changed")
    progress = read(old / "CLOSURE_PROGRESS.json")
    saved = {}
    for checkpoint in sorted((old / "sessions").glob("*.json")):
        if checkpoint.name.endswith(".receipt.json"):
            continue
        receipt = checkpoint.with_suffix(".receipt.json")
        if read(receipt)["sha256"] != filehash(checkpoint):
            raise ValueError("original scored checkpoint changed")
        for path in (checkpoint, receipt):
            saved[path.relative_to(old).as_posix()] = filehash(path)
    if len(saved) != 2 * progress["completed_scored_sessions"]:
        raise ValueError("original scored checkpoint coverage differs")
    prior = max(float(progress["active_seconds"]),
                (datetime.fromisoformat(failed["at"]) - datetime.fromisoformat(plan["at"])).total_seconds())
    if not math.isfinite(prior) or prior < 0 or prior >= 3 * FORECAST_SECONDS:
        raise ValueError("original cumulative allowance unavailable")
    identity = dict(failed_plan_sha256=filehash(plan_path), failed_record_sha256=filehash(failed_path),
                    old_binding_sha256=filehash(old / "CLOSURE_RUN_BINDINGS.json"),
                    old_progress_sha256=filehash(old / "CLOSURE_PROGRESS.json"),
                    retained_files=saved, charged_prior_seconds=prior, cumulative_cap_seconds=3 * FORECAST_SECONDS)
    return source, old, identity


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    started = time.monotonic()
    source, old, identity = failure_identity(inputs, config)
    if (output / "TIMING_BINDINGS.json").exists():
        return verify(output, inputs, config)["primary"]
    freeze(output / "RECOVERY_SOURCE.json", identity)
    freeze(output / "RECOVERY_RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(__file__),
           inputs={k: str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k, v in inputs.items()}))
    for name, expected in identity["retained_files"].items():
        target = output / name
        if target.exists():
            if filehash(target) != expected:
                raise ValueError("reused original checkpoint bytes differ")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write((old / name).read_bytes())
    prior = read(output / "CLOSURE_PROGRESS.json")["active_seconds"] if (output / "CLOSURE_PROGRESS.json").exists() else identity["charged_prior_seconds"]
    elapsed = lambda: prior + time.monotonic() - started
    original.authorize_pilot(source)
    encoder = measure.Encoder(source)
    try:
        sessions, exclusions = score_rows(source, encoder, output, elapsed)
    except CooperativeYield as exc:
        return dict(status="yielded", card="D24", reason=str(exc))
    result, details = original.summarize(sessions, config)
    if elapsed() > 3 * FORECAST_SECONDS:
        raise RuntimeError("D24 cumulative threefold active-time ceiling")
    artifacts = {"CLOSURE_ROWS.json": sessions, "CLOSURE_PRIMARY.json": result,
                 "CLOSURE_DETAILS.json": details, "CLOSURE_SOURCE_EXCLUSIONS.json": exclusions}
    for name, value in artifacts.items():
        freeze(output / name, value)
    freeze(output / "CLOSURE_TIMING.json", dict(wall_seconds=elapsed(), charged_prior_seconds=identity["charged_prior_seconds"],
           forecast_cpu_seconds=FORECAST_SECONDS, cumulative_cap_seconds=3 * FORECAST_SECONDS))
    bind(output, inputs, config, list(artifacts) + ["RECOVERY_SOURCE.json", "CLOSURE_TIMING.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    started = time.monotonic()
    output = Path(output)
    source, _, identity = failure_identity(inputs, config)
    check_binding(output, inputs, config)
    if read(output / "RECOVERY_SOURCE.json") != identity:
        raise ValueError("recovery source receipt differs")
    original.authorize_pilot(source)
    sessions, exclusions = score_rows(source, measure.Encoder(source))
    result, details = original.summarize(sessions, config)
    for name, value in (("CLOSURE_ROWS.json", sessions), ("CLOSURE_PRIMARY.json", result),
                        ("CLOSURE_DETAILS.json", details), ("CLOSURE_SOURCE_EXCLUSIONS.json", exclusions)):
        if read(output / name) != value:
            raise ValueError("D24 recovered outputs do not reconstruct")
    total = read(output / "CLOSURE_TIMING.json")["wall_seconds"] + time.monotonic() - started
    if total > 3 * FORECAST_SECONDS:
        raise RuntimeError("D24 cumulative execute/verify allowance exhausted")
    return dict(verified=True, primary=result, preserved_checkpoint_files=len(identity["retained_files"]),
                exclusions_reconstructed=len(exclusions), cumulative_cap_seconds=3 * FORECAST_SECONDS)

