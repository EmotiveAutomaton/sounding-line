import copy
import pytest
from runners.stage9.factorial_analysis import summarize
from runners.stage9.training_jobs import FITS


def fixture(breadth=0.,exposure=0.,interaction=0.,reverse_smollm=False):
    rows=[]
    for family,recipe,seed in FITS:
        b=int(recipe.startswith('both'));e=int(recipe.endswith('mixed'))
        effect=b*breadth+e*exposure+b*e*interaction
        if reverse_smollm and family=='smollm':effect=-effect
        paired=[{'unit':str(i),'source_unit':str(i),'domain':'essay' if i<96 else 'workshop_doc',
            'law':'original' if i%2 else 'expanded','purpose':'teach','target_type':'write',
            'rival_log_score':-3.,'reader_log_score':-4.+effect,'valid':True} for i in range(192)]
        rows.append({'family':family,'recipe':recipe,'seed':seed,'status':'COMPLETE','choice_rows':paired,
            'instrument_accepted':True,'generation':{}})
    return rows


def estimate(result,family,contrast):
    return result['families'][family]['effects'][contrast]['groups']['overall']['estimate']


def test_null_and_independent_factorial_interaction_with_reversed_family():
    null=summarize(fixture(),'scientific',draws=100)
    for family in ('qwen','smollm'):
        for name in null['families'][family]['effects']:
            assert estimate(null,family,name)['mean']==0
    result=summarize(fixture(.2,.1,.3,True),'scientific',draws=100)
    for family,sign in [('qwen',1),('smollm',-1)]:
        assert estimate(result,family,'breadth_expert')['mean']==pytest.approx(sign*.2)
        assert estimate(result,family,'exposure_original')['mean']==pytest.approx(sign*.1)
        assert estimate(result,family,'interaction')['mean']==pytest.approx(sign*.3)
        assert estimate(result,family,'breadth_main')['mean']==pytest.approx(sign*.35)
        assert estimate(result,family,'exposure_main')['mean']==pytest.approx(sign*.25)
    assert summarize(list(reversed(fixture(.2,.1,.3,True))),'scientific',draws=100)['families']['qwen']['effects']==result['families']['qwen']['effects']


def test_lucky_seed_failed_seed_and_invalid_instrument_are_retained():
    rows=fixture()
    for row in rows:
        if row['family']=='qwen' and row['recipe']=='both_mixed':
            for p in row['choice_rows']:p['reader_log_score']+=1. if row['seed']==9001 else -.5
    result=summarize(rows,'scientific',draws=100)
    overall=result['families']['qwen']['effects']['exposure_both']['groups']['overall']
    assert overall['estimate']['mean']==0
    assert overall['per_seed']['9001']['mean']==1. and overall['per_seed']['9002']['mean']==-.5
    broken=next(r for r in rows if r['family']=='qwen' and r['recipe']=='original_mixed' and r['seed']==9002)
    broken.update(status='FAILED',reason='retained actual failure')
    result=summarize(rows,'scientific',draws=100)
    assert result['families']['qwen']['effects']['interaction']['disposition']=='NOT RUN WITH REASON'
    assert estimate(result,'qwen','breadth_expert')['mean']==0
    rows=fixture(.2);rows[0]['instrument_accepted']=False
    result=summarize(rows,'scientific',draws=100)
    assert result['families']['qwen']['effects']['breadth_expert']['groups']['overall']['disposition']=='IMPLEMENTATION INVALID'


def test_missing_unfinished_support_mismatch_and_nonfinite_scores():
    rows=fixture()
    with pytest.raises(ValueError):summarize(rows[:-1],'scientific',draws=100)
    rows[0]['status']='RUNNING'
    with pytest.raises(ValueError):summarize(rows,'scientific',draws=100)
    rows=fixture();rows[0]['choice_rows'][0]['unit']='different-public-question'
    with pytest.raises(ValueError,match='paired questions'):summarize(rows,'scientific',draws=100)
    rows=fixture();rows[0]['choice_rows'][0]['reader_log_score']={'extended_real':'negative_infinity'}
    result=summarize(rows,'scientific',draws=100)
    value=estimate(result,'qwen','breadth_expert')
    assert value['finite_estimate'] is False and value['excluded_targets']==0 and value['n_targets']==576
    assert len(result['families']['qwen']['all_seed_profiles'])==12


def test_repeated_questions_do_not_add_independent_units():
    rows=fixture(.2)
    for row in rows:
        for p in row['choice_rows']:p['unit']='one-public-question'
    result=summarize(rows,'scientific',draws=100)
    value=estimate(result,'qwen','breadth_expert')
    assert value['n_units']==1 and value['ci'] is None and value['n_targets']==576
