"""TC: audit logged delta timing, never reconstruct individual keypresses.

DESIGN CHECK: LESSONS sections 3-5 read 2026-10-17. Under a clock/coalescing
null, single-character share below 0.5, resolution above 100 ms, no typed
characters, or no positive interval invalidates pauses. Under fine recorded
timing, share >=0.8 admits per-character measurement; [0.5,0.8) admits the
interval before the delta containing the first character. Boundaries are
exhaustive, exact, and derived from the curator's October 17 TC rule. A usable
logged clock is not evidence that individual physical keypresses were logged.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from runners.drive.cards import states  # shared campaign state contract


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def filehash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, allow_nan=False)
        stream.write("\n")


def band(single_characters, typed_characters, resolution_ms):
    """Integer comparisons avoid floating-point gaps at 50% and 80%."""
    if typed_characters <= 0 or resolution_ms is None:
        return "invalid"
    if not Decimal(str(resolution_ms)).is_finite() or not 0 < Decimal(str(resolution_ms)) <= 100:
        return "invalid"
    if 5 * single_characters >= 4 * typed_characters:
        return "per_character"
    if 2 * single_characters >= typed_characters:
        return "first_character_delta"
    return "invalid"


def summarize_session(session):
    counts = Counter(typed_characters=0, single_characters=0, typed_insert_deltas=0,
                     multi_character_deltas=0, multi_characters=0, nonuser_characters=0,
                     delta_intervals=0, zero_intervals=0, positive_intervals=0,
                     user_insert_intervals=0, zero_user_insert_intervals=0)
    previous = previous_user = minimum = user_minimum = None
    previous_ordinal = -1
    for delta in session["deltas"]:
        timestamp = Decimal(str(delta["seconds"])) * 1000
        ordinal = delta["ordinal"]
        if not timestamp.is_finite() or timestamp < 0 or ordinal <= previous_ordinal:
            raise ValueError("invalid delta timestamp or ordinal")
        previous_ordinal = ordinal
        n = delta["inserted_codepoints"]
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise ValueError("invalid inserted codepoint count")
        if previous is not None:
            interval = timestamp - previous
            if interval < 0:
                raise ValueError("delta chronology reversed")
            counts["delta_intervals"] += 1
            counts["zero_intervals"] += int(interval == 0)
            counts["positive_intervals"] += int(interval > 0)
            if interval > 0:
                minimum = interval if minimum is None else min(minimum, interval)
        previous = timestamp
        if delta["source"] == "user" and n:
            counts["typed_characters"] += n
            counts["typed_insert_deltas"] += 1
            counts["single_characters"] += int(n == 1)
            counts["multi_character_deltas"] += int(n > 1)
            counts["multi_characters"] += n if n > 1 else 0
            if previous_user is not None:
                interval = timestamp - previous_user
                counts["user_insert_intervals"] += 1
                counts["zero_user_insert_intervals"] += int(interval == 0)
                if interval > 0:
                    user_minimum = interval if user_minimum is None else min(user_minimum, interval)
            previous_user = timestamp
        elif delta["source"] != "user":
            counts["nonuser_characters"] += n
    return dict(session=session["session"], writer=session["writer"], counts=dict(counts),
                resolution_ms=None if minimum is None else float(minimum),
                user_insert_resolution_ms=None if user_minimum is None else float(user_minimum))


def primary(summaries):
    total = Counter()
    for item in summaries:
        total.update(item["counts"])
    positive = [s["resolution_ms"] for s in summaries if s["resolution_ms"] is not None]
    resolution = min(positive) if positive else None
    mode = band(total["single_characters"], total["typed_characters"], resolution)
    share = total["single_characters"] / total["typed_characters"] if total["typed_characters"] else None
    return dict(card="TC", descriptive=True, timing_mode=mode,
                state=states.instrument_state(True, usable=mode != "invalid"),
                pause_valid=mode != "invalid", counts=dict(total),
                sessions=len(summaries), writers=len({s["writer"] for s in summaries}),
                single_character_share=share, resolution_ms=resolution,
                zero_interval_share=total["zero_intervals"] / total["delta_intervals"] if total["delta_intervals"] else None,
                interval_denominator="consecutive logged text-delta events within sessions; no cross-session intervals",
                character_unit="Unicode codepoints inserted by eventSource=user; not physical keypresses",
                multi_insert_interpretation="non-suggestion multi-character user insert; paste/autocorrect causes are not identified",
                route=("Timing cards use the admitted logged interval convention." if mode != "invalid" else
                       "D30 uses D30.v1 revision; D17 and D33 blocked; D16/D37 omit pause shares; D3/D39 unchanged."))


def session_paths(inputs):
    index_path = Path(inputs["session_index"]).resolve()
    complete_path = Path(inputs["foundation_complete"]).resolve()
    complete = read(complete_path)
    if complete.get("status") != "COMPLETE":
        raise ValueError("P2 foundation is incomplete")
    relative = index_path.relative_to(complete_path.parent).as_posix()
    if complete["outputs"].get(relative) != filehash(index_path):
        raise ValueError("P2 index not authenticated by completion")
    index = read(index_path)
    if not index or len({row["session"] for row in index}) != len(index):
        raise ValueError("empty or duplicate session roster")
    for row in sorted(index, key=lambda r: r["session"]):
        path = (index_path.parent / row["file"]).resolve()
        path.relative_to(index_path.parent)
        if filehash(path) != row["sha256"]:
            raise ValueError("P2 session hash changed")
        yield row, path


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if config:
        raise ValueError("TC has no adjustable bands or sampling configuration")
    output = Path(output)
    summaries = []
    for row, path in session_paths(inputs):
        session = read(path)
        if (session["session"], session["writer"]) != (row["session"], row["writer"]):
            raise ValueError("P2 session identity mismatch")
        summaries.append(summarize_session(session))
    result = primary(summaries)
    write(output / "TC_INTERMEDIATES.json", summaries)
    write(output / "TC_PRIMARY.json", result)
    write(output / "TC_BINDINGS.json", dict(inputs={k: filehash(v) for k, v in inputs.items()},
          intermediates_sha256=filehash(output / "TC_INTERMEDIATES.json"), config=config))
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    """Owner invokes this in a fresh process; no corpus scientific replay."""
    output = Path(output)
    binding = read(output / "TC_BINDINGS.json")
    if binding["config"] != config or binding["inputs"] != {k: filehash(v) for k, v in inputs.items()}:
        raise ValueError("TC input/config binding changed")
    if binding["intermediates_sha256"] != filehash(output / "TC_INTERMEDIATES.json"):
        raise ValueError("TC intermediates changed")
    result = primary(read(output / "TC_INTERMEDIATES.json"))
    if result != read(output / "TC_PRIMARY.json"):
        raise ValueError("TC primary does not recompute")
    return dict(verified=True, primary=result)
