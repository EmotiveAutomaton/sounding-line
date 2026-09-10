"""Evaluator-only actual action execution and explicitly assisted rollout.

DESIGN CHECK: C01/C02/C06/C08/X08/X11/X12; LESSONS 3--5 and CONTROLS read.
NULL: fluent prose, wrong clocks, illegal or repeated actions and invented outcomes
are retained failures; early stopping is reported separately, never called a long
successful rollout. ALTERNATIVE: the existing constructor's own actions replay
exactly. Supplying outcomes can repair outcome production only; genuine-state resets
cannot be credited as unaided action competence. No proposed Python is executed.
Bands: valid observed execution, invalid response/action/outcome, or unrealized
matched-state/reset condition, each recorded separately on every assigned unit.
"""
import copy

from runners.stage8.reader import logfmt as LF
from runners.stage9.common import canonical,digest,distribution
from runners.stage9.construction import LAW,Replay,rendered_prefix
from runners.stage9.artifact_preparation import evidence as artifact_evidence

HORIZONS=(1,4,8,16)
MODES=('offered','environment_outcome','self_outcome')


def state_identity(replay):
    """Private exact state matching, including clock and previous-action effects."""
    state=copy.deepcopy(replay.snapshot())
    state['pending']=sorted(state['pending'],key=LAW.action_id)
    state['subjective_action_space']=sorted(state['subjective_action_space'])
    return digest({'state':state,'clock':len(replay.steps),'last_type':replay.last_type,
        'goal_name':replay.goal_name,'goal_last':replay.goal_last,'done':sorted(replay.done),
        'inventory':sorted(replay.inventory,key=LAW.action_id)})


def public_input(world,steps,view='process_record',offered=False):
    """No state, inventory membership, future change or truth crosses the boundary."""
    if view=='process_record':
        prefix=rendered_prefix(world,steps)
    elif view=='artifact':
        visible=artifact_evidence(world,steps,'artifact')['current']
        prefix=('Current artifact and its original commission:\n'+canonical(visible)+
            '\nName one next action using: NN TYPE SECTION SLOT [done|failed], or NN stop.\n'+
            'TYPE is write, revise, check, consult, cite, restructure, probe or fix.\n'+
            'The action number for this interaction is '+str(len(steps))+'.\n')
    else:
        raise ValueError('undeclared rollout evidence view')
    options={}
    if offered:
        # Use the same broad visible support in every route; no hidden inventory
        # mask and no externally supplied objective outcome in these continuations.
        from runners.stage9.artifact_view import support
        visible=artifact_evidence(world,steps,'process_record')['current']
        for aid in support(visible,'process_record'):
            options[aid]=LF.stop_line(len(steps)) if aid=='stop' else LF.event_line(len(steps),*aid.split(':'))
    return {'prefix':prefix,'options':options}


def parse_action(text,clock):
    lines=[line for line in text.splitlines() if line.strip()]
    if not lines:
        return None,'empty response'
    event=LF.parse_line(lines[0])
    if event is None:
        return None,'first nonempty line is not a supported action'
    if event['i']!=clock:
        return None,'action clock differs from actual interaction state'
    return event,None


def execute_action(replay,result,mode,options):
    if mode not in MODES:raise ValueError('undeclared action assistance')
    before=state_identity(replay)
    outcome={'valid_execution':bool(result.get('accepted')),'legal':False,'stopped':False,
        'state_before':before,'state_after':before,'actual_event':None,'claimed_outcome':None}
    if not result.get('accepted'):
        return outcome|{'failure':'invalid reader call'}
    prediction=result['prediction']
    if mode=='offered':
        probs=distribution(prediction['probs'])
        if set(probs)!=set(options):
            raise ValueError('offered prediction support differs from actual public options')
        # Canonical tie-breaking is part of this assisted package, not model certainty.
        aid=min(probs,key=lambda k:(-probs[k],k))
        event={'i':len(replay.steps),'stop':True} if aid=='stop' else dict(zip(('type','section','slot'),aid.split(':')))|{'i':len(replay.steps)}
        error=None
    else:
        event,error=parse_action(prediction['text'],len(replay.steps))
    if error:return outcome|{'failure':error}
    if event.get('stop'):
        return outcome|{'legal':True,'stopped':True,'failure':None}
    claimed=event.get('outcome')
    outcome['claimed_outcome']=claimed
    if mode=='self_outcome' and claimed not in ('done','failed'):
        return outcome|{'failure':'self-produced action omits a supported outcome'}
    try:
        actual=replay.apply(event,verify_outcome=mode=='self_outcome')
    except ValueError as exc:
        # Replay's refusal occurs before mutation; a failed proposal is still an attempt.
        if state_identity(replay)!=before:raise ValueError('rejected action mutated state') from exc
        return outcome|{'failure':str(exc)}
    return outcome|{'legal':True,'state_after':state_identity(replay),'actual_event':actual,
        'supplied_outcome':mode!='self_outcome','failure':None}


def rollout(world,call,*,mode,horizon=16,reset_every=0,view='process_record',seed=990091):
    """call receives public evidence only. Evaluator truths never enter its arguments.

    A completed trajectory supplies all nested 1/4/8/16 horizon summaries without
    repeating inference. Per-call persistence belongs to the actual queue handler.
    """
    if mode not in MODES or type(horizon) is not int or not 1<=horizon<=16 or reset_every not in (0,4):
        raise ValueError('undeclared rollout mode, horizon or reset interval')
    replay=Replay(world,extend_visible=True);attempts=[];resets=[];terminal=False;failure=None;realized=True
    for index in range(horizon):
        if reset_every and index and index%reset_every==0:
            genuine=world['trajectory']['steps']
            if index>len(genuine):
                realized=False;failure='genuine reset state unavailable at declared boundary';break
            previous=state_identity(replay)
            replay=Replay(world,genuine[:index],extend_visible=True)
            resets.append({'at_interaction':index,'replaced_state':previous,'genuine_state':state_identity(replay),
                           'genuine_prefix_sha256':digest(genuine[:index])})
        evidence=public_input(world,replay.steps,view,offered=mode=='offered')
        arguments={'operation':'choice' if mode=='offered' else 'generate'}
        if mode!='offered':arguments.update(max_new_tokens=32,seed=seed+index)
        result=call(evidence,arguments,index)
        action=execute_action(replay,result,mode,evidence['options'])
        attempts.append({'interaction':index,'evidence_sha256':digest(evidence),'call':result,**action})
        if not action['legal']:
            failure=action['failure'];break
        if action['stopped']:
            terminal=True;break
    summaries={}
    for requested in HORIZONS:
        if requested>horizon:continue
        prefix=attempts[:requested]
        summaries[str(requested)]={'attempted_interactions':len(prefix),
            'legal_interactions':sum(r['legal'] for r in prefix),'stopped':any(r['stopped'] for r in prefix),
            'reached_action_horizon':sum(r['actual_event'] is not None for r in prefix)==requested,
            'all_observed_actions_legal':bool(prefix) and all(r['legal'] for r in prefix),
            'reset_boundaries':[r['at_interaction'] for r in resets if r['at_interaction']<requested],
            'reset_realized':realized or len(prefix)>=requested}
    return {'mode':mode,'view':view,'requested_horizon':horizon,'reset_every':reset_every,
        'assistance':{'offered_actions':mode=='offered','environment_outcomes':mode!='self_outcome',
                      'genuine_state_reset_every':reset_every},'attempts':attempts,'resets':resets,
        'horizons':summaries,'realized':realized,'stopped':terminal,'failure':failure,
        'final_state':state_identity(replay),'events':replay.steps,'extensions':replay.extensions,
        'scope':'local stepwise interaction; self_outcome is not the historical uninterrupted full-log comparator'}


def matched_altered_prefix(world,boundary):
    """A changed legal history must leave the full executed state unchanged."""
    genuine=world['trajectory']['steps'][:boundary]
    if len(genuine)!=boundary or boundary<3:
        return {'realized':False,'reason':'insufficient genuine prefix for a state-matched alteration'}
    original=Replay(world,genuine);wanted=state_identity(original)
    # Preserve the last event explicitly, then check all other operative state.
    for left in range(boundary-2):
        for right in range(left+1,boundary-1):
            altered=copy.deepcopy(genuine);altered[left],altered[right]=altered[right],altered[left]
            for i,event in enumerate(altered):event['i']=i
            try:other=Replay(world,altered)
            except ValueError:continue
            if state_identity(other)==wanted and digest(other.steps)!=digest(original.steps):
                return {'realized':True,'genuine':original.steps,'altered':other.steps,
                        'state_sha256':wanted,'matching':'exact private operative state, action clock and previous action'}
    return {'realized':False,'reason':'no bounded commuting alteration preserves the full operative state'}
