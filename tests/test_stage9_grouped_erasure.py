import copy
import itertools
import math
import random

import pytest

from runners.stage9.artifact_view import all_header_actions
from runners.stage9.erased_inference import artifact_likelihood,transition
from runners.stage9.grouped_erasure import Kernel,likelihood
from runners.stage9.mark_program import neutral_program
from runners.stage9.program_inference import Budget
from tests.test_stage9_erased_inference import A,B,marked,program


def rich():
    work=marked([])
    work['context']['sections']=[{'name':'s','slots':['one','two']},{'name':'t','slots':['three']}]
    work['marks']=sorted(['write:s:one','write:s:two','check:s:one','check:t:three','cite:t:ref'])
    p=neutral_program();rng=random.Random(997)
    p['section_bias']=.83
    p['expertise']['progress']={k:rng.uniform(-2,2) for k in p['expertise']['progress']}
    p['purpose']={k:rng.uniform(-1,1) for k in p['purpose']}
    p['expertise']['success']={k:rng.uniform(.1,1) for k in p['expertise']['success']}
    p['context']['library']='available';work['context']['tools']['library']=False
    return p,work


def test_grouped_transitions_match_full_action_execution_at_every_count_state():
    p,work=rich();kernel=Kernel(p,work)
    for state in itertools.product(*(range(n+1) for n in kernel.maximum)):
        observed={'context':work['context'],'marks':kernel.representative_marks(state)}
        independent=transition(p,observed,Budget(10))
        edges=kernel.edges(state,Budget(10))
        expected=[sum(independent[a] for a in ids[n:]) for ids,n in zip(kernel.observed_marks,state)]
        assert edges==pytest.approx(expected,rel=1e-12,abs=1e-14)


def test_exact_grouping_matches_subset_sum_and_independent_fractions():
    assert math.exp(likelihood(program(),marked([A,B]),Budget(100))['log_mass'])==pytest.approx(9/16)
    assert math.exp(likelihood(program(success=.5),marked([A,B]),Budget(100))['log_mass'])==pytest.approx(9/25)
    p,work=rich()
    exact=artifact_likelihood(p,work,Budget(10000))
    grouped=likelihood(p,work,Budget(10000))
    assert grouped['log_mass']==pytest.approx(exact['log_mass'],abs=1e-12)
    assert grouped['count_states']<2**len(work['marks'])
    assert grouped['exact']


def test_known_density_sampler_agrees_in_mean_and_reports_nonconstant_uncertainty():
    p,work=rich()
    exact=math.exp(likelihood(p,work,Budget(10000))['log_mass'])
    values=[likelihood(p,work,Budget(1000),exact_states=0,draws=8,seed=i) for i in range(300)]
    ratios=[math.exp(v['log_mass'])/exact for v in values]
    assert sum(ratios)/len(ratios)==pytest.approx(1.,abs=.02)
    assert max(ratios)-min(ratios)>.01
    assert all(not v['exact'] and v['proposal_density_known'] and v['relative_standard_error']>0 for v in values)


def test_empty_impossible_and_budget_exhaustion_remain_explicit():
    assert likelihood(program(),marked([]),Budget(1))['log_mass']==0
    p=program();p['available_types']=['check']
    assert likelihood(p,marked([A]),Budget(20))['log_mass']==-math.inf
    with pytest.raises(ValueError,match='budget'):
        likelihood(*rich(),Budget(1))
