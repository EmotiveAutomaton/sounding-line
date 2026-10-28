import copy

import numpy as np
import pytest
from runners.drive.cards import week3_tr3_statistics as m


def chronology(data):
    rows=data['census']['roster']
    for r in rows:
        group=[s for s in rows if s['writer']==r['writer']]
        r['strict_prior_sessions']=sorted(s['session'] for s in group if s['end']<r['start'])
        r['overlapping_or_touching_sessions']=sorted(s['session'] for s in group if s['session']!=r['session'] and
            max(s['start'],r['start'])<=min(s['end'],r['end']))


def fixture():
    names=['w1:f','w1:g','w1:h','w1:i']; rows=[]; units={}
    for writer in ('a','b'):
        for k in range(2):
            sid=writer+str(k);chars=20 if k==0 else 100
            row=dict(session=sid,writer=writer,prompt='p',half='test',start=100*k,end=100*k+10,
                     typed_inserted_characters=chars)
            offers=({names[0 if writer=='a' else 1]:dict(shown=1,accepted=1),
                     names[2 if writer=='a' else 3]:dict(shown=2,dismissed=2)} if k==0 else {})
            counts={'w1:f':3,'w1:h':1,'w1:g':1,'w1:i':1} if sid=='a1' else {}
            rows.append(row);units[sid]=dict(session=sid,writer=writer,prompt='p',half='test',
                                           typed_characters=chars,human_counts=counts,offers=offers)
    data=dict(census=dict(roster=rows),units=units,
              selection=dict(features=[dict(feature=f,family='w1',frequency_decile=5) for f in names]))
    chronology(data);return data


def test_exact_matched_rates_and_secondary_weights():
    study=m.Study(**fixture()); result=study.evaluate(details=True)
    assert result['estimates']['primary']==50
    assert result['estimates']['accepted_minus_dismissed']==100
    assert result['estimates']['dismissed_minus_placebo']==0
    assert result['estimates']['without_current_reexposure']==50
    assert result['estimates']['dose']<0
    assert result['support']['primary']==dict(writers=2,sessions=2)
    assert result['exclusions']=={'no-prior-session':2}


def test_reassignment_rebuilds_earlier_typing_eligibility_matches_and_practice():
    study=m.Study(**fixture()); original=study.evaluate(details=True)
    shuffled=dict(study.outcomes);shuffled['a0'],shuffled['a1']=shuffled['a1'],shuffled['a0']
    changed=study.evaluate(shuffled,details=True)
    before=next(s for s in original['sessions'] if s['session']=='a1')
    after=next(s for s in changed['sessions'] if s['session']=='a1')
    assert before['eligibility']==2 and before['practice_characters']==20
    assert after['eligibility']==0 and after['practice_characters']==100
    assert after['exclusion']=='no-eligible-feature' and after['matches']=={}
    assert changed['estimates']['primary']==0


def test_current_reexposure_only_changes_declared_diagnostic():
    data=fixture();data['units']['a1']['offers']={'w1:f':dict(shown=1,other=1)}
    result=m.Study(**data).evaluate()
    assert result['estimates']['primary']==50
    assert result['estimates']['without_current_reexposure']==0


def test_donor_touching_boundary_is_not_earlier_and_overlap_stays_unsupported():
    data=fixture();next(r for r in data['census']['roster'] if r['session']=='b0')['end']=100
    chronology(data);result=m.Study(**data).evaluate()
    assert result['estimates']['primary'] is None
    assert result['exclusions']['ambiguous-chronology']==2
    assert result['exclusions']['no-placebo-match']==1


def test_wrong_prompt_or_frequency_bin_cannot_match():
    data=fixture()
    for r in data['census']['roster']:
        if r['writer']=='b':r['prompt']='other';data['units'][r['session']]['prompt']='other'
    assert m.Study(**data).evaluate()['estimates']['primary'] is None
    data=fixture()
    for r in data['selection']['features']:
        if r['feature'] in ('w1:g','w1:i'):r['frequency_decile']=6
    assert m.Study(**data).evaluate()['estimates']['primary'] is None


def test_zero_denominator_is_missing_not_a_zero_effect():
    data=fixture();data['units']['a1']['typed_characters']=0
    next(r for r in data['census']['roster'] if r['session']=='a1')['typed_inserted_characters']=0
    result=m.Study(**data).evaluate()
    assert result['estimates']['primary']==0 and result['support']['primary']['writers']==1
    assert result['exclusions']['zero-typed-characters']==1


def test_mixed_exposure_retained_in_primary_but_not_pure_secondary():
    data=fixture();data['units']['a0']['offers']['w1:f']=dict(shown=2,accepted=1,dismissed=1)
    result=m.Study(**data).evaluate(details=True)
    assert result['estimates']['primary']==50
    assert result['support']['accepted_minus_dismissed']['writers']==1
    assert next(s for s in result['sessions'] if s['session']=='a1')['exposure_kinds']['mixed']==1


def test_bootstrap_keeps_complete_writer_tuples():
    result=m.Study(**fixture()).evaluate()
    band=m.intervals(result,['a','b'],draws=2000)['primary']
    assert band['defined']==2000 and band['interval']==[0,100]


def test_permutations_preserve_writer_prompt_pairs_and_counts():
    data=m.world(123,0,writers=4);study=m.Study(**data);shuffled=study.permute(np.random.default_rng(1))
    for block in study.blocks:
        before=sorted((sorted(study.outcomes[s][0].items()),study.outcomes[s][1]) for s in block)
        after=sorted((sorted(shuffled[s][0].items()),shuffled[s][1]) for s in block)
        assert before==after


def test_reference_undefined_values_are_retained_and_not_zeroed():
    data=fixture()
    # Both writers must have later typing that removes prior eligibility when
    # reassigned to their first session. Empty typing for b in both sessions
    # made the old example always retain at least one usable comparison.
    data['units']['b1']['human_counts']=dict(data['units']['a1']['human_counts'])
    study=m.Study(**data)
    both_swapped=dict(study.outcomes)
    for writer in ('a','b'):
        both_swapped[writer+'0'],both_swapped[writer+'1']=study.outcomes[writer+'1'],study.outcomes[writer+'0']
    missing=study.evaluate(both_swapped)
    assert missing['estimates']['primary'] is None
    assert missing['support']['primary']==dict(writers=0,sessions=0)
    result=m.describe(study,permutations=20,bootstraps=30)
    assert result['reference_histories_rebuilt']
    assert len(result['references'])==20
    assert 0<result['metrics']['primary']['reference_defined']<20
    assert any(r['estimates']['primary'] is None for r in result['references'])
    assert not result['metrics']['primary']['reference_supported']
    assert result['metrics']['primary']['p_positive'] is None


@pytest.mark.parametrize('fault',['denominator','count','offers','identity','chronology','population'])
def test_invalid_source_refuses(fault):
    data=fixture()
    if fault=='denominator':data['units']['a1']['typed_characters']=-1
    elif fault=='count':data['units']['a1']['human_counts']['w1:f']=True
    elif fault=='offers':data['units']['a0']['offers']['w1:f']['shown']=2
    elif fault=='identity':data['units']['a1']['writer']='wrong'
    elif fault=='chronology':data['census']['roster'][1]['strict_prior_sessions']=[]
    else:del data['units']['b1']
    with pytest.raises(ValueError):m.Study(**data)


def test_planted_directions_exist_before_inference():
    positive=m.Study(**m.world(20261026,1)).evaluate()['estimates']['primary']
    negative=m.Study(**m.world(20261026,-1)).evaluate()['estimates']['primary']
    assert positive>0 and negative<0
