import numpy as np
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from runners.drive.cards.timing_events import accepted_lifetimes, d3, d23, session_words, execute, verify
from runners.drive.cards.timing_census import write, read, filehash
from runners.drive.timeline import rebuild


def accepted_events():
    return [dict(eventName="system-initialize", currentDoc="\n"), dict(eventName="suggestion-open"),
            dict(eventName="suggestion-select"), dict(eventName="text-insert", eventSource="api", textDelta={"ops": [{"insert": "abcd"}]})]


def test_half_deletion_and_repeated_interior_insertions_are_reversals():
    deleted = accepted_events() + [dict(eventName="text-edit", eventSource="user", textDelta={"ops": [{"delete": 2}]})]
    assert accepted_lifetimes(deleted)[1]["reversed"]
    inserted = accepted_events() + [dict(eventName="text-edit", eventSource="user", textDelta={"ops": [{"retain": 2}, {"insert": "x"}]}),
                                    dict(eventName="text-edit", eventSource="user", textDelta={"ops": [{"retain": 3}, {"insert": "y"}]})]
    row = accepted_lifetimes(inserted)[1]
    assert row["reversed"] and row["inserted_inside_utf16"] == 2
    assert row["surviving_utf16"] == 4


def test_unrelated_prefix_shift_keeps_accepted_span_unreversed():
    shifted = accepted_events() + [dict(eventName="text-edit", eventSource="user", textDelta={"ops": [{"insert": "prefix "}]})]
    assert not accepted_lifetimes(shifted)[1]["reversed"]


def test_fast_reversal_contrast_and_tied_clocks():
    rows = [dict(writer=str(w), session=str(w), ordinal=i, latency=float(i), reversed=i < 4)
            for w in range(5) for i in range(20)]
    config = dict(seed=20261017, bootstrap_draws=50, extension=False)
    result, _ = d3(rows, config)
    assert result["effect"] == 1 and result["state"] == "positive"
    tied = [dict(row, latency=1.) for row in rows]
    assert d3(tied, config)[0]["state"] == "invalid"


def test_prompt_repeat_density_and_zero_words_are_explicit():
    rows = [dict(writer=str(w), session=f"{w}-{i}", timestamp=i, prompt="p", requests=10 if i == 0 else 3, words=100)
            for w in range(5) for i in range(4)]
    config = dict(seed=20261017, bootstrap_draws=50, extension=False)
    result, _ = d23(rows, config)
    assert result["effect"] == 7 and result["state"] == "positive"
    assert session_words(dict(final_spans=[dict(origin="prompt", text="Given prompt "), dict(origin="typed", text="my text "), dict(origin="accepted", text="AI words")])) == 4


def test_singleton_prompt_cannot_confound_repeat_contrast_and_zero_first_is_not_reassigned():
    rows = [dict(writer=str(w), session=f"{w}-{i}", timestamp=i, prompt="p" if i < 2 else "singleton", requests=5 if i < 2 else 80, words=100)
            for w in range(5) for i in range(3)]
    config = dict(seed=20261017, bootstrap_draws=50, extension=False)
    assert d23(rows, config)[0]["effect"] == 0
    for row in rows:
        if row["timestamp"] == 0:
            row["words"] = 0
    result, _ = d23(rows, config)
    assert result["state"] == "invalid" and result["excluded_zero_word_sessions"] == 5


def test_session_order_extension_and_long_latency_extension_use_own_contrast():
    config = dict(seed=20261017, bootstrap_draws=50, extension=True)
    rows = [dict(writer=str(w), session=f"{w}-{i}", timestamp=i, prompt="p", requests=30 + w - 2 * i + (3 if i == 0 else 0), words=100)
            for w in range(8) for i in range(7)]
    result, _ = d23(rows, config)
    assert np.isclose(result["effect"], 2) and result["state"] == "positive"
    assert abs(result["controls"]["within_writer_request_shuffle"]["effect"]) < 1
    reversals = [dict(writer=str(w), session=str(w), ordinal=i, latency=float(i), reversed=i >= 16)
                 for w in range(5) for i in range(20)]
    assert d3(reversals, config)[0]["effect"] == 1


def test_empty_extension_does_not_fall_back_and_tied_chronology_is_disclosed():
    config = dict(seed=20261017, bootstrap_draws=50, extension=True)
    result, _ = d23([], config)
    assert result["state"] == "invalid" and "chronological extension" in result["reason"]
    rows = [dict(writer=str(w), session=f"{w}-{i}", timestamp=0, prompt="p", requests=5, words=100)
            for w in range(5) for i in range(2)]
    result, _ = d23(rows, dict(config, extension=False))
    assert result["state"] == "invalid" and result["excluded_writers_tied_session_times"] == 5


def test_utf16_internal_insert_and_noncanonical_append():
    events = accepted_events()
    events[3]["textDelta"] = {"ops": [{"insert": "😀abcd"}]}
    events += [dict(eventName="text-edit", eventSource="user", textDelta={"ops": [{"retain": 3}, {"insert": "😀"}]}),
               dict(eventName="text-edit", eventSource="user", textDelta={"ops": [{"retain": 5}, {"insert": "x"}]})]
    row = accepted_lifetimes(events)[1]
    assert row["original_utf16"] == 6 and row["inserted_inside_utf16"] == 3 and row["reversed"]
    events = accepted_events()
    events[0]["currentDoc"] = "prefix\n"
    with pytest.raises(ValueError, match="canonical append"):
        accepted_lifetimes(events)


def event_inputs(root, card, direction):
    """Create real serialized P2 timelines from known-answer synthetic logs."""
    root = Path(root).resolve()
    foundation = root / "foundation"
    metadata, index = [], []
    for writer in range(8):
        for session in range(4 if card == "D23" else 1):
            identity = f"w{writer}s{session}"
            events = []
            clock = 0
            def event(name, source="user", delay=1, **kwargs):
                nonlocal clock
                clock += delay
                events.append(dict(eventName=name, eventSource=source, eventTimestamp=clock * 1000, **kwargs))
            event("system-initialize", "api", currentDoc="\n")
            menus = []
            if card == "D23":
                event("text-insert", textDelta={"ops": [{"insert": "word " * 100}]})
                requests = 8 + (7 * direction if session == 0 else 0)
                for _ in range(requests):
                    event("suggestion-get")
                # A request and a shown menu are different observable events.
                event("suggestion-open")
                start = len(events) - 1
                event("suggestion-close")
                menus.append(dict(key=identity, ordinal=start, end_ordinal=len(events), handling="dismiss", menu=["unused"]))
            else:
                document = "\n"
                for i in range(20):
                    event("suggestion-get")
                    event("suggestion-open")
                    start = len(events) - 1
                    event("suggestion-select", delay=i + 1)
                    event("text-insert", "api", textDelta={"ops": [{"retain": len(document) - 1}, {"insert": "abcd "}]})
                    document = document[:-1] + "abcd \n"
                    reversed_ = i < 4 if direction == 1 else 8 <= i < 12 if direction == -1 else i % 4 < 2
                    if reversed_:
                        event("text-delete", textDelta={"ops": [{"retain": len(document) - 6}, {"delete": 5}]})
                        document = document[:-6] + "\n"
                    menus.append(dict(key=f"{identity}-{i}", ordinal=start, end_ordinal=len(events), handling="edit" if reversed_ else "accept", menu=["abcd "]))
            timeline = rebuild(events, menus)
            raw = root / "raw" / (identity + ".jsonl")
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8", newline="\n")
            timeline.update(session=identity, writer=str(writer), prompt="prompt", source_sha256=filehash(raw))
            path = foundation / "sessions" / (identity + ".json")
            write(path, timeline)
            index.append(dict(session=identity, writer=str(writer), file=path.relative_to(foundation).as_posix(), sha256=filehash(path)))
            metadata.append(dict(session=identity, writer=str(writer), prompt="prompt", timestamp=session,
                                 path=raw.relative_to(root).as_posix(), source_sha256=filehash(raw)))
    side = root / ("raw_roster.json" if card == "D3" else "prepared_sessions.json")
    write(side, metadata)
    write(foundation / "SESSION_INDEX.json", index)
    write(foundation / "PLAN.json", dict(pins={side.relative_to(root).as_posix(): filehash(side)}))
    write(foundation / "COMPLETE.json", dict(status="COMPLETE", plan_sha256=filehash(foundation / "PLAN.json"),
                                            outputs={"SESSION_INDEX.json": filehash(foundation / "SESSION_INDEX.json")}))
    inputs = dict(repo_root=str(root), session_index=str(foundation / "SESSION_INDEX.json"),
                  foundation_complete=str(foundation / "COMPLETE.json"), foundation_plan=str(foundation / "PLAN.json"))
    inputs["raw_roster" if card == "D3" else "prepared_sessions"] = str(side)
    return inputs


@pytest.mark.parametrize("card", ["D23", "D3"])
@pytest.mark.parametrize("direction,state", [(1, "positive"), (0, "null"), (-1, "negative")])
def test_serialized_handler_known_answer_and_fresh_process(tmp_path, card, direction, state):
    inputs = event_inputs(tmp_path / "source", card, direction)
    config = dict(card=card, extension=False, bootstrap_draws=2000, seed=20261017)
    output = tmp_path / "run"
    result = execute(output, inputs, config)
    assert result["state"] == state
    assert result["effect"] == (7 * direction if card == "D23" else direction)
    assert verify(output, inputs, config)["verified"]
    assert execute(output, inputs, config) == result
    manifest = tmp_path / "verification.json"
    write(manifest, dict(output=str(output), inputs=inputs, config=config))
    code = "import json,sys; from pathlib import Path; from runners.drive.cards.timing_events import verify; x=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(x['output']),x['inputs'],x['config'])))"
    child = subprocess.run([sys.executable, "-c", code, str(manifest)], text=True, capture_output=True, timeout=60,
                           env=dict(os.environ, PYTHONHASHSEED="431"), creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)["primary"] == result


def test_safe_checkpoint_yield_and_authenticated_source_refusals(tmp_path):
    inputs = event_inputs(tmp_path / "source", "D23", 1)
    config = dict(card="D23", extension=False, bootstrap_draws=2000, seed=20261017)
    output = tmp_path / "run"
    write(output / "YIELD_REQUEST.json", {})
    assert execute(output, inputs, config)["status"] == "yielded"
    checkpoint = next((output / "sessions").glob("*.json"))
    first_hash = filehash(checkpoint)
    (output / "YIELD_REQUEST.json").unlink()
    assert execute(output, inputs, config)["state"] == "positive"
    assert filehash(checkpoint) == first_hash
    with pytest.raises(ValueError, match="configuration"):
        execute(tmp_path / "wrong", inputs, dict(config, extra=True))
    rows = read(output / "EVENT_ROWS.json")
    rows[0]["requests"] += 1
    (output / "EVENT_ROWS.json").write_text(json.dumps(rows), encoding="utf-8")
    binding = read(output / "TIMING_BINDINGS.json")
    binding["outputs"]["EVENT_ROWS.json"] = filehash(output / "EVENT_ROWS.json")
    (output / "TIMING_BINDINGS.json").write_text(json.dumps(binding), encoding="utf-8")
    with pytest.raises(ValueError, match="reconstruct from authenticated"):
        verify(output, inputs, config)
    source = Path(inputs["session_index"]).parent / read(inputs["session_index"])[0]["file"]
    source.write_text(source.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="P2 session hash"):
        execute(tmp_path / "changed-source", inputs, config)
