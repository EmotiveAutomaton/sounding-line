from pathlib import Path

import pytest

from runners.drive.cards import week_probes as card
from runners.drive.cards.menus_io import sha256, write


def session(sid, actions=(), writer="a", prompt="p", timestamp=0):
    return dict(session=sid, writer=writer, prompt=prompt, timestamp=timestamp,
                rows=[dict(session=sid, writer=writer, ordinal=i, handling=a)
                      for i, a in enumerate(actions)])


def failure(sid="s", deleted=4, original=5):
    return dict(session=sid, writer="a", ordinal=10, source_span_ordinal=0,
                kind="model", original_codepoints=original,
                deleted_codepoints=deleted, deleted_text="x"*original)


def test_zero_population_and_zero_event_sessions_are_different():
    assert card.summarize([])["status"] == "unsupported"
    out = card.summarize(card.count_sessions([session("s")], []))
    assert out["sessions"] == 1 and out["combined_rate_per_session"] == 0
    assert out["route"].startswith("rare")


def test_maximal_dismissal_runs_and_interruptions():
    actions = ["dismiss"]*7+["ignore"]+["dismiss"]*2+["accept"]+["dismiss"]*3
    rows = card.count_sessions([session("s", actions)], [])
    assert rows[0]["dismissal_runs"] == 2


def test_repeats_are_within_writer_prompt_and_order_invariant():
    sessions = [session("s1", timestamp=2), session("s0", timestamp=1),
                session("other", prompt="q"), session("b", writer="b")]
    expected = card.count_sessions(sessions, [])
    assert expected == card.count_sessions(list(reversed(sessions)), [])
    assert sum(r["repeat_prompt_sessions"] for r in expected) == 1


def test_exact_deletion_boundary_and_parent_acceptance():
    assert card.count_sessions([session("s", ["accept"])], [failure()])[0]["accepted_text_corrections"] == 1
    with pytest.raises(ValueError, match="eighty-percent"):
        card.count_sessions([session("s", ["accept"])], [failure(deleted=3)])
    with pytest.raises(ValueError, match="originating"):
        card.count_sessions([session("s", ["dismiss"])], [failure()])
    with pytest.raises(ValueError, match="Duplicate"):
        card.count_sessions([session("s", ["accept"])], [failure(), failure()])


def test_rate_boundary_is_common_and_writer_weights_are_explicit():
    rows = card.count_sessions([session("s", ["accept"])], [failure()])
    out = card.summarize(rows)
    assert out["combined_rate_per_session"] == 1
    assert out["route"].startswith("common")
    assert out["mean_writer_rates"]["accepted_text_corrections"] == 1


def fixture(root):
    root = Path(root)
    sessions_path, failures_path, binding_path = (root/n for n in ("sessions.json", "FAILURES.json", "INPUTS.json"))
    write(sessions_path, [session("s", ["accept", "dismiss", "dismiss", "dismiss"]), session("t", timestamp=1)])
    write(failures_path, [failure()])
    write(binding_path, dict(paths={"sessions": str(sessions_path)}, pins={str(sessions_path): sha256(sessions_path)}))
    complete = root/"COMPLETE.json"
    write(complete, dict(status="COMPLETE", fresh_process_verified=True,
                         outputs={p.name: sha256(p) for p in (failures_path, binding_path)}))
    return dict(sessions=str(sessions_path), d39_failures=str(failures_path),
                d39_inputs=str(binding_path), d39_completion=str(complete))


def test_actual_handlers_reentry_and_source_tamper(tmp_path):
    inputs = fixture(tmp_path)
    output = tmp_path/"output"
    assert card.execute(output, inputs, card.CONFIG)["status"] == "complete"
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    card.execute(output, inputs, card.CONFIG)
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}
    assert card.verify(output, inputs, card.CONFIG)["verified"]
    Path(inputs["sessions"]).write_text("[]\n", encoding="utf8")
    with pytest.raises(ValueError, match="binding"):
        card.verify(output, inputs, card.CONFIG)


def test_changed_saved_result_and_config_are_refused(tmp_path):
    inputs = fixture(tmp_path)
    output = tmp_path/"output"
    card.execute(output, inputs, card.CONFIG)
    (output/"NP1_PRIMARY.json").write_text('{"status":"complete"}\n', encoding="utf8")
    with pytest.raises(ValueError, match="reconstruction"):
        card.verify(output, inputs, card.CONFIG)
    with pytest.raises(ValueError, match="configuration"):
        card.execute(output, inputs, dict(card.CONFIG, minimum_dismissals=2))


def test_own_and_blank_spans_do_not_count_and_unknown_provenance_refuses():
    event = failure()
    event["kind"] = "own"
    assert card.count_sessions([session("s", ["accept"])], [event])[0]["accepted_text_corrections"] == 0
    event["kind"] = "unknown"
    with pytest.raises(ValueError, match="provenance"):
        card.count_sessions([session("s", ["accept"])], [event])
    event = dict(failure(), deleted_text=" " * 5)
    assert card.count_sessions([session("s", ["accept"])], [event])[0]["accepted_text_corrections"] == 0


def test_changed_correction_source_and_unverified_parent_refuse(tmp_path):
    inputs = fixture(tmp_path)
    Path(inputs["d39_failures"]).write_text("[]\n", encoding="utf8")
    with pytest.raises(ValueError, match="bound by completion"):
        card.load(inputs, card.CONFIG)
    Path(inputs["d39_completion"]).write_text('{"status":"COMPLETE"}\n', encoding="utf8")
    with pytest.raises(ValueError, match="independently verified"):
        card.load(inputs, card.CONFIG)
