"""NP1 source recovery: authenticate absent prepared-menu joins by raw replay.

DESIGN CHECK (2026-10-22): LESSONS sections 3-5 read for this repair.
NULL: zero-event sessions remain zero; no event is invented or silently dropped.
ALTERNATIVE: a correction omitted from the prepared menu table counts only when
the frozen D39 extractor reconstructs its entire authenticated session ledger.
Wrong existing handling, source tampering, duplicate identities or changed
replay fail closed. All original thresholds, categories and denominators stay.
"""
from collections import defaultdict
import json
from pathlib import Path

from . import week_probes as base
from .events_d39 import extract_failures
from .menus_io import read, sha256, write

CONFIG = dict(base.CONFIG, source_recovery_version=1)
EXTRA = {"source_roster", "source_root", "p2_index"}


def contained(root, relative):
    path = (Path(root) / relative).resolve()
    path.relative_to(Path(root).resolve())
    return path


def unique(rows):
    index = {r["session"]: r for r in rows}
    if len(index) != len(rows):
        raise ValueError("Duplicate source session identity")
    return index


def reconstruct(inputs, config):
    if set(inputs) != base.INPUTS | EXTRA or config != CONFIG:
        raise ValueError("Frozen NP1 recovery inputs/configuration differ")
    sessions, failures = base.load({k: inputs[k] for k in base.INPUTS}, base.CONFIG)
    binding = read(inputs["d39_inputs"])
    for key in EXTRA:
        if Path(binding["paths"][key]).resolve() != Path(inputs[key]).resolve():
            raise ValueError("D39 source path binding differs")
        if key != "source_root" and binding["pins"].get(str(Path(inputs[key]))) != sha256(inputs[key]):
            raise ValueError("D39 source hash binding differs")
    cohort = unique(sessions)
    roster, timelines = unique(read(inputs["source_roster"])), unique(read(inputs["p2_index"]))
    if set(cohort) != set(timelines) or not set(cohort) <= set(roster):
        raise ValueError("D39 source cohort differs")
    # The original counter validates every session/menu, even with no failures.
    base.count_sessions(sessions, [])
    menus = {s["session"]: {r["ordinal"]: r for r in s["rows"]} for s in sessions}
    missing, retained, seen = [], [], set()
    for event in failures:
        sid = event["session"]
        key = (sid, event["ordinal"], event["kind"], event["source_span_ordinal"])
        if key in seen or sid not in cohort or event["writer"] != cohort[sid]["writer"]:
            raise ValueError("Duplicate or inconsistent correction identity")
        seen.add(key)
        if event["kind"] == "model" and event["source_span_ordinal"] not in menus[sid]:
            missing.append(event)
        else:
            retained.append(event)
    rows = base.count_sessions(sessions, retained)
    row_index = {r["session"]: r for r in rows}
    by_writer = defaultdict(list)
    for session in sessions:
        by_writer[session["writer"]].append(session)
    positions = {s["session"]: i for group in by_writer.values()
                 for i, s in enumerate(sorted(group, key=lambda s: (s["timestamp"], s["session"])))}
    proofs = []
    for sid in sorted({r["session"] for r in missing}):
        meta, item = roster[sid], timelines[sid]
        if item["writer"] != cohort[sid]["writer"]:
            raise ValueError("D39 timeline writer differs")
        source = contained(inputs["source_root"], meta["path"])
        timeline = contained(Path(inputs["p2_index"]).parent, item["file"])
        for path, digest in ((source, meta["source_sha256"]), (timeline, item["sha256"])):
            if sha256(path) != digest:
                raise ValueError("D39 replay source changed")
        events = [json.loads(line) for line in source.read_text(encoding="utf8").splitlines() if line.strip()]
        replay = [dict(r, session=sid, writer=cohort[sid]["writer"], session_index=positions[sid])
                  for r in extract_failures(events, read(timeline))]
        saved = [r for r in failures if r["session"] == sid]
        order = lambda r: (r["ordinal"], r["kind"], r["source_span_ordinal"])
        if sorted(replay, key=order) != sorted(saved, key=order):
            raise ValueError("D39 full session ledger replay differs")
        absent = [r for r in missing if r["session"] == sid]
        for event in absent:
            if events[event["source_span_ordinal"]]["eventName"] != "suggestion-open":
                raise ValueError("D39 originating raw menu differs")
            row_index[sid]["accepted_text_corrections"] += int(bool(event["deleted_text"].strip()))
        proofs.append(dict(session=sid, source_sha256=sha256(source), timeline_sha256=sha256(timeline),
                           full_session_ledger_replayed=True, missing_menu_corrections=len(absent)))
    summary = base.summarize(rows)
    summary["source_recovery"] = dict(version=1, sessions_replayed=len(proofs),
                                      missing_menu_corrections=len(missing), dropped_sessions=0,
                                      dropped_corrections=0, prepared_menu_rows_changed=False)
    return rows, summary, proofs


def run(output, inputs, config, verify=False):
    rows, summary, proofs = reconstruct(inputs, config)
    binding = dict(config=config, inputs={k: sha256(v) for k, v in sorted(inputs.items()) if k != "source_root"},
                   source_root=str(Path(inputs["source_root"]).resolve()))
    values = {"NP1_BINDINGS.json": binding, "NP1_SESSIONS.json": rows,
              "NP1_PRIMARY.json": summary, "NP1_SOURCE_PROOFS.json": proofs}
    output = Path(output)
    if verify:
        for name, expected in values.items():
            if read(output/name) != expected:
                raise ValueError("NP1 recovery fresh reconstruction differs: " + name)
        return dict(verified=True, source_reconstructed=True, sessions=len(rows))
    output.mkdir(parents=True, exist_ok=True)
    for name, value in values.items():
        path = output/name
        if path.exists() and read(path) != value:
            raise ValueError("NP1 recovery immutable reentry differs: " + name)
        if not path.exists():
            write(path, value)
    return dict(status="complete", sessions=len(rows), scientific_admission=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, verify=True)
