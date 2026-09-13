"""Pinned second local model on the unchanged human comparison population.

DESIGN CHECK: LESSONS2-5; Stage10 section9. NULL/ALTERNATIVE retain the same
tasks, training memory, R0/R2 and development-selected structured rival. No
download, cloud call, model fallback or evaluation-guided selection. A small
discarded source pilot must admit each route; malformed predictions remain.
"""
import argparse
from contextlib import contextmanager
from pathlib import Path
import time
from . import ollama, human_routes, human_memory_routes, deliberation
from .contracts import digest,parse_forecast
from .reader import from_record
from .queue import read,status
from .revision_bank import checked,finish,device,sha

MODEL='llama3.1:8b'
MODEL_DIGEST='46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e'


@contextmanager
def profile():
    old=(ollama.MODEL,ollama.MODEL_DIGEST)
    ollama.MODEL,ollama.MODEL_DIGEST=MODEL,MODEL_DIGEST
    try:yield
    finally:ollama.MODEL,ollama.MODEL_DIGEST=old


def sources():
    return {**human_memory_routes.identity(),**deliberation.identity(),
            'runners/stage10/local_comparator.py':sha(Path(__file__)),
            'runners/stage10/revision_bank.py':sha(Path(__file__).with_name('revision_bank.py'))}


def select(prepared,pilot,memory,rival,output):
    from .human_effort_evaluation import metadata
    frozen=read(prepared/'FROZEN.json');discarded=read(pilot/'FROZEN.json')
    if discarded['scope']!='discarded legacy pilot writer, excluded from the scientific cohort':raise ValueError('discarded human pilot required')
    trained,answers,learned=human_memory_routes.inputs(prepared,memory)
    selected=read(rival/'FROZEN.json');arm=selected['fit']['chosen']
    if arm not in {'R3','R4-grounded'}:raise ValueError('undeclared selected rival')
    # The prior complete, development-only choice and its exact sources bind.
    for p,h in selected['input_files'].items():
        if sha(Path(p))!=h:raise ValueError('original development selection input changed')
    evaluation=read(prepared/'evaluation-public.json');pilot_tasks=read(pilot/'development-public.json')
    if digest(evaluation)!=frozen['public_sha256']['evaluation'] or digest(pilot_tasks)!=discarded['public_sha256']['development']:raise ValueError('public cohort differs')
    identities=metadata(prepared,'evaluation',frozen)
    if {r['task_id'] for r in pilot_tasks['tasks']} & {r['task_id'] for r in evaluation['tasks']}:raise ValueError('pilot/evaluation overlap')
    # Reuse the entire original population. No outcome- or validity-based subset.
    with profile():
        for row in [*pilot_tasks['tasks'],*evaluation['tasks']]:
            task=from_record(row);ollama.request_for(task,context_tokens=16384)
            if arm=='R4-grounded':human_memory_routes.representation_for(task,trained,answers,learned,arm)
    manifest={'sources':sources(),'prepared':prepared.as_posix(),'memory':memory.as_posix(),
        'training_public_sha256':digest(trained),'training_answers_sha256':digest(answers),'learned_sha256':digest(learned),
        'model':MODEL,'model_digest':MODEL_DIGEST,'arms':list(dict.fromkeys(['R0','R2','R3','R1-memory',arm])),
        'rival_receipt_sha256':sha(rival/'FROZEN.json'),'rival_rule':selected['fit']['rule'],
        'pilot_sha256':digest(pilot_tasks),'evaluation_sha256':digest(evaluation),
        'scope':'selected second-local-model descriptive comparison; unchanged original held-out-writer population'}
    output.mkdir(parents=True,exist_ok=False)
    for name,value in [('SELECTION.json',manifest),('pilot-public.json',pilot_tasks),('evaluation-public.json',evaluation),('evaluation-identity.json',identities)]:ollama.write_new(output/name,value)
    return finish(output,digest(manifest))


def replay_raw(root):
    for attempt_path in root.rglob('ATTEMPT.json'):
        attempt=read(attempt_path);raw=read(attempt_path.with_name('RAW.json'));request=read(attempt_path.with_name('REQUEST.json'))
        if digest(raw)!=attempt['raw_sha256'] or request['request']['model']!=MODEL:raise ValueError('raw second-model identity differs')
        if attempt['cost']!={k:raw.get(k) for k in attempt['cost']}:raise ValueError('raw cost differs')
        if request['binding']!=digest({'request':request['request'],'model_digest':MODEL_DIGEST}):raise ValueError('raw model digest differs')


def run(selection,output,phase,admission=None):
    if phase not in {'pilot','evaluation'}:raise ValueError('undeclared comparator phase')
    checked(selection);manifest=read(selection/'SELECTION.json')
    if manifest['sources']!=sources() or (manifest['model'],manifest['model_digest'])!=(MODEL,MODEL_DIGEST):raise ValueError('second-model source changed')
    if phase=='evaluation':
        receipt=checked(admission)
        if receipt['selection_binding']!=digest(manifest) or receipt['admitted'] is not True:raise ValueError('second-model literal admission required')
    training,answers,learned=human_memory_routes.inputs(Path(manifest['prepared']),Path(manifest['memory']))
    if [digest(training),digest(answers),digest(learned)]!=[manifest['training_public_sha256'],manifest['training_answers_sha256'],manifest['learned_sha256']]:raise ValueError('selected memory changed')
    public=read(selection/(phase+'-public.json'))
    if digest(public)!=manifest[phase+'_sha256']:raise ValueError('selected tasks changed')
    binding=digest([manifest,phase]);replay=(output/'COMPLETE.json').exists();rows=[]
    if replay:
        old=checked(output)
        if old['binding']!=binding:raise ValueError('completed model binding differs')
    with profile(),device(output,replay):
        for row in public['tasks']:
            task=from_record(row)
            for arm in manifest['arms']:
                directory=output/'routes'/task.task_id/arm
                if replay and not directory.exists():raise ValueError('missing completed route')
                if not replay:status(output/'STATUS.json',{'at':ollama.now(),'phase':phase,'completed_routes':len(rows),'task':task.task_id,'arm':arm})
                if arm=='R0':result=ollama.call(task,directory,context_tokens=16384)
                elif arm=='R2':result=deliberation.route(task,directory)
                elif arm=='R3':result=human_routes.route(task,directory)
                else:result=human_memory_routes.route(task,directory,arm,training,answers,learned)
                rows.append({'task_id':task.task_id,'arm':arm,'result':result})
    replay_raw(output)
    roster={'phase':phase,'rows':rows}
    if (output/'ROSTER.json').exists():
        if read(output/'ROSTER.json')!=roster:raise ValueError('second-model roster differs')
    else:ollama.write_new(output/'ROSTER.json',roster)
    extra={}
    if phase=='pilot':extra={'admitted':all(any(r['arm']==a and r['result']['status']=='VALID' for r in rows) for a in manifest['arms']),
                              'selection_binding':digest(manifest),'criterion':'each route parses legally on at least one discarded task; no accuracy gate'}
    return finish(output,binding,extra)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','pilot','evaluation'])
    for key in ['prepared','pilot','memory','rival','selection','admission','output']:p.add_argument('--'+key,type=Path,required=key=='output')
    a=p.parse_args()
    try:
        if a.action=='select':select(a.prepared,a.pilot,a.memory,a.rival,a.output)
        else:run(a.selection,a.output,a.action,a.admission)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():ollama.write_new(a.output/'FAILED.json',{'at':ollama.now(),'error':repr(exc)})
        raise
