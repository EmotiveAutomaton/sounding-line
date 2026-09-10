import copy
import math
import pytest
from runners.stage9.paired_artifact_analysis import evaluate
from runners.stage9.launch import handler_operation


def rows(probability,target='x'):
    return [{'unit':str(i),'truth':target,'domain':'a' if i%2 else 'b','purpose':'p',
             'rows':{'query':{'evidence_sha256':'same-past-'+str(i),'support':['x','y'],
                 'predictions':{'model':{'x':probability,'y':1-probability},'base':{'x':.5,'y':.5}},
                 'validity':{'model':True,'base':True}}}} for i in range(4)]


def card():
    return {'id':'fixture','card':'T04','left':{'query':'query','model':'model','baseline':'base'},
            'right':{'query':'query','model':'model','baseline':'base'},'threshold':.05,'strata':['domain','purpose'],
            'required_controls':['paired actual interventions'],'meaning':'difference of gains against each condition own future'}


def test_interaction_uses_each_actual_future_and_null_is_gain_equality():
    a=rows(.8);b=rows(.2,'y');expected=[r['unit'] for r in a]
    zero=evaluate(a,b,expected,card(),role='discovery',draws=100)
    assert zero['overall']['mean']==pytest.approx(0.,abs=1e-14)
    b=rows(.4,'y');result=evaluate(a,b,expected,card(),role='discovery',draws=100)
    assert result['overall']['mean']==pytest.approx(math.log(.8/.6))
    assert result['promotion_eligible'] is False
    assert handler_operation({'module':'runners.stage9.paired_artifact_analysis','arguments':[]})[1]=='paired-analysis'


def test_unpaired_evidence_or_missing_required_component_refuses_all_units():
    a=rows(.8);b=rows(.4);expected=[r['unit'] for r in a]
    bad=copy.deepcopy(b);bad[0]['rows']['query']['evidence_sha256']='different'
    with pytest.raises(ValueError):evaluate(a,bad,expected,card(),role='pilot',draws=100)
    with pytest.raises(ValueError):evaluate(a,b[:-1],expected,card(),role='pilot',draws=100)
    bad=copy.deepcopy(b);bad[0]['rows']['query']['validity']['model']=False
    invalid=evaluate(a,bad,expected,card(),role='pilot',draws=100)
    assert invalid['disposition']=='IMPLEMENTATION INVALID' and invalid['scored_units']==0 and invalid['excluded_units']==0
    assert invalid['assigned_units']==4 and 'overall' not in invalid


def test_zero_probability_is_retained_without_finite_only_interaction():
    a=rows(0.);b=rows(.4);expected=[r['unit'] for r in a]
    result=evaluate(a,b,expected,card(),role='discovery',draws=100)
    assert result['disposition']=='DESCRIPTIVE' and result['finite_estimate'] is False
    assert result['assigned_units']==result['scored_units']==4 and result['excluded_units']==0
    assert len(result['unit_scores'])==4 and 'overall' not in result
