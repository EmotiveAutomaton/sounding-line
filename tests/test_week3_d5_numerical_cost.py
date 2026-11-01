"""Cost-only producer replay, complete-source boundary and refusal checks."""
from pathlib import Path
import numpy as np
import pytest
from runners.stage14.common import read,freeze
from runners.drive.cards import week3_d5_numerical_cost as c


def test_constructed_handler_and_output_tamper(tmp_path):
    assert c.execute(tmp_path,{},c.CONSTRUCTED)['status']=='complete'
    assert c.verify(tmp_path,{},c.CONSTRUCTED)['full_fresh_constructed_cost_replay']
    s=read(tmp_path/'SUMMARY.json')
    assert s['constructed_features_only'] and not s['human_outcomes_computed'] and not s['scientific_admission']
    assert s['numerical_operations']==48 and len(s['operation_hashes'])==6
    assert read(tmp_path/'TIMING.json')['complete_single_world_both_passes_margin_cpu_seconds']>0
    s['operation_hashes'][0]='wrong';(tmp_path/'SUMMARY.json').unlink();freeze(tmp_path/'SUMMARY.json',s)
    with pytest.raises(ValueError,match='replay differs'):c.verify(tmp_path,{},c.CONSTRUCTED)


def test_actual_complete_source_returns_only_layout_masks_and_banks():
    base=Path('results/phase_2_4_stage_15/raw/drive-week3-20261025')
    inputs=dict(context_complete=str(base/'D5-context-support/COMPLETE.json'),reader_complete=str(base/'D5-reader-cache/COMPLETE.json'))
    rows,folds,roster,banks,masks,shares,pins=c.load(inputs,c.CONFIG)
    assert (len(rows),len(folds),len(roster),len(shares))==(1399,61,45,200)
    assert {k:v.shape for k,v in masks.items()}=={'selection':(1399,4),'rhythm':(1399,22)}
    assert all(v.dtype==np.bool_ for v in masks.values()) and len(pins)>2800
    assert all(len(b['assignments'])==1000 for b in banks.values())
    assert not any(p.endswith('.npy.gz') for p in pins)


def test_changed_producer_and_config_refuse(tmp_path):
    with pytest.raises(ValueError,match='configuration'):c.load({},dict(c.CONSTRUCTED,sample_draws=1))
    freeze(tmp_path/'COMPLETE.json',{'status':'FAILED'})
    with pytest.raises(ValueError,match='completed source'):c.load(dict(context_complete=str(tmp_path/'COMPLETE.json'),reader_complete='unread'),c.CONFIG)


def test_constructed_boundary_yield(tmp_path):
    freeze(tmp_path/'YIELD_REQUEST.json',{'why':'test'})
    assert c.execute(tmp_path,{},c.CONSTRUCTED)['status']=='yielded'
    assert not (tmp_path/'SUMMARY.json').exists()
