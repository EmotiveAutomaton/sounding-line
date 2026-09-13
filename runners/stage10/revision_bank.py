"""Finite ScholaWrite six-strategy bank with literal admission and separate fit.

DESIGN CHECK: Stage 10 sections 7,9,10; LESSONS2-5. NULL and ALTERNATIVE keep
whole projects apart, exclude pilot boundaries in every partition, retain invalid
routes and all costs, and open only development answers for policy fitting.
Pilot admission concerns parse/transport, never prediction accuracy. Evaluation
labels are not loaded here. A complete replay executes no new model requests.
"""
import argparse
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
from pathlib import Path

from runners.stage9.process_identity import native_identity
from soundingline.gpulock import GPU_LOCK, acquire_gpu_lock, release_gpu_lock
from . import effort, ollama, revision_readers
from .contracts import digest
from .reader import from_record
from .queue import read, status

ARMS=['R0','R1','R2','R3','R4-opaque','R4-grounded']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    return {**revision_readers.identity(),'runners/stage10/revision_bank.py':sha(Path(__file__)),
            'runners/stage10/queue.py':sha(Path(__file__).with_name('queue.py'))}


def files(output):
    return {p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file() and p!=output/'COMPLETE.json'}


def finish(output,binding,extra=None):
    value={'status':'COMPLETE','binding':binding,'files':files(output),**(extra or {})}
    if (output/'COMPLETE.json').exists():
        if read(output/'COMPLETE.json')!=value:raise ValueError('completed revision bank changed')
    else:ollama.write_new(output/'COMPLETE.json',value)
    return value


def checked(output):
    value=read(output/'COMPLETE.json')
    if value.get('status')!='COMPLETE' or value['files']!=files(output):raise ValueError('revision bank inventory differs')
    return value


def select(prepared,output):
    frozen=read(prepared/'FROZEN.json'); lanes={};identities={}
    for lane in ['train','development','evaluation']:
        public=read(prepared/(lane+'-public.json'));identity=read(prepared/(lane+'-identity.json'))
        if digest(public)!=frozen['public_sha256'][lane] or digest(identity)!=frozen['identity_sha256'][lane]:raise ValueError('frozen revision source differs')
        lanes[lane]=public['tasks'];identities[lane]=identity['targets']
        if {r['task_id'] for r in lanes[lane]}!={r['task_id'] for r in identities[lane]}:raise ValueError('identity coverage differs')
    answers=read(prepared/'train-evaluator.json')
    if digest(answers)!=frozen['evaluator_sha256']['train']:raise ValueError('training answers differ')
    # Source preparation uses the same hash ordering in every fold. The first
    # boundary of EVERY project is excluded from science, including when that
    # project is development or evaluation in another fold.
    excluded=set();pilot=[]
    for lane in lanes:
        groups=defaultdict(list)
        for row in identities[lane]:groups[row['writer_component']].append(row['boundary'])
        for group,boundaries in groups.items():
            excluded.add(min(set(boundaries),key=lambda b:digest(['s10-schola-screen-v1',b])))
    training_ids={r['task_id'] for r in identities['train'] if r['boundary'] not in excluded}
    training=[r for r in lanes['train'] if r['task_id'] in training_ids]
    train_answers=[r for r in answers['targets'] if r['task_id'] in training_ids]
    readers=revision_readers.Readers(training,train_answers);rejections=[]
    selected={};selected_identity={}
    for lane in lanes:
        by_id={r['task_id']:r for r in lanes[lane]};groups=defaultdict(list)
        for row in identities[lane]:groups[row['boundary']].append(row)
        keep=[]
        for boundary,rows in groups.items():
            if boundary in excluded:
                if lane=='train':pilot.extend(by_id[r['task_id']] for r in rows)
                continue
            if lane!='train':
                try:
                    for r in rows:readers.preflight(from_record(by_id[r['task_id']]))
                except ValueError as exc:
                    rejections.append({'lane':lane,'boundary':boundary,'reason':str(exc)});continue
            keep.extend(rows)
        selected_identity[lane]=keep
        selected[lane]=[by_id[r['task_id']] for r in keep]
        if not keep:raise ValueError('required partition empty after common request admission')
    # One boundary's six target/view tasks is a discarded instrument sample.
    # Choose by source order, not by any forecast or target outcome.
    pilot=pilot[:6]
    for row in pilot:readers.preflight(from_record(row))
    binding=digest({'frozen':frozen,'sources':sources(),'readers':readers.sources})
    output.mkdir(parents=True,exist_ok=False)
    ollama.write_new(output/'SELECTION.json',{'binding':binding,'sources':sources(),'prepared':prepared.as_posix(),
        'frozen_sha256':digest(frozen),'reader_sources':readers.sources,'excluded_pilot_boundaries':sorted(excluded),
        'rejections':rejections,'selected':{k:len(v) for k,v in selected.items()},
        'scope':'whole-project descriptive screen; at most three central contrasts from original stage freeze'})
    for lane in selected:
        ollama.write_new(output/(lane+'-public.json'),{'tasks':selected[lane]})
        ollama.write_new(output/(lane+'-identity.json'),{'targets':selected_identity[lane]})
    ollama.write_new(output/'train-evaluator.json',{'targets':train_answers})
    ollama.write_new(output/'pilot-public.json',{'tasks':pilot})
    ollama.write_new(output/'LIBRARY.json',readers.library)
    return finish(output,binding)


def load(selection):
    checked(selection);record=read(selection/'SELECTION.json')
    if record['sources']!=sources():raise ValueError('selected reader sources changed')
    readers=revision_readers.Readers(read(selection/'train-public.json')['tasks'],read(selection/'train-evaluator.json')['targets'])
    if readers.sources!=record['reader_sources'] or readers.library!=read(selection/'LIBRARY.json'):raise ValueError('training memory changed')
    return record,readers


@contextmanager
def device(output,replay):
    if replay:yield;return
    if (output/'OWNER.json').exists():raise ValueError('unfinished worker requires native ownership inspection')
    if GPU_LOCK.exists():raise RuntimeError('GPU already owned; no reclamation')
    output.mkdir(parents=True,exist_ok=True)
    ollama.write_new(output/'OWNER.json',{'at':ollama.now(),'native':native_identity()})
    acquire_gpu_lock('stage10-revision-bank')
    try:yield
    finally:release_gpu_lock()


def predict(selection,output,phase,admission=None):
    if phase not in {'pilot','development','evaluation'}:raise ValueError('undeclared phase')
    record,readers=load(selection);binding=digest([record['binding'],phase])
    if phase!='pilot':
        admitted=checked(admission)
        if admitted['selection_binding']!=record['binding'] or admitted['admitted'] is not True:raise ValueError('literal admission required')
        receipt={'path':admission.as_posix(),'sha256':sha(admission/'COMPLETE.json')}
        if (output/'ADMISSION_PATH.json').exists():
            if read(output/'ADMISSION_PATH.json')!=receipt:raise ValueError('pilot source changed')
        else:ollama.write_new(output/'ADMISSION_PATH.json',receipt)
    rows=read(selection/(phase+'-public.json'))['tasks'];results=[]
    replay=(output/'COMPLETE.json').exists()
    if replay:checked(output)
    with device(output,replay):
        for row in rows:
            task=from_record(row)
            routes=[(a,768) for a in ARMS]
            if phase in {'pilot','development'}:routes += [('R0-reserved',256),('R1-reserved',512),('R3-reserved',512)]
            for arm,allowance in routes:
                if not replay:status(output/'STATUS.json',{'at':ollama.now(),'phase':phase,'completed_routes':len(results),'task':task.task_id,'arm':arm})
                result=readers.route(task,output/'routes'/task.task_id/arm,arm.split('-reserved')[0],allowance)
                results.append({'task_id':task.task_id,'arm':arm,'result':result})
    roster={'phase':phase,'selection_binding':record['binding'],'routes':results}
    if (output/'ROSTER.json').exists():
        if read(output/'ROSTER.json')!=roster:raise ValueError('reconstructed roster differs')
    else:ollama.write_new(output/'ROSTER.json',roster)
    extra={}
    if phase=='pilot':
        arm_names={r['arm'] for r in results}
        admitted=all(any(r['arm']==arm and r['result']['status']=='VALID' for r in results) for arm in arm_names)
        extra={'admitted':admitted,'selection_binding':record['binding'],
               'criterion':'at least one complete legal parsed route for each declared reader/budget; accuracy is not an admission criterion'}
    return finish(output,binding,extra)


def fit(selection,development,output):
    record,readers=load(selection);checked(development)
    # Rebuild every request/parse/execution from complete raw outputs BEFORE
    # opening development outcomes. Complete route replay cannot dispatch.
    predict(selection,development,'development',Path(read(development/'ADMISSION_PATH.json')['path']))
    prepared=Path(record['prepared']);frozen=read(prepared/'FROZEN.json')
    labels=read(prepared/'development-evaluator.json')
    if digest(labels)!=frozen['evaluator_sha256']['development']:raise ValueError('development labels differ')
    labels={r['task_id']:r for r in labels['targets']}
    routes={(r['task_id'],r['arm']):r['result'] for r in read(development/'ROSTER.json')['routes']}
    tasks=read(selection/'development-public.json')['tasks']
    bundle={'schema':'stage10.effort-development.1','phase':'development','complete':True,
            'producers':{'development':sha(development/'COMPLETE.json'),'selection':sha(selection/'COMPLETE.json')},
            'rows':[{'task':r,'truth':labels[r['task_id']]['correct_choice'],'group':labels[r['task_id']]['writer_component'],
                     'routes':{a:routes[(r['task_id'],a+'-reserved')] for a in ['R0','R1','R3']}} for r in tasks]}
    frozen_policy=effort.fit(bundle)
    output.mkdir(parents=True,exist_ok=False)
    ollama.write_new(output/'FIT.json',frozen_policy);ollama.write_new(output/'BUNDLE.json',bundle)
    return finish(output,digest(bundle))


def adaptive(selection,policy,output):
    record,readers=load(selection);checked(policy);frozen=read(policy/'FIT.json');effort.verify_policy(frozen)
    tasks=read(selection/'evaluation-public.json')['tasks'];ids={r['task_id']:r for r in read(selection/'evaluation-identity.json')['targets']}
    binding=digest([record['binding'],frozen]);replay=(output/'COMPLETE.json').exists();rows=[]
    if replay:checked(output)
    with device(output,replay):
        for row in tasks:
            task=from_record(row)
            for mode in ['fixed','confidence-only','benefit-cost']:
                if not replay:status(output/'STATUS.json',{'at':ollama.now(),'completed_routes':len(rows),'task':task.task_id,'mode':mode})
                result=effort.run(task,output/'routes'/task.task_id/mode,frozen,readers.initial,
                    {'R1':readers.retrieval,'R3':readers.structured},mode=mode,group=ids[task.task_id]['writer_component'],reader_sources=readers.sources)
                rows.append({'task_id':task.task_id,'arm':'R5-'+mode,'result':result})
    roster={'phase':'evaluation','selection_binding':record['binding'],'routes':rows}
    if (output/'ROSTER.json').exists():
        if read(output/'ROSTER.json')!=roster:raise ValueError('adaptive roster differs')
    else:ollama.write_new(output/'ROSTER.json',roster)
    return finish(output,binding)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','pilot','development','evaluation','fit','adaptive'])
    for name in ['prepared','selection','admission','development','policy','output']:p.add_argument('--'+name,type=Path,required=name=='output')
    a=p.parse_args()
    try:
        if a.action=='select':select(a.prepared,a.output)
        elif a.action=='fit':fit(a.selection,a.development,a.output)
        elif a.action=='adaptive':adaptive(a.selection,a.policy,a.output)
        else:predict(a.selection,a.output,a.action,a.admission)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():ollama.write_new(a.output/'FAILED.json',{'at':ollama.now(),'error':repr(exc)})
        raise


if __name__=='__main__':main()
