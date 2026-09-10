import copy
import math

import pytest

from runners.stage9.confirmation_statistics import CONTRACT, evaluate, family, tail_probability


def fixture(kind='positive', center=.15, adequate=True, name='one'):
    units = ['unit-' + str(i) for i in range(60)]
    seeds = [9001,9002,9003]
    packet = {'id': name, 'reserve_units': units, 'analysis_contract': copy.deepcopy(CONTRACT),
        'planning': {'planned_units':60,'practical_threshold':.05,'family':3,'familywise_alpha':.05,
                     'power_adequate':adequate,'claim_kind':kind,'discovery':{'seeds':seeds}}}
    targets = {u:['target-'+str(j) for j in range(i % 3 + 1)] for i,u in enumerate(units)}
    rows = [{'unit':u,'target':target,'seed':seed,
             'difference': center + (-.1 if i < 30 else .1) + shift}
            for i,u in enumerate(units) for target in targets[u]
            for seed,shift in zip(seeds,(-.02,0.,.02))]
    return packet, {'status':'COMPLETE','rows':rows,'assigned_targets':targets}


def test_student_t_tail_matches_analytic_cauchy_known_answers():
    # At one degree of freedom, Student t is exactly a Cauchy distribution.
    assert tail_probability(0.,1.,1,'positive',.05) == 1.
    assert tail_probability(1.,1.,1,'positive',.05) == pytest.approx(.5)
    for mean in (-2.,-.1,0.,.1,2.):
        cdf = lambda x: .5 + math.atan(x) / math.pi
        expected = max(1-cdf(mean+.05),cdf(mean-.05))
        assert tail_probability(mean,1.,1,'equivalence',.05) == pytest.approx(expected)


@pytest.mark.parametrize('kind,center,passes',[
    ('positive',.15,True),('negative',-.15,True),('equivalence',0.,True),
    ('positive',0.,False),('negative',.15,False),('equivalence',.15,False)])
def test_known_signal_null_wrong_direction_and_equivalence(kind,center,passes):
    packet,outcome=fixture(kind,center)
    result=family([packet],{'one':outcome})['claims']['one']
    assert result['summary']['n_units']==60
    assert result['summary']['mean']==pytest.approx(center,abs=1e-14)
    assert result['statistical_pass'] is passes
    assert result['scientific_confirmation'] is False
    assert list(result['summary']['seed_means'].values())==pytest.approx([center-.02,center,center+.02],abs=1e-14)


@pytest.mark.parametrize('fault',['missing_target_all_seeds','missing_seed','extra_unit','duplicate','nonfinite','changed_contract'])
def test_full_assigned_grid_and_frozen_analysis_are_required(fault):
    packet,outcome=fixture()
    if fault=='missing_target_all_seeds':outcome['rows']=outcome['rows'][3:]
    elif fault=='missing_seed':outcome['rows']=[r for r in outcome['rows'] if r['seed']!=9003]
    elif fault=='extra_unit':outcome['rows'][0]['unit']='unassigned'
    elif fault=='duplicate':outcome['rows'].append(outcome['rows'][0])
    elif fault=='nonfinite':outcome['rows'][0]['difference']=math.inf
    else:packet['analysis_contract']['bootstrap_seed']=7
    with pytest.raises(ValueError):family([packet],{'one':outcome})


def test_zero_variance_and_short_reserve_cannot_grant_statistical_pass():
    packet,outcome=fixture(adequate=False)
    result=family([packet],{'one':outcome})['claims']['one']
    assert result['multiplicity']['reject'] and not result['statistical_pass']
    for row in outcome['rows']:row['difference']=0.
    result=family([packet],{'one':outcome})['claims']['one']
    assert result['status']=='UNSUPPORTED_VARIANCE' and not result['statistical_pass']


def test_failed_and_unrun_claims_remain_in_the_exact_frozen_family():
    packet,outcome=fixture()
    bad=copy.deepcopy(packet);bad['id']='failed'
    unrun=copy.deepcopy(packet);unrun['id']='unrun'
    outcomes={'one':outcome,'failed':{'status':'FAILED','reason':'retained failed call','receipt_sha256':'a'*64},
              'unrun':{'status':'NOT_RUN','reason':'required gate failed','receipt_sha256':'b'*64}}
    result=family([packet,bad,unrun],outcomes)
    assert list(result['claims'])==['one','failed','unrun'] and result['family']==3
    assert result['claims']['one']['multiplicity']['threshold']==.05/3
    assert result['claims']['failed']['raw_p'] is None and not result['claims']['failed']['statistical_pass']
    with pytest.raises(ValueError):family([packet,bad,unrun],{'one':outcome})
    with pytest.raises(ValueError):family([packet],{'one':{'status':'RUNNING'}})
    assert family([],{})['selected_count']==0


def test_unit_and_row_order_do_not_change_results():
    packet,outcome=fixture()
    first=evaluate(packet,outcome['rows'],outcome['assigned_targets'])
    second=evaluate(packet,list(reversed(outcome['rows'])),dict(reversed(list(outcome['assigned_targets'].items()))))
    assert first==second
