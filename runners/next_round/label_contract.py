"""Bounded F4 label-definition diagnostic; no feature promotion.

DESIGN CHECK: LESSONS 2-5, CONTROLS 1-3 re-read 2026-10-15.
NULL: equal predictions give zero paired benefit; constants fail other labels.
ALTERNATIVE: explicit definitions improve target labels without hidden exclusions.
Complete roster only; invalid returned answers stay wrong, unknown transport stops.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'
import argparse,json,random,threading,time,traceback
from pathlib import Path
from collections import defaultdict
from . import literal_models as lm
from .scope_diagnostic import SCOPE,NoCache
from .queue import resource_snapshot,require_resources
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,digest,now,limits
from runners.stage9.process_identity import native_identity

ROOT=REPO/'results/phase_2_4_stage_15/raw/label-contract-v1'
DEFINITIONS={
 'Q6':('Here grammatical person means the pronoun-person groups present in the target text, '
        'not its narrative viewpoint or only its subject. First-person pronouns include I, me, '
        'my, we, us, our; second-person pronouns include you, your; third-person pronouns '
        'include he, him, his, she, her, they, them, their. Answer mixed if more than one '
        'of these groups is present, otherwise answer the single group present.\n'),
 'Q10':('The answer is an array of tags literally supported by the target text. '
         'Return an empty array when none of the listed themes is present. '
         'Absence of a listed theme is not uncertainty. Use ["unclear"] only when '
         'the evidence is insufficient to decide, never alongside other tags. '
         'Do not infer hidden themes from neutral objects or from the context.\n')}

def targets():
    out=[]
    for i,verb in enumerate(('marked the square','moved the folder','counted the lines','opened the drawer')):
        for label,subject in [('first','I'),('second','You'),('third','She'),('mixed','I and you')]:
            out.append(dict(target=f'Q6-{label}-{i}',question='Q6',label=label,text=f'{subject} {verb}.'))
    themes={
     'danger':['The unstable cliff could collapse on the hikers.','The damaged roof could fall on people below.','The exposed live wire could electrocute a passerby.','The thin ice could break beneath the skater.'],
     'care':['The friend gently comforted the distressed visitor.','The parent lovingly reassured the worried child.','The volunteer kindly supported the anxious newcomer.','The neighbor tenderly comforted the upset friend.'],
     'play or humor':['The children played a silly game and laughed.','The comedian told a joke and everyone chuckled.','The friends amused each other with playful riddles.','The clown performed a funny routine for laughing spectators.'],
     'conflict':['The rivals argued angrily with each other.','The two teams fought over their disagreement.','The neighbors quarreled about their dispute.','The opponents exchanged hostile accusations.'],
     'loss or separation':['The traveler grieved after a loved one died.','The widow mourned the death of her spouse.','The friends sadly said their final goodbye forever.','The family wept over the loss of a beloved relative.'],
     'desire':['The couple felt romantic attraction toward each other.','The visitor felt sexual desire for the host.','The two lovers longed romantically for each other.','The suitor was filled with passionate attraction.'],
     'discovery':['The explorer discovered an unknown island.','The researcher uncovered a previously unknown pattern.','The astronomer discovered a new comet.','The investigator found a previously unknown passage.'],
     'status':['The official gained prestige and high social rank.','The award elevated the scholar to an esteemed position.','The leader received an honor conferring great prestige.','The newcomer rose to an elite rank in the hierarchy.'],
     'food or body':['The diner ate bread to satisfy hunger.','The guest drank soup at lunch.','The cook tasted a spoonful of rice.','The baker chewed a biscuit.'],
     'empty':['The rectangle has four straight sides.','The table lists the numbers in ascending order.','The circle is to the left of the triangle.','The letters are in alphabetical order.']}
    for label,texts in themes.items():
        for i,text in enumerate(texts):out.append(dict(target=f'Q10-{label}-{i}',question='Q10',label=[] if label=='empty' else [label],text=text))
    assert len(out)==56 and len({r['text'] for r in out})==56
    return out

def roster():
    Transcriber,_,_,_=lm.engine()
    class Capture:
        model_id='prompt-capture';settings={}
        def complete(self,prompt,schema):
            self.prompt,self.schema=prompt,schema
            return dict(text=json.dumps(dict(answer=self.label)))
    c=Capture();t=Transcriber(c,NoCache());conditions=[]
    for row in targets():
        for context_kind in ('neutral','conflicting'):
            if context_kind=='neutral':context='The table lists three numbers.'
            elif row['question']=='Q6':context='You arranged the sheets.' if row['label'] in ('first','third') else 'She arranged the sheets.'
            else:context='The guest ate a sandwich.' if row['label']!=['food or body'] else 'The friend gently comforted the child.'
            c.label=row['label'];t.ask(row['question'],context=context,text=row['text'],admission_test=True)
            for arm in ('scoped','defined'):
                prompt=SCOPE+(DEFINITIONS[row['question']] if arm=='defined' else '')+c.prompt
                assert len(prompt)<4000
                conditions.append(dict(row,context_kind=context_kind,context=context,arm=arm,prompt=prompt,schema=c.schema))
    out=[];rng=random.Random(151016)
    for model in lm.MODELS:
        for repeat in (0,1):
            order=list(conditions);rng.shuffle(order)
            for r in order:out.append(dict(r,model=model,repeat=repeat,slot=len(out)))
    assert len(out)==896
    return out

def parse(row,response):
    from tompathy_engine.transcribe.runner import validate_answer
    result={k:v for k,v in row.items() if k not in ('prompt','schema','text','context')}
    try:result.update(valid=True,answer=validate_answer(row['question'],json.loads(response['text'])))
    except (ValueError,TypeError):result.update(valid=False,answer=None)
    result['correct']=result['valid'] and result['answer']==row['label']
    return result

def summarize(rows,expected):
    if len(rows)!=len(expected) or len({r['slot'] for r in rows})!=len(expected):raise ValueError('incomplete or duplicate roster')
    expected_by={r['slot']:r for r in expected}
    groups=defaultdict(list);pairs=defaultdict(dict);repeats=defaultdict(dict);contexts=defaultdict(dict)
    for r in rows:
        source=expected_by[r['slot']]
        for key in ('target','question','model','repeat','arm','context_kind','label'):
            if r[key]!=source[key]:raise ValueError('changed row identity')
        if r['correct']!=(r['valid'] and r['answer']==r['label']):raise ValueError('changed score')
        g='|'.join((r['model'],r['question'],json.dumps(r['label']),r['context_kind']))
        groups[g+'|'+r['arm']].append(r)
        pairs[(g,r['target'],r['repeat'])][r['arm']]=r
        repeats[(r['model'],r['target'],r['context_kind'],r['arm'])][r['repeat']]=r
        contexts[(r['model'],r['target'],r['arm'],r['repeat'])][r['context_kind']]=r
    paired={}
    for (g,_,_),v in pairs.items():
        if set(v)!={'scoped','defined'}:raise ValueError('unpaired prompt')
        d=int(v['defined']['correct'])-int(v['scoped']['correct'])
        counts=paired.setdefault(g,dict(improved=0,worsened=0,unchanged=0))
        counts[{1:'improved',0:'unchanged',-1:'worsened'}[d]]+=1
    sig=lambda r:(r['valid'],r['answer'])
    rr={};cc={}
    for (m,t,c,a),v in repeats.items():
        if set(v)!={0,1}:raise ValueError('missing repeat')
        key=m+'|'+expected_by[v[0]['slot']]['question']+'|'+a
        z=rr.setdefault(key,dict(pairs=0,disagree=0));z['pairs']+=1;z['disagree']+=sig(v[0])!=sig(v[1])
    for (m,t,a,rep),v in contexts.items():
        if set(v)!={'neutral','conflicting'}:raise ValueError('missing context')
        key=m+'|'+v['neutral']['question']+'|'+a
        z=cc.setdefault(key,dict(pairs=0,flips=0));z['pairs']+=1;z['flips']+=sig(v['neutral'])!=sig(v['conflicting'])
    return dict(cells={k:dict(attempted=len(v),valid=sum(x['valid'] for x in v),correct=sum(x['correct'] for x in v)) for k,v in sorted(groups.items())},paired=paired,repeat_disagreement=rr,context_flips=cc,diagnostic_only=True,feature_admission=False,scientific_admission=False)

class SlottedBackend(lm.Backend):
    def __init__(self,model,folder,guard):super().__init__(model,folder,guard);self.base=folder;self.slot=None
    def complete(self,prompt,schema):
        self.folder=self.base/f'{self.slot:04d}'
        try:return super().complete(prompt,schema)
        except ValueError as exc:
            if str(exc)!='unfinished or unexpected thinking response':raise
            return dict(text='__invalid_returned_response__')

def replay(root=ROOT):
    plan=read(root/'PLAN.json');check_pins(plan['pins']);done=read(root/'COMPLETE.json')
    if done['plan_sha256']!=filehash(root/'PLAN.json'):raise ValueError('plan changed')
    for rel,h in done['outputs'].items():
        if filehash(root/rel)!=h:raise ValueError('output changed')
    items=read(root/'ITEMS.json')
    if items!=roster():raise ValueError('roster changed')
    outcomes=[]
    for row in items:
        b=lm.Replay(plan['models'][row['model']],root/'calls'/f'{row["slot"]:04d}')
        try:response=b.complete(row['prompt'],row['schema'])
        except ValueError as exc:
            if str(exc)!='unfinished or unexpected thinking response':raise
            response=dict(text='__invalid_returned_response__')
        result=parse(row,response)
        if result!=read(root/'outcomes'/f'{row["slot"]:04d}.json'):raise ValueError('outcome changed')
        outcomes.append(result)
    if summarize(outcomes,items)!=read(root/'SUMMARY.json'):raise ValueError('summary changed')
    if len(list((root/'calls').glob('*/*/REQUEST.json')))!=896:raise ValueError('unaccounted requests')
    return dict(at=now(),status='VERIFIED',calls=896,complete_sha256=filehash(root/'COMPLETE.json'),scientific_admission=False)

def prepare(service_pid):
    limits();require_resources(resource_snapshot())
    if (ROOT/'PLAN.json').exists():raise ValueError('already prepared')
    for model in lm.MODELS.values():lm.inspect(model)
    if (REPO/'results/.literal-cpu.lock').exists():raise ValueError('service leased')
    service=native_identity(service_pid)
    if service is None:raise ValueError('service absent')
    freeze(ROOT/'ITEMS.json',roster())
    sources=[ROOT/'ITEMS.json']+[REPO/p for p in ('runners/next_round/label_contract.py','runners/next_round/literal_models.py','runners/next_round/scope_diagnostic.py','runners/next_round/literal_admission.py','runners/next_round/engine_interface_v2.py','runners/next_round/queue.py','runners/stage14/common.py','runners/stage9/process_identity.py','tests/test_next_round_label_contract.py','docs/design/stage-15/LABEL_CONTRACT_DIAGNOSTIC.md')]
    sources += [lm.CAPSULE/'PIN.json',*[lm.CAPSULE/n for n in read(lm.CAPSULE/'PIN.json')['files']]]
    freeze(ROOT/'PLAN.json',dict(at=now(),models=lm.MODELS,pins=pins(sources),service_native=service,maximum_calls=896,max_wall_seconds=43200,provider_calls=0,scientific_admission=False))

def run(root=ROOT):
    limits();plan=read(root/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    if native_identity(plan['service_native']['pid'])!=plan['service_native']:raise RuntimeError('service drift')
    with (root/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    lease=REPO/'results/.literal-cpu.lock';token=json.dumps(native_identity()).encode()
    fd=os.open(lease,os.O_WRONLY|os.O_CREAT|os.O_EXCL);os.write(fd,token);os.close(fd)
    started=time.time();stop=threading.Event();backend=None;results=[];total=0
    def deadline():
        if stop.wait(plan['max_wall_seconds']):return
        atomic(root/'FAILED.json',dict(status='FAILED',at=now(),reason='wall ceiling; lease retained'));os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (root/'MONITOR_READY.json').exists():
            if time.time()-started>60:raise TimeoutError('monitor absent')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256']!=filehash(root/'OWNER.json'):raise ValueError('monitor mismatch')
        lm.engine()
        items=read(root/'ITEMS.json')
        for model_id,model in plan['models'].items():
            lm.inspect(model)
            def guard():
                check_pins(plan['pins']);resources=resource_snapshot();require_resources(resources)
                if native_identity(plan['service_native']['pid'])!=plan['service_native']:raise RuntimeError('service drift')
                if lease.read_bytes()!=token:raise RuntimeError('lease drift')
                if total+backend.calls>=plan['maximum_calls']:raise RuntimeError('call ceiling')
                atomic(root/'PROGRESS.json',dict(at=now(),model=model_id,completed_calls=total+backend.calls,resources=resources))
            backend=SlottedBackend(model,root/'calls',guard)
            for row in (r for r in items if r['model']==model_id):
                backend.slot=row['slot'];result=parse(row,backend.complete(row['prompt'],row['schema']));results.append(result)
                freeze(root/'outcomes'/f'{row["slot"]:04d}.json',result)
            backend.close();total+=backend.calls
        check_pins(plan['pins'])
        if total!=plan['maximum_calls'] or lease.read_bytes()!=token:raise RuntimeError('endpoint mismatch')
        freeze(root/'SUMMARY.json',summarize(results,items))
        paths=[root/'ITEMS.json',root/'SUMMARY.json',*sorted((root/'outcomes').glob('*.json')),*sorted((root/'calls').rglob('*.json'))]
        lease.unlink()
        freeze(root/'COMPLETE.json',dict(status='COMPLETE',at=now(),calls=total,wall_seconds=time.time()-started,plan_sha256=filehash(root/'PLAN.json'),outputs={p.relative_to(root).as_posix():filehash(p) for p in paths},provider_calls=0,scientific_admission=False,write_through_required=True))
        freeze(root/'REPLAY.json',replay(root))
    except BaseException as exc:
        freeze(root/'FAILED.json',dict(status='FAILED',at=now(),error=str(exc),traceback=traceback.format_exc(),lease_retained=lease.exists()));raise
    finally:stop.set()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','replay']);p.add_argument('--service-pid',type=int);a=p.parse_args()
    if a.action=='prepare':prepare(a.service_pid)
    elif a.action=='run':run()
    else:print(json.dumps(replay()))
