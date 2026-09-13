"""Small continuity anchor: one future-cycle distribution per whole essay/view.

DESIGN CHECK: Stage10 section7, LESSONS2-5 and original ArgRewrite whole-cycle
contract. NULL/ALTERNATIVE retain the nine published classes and essay grouping.
Later target locations never select earlier evidence. Record views show an
explicit earlier-draft diff. This does not rename purpose annotations as effects.
"""
import argparse
from collections import Counter
from dataclasses import asdict,replace
import difflib
from pathlib import Path
from runners.stage9.argrewrite import CLASSES,future_visible
from . import ollama,deliberation,comparison_inputs
from .contracts import PublicTask,choices_for,canonical,digest
from .reader import from_record
from .queue import read,status
from .revision_bank import sha,finish,checked,device

ROOT=Path('results/phase_2_4_stage_9/private/prepared/argrewrite-v3')


def source_identity():
    names=['runners/stage10/argrewrite_reader.py','runners/stage9/argrewrite.py','runners/stage10/revision_bank.py']
    return {**deliberation.identity(),**{n:sha(Path(n)) for n in names}}


def project(essay,view):
    evidence=future_visible(essay,'artifact' if view=='artifact' else 'record')
    if view=='process-record':evidence={**evidence,'explicit_earlier_diff':'\n'.join(difflib.ndiff(evidence['before'].splitlines(),evidence['after'].splitlines()))}
    return PublicTask(digest(['s10-arg-whole-cycle',essay['group'],view])[:32],'argrewrite-future-cycle',view,evidence,
        'Forecast the annotated revision-purpose class of a uniformly sampled usable canonical revision unit in the NEXT whole draft2-to-draft3 cycle. Give one distribution for this entire essay, not a location-selected edit.',
        choices_for([c.replace('_',' ') for c in CLASSES],essay['group']),
        'future draft2-to-draft3 cycle; only drafts1/2 and earlier annotations are available',
        'human student revision; released annotations are not direct reports of unconscious intent','historically exposed ArgRewrite; descriptive essay separation')


def prepare(output,root=ROOT,maximum=12):
    if not 1<=maximum<=18:raise ValueError('small anchor only')
    identity=read(root/'IDENTITY.json');complete=read(root/'COMPLETE.json')
    if complete['identity_sha256']!=digest(identity) or not complete['historical_v4_exact']:raise ValueError('canonical ArgRewrite preparation required')
    paths=sorted((root/'essays').glob('*.json'));essays=[read(p) for p in paths]
    if len(essays)!=complete['essay_student_lineages']:raise ValueError('incomplete essay inventory')
    groups=sorted([e['group'] for e in essays],key=lambda g:digest({'arg-fit':g}));training=set(groups[:3*len(groups)//4])
    pilot=[];evaluation=[];targets={};excluded=[];pilot_groups=set()
    for essay in sorted(essays,key=lambda e:digest(['stage10-arg-continuity',e['group']])):
        if not essay['future_usable']:excluded.append({'group':essay['group'],'reason':'original future preparation exclusion'});continue
        future=[u for u in essay['units'] if u['cycle']=='23' and u['usable']]
        if not future:excluded.append({'group':essay['group'],'reason':'empty usable future cycle'});continue
        tasks=[project(essay,view) for view in ['artifact','process-record']]
        try:
            for task in tasks:
                # Reserve a full R2 scratchpad without truncating source evidence.
                if len(canonical(task.public()).encode('utf8'))>12000:raise ValueError('whole source exceeds common request allowance')
                ollama.request_for(task,context_tokens=16384)
        except ValueError as exc:excluded.append({'group':essay['group'],'reason':str(exc)});continue
        if essay['group'] in training:
            if len(pilot_groups)>=2:continue
            pilot_groups.add(essay['group']);pilot.extend(asdict(t) for t in tasks)
        else:
            if len(evaluation)>=maximum*2:continue
            evaluation.extend(asdict(t) for t in tasks)
            for t in tasks:targets[t.task_id]={'group':essay['group'],'units':[{'key':u['key'],'truth':next(k for k,v in t.choices if v==u['fine'].replace('_',' '))} for u in future]}
    if len(pilot_groups)!=2 or not evaluation:raise ValueError('no complete small anchor/pilot population')
    prior={c:1/len(CLASSES) for c in CLASSES};fit_groups=[]
    for essay in essays:
        if essay['group'] not in training-pilot_groups or not essay['future_usable']:continue
        units=[u['fine'] for u in essay['units'] if u['cycle']=='23' and u['usable']]
        if not units:continue
        fit_groups.append(essay['group'])
        for c,n in Counter(units).items():prior[c]+=n/len(units)
    total=sum(prior.values());prior={c:n/total for c,n in prior.items()}
    pins={p.as_posix():sha(p) for p in [root/'IDENTITY.json',root/'COMPLETE.json',*paths]}
    frozen={'sources':source_identity(),'inputs':pins,'pilot_groups':sorted(pilot_groups),'fit_groups':sorted(fit_groups),'excluded':excluded,
        'public_sha256':{'pilot':digest({'tasks':pilot}),'evaluation':digest({'tasks':evaluation})},'targets_sha256':digest(targets),'prior':prior,
        'scope':'one whole-cycle forecast per essay/view; scored over all canonical future units with equal essay weight; no target-selected spans'}
    output.mkdir(parents=True,exist_ok=False)
    for name,value in [('FROZEN.json',frozen),('pilot-public.json',{'tasks':pilot}),('evaluation-public.json',{'tasks':evaluation}),('evaluation-targets.json',targets)]:ollama.write_new(output/name,value)
    return finish(output,digest(frozen))


def run(prepared,output,phase,admission=None):
    checked(prepared);frozen=read(prepared/'FROZEN.json')
    if phase not in {'pilot','evaluation'} or frozen['sources']!=source_identity():raise ValueError('anchor source/phase differs')
    if phase=='evaluation':
        p=checked(admission)
        if not p['admitted'] or p['prepared_sha256']!=digest(frozen):raise ValueError('literal anchor admission required')
    tasks=read(prepared/(phase+'-public.json'));binding=digest([frozen,phase]);rows=[]
    if digest(tasks)!=frozen['public_sha256'][phase]:raise ValueError('anchor task changed')
    replay=(output/'COMPLETE.json').exists()
    if replay:checked(output)
    with device(output,replay):
        for row in tasks['tasks']:
            task=from_record(row)
            for arm in ['R0','R2']:
                target=output/'routes'/task.task_id/arm
                if replay and not target.exists():raise ValueError('missing original anchor route')
                if not replay:status(output/'STATUS.json',{'at':ollama.now(),'completed_routes':len(rows),'task':task.task_id,'arm':arm})
                result=ollama.call(task,target,context_tokens=16384) if arm=='R0' else deliberation.route(task,target)
                rows.append({'task_id':task.task_id,'arm':arm,'result':result})
    roster={'phase':phase,'routes':rows}
    if (output/'ROSTER.json').exists():
        if read(output/'ROSTER.json')!=roster:raise ValueError('anchor replay differs')
    else:ollama.write_new(output/'ROSTER.json',roster)
    extra={'prepared_sha256':digest(frozen)}
    if phase=='pilot':extra['admitted']=all(any(r['arm']==arm and r['result']['status']=='VALID' for r in rows) for arm in ['R0','R2'])
    return finish(output,binding,extra)


def analyze(prepared,prediction,output):
    ev=comparison_inputs.Evidence();checked(prepared);checked(prediction);ev.producer(prediction)
    frozen=ev.get(prepared/'FROZEN.json');tasks=ev.get(prepared/'evaluation-public.json')['tasks']
    targets=ev.get(prepared/'evaluation-targets.json')
    if digest(targets)!=frozen['targets_sha256']:raise ValueError('original whole-cycle target changed')
    records={(r['task_id'],r['arm']):r['result'] for r in ev.get(prediction/'ROSTER.json')['routes']}
    projected=[];labels={};routes={a:{} for a in ['R0','R2','baseline-class-prior']}
    for row in tasks:
        task=from_record(row);target=targets[task.task_id]
        probability={k:frozen['prior'][v.replace(' ','_')] for k,v in task.choices}
        baseline={'status':'VALID','forecast':{'choice':max(probability,key=probability.get),'probabilities':probability,'explanation':'Training-essay-balanced prior.','insufficient_evidence':False}}
        for unit in target['units']:
            unit_task=replace(task,task_id=digest([task.task_id,unit['key']])[:32]);projected.append(asdict(unit_task))
            labels[unit_task.task_id]={'correct_choice':unit['truth'],'writer_component':target['group'],'prompt_component':target['group'],'source_event':unit['key']}
            for arm in routes:routes[arm][unit_task.task_id]=baseline if arm.startswith('baseline') else records[(task.task_id,arm)]
    cells=comparison_inputs.capsules(projected,labels,routes,'ArgRewrite prospective continuity',frozen['scope'],frozen['excluded'])
    for cell in cells:
        view=cell['tasks'][0]['evidence_view'];own=[t for t in tasks if t['evidence_view']==view]
        for arm in ['R0','R2']:cell['costs'][arm]={k:sum(comparison_inputs.costs(records[(t['task_id'],arm)])[k] for t in own) for k in comparison_inputs.costs(records[(own[0]['task_id'],arm)])}
        cell['contrasts']=[['R2','R0']]
    return comparison_inputs.save(ev,cells,output)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','pilot','evaluation','analyze']);p.add_argument('--output',type=Path,required=True)
    for name in ['prepared','admission','prediction']:p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    try:
        if a.action=='prepare':prepare(a.output)
        elif a.action=='analyze':analyze(a.prepared,a.prediction,a.output)
        else:run(a.prepared,a.output,a.action,a.admission)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():ollama.write_new(a.output/'FAILED.json',{'at':ollama.now(),'error':repr(exc)})
        raise
