import pytest
from runners.drive.cards import week3_pieces_pilot as w
from tests.test_week3_pieces_coverage import prepared


def test_first_tenth_measures_new_work_and_replays_without_verdict(tmp_path):
    inputs=prepared(tmp_path)
    config=dict(mode="constructed",coarse=False,seed=20261026,pilot_draws=2,minimum_occurrences=1,minimum_writers=1)
    result=w.execute(tmp_path/"pilot",inputs,config)
    assert result["status"]=="cost_probe_complete" and not result["scientific_admission"]
    assert result["timing"]["reference_cpu_seconds"]>0
    assert result["timing"]["projected_combined_coverage_cpu_seconds"]>result["timing"]["cpu_seconds"]
    assert w.verify(tmp_path/"pilot",inputs,config)["verified"]


def test_zero_work_or_reduced_corpus_probe_refused(tmp_path):
    config=dict(mode="constructed",coarse=False,seed=20261026,pilot_draws=0,minimum_occurrences=1,minimum_writers=1)
    with pytest.raises(ValueError,match="positive new-work"):
        w.measure(tmp_path,{},config)
    with pytest.raises(ValueError,match="first tenth"):
        w.measure(tmp_path,{},dict(config,mode="corpus",pilot_draws=2))
