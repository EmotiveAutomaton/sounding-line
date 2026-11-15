"""Constructed-only Week 6 IN14/IN16 checks; no corpus outcomes."""
import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week6_in14_math_v1 as c
from runners.drive.cards import week6_in16_math_v1 as d
from runners.drive.cards import week6_in14_in16_fixture_v1 as fixture
from runners.drive.cards import week6_in14_in16_source_v1 as source
from runners.drive.cards import week6_in14_in16_run_v1 as run


def surveys():
    return pd.DataFrame([{'text_id':f't{i}','prolific_id':'w','emotion':e,
        'timestamp':f'2021/01/01 12:{i*4:02}:00 PM CET','round_number':'round-2',
        **dict.fromkeys(c.PRIOR,2),'source_qualified':True,'intensity':3,'emotion_duration_rank':2,'N':4.}
        for i,e in enumerate(['anger','joy','fear','sadness','pride'])])


def test_zones_and_unknown_zone():
    assert c.timestamp('2021/01/01 01:00:00 PM EET')==c.timestamp('2021/01/01 12:00:00 PM CET')
    with pytest.raises(ValueError,match='zone'):c.timestamp('2021/01/01 12:00:00 PM XYZ')


def test_pair_before_exclusion_never_bridges():
    frame=surveys();frame.loc[2,'source_qualified']=False
    rows,counts=c.pairs(frame,['round-2'])
    assert counts['unqualified']==2 and counts['retained']==2
    assert set(rows.pair_id)=={'t0:t1','t3:t4'}


def test_same_prompt_and_surprise_removed_before_long_rows():
    frame=surveys();frame.loc[1,'emotion']='anger';frame.loc[2,'emotion']='surprise'
    rows,counts=c.pairs(frame,['round-2'])
    assert counts['same_prompt']==1 and counts['first_prompt_set_aside']==1
    assert set(rows.feeling)==set(c.FEELINGS) and 'surprise' not in set(rows.feeling)


def test_ineligible_round_keeps_original_adjacency():
    frame=surveys();frame.loc[2,'round_number']='round-3';frame.loc[3:,'round_number']='round-3'
    rows,counts=c.pairs(frame,['round-2'])
    assert counts['ineligible_round']==3 and set(rows.pair_id)=={'t0:t1'}


def test_chronology_and_scale_refuse():
    frame=surveys();frame.loc[0,'round_number']='round-3'
    with pytest.raises(ValueError,match='round order'):c.pairs(frame,['round-2','round-3'])
    frame=surveys();frame.loc[1,'anger']=6
    with pytest.raises(ValueError,match='rating'):c.pairs(frame,['round-2'])


@pytest.mark.parametrize('plant,gaps',[(.5,(2.,10.)),(.5,(30.,60.)),(0.,(2.,10.))])
def test_carryover_plant_and_independent_fit(plant,gaps):
    rows=fixture.carryover(plant,gaps=gaps);panel=c.design(rows)
    actual,error=c.fit(panel);replay,other=c.fit(panel,independent=True)
    expected=plant*20/(gaps[1]-gaps[0])*(np.exp(-gaps[0]/20)-np.exp(-gaps[1]/20))
    assert error is None and other is None and abs(actual['prompt']-expected)<.012
    assert np.allclose(list(actual.values()),list(replay.values()),atol=1e-10)


def test_writer_counts_change_fit_like_weighted_rows():
    panel=c.design(fixture.carryover(pairs=160,writers=8));weights={k:i%3 for i,k in enumerate(panel['keys'])}
    actual,_=c.fit(panel,weights);expected,_=c.fit(panel,weights,True)
    assert np.allclose(list(actual.values()),list(expected.values()),atol=1e-10)


def test_shared_survey_boundary_is_visible_not_false_reliability():
    frame=surveys()
    for i in range(len(frame)):
        for j,k in enumerate(c.PRIOR):frame.loc[i,k]=1+(i+j)%5
    rows,_=c.pairs(frame,['round-2']);people=c.person_preparation(rows)
    assert len(people)==1 and people[0]['halves_share_survey'] is True
    assert 'corrected_reliability' not in people[0]


@pytest.mark.parametrize('slope',[.2,0.])
def test_clearing_plant_units_and_replay(slope):
    prepared=d.prepare(fixture.clearing_frame(slope));counts=dict.fromkeys(prepared['keys'],1)
    actual,error=d.clearing(prepared['clearing'],counts);replay,_=d.clearing(prepared['clearing'],counts,True)
    assert error is None and abs(actual-slope)<1e-10 and abs(actual-replay)<1e-10


def test_reml_writer_share_and_reference():
    frame=fixture.share_frame();panel=d.matrix(frame,list(source.original.APPRAISALS),'intensity');counts=dict.fromkeys(panel['keys'],1)
    actual,error=d.writer_share(panel,counts);reference,other=d.writer_share(panel,counts,True)
    assert error is None and other is None and abs(actual-.2)<.03
    assert abs(actual-reference)<1e-7


def test_reml_boundary_zero_and_one_writer_refusal():
    frame=fixture.share_frame(0,writers=80);panel=d.matrix(frame,list(source.original.APPRAISALS),'intensity')
    value,error=d.writer_share(panel,dict.fromkeys(panel['keys'],1))
    assert error is None and 0<=value<.06
    value,error=d.writer_share(panel,{panel['keys'][0]:80})
    assert value is None and 'two independent' in error


def test_inventory_conflicts_and_missing_are_not_selected():
    frame=pd.DataFrame({'prolific_id':['a','a','b','b','c'],'anxious':[6,6,2,3,np.nan],'calm':[2,2,6,6,np.nan]})
    scores,counts=source.trait_map(frame)
    assert scores['a']==6 and np.isnan(scores['b']) and np.isnan(scores['c'])
    assert counts=={'available':1,'conflicting_source_items':1,'missing':1}


def test_duration_none_does_not_become_zero():
    assert source.duration.rank('I had none',True) is None
    assert [source.duration.rank(v) for v in ['seconds','minutes','hours','days','weeks']]==[1,2,3,4,5]
    with pytest.raises(ValueError):source.duration.rank('months')


def test_failed_draw_and_primary_reference_boundaries():
    result=run.summary(.2,[.2]*1999+[None],30,True)
    assert result['status']=='invalid_uncertainty' and result['failed_draws']==[1999] and 'interval' not in result
    result=run.summary(.2,[.2]*2000,30,True,True)
    assert 'outcome' not in result
    assert run.summary(.2,[.2]*2000,1,True)['status']=='unsupported'


BOUNDARY_CASES=[
    ((-.2,-.2),'against'),((-.2,-.1),'against'),((-.2,0.),'inconclusive'),
    ((-.2,.1),'inconclusive'),((-.2,.2),'inconclusive'),
    ((-.1,-.1),'against'),((-.1,0.),'against'),((-.1,.1),'against'),((-.1,.2),'inconclusive'),
    ((0.,0.),'against'),((0.,.1),'against'),((0.,.2),'inconclusive'),
    ((.1,.1),'against'),((.1,.2),'inconclusive'),((.2,.2),'supports'),
    ((-.2,-1e-12),'against'),((-.2,1e-12),'inconclusive'),
    ((.1+1e-12,.2),'supports'),((.1-1e-12,.2),'inconclusive'),
    ((-.1-1e-12,.1),'inconclusive'),((-.1+1e-12,.1),'against'),
    ((-.1,.1+1e-12),'inconclusive'),((-.1,.1-1e-12),'against'),
]


@pytest.mark.parametrize('interval,expected',BOUNDARY_CASES)
@pytest.mark.parametrize('direction',[1,-1])
def test_three_way_exhaustive_boundary_grid(interval,expected,direction):
    signed=interval if direction==1 else (-interval[1],-interval[0])
    assert run.three_way(signed,.1,direction)==expected


def test_three_way_refuses_invalid_inputs_and_preserves_report_scope():
    for interval,bar,direction in [((1.,0.),.1,1),((0.,np.nan),.1,1),((0.,1.),0.,1),((0.,1.),.1,0)]:
        with pytest.raises(ValueError):run.three_way(interval,bar,direction)
    assert run.summary(-.05,[-.05]*2000,30,True)['outcome']=='against'
    assert run.summary(0.,[0.]*2000,30,True)['outcome']=='against'
    assert run.summary(.2,[.2]*2000,30,True)['outcome']=='supports'
    for primary,reference,writers in [(False,False,30),(True,True,30),(True,False,19)]:
        assert 'outcome' not in run.summary(.2,[.2]*2000,writers,primary,reference)


def test_settings_refuse_dropped_draws_or_implicit_population():
    with pytest.raises(ValueError):run.settings('IN14',{})
    with pytest.raises(ValueError):run.settings('IN16',{'source_scope':'real-event-primary','draws':20})
    assert run.settings('IN16',{'source_scope':'real-event-primary'})['bar']==.1
    assert run.settings('IN14',{'source_scope':'real-event-primary'})['seed']==20261107
    assert run.settings('IN16',{'source_scope':'real-event-primary'})['seed']==20261107


def test_checkpoint_resume_binding_and_cooperative_yield(tmp_path):
    pieces=[]
    rng=np.random.default_rng(331)
    for i in range(8):
        frame=surveys();frame['prolific_id']=f'w{i}'
        frame['text_id']=[f'w{i}t{j}' for j in range(len(frame))]
        for feeling in c.PRIOR:frame[feeling]=rng.integers(1,6,len(frame))
        pieces.append(frame)
    frame=pd.concat(pieces,ignore_index=True)
    identity={'eligible_rounds':['round-2'],'constructed':True}
    config={'source_scope':'real-event-primary','max_new_draws':1}
    a=run.calculate('IN14',frame,identity,tmp_path,config)
    b=run.calculate('IN14',frame,identity,tmp_path,config)
    assert a['completed']==1 and b['completed']==2 and b['verified'] is False
    frame.loc[0,'anger']=1 if frame.loc[0,'anger']!=1 else 2
    with pytest.raises(ValueError,match='binding changed'):
        run.calculate('IN14',frame,identity,tmp_path,config)


def test_blank_questionnaire_gate_checks_every_member_and_item_order(tmp_path,monkeypatch):
    import hashlib,json,zipfile
    member='questionnaires/generation/round-2/strategy1_free/anger.pdf'
    blank=b'constructed blank questionnaire'
    document={'eligible_rounds':['round-2'],'questionnaires':[{'member':member,'sha256':hashlib.sha256(blank).hexdigest(),
        'eligible':True,'current_state_page':2,'named_prompt_page':3,'recall_page':3}]}
    manifest=tmp_path/'review.json';manifest.write_text(json.dumps(document))
    monkeypatch.setattr(source,'ELIGIBILITY',manifest)
    monkeypatch.setattr(source,'ELIGIBILITY_PIN',hashlib.sha256(manifest.read_bytes()).hexdigest())
    path=tmp_path/'archive.zip'
    with zipfile.ZipFile(path,'w') as archive:archive.writestr(member,blank)
    with zipfile.ZipFile(path) as archive:assert source.questionnaire_check(archive)==['round-2']
    document['questionnaires'][0]['named_prompt_page']=1;manifest.write_text(json.dumps(document))
    monkeypatch.setattr(source,'ELIGIBILITY_PIN',hashlib.sha256(manifest.read_bytes()).hexdigest())
    with zipfile.ZipFile(path) as archive:
        with pytest.raises(ValueError,match='precede'):source.questionnaire_check(archive)
