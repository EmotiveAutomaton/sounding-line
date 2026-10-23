import copy
import hashlib

import pytest

from runners.drive.cards import week_directed_timing as card
from tests.test_drive_week_directed_reading import fixture, population, DICTIONARY


def test_sampled_units_are_exact_full_runner_outputs_with_full_gallery():
    rows = population("early")
    work, _ = card.benchmark(rows, DICTIONARY)
    _, ledger = card.base.study(rows, DICTIONARY)
    expected = {(r["writer"], r["policy"], r["replicate"]): hashlib.sha256(card.encoded(r)).hexdigest() for r in ledger}
    assert work["gallery_size"] == 3 and len(work["units"]) == 24
    for r in work["units"]:
        assert r["output_sha256"] == expected[(r["writer"], r["policy"], r["replicate"])]


def test_forecast_counts_full_work_and_both_passes_with_margin():
    work, timing = card.benchmark(population(), DICTIONARY)
    measured = dict(unit_seconds=[1.]*24, elapsed_seconds=30.)
    result = card.forecast(work, [measured, measured])
    assert result["combined_wall_seconds"] == 4*(3*203+6)+30
    assert result["full_random_orders"] == 200 and result["full_writer_draws"] == 2000
    assert result["outcome_used_for_admission"] is False
    with pytest.raises(ValueError, match="Both"):
        card.forecast(work, [measured])
    malformed = copy.deepcopy(work); malformed["units"].pop()
    with pytest.raises(ValueError, match="Incomplete"):
        card.forecast(malformed, [measured, measured])


def test_bad_times_and_ineligible_or_duplicate_sources_refuse():
    rows = population()
    work, _ = card.benchmark(rows, DICTIONARY)
    measured = dict(unit_seconds=[0.]*24, elapsed_seconds=30.)
    with pytest.raises(ValueError, match="Invalid timing"):
        card.forecast(work, [measured, measured])
    with pytest.raises(ValueError, match="Duplicate"):
        card.benchmark(rows+rows[:1], DICTIONARY)
    with pytest.raises(ValueError, match="gallery"):
        card.benchmark(rows[:11], DICTIONARY)


def test_complete_serialized_handlers_and_single_replay(tmp_path):
    inputs = fixture(tmp_path/"fixture")
    output = tmp_path/"output"
    assert card.execute(output, inputs, card.CONFIG)["no_scientific_contrast"]
    assert card.verify(output, inputs, card.CONFIG)["full_gallery_replayed"]
    with pytest.raises(ValueError, match="already recorded"):
        card.verify(output, inputs, card.CONFIG)
    with pytest.raises(ValueError, match="configuration"):
        card.execute(tmp_path/"wrong", inputs, dict(card.CONFIG, random_replicates=1))


def test_changed_saved_work_refuses(tmp_path):
    inputs = fixture(tmp_path/"fixture"); output = tmp_path/"output"
    card.execute(output, inputs, card.CONFIG)
    (output/"WORK.json").write_text("{}", encoding="utf8")
    with pytest.raises(ValueError, match="reconstruction"):
        card.verify(output, inputs, card.CONFIG)


def test_changed_source_refuses(tmp_path):
    inputs = fixture(tmp_path/"fixture"); output = tmp_path/"output"
    card.execute(output, inputs, card.CONFIG)
    (tmp_path/"fixture/output/STYLE_DICTIONARY.json").write_text("{}", encoding="utf8")
    with pytest.raises(ValueError, match="bound by completion"):
        card.verify(output, inputs, card.CONFIG)
