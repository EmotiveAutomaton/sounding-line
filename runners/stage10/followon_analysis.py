"""Complete-cell joins for the finite local Stage 10 extension.

DESIGN CHECK: LESSONS3-5 and the existing comparison freeze. NULL and
ALTERNATIVE retain identical denominators and all invalid outputs. Labels
join only after the complete declared prediction producers. Different models,
evidence interventions and source targets remain separately labelled.
"""
import argparse
import copy
from dataclasses import asdict
from pathlib import Path
from . import comparison,comparison_bank,comparison_inputs as ci,reading_effort
from .contracts import digest
from .queue import read
from .reader import from_record
from .revision_bank import checked,finish,sha
from .ollama import write_new,now

ROOT=ci.ROOT


def verify(sources):
    for name,expected in sources.items():
        if sha(Path(name))!=expected:raise ValueError('comparison input source changed: '+name)


def retain(ev,root):
    for p in root.rglob('*'):
        if p.is_file():ev.sources[p.as_posix()]=sha(p)


def prior(tasks,training,answers):
    # Training-only case-balanced prior; opaque labels are mapped by meaning.
    counts={};groups={}
    by_id={r['task_id']:r for r in answers}
    for row in training:
        group=by_id[row['task_id']].get('case_id',by_id[row['task_id']].get('writer_component'))
        groups[group]=groups.get(group,0)+1
    for row in training:
        a=by_id[row['task_id']];group=a.get('case_id',a.get('writer_component'))
        value=dict(row['choices'])[a['correct_choice']];counts[value]=counts.get(value,0)+1/groups[group]
    output={}
    for row in tasks:
        task=from_record(row);weights={k:counts.get(v,0)+1/len(task.choices) for k,v in task.choices}
        probabilities={k:v/sum(weights.values()) for k,v in weights.items()}
        output[task.task_id]={'status':'VALID','forecast':{'choice':max(probabilities,key=probabilities.get),
            'probabilities':probabilities,'insufficient_evidence':False,'explanation':'Training-case-balanced prior.'},'model_calls':0}
    return output


def second_model(selection,prediction,output):
    checked(selection);checked(prediction);ev=ci.Evidence()
    base=ev.get(ROOT/'coauthor-comparison-inputs-v1/BUNDLE.json')
    ev.sources.update(base['sources']);verify(base['sources'])
    chosen=ev.get(selection/'SELECTION.json');tasks=ev.get(selection/'evaluation-public.json')['tasks']
    retain(ev,selection);retain(ev,prediction)
    rows=ev.get(prediction/'ROSTER.json')['rows'];results={(r['task_id'],r['arm']):r['result'] for r in rows}
    if {r['task_id'] for r in rows}!={r['task_id'] for r in tasks}:raise ValueError('second model roster differs')
    cells=copy.deepcopy(base['cells'])
    for cell in cells:
        own={r['task_id'] for r in cell['tasks']}
        for arm in chosen['arms']:
            name='second-local/'+arm
            cell['predictions'][name]={i:{'task_public':from_record(next(r for r in tasks if r['task_id']==i)).public(),
                'status':'VALID' if results[i,arm]['status']=='VALID' else 'INVALID','forecast':results[i,arm]['forecast']} for i in own}
            cell['costs'][name]={k:sum(ci.costs(results[i,arm])[k] for i in own) for k in ci.costs(results[next(iter(own)),arm])}
            cell['contrasts'].append([name,arm])
        cell['contrasts'].extend([['second-local/R3','second-local/R2'],['second-local/R4-grounded','second-local/R1-memory']])
        cell['scope']+=' Second local profile '+chosen['model']+'; same original cohort and original selected rival; reused first-model costs are not new expenditure.'
    ev.sources[Path(__file__).as_posix()]=sha(Path(__file__))
    return ci.save(ev,cells,output)


def reading(adaptive,output):
    checked(adaptive);ev=ci.Evidence();prepared=ROOT/'reading-screen-v1';original=ROOT/'reading-science-v1/evaluation'
    ev.producer(original);readers=reading_effort.Readers(prepared);tasks=readers.tasks('evaluation');rows=[asdict(t) for t in tasks]
    routes={a:{} for a in ['R0','R1-memory','R2','R3','R4-opaque','R4-grounded']}
    for task in tasks:
        for arm in routes:
            path=original/'attempts'/task.task_id/('R1' if arm=='R1-memory' else arm)/'ROUTE.json'
            routes[arm][task.task_id]=ev.route(path)
    retain(ev,prepared);retain(ev,adaptive)
    for r in ev.get(adaptive/'ROSTER.json')['rows']:routes.setdefault(r['arm'],{})[r['task_id']]=r['result']
    labels=reading_effort.truths(prepared,'evaluation',tasks,ev)
    routes['baseline-class-prior']=prior(rows,readers.training,readers.answers)
    cells=ci.capsules(rows,labels,routes,'Ghost native reconstruction',
        'Historically exposed constructed cases; views and calls are not independent makers. Exact execution, prediction and historical correspondence are separate outcomes.')
    # Retain each executor response as an explicit separate readout; do not
    # convert predictive mixture success into historical-process recovery.
    executions=[]
    for p in original.rglob('EXECUTION.json'):
        value=ev.get(p);executions.append({'source':p.as_posix(),'response':value['response']})
    output.mkdir(parents=True,exist_ok=False)
    write_new(output/'EXECUTION_READOUTS.json',{'executions':executions,'scope':'native legality/reconstruction evidence; human interpretation and historical identity remain separate'})
    # save expects a new directory, so this auxiliary evidence is a sibling
    # named explicitly inside the final input capsule, not an extra result bank.
    ev.sources[Path(__file__).as_posix()]=sha(Path(__file__))
    bundle={'schema':'stage10.comparison-bank.1','sources':ev.sources,'cells':cells,'scope':'complete private cells; no final scientific verdict'}
    comparison_bank.analyze(bundle);write_new(output/'BUNDLE.json',bundle)
    return finish(output,digest(bundle),{'scientific_verdict':False})


def opportunity(output):
    ev=ci.Evidence();prepared=ROOT/'ghost-opportunity-screen-v1';legacy=ROOT/'ghost-opportunity-development-v1';adaptive=ROOT/'effort-evaluation-v1'
    ev.producer(legacy);ev.producer(adaptive)
    allocation=ev.get(ROOT/'effort-policy-v1/ALLOCATION.json');source=ev.get(prepared/'ALLOCATION.json');frozen=ev.get(prepared/'FROZEN.json')
    if digest(source)!=allocation['source_allocation_sha256']:raise ValueError('original opportunity allocation changed')
    all_public=ev.get(prepared/'development-public.json')
    if digest(all_public)!=frozen['public_sha256']['development']:raise ValueError('original opportunity tasks changed')
    members={r['task_id']:r['case_id'] for r in source['tasks']};reserve=set(allocation['evaluation_cases'])
    tasks=[r for r in all_public['tasks'] if members[r['task_id']] in reserve];routes={a:{} for a in ['R0','R1','R2','R3','R5-fixed','R5-confidence-only','R5-benefit-cost']}
    for row in tasks:
        i=row['task_id']
        for arm in ['R0','R1']:routes[arm][i]=ev.route(legacy/'direct-example/attempts'/i/arm/'ATTEMPT.json')
        routes['R2'][i]=ev.route(legacy/'deliberation/attempts'/i/'ROUTE.json')
        routes['R3'][i]=ev.route(legacy/'structured/attempts'/i/'ROUTE.json')
        for mode in ['fixed','confidence-only','benefit-cost']:routes['R5-'+mode][i]=ev.route(adaptive/'attempts'/i/mode/'ROUTE.json')
    manifest=ev.get(reading_effort.PUBLIC/'PUBLIC_MANIFEST.json')
    if ev.get(reading_effort.EXPORT/'PUBLIC_MANIFEST.json')!=manifest:raise ValueError('export mismatch')
    raw=ev.get(reading_effort.EXPORT/'RAW_MANIFEST.json');case_members={c['case_id']:set(c['tasks_in_recorded_order']) for c in manifest['cases']};labels={}
    for row in tasks:
        task=from_record(row);case=members[task.task_id];relative='private/'+case+'-evaluation.json';path=reading_effort.EXPORT/relative
        if sha(path)!=raw['files'][relative]:raise ValueError('original opportunity truth changed')
        value=ev.get(path)
        if value['case_id']!=case or set(value['task_ids'])!=case_members[case]:raise ValueError('task/case membership changed')
        actual=value['hidden_continuations']
        if type(actual['artifact']) is not int or actual['artifact'] not in (0,1) or type(actual['legal']) is not bool:raise ValueError('not an enacted binary outcome')
        labels[task.task_id]={'correct_choice':next(k for k,v in task.choices if v==str(actual['artifact'])),
            'writer_component':case,'prompt_component':case,'source_event':task.task_id}
    train=ev.get(prepared/'train-public.json');answers=ev.get(prepared/'train-evaluator.json')
    if digest(train)!=frozen['public_sha256']['train'] or digest(answers)!=frozen['evaluator_sha256']['train']:raise ValueError('training source changed')
    routes['baseline-class-prior']=prior(tasks,train['tasks'],answers['targets'])
    cells=ci.capsules(tasks,labels,routes,'Ghost opportunity reserved cases',allocation['scope']+'; R4 is not substituted from a different task interface.')
    ev.sources[Path(__file__).as_posix()]=sha(Path(__file__))
    return ci.save(ev,cells,output)


def history_difference(original,altered,pairs):
    """Paired evidence intervention, explicitly different from strategy pairing."""
    if len(original['rows'])!=len(pairs) or len(altered['rows'])!=len(pairs):raise ValueError('history denominator differs')
    left={r['task_id']:r for r in original['rows']};right={r['task_id']:r for r in altered['rows']};rows=[]
    for pair in pairs:
        x=left[pair['original']['task_id']];y=right[pair['altered']['task_id']]
        a=copy.deepcopy(x['public']);b=copy.deepcopy(y['public'])
        h=a['evidence'].pop('earlier_handling');j=b['evidence'].pop('earlier_handling')
        if a!=b or len(h)!=len(j) or pair['original_writer']==pair['donor_writer']:raise ValueError('undeclared history intervention')
        if any(x[k]!=y[k] for k in ['truth','group','event','dependencies','component']):raise ValueError('history grouping or target differs')
        rows.append({'group':x['group'],'component':x['component'],'benefit':y['brier_system']-x['brier_system'],
            'accuracy':x['generated_correct']-y['generated_correct']})
    return {'direction':'positive favors original own history; altered loss minus original loss',
        'brier':comparison.uncertainty(rows,'benefit'),'generated_accuracy':comparison.uncertainty(rows,'accuracy'),
        'attempted_pairs':len(rows),'original_invalid':original['summary']['invalid'],'altered_invalid':altered['summary']['invalid']}


def history(output):
    ev=ci.Evidence();frozen=ev.get(ROOT/'human-history-selection-v1/FROZEN.json');producer=ROOT/'human-history-evaluation-v1';ev.producer(producer)
    original=ev.get(ROOT/'coauthor-comparison-inputs-v1/BUNDLE.json');ev.sources.update(original['sources']);verify(original['sources'])
    cell=next(c for c in original['cells'] if c['tasks'][0]['evidence_view']=='process-record');results={}
    for arm in ['R0',frozen['fit']['chosen']]:
        own=[];changed=[];answers={};pred_a={};pred_b={}
        for pair in frozen['pairs']:
            a=from_record(pair['original']);b=from_record(pair['altered']);own.append(a);changed.append(b)
            target=cell['answers'][a.task_id];answers[a.task_id]=target;answers[b.task_id]=target
            pred_a[a.task_id]=cell['predictions'][arm][a.task_id]
            path=producer/'attempts'/digest([b.task_id,arm])[:32]/('ATTEMPT.json' if arm=='R0' else 'ROUTE.json');value=ev.route(path)
            pred_b[b.task_id]={'task_public':b.public(),'status':'VALID' if value['status']=='VALID' else 'INVALID','forecast':value['forecast']}
        x=comparison.cell(own,{t.task_id:answers[t.task_id] for t in own},pred_a,population='matched history')
        y=comparison.cell(changed,{t.task_id:answers[t.task_id] for t in changed},pred_b,population='matched history')
        results[arm]={'paired':history_difference(x,y,frozen['pairs']),'original':x,'altered':y}
    output.mkdir(parents=True,exist_ok=False);write_new(output/'RESULT.json',{'results':results,'excluded':frozen['excluded'],
        'sources':ev.sources,'scope':'preselected exact-length other-writer history; same task otherwise, no new independent population or personal-intent truth'})
    return finish(output,digest(ev.sources),{'scientific_verdict':False})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['second-model','reading','opportunity','history']);p.add_argument('--output',type=Path,required=True)
    for name in ['selection','prediction','adaptive']:p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    try:
        if a.action=='second-model':second_model(a.selection,a.prediction,a.output)
        elif a.action=='reading':reading(a.adaptive,a.output)
        elif a.action=='opportunity':opportunity(a.output)
        else:history(a.output)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():write_new(a.output/'FAILED.json',{'at':now(),'error':repr(exc)})
        raise
