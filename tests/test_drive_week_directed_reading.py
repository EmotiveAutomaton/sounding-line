import gzip
import json
from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import week_directed_reading as card
from runners.drive.cards.week_reading_order import make_order
from runners.drive.cards.menus_io import sha256, write
from runners.drive.cards.timing_pmap_stats import identify, profile as original_profile

DICTIONARY = dict(words=["common", "w0", "w1", "w2"], punctuation=["."], character_bigrams=[])


def population(signal="always"):
    rows = []
    for wi in range(3):
        metadata = [dict(session=f"{wi}-{i:02d}", writer=f"w{wi}", prompt=f"p{i%3}", timestamp=i, typed_words=20)
                    for i in range(12)]
        order = make_order(metadata, "directed", card.CONFIG["seed"]+wi*1000)
        selected = order["steps"][0 if signal == "early" else -1]["session"]
        for meta in metadata:
            word = meta["writer"] if signal == "always" or meta["session"] == selected else "common"
            rows.append(dict(**{k: v for k, v in meta.items() if k != "typed_words"},
                word_counts={word:20}, punctuation_counts={}, handling={"accept":1},
                tc_timing_mode="valid", within_intervals=[float(wi+1)], onset_intervals=[float(wi+2)],
                bigram_intervals={}, revision={}, accepted_characters=0, edited_accepted_characters=0,
                accepted_options=0, declined_options=0, accepted_vector_sum=[0]*384,
                declined_vector_sum=[0]*384, requests=0, final_words=20))
    return rows


def test_profile_matches_original_pmap_for_all_three_channels():
    rows = population()[:5]
    expected = original_profile(rows, DICTIONARY, {f"p{i}":20 for i in range(3)})
    assert card.profile(rows, DICTIONARY) == {c: expected[c] for c in card.CHANNELS}


def test_gallery_matches_original_and_ties_do_not_identify():
    a = np.array([[1., 0], [0., 1], [.1, .1]])
    b = np.array([[1., 0], [0., 1], [.5, .5]])
    scores = identify(a, b)["scores"]; gallery = card.gallery_model(b)
    assert [card.correct_identification(a[i], i, gallery) for i in range(3)] == [s == 1 for s in scores]
    tie = card.gallery_model([[1., 1.]]*3)
    assert not any(card.correct_identification([1., 1.], i, tie) for i in range(3))


def test_stability_is_suffix_not_first_hit_and_censoring_is_explicit():
    assert card.stable_time([True, False, True]) == dict(sessions=3, censored=False)
    assert card.stable_time([True, False]) == dict(sessions=3, censored=True)
    assert card.stable_time([True, True]) == dict(sessions=1, censored=False)
    assert card.first_time([True, False]) == dict(sessions=1, censored=False)
    assert card.first_time([False, False]) == dict(sessions=3, censored=True)


@pytest.mark.parametrize("signal,sign", [("always",0), ("early",-1), ("late",1)])
def test_complete_known_answer_policy_pipeline_and_direction(signal, sign):
    result, ledger = card.study(population(signal), DICTIONARY)
    estimate = result["primary"]["estimate"]
    assert np.sign(estimate) == sign
    assert len(ledger) == 3*203
    if sign == 0:
        assert result["primary"]["lower"] == result["primary"]["upper"] == 0
        assert result["route"] == "retain chronological default"
    elif sign < 0:
        assert result["primary"]["upper"] < 0
    else:
        assert result["primary"]["lower"] > 0
    assert result["population_reweighting"] is False


def test_exact_eligibility_and_duplicate_source_refusal():
    rows = population()
    result, _ = card.study(rows[:11], DICTIONARY)
    assert result["status"] == "unsupported"
    with pytest.raises(ValueError, match="Duplicate"):
        card.study(rows + rows[:1], DICTIONARY)


def fixture(root):
    root = Path(root); output = root/"output"; (output/"sessions").mkdir(parents=True)
    rows = population("early")
    for row in rows:
        with gzip.open(output/"sessions"/(row["session"]+".json.gz"), "xt", encoding="utf8") as stream:
            json.dump(row, stream)
    write(output/"STYLE_DICTIONARY.json", DICTIONARY)
    write(output/"PRIMARY.json", dict(source_audit=dict(sessions=len(rows))))
    complete = root/"COMPLETE.json"
    write(complete, dict(status="COMPLETE", fresh_process_verified=True,
        outputs={p.relative_to(root).as_posix():sha256(p) for p in output.rglob("*") if p.is_file()}))
    return dict(pmap_completion=str(complete))


def test_full_serialized_handlers_fresh_replay_and_tamper(tmp_path):
    inputs = fixture(tmp_path/"fixture"); output = tmp_path/"result"
    assert card.execute(output, inputs, card.CONFIG)["status"] == "complete"
    assert card.verify(output, inputs, card.CONFIG)["full_policies_replayed"]
    original = {p.name:p.read_bytes() for p in output.iterdir()}
    card.execute(output, inputs, card.CONFIG)
    assert original == {p.name:p.read_bytes() for p in output.iterdir()}
    (output/"DR1_BINDINGS.json").write_text("{}", encoding="utf8")
    with pytest.raises(ValueError, match="reconstruction"):
        card.verify(output, inputs, card.CONFIG)


def test_source_population_and_config_tampering_refuse(tmp_path):
    inputs = fixture(tmp_path/"fixture")
    complete = Path(inputs["pmap_completion"])
    (complete.parent/"output/PRIMARY.json").write_text("{}", encoding="utf8")
    with pytest.raises(ValueError, match="bound by completion"):
        card.load(inputs)
    with pytest.raises(ValueError, match="configuration"):
        card.study(population(), DICTIONARY, dict(card.CONFIG, random_orders=2))
