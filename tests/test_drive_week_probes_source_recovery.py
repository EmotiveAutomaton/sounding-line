import json
from pathlib import Path

import pytest

from runners.drive.cards import week_probes_source_recovery as card
from runners.drive.cards.events_d39 import extract_failures
from runners.drive.cards.menus_io import read, sha256
from runners.drive.timeline import rebuild


def write(path, value):
    # Tests deliberately mutate fixtures; production outputs remain exclusive.
    Path(path).write_text(json.dumps(value, ensure_ascii=False)+"\n", encoding="utf8")


def fixture(root, handling=None):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    def event(i, name, source="user", **kwargs):
        return dict(eventNum=i, eventTimestamp=1000+i*100, eventName=name,
                    eventSource=source, **kwargs)
    events = [event(0, "system-initialize", "api", currentDoc="\n"),
              event(1, "suggestion-get"), event(2, "suggestion-open"),
              event(3, "suggestion-select"),
              event(4, "text-insert", "api", textDelta={"ops": [{"insert": "😀ABCD"}]}),
              event(5, "text-delete", textDelta={"ops": [{"retain": 2}, {"delete": 4}]}),
              event(6, "text-delete", textDelta={"ops": [{"delete": 2}]})]
    timeline = rebuild(events, [dict(key="m", ordinal=2, end_ordinal=7, handling="edit", menu=["😀ABCD"])])
    raw, timeline_path = root/"raw.jsonl", root/"timeline.json"
    raw.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in events), encoding="utf8")
    write(timeline_path, timeline)
    sessions = [dict(session="s", writer="a", prompt="p", timestamp=0, rows=[]),
                dict(session="t", writer="a", prompt="p", timestamp=1, rows=[])]
    if handling is not None:
        sessions[0]["rows"].append(dict(session="s", writer="a", ordinal=2, handling=handling))
    # Dismissal runs must not acquire invented acceptance rows during recovery.
    sessions[0]["rows"] += [dict(session="s", writer="a", ordinal=i, handling="dismiss") for i in (10, 11, 12)]
    paths = {k: str(root/name) for k, name in dict(sessions="sessions.json", d39_failures="FAILURES.json",
             d39_inputs="INPUTS.json", d39_completion="COMPLETE.json", source_roster="roster.json", p2_index="index.json").items()}
    paths["source_root"] = str(root)
    write(paths["sessions"], sessions)
    write(paths["source_roster"], [dict(session=sid, path=raw.name, source_sha256=sha256(raw)) for sid in ("s", "t")])
    write(paths["p2_index"], [dict(session=sid, writer="a", file=timeline_path.name, sha256=sha256(timeline_path)) for sid in ("s", "t")])
    write(paths["d39_failures"], [dict(e, session="s", writer="a", session_index=0) for e in extract_failures(events, timeline)])
    reseal(paths)
    return paths


def reseal(paths):
    sources = {k: paths[k] for k in ("sessions", "source_roster", "source_root", "p2_index")}
    write(paths["d39_inputs"], dict(paths=sources, pins={v: sha256(v) for k, v in sources.items() if k != "source_root"}))
    write(paths["d39_completion"], dict(status="COMPLETE", fresh_process_verified=True,
          outputs={Path(paths[k]).name: sha256(paths[k]) for k in ("d39_failures", "d39_inputs")}))


def test_raw_replay_recovers_omitted_menu_without_changing_other_counts(tmp_path):
    inputs = fixture(tmp_path)
    before = Path(inputs["sessions"]).read_bytes()
    rows, summary, proofs = card.reconstruct(inputs, card.CONFIG)
    assert summary["sessions"] == 2
    assert summary["counts"] == dict(accepted_text_corrections=1, dismissal_runs=1, repeat_prompt_sessions=1)
    assert proofs[0]["full_session_ledger_replayed"]
    assert rows[1]["accepted_text_corrections"] == 0
    assert Path(inputs["sessions"]).read_bytes() == before


def test_existing_acceptance_uses_original_path_and_wrong_handling_stays_invalid(tmp_path):
    inputs = fixture(tmp_path, "accept")
    assert card.reconstruct(inputs, card.CONFIG)[2] == []
    sessions = read(inputs["sessions"])
    sessions[0]["rows"][0]["handling"] = "dismiss"
    write(inputs["sessions"], sessions)
    reseal(inputs)
    with pytest.raises(ValueError, match="originating"):
        card.reconstruct(inputs, card.CONFIG)


@pytest.mark.parametrize("mutation", ["duplicate", "wrong_ledger", "raw_hash", "timeline_hash", "writer", "path_escape"])
def test_untrusted_recovery_is_refused(tmp_path, mutation):
    inputs = fixture(tmp_path)
    if mutation in ("duplicate", "wrong_ledger"):
        failures = read(inputs["d39_failures"])
        if mutation == "duplicate":
            failures.append(dict(failures[0]))
        else:
            failures[0]["deleted_text"] = "wrong"
        write(inputs["d39_failures"], failures)
    elif mutation in ("raw_hash", "path_escape"):
        roster = read(inputs["source_roster"])
        roster[0]["source_sha256" if mutation == "raw_hash" else "path"] = "bad" if mutation == "raw_hash" else "../outside.jsonl"
        write(inputs["source_roster"], roster)
    else:
        index = read(inputs["p2_index"])
        index[0]["sha256" if mutation == "timeline_hash" else "writer"] = "bad"
        write(inputs["p2_index"], index)
    reseal(inputs)
    with pytest.raises(ValueError):
        card.reconstruct(inputs, card.CONFIG)


def test_handlers_reentry_saved_output_tamper_and_source_binding(tmp_path):
    inputs = fixture(tmp_path)
    out = tmp_path/"output"
    card.execute(out, inputs, card.CONFIG)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    card.execute(out, inputs, card.CONFIG)
    assert before == {p.name: p.read_bytes() for p in out.iterdir()}
    assert card.verify(out, inputs, card.CONFIG)["verified"]
    write(out/"NP1_PRIMARY.json", {})
    with pytest.raises(ValueError, match="reconstruction"):
        card.verify(out, inputs, card.CONFIG)
    Path(inputs["source_roster"]).write_text("[]", encoding="utf8")
    with pytest.raises(ValueError, match="binding"):
        card.reconstruct(inputs, card.CONFIG)


def test_empty_ledger_does_not_invent_events(tmp_path):
    inputs = fixture(tmp_path)
    write(inputs["d39_failures"], [])
    reseal(inputs)
    assert card.reconstruct(inputs, card.CONFIG)[1]["counts"]["accepted_text_corrections"] == 0
