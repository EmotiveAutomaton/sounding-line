import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import events_d6 as card


def fixture_session(writer="w", session="s", domain="creative"):
    menu = [dict(index=i, original=f"option{i}", probability=float(i + 1) / 10) for i in range(5)]
    def event(name, hover="", selected=0, **kwargs):
        return dict(eventName=name, currentHoverIndex=hover, currentSuggestionIndex=selected, **kwargs)
    events = [event("system-initialize"), event("suggestion-open", currentSuggestions=menu),
              event("suggestion-hover", 0), event("suggestion-down", 0, 4),
              event("suggestion-select", 4, 4), event("suggestion-close", 4, 4)]
    for i, e in enumerate(events):
        e["eventTimestamp"] = i * 1000
    row = dict(key=session + "-m", ordinal=1, end_ordinal=len(events), menu=[o["original"] for o in menu],
               inserted="option4", handling="accept")
    prepared = dict(writer=writer, session=session, rows=[row])
    p2 = dict(decisions=[dict(key=row["key"], ordinal=1, menu_size=5)])
    return events, prepared, p2, domain


def test_hover_keyboard_and_default_are_separate():
    events, prepared, p2, domain = fixture_session()
    events[1]["currentHoverIndex"] = 77  # Stale from another menu; never a target.
    out = card.extract_session(events, prepared, p2, domain)
    row = out["rows"][0]
    assert row["hovered"] == [True, False, False, False, False]
    assert row["navigated"] == [False, False, False, False, True]
    assert row["targeted"] == [True, False, False, False, True]
    assert row["open_hover"] == 77
    assert row["dwell_seconds"] == 3
    assert out["audit"]["keyboard_navigation_events"] == 1


def test_option_identity_and_keyboard_dom_position_differ():
    events, prepared, p2, domain = fixture_session()
    for i, option in enumerate(events[1]["currentSuggestions"]):
        option["index"] = [9, 7, 3, 1, 0][i]
    events[2]["currentHoverIndex"] = 9
    events[4]["currentSuggestionIndex"] = 0
    out = card.extract_session(events, prepared, p2, domain)["rows"][0]
    assert out["hovered"][0] and out["navigated"][4] and out["selected"] == 4


def test_reopened_episode_retains_menu_and_excludes_hidden_hover():
    events, prepared, p2, domain = fixture_session()
    events[2:4] = [dict(eventName=n, currentHoverIndex=h, currentSuggestionIndex=0)
                   for n, h in [("suggestion-close", ""), ("suggestion-hover", 0),
                                ("suggestion-reopen", 0), ("suggestion-hover", 4)]]
    for i, event in enumerate(events):
        event["eventTimestamp"] = i * 1000
    prepared["rows"][0]["end_ordinal"] = len(events)
    out = card.extract_session(events, prepared, p2, domain)
    row = out["rows"][0]
    assert row["hovered"] == [False, False, False, False, True]
    assert len(row["visible_episodes"]) == 2
    assert row["dwell_seconds"] == 3
    assert out["audit"]["target_events_outside_visible_episodes"] == 1


def test_no_hover_is_not_no_target_or_default():
    events, prepared, p2, domain = fixture_session()
    events[2]["eventName"] = "cursor-forward"
    row = card.extract_session(events, prepared, p2, domain)["rows"][0]
    assert not any(row["hovered"])
    assert row["targeted"][4]
    assert row["default_all"][0]
    assert not row["default_argumentative"][0]
    argumentative = card.extract_session(events, prepared, p2, "argumentative")["rows"][0]
    assert argumentative["default_argumentative"][0]


def test_invalid_relevant_pointer_and_join_fail():
    events, prepared, p2, domain = fixture_session()
    events[2]["currentHoverIndex"] = 77
    with pytest.raises(ValueError, match="outside displayed menu"):
        card.extract_session(events, prepared, p2, domain)
    events[2]["currentHoverIndex"] = 0
    prepared["rows"][0]["inserted"] = "wrong"
    with pytest.raises(ValueError, match="text differs"):
        card.extract_session(events, prepared, p2, domain)


def test_missing_hover_target_is_excluded_not_counted_unhovered():
    events, prepared, p2, domain = fixture_session()
    events[2]["currentHoverIndex"] = ""
    row = card.extract_session(events, prepared, p2, domain)["rows"][0]
    assert not row["hover_target_complete"]
    result = card.statistics([row], dict(bootstrap=2000, seed=20261017))
    assert result["primary"]["state"] == "invalid"
    assert result["excluded_five_item_missing_hover_target"] == 1
    assert result["excluded_nonfive_menus"] == 0


def planted_rows():
    rows = []
    for w in range(20):
        for j in range(20):
            row = card.extract_session(*fixture_session(str(w), f"{w}-{j}"))["rows"][0]
            row["hovered"] = [j < 15, j < 10, j < 10, j < 10, j < 5]
            rows.append(row)
    return rows


def test_known_null_positive_reverse_and_weighting():
    rows = planted_rows()
    config = dict(bootstrap=2000, seed=20261017)
    result = card.statistics(rows, config)
    assert result["primary"]["effect"] == .5
    assert result["primary"]["state"] == "positive"
    assert result["primary"]["z"] is None
    assert abs(result["controls"]["within_menu_position_shuffle"]["effect"]) < .1
    for row in rows:
        row["hovered"] = [False] * 5
    assert card.contrast(rows, 2000, 1)["state"] == "null"
    for row in rows:
        row["hovered"][4] = True
    assert card.contrast(rows, 2000, 1)["state"] == "negative"
    rows[0]["hovered"] = [True, False, False, False, False]
    duplicate_writer = [dict(rows[0]) for _ in range(100)]
    # Same menus duplicated inside one writer change that writer's mean only.
    unequal = card.contrast(rows + duplicate_writer, 2000, 1)
    assert unequal["writers"] == 20
    assert unequal["effect"] < -.9
    assert card.contrast(rows[:20], 2000, 1)["state"] == "invalid"


def test_latent_exposure_bounds_cover_zero():
    result = card.statistics(planted_rows(), dict(bootstrap=2000, seed=20261017))
    bounds = result["latent_exposure_bounds"]
    assert bounds["lower"]["effect"] == -.25
    assert bounds["upper"]["effect"] == .75
    assert result["assignment_audit"]["mean_ascending_score_rank_by_position"] == [0, 1, 2, 3, 4]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf8")


def handler_fixture(tmp_path):
    source = tmp_path / "sources"
    source.mkdir()
    index = []
    roster = []
    sessions = []
    for n in range(3):
        events, prepared, p2, domain = fixture_session(f"writer{n}", f"session{n}")
        raw = source / f"source{n}.jsonl"
        raw.write_text("\n".join(json.dumps(e) for e in events), encoding="utf8")
        p2path = tmp_path / f"p2-{n}.json"
        write_json(p2path, p2)
        index.append(dict(session=prepared["session"], writer=prepared["writer"], file=p2path.name, sha256=card.filehash(p2path)))
        roster.append(dict(session=prepared["session"], writer=prepared["writer"], domain=domain,
                           path=raw.name, source_sha256=card.filehash(raw)))
        sessions.append(prepared)
    code = tmp_path / "interface-fixture.js"
    code.write_text("// Synthetic fixture; not historical interface evidence.", encoding="utf8")
    review = dict(status="reviewed", source_files=[dict(path=str(code), sha256=card.filehash(code))],
                  findings={k: "fixture" for k in ("display_order", "hover_event", "keyboard_navigation", "default_highlight", "domain_mapping")})
    paths = dict(p2_index=tmp_path / "p2-index.json", source_roster=tmp_path / "roster.json",
                 source_root=source, sessions=tmp_path / "prepared.json", interface_audit=tmp_path / "review.json")
    for key, value in (("p2_index", index), ("source_roster", roster), ("sessions", sessions), ("interface_audit", review)):
        write_json(paths[key], value)
    return {k: str(v) for k, v in paths.items()}, dict(bootstrap=2000, seed=20261017)


def test_actual_handler_fresh_process_and_complete_refusal(tmp_path):
    inputs, config = handler_fixture(tmp_path)
    output = tmp_path / "output"
    result = card.execute(output, inputs, config)
    assert result["primary"]["effect"] == 1.
    payload = tmp_path / "verify.json"
    write_json(payload, dict(inputs=inputs, config=config, output=str(output)))
    script = "import json,sys; from pathlib import Path; from runners.drive.cards.events_d6 import verify; p=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(p['output']),p['inputs'],p['config'])))"
    env = dict(os.environ, PYTHONHASHSEED="287")
    completed = subprocess.run([sys.executable, "-B", "-c", script, str(payload)], env=env, capture_output=True, text=True, check=True)
    assert json.loads(completed.stdout)["verified"]
    with pytest.raises(ValueError, match="completed output"):
        card.execute(output, inputs, config)
    rows = output / "ROWS.json"
    rows.write_text("[]", encoding="utf8")
    with pytest.raises(ValueError, match="output changed"):
        card.verify(output, inputs, config)


def test_yield_resume_skips_completed_session_and_rejects_mutation(tmp_path, monkeypatch):
    inputs, config = handler_fixture(tmp_path)
    output = tmp_path / "output"
    original = card.extract_session
    calls = []
    def extract(*args):
        calls.append(args[1]["session"])
        if len(calls) == 1:
            write_json(output / "YIELD_REQUEST.json", {})
        return original(*args)
    monkeypatch.setattr(card, "extract_session", extract)
    first = card.execute(output, inputs, config)
    assert first["status"] == "yielded" and first["sessions_saved"] == 1
    retained = (output / "sessions/session0.json").read_bytes()
    (output / "YIELD_REQUEST.json").unlink()
    result = card.execute(output, inputs, config)
    assert calls == ["session0", "session1", "session2"]
    assert (output / "sessions/session0.json").read_bytes() == retained
    assert result["primary"]["state"] == "positive"
    assert card.verify(output, inputs, config)["verified"]
    Path(inputs["interface_audit"]).write_text("{}", encoding="utf8")
    with pytest.raises(ValueError, match="source changed"):
        card.verify(output, inputs, config)
