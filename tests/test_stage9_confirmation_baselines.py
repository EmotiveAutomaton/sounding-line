import copy
import math

import pytest

from runners.stage9 import confirmation_baselines as subject


def rows():
    return [{'unit':str(i),'target':'event','truth':'a','role':'pilot',
             'sides':{'left':{'valid':True,'probabilities':{'a':.8,'b':.2}},
                      'right':{'valid':True,'probabilities':{'a':.5,'b':.5}}},'costs':[]} for i in range(3)]


def test_complete_forecasts_recompute_the_actual_proper_paired_scores():
    result=subject.calculation_input(rows(),['0','1','2'])
    assert result['calculation_status']=='READY'
    assert [r['difference'] for r in result['paired_rows']]==pytest.approx([math.log(.8/.5)]*3)
    assert all(r['seed'] is None for r in result['paired_rows'])
    assert not result['scientific_confirmation'] and result['excluded_units']==0


@pytest.mark.parametrize('fault',['invalid','left_zero','right_zero','both_zero'])
def test_failure_or_nonfinite_target_prevents_any_finite_subset(fault):
    data=rows();item=data[1]
    if fault=='invalid':item['sides']['left']['valid']=False
    else:
        for side in ('left','right'):
            if fault=='both_zero' or fault==side+'_zero':item['sides'][side]['probabilities']={'a':0.,'b':1.}
    result=subject.calculation_input(data,['0','1','2'])
    assert result['calculation_status']=='NOT_RUN' and result['paired_rows'] is None
    assert result['assigned_units']==3 and result['excluded_units']==result['excluded_targets']==0
    assert result['limitations'][0]['unit']=='1'
    assert len(result['all_available_scores'])==(2 if fault=='invalid' else 3)


def test_missing_or_added_units_and_mismatched_support_refuse():
    data=rows()
    with pytest.raises(ValueError):subject.calculation_input(data[:-1],['0','1','2'])
    with pytest.raises(ValueError):subject.calculation_input(data+data[:1],['0','1','2'])
    data[0]['sides']['right']['probabilities']={'a':1.}
    with pytest.raises(ValueError):subject.calculation_input(data,['0','1','2'])


def test_frozen_views_and_doses_are_the_only_capsule_inputs(monkeypatch):
    case={'unit':'u','role':'pilot','target':'a'}
    seen=[]
    def project(case,dose,view):
        return {'support':['a','b'],'dose':dose,'view':view}
    monkeypatch.setattr(subject,'dose_view',project)
    models={'models':{'artifact':{'fit':{'parameters':'fixture'}},'process_record':{'other':{}}},
            'types':{'artifact':{'type':'fixture'},'process_record':{}}}
    contrast={'left':{'view':'artifact','dose':7,'model':'fit|cheap-8.0'},
              'right':{'view':'artifact','dose':0,'model':'fit|population'}}
    def call(bundle,view):
        seen.append((copy.deepcopy(bundle),view))
        return {'accepted':True,'wall_s':0.,'capsule':'fixture',
                'prediction':{'predictions':{name:{contrast[name]['model']:{'a':.5,'b':.5}} for name in bundle['evidences']}}}
    result=subject.forecast(case,models,contrast,call)
    assert len(seen)==1 and seen[0][1]=='artifact' and set(seen[0][0]['models'])=={'fit'}
    assert {name:e['dose'] for name,e in seen[0][0]['evidences'].items()}=={'left':7,'right':0}
    assert set(result['sides'])=={'left','right'}
