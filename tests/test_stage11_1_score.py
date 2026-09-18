"""Proper scores, nonempty utility and dependent weighting have known answers."""
from runners.stage11_1.score import finite,episode,summarize
from runners.stage11_1.models import FIELDS,ACTIONS
from runners.stage11_1.targets import project
from runners.stage11.run import fixture
from runners.stage11.replay import replay


def pair():
    lines=fixture();e=replay(lines)['events'][0];t=project(e,lines)
    row=dict(key='x',writer='w',session='s',prompt='p',target=t)
    f=dict(facts=[dict(slot=t['slot'],**{k:[float(x==t[k]) for x in labels] for k,labels in FIELDS.items()},
        span_ids=t['span_ids'],span_state=t['span_state']) for t in t['facts']],
        handling=[float(a==e['decision']) for a in ACTIONS],attributes=t['attributes'])
    return row,f


def test_score_direction_and_zero_support():
    assert finite([1,0],'a',('a','b'))['brier']==0
    assert finite([1,0],'b',('a','b'))['brier']==1
    assert finite([1,0],'b',('a','b'))['log_loss']=='infinite'


def test_oracle_unknown_and_invalid_yield():
    row,f=pair();oracle=summarize([episode(row,f)])
    assert oracle['useful_positive_per_episode']==2 and oracle['span_exact']==1
    assert all(x['brier']==0 for x in oracle['dimensions'].values())
    for fact in f['facts']:
        for k,labels in FIELDS.items():fact[k]=[float(x=='unknown') for x in labels]
        fact['span_ids']=[];fact['span_state']='unknown'
    unknown=summarize([episode(row,f)])
    assert unknown['useful_positive_per_episode']==0 and unknown['covered']==0
    assert all(r['raw_risk']==1 for r in unknown['operation_risk_at_fixed_coverage'])
    invalid=summarize([episode(row,None)])
    assert invalid['dimensions']['operation']['brier']==1 and invalid['invalid']==1


def test_writers_not_repeated_episodes_define_primary_mean():
    row,f=pair();a=episode(row,f);b=episode(dict(row,key='b',writer='other',session='other'),None)
    result=summarize([a,a,a,b])
    assert result['dimensions']['operation']['brier']==.5
    assert result['prompt_components']==1 and result['writers']==2
