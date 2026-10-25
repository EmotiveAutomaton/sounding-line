"""WB1/PP1 source-only event alphabet and interval preparation.

DESIGN CHECK: LESSONS sections 3-5 and CONTROLS read 2026-10-25. NULL:
malformed chronology, changed provenance, non-canonical delta counts, duplicate
sessions or altered checkpoints refuse preparation. ALTERNATIVE: exact source
replay reproduces P2 and preserves every event's ordinals, including censored
menus and future-linked accepted-text edits. These receipts license inputs only;
no piece, timing-gradient or downstream gate is decided here. Constructed tests
exercise UTF-16 offsets, exact 2/60-second boundaries and both interval endpoints.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_events import source_sessions
from runners.drive.cards.timing_p6 import gzread, gzwrite, write_equal
from runners.stage14.common import atomic
from runners.stage9.coauthor import units, text_of, delta_ops, apply_delta

SEED = 20261026
SCHEMA = "week3-event-input-v1"


def stratified_split(session_counts, seed=SEED):
    """Adjacent sorted counts form strata; alternate singleton assignment.

    Random ties and paired allocation use a fixed generator. Counts are the only
    stratum feature; event values and outcomes cannot affect discovery membership.
    """
    rng = np.random.default_rng(seed)
    names = sorted(session_counts)
    if len(names) < 2:
        raise ValueError("writer-disjoint split requires at least two writers")
    tie = dict(zip(names, rng.random(len(names)).tolist()))
    names.sort(key=lambda w: (session_counts[w], tie[w], w))
    result = {}
    for start in range(0, len(names), 2):
        pair = names[start:start + 2]
        if len(pair) == 2:
            discovery = int(rng.integers(2))
            for i, writer in enumerate(pair):
                result[writer] = "discovery" if i == discovery else "test"
        else:
            result[pair[0]] = "discovery" if sum(v == "discovery" for v in result.values()) <= sum(v == "test" for v in result.values()) else "test"
    return dict(sorted(result.items()))


def checked_clock(events):
    if not events or events[0].get("eventName") != "system-initialize":
        raise ValueError("source initialization required")
    values = [float(e["eventTimestamp"]) / 1000 for e in events]
    if not all(math.isfinite(v) for v in values) or values != sorted(values):
        raise ValueError("invalid source chronology")
    return [v - values[0] for v in values]


def location(before, revision=False):
    if revision:
        return "before_revision"
    if re.search(r"\n\s*$", before):
        return "before_paragraph"
    if not before.strip() or re.search(r"[.!?][\"')\]]*\s*$", before):
        return "before_sentence"
    if before and (before[-1].isalnum() or before[-1] in "'\u2019"):
        return "within_word"
    return "before_word"


def extract_session(events, timeline):
    """Replay original deltas and expose annotated actions, never keypresses.

    Revision is any user deletion or insertion before the document's terminal
    newline position. One changed delta can contribute revision/deletion/typing
    tokens, in that deterministic order. Menu-resolution tokens are keyed to P2.
    """
    clocks = checked_clock(events)
    doc = units(events[0]["currentDoc"])
    deltas = {d["ordinal"]: d for d in timeline["deltas"]}
    if len(deltas) != len(timeline["deltas"]):
        raise ValueError("duplicate P2 delta ordinal")
    acceptance_time = {}
    resolution = defaultdict(list)
    for decision in timeline["decisions"]:
        ordinal = decision["resolution_ordinal"]
        if not 0 <= ordinal < len(events):
            raise ValueError("invalid P2 menu resolution")
        handling = decision["handling"]
        if handling in {"accept", "edit"}:
            acceptance_time[decision["ordinal"]] = clocks[ordinal]
            kind = "accept"
        elif handling in {"ignore", "dismiss"}:
            kind = "ignore"
        else:
            raise ValueError("unknown canonical handling")
        resolution[ordinal].append(dict(kind=kind, length=1,
            source_ordinals=[ordinal], menu_ordinal=decision["ordinal"],
            censored=decision["latency_kind"].startswith("right_censored"),
            handling=handling, seconds=clocks[ordinal]))
    actions, intervals, excluded = [], [], Counter()
    previous = None
    previous_cursor = None
    crossed_suggestion = False
    seen = set()
    for ordinal, event in enumerate(events):
        name = event["eventName"]
        if name.startswith("suggestion-"):
            crossed_suggestion = True
        if name == "suggestion-get":
            actions.append(dict(kind="request", length=1, seconds=clocks[ordinal], source_ordinals=[ordinal]))
        actions.extend(resolution.get(ordinal, []))
        ops = delta_ops(event.get("textDelta"))
        if not ops:
            continue
        if ordinal not in deltas:
            raise ValueError("raw delta absent from P2")
        seen.add(ordinal)
        row = deltas[ordinal]
        user = event.get("eventSource") == "user"
        before_doc = text_of(doc)
        insertion = "".join(op["insert"] for op in ops if "insert" in op)
        ndelete = sum(op.get("delete", 0) for op in ops)
        if (row["source"], row["inserted_codepoints"], row["inserted_utf16"], row["deleted_utf16"]) != (event.get("eventSource"), len(insertion), len(units(insertion)), ndelete):
            raise ValueError("raw/P2 delta disagreement")
        if not math.isclose(row["seconds"], clocks[ordinal], rel_tol=0, abs_tol=1e-7):
            raise ValueError("raw/P2 clock disagreement")
        cursor, positions, removed = 0, [], []
        for op in ops:
            if "retain" in op:
                cursor += op["retain"]
            elif "delete" in op:
                positions.append(cursor)
                removed.append(text_of(doc[cursor:cursor + op["delete"]]))
                cursor += op["delete"]
            else:
                positions.append(cursor)
        at = min(positions) if positions else len(doc)
        terminal = len(doc) - (1 if before_doc.endswith("\n") else 0)
        revision = user and (ndelete > 0 or at < terminal)
        continuing_cursor = previous_cursor is not None and (at == previous_cursor or (ndelete and at + ndelete == previous_cursor))
        revision_move = user and at < terminal and not continuing_cursor
        base = dict(seconds=clocks[ordinal], source_ordinals=[ordinal])
        if revision_move:
            actions.append(dict(base, kind="revision", length=1))
        if user and ndelete:
            actions.append(dict(base, kind="delete", length=sum(len(s) for s in removed)))
        if user and insertion:
            actions.append(dict(base, kind="insert", length=len(insertion)))
        touched = row["accepted_owners_touched"] if user else []
        recent = [owner for owner in touched if owner in acceptance_time and 0 <= clocks[ordinal] - acceptance_time[owner] <= 60]
        if recent:
            actions.append(dict(base, kind="edit_accepted", length=1, accepted_menu_ordinals=recent,
                                future_linked=True))
        # An interval touches both endpoints and every suggestion event between.
        single = user and len(insertion) == 1 and ndelete == 0
        if user and (insertion or ndelete) and previous is not None:
            gap = clocks[ordinal] - previous["seconds"]
            target_ok = single or (ndelete > 0 and not insertion)
            reason = ("nonpositive" if gap <= 0 else "suggestion" if crossed_suggestion else
                      "endpoint_not_single_user_insert" if not previous["single"] or not target_ok else None)
            if reason:
                excluded[reason] += 1
            else:
                prefix = text_of(doc[:at])
                char = insertion[:1]
                where = "separator" if char.isspace() and not revision else location(prefix, revision)
                intervals.append(dict(ordinal=ordinal, previous_ordinal=previous["ordinal"], seconds=clocks[ordinal],
                    interval_seconds=gap, location=where, next_upper_or_punctuation=bool(char and (char.isupper() or (not char.isalnum() and not char.isspace()))),
                    mechanical_training=where in {"within_word", "before_word"},
                    target="deletion" if ndelete and not insertion else "single_character_insert"))
        doc, _, _ = apply_delta(doc, [None] * len(doc), event.get("textDelta"))
        previous_cursor = at + len(units(insertion)) if user else None
        previous = dict(single=single, seconds=clocks[ordinal], ordinal=ordinal)
        crossed_suggestion = name.startswith("suggestion-")
    if seen != set(deltas) or text_of(doc) != timeline["final_document"]:
        raise ValueError("source replay does not reproduce complete P2")
    actions.sort(key=lambda a: (a["source_ordinals"][0],
                               {"request": 0, "accept": 1, "ignore": 1, "revision": 2,
                                "delete": 3, "insert": 4, "edit_accepted": 5}[a["kind"]]))
    return dict(actions=collapse_actions(actions), intervals=intervals,
                interval_exclusions=dict(sorted(excluded.items())),
                raw_events=len(events), raw_deltas=len(deltas),
                final_document_sha256=hashlib.sha256(text_of(doc).encode("utf-8")).hexdigest())


def collapse_actions(actions):
    """Aggregate adjacent typing/deletion actions; insert explicit >=2s gaps.

    A menu or revision event interrupts a run. Pauses span consecutive meaningful
    actions (including menu actions), so system/request waits remain observable
    in WB1; PP1 separately removes suggestion-touching intervals.
    """
    result = []
    last_clock = None
    for action in actions:
        item = dict(action)
        gap = None if last_clock is None else item["seconds"] - last_clock
        if gap is not None and gap < 0:
            raise ValueError("action chronology reversed")
        if gap is not None and gap >= 2:
            result.append(dict(kind="pause", length=gap, seconds=item["seconds"],
                               source_ordinals=[result[-1]["source_ordinals"][-1], item["source_ordinals"][0]]))
        kind = "burst" if item["kind"] == "insert" else item["kind"]
        item["kind"] = kind
        if result and kind in {"burst", "delete"} and result[-1]["kind"] == kind and gap is not None and gap < 2:
            result[-1]["length"] += item["length"]
            result[-1]["source_ordinals"].extend(item["source_ordinals"])
            result[-1]["seconds"] = item["seconds"]
        else:
            result.append(item)
        last_clock = item["seconds"]
    return result


def bin_edges(units_):
    pools = defaultdict(list)
    for item in units_:
        for action in item["actions"]:
            if action["kind"] in {"burst", "pause", "delete"}:
                pools[action["kind"]].append(action["length"])
    return {kind: dict(terciles=np.quantile(pools[kind], [1/3, 2/3]).tolist(),
                       median=float(np.median(pools[kind])), observations=len(pools[kind]))
            if pools[kind] else dict(terciles=None, median=None, observations=0)
            for kind in ("burst", "pause", "delete")}


def symbols(actions, edges, coarse=False):
    result = []
    for event in actions:
        kind = event["kind"]
        if coarse and kind == "revision":
            continue
        if kind in {"burst", "pause", "delete"}:
            cut = [edges[kind]["median"]] if coarse else edges[kind]["terciles"]
            if cut is None or any(v is None for v in cut):
                raise ValueError("missing alphabet cutpoints")
            # Equal lengths never split across bins; empty bins are disclosed.
            kind += str(int(np.searchsorted(cut, event["length"], side="left")))
        elif kind == "ignore" and event.get("censored"):
            kind = "ignore_censored"
        result.append(kind)
    return result


def validate_config(config):
    if set(config) != {"mode", "expected_sessions", "seed"} or config["mode"] not in {"constructed", "corpus"} or config["seed"] != SEED:
        raise ValueError("frozen preparation configuration required")
    if type(config["expected_sessions"]) is not int or config["expected_sessions"] < 1:
        raise ValueError("positive fixed session census required")
    if config["mode"] == "corpus" and config["expected_sessions"] != 1399:
        raise ValueError("full canonical P2 census required")


def prepare(output, inputs, config, verify=False):
    validate_config(config)
    required = {"repo_root", "session_index", "foundation_complete", "foundation_plan", "raw_roster", "prepared_sessions"}
    if set(inputs) != required:
        raise ValueError("exact source preparation inputs required")
    output = Path(output)
    root = Path(inputs["repo_root"]).resolve()
    plan = read(inputs["foundation_plan"])
    metadata_path = Path(inputs["prepared_sessions"]).resolve()
    if plan["pins"].get(metadata_path.relative_to(root).as_posix()) != filehash(metadata_path):
        raise ValueError("prepared metadata is not pinned by foundation")
    metadata_list = read(metadata_path)
    metadata = {r["session"]: r for r in metadata_list}
    if len(metadata) != len(metadata_list):
        raise ValueError("duplicate prepared metadata")
    started = time.monotonic()
    units_, index, bindings = [], [], {}
    for key in sorted(required - {"repo_root"}):
        bindings[str(Path(inputs[key]).resolve())] = filehash(inputs[key])
    for done, (row, timeline, raw_meta) in enumerate(source_sessions(inputs, "raw_roster"), 1):
        meta = metadata[row["session"]]
        if meta["writer"] != row["writer"] or meta["prompt"] != timeline["prompt"]:
            raise ValueError("prepared/P2 metadata identity mismatch")
        source = (root / raw_meta["path"]).resolve()
        source.relative_to(root)
        events = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
        record = dict(schema=SCHEMA, session=row["session"], writer=row["writer"], prompt=timeline["prompt"],
                      timestamp=meta["timestamp"], genre=meta.get("genre"),
                      raw_sha256=filehash(source), p2_sha256=row["sha256"], **extract_session(events, timeline))
        filename = "sessions/" + hashlib.sha256(row["session"].encode()).hexdigest() + ".json.gz"
        path = output / filename
        if verify or path.exists():
            if gzread(path) != record:
                raise ValueError("saved session does not reproduce original source")
        else:
            gzwrite(path, record)
        units_.append(record)
        index.append(dict(session=row["session"], writer=row["writer"], file=filename, sha256=filehash(path)))
        bindings[str(source)] = record["raw_sha256"]
        bindings[str((Path(inputs["session_index"]).parent / row["file"]).resolve())] = row["sha256"]
        if not verify:
            atomic(output / "PROGRESS.json", dict(phase="source_only", sessions_completed=done,
                expected_sessions=config["expected_sessions"], wall_seconds=time.monotonic() - started))
    if len(index) != config["expected_sessions"]:
        raise ValueError("canonical session census changed")
    counts = Counter(r["writer"] for r in units_)
    split = stratified_split(counts)
    edges = bin_edges(units_)
    result = dict(card="WB1-input", schema=SCHEMA, status="prepared", scientific_result=False,
        sessions=len(units_), writers=len(counts), alphabet_event_counts=dict(sorted(Counter(a["kind"] for r in units_ for a in r["actions"]).items())),
        timing_intervals=sum(len(r["intervals"]) for r in units_),
        convention="logged changes, not physical keypresses; WB1 timing includes menu waits; PP1 excludes suggestion-touching or multi-insert endpoints",
        timing_revision_scope="interval before a user deletion or insertion away from the terminal newline; separate target field preserves deletion endpoints",
        seed=SEED, source_bindings=bindings)
    payloads = {"WB1_INPUT_INDEX.json": index, "WB1_WRITER_SPLIT.json": dict(seed=SEED, method="random paired adjacent session-count strata", writers=split, session_counts=dict(sorted(counts.items()))),
                "WB1_BIN_EDGES.json": edges, "WB1_INPUT_RESULT.json": result}
    for name, payload in payloads.items():
        if verify:
            if read(output / name) != payload:
                raise ValueError("saved preparation aggregate changed: " + name)
        else:
            write_equal(output / name, payload)
    return result


def execute(output, inputs, config):
    return prepare(output, inputs, config)


def verify(output, inputs, config):
    result = prepare(output, inputs, config, verify=True)
    return dict(verified=True, sessions=result["sessions"], source_replay="complete uncached raw and P2 reconstruction", scientific_result=False)
