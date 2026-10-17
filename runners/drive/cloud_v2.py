"""A0 whole known-answer Haiku batteries through the guarded Gear 3 route.

DESIGN CHECK: LESSONS 3-5. NULL: malformed, constant, wrong or truncated answers
fail the original complete-question/per-label gates; failed questions cannot
enter paid annotation. ALTERNATIVE: exact canonical known answers admit only
constructed measurement. Unknown dispatch/usage retains reservation; no retry.
"""
import argparse,json,re,time,traceback
from decimal import Decimal,ROUND_CEILING
from pathlib import Path
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,digest,now,limits
from runners.stage14_midweek.api import request
from runners.next_round.literal_admission import engine,gate_summary
from runners.next_round.literal_models import MemoryCache
from runners.next_round.engine_interface_v2 import CAPSULE
from runners.next_round.queue import resource_snapshot,require_resources
from runners.stage9.process_identity import native_identity
from .budget import reserve,reconcile,ceiling,APPROVAL

ROOT=REPO/'results/phase_2_4_stage_15/raw/drive-a0-v2'
MODEL='claude-haiku-5-5'
QUESTIONS=('Q1','Q3','Q4','Q5','Q6','Q7','Q8','Q9','Q10')
SETTINGS=dict(max_tokens=32,thinking={'type':'disabled'},transport='anthropic-batch',prompt='canonical-82789fdb50d9',grammar='provider-no-array-maxitems-v2')


def params(prompt,schema):
    # The provider grammar excludes uniqueItems and maxItems; the canonical parser still
    # enforces uniqueness. No scientific answer contract is relaxed.
    schema=json.loads(json.dumps(schema))
    if schema['properties']['answer'].get('type')=='array':
        schema['properties']['answer'].pop('uniqueItems',None)
        schema['properties']['answer'].pop('maxItems',None)
    return dict(model=MODEL,max_tokens=32,thinking={'type':'disabled'},
        messages=[dict(role='user',content=prompt)],output_config={'format':{'type':'json_schema','schema':schema}})


class Collect:
    model_id=MODEL
    settings=SETTINGS
    def __init__(self):self.rows=[];self.expected=None;self.question=None
    def complete(self,prompt,schema):
        wire=params(prompt,schema);ident=digest(wire)
        self.rows.append(dict(custom_id=ident,question=self.question,params=wire))
        return dict(text=json.dumps({'answer':self.expected}),logprobs=None)


def prepare():
    if (ROOT/'PLAN.json').exists():raise ValueError('already prepared; retrieve existing attempt')
    limits();require_resources(resource_snapshot());ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'PREPARE.claim').open('x',encoding='utf8') as stream:stream.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),stage='counting before dispatch'))
    Transcriber,_,constructed,_=engine();backend=Collect();tr=Transcriber(backend,MemoryCache());items={}
    for q in QUESTIONS:
        items[q]=constructed(q);backend.question=q
        for item in items[q]:
            backend.expected=item['expected']
            tr.ask(q,context=item['context'],text=item['text'],before=item.get('before'),admission_test=True)
    rows=backend.rows
    if len(rows)!=1800 or len({r['custom_id'] for r in rows})!=1800:raise ValueError('canonical full battery coverage differs')
    freeze(ROOT/'ITEMS.json',items);freeze(ROOT/'REQUESTS.json',rows)
    access=json.loads(request('/v1/models/'+MODEL));freeze(ROOT/'ACCESS.json',dict(at=time.time(),model=access))
    counts={};old=REPO/'results/phase_2_4_stage_15/raw/drive-a0-v1'
    previous={r['custom_id']:r for r in read(old/'REQUESTS.json')}
    reuse={};prepared_at=time.time()
    freeze(ROOT/'PREPARE_PINS.json',pins([REPO/'runners/drive/cloud_v2.py',REPO/'runners/drive/budget.py',REPO/'runners/gear3.py',ROOT/'REQUESTS.json',old/'REQUESTS.json',old/'FAILED.json']))
    for i,row in enumerate(rows):
        require_resources(resource_snapshot())
        body={k:v for k,v in row['params'].items() if k!='max_tokens'}
        if time.time()-prepared_at>7200:raise TimeoutError('bounded token-count preparation')
        prior=old/'counts'/(row['custom_id']+'.json')
        if row['custom_id'] in previous and previous[row['custom_id']]['params']==row['params'] and prior.exists() and time.time()-prior.stat().st_mtime<86400:
            counts[row['custom_id']]=read(prior)['input_tokens'];reuse[str(prior.relative_to(REPO)).replace('\\','/')]=filehash(prior)
        else:counts[row['custom_id']]=json.loads(request('/v1/messages/count_tokens',body))['input_tokens']
        atomic(ROOT/'COUNT_PROGRESS.json',dict(at=now(),done=i+1,total=len(rows)))
        freeze(ROOT/'counts'/(row['custom_id']+'.json'),dict(input_tokens=counts[row['custom_id']]))
    freeze(ROOT/'REUSED_COUNTS.json',reuse);check_pins(read(ROOT/'PREPARE_PINS.json'));freeze(ROOT/'COUNTS.json',counts);cents=ceiling(rows,counts)
    if cents>100:raise ValueError('A0 reservation exceeds $1; no dispatch')
    src=[REPO/p for p in ('runners/drive/cloud_v2.py','runners/drive/budget.py','runners/gear3.py',
        'runners/stage14_midweek/api.py','runners/stage14/common.py','runners/next_round/literal_admission.py',
        'runners/next_round/literal_models.py','runners/next_round/engine_interface_v2.py','runners/next_round/queue.py',
        'runners/stage9/process_identity.py','soundingline/probe/client.py','tests/test_drive_cloud_v2.py')]
    src += [APPROVAL,*[ROOT/p for p in ('ITEMS.json','REQUESTS.json','COUNTS.json','ACCESS.json','PREPARE_PINS.json','REUSED_COUNTS.json')],
            CAPSULE/'PIN.json',*[CAPSULE/n for n in read(CAPSULE/'PIN.json')['files']]]
    freeze(ROOT/'PLAN.json',dict(at=time.time(),pins=pins(src),questions=list(QUESTIONS),requests=len(rows),
        reserved_cents=cents,reused_counts=len(reuse),model=MODEL,settings=SETTINGS,max_wait_seconds=90000,scientific_admission=False))
    return dict(status='PREPARED',requests=len(rows),reserved_cents=cents)


def submit():
    plan=read(ROOT/'PLAN.json');check_pins(plan['pins'])
    if time.time()-plan['at']>86400:raise ValueError('stale counted plan')
    with (ROOT/'SUBMIT.claim').open('x',encoding='utf8') as stream:stream.write(now()+'\n')
    reservation=reserve('api-drive-a0-v2','A0',plan['reserved_cents'],filehash(ROOT/'PLAN.json'),'anthropic')
    freeze(ROOT/'RESERVATION.json',reservation)
    wire=dict(requests=[{k:r[k] for k in ('custom_id','params')} for r in read(ROOT/'REQUESTS.json')]);freeze(ROOT/'WIRE.json',wire)
    try:
        raw=request('/v1/messages/batches',wire);(ROOT/'SUBMIT_RESPONSE.json').write_bytes(raw);batch=json.loads(raw)
        if not re.fullmatch(r'[a-zA-Z0-9_-]+',batch['id']):raise ValueError('invalid batch identity')
        freeze(ROOT/'SUBMITTED.json',dict(at=now(),status='SUBMITTED',batch_id=batch['id'],reservation_sha256=filehash(ROOT/'RESERVATION.json')))
    except BaseException as exc:
        freeze(ROOT/'UNKNOWN.json',dict(status='UNKNOWN',at=now(),reason=type(exc).__name__,reservation_retained=True));raise


class Replay:
    model_id=MODEL
    settings=SETTINGS
    def __init__(self,results):self.results=results;self.seen=set()
    def complete(self,prompt,schema):
        ident=digest(params(prompt,schema));self.seen.add(ident);r=self.results[ident]['result']
        if r['type']!='succeeded':raise ValueError('provider item failed')
        msg=r['message']
        if msg['model']!=MODEL or msg.get('stop_reason')!='end_turn':raise ValueError('model drift or output truncation')
        if any(c['type']!='text' for c in msg['content']):raise ValueError('unexpected nonliteral content')
        return dict(text=''.join(c['text'] for c in msg['content']),logprobs=None)


def replay():
    plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);rows=read(ROOT/'REQUESTS.json')
    results=[json.loads(line) for line in (ROOT/'RESULTS.jsonl').read_text(encoding='utf8').splitlines()]
    by={r['custom_id']:r for r in results}
    if len(by)!=len(results) or set(by)!={r['custom_id'] for r in rows}:raise ValueError('provider coverage differs')
    Transcriber,battery,constructed,_=engine();summaries={};all_seen=set()
    for q in QUESTIONS:
        items=read(ROOT/'ITEMS.json')[q]
        if items!=constructed(q):raise ValueError('constructed roster changed')
        backend=Replay(by);canonical=battery(Transcriber(backend,MemoryCache()),q,items)
        summaries[q]=gate_summary(canonical,items);all_seen.update(backend.seen)
    if all_seen!=set(by):raise ValueError('unreplayed provider rows')
    cost=Decimal(0);usage_complete=True
    for r in results:
        if r['result']['type']!='succeeded':usage_complete=False;continue
        u=r['result']['message']['usage']
        if any(type(u.get(k))!=int or u[k]<0 for k in ('input_tokens','output_tokens')):raise ValueError('invalid usage')
        if u.get('cache_creation_input_tokens',0) or u.get('cache_read_input_tokens',0):usage_complete=False
        cost+=(Decimal('.05')*u['input_tokens']+Decimal('.25')*u['output_tokens'])/10000
    freeze(ROOT/'SUMMARY.json',summaries)
    receipt=dict(status='COMPLETE',at=now(),questions=len(summaries),requests=len(results),
        outputs={p:filehash(ROOT/p) for p in ('PLAN.json','REQUESTS.json','COUNTS.json','ITEMS.json','SUBMITTED.json','STATUS.json','RESULTS.jsonl','SUMMARY.json')},
        usage_complete=usage_complete,measured_token_cents=int(cost.to_integral_value(rounding=ROUND_CEILING)),
        constructed_only=True,native_admission=False,scientific_admission=False,write_through_required=True)
    # Idempotent replay preserves original terminal timestamp.
    if (ROOT/'COMPLETE.json').exists():receipt['at']=read(ROOT/'COMPLETE.json')['at']
    freeze(ROOT/'COMPLETE.json',receipt)
    if usage_complete:
        status=read(ROOT/'STATUS.json')
        if status.get('processing_status')!='ended' or status['id']!=read(ROOT/'SUBMITTED.json')['batch_id']:raise ValueError('ended exact batch required')
        reconcile('api-drive-a0-v2',receipt['measured_token_cents'],filehash(ROOT/'COMPLETE.json'))
    return dict(status='COMPLETE',whole_questions=len(summaries),usage_complete=usage_complete)


def retrieve():
    batch=read(ROOT/'SUBMITTED.json')['batch_id'];status=json.loads(request('/v1/messages/batches/'+batch));atomic(ROOT/'STATUS.json',status)
    if status.get('id')!=batch:raise ValueError('batch status identity differs')
    if status['processing_status']!='ended':return dict(status=status['processing_status'])
    if not (ROOT/'RESULTS.jsonl').exists():(ROOT/'RESULTS.jsonl').write_bytes(request('/v1/messages/batches/'+batch+'/results'))
    return replay()


def run():
    try:
        result=prepare();print(json.dumps(result),flush=True)
        # The parent registers native disappearance plus both whole-job terminals.
        started=time.time()
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-started>90:raise TimeoutError('monitor handshake absent')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor identity differs')
        submit();started=time.time()
        while time.time()-started<90000:
            result=retrieve()
            if result['status']=='COMPLETE':print(json.dumps(result));return
            time.sleep(60)  # inexpensive service wait, never an agent polling turn
        raise TimeoutError('bounded batch wait ended; retrieve existing batch only')
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason=str(exc),traceback=traceback.format_exc(),
            reservation_retained=(ROOT/'RESERVATION.json').exists()))
        raise


def cli(argv):
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['run','prepare','submit','retrieve','replay']);args=ap.parse_args(argv)
    result=globals()[args.action]()
    if result is not None:print(json.dumps(result))
