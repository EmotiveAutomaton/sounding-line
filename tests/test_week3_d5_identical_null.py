"""Analytic-null assertion must reject alternatives, corruption and missingness."""
import numpy as np
import pytest
from runners.stage14.common import read,freeze
from runners.drive.cards import week3_d5_identical_null as c
from runners.drive.cards import week3_d5_scoring_core as core


def test_complete_constructed_replay_and_tamper(tmp_path):
    assert c.CONFIG['sample_draws']==1000
    assert c.execute(tmp_path,{},c.CONSTRUCTED)['status']=='complete'
    assert c.verify(tmp_path,{},c.CONSTRUCTED)['full_fresh_identical_null_replay']
    s=read(tmp_path/'SUMMARY.json');assert s['identical_known_answer_verified']
    assert s['numerical_operations']==48 and len(s['operation_hashes'])==6
    assert not s['human_outcomes_computed'] and not s['scientific_admission']
    s['operation_hashes'][0]='wrong';(tmp_path/'SUMMARY.json').unlink();freeze(tmp_path/'SUMMARY.json',s)
    with pytest.raises(ValueError,match='replay differs'):c.verify(tmp_path,{},c.CONSTRUCTED)


def test_analytic_check_rejects_person_alternative_and_nonfinite():
    distinct,_=core.process_scores(np.eye(6),np.eye(6),np.arange(6))
    with pytest.raises(ValueError,match='analytic answer'):c.require_identical(distinct,6)
    for broken in ([0]*6,[np.nan]*6,[np.inf]*6):
        with pytest.raises(ValueError,match='analytic answer'):c.require_identical(broken,6)
    c.require_identical(np.full(6,1/6),6)


def test_no_reduced_full_config_and_boundary_yield(tmp_path):
    with pytest.raises(ValueError,match='configuration'):c.load({},dict(c.CONFIG,sample_draws=12))
    freeze(tmp_path/'YIELD_REQUEST.json',{'why':'test'})
    assert c.execute(tmp_path,{},c.CONSTRUCTED)['status']=='yielded'
    assert not (tmp_path/'SUMMARY.json').exists()
