import copy
import time

import pytest

from runners.stage9.common import ROOT
from runners.stage9.queue import manual_review_path, validate_manifest


def plan():
    source = 'runners/stage9/confirmation_fixture.py'
    freezer = 'runners/stage9/confirmation_freeze.py'
    return {'kind':'prelaunch_rehearsal', 'horizon_epoch':time.time()+60,
        'sources':{'files':{source:'fixture',freezer:'fixture'}}, 'jobs':[
            {'id':'source','module':'runners.stage9.confirmation_fixture','arguments':[],
             'produces':str(ROOT/'private/review-fixture/source/COMPLETE.json'),
             'after':[],'requires':[],'resource':'cpu','role':'work','estimated_gpu_seconds':0},
            {'id':'freeze','module':'runners.stage9.confirmation_freeze',
             'arguments':['--review',str(ROOT/'private/review-fixture/REVIEW.json')],
             'produces':str(ROOT/'private/review-fixture/freeze/COMPLETE.json'),
             'after':['source'],'requires':[],'allow_failed_dependencies':True,
             'resource':'cpu','role':'closure','estimated_gpu_seconds':0}]}


def test_absent_review_is_a_declared_future_input_not_manifest_failure():
    p=plan()
    assert validate_manifest(p)
    assert manual_review_path(p['jobs'][0]) is None
    assert manual_review_path(p['jobs'][1]) == ROOT/'private/review-fixture/REVIEW.json'


@pytest.mark.parametrize('fault',['missing_upstream','failed_dependency_gate','scientific_gate','duplicate_path'])
def test_review_cannot_avoid_upstream_failures_or_hide_an_input(fault):
    p=copy.deepcopy(plan());job=p['jobs'][1]
    if fault=='missing_upstream':job['after']=[]
    elif fault=='failed_dependency_gate':job['allow_failed_dependencies']=False
    elif fault=='scientific_gate':job['requires']=[{'job':'source','field':['accepted'],'equals':True}]
    else:job['arguments']+=job['arguments']
    with pytest.raises(ValueError):validate_manifest(p)
