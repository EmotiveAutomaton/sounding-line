import math

from runners.drive.cards.timing_p6 import KneserNey, training_sequences
from runners.drive.cards import timing_p6 as p6
from runners.drive.cards.timing_census import write, filehash


def test_kn_normalizes_seen_unseen_contexts_and_prefers_planted_continuation():
    sequences = [["red", "fox", "runs"]] * 30 + [["blue", "bird", "flies"]] * 30 + [["rare"]]
    model = KneserNey(sequences)
    support = model.vocabulary - {"<s>"}
    for context in [[], ["red"], ["red", "fox"], ["absent", "history"]]:
        assert abs(sum(model.score(w, context) for w in support) - 1) < 1e-12
    assert model.score("runs", ["red", "fox"]) > model.score("flies", ["red", "fox"])
    assert model.score("unseen", ["new", "context"]) > 0


def test_kn_unigram_continuation_uses_context_diversity_not_token_frequency():
    model = KneserNey([["a", "x"]] * 100 + [["b", "y"], ["c", "y"]] * 2)
    assert model.score("y", ["unseen", "context"]) > model.score("x", ["unseen", "context"])


def test_training_never_joins_across_api_spans():
    timeline = {"final_spans": [dict(origin="typed", text="cat "), dict(origin="typed", text="sat"),
                                dict(origin="accepted", text=" near "), dict(origin="typed", text="the sea")]}
    assert training_sequences(timeline) == [["cat", "sat"], ["the", "sea"]]


def test_full_handler_heldout_writer_and_saved_primary(tmp_path):
    import json
    index, roster, prepared = [], [], []
    root = tmp_path / "source"
    root.mkdir()
    for i, text in enumerate(["own unique own unique ", "red fox red fox rare ", "red bird red bird other "]):
        sid, writer = f"s{i}", f"w{i}"
        path = root / f"{sid}.jsonl"
        events = [dict(eventName="system-initialize", eventTimestamp=0, currentDoc=""),
                  dict(eventName="text-insert", eventTimestamp=100, eventSource="user", textDelta={"ops": [{"insert": text}]})]
        path.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
        source_hash = filehash(path)
        timeline = dict(session=sid, writer=writer, prompt="p", deltas=[], final_document=text,
                        source_sha256=source_hash, final_spans=[dict(origin="typed", text=text)])
        saved = root / "sessions" / f"{sid}.json"
        write(saved, timeline)
        index.append(dict(session=sid, writer=writer, file=f"sessions/{sid}.json", sha256=filehash(saved)))
        roster.append(dict(session=sid, path=f"{sid}.jsonl", source_sha256=source_hash))
        prepared.append(dict(session=sid, timestamp=i, end_at=i + 1))
    write(root / "SESSION_INDEX.json", index)
    write(root / "COMPLETE.json", dict(status="COMPLETE", outputs={"SESSION_INDEX.json": filehash(root / "SESSION_INDEX.json")}))
    write(root / "ROSTER.json", roster)
    write(root / "SESSIONS.json", prepared)
    inputs = dict(repo_root=str(root), raw_roster=str(root / "ROSTER.json"), prepared_sessions=str(root / "SESSIONS.json"),
                  session_index=str(root / "SESSION_INDEX.json"), foundation_complete=str(root / "COMPLETE.json"))
    output = tmp_path / "output"
    write(output / "YIELD_REQUEST.json", {"reason": "constructed cooperative yield test"})
    yielded = p6.execute(output, inputs, {})
    assert yielded["status"] == "yielded"
    assert not (output / "P6_PRIMARY.json").exists()
    (output / "YIELD_REQUEST.json").unlink()
    result = p6.execute(output, inputs, {})
    assert p6.verify(output, inputs, {})["primary"] == result
    own = p6.gzread(output / "scores/s0.json.gz")
    assert all(w["population_probability"] > 0 for w in own["words"])
    # Recipient-only words map to donor <unk>, rather than getting recipient counts.
    donor_model = KneserNey([["red", "fox", "red", "fox", "rare"], ["red", "bird", "red", "bird", "other"]])
    assert own["words"][0]["population_probability"] == donor_model.score("<unk>", [])
    assert (output / "FIRST_TENTH.json").exists()
    assert p6.execute(output, inputs, {}) == result
