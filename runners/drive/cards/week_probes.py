"""NP1: count authenticated probe-like events without inferring information gain.

DESIGN CHECK (2026-10-20): LESSONS sections 3-5.
NULL: empty sessions remain in the denominator and give zero events.
ALTERNATIVE: inserting a qualifying correction or maximal dismissal run raises
only its own count. Duplicate identities, altered sources and invalid decisions
fail closed. Exactly one event/session is common; below one is rare. Counts
cannot establish the maker's intent or identify Ghost's probe types.
"""
from collections import defaultdict
from pathlib import Path
import math

from .events_d4_sources import bind_completed
from .menus_io import read, sha256, write

CONFIG = dict(card="NP1", schema_version=1, minimum_dismissals=3,
              deleted_share_numerator=4, deleted_share_denominator=5)
INPUTS = {"sessions", "d39_failures", "d39_inputs", "d39_completion"}
KINDS = ("accepted_text_corrections", "dismissal_runs", "repeat_prompt_sessions")


def load(inputs, config):
    if set(inputs) != INPUTS or config != CONFIG:
        raise ValueError("Frozen NP1 inputs or configuration differ")
    for key in ("d39_failures", "d39_inputs"):
        bind_completed(inputs["d39_completion"], inputs[key])
    binding = read(inputs["d39_inputs"])
    session_path = str(Path(inputs["sessions"]))
    if (Path(binding["paths"]["sessions"]).resolve() != Path(session_path).resolve()
            or binding["pins"].get(session_path) != sha256(session_path)):
        raise ValueError("D39 session source binding differs")
    return read(session_path), read(inputs["d39_failures"])


def count_sessions(sessions, failures, config=CONFIG):
    if config != CONFIG:
        raise ValueError("Frozen NP1 configuration differs")
    index = {}
    writers = defaultdict(list)
    menus = {}
    for session in sessions:
        sid = session["session"]
        if sid in index or not session["writer"] or not session["prompt"]:
            raise ValueError("Duplicate session or absent writer/prompt")
        if not math.isfinite(session["timestamp"]):
            raise ValueError("Nonfinite session date")
        index[sid] = dict(session=sid, writer=session["writer"],
                         **{kind: 0 for kind in KINDS})
        writers[session["writer"]].append(session)
        own = {}
        run = 0
        for row in sorted(session["rows"], key=lambda x: x["ordinal"]):
            if (row["session"] != sid or row["writer"] != session["writer"]
                    or row["ordinal"] in own
                    or row["handling"] not in {"accept", "edit", "dismiss", "ignore"}):
                raise ValueError("Ambiguous or inconsistent menu identity")
            own[row["ordinal"]] = row
            if row["handling"] == "dismiss":
                run += 1
            else:
                index[sid]["dismissal_runs"] += int(run >= 3)
                run = 0
        index[sid]["dismissal_runs"] += int(run >= 3)
        menus[sid] = own

    seen = set()
    for event in failures:
        sid = event["session"]
        key = (sid, event["ordinal"], event["kind"], event["source_span_ordinal"])
        if key in seen or sid not in index or event["writer"] != index[sid]["writer"]:
            raise ValueError("Duplicate or inconsistent correction identity")
        seen.add(key)
        if event["kind"] not in {"model", "own"}:
            raise ValueError("Unknown correction provenance")
        if event["kind"] != "model":
            continue
        original = event["original_codepoints"]
        deleted = event["deleted_codepoints"]
        if (type(original) is not int or type(deleted) is not int or original <= 0
                or not 0 <= deleted <= original or 5 * deleted < 4 * original
                or len(event["deleted_text"]) != original
                or event["source_span_ordinal"] >= event["ordinal"]):
            raise ValueError("Correction does not match D38's eighty-percent event")
        origin = menus[sid].get(event["source_span_ordinal"])
        if origin is None or origin["handling"] not in {"accept", "edit"}:
            raise ValueError("Correction has no originating acceptance")
        # D38 excludes blank original spans; its later before/after menu support
        # is needed for its gradient, not for NP1's event census.
        if event["deleted_text"].strip():
            index[sid]["accepted_text_corrections"] += 1
    for own in writers.values():
        prompts = set()
        for session in sorted(own, key=lambda x: (x["timestamp"], x["session"])):
            index[session["session"]]["repeat_prompt_sessions"] = int(session["prompt"] in prompts)
            prompts.add(session["prompt"])
    return [index[sid] for sid in sorted(index)]


def summarize(rows):
    if not rows:
        return dict(status="unsupported", reason="empty source population",
                    scientific_admission=False)
    groups = defaultdict(list)
    for row in rows:
        groups[row["writer"]].append(row)
    totals = {kind: sum(r[kind] for r in rows) for kind in KINDS}
    by_writer = [{
        "writer": writer, "sessions": len(group),
        "counts": {kind: sum(r[kind] for r in group) for kind in KINDS},
        "rates_per_session": {kind: sum(r[kind] for r in group)/len(group) for kind in KINDS}
    } for writer, group in sorted(groups.items())]
    rates = {kind: total/len(rows) for kind, total in totals.items()}
    combined = sum(totals.values())/len(rows)
    return dict(status="complete", sessions=len(rows), writers=len(groups),
                counts=totals, rates_per_session=rates,
                mean_writer_rates={kind: sum(w["rates_per_session"][kind] for w in by_writer)/len(by_writer) for kind in KINDS},
                sessions_with_any=sum(any(r[k] for k in KINDS) for r in rows),
                combined_rate_per_session=combined,
                route="rare: owner probes needed" if combined < 1 else "common: mine observed probe-like events",
                writer_rows=by_writer,
                definitions=dict(accepted_text_corrections="D38 original accepted span: at least 80% deleted; no before/after gradient-support requirement",
                                 dismissal_runs="one maximal consecutive run of at least three dismissals; ignore/accept/edit breaks a run",
                                 repeat_prompt_sessions="each session after the first for the same writer and prompt, chronological with session-ID ties"),
                caveat="Categories can co-occur. Counts do not establish intentional probing, expected information or mapping to Ghost's probe types.",
                scientific_admission=False, family_counter_change=False)


def run(output, inputs, config, verify=False):
    output = Path(output)
    sessions, failures = load(inputs, config)
    rows = count_sessions(sessions, failures, config)
    summary = summarize(rows)
    binding = dict(config=config, inputs={k: sha256(v) for k, v in sorted(inputs.items())})
    values = {"NP1_BINDINGS.json": binding, "NP1_SESSIONS.json": rows, "NP1_PRIMARY.json": summary}
    if verify:
        for name, expected in values.items():
            if read(output/name) != expected:
                raise ValueError("NP1 fresh reconstruction differs: "+name)
        return dict(verified=True, source_reconstructed=True, sessions=len(rows))
    output.mkdir(parents=True, exist_ok=True)
    for name, value in values.items():
        path = output/name
        if path.exists() and read(path) != value:
            raise ValueError("NP1 immutable reentry differs: "+name)
        if not path.exists():
            write(path, value)
    return dict(status="complete", sessions=len(rows), scientific_admission=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, verify=True)
