"""Predecision draft snapshots, distinct from action/handling records.

DESIGN CHECK: LESSONS3-5 and CONTROLS6 reread. NULL: an unchanged earlier draft
adds no new content; retain it and empty histories explicitly. ALTERNATIVE:
a truly earlier state may improve a future handling forecast. No later state,
handling label or inferred cross-session chronology enters public evidence.
This producer does not score that hypothesis or substitute R2 for R3/R4.
"""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from . import ollama, phase_queue, phase_deliberation
from .contracts import canonical, digest
from .reader import from_record, build
from .queue import read, status
from .human_effort_evaluation import metadata


def identity():
    return {**phase_queue.source_identity(),**phase_deliberation.identity(),
        'runners/stage10/earlier_artifacts.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def projection(raw):
    allowed={'key','events','ordinal','document','usable','options','trimmed'}
    return json.loads(raw,object_pairs_hook=lambda pairs:{k:v for k,v in pairs if k in allowed})


def index_session(session):
    previous=None; last=-1; rows={}
    for event in session['events']:
        ordinal=event['ordinal']
        if type(ordinal) is not int or ordinal<=last: raise ValueError('source chronology repeats or reverses')
        last=ordinal
        if not event['usable']: continue
        if not isinstance(event['document'],str): raise ValueError('draft must be source text')
        key=digest({'session':session['key'],'event':ordinal})
        rows[key]={'current':event,'prior':previous,'session':session['key']}
        previous={'ordinal':ordinal,'document':event['document']}
    return rows


def extend(task, source):
    current=source['current']; prior=source['prior']
    if task.evidence_view!='artifact' or task.evidence!={'document':current['document'],'suggestions':[r['trimmed'] for r in current['options']]}:
        raise ValueError('current source draft/menu differs from frozen task')
    if prior and prior['ordinal']>=current['ordinal']: raise ValueError('future or current draft cannot be prior')
    previous=[] if prior is None else [prior['document']]
    return replace(task,task_id=digest(['s10-earlier-artifacts-v1',task.task_id])[:32],
        evidence_view='earlier-artifacts',evidence={**task.evidence,'earlier_drafts':previous})


def bounds(task, training, answers):
    for arm in ('R0','R1'): build(task,arm,training,answers)
    ollama.request_for(task,generated_tokens=384,context_tokens=16384)
    reserved=replace(task,evidence={'original_source_evidence':task.evidence,
        'reader_scratchpad':{'origin':"this reader's earlier unverified response to the same task; not an observation",
                            'parse_status':'INVALID','draft':'x'*4096}})
    ollama.request_for(reserved,generated_tokens=384,context_tokens=16384,
        instruction='Reconsider the original evidence and the earlier reader draft. The draft may be wrong and is not an observed outcome. Return your final direct forecast without inventing a latent maker narrative.')


def prepare(original, sessions, output):
    frozen=read(original/'FROZEN.json'); sources=read(original/'SOURCE.json')
    if digest(sources)!=frozen['source_sha256']: raise ValueError('original source inventory changed')
    indexed={}; pins={}
    for key,expected in sources['source_sessions'].items():
        path=sessions/(key+'.json'); raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError('source session changed')
        session=projection(raw)
        if session['key']!=key: raise ValueError('session identity changed')
        rows=index_session(session)
        if indexed.keys() & rows.keys(): raise ValueError('duplicate source events')
        indexed.update(rows); pins[str(path)]=expected
    training_labels=read(original/'train-evaluator.json')
    if digest(training_labels)!=frozen['evaluator_sha256']['train']: raise ValueError('training labels changed')
    label_map={r['task_id']:r for r in training_labels['targets']}
    public={}; identities={}; counts={}; exclusions=[]
    for phase in ('train','development','evaluation'):
        payload=read(original/(phase+'-public.json'))
        if digest(payload)!=frozen['public_sha256'][phase]: raise ValueError('original public cohort changed')
        groups=metadata(original,phase,frozen); tasks=[]; ids=[]
        for record in payload['tasks']:
            task=from_record(record)
            if task.evidence_view!='artifact': continue
            source=indexed[groups[task.task_id]['source_event']]
            extended=extend(task,source)
            tasks.append(asdict(extended))
            ids.append({**groups[task.task_id],'task_id':extended.task_id,'original_task_id':task.task_id,
                'session':source['session'],'current_ordinal':source['current']['ordinal'],
                'prior_ordinal':source['prior']['ordinal'] if source['prior'] else None,
                'earlier_draft_present':source['prior'] is not None,
                'earlier_draft_identical':bool(source['prior'] and source['prior']['document']==source['current']['document'])})
        public[phase]={'tasks':tasks}; identities[phase]=ids
    labels={'targets':[{**label_map[r['original_task_id']],'task_id':r['task_id']} for r in identities['train']]}
    for phase in ('development','evaluation'):
        retained=[]; retained_ids=[]
        for record,own in zip(public[phase]['tasks'],identities[phase]):
            try: bounds(from_record(record),public['train']['tasks'],labels['targets'])
            except ValueError as exc:
                exclusions.append({'phase':phase,'task_id':record['task_id'],'original_task_id':own['original_task_id'],'reason':str(exc)})
                continue
            retained.append(record); retained_ids.append(own)
        if not retained: raise ValueError('no targets fit the unchanged reader budget')
        public[phase]={'tasks':retained}; identities[phase]=retained_ids
    for phase,rows in identities.items():
        counts[phase]={'tasks':len(rows),'writers':len({r['writer_component'] for r in rows}),
            'prompts':len({r['prompt_component'] for r in rows}),
            'no_earlier_draft':sum(not r['earlier_draft_present'] for r in rows),
            'identical_earlier_draft':sum(r['earlier_draft_identical'] for r in rows)}
    result={'status':'FROZEN','sources':identity(),'original_root':str(original),
        'original_frozen_sha256':digest(frozen),'source_files':pins,'counts':counts,'exclusions':exclusions,
        'public_sha256':{k:digest(v) for k,v in public.items()},'evaluator_sha256':{'train':digest(labels)},
        'identities_sha256':digest(identities),'scope':'latest earlier usable menu-time draft within the same verified session; no handling outcomes supplied; historical descriptive sources',
        'remaining':'R3/R4/R5 earlier-artifact extension and full paired scientific comparison remain separate'}
    records={**{k+'-public.json':v for k,v in public.items()},'train-evaluator.json':labels,'IDENTITIES.json':identities,'FROZEN.json':result}
    if (output/'FROZEN.json').exists():
        if any(read(output/name)!=json.loads(canonical(value)) for name,value in records.items()): raise ValueError('earlier-artifact freeze changed')
    else:
        for name,value in records.items(): ollama.write_new(output/name,value)
    return result


def run(prepared, output, pilot):
    frozen=read(prepared/'FROZEN.json')
    if frozen['sources']!=identity(): raise ValueError('earlier-artifact code changed')
    for name,value in frozen['source_files'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=value: raise ValueError('original draft source changed')
    admission=read(pilot)
    if admission.get('status')!='PASS' or admission.get('sources')!=identity() or admission.get('prepared_sha256')!=digest(frozen):
        raise ValueError('source-bound literal earlier-artifact pilot required')
    manifest={'sources':identity(),'prepared_sha256':digest(frozen),'pilot_sha256':digest(admission),
        'jobs':[{'phase':p,'reader':r,'produces':f'{p}/{r}/COMPLETE.json'} for p in ('development','evaluation') for r in ('direct-example','deliberation')]}
    if (output/'MANIFEST.json').exists():
        if read(output/'MANIFEST.json')!=manifest: raise ValueError('earlier-artifact queue changed')
    else: ollama.write_new(output/'MANIFEST.json',manifest)
    completed=(output/'COMPLETE.json').exists(); results=[]
    for job in manifest['jobs']:
        if identity()!=manifest['sources']: raise ValueError('running source changed')
        directory=output/job['phase']/job['reader']
        if completed and not (directory/'COMPLETE.json').exists(): raise ValueError('completed child missing; no rerun')
        if not completed and not (directory/'COMPLETE.json').exists() and (directory/'OWNER.json').exists():
            raise RuntimeError('unfinished child requires native ownership recovery')
        if not completed: status(output/'STATUS.json',{'at':ollama.now(),'status':'RUNNING','active':job,'completed_jobs':len(results),'planned_jobs':len(manifest['jobs'])})
        r=(phase_queue.run(prepared,directory,['R0','R1'],job['phase']) if job['reader']=='direct-example'
           else phase_deliberation.run(prepared,directory,job['phase']))
        if r['status']!='COMPLETE': raise ValueError('child did not complete')
        results.append({**job,'sha256':digest(r),'calls':r.get('attempted_calls',r.get('model_calls'))})
    result={'status':'COMPLETE','manifest_sha256':digest(manifest),'jobs':results,'model_calls':sum(r['calls'] for r in results)}
    if completed:
        if read(output/'COMPLETE.json')!=result: raise ValueError('completed chain changed')
    else:
        ollama.write_new(output/'COMPLETE.json',result)
        status(output/'STATUS.json',{'at':ollama.now(),'status':'COMPLETE','completed_jobs':len(results)})
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--prepared',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--pilot',type=Path,required=True)
    a=p.parse_args()
    try: run(a.prepared,a.output,a.pilot)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists(): ollama.write_new(a.output/'FAILED.json',{'at':ollama.now(),'error':repr(exc)})
        raise
