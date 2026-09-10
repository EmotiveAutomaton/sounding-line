import copy
import pytest
from runners.stage9.common import digest
from runners.stage9.construction import register
from runners.stage9.finite_queries import projected_case,evaluate_unit
from runners.stage9.operation_analysis import finite_profile,prefix_profile,rollout_profile,ROLLOUTS
from runners.stage9.neural_operations import prefix_unit,OPERATIONS
from runners.stage9.recipes import POP,sampled_world
from runners.stage9.rollout_operations import rollout,matched_altered_prefix
from runners.stage8.reader import logfmt as LF


def worlds(count=8):
    register()
    return [sampled_world(POP.pop_lid(i,d,9994000),'both') for d in POP.DOMAINS for i in range(count)]


def test_exact_longer_distinction_beats_constant_and_invalid_readers():
    world=worlds(1)[0]
    finite,check,queries,inputs,key=projected_case(world)
    answers={digest(e):q['truth'] for e,q in zip(inputs,queries)}
    def call(evidence,args,index):
        answer=answers[digest(evidence)]
        return {'accepted':True,'prediction':{'probs':{v:float(v==answer) for v in ('yes','no')}}}
    row={'unit':'known-world','result':evaluate_unit(world,call)}
    result=finite_profile([row]);assert result['exact_supported_battery_pass'] and result['longer_distinction']['rate']==1
    constant=copy.deepcopy(row)
    for q in constant['result']['queries']:q['call']['prediction']['probs']={'yes':1.,'no':0.}
    result=finite_profile([constant]);assert not result['exact_supported_battery_pass'] and result['longer_distinction']['rate']==0
    for q in constant['result']['queries']:q['call']={'accepted':False}
    assert not finite_profile([constant])['exact_supported_battery_pass']
    with pytest.raises(ValueError,match='representative'):finite_profile([row,row])


def test_matched_prefix_known_identity_and_missing_generated_state():
    world=next(w for w in worlds(16) if matched_altered_prefix(w,3)['realized'])
    def call(evidence,args,index):
        if args['operation']=='choice':
            from runners.stage9.construction import Replay
            p=Replay(world,world['trajectory']['steps'][:3]).probabilities()
            return {'accepted':True,'prediction':{'probs':{k:p.get(k,0.) for k in evidence['options']}},
                'copied_sources':{'evidence_sha256':digest(evidence)}}
        event=world['trajectory']['steps'][int(index.split('-')[-1])]
        return {'accepted':True,'prediction':{'text':LF.event_line(event['i'],event['type'],event['section'],event['slot'],event['outcome'])}}
    case={'unit':'known','private_factors':{'domain':world['domain']},'source_worlds':[world]}
    row={'unit':'known','result':prefix_unit(world,call)}
    assert row['result']['matched_generated_state']
    result=prefix_profile([case],[row],draws=100)
    for name in ('altered','generated'):
        assert result['domains'][world['domain']]['contrasts'][name]['contrast']['mean']==0
    row['result']['matched_generated_state']=False;del row['result']['predictions']['generated']
    result=prefix_profile([case],[row],draws=100)
    assert result['domains'][world['domain']]['contrasts']['generated']['disposition']=='NOT RUN WITH REASON'
    assert result['domains'][world['domain']]['contrasts']['altered']['contrast']['mean']==0


def test_early_stop_is_not_sustained_success_and_aliases_do_not_inflate_n():
    world=worlds(1)[0]
    def stop(evidence,args,index):
        if args['operation']=='choice':return {'accepted':True,'prediction':{'probs':{k:float(k=='stop') for k in evidence['options']}}}
        return {'accepted':True,'prediction':{'text':'00 stop'}}
    result_by_operation={k:rollout(world,stop,**OPERATIONS[k]) for k in ROLLOUTS}
    cases=[{'unit':str(i),'private_factors':{'domain':world['domain']}} for i in range(2)]
    rows={op:[{'unit':c['unit'],'result':copy.deepcopy(result_by_operation[op])} for c in cases] for op in ROLLOUTS}
    result=rollout_profile(cases,rows,draws=100)['domains'][world['domain']]
    for condition in result['conditions'].values():
        assert condition['distinct_initial_public_questions']==1
        assert condition['stop_rate']['successes']==2
        assert condition['horizons']['16']['reached_action_horizon']['successes']==0
    for contrast in result['contrasts'].values():
        for row in contrast.values():assert row['contrast']['mean']==0 and row['contrast']['ci'] is None
    del rows['self_outcome']
    with pytest.raises(ValueError,match='all five'):rollout_profile(cases,rows,draws=100)
