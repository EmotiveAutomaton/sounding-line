import numpy as np
import time
import pytest

from runners.drive.cards.timing_d17 import intervals, mixture, analyze, icc, CooperativeYield
from runners.drive.cards.timing_census import write, filehash


def test_observed_delta_locations_and_single_character_restriction():
    events = [dict(eventName="system-initialize", eventTimestamp=0, currentDoc="")]
    text = "cat dog. run "
    for i, char in enumerate(text, 1):
        events.append(dict(eventName="text-insert", eventTimestamp=i * 100, eventSource="user",
                           textDelta={"ops": [{"retain": i - 1}, {"insert": char}]}))
    out = intervals(events, "per_character")
    assert len(out["within_word"]) == 6
    assert len(out["between_words"]) == 1
    assert len(out["between_sentences"]) == 1


def test_icc_sees_writer_stability_and_refuses_constant_weights():
    weights = [dict(writer=str(w), session=f"{w}-{s}", slowest_weight=w / 10 + .01 * s) for w in range(6) for s in range(4)]
    result = analyze(weights, dict(seed=20261017, bootstrap_draws=100))
    assert result["effect"] > .95
    assert result["state"] == "positive"
    assert icc([[1, 1], [1, 1], [1, 1]]) is None


def test_normalizing_by_within_word_speed_removes_uniform_scale():
    rng = np.random.default_rng(19)
    sessions, scaled = [], []
    for w in range(3):
        for s in range(2):
            values = np.exp(rng.normal(1, .2, 40))
            row = dict(writer=str(w), session=f"{w}-{s}", intervals=dict(within_word=[.1, .1, .1], between_words=values.tolist()))
            sessions.append(row)
            factor = w + 1
            scaled.append(dict(row, intervals=dict(within_word=[.1 * factor] * 3, between_words=(values * factor).tolist())))
    a, ma = mixture(sessions, "between_words", 42)
    b, mb = mixture(scaled, "between_words", 42)
    assert ma["components"] == mb["components"]
    assert np.allclose([r["slowest_weight"] for r in a], [r["slowest_weight"] for r in b], atol=1e-8)


def test_mixture_yields_and_resumes_at_authenticated_component_boundary(tmp_path):
    rng = np.random.default_rng(33)
    sessions = [dict(writer=str(w), session=str(w), intervals=dict(within_word=[.1, .1], between_words=np.exp(rng.normal(0, .3, 40)).tolist())) for w in range(3)]
    write(tmp_path / "YIELD_REQUEST.json", dict(reason="constructed test"))
    with pytest.raises(CooperativeYield):
        mixture(sessions, "between_words", 42, tmp_path, time.monotonic(), 0)
    first_hash = filehash(tmp_path / "D17_MIXTURE_K1.json")
    assert (tmp_path / "FIRST_TENTH.json").exists()
    (tmp_path / "YIELD_REQUEST.json").unlink()
    weights, _ = mixture(sessions, "between_words", 42, tmp_path, time.monotonic(), 1)
    assert len(weights) == 3
    assert first_hash == filehash(tmp_path / "D17_MIXTURE_K1.json")


def test_request_to_open_wait_is_excluded_without_changing_following_interval():
    events = [dict(eventName="system-initialize", eventTimestamp=0, currentDoc="cat "),
              dict(eventName="text-insert", eventTimestamp=100, eventSource="user", textDelta={"ops":[{"retain":4},{"insert":" "}]}),
              dict(eventName="suggestion-get", eventTimestamp=200),
              dict(eventName="suggestion-open", eventTimestamp=2200),
              dict(eventName="text-insert", eventTimestamp=2300, eventSource="user", textDelta={"ops":[{"retain":5},{"insert":"a"}]}),
              dict(eventName="text-insert", eventTimestamp=2400, eventSource="user", textDelta={"ops":[{"retain":6},{"insert":"b"}]})]
    values = intervals(events, "per_character")
    assert values["excluded_system_wait"] == 1 and values["between_words"] == []
    assert values["within_word"] == pytest.approx([.1])
    # A request with no recorded response also cannot become a writing pause.
    del events[3]
    values = intervals(events, "per_character")
    assert values["excluded_system_wait"] == 2 and values["within_word"] == []


def serialized_inputs(tmp_path, stable=True):
    import json
    from pathlib import Path
    rng = np.random.default_rng(17)
    index, roster = [], []
    foundation, tc = tmp_path / "foundation", tmp_path / "tc"
    for w in range(6):
        for s in range(4):
            sid = f"w{w}s{s}"
            events = [dict(eventName="system-initialize", eventTimestamp=0, currentDoc="")]
            clock, position = 0., 0
            slow_count = (3 + w * 5 + s % 2) if stable else (4 + s * 8)
            slow = np.arange(32) < slow_count
            rng.shuffle(slow)
            for word in range(32):
                for c, char in enumerate("cat "):
                    step = (.15 if not slow[word] else 3.) if c == 0 else .1
                    clock += step * np.exp(rng.normal(0, .025)) * 1000
                    events.append(dict(eventName="text-insert", eventTimestamp=clock, eventSource="user",
                                       textDelta={"ops":[{"retain":position},{"insert":char}]}))
                    position += 1
            raw = tmp_path / "raw" / (sid + ".jsonl")
            raw.parent.mkdir(exist_ok=True)
            raw.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
            record = dict(session=sid, writer=str(w), source_sha256=filehash(raw))
            session = foundation / "sessions" / (sid + ".json")
            write(session, record)
            index.append(dict(session=sid, writer=str(w), file=session.relative_to(foundation).as_posix(), sha256=filehash(session)))
            roster.append(dict(record, path=raw.relative_to(tmp_path).as_posix()))
    write(foundation / "SESSION_INDEX.json", index)
    write(foundation / "COMPLETE.json", dict(status="COMPLETE", outputs={"SESSION_INDEX.json":filehash(foundation / "SESSION_INDEX.json")}))
    write(tmp_path / "ROSTER.json", roster)
    write(tc / "output/TC_PRIMARY.json", dict(timing_mode="per_character"))
    write(tc / "COMPLETE.json", dict(status="COMPLETE", fresh_process_verified=True, outputs={"output/TC_PRIMARY.json":filehash(tc / "output/TC_PRIMARY.json")}))
    return dict(session_index=str(foundation / "SESSION_INDEX.json"), foundation_complete=str(foundation / "COMPLETE.json"),
                raw_roster=str(tmp_path / "ROSTER.json"), repo_root=str(tmp_path), tc_primary=str(tc / "output/TC_PRIMARY.json"),
                tc_completion=str(tc / "COMPLETE.json")), dict(seed=20261017, bootstrap_draws=2000, extension=False)


def test_serialized_positive_resume_fresh_process_replay_and_immutable_reentry(tmp_path):
    import json
    import subprocess
    import sys
    from runners.drive.cards.timing_d17 import execute
    inputs, config = serialized_inputs(tmp_path)
    output = tmp_path / "output"
    write(output / "YIELD_REQUEST.json", {})
    assert execute(output, inputs, config)["status"] == "yielded"
    checkpoint = next((output / "intervals").glob("*.receipt.json"))
    retained = checkpoint.read_bytes()
    (output / "YIELD_REQUEST.json").unlink()
    result = execute(output, inputs, config)
    assert result["state"] == "positive" and result["effect"] > .95
    assert result["writer_shuffle_icc"] < .3
    assert checkpoint.read_bytes() == retained
    write(tmp_path / "plan.json", dict(output=str(output), inputs=inputs, config=config))
    code = "import json,sys;from pathlib import Path;from runners.drive.cards.timing_d17 import verify;p=json.load(open(sys.argv[1]));print(json.dumps(verify(Path(p['output']),p['inputs'],p['config'])['verified']))"
    done = subprocess.run([sys.executable, "-B", "-c", code, str(tmp_path / "plan.json")], check=True, capture_output=True, text=True)
    assert json.loads(done.stdout) is True
    snapshots = {str(p):p.read_bytes() for p in output.rglob("*") if p.is_file()}
    assert execute(output, inputs, config) == result
    assert snapshots == {str(p):p.read_bytes() for p in output.rglob("*") if p.is_file()}


def test_serialized_unstable_writer_null_does_not_pass(tmp_path):
    from runners.drive.cards.timing_d17 import execute, verify
    inputs, config = serialized_inputs(tmp_path, stable=False)
    result = execute(tmp_path / "output", inputs, config)
    # Balanced within-writer variation has a negative ANOVA ICC, not zero:
    # the exhaustive campaign state vocabulary therefore calls this negative.
    assert result["state"] == "negative" and result["ci_high"] < 0
    assert verify(tmp_path / "output", inputs, config)["verified"]


@pytest.mark.parametrize("kind", ["raw", "completion", "identity", "duplicate", "unknown_mode", "escape"])
def test_authentication_refusals_precede_estimation(tmp_path, kind):
    import json
    from pathlib import Path
    from runners.drive.cards.timing_d17 import execute
    from runners.drive.cards.timing_census import read
    inputs, config = serialized_inputs(tmp_path)
    roster = read(inputs["raw_roster"])
    if kind == "raw":
        (tmp_path / roster[0]["path"]).write_text("changed")
    elif kind == "completion":
        Path(inputs["tc_primary"]).write_text('{"timing_mode":"invalid"}')
    elif kind in ("identity", "duplicate", "escape"):
        if kind == "identity":
            roster[0]["writer"] = "different"
        elif kind == "duplicate":
            roster.append(roster[0])
        else:
            roster[0]["path"] = "../outside.jsonl"
        Path(inputs["raw_roster"]).write_text(json.dumps(roster))
    else:
        Path(inputs["tc_primary"]).write_text('{"timing_mode":"mystery"}')
        completion = read(inputs["tc_completion"])
        completion["outputs"]["output/TC_PRIMARY.json"] = filehash(inputs["tc_primary"])
        Path(inputs["tc_completion"]).write_text(json.dumps(completion))
    with pytest.raises(ValueError):
        execute(tmp_path / "output", inputs, config)
    assert not (tmp_path / "output/D17_PRIMARY.json").exists()


def test_saved_weight_mutation_is_refused(tmp_path):
    from runners.drive.cards.timing_d17 import execute, verify
    inputs, config = serialized_inputs(tmp_path)
    output = tmp_path / "output"
    execute(output, inputs, config)
    (output / "D17_WEIGHTS.json").write_text("[]")
    with pytest.raises(ValueError, match="intermediate/output changed"):
        verify(output, inputs, config)
