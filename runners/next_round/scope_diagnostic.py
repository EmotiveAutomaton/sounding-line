"""Frozen target/context diagnostic; separate from canonical admission.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1-3 read 2026-10-15.
NULL: target-only oracle is context invariant; context copying fails discordance.
ALTERNATIVE: explicit scope reduces context interference. Repeat disagreement
is retained. No threshold rescue, partial score, paid call or engine mutation.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'
import argparse,json,random,threading,time,traceback
from collections import defaultdict
from statistics import mean
from .literal_admission import engine,Backend,inspect_service,CAPSULE
from .queue import resource_snapshot,require_resources
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,digest,now,limits
from runners.stage9.process_identity import native_identity

ROOT=REPO/'results/phase_2_4_stage_15/raw/scope-diagnostic-v1'
SCOPE=('For this question, classify only the value of the "text" field. '
       'The "context" field is a separate earlier sentence, not part of the target. '
       'Exclude its grammatical person and theme tags from your answer.\n')


def targets():
    out=[]
    verbs=('marked the square','moved the folder','counted the lines','opened the drawer')
    for j,verb in enumerate(verbs):
        for label,subject in [('first','I'),('second','You'),('third','She'),('mixed','I and you')]:
            # Plural agreement is deliberately avoided by past-tense predicates.
            text=f'{subject} {verb}.'
            match={'first':'We arranged the sheets.','second':'You arranged the sheets.',
                   'third':'They arranged the sheets.','mixed':'We and you arranged the sheets.'}[label]
            conflict='You arranged the sheets.' if label in ('first','third') else 'She arranged the sheets.'
            out.append(dict(id=f'Q6-{label}-{j}',question='Q6',label=label,text=text,matching=match,conflicting=conflict))
    theme_texts={
        'empty':['The line has six marks.','The square is beside the circle.','The page has three columns.','The folder has a blue label.'],
        'food_or_body':['The cook ate the bread.','The child drank the soup.','The diner tasted the rice.','The baker chewed the biscuit.'],
        'danger':['The unstable cliff could collapse at any moment.','The damaged roof could fall on anyone beneath it.','The exposed live wire could electrocute anyone touching it.','The thin ice could break beneath a person.'],
        'care':['The friend gently comforted the upset visitor.','The parent lovingly reassured the worried child.','The volunteer kindly supported the anxious newcomer.','The neighbor tenderly comforted the distressed friend.']}
    contexts={'empty':'The table lists four numbers.','food_or_body':'The guest ate a sandwich.',
              'danger':'The unstable bridge could collapse beneath anyone crossing it.',
              'care':'The caregiver gently comforted the distressed child.'}
    for label,texts in theme_texts.items():
        for j,text in enumerate(texts):
            other='food_or_body' if label in ('empty','care') else 'care'
            out.append(dict(id=f'Q10-{label}-{j}',question='Q10',label=[] if label=='empty' else [label.replace('_',' ')],
                text=text,matching=contexts[label],conflicting=contexts[other]))
    return out


class NoCache:
    def get(self,key):return None
    def put(self,key,value):pass


def conditions():
    Transcriber,_,_,_=engine()
    class Capture:
        model_id=Backend.model_id;settings=Backend.settings
        def complete(self,prompt,schema):
            self.prompt,self.schema=prompt,schema
            return dict(text=json.dumps({'answer':self.label}),logprobs=None)
    capture=Capture();transcriber=Transcriber(capture,NoCache());out=[]
    for target in targets():
        for context in ('absent','matching','conflicting'):
            capture.label=target['label']
            transcriber.ask(target['question'],context='' if context=='absent' else target[context],
                text=target['text'],admission_test=True)
            for arm in ('original','explicit'):
                prompt=('' if arm=='original' else SCOPE)+capture.prompt
                if len(prompt)>3000:raise ValueError('serialized prompt bound')
                out.append(dict(id=target['id']+'-'+context+'-'+arm,target=target['id'],question=target['question'],
                    label=target['label'],context=context,arm=arm,prompt=prompt,schema=capture.schema))
    return out


def roster():
    rows=conditions();rng=random.Random(151015);out=[]
    for repeat in (0,1):
        order=list(rows);rng.shuffle(order)
        start=len(out)
        out.extend(dict(r,repeat=repeat,slot=start+i) for i,r in enumerate(order))
    return out


def summarize(rows):
    groups=defaultdict(list);by_condition=defaultdict(list);by_target=defaultdict(dict)
    for r in rows:
        key='|'.join((r['question'],json.dumps(r['label']),r['context'],r['arm']))
        groups[key].append(r);by_condition[r['id']].append(r)
        by_target[(r['target'],r['arm'],r['repeat'])][r['context']]=r
    cells={k:dict(attempted=len(v),valid=sum(r['valid'] for r in v),correct=sum(r['correct'] for r in v)) for k,v in sorted(groups.items())}
    repeats={}
    for q in ('Q6','Q10'):
        pairs=[v for v in by_condition.values() if v[0]['question']==q]
        if any(len(v)!=2 or {r['repeat'] for r in v}!={0,1} for v in pairs):raise ValueError('incomplete repeat pairs')
        repeats[q]=dict(pairs=len(pairs),disagree=sum((v[0]['valid'],v[0].get('answer'))!=(v[1]['valid'],v[1].get('answer')) for v in pairs))
    effects={}
    for q in ('Q6','Q10'):
        rates={}
        for a in ('original','explicit'):
            for c in ('absent','matching','conflicting'):
                rr=[r for r in rows if r['question']==q and r['arm']==a and r['context']==c]
                rates[a+'|'+c]=mean(r['correct'] for r in rr)
        flips={}
        for a in ('original','explicit'):
            pairs=[v for (t,arm,rep),v in by_target.items() if arm==a and v['absent']['question']==q]
            if any(set(v)!={'absent','matching','conflicting'} for v in pairs):raise ValueError('incomplete contexts')
            flips[a]={c:sum((v['absent']['valid'],v['absent'].get('answer'))!=(v[c]['valid'],v[c].get('answer')) for v in pairs) for c in ('matching','conflicting')}
        interaction=(rates['explicit|conflicting']-rates['original|conflicting'])-(rates['explicit|matching']-rates['original|matching'])
        effects[q]=dict(accuracy=rates,context_flips_from_absent=flips,prompt_by_conflict_difference=interaction)
    return dict(cells=cells,repeat_disagreement=repeats,effects=effects,engine_admission=False,exploratory=True)


class RepeatedBackend(Backend):
    def __init__(self,folder,guard):super().__init__(folder,guard);self.base=folder;self.slot=None
    def complete(self,prompt,schema):
        self.folder=self.base/f'{self.slot:04d}'
        response=super().complete(prompt,schema)
        files=list(self.folder.glob('*/RAW.json'))
        if len(files)!=1:raise ValueError('wire accounting')
        if not 0<read(files[0]).get('prompt_eval_count',0)<1500:raise ValueError('prompt token bound')
        return response


def prepare():
    limits();require_resources(resource_snapshot());inspect_service()
    rows=roster()
    if len(rows)!=384 or len({(r['id'],r['repeat']) for r in rows})!=384:raise ValueError('roster')
    freeze(ROOT/'ITEMS.json',rows)
    sources=[ROOT/'ITEMS.json']+[REPO/n for n in ('runners/next_round/scope_diagnostic.py',
        'runners/next_round/literal_admission.py','runners/next_round/engine_interface_v2.py',
        'runners/next_round/queue.py','runners/stage14/common.py','runners/stage9/process_identity.py',
        'tests/test_next_round_addendum.py','docs/design/stage-15/VALIDITY_EXPLORATION_ADDENDUM.md')]
    sources += [CAPSULE/'PIN.json',*[CAPSULE/n for n in read(CAPSULE/'PIN.json')['files']]]
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(sources),maximum_calls=384,max_wall_seconds=10800,
        engine_admission=False,provider_calls=0,scope='diagnosis only; original disabled questions unchanged'))


def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot());inspect_service()
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    lease=REPO/'results/.literal-cpu.lock';token=json.dumps(native_identity()).encode()
    fd=os.open(lease,os.O_WRONLY|os.O_CREAT|os.O_EXCL);os.write(fd,token);os.close(fd)
    started=time.time();stop=threading.Event();backend=None
    def deadline():
        if stop.wait(plan['max_wall_seconds']):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='wall ceiling; lease retained'));os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-started>60:raise TimeoutError('monitor not registered')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor identity mismatch')
        engine();from tompathy_engine.transcribe.runner import validate_answer
        def guard():
            require_resources(resource_snapshot())
            if backend.calls>=plan['maximum_calls']:raise RuntimeError('call ceiling')
            atomic(ROOT/'PROGRESS.json',dict(at=now(),completed_calls=backend.calls,resources=resource_snapshot()))
        backend=RepeatedBackend(ROOT/'calls',guard);results=[]
        for row in read(ROOT/'ITEMS.json'):
            backend.slot=row['slot'];response=backend.complete(row['prompt'],row['schema'])
            result={k:v for k,v in row.items() if k not in ('prompt','schema')}
            try:result.update(answer=validate_answer(row['question'],json.loads(response['text'])),valid=True)
            except (ValueError,TypeError):result.update(valid=False,answer=None)
            result['correct']=result['valid'] and result['answer']==row['label'];results.append(result)
            freeze(ROOT/'outcomes'/f'{row["slot"]:04d}.json',result)
        backend.close();check_pins(plan['pins'])
        if lease.read_bytes()!=token:raise RuntimeError('lease changed')
        lease.unlink();freeze(ROOT/'SUMMARY.json',summarize(results))
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),wall_seconds=time.time()-started,
            calls=backend.calls,outputs=pins([ROOT/'SUMMARY.json',*sorted((ROOT/'outcomes').glob('*.json'))]),
            outputs_relative_to='repository',plan_sha256=filehash(ROOT/'PLAN.json'),engine_admission=False,provider_calls=0))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),error=str(exc),traceback=traceback.format_exc(),lease_retained=lease.exists()));raise
    finally:stop.set()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args()
    prepare() if a.action=='prepare' else run()
