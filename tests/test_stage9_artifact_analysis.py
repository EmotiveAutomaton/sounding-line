import copy
import pytest
from runners.stage9.artifact_analysis import select,evaluate


def rows(prefix):
    return [{'unit':prefix+str(i),'truth':'x','domain':'a' if i%2 else 'b','purpose':'p',
        'rows':{'artifact|dose1':{'predictions':{'weak':{'x':.1,'y':.9},'best':{'x':.2,'y':.8},
            'model':{'x':.8,'y':.2}},'validity':{'weak':True,'best':True,'model':True}}}} for i in range(4)]


def card():
    return {'id':'fixture','card':'M01','left':{'query':'artifact|dose1','model':'model'},
        'right':{'query':'artifact|dose1','selected_for':'artifact|dose1'},'threshold':.05,
        'strata':['domain','purpose'],'required_controls':['wrong-maker'],
        'meaning':'known prospective advantage with separate control adjudication'}


def test_actual_selection_is_frozen_and_distinct_from_scientific_warrant():
    development=rows('dev');discovery=rows('disc');package='a'*64
    selected=select(development,[r['unit'] for r in development],{'artifact|dose1':['weak','best']},package)
    assert selected['artifact|dose1']['selection']['selected']=='best'
    result=evaluate(discovery,[r['unit'] for r in discovery],card(),selection=selected,package=package,draws=100)
    assert result['overall']['mean']==pytest.approx(1.3862943611198906)
    assert result['disposition']=='SUPPORT CANDIDATE'
    assert result['promotion_eligible'] is False
    with pytest.raises(ValueError):evaluate(development,[r['unit'] for r in development],card(),selection=selected,package=package,draws=100)
    with pytest.raises(ValueError):evaluate(discovery,[r['unit'] for r in discovery],card(),selection=selected,package='b'*64,draws=100)


def test_failed_required_prediction_retains_every_unit_without_a_score():
    development=rows('dev');discovery=rows('disc');package='a'*64
    selected=select(development,[r['unit'] for r in development],{'artifact|dose1':['weak','best']},package)
    discovery[0]['rows']['artifact|dose1']['validity']['model']=False
    result=evaluate(discovery,[r['unit'] for r in discovery],card(),selection=selected,package=package,draws=100)
    assert result['disposition']=='IMPLEMENTATION INVALID'
    assert result['assigned_units']==4 and result['scored_units']==0 and result['excluded_units']==0
    assert 'overall' not in result
    with pytest.raises(ValueError):
        evaluate(discovery[:-1],[r['unit'] for r in discovery],card(),selection=selected,package=package,draws=100)
    with pytest.raises(ValueError):
        select(discovery[:-1],[r['unit'] for r in discovery],{'artifact|dose1':['model']},package)
    # Unrelated model failure cannot contaminate the complete baseline selection.
    assert select(discovery,[r['unit'] for r in discovery],{'artifact|dose1':['weak','best']},package)['artifact|dose1']['accepted']


def test_equal_forecasts_and_incomplete_discovery_have_distinct_dispositions():
    data=rows('disc');contrast=card();contrast['right']={'query':'artifact|dose1','model':'model'}
    result=evaluate(data,[r['unit'] for r in data],contrast,selection=None,package='a'*64,draws=100)
    assert result['overall']['mean']==0 and result['disposition']=='PRACTICALLY SMALL'
    with pytest.raises(ValueError):evaluate(data[:-1],[r['unit'] for r in data],contrast,selection=None,package='a'*64,draws=100)
