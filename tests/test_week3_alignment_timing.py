"""Timing is not a smaller-population inference or a reduced null bank."""
import json
from pathlib import Path
import pytest
from runners.drive.cards import week3_alignment_timing as card
from runners.drive.cards.menus_io import read,sha256
from tests.test_week3_alignment_stats import fixture


def test_actual_timing_and_fresh_replay_compute_no_heldout_score(tmp_path,monkeypatch):
    inputs=fixture(tmp_path/'inputs');output=tmp_path/'output'
    def forbidden(*args,**kwargs):raise AssertionError('timing must not score a hypothesis')
    monkeypatch.setattr(card.stats,'losses',forbidden);monkeypatch.setattr(card.stats,'summarize',forbidden)
    report=card.execute(output,inputs,{'fixture':True})
    assert report['scientific_inference'] is False and report['pilot_population_is_not_scientific_cohort']
    assert report['fixed_people_full']==report['people_with_sampled_training']==5
    assert card.verify(output,inputs,{'fixture':True})['verified']
    timing=read(output/'TIMING.json')
    assert timing['fit_and_fresh_replay_1000_null_projection_cpu_seconds']==timing['one_full_fit_projection_cpu_seconds']*2002


def test_production_timing_refuses_fixture_features(tmp_path):
    inputs=fixture(tmp_path/'inputs')
    with pytest.raises(ValueError,match='ten-percent feature pilot'):
        card.execute(tmp_path/'out',inputs,{})


def test_feature_receipt_cannot_be_mixed_with_other_preparation(tmp_path):
    inputs=fixture(tmp_path/'inputs');path=Path(inputs['features_summary']);summary=read(path)
    summary['input_hashes']['prepared_summary']='0'*64;path.write_text(json.dumps(summary))
    completion=Path(inputs['features_complete']);receipt=read(completion);receipt['outputs']['output/SUMMARY.json']=sha256(path)
    completion.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='different prepared'):
        card.execute(tmp_path/'out',inputs,{'fixture':True})


def test_changed_completed_timing_report_refused(tmp_path):
    inputs=fixture(tmp_path/'inputs');output=tmp_path/'output';card.execute(output,inputs,{'fixture':True})
    path=output/'SUMMARY.json';value=read(path);value['fixed_people_full']+=1;path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='recomputation'):
        card.verify(output,inputs,{'fixture':True})
