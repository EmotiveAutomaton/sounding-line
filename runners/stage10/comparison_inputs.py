"""Assemble complete human comparison cells without choosing by outcomes.

DESIGN CHECK: frozen Stage10 contrasts, LESSONS3-5. Exact pre-existing selection
rosters determine every denominator under NULL and ALTERNATIVE. Future answers
join only after all declared readers have complete produces. Never filter by
validity or effect direction. Raw human text remains in private result folders.
"""
import argparse
from collections import Counter,defaultdict
from pathlib import Path
from .contracts import digest
from .queue import read
from .reader import from_record
from .ollama import write_new,now
from .revision_bank import sha,finish,checked
from . import comparison_bank,revision_source

ROOT=Path('results/phase_2_4_stage_10/raw')
CONTRASTS=[('R3','R2'),('R4-grounded','R1-memory'),('R5-benefit-cost','R5-fixed'),
           ('R4-grounded','R3'),('R4-grounded','R4-opaque'),('R5-confidence-only','R5-fixed'),('R5-benefit-cost','R5-confidence-only')]


def costs(result):
    if 'cost' in result and 'model_calls' in result['cost']:
        c=result['cost'];return {k:c[k] for k in ['model_calls','input_tokens','output_tokens','wall_seconds','executor_evaluations']}
    if 'calls' in result:
        calls=result['calls'];return {'model_calls':len(calls),'input_tokens':sum(c['cost']['prompt_eval_count'] for c in calls),
            'output_tokens':sum(c['cost']['eval_count'] for c in calls),'wall_seconds':sum(c['wall_seconds'] for c in calls),'executor_evaluations':0}
    if 'cost' in result:
        c=result['cost'];return {'model_calls':1,'input_tokens':c['prompt_eval_count'],'output_tokens':c['eval_count'],
                               'wall_seconds':result['wall_seconds'],'executor_evaluations':0}
    return {k:result.get(old,0) for k,old in [('model_calls','model_calls'),('input_tokens','input_tokens'),
        ('output_tokens','generated_tokens'),('wall_seconds','wall_seconds'),('executor_evaluations','executor_evaluations')]}


def capsules(tasks,labels,routes,population,scope,exclusions=()):
    output=[];partitions=defaultdict(list)
    for row in tasks:partitions[(row['family'],row['evidence_view'])].append(from_record(row))
    for (family,view),own in sorted(partitions.items()):
        ids={t.task_id for t in own};predictions={};charges={}
        answers={i:{'truth':labels[i]['correct_choice'],'group':labels[i]['writer_component'],
                    'dependencies':[labels[i]['prompt_component']],'event':labels[i]['source_event']} for i in ids}
        for arm,rows in routes.items():
            if not ids<=set(rows):raise ValueError('complete common reader roster missing: '+arm)
            predictions[arm]={t.task_id:{'task_public':t.public(),'status':'VALID' if rows[t.task_id]['status']=='VALID' else 'INVALID',
                                      'forecast':rows[t.task_id]['forecast']} for t in own}
            charges[arm]={k:sum(costs(rows[i])[k] for i in ids) for k in costs(next(iter(rows.values())))}
        contrasts=[list(p) for p in CONTRASTS if set(p)<=set(routes)]
        output.append({'tasks':[next(r for r in tasks if r['task_id']==t.task_id) for t in own],
            'answers':answers,'predictions':predictions,'population':population+' / '+family+' / '+view,
            'scope':scope,'costs':charges,'contrasts':contrasts,'exclusions':list(exclusions)})
    return output


class Evidence:
    def __init__(self):self.sources={}
    def get(self,path):
        self.sources[path.as_posix()]=sha(path);return read(path)
    def producer(self,root):
        complete=self.get(root/'COMPLETE.json')
        if complete.get('status')!='COMPLETE':raise ValueError('incomplete prediction producer')
        return complete
    def route(self,path):
        # Bind all saved request/raw/cost/execution material, already internally
        # landed for legacy producers, rather than only an extracted forecast.
        for p in path.parent.rglob('*'):
            if p.is_file():self.sources[p.as_posix()]=sha(p)
        value=self.get(path)
        terminal=path.with_name('COMPLETE.json')
        if terminal.exists():
            for name,expected in self.get(terminal).get('files',{}).items():
                p=path.parent/name
                if not p.resolve().is_relative_to(path.parent.resolve()) or sha(p)!=expected:raise ValueError('retained route changed')
        return value


def human(output,earlier=False):
    ev=Evidence();base=ROOT/'coauthor-screen-v1';phase='evaluation'
    original=ev.get(base/'FROZEN.json')
    if earlier:
        selected=ROOT/'earlier-structured-selection-v1';frozen=ev.get(selected/'FROZEN.json');public=ev.get(selected/'evaluation-public.json')
        identities=ev.get(selected/'IDENTITIES.json')['evaluation']
        direct=ROOT/'earlier-artifact-science-v1/evaluation/direct-example';r2=ROOT/'earlier-artifact-science-v1/evaluation/deliberation'
        structured=ROOT/'earlier-structured-science-v1';adaptive=ROOT/'earlier-effort-science-v1/evaluation'
        r3=None
    else:
        selected=base;frozen=original;public=ev.get(base/'evaluation-public.json');identities=None
        direct=ROOT/'coauthor-evaluation-v1';r2=ROOT/'coauthor-deliberation-evaluation-v1'
        structured=ROOT/'human-memory-science-v1';adaptive=ROOT/'human-effort-evaluation-v1';r3=ROOT/'human-science-v1/evaluation'
    if digest(public)!=frozen['public_sha256']['evaluation']:raise ValueError('frozen comparison population changed')
    for p in [direct,r2,structured,adaptive]+([r3] if r3 else []):ev.producer(p)
    # Only now reveal the complete original evaluation labels for scoring.
    answers=ev.get(base/'evaluation-evaluator.json')
    if digest(answers)!=original['evaluator_sha256']['evaluation']:raise ValueError('original evaluator changed')
    labels={r['task_id']:r for r in answers['targets']}
    if earlier:
        labels={r['task_id']:{**labels[r['original_task_id']],**{k:r[k] for k in ['task_id','writer_component','prompt_component','source_event']}} for r in identities}
    routes={a:{} for a in ['R0','R1','R2','R3','R1-memory','R4-opaque','R4-grounded','R5-fixed','R5-confidence-only','R5-benefit-cost']}
    for row in public['tasks']:
        i=row['task_id']
        for arm in ['R0','R1']:routes[arm][i]=ev.route(direct/'attempts'/i/arm/'ATTEMPT.json')
        routes['R2'][i]=ev.route(r2/'attempts'/i/'ROUTE.json')
        for arm in ['R3','R1-memory','R4-opaque','R4-grounded']:
            path=(r3/'attempts'/i/'ROUTE.json' if arm=='R3' and r3 else structured/'attempts'/digest([phase,i,arm])[:32]/'ROUTE.json')
            routes[arm][i]=ev.route(path)
        for mode in ['fixed','confidence-only','benefit-cost']:routes['R5-'+mode][i]=ev.route(adaptive/'attempts'/i/mode/'ROUTE.json')
    if not earlier:
        ev.producer(ROOT/'human-baselines-v1');baseline=ev.get(ROOT/'human-baselines-v1/RESULT.json')
        for row in baseline['predictions']:
            if row['phase']=='evaluation':routes.setdefault('baseline-'+row['arm'],{})[row['task_id']]=row
    cells=capsules(public['tasks'],labels,routes,'CoAuthor earlier drafts' if earlier else 'CoAuthor original',
        'Historically exposed descriptive human handling; fixed writer/prompt separation. Model suggestions are not human-authored text.',
        frozen.get('additional_context_exclusions',[]))
    return save(ev,cells,output)


def schola(selection,prediction,adaptive,output):
    ev=Evidence();checked(selection);checked(prediction);checked(adaptive)
    selected=ev.get(selection/'SELECTION.json');prepared=Path(selected['prepared']);frozen=ev.get(prepared/'FROZEN.json')
    tasks=ev.get(selection/'evaluation-public.json')['tasks'];routes={}
    for root in [prediction,adaptive]:
        ev.producer(root)
        for p in root.rglob('*'):
            if p.is_file():ev.sources[p.as_posix()]=sha(p)
        for row in ev.get(root/'ROSTER.json')['routes']:
            arm='R1-memory' if row['arm']=='R1' else row['arm'];routes.setdefault(arm,{})[row['task_id']]=row['result']
    answers=ev.get(prepared/'evaluation-evaluator.json')
    if digest(answers)!=frozen['evaluator_sha256']['evaluation']:raise ValueError('whole-project evaluator changed')
    labels={r['task_id']:r for r in answers['targets']}
    train=ev.get(selection/'train-public.json')['tasks'];train_labels={r['task_id']:r for r in ev.get(selection/'train-evaluator.json')['targets']}
    for row in tasks:
        task=from_record(row);pool=[from_record(r) for r in train if r['family']==task.family and r['evidence_view']==task.evidence_view]
        groups=Counter(train_labels[t.task_id]['writer_component'] for t in pool);counts={v:1/len(task.choices) for _,v in task.choices}
        for t in pool:counts[dict(t.choices)[train_labels[t.task_id]['correct_choice']]]+=1/groups[train_labels[t.task_id]['writer_component']]
        probabilities={k:counts[v]/sum(counts.values()) for k,v in task.choices}
        forecast={'choice':max(probabilities,key=probabilities.get),'probabilities':probabilities,'insufficient_evidence':False,'explanation':'Training-project-balanced class prior with one total prior pseudocount.'}
        routes.setdefault('baseline-class-prior',{})[task.task_id]={'status':'VALID','forecast':forecast,'model_calls':0}
    cells=capsules(tasks,labels,routes,'ScholaWrite fold '+str(frozen['fold']),
        'Descriptive whole-project separation; released edit annotations are not writer-stated goals. Cross-fold roles overlap; do not count folds as independent projects.',selected['rejections'])
    return save(ev,cells,output)


def save(evidence,cells,output):
    evidence.sources[Path(__file__).as_posix()]=sha(Path(__file__))
    bundle={'schema':'stage10.comparison-bank.1','sources':evidence.sources,'cells':cells,'scope':'complete private numerical cells; single stage scientific packet remains required'}
    comparison_bank.analyze(bundle)  # Validate full roster before writing a produce.
    output.mkdir(parents=True,exist_ok=False);write_new(output/'BUNDLE.json',bundle)
    return finish(output,digest(bundle),{'scientific_verdict':False})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['human','earlier','schola']);p.add_argument('--output',type=Path,required=True)
    for name in ['selection','prediction','adaptive']:p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    try:
        if a.mode=='schola':schola(a.selection,a.prediction,a.adaptive,a.output)
        else:human(a.output,a.mode=='earlier')
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():write_new(a.output/'FAILED.json',{'at':now(),'error':repr(exc)})
        raise
