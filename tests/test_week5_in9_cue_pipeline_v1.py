import copy
import math
import numpy as np
import pytest
from runners.drive.cards import week5_in9_cue_pipeline_v1 as study
from runners.drive.cards import week5_in9_cue_fixture_v1 as fixture


def test_hand_counts_and_complete_private_source_reentry(tmp_path):
    fixture.source_chain(tmp_path/'source')


def test_literal_negation_is_not_semantic_qualification():
    text='Nobody laughed at me. This was not everyone; it was quiet.'
    assert study.literal.count(text)['LAUGHED_AT']==1
    assert study.literal.count(text)==study.literal.independent_count(text)


def test_census_and_fixed_sample_preserve_80percent_gate():
    frame=fixture.world(); small=frame.iloc[:80].copy()
    for frame_,expected in [(frame,'fixed100-hit sample'),(small,'census')]:
        specimen,audit,identity=fixture.reviews(frame_)
        assert specimen['families']['VICTIM']['method']==expected
        n=len(audit['families']['VICTIM']); allowed=n//5
        for i in range(allowed): audit['families']['VICTIM'][i].update(correct=False,reason='literal_only')
        assert study.audit_gate(specimen,audit,identity)['VICTIM']['status']=='qualified literal cue'
        audit['families']['VICTIM'][allowed].update(correct=False,reason='literal_only')
        assert study.audit_gate(specimen,audit,identity)['VICTIM']['status']=='instrument failed'


def test_prevalence_missing_review_and_source_swap_refusals(tmp_path):
    frame=fixture.world(); frame['VICTIM']=0; frame.loc[0,'VICTIM']=1
    specimen,audit,identity=fixture.reviews(frame)
    assert study.audit_gate(specimen,None,identity)['VICTIM']['status'].startswith('unsupported')
    assert study.audit_gate(specimen,None,identity)['AUDIENCE']['status'].startswith('held')
    altered=copy.deepcopy(audit);altered['sample_sha256']='other'
    with pytest.raises(ValueError,match='source/sample'):study.audit_gate(specimen,altered,identity)
    altered=copy.deepcopy(audit);altered['families']['AUDIENCE'][0]['text']='forbidden'
    with pytest.raises(ValueError,match='never source text'):study.audit_gate(specimen,altered,identity)
    with fixture.prepared_boundary(frame,specimen,None,identity):
        result=study.execute(tmp_path/'held',{}, {'phase':'IN9-cues'})
        assert result['status'].startswith('count-only') and not (tmp_path/'held/DRAWS.json').exists()


def test_hand_log_odds_and_finite_support():
    assert study.math.odds([2,1,1,2])['log_odds_ratio']==math.log(4)
    assert abs(study.math.odds([2,1,1,2],True)['log_odds_ratio']-math.log(4))<1e-12
    assert study.math.odds([2,2,2,2])['log_odds_ratio']==0
    assert 'failure' in study.math.odds([0,2,2,2])
    point=study.math.odds([20,10,10,20]);draws=[point]*1999+[study.math.odds([0,10,10,20])]
    result=study.math.summarize(point,draws,40)
    assert result['failed_draws']==[1999] and result['population_interval'] is None
    assert study.math.summarize(point,[],1)['status']=='below floor, descriptive'


def test_complete_signed2000_draws_and_independent_handler_replay(tmp_path):
    assert fixture.full_chain(tmp_path/'signed','positive')['passed']


def test_complete_exact_null2000_draws_and_no_false_inference(tmp_path):
    assert fixture.full_chain(tmp_path/'null','null')['passed']


def test_whole_writer_weights_and_checkpoint_tamper_refuse(tmp_path):
    frame=fixture.world(); p=study.math.prepare(frame)
    weights=study.math.draw_weights(p['codes'],len(p['keys']),17)
    assert all(len(np.unique(weights[p['codes']==code]))==1 for code in range(len(p['keys'])))
    specimen,audit,identity=fixture.reviews(frame);config={'phase':'IN9-cues','max_new_draws':1}
    with fixture.prepared_boundary(frame,specimen,audit,identity):
        assert study.execute(tmp_path/'one',{},config)['status']=='yielded'
        (tmp_path/'one/DRAWS.json').write_text('{}',encoding='utf8')
        with pytest.raises(ValueError,match='checkpoint changed'):study.execute(tmp_path/'one',{},config)


def test_changed_source_binding_and_undeclared_phase_refuse(tmp_path):
    with pytest.raises(ValueError): study.load_source({})
    with pytest.raises(ValueError): study.settings({'phase':'IN9-cues','draws':100})
    frame=fixture.world();specimen,audit,identity=fixture.reviews(frame);config={'phase':'IN9-cues','max_new_draws':1}
    with fixture.prepared_boundary(frame,specimen,audit,identity): study.execute(tmp_path/'one',{},config)
    identity['unrelated_new_source']='changed'
    with fixture.prepared_boundary(frame,specimen,audit,identity), pytest.raises(ValueError,match='binding changed'):
        study.execute(tmp_path/'one',{},config)
