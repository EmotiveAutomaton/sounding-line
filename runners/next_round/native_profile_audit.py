"""Source-bound native mapping audit; no human prediction or inference calls.

DESIGN CHECK: LESSONS 2-5 / CONTROLS 1-3 read 2026-10-15.
NULL: altered identity/action/menu/text/time or future history refuses.
ALTERNATIVE: the whole native source mapping agrees. Missing rows count as faults.
This is mapping evidence, not an independent mechanism or fresh holdout witness.
"""
import argparse,json,os,sys,time,threading,traceback
from pathlib import Path
from .engine_interface_v2 import CAPSULE,verify,run as engine_run
from .queue import resource_snapshot,require_resources
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,now,limits
from runners.stage9.process_identity import native_identity

ROOT=REPO/'results/phase_2_4_stage_15/raw/native-profile-audit-v1'
PROFILE=REPO/'results/phase_2_4_stage_15/raw/profile-features-v1'
SOURCE=REPO/'results/gear3/G3-S14-MAKER-1/raw/data-v2'
SESSIONS=REPO/'results/phase_2_4_stage_15/raw/phase0-v1/prepared/SESSIONS.json'
ROSTER=REPO/'results/phase_2_4_stage_14/raw/jobs/H01-replay-census-v1/ROSTER.json'

def chronology(targets,training,source):
    for t in targets:
        c=training[t['writer']]
        if c['cutoff']>t['open_at']:raise ValueError('cutoff after target')
        for arm in ('h2','h3'):
            for h in c[arm]:
                r=source[h['key']]
                if h['key']==t['key'] or r['resolved_at']>=c['cutoff']:raise ValueError('target/future profile history')
                for key in ('writer','prompt','open_at','resolved_at','handling','menu','document','ordinal','session'):
                    if h[key]!=r[key]:raise ValueError('history source mapping differs: '+key)

def prepare():
    if (ROOT/'PLAN.json').exists():raise ValueError('already prepared')
    verify();plan=read(PROFILE/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    source={r['key']:r for s in read(SESSIONS) for r in s['rows']}
    training=read(SOURCE/'TRAINING.json');targets=read(PROFILE/'FEATURES.json');chronology(targets,training,source)
    expected={t['key']:source[t['key']] for t in targets}
    for w in {t['writer'] for t in targets}:
        for arm in ('h2','h3'):
            for h in training[w][arm]:expected[h['key']]=source[h['key']]
    sessions=sorted({r['session'] for r in expected.values()})
    roster={s['session']:s for s in read(ROSTER)}
    needed=[roster[s] for s in sessions]
    for s in needed:
        if filehash(REPO/s['path'])!=s['source_sha256']:raise ValueError('native source changed')
    freeze(ROOT/'EXPECTED.json',list(expected.values()));freeze(ROOT/'ROSTER.json',needed)
    sources=[ROOT/'EXPECTED.json',ROOT/'ROSTER.json',SESSIONS,ROSTER,PROFILE/'PLAN.json',PROFILE/'FEATURES.json',PROFILE/'LABELS.json',SOURCE/'TRAINING.json',SOURCE/'EVALUATOR.json',
        REPO/'runners/next_round/native_profile_audit.py',REPO/'tests/test_native_profile_audit.py',
        REPO/'docs/design/stage-15/NATIVE_PROFILE_VALIDATION.md']
    sources += [REPO/s['path'] for s in needed]+[CAPSULE/'PIN.json',*[CAPSULE/n for n in read(CAPSULE/'PIN.json')['files']]]
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(sources),sessions=sessions,targets=len(targets),records=len(expected),
        implementation_hash=plan['implementation_hash'],ledger_schema_hash=plan['ledger_schema_hash'],
        profile_plan_sha256=filehash(PROFILE/'PLAN.json'),max_wall_seconds=7200,provider_calls=0,scientific_admission=False))
    freeze(ROOT/'HOLDOUT_POLICY.json',dict(status='PASS',scope='holdout_policy',at=now(),
        implementation_hash=plan['implementation_hash'],ledger_schema_hash=plan['ledger_schema_hash'],
        plan_sha256=filehash(PROFILE/'PLAN.json'),policy_sha256=filehash(REPO/'docs/design/stage-15/NATIVE_PROFILE_VALIDATION.md'),
        source_exposed=True,targets=len(targets),arms=plan['arms'],source_chronology_checked=True,
        optional_stopping=False,confirmatory=False,conditional_nonsimultaneous_intervals=True,
        constructed_software_fixture=False,engine_admission=False))
    print(json.dumps(dict(prepared=True,sessions=len(sessions),source_records=len(expected),targets=len(targets))))

CHILD='''import json,hashlib
from datetime import datetime
from pathlib import Path
from tompathy_engine.adapters.coauthor import compile_session
from tompathy_engine.ledger.store import Ledger
from tompathy_engine.ledger.schema import Decision
source,destination,meta=Path(sys.argv[1]),Path(sys.argv[2]),json.loads(sys.argv[3])
if hashlib.sha256(source.read_bytes()).hexdigest()!=meta['source_sha256']:raise ValueError('source drift')
events=[json.loads(s) for s in source.read_text(encoding='utf8').splitlines()]
ledger=Ledger(destination/'ledger')
rows,provenance,excluded=compile_session(events,source_id=source.stem,writer=meta['writer'],prompt='',prompt_id=meta['prompt'],source_hash=meta['source_sha256'],ledger=ledger)
out=[]
for d in rows:
    if not isinstance(d,Decision):continue
    out.append(dict(ordinal=d.context['source_ordinal'],handling=d.action,open_at=d.t_open.timestamp()*1000,resolved_at=d.t_resolve.timestamp()*1000,
        menu=[ledger.get_text(o.content_ref) for o in d.options if o.origin=='ai'],document=ledger.get_text(d.context['document_ref']),
        maker_id=d.maker_id,prompt=d.context['prompt_id']))
with (destination/'NATIVE.json').open('x',encoding='utf8') as f:json.dump(dict(rows=out,excluded=excluded),f,ensure_ascii=False,sort_keys=True)
print(json.dumps(dict(decisions=len(out),excluded=len(excluded))))
'''

def compare(expected,native):
    by={r['ordinal']:r for r in native};faults=[]
    if len(by)!=len(native):raise ValueError('duplicate native ordinals')
    for r in expected:
        got=by.get(r['ordinal'])
        if got is None:faults.append(dict(key=r['key'],field='missing native decision'));continue
        for field in ('handling','menu','document','prompt'):
            if r[field]!=got[field]:faults.append(dict(key=r['key'],field=field))
        for field in ('open_at','resolved_at'):
            if abs(r[field]-got[field])>.001:faults.append(dict(key=r['key'],field=field))
    return faults

def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    started=time.time();stop=threading.Event()
    def deadline():
        if stop.wait(plan['max_wall_seconds']):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='finite audit wall ceiling'));os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-started>60:raise TimeoutError('monitor missing')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor mismatch')
        expected=read(ROOT/'EXPECTED.json');faults=[];census=[]
        for index,s in enumerate(read(ROOT/'ROSTER.json')):
            require_resources(resource_snapshot());destination=ROOT/'sessions'/s['session'];destination.mkdir(parents=True,exist_ok=False)
            atomic(ROOT/'PROGRESS.json',dict(at=now(),completed_sessions=index,total_sessions=len(plan['sessions'])))
            outcome=engine_run(CHILD,[REPO/s['path'],destination,json.dumps(s)])
            (destination/'stdout.log').write_text(outcome.stdout,encoding='utf8',newline='\n')
            native=read(destination/'NATIVE.json');wanted=[r for r in expected if r['session']==s['session']]
            faults.extend(compare(wanted,native['rows']))
            census.append(dict(session=s['session'],needed=len(wanted),native=len(native['rows']),excluded=len(native['excluded'])))
        check_pins(plan['pins'])
        freeze(ROOT/'DETAILS.json',dict(faults=faults,census=census))
        freeze(ROOT/'NATIVE_ADAPTER.json',dict(status='FAIL' if faults else 'PASS',scope='native_adapter',at=now(),
            implementation_hash=plan['implementation_hash'],ledger_schema_hash=plan['ledger_schema_hash'],
            plan_sha256=plan['profile_plan_sha256'],records=len(expected),sessions=len(census),mismatches=len(faults),
            constructed_software_fixture=False,shared_porting_ancestor=True,engine_admission=False))
        outputs={p.relative_to(ROOT).as_posix():filehash(p) for p in ROOT.rglob('*') if p.is_file() and p.name in ('NATIVE.json','NATIVE_ADAPTER.json','DETAILS.json','HOLDOUT_POLICY.json','EXPECTED.json','ROSTER.json')}
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs=outputs,plan_sha256=filehash(ROOT/'PLAN.json'),
            provider_calls=0,scientific_admission=False,write_through_required=True))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),error=str(exc),traceback=traceback.format_exc()));raise
    finally:stop.set()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args()
    prepare() if a.action=='prepare' else run()
