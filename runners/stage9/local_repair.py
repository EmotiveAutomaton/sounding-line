"""One requested mark repair and prospective execution on the existing constructor.

DESIGN CHECK: C03/X02/X08/X09/X11; LESSONS 3--5, CONTROLS 6.
NULL: fluent stories, wrong actions, collateral extra marks and unsupported outcomes
remain failed attempts. ALTERNATIVE: the exact executor realizes the requested
visible mark when fixable and preserves all other marks. Predict an unseen proposed
edit's execution before its outcome is shown; then independently propose the repair.
The task is the constructor's symbolic operation marks, not natural-text quality or
human motive truth. Only the ordinary initial context and selected artifact/record
view are exposed. Actual tools at the hidden producer clock stay evaluator-side.
Consequences can therefore differ from an initial-header availability heuristic.
No capability gate or scientific result is computed by this execution module alone.
"""
import copy
from runners.stage9.artifact_preparation import work
from runners.stage9.artifact_view import all_header_actions
from runners.stage9.common import canonical,digest
from runners.stage9.construction import Replay
from runners.stage9.rollout_operations import execute_action,parse_action

LABELS=('done','failed','illegal','stopped')


def pick(values,identity,purpose):
    return values[int(digest({'task':identity,'purpose':purpose})[:16],16)%len(values)]


def task_case(case,view):
    world=case['source_worlds'][0];cut=case['requested_boundary']
    events=world['trajectory']['steps'][:cut]
    visible=work(world,events,view,observed_stop=None)
    # Fix the same requested edit and consequence question across evidence views.
    # Extra process access must not silently select a different editing task.
    visible_id=digest(work(world,events,'artifact'))
    candidates=sorted(set(all_header_actions(visible['context']))-set(visible['marks']))
    if not candidates:
        return {'realized':False,'reason':'no remaining visible mark request','view':view}
    # The request is fixed from permitted information, before any reader response.
    # Do not select it by fixability or by the model's preferred move.
    goal=pick(candidates,visible_id,'requested-new-mark')
    proposed=pick(['stop',*sorted(all_header_actions(visible['context']))],visible_id,'unseen-proposed-edit')
    return {'realized':True,'view':view,'current':visible,'requested_mark':goal,
        'proposed_edit':proposed,'public_task_sha256':digest({'view':view,'current':visible,'goal':goal,'proposed':proposed}),
        'world':world,'events':events,'unit':case['unit'],
        'scope':'symbolic local editing request; preserve all other marks, with initial context only'}


def input_for(task,operation):
    if not task['realized'] or operation not in ('consequence','repair'):
        raise ValueError('unrealized or unknown local operation')
    prefix=('Current constructed work and its original context:\n'+canonical(task['current'])+
        '\nEditing request: add the mark '+task['requested_mark']+
        '. Preserve every existing mark and add no other mark. A mark names TYPE:SECTION:SLOT.\n'
        'Operations are write, revise, check, consult, cite, restructure, probe, fix, and stop. '
        'cite requires library; consult requires source_access; the others require no tool. '
        'An unavailable tool produces failed and adds no mark. A completed operation adds its mark; '
        'repeating a completed operation or naming an absent section/slot is illegal. '
        'Some original-context tools may have changed since the work began.\n')
    if operation=='consequence':
        prefix+=('Before executing anything, predict the outcome of this proposed unseen edit: '+task['proposed_edit']+
                 '. Answer done, failed, illegal, or stopped.\nOutcome:')
        return {'prefix':prefix,'options':{label:' '+label for label in LABELS}}
    prefix+=('Propose one action to satisfy the editing request. Use exactly one line: '
             '00 TYPE SECTION SLOT [done|failed], or 00 stop. '
             '00 numbers this new interaction, not the unobserved producer history.\nAction:\n')
    return {'prefix':prefix,'options':{}}


def consequence(task):
    if task['proposed_edit']=='stop':return 'stopped'
    replay=Replay(task['world'],task['events'],extend_visible=True)
    event=dict(zip(('type','section','slot'),task['proposed_edit'].split(':')))
    try:return replay.apply(event,verify_outcome=False)['outcome']
    except ValueError:return 'illegal'


def repair_truth(task,prediction):
    replay=Replay(task['world'],task['events'],extend_visible=True)
    wanted=dict(zip(('type','section','slot'),task['requested_mark'].split(':')))
    probe=Replay(task['world'],task['events'],extend_visible=True)
    try:fixable=probe.apply(wanted,verify_outcome=False)['outcome']=='done'
    except ValueError:fixable=False
    before=sorted(replay.done);converted=copy.deepcopy(prediction)
    # The external repair API owns a fresh interaction clock. Translate it only
    # after exact parsing; do not reveal or require the hidden producer clock.
    if prediction.get('accepted'):
        event,error=parse_action(prediction['prediction']['text'],0)
        if error:
            return {'valid_execution':True,'legal':False,'fixable':fixable,'goal_improving':False,
                'collateral_damage':False,'failure':error,'marks_before':before,'marks_after':before}
        from runners.stage8.reader import logfmt as LF
        converted['prediction']['text']=(LF.stop_line(len(replay.steps)) if event.get('stop') else
            LF.event_line(len(replay.steps),event['type'],event['section'],event['slot'],event.get('outcome')))
    action=execute_action(replay,converted,'environment_outcome',{})
    added=set(replay.done)-set(before)
    return {**action,'fixable':fixable,'goal_improving':task['requested_mark'] in added,
        'collateral_damage':bool(added-{task['requested_mark']}) or not set(before)<=replay.done,
        'marks_before':before,'marks_after':sorted(replay.done),
        'assistance':'executor supplies objective outcome only; it does not choose or legalize the proposed action'}


def evaluate_unit(case,view,call):
    task=task_case(case,view)
    if not task['realized']:return task
    prospective=call(input_for(task,'consequence'),{'operation':'choice'},'prospective')
    repair=call(input_for(task,'repair'),{'operation':'generate','max_new_tokens':32,
        'seed':int(digest({'local_repair':task['public_task_sha256']})[:8],16)},'repair')
    # No true consequence or repaired state is supplied between the two calls.
    return {'realized':True,'view':view,'public_task_sha256':task['public_task_sha256'],
        'requested_mark':task['requested_mark'],'proposed_edit':task['proposed_edit'],
        'consequence_truth':consequence(task),'prospective_call':prospective,'repair_call':repair,
        'repair_execution':repair_truth(task,repair),'scope':task['scope']}
