"""P8: retain GPT-3's logged suggestion probability and decoding settings.

This extraction performs no likelihood reinterpretation: the producer's field
called probability is retained as a finite logged score, which can exceed one.
No value is exponentiated, clipped or normalized. A natural logarithm is a
separately named transform of positive scores, not a token log probability.
The dispatcher owns private output placement, source pins and worker resources.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from .menus_io import assert_equal, input_hashes, read, sha256, write
from . import states

SETTINGS = ("currentN", "currentMaxToken", "currentTemperature", "currentTopP",
            "currentPresencePenalty", "currentFrequencyPenalty")


def extract_session(events, session, source_hash):
    wanted = {row["ordinal"]: row for row in session["rows"]}
    if len(wanted) != len(session["rows"]):
        raise ValueError("duplicate decision ordinal")
    found = set()
    for ordinal, event in enumerate(events):
        if ordinal not in wanted:
            continue
        row = wanted[ordinal]
        if event.get("eventName") != "suggestion-open":
            raise ValueError("frozen decision is not a suggestion-open event")
        options = event["currentSuggestions"]
        if isinstance(options, str):
            options = json.loads(options)
        if not isinstance(options, list) or not options:
            raise ValueError("empty or malformed logged menu")
        if [option["original"] for option in options] != row["menu"]:
            raise ValueError("logged suggestion ordering/text differs from frozen menu")
        indices = [option["index"] for option in options]
        if any(type(index) is not int for index in indices) or len(set(indices)) != len(indices):
            raise ValueError("invalid or duplicate logged suggestion index")
        settings = {name: event.get(name) for name in SETTINGS}
        numeric = {}
        for name, value in settings.items():
            if value in (None, ""):
                numeric[name] = None
            else:
                parsed = float(value)
                if not math.isfinite(parsed):
                    raise ValueError("nonfinite decoding setting")
                numeric[name] = parsed
        for position, option in enumerate(options):
            logged = option.get("probability")
            if logged is None:
                value, status = None, "missing"
            else:
                if isinstance(logged, bool):
                    raise ValueError("boolean probability")
                value = float(logged)
                if not math.isfinite(value):
                    raise ValueError("nonfinite logged producer score")
                status = ("negative" if value < 0 else "zero" if value == 0 else
                          "above_one" if value > 1 else "positive_at_most_one")
            yield dict(key=row["key"], session=session["session"], writer=session["writer"],
                       ordinal=ordinal, position=position, suggestion_index=option["index"],
                       probability_logged=logged, logged_score=value, score_status=status,
                       log_positive_score=math.log(value) if value is not None and value > 0 else None,
                       decoding_logged=settings, decoding_numeric=numeric,
                       source_sha256=source_hash)
        found.add(ordinal)
    if found != set(wanted):
        raise ValueError("frozen decision missing from raw log")


def rows_from_inputs(inputs):
    sessions = read(inputs["sessions"])
    roster_rows = read(inputs["roster"])
    roster = {row["session"]: row for row in roster_rows}
    if len(roster) != len(roster_rows):
        raise ValueError("duplicate source roster session")
    source_root = Path(inputs["source_root"]).resolve()
    for session in sorted(sessions, key=lambda row: row["session"]):
        source = roster[session["session"]]
        path = (source_root / source["path"]).resolve()
        if not path.is_relative_to(source_root):
            raise ValueError("source path outside explicit root")
        identity = sha256(path)
        if identity != source["source_sha256"]:
            raise ValueError("raw source hash changed")
        with path.open(encoding="utf8") as stream:
            yield from extract_session((json.loads(line) for line in stream), session, identity)


def summarize(rows):
    counts = Counter()
    menus, sessions, writers = set(), set(), set()
    for row in rows:
        counts[row["score_status"]] += 1
        menus.add(row["key"]); sessions.add(row["session"]); writers.add(row["writer"])
        counts["suggestions"] += 1
        counts["settings_missing"] += any(value is None for value in row["decoding_numeric"].values())
    return dict(suggestions=counts["suggestions"], menus=len(menus), sessions=len(sessions),
                writers=len(writers), score_counts={key: counts[key] for key in ("negative", "zero", "positive_at_most_one", "above_one", "missing")},
                suggestions_with_missing_settings=counts["settings_missing"],
                interpretation="Producer field named probability retained as a finite score. Frontend stores and optionally sorts it unchanged. Backend probability semantics unverified; values above one are retained, not treated as normalized probabilities.")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    destination = output / "SUGGESTIONS.jsonl"
    rows = list(rows_from_inputs(inputs))
    identities = [(row["key"], row["position"]) for row in rows]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate suggestion identity")
    with destination.open("x", encoding="utf8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    result = dict(card="P8", status="complete", state=states.instrument_state(True), descriptive=True, summary=summarize(rows),
                  input_hashes=input_hashes(inputs), table_sha256=sha256(destination),
                  private_outputs=["SUGGESTIONS.jsonl"])
    write(output / "SUMMARY.json", result)
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    with (output / "SUGGESTIONS.jsonl").open(encoding="utf8") as stream:
        saved = [json.loads(line) for line in stream]
    expected = list(rows_from_inputs(inputs))
    assert_equal(saved, expected)
    report = read(output / "SUMMARY.json")
    assert_equal(report["summary"], summarize(saved))
    assert_equal(report["input_hashes"], input_hashes(inputs))
    if report["table_sha256"] != sha256(output / "SUGGESTIONS.jsonl"):
        raise ValueError("saved suggestion table changed")
    return dict(verified=True, primary_recomputed=report["summary"])
