"""Synthetic scorer fixtures; the separate owner native pilot remains required."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import timing_closure as card
from runners.drive.cards import timing_closure_measure as measure
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_events import CooperativeYield
from runners.drive.timeline import rebuild


class FixtureEncoder:
    def __init__(self, inputs):
        measure.model_identity(inputs)

    def score(self, text):
        positive = measure.lexical(text) or text in measure.ANCHORS or text in measure.HELDOUT_ENDINGS
        cosine = .5 if positive else -.5
        lexical = measure.lexical(text)
        return dict(lexical=lexical, cosine=cosine, closure=(lexical + (cosine+1)/2)/2,
                    truncated=False, text_sha256=__import__('hashlib').sha256(text.encode()).hexdigest())


def complete(output):
    path = output.parent / "COMPLETE.json"
    write(path, dict(status="COMPLETE", fresh_process_verified=True,
                     outputs={"output/" + p.name: filehash(p) for p in output.glob("*.json")}))
    return str(path)


def fixture_inputs(root, direction=1):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    model = root / "fake-model"
    model.mkdir()
    manifest = root / "MODEL.json"
    write(manifest, dict(repo="sentence-transformers/all-MiniLM-L6-v2", path=str(model), revision="synthetic", files={}))
    content = root / "CONTENT_COMPLETE.json"
    write(content, dict(status="COMPLETE", outputs={"MODEL.json": filehash(manifest)}))
    inputs = dict(model_manifest=str(manifest), content_complete=str(content))
    foundation = root / "foundation"
    index, roster = [], []
    for writer in range(12):
        identity = f"w{writer}"
        events = [dict(eventName="system-initialize", eventSource="api", eventTimestamp=1000, currentDoc="\n")]
        menus, document = [], "\n"
        for second in range(480, 721, 20):
            ending = second >= 600 if direction == 1 else second < 600 if direction == -1 else False
            text = "In conclusion, the matter is settled. " if ending else "She began searching the room. "
            events.append(dict(eventName="suggestion-get", eventSource="user", eventTimestamp=1000+(second-2)*1000))
            ordinal = len(events)
            events.append(dict(eventName="suggestion-open", eventSource="user", eventTimestamp=1000+(second-1)*1000))
            events.append(dict(eventName="suggestion-select", eventSource="user", eventTimestamp=1000+second*1000))
            events.append(dict(eventName="text-insert", eventSource="api", eventTimestamp=1000+(second+.1)*1000,
                               textDelta=dict(ops=[dict(retain=len(document)-1), dict(insert=text)])))
            document = document[:-1] + text + "\n"
            events.append(dict(eventName="text-insert", eventSource="user", eventTimestamp=1000+(second+.2)*1000,
                               textDelta=dict(ops=[dict(retain=len(document)-1), dict(insert=text)])))
            document = document[:-1] + text + "\n"
            menus.append(dict(key=f"{identity}-{second}", ordinal=ordinal, end_ordinal=len(events), handling="accept", menu=[text]))
        events.append(dict(eventName="system-finish", eventSource="user", eventTimestamp=901000))
        timeline = rebuild(events, menus)
        raw = root / "raw" / (identity + ".jsonl")
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text("".join(json.dumps(e)+'\n' for e in events), encoding="utf-8", newline="\n")
        timeline.update(session=identity, writer=str(writer), prompt="prompt", source_sha256=filehash(raw))
        path = foundation / "sessions" / (identity + ".json")
        write(path, timeline)
        index.append(dict(session=identity, writer=str(writer), file=path.relative_to(foundation).as_posix(), sha256=filehash(path)))
        roster.append(dict(session=identity, writer=str(writer), prompt="prompt", path=raw.relative_to(root).as_posix(), source_sha256=filehash(raw)))
    side = root / "ROSTER.json"
    write(side, roster)
    write(foundation / "SESSION_INDEX.json", index)
    write(foundation / "PLAN.json", dict(pins={side.relative_to(root).as_posix(): filehash(side)}))
    write(foundation / "COMPLETE.json", dict(status="COMPLETE", plan_sha256=filehash(foundation / "PLAN.json"),
          outputs={"SESSION_INDEX.json": filehash(foundation / "SESSION_INDEX.json")}))
    inputs.update(repo_root=str(root), raw_roster=str(side), session_index=str(foundation / "SESSION_INDEX.json"),
                  foundation_plan=str(foundation / "PLAN.json"), foundation_complete=str(foundation / "COMPLETE.json"))
    return inputs


def admitted_inputs(tmp_path, monkeypatch, direction):
    monkeypatch.setattr(measure, "Encoder", FixtureEncoder)
    inputs = fixture_inputs(tmp_path / "source", direction)
    pilot_inputs = {k: inputs[k] for k in card.MODEL_INPUTS}
    pilot_output = tmp_path / "pilot" / "output"
    assert card.execute(pilot_output, pilot_inputs, card.config_for("pilot"))["state"] == "positive"
    assert card.verify(pilot_output, pilot_inputs, card.config_for("pilot"))["verified"]
    return dict(inputs, pilot_complete=complete(pilot_output))


@pytest.mark.parametrize("direction,state", [(1, "positive"), (0, "null"), (-1, "negative")])
def test_serialized_jump_and_fresh_process(tmp_path, monkeypatch, direction, state):
    inputs = admitted_inputs(tmp_path, monkeypatch, direction)
    output = tmp_path / "primary" / "output"
    config = card.config_for("primary")
    result = card.execute(output, inputs, config)
    assert result["state"] == state
    assert result["effect"] == pytest.approx(.75 * direction, abs=1e-10)
    details = read(output / "CLOSURE_DETAILS.json")
    assert details["secondaries"]["typed_closure_timer"]["effect"] == pytest.approx(.75 * direction, abs=1e-10)
    assert "accepted_closure_own_median_length" in details["secondaries"]
    assert "requests_per_minute_timer" in details["secondaries"]
    manifest = tmp_path / "verify.json"
    write(manifest, dict(output=str(output), inputs=inputs, config=config))
    code = "import json,sys; from pathlib import Path; from tests.test_drive_cards_timing_closure import FixtureEncoder; from runners.drive.cards import timing_closure as c; c.measure.Encoder=FixtureEncoder; x=json.load(open(sys.argv[1])); print(json.dumps(c.verify(Path(x['output']),x['inputs'],x['config'])))"
    child = subprocess.run([sys.executable, "-c", code, str(manifest)], capture_output=True, text=True, timeout=120,
                           env=dict(os.environ, PYTHONHASHSEED="431"), creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)["primary"] == result
    extension_inputs = dict(inputs, primary_complete=complete(output))
    if direction == 1:
        extension = card.execute(tmp_path / "extension", extension_inputs, card.config_for("extension"))
        assert extension["state"] == "positive"
        assert card.verify(tmp_path / "extension", extension_inputs, card.config_for("extension"))["verified"]
        sensitivity = read(tmp_path / "extension" / "CLOSURE_DETAILS.json")["secondaries"]
        assert set(sensitivity) == {"accepted_closure_window_60", "accepted_closure_window_120", "accepted_closure_window_180"}
    else:
        with pytest.raises(ValueError, match="does not permit"):
            card.execute(tmp_path / "refused-extension", extension_inputs, card.config_for("extension"))


def test_measure_boundaries_and_counterexamples(tmp_path):
    assert len(measure.ANCHORS) == 12
    assert len(measure.HELDOUT_ENDINGS) == len(measure.HELDOUT_MIDPOINTS) == 12
    assert not set(measure.ANCHORS) & set(measure.HELDOUT_ENDINGS)
    assert measure.lexical("In conclusion, this is the final choice.") == 1
    assert measure.lexical("The next section considers another example.") == 0
    assert measure.lexical(measure.AMBIGUOUS) == 1  # retained known lexical false positive
    inputs = fixture_inputs(tmp_path)
    source = read(inputs["raw_roster"])[0]
    events = [json.loads(line) for line in (Path(inputs["repo_root"]) / source["path"]).read_text().splitlines()]
    index = read(inputs["session_index"])[0]
    timeline = read(Path(inputs["session_index"]).parent / index["file"])
    replayed = measure.replay(events, timeline)
    assert sum(r["kind"] == "accepted" for r in replayed["entries"]) == 13
    assert sum(r["kind"] == "typed" for r in replayed["entries"]) == 13
    assert len(replayed["requests"]) == 13
    assert replayed["duration_seconds"] == 900
    timeline["final_document"] += "forged"
    with pytest.raises(ValueError, match="correspondence"):
        measure.replay(events, timeline)


def test_heldout_pilot_gate_cannot_pass_anchor_self_similarity(tmp_path):
    inputs = fixture_inputs(tmp_path)
    assert measure.pilot(FixtureEncoder(inputs))["state"] == "positive"
    class SelfSimilarityOnly(FixtureEncoder):
        def score(self, text):
            score = super().score(text)
            if text in measure.HELDOUT_ENDINGS:
                score.update(cosine=-.5, closure=(score["lexical"]+.25)/2)
            return score
    result = measure.pilot(SelfSimilarityOnly(inputs))
    assert result["anchor_self_sanity_cosine"] > 0
    assert result["heldout_ending_minus_middle_cosine"] == 0
    assert result["state"] == "invalid"


def test_saved_unit_yield_and_mutation(tmp_path, monkeypatch):
    inputs = admitted_inputs(tmp_path, monkeypatch, 1)
    output = tmp_path / "run"
    write(output / "YIELD_REQUEST.json", {})
    assert card.execute(output, inputs, card.config_for("primary"))["status"] == "yielded"
    checkpoint = next(p for p in (output / "sessions").glob("*.json") if not p.name.endswith("receipt.json"))
    saved = filehash(checkpoint)
    (output / "YIELD_REQUEST.json").unlink()
    rows = card.score_rows(inputs, FixtureEncoder(inputs), output, lambda: .1)
    assert filehash(checkpoint) == saved
    assert len(rows) == 12
    wrong = read(checkpoint)
    wrong["session"]["entries"][0]["text"] = "forged"
    checkpoint.write_text(json.dumps(wrong), encoding="utf-8")
    with pytest.raises(ValueError, match="checkpoint changed"):
        card.score_rows(inputs, FixtureEncoder(inputs), output, lambda: .1)
    with pytest.raises(ValueError, match="configuration"):
        card.execute(tmp_path / "wrong", inputs, dict(card.config_for("primary"), seed=True))


def test_rate_exposure_and_constant_discontinuity():
    sessions = [dict(writer=str(w), session=str(w), duration_seconds=615, requests=[605], accepted_times=[], entries=[]) for w in range(12)]
    rates = card.rate_records(sessions, "requests")
    assert [r["outcome"] for r in rates if r["location"] >= 0] == [4.] * 12
    rows = [dict(writer=str(w), location=t, outcome=.5) for w in range(12) for t in (-3, -2, -1, 1, 2, 3)]
    assert card.rd(rows, card.config_for("primary"))["effect"] == 0
    assert card.rd(rows, card.config_for("primary"))["state"] == "null"


def test_typed_deleted_unicode_sentence_retained_and_prompt_boundary_excluded():
    events = [dict(eventName="system-initialize", eventSource="api", eventTimestamp=0, currentDoc="Prompt.\n"),
              dict(eventName="text-insert", eventSource="user", eventTimestamp=500000,
                   textDelta=dict(ops=[dict(retain=7), dict(insert="A fox 😀 came home.")])),
              dict(eventName="text-delete", eventSource="user", eventTimestamp=501000,
                   textDelta=dict(ops=[dict(retain=7), dict(delete=19)])),
              dict(eventName="system-finish", eventSource="user", eventTimestamp=900000)]
    timeline = rebuild(events, [])
    result = measure.replay(events, timeline)
    assert [r["text"] for r in result["entries"]] == ["A fox 😀 came home."]
    assert result["entries"][0]["words_at_event"] == 4
    events[0]["currentDoc"] = "Prompt \n"
    result = measure.replay(events, rebuild(events, []))
    assert result["entries"] == []
