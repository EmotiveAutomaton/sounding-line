"""The same prospective target in trained log and matched structured evidence views.

DESIGN CHECK: C01/C05/C08/X02/X06/X08; LESSONS 3--5.
NULL: future labels, hidden clock in artifact-only evidence, or a different query
between views invalidates the comparison. ALTERNATIVE: structured artifact/process
conditions share the same offered continuation strings and source target; raw logs
remain a separate rendering diagnostic. One call, no earlier artifacts and no
outcome supplied. These observations do not grant broad generation admission.
"""
from runners.stage9.common import canonical,digest
from runners.stage9.rollout_operations import public_input
from runners.stage9.artifact_view import support,validate_work

RENDERINGS={'genuine_choice':'raw_process_record',
            'process_choice':'structured_process_record',
            'artifact_choice':'structured_artifact'}


def choice_input(case,operation):
    if operation not in RENDERINGS:raise ValueError('undeclared prospective choice rendering')
    if operation=='genuine_choice':
        world=case['source_worlds'][0]
        return public_input(world,world['trajectory']['steps'][:case['requested_boundary']],offered=True)
    view='artifact' if operation=='artifact_choice' else 'process_record'
    current=case['views'][view]['current'];validate_work(current,view)
    actions=support(current,view)
    prefix=('Predict this maker\'s next action from the current work and its original task context. '
        'Choose one offered action identifier or stop.\nCurrent work:\n'+canonical(current)+'\nNext action:')
    return {'prefix':prefix,'options':{key:' '+key for key in actions}}


def evaluate_unit(case,operation,call):
    evidence=choice_input(case,operation)
    if case['target'] not in evidence['options']:raise ValueError('actual next target missing from offered support')
    result=call(evidence,{'operation':'choice'},'prospective-choice')
    return {'call':result,'input_sha256':digest(evidence),'target':case['target'],
        'rendering':RENDERINGS[operation],'earlier_work_dose':0,
        'scope':'one prospective choice; structured views share continuations, raw trained-log rendering is separate'}
