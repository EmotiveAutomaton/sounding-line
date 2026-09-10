"""Supplied-rule finite execution questions over the existing constructor subset.

DESIGN CHECK: C04/I05/I06/X08/X10; LESSONS 3--5, CONTROLS 6.
NULL: a constant answer misses the realized longer distinction; arbitrary histories
cannot count as equivalent. ALTERNATIVE: the compact declared rules agree with the
independently constructed transition graph on every bounded sequence before model
queries are admitted. Fixed probes test compression and longer distinction; they
are not an exhaustive learned-language boundary or a reproduction of Vafa's models.
Truth/transition-graph state identifiers stay evaluator-side. This is explicitly
supplied objective state/rules, never an artifact-only or stochastic-policy claim.
"""
import copy
import itertools
from runners.stage9.automata import accepts
from runners.stage9.common import canonical,digest
from runners.stage9.construction import LAW

CONDITIONS=('distinction_left','distinction_right','compression_left','compression_right')


def projection(case,condition):
    if condition not in CONDITIONS:raise ValueError('unknown finite condition')
    kind,side=condition.split('_')
    world=case['changed_world'] if condition=='distinction_right' else case['world']
    actions={LAW.action_id(a):{'requires':list(a['requires'])} for a in case['actions']}
    history=[{k:e[k] for k in ('type','section','slot','outcome')} for e in case[kind][side+'_prefix']]
    events=[]
    for at,change in world['trajectory']['changes']:
        if change!='library_arrives':raise ValueError('compact finite language only implements the reviewed library-arrival intervention')
        events.append({'after_action':at,'library_available':True})
    return {'version':'s9-three-action-execution-v1','actions':actions,
        'initial_tools':copy.deepcopy(world['state']['external_context']['tools']),
        'context_events':events,'observed_history':history,'additional_action_horizon':4}


def execute_rules(rules,sequence):
    """Independent compact execution, validated against the original Replay graph."""
    tools=dict(rules['initial_tools']);completed=set();clock=0;stopped=False
    def arrival():
        for event in rules['context_events']:
            if event['after_action']==clock:tools['library']=event['library_available']
    def apply(token):
        nonlocal clock,stopped
        if stopped:return False
        if token=='stop':stopped=True;return True
        try:aid,outcome=token.rsplit(':',1)
        except ValueError:return False
        if aid not in rules['actions'] or aid in completed:return False
        actual='done' if all(tools.get(k,False) for k in rules['actions'][aid]['requires']) else 'failed'
        if outcome!=actual:return False
        if actual=='done':completed.add(aid)
        clock+=1;arrival();return True
    arrival()
    for event in rules['observed_history']:
        if not apply(LAW.action_id(event)+':'+event['outcome']):
            raise ValueError('declared initial history is not executable')
    for index,token in enumerate(sequence):
        if index>=rules['additional_action_horizon'] or not apply(token):return False
    return True


def validate_projection(case):
    """Exhaust all words through four symbols, including empty and after-STOP cases."""
    checked=0
    for condition in CONDITIONS:
        kind,side=condition.split('_');graph=case[kind][side];rules=projection(case,condition)
        for length in range(5):
            for sequence in itertools.product(graph['alphabet'],repeat=length):
                if execute_rules(rules,sequence)!=accepts(graph,graph['initial'],sequence):
                    raise ValueError('compact objective rules differ from the actual constructor graph')
                checked+=1
    return {'all_bounded_sequences_match':True,'sequences_checked':checked,'maximum_length':4,
            'projection_sha256':digest({c:projection(case,c) for c in CONDITIONS})}


def query_plan(case):
    alphabet=case['distinction']['left']['alphabet']
    separator=case['distinction']['separator']['suffix']
    if len(separator)<2 or not case['distinction']['one_step_support_identical']:
        raise ValueError('finite task lacks a realized longer distinction')
    words=[[token] for token in alphabet]
    words.extend([separator,['stop',alphabet[1]],[alphabet[2],alphabet[2]],
                  [alphabet[2],alphabet[4],alphabet[6]],
                  [alphabet[2],alphabet[4],alphabet[6],'stop']])
    unique=[]
    for word in words:
        if word not in unique:unique.append(word)
    records=[]
    for condition in CONDITIONS:
        kind,side=condition.split('_');graph=case[kind][side]
        for index,word in enumerate(unique):
            truth=accepts(graph,graph['initial'],word)
            records.append({'query':condition+'-'+str(index),'condition':condition,'sequence':word,'truth':'yes' if truth else 'no'})
    left=case['distinction']['left'];right=case['distinction']['right']
    if accepts(left,left['initial'],separator)==accepts(right,right['initial'],separator):
        raise ValueError('declared separating sequence does not separate')
    return records


def reader_input(case,query):
    rules=projection(case,query['condition'])
    prefix=('Decide whether the proposed sequence is an executable continuation under these supplied rules.\n'
        'The keys in actions are the entire declared action alphabet. An action cannot repeat after it finishes with done. '
        'If every required tool is available its outcome must be done; otherwise its outcome must be failed. '
        'A failed action can repeat. Every action advances the clock by one. Context events apply at the stated action clock. '
        'stop is legal and ends execution; no symbol may follow it. The additional horizon counts proposed symbols, including stop. '
        'First execute the observed history, then the proposed sequence. Answer yes or no.\n'
        'Rules and observed history: '+canonical(rules)+'\nProposed sequence: '+canonical(query['sequence'])+'\nAnswer:')
    return {'prefix':prefix,'options':{'yes':' yes','no':' no'}}


def projected_case(world):
    from runners.stage9.finite_world import from_world
    finite=from_world(world)
    validation=validate_projection(finite)
    queries=query_plan(finite)
    inputs=[reader_input(finite,query) for query in queries]
    # Identity is what the reader receives and the operation's actual truth, not
    # the private source world's name, topic, maker or seed.
    identity=digest([{'input':evidence,'truth':query['truth']} for evidence,query in zip(inputs,queries)])
    return finite,validation,queries,inputs,identity


def group_cases(cases):
    representatives=[];groups={}
    for case in cases:
        identity=projected_case(case['source_worlds'][0])[-1]
        if identity not in groups:
            representatives.append(case)
            groups[identity]={'representative':case['unit'],'source_units':[], 'source_domains':[]}
        groups[identity]['source_units'].append(case['unit'])
        groups[identity]['source_domains'].append(case['source_worlds'][0]['domain'])
    return representatives,groups


def evaluate_unit(world,call):
    """Freeze all queries and their answers before any actual reader call."""
    finite,validation,queries,inputs,identity=projected_case(world)
    predictions=[]
    for query,evidence in zip(queries,inputs):
        result=call(evidence,{'operation':'choice'},query['query'])
        predictions.append({'query':query,'input_sha256':digest(evidence),'call':result})
    return {'projection_identity':identity,'projection_validation':validation,
        'queries':predictions,'query_plan_sha256':digest(queries),
        'scope':'bounded supplied-rule operation diagnostic; source aliases are not independent neural units; no learned-language boundary claim'}
