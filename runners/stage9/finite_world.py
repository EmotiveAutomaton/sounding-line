"""Bounded objective-execution language over the existing artifact constructor.

DESIGN CHECK: C04/I05. Restrict the query alphabet to three declared existing
inventory actions and STOP, with explicit objective outcomes and finite horizon.
Use the existing library-arrival intervention; no new maker dynamics. Equivalence
here concerns legal observable execution on this alphabet, not stochastic policies,
hidden purposes, global process recovery or historical artifact identification.
"""
import copy
from collections import deque

from runners.stage9.automata import validate,accepts,shortest_separator
from runners.stage9.common import digest
from runners.stage9.construction import Replay,LAW,register
from runners.stage9.recipes import sampled_world,POP


def token(action,outcome):
    return LAW.action_id(action)+':'+outcome


def alphabet_actions(world):
    library=[a for a in world['inventory'] if 'library' in a['requires']]
    others=[a for a in world['inventory'] if 'library' not in a['requires']]
    if not library or len(others)<2:
        raise ValueError('existing inventory cannot realize the finite objective subset')
    return [library[0],*others[:2]]


def graph(world,actions,initial_prefix=(),horizon=4,state_cap=10000):
    if not 1<=horizon<=16 or len(actions)!=3:
        raise ValueError('declared three-action finite language required')
    aids={LAW.action_id(a) for a in actions}
    if len(aids)!=3 or not aids<={LAW.action_id(a) for a in world['inventory']}:
        raise ValueError('query subset differs from existing inventory')
    alphabet=['stop']+[token(a,outcome) for a in actions for outcome in ('done','failed')]
    pending=deque([tuple(copy.deepcopy(initial_prefix))]);states={};histories={};accepting=[]
    initial_clock=len(initial_prefix)
    def state_key(replay):
        return digest({'snapshot':replay.snapshot(),'last_type':replay.last_type,
                       'step':len(replay.steps),'done':sorted(replay.done),'initial_clock':initial_clock})[:24]
    first=Replay(world,initial_prefix);initial=state_key(first)
    while pending:
        prefix=pending.popleft();replay=Replay(world,prefix);key=state_key(replay)
        if key in states:continue
        if len(states)>=state_cap:raise ValueError('finite constructor state budget exhausted')
        states[key]={};histories[key]=list(prefix);accepting.append(key)
        if len(prefix)-initial_clock>=horizon:continue
        states[key]['stop']='TERMINATED'
        legal={LAW.action_id(a):a for a in replay.legal_actions()}
        for action in actions:
            aid=LAW.action_id(action)
            if aid not in legal or aid not in {LAW.action_id(a) for a in replay.pending}:continue
            event=legal[aid]|{'i':len(prefix)}
            child=Replay(world,prefix);actual=child.apply(event)
            destination=state_key(child);states[key][token(action,actual['outcome'])]=destination
            pending.append(tuple(list(prefix)+[actual]))
    states['TERMINATED']={};accepting.append('TERMINATED')
    result={'alphabet':alphabet,'transitions':states,'initial':initial,'accepting':accepting}
    validate(result)
    return result,{'horizon':horizon,'state_count':len(states),'initial_prefix_sha256':digest(initial_prefix),
                   'scope':'exact bounded objective execution, three original inventory actions plus STOP',
                   'private_history_by_state':histories}


def merge(left,right):
    if left['alphabet']!=right['alphabet']:raise ValueError('language supports differ')
    transitions={};accepting=[]
    for prefix,g in [('L:',left),('R:',right)]:
        transitions.update({prefix+k:{t:prefix+v for t,v in row.items()} for k,row in g['transitions'].items()})
        accepting.extend(prefix+k for k in g['accepting'])
    result={'alphabet':left['alphabet'],'transitions':transitions,'accepting':accepting,'initial':'L:'+left['initial']}
    validate(result);return result,'L:'+left['initial'],'R:'+right['initial']


def case(index,domain,band=9970000):
    register();world=sampled_world(POP.pop_lid(index,domain,band),'both')
    return from_world(world)


def from_world(world):
    """Project an already assigned source world; do not draw a replacement unit."""
    actions=alphabet_actions(world)
    # Common known initial tool setting. Only the future library-arrival schedule
    # differs, and that intervention is already defined in the existing executor.
    world=copy.deepcopy(world)
    world['state']['external_context']['tools']['library']=False
    world['state']['belief_state']['believed_tools']['library']=False
    world['trajectory']['changes']=[]
    changed=copy.deepcopy(world);changed['trajectory']['changes']=[(1,'library_arrives')]
    left,lr=graph(world,actions);right,rr=graph(changed,actions)
    combined,a,b=merge(left,right);separator=shortest_separator(combined,a,b)
    one_step_equal=all(accepts(left,left['initial'],[t])==accepts(right,right['initial'],[t]) for t in left['alphabet'])
    if not one_step_equal or separator['equivalent'] or len(separator['suffix'])<2:
        raise ValueError('longer distinguishing continuation was not realized')
    # Two completed commuting operations reach the same objective execution state.
    ordinary=actions[1:]
    prefixes=[]
    for order in (ordinary,list(reversed(ordinary))):
        replay=Replay(world)
        for action in order:replay.apply(action,verify_outcome=False)
        prefixes.append(replay.steps)
    ga,ar=graph(world,actions,prefixes[0]);gb,br=graph(world,actions,prefixes[1])
    comp,ca,cb=merge(ga,gb);equivalence=shortest_separator(comp,ca,cb)
    if not equivalence['equivalent']:raise ValueError('proposed compression histories are not language-equivalent')
    return {'world':world,'changed_world':changed,'actions':actions,
            'distinction':{'left':left,'right':right,'left_prefix':[],'right_prefix':[],'separator':separator,
                           'one_step_support_identical':one_step_equal},
            'compression':{'left':ga,'right':gb,'left_prefix':prefixes[0],'right_prefix':prefixes[1],'equivalence':equivalence},
            'scope':'supplied finite objective rules and future context schedule; not artifact-only inference',
            'source_lineage':world['lid']}
