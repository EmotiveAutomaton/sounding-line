"""Chronological profile-feature comparison using the pinned canonical engine.

DESIGN CHECK: LESSONS 3-5 / CONTROLS 1-3 read 2026-10-15.
NULL: constant profile columns cannot distinguish choices; future labels cannot
change earlier predictions. ALTERNATIVE: a planted profile relation is learned,
and donor substitution reverses it. Missing exact scientific witnesses refuse
before human fitting. Constructed software checks are never those witnesses.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'
import argparse,hashlib,re,sys,time,threading,traceback
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from .engine_interface_v2 import CAPSULE,verify as verify_engine
from .queue import require_resources,resource_snapshot
from .statistics import losses
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,digest,limits,now
from runners.stage9.process_identity import native_identity
from runners.stage14_midweek.data import RAW as SOURCE,ACTIONS
from runners.stage14_midweek.baselines import features

ROOT=REPO/'results/phase_2_4_stage_15/raw/profile-features-v1'
PROFILE=REPO/'results/phase_2_4_stage_15/raw/r3-profiles-v7/main'
REPLAY=REPO/'results/phase_2_4_stage_15/raw/phase0-v1/prepared/SESSIONS.json'
ARMS=('baseline','own','donor')


def engine():
    verify_engine();path=str(CAPSULE/'engine')
    if path not in sys.path:sys.path.insert(0,path)
    import tompathy_engine
    if not Path(tompathy_engine.__file__).resolve().is_relative_to(CAPSULE):raise ValueError('wrong engine')
    from tompathy_engine.models.backbone import Backbone,Choice
    from tompathy_engine.admission import implementation_hash
    from tompathy_engine.ledger.schema import schema_hash
    return Backbone,Choice,implementation_hash(),schema_hash()


def profile_vector(statements,dimensions=32):
    x=np.zeros(dimensions)
    for statement in statements:
        for word in re.findall(r'\w+',statement.casefold()):
            x[int.from_bytes(hashlib.sha256(word.encode()).digest()[:8],'big')%dimensions]+=1
    length=np.linalg.norm(x)
    return x/length if length else x


def choice_features(task,profile,n_options=4):
    vector=np.r_[task,profile]
    if vector.ndim!=1 or not np.isfinite(vector).all():raise ValueError('nonfinite feature')
    return np.kron(np.eye(n_options),vector[None,:])


def validate_native(target,raw,config):
    for field in ('writer','prompt','open_at','document','menu','handling'):
        if raw[field]!=target[field]:raise ValueError('native target mapping differs: '+field)
    if raw['resolved_at']<target['open_at']:raise ValueError('reversed source chronology')
    if config['cutoff']>target['open_at']:raise ValueError('profile cutoff after target')
    for field in ('h2','h3'):
        if any(h['resolved_at']>=config['cutoff'] for h in config[field]):raise ValueError('future profile history')


def validate_admission(path,plan):
    receipt=read(path)
    if receipt.get('scope')!='S15-PROFILE-FEATURE-V1' or receipt.get('plan_sha256')!=filehash(ROOT/'PLAN.json'):
        raise ValueError('research admission scope/plan mismatch')
    if receipt.get('implementation_hash')!=plan['implementation_hash'] or receipt.get('ledger_schema_hash')!=plan['ledger_schema_hash']:
        raise ValueError('scientific admission engine mismatch')
    witnesses=receipt.get('witnesses',{})
    if set(witnesses)!={'ghost','native_adapter','holdout_policy'}:raise ValueError('complete scientific witnesses required')
    for kind,witness in witnesses.items():
        p=Path(witness['path']);p=p if p.is_absolute() else REPO/p
        if filehash(p)!=witness['sha256']:raise ValueError('scientific witness changed')
        value=read(p)
        if value.get('status')!='PASS' or value.get('scope')!=kind or value.get('constructed_software_fixture'):
            raise ValueError('witness is not an admitted research record')
        if value.get('implementation_hash')!=plan['implementation_hash']:raise ValueError('witness belongs to another engine')
    return receipt


def prepare():
    limits();require_resources(resource_snapshot())
    if (ROOT/'PLAN.json').exists():raise ValueError('already prepared')
    from .profiles_v7 import replay
    complete=replay('main');landing=read(PROFILE/'LANDED.json')
    if complete['valid']!=complete['attempted'] or complete['valid']!=62:raise ValueError('whole profile main required')
    if not landing['full_write_through'] or landing['complete_sha256']!=filehash(PROFILE/'COMPLETE.json'):
        raise ValueError('complete profile landing required')
    _,_,implementation,schema=engine()
    oldplan=read(REPO/'results/phase_2_4_stage_15/raw/phase0-v1/PLAN.json')
    if oldplan['pins'][REPLAY.relative_to(REPO).as_posix()]!=filehash(REPLAY):raise ValueError('source replay changed')
    training=read(SOURCE/'data-v2/TRAINING.json');profiles=read(PROFILE/'PROFILES.json')
    requests=read(PROFILE/'REQUESTS.json');lookup={(r['writer'],r['arm']):profiles[r['custom_id']] for r in requests}
    source={r['key']:r for s in read(REPLAY) for r in s['rows']}
    targets=[r for r in read(SOURCE/'data-v2/EVALUATOR.json') if not r['pilot']]
    targets.sort(key=lambda r:(r['open_at'],r['key']))
    prepared=[];labels=[]
    for target in targets:
        raw=source[target['key']]
        config=training[target['writer']]
        validate_native(target,raw,config)
        task=features(target,[],False)
        views={'baseline':np.zeros(32)}
        for name,arm in (('own','M1'),('donor','M0')):
            views[name]=profile_vector([p['statement'] for p in lookup[target['writer'],arm]['preferences']])
        prepared.append(dict(key=target['key'],writer=target['writer'],prompt=target['prompt'],
            open_at=target['open_at'],resolved_at=raw['resolved_at'],profile_cutoff=config['cutoff'],
            features={name:choice_features(task,v).tolist() for name,v in views.items()}))
        labels.append(dict(key=target['key'],action=ACTIONS.index(raw['handling'])))
    if len(prepared)!=234 or len({r['writer'] for r in prepared})!=31:raise ValueError('frozen main roster differs')
    freeze(ROOT/'FEATURES.json',prepared);freeze(ROOT/'LABELS.json',labels)
    paths=[REPO/p for p in ('runners/next_round/profile_features.py','runners/next_round/engine_interface_v2.py',
        'runners/next_round/queue.py','runners/next_round/statistics.py','runners/stage14/common.py',
        'runners/stage9/process_identity.py','runners/stage14_midweek/data.py','runners/stage14_midweek/baselines.py',
        'runners/stage14_midweek/analyze_modal.py','tests/test_next_round_profile_features.py',
        'docs/design/stage-15/PROFILE_FEATURE_COMPARISON.md')]
    paths += [REPLAY,ROOT/'FEATURES.json',ROOT/'LABELS.json',CAPSULE/'PIN.json',*[CAPSULE/p for p in read(CAPSULE/'PIN.json')['files']]]
    paths += [p for p in PROFILE.glob('*.json') if p.name not in ('PROGRESS.json','SUPERVISION.json','STATUS.json')]
    paths += list((SOURCE/'data-v2').glob('*.json'))
    from .phase0 import verify_manifest
    verify_manifest(SOURCE/'modal-analysis-v2')
    paths += [SOURCE/'modal-analysis-v2'/n for n in ('PREDICTIONS.json','COMPLETE.json')]
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(paths),arms=list(ARMS),targets=len(prepared),writers=31,
        implementation_hash=implementation,ledger_schema_hash=schema,source_exposed=True,
        max_wall_seconds=43200,provider_calls=0,engine_admission=False,margin=.005))
    freeze(ROOT/'PREPARED.json',dict(at=now(),status='PREPARED',source_mapping=True,chronology_verified=True,
        plan_sha256=filehash(ROOT/'PLAN.json'),scientific_execution=False,
        waiting_for=['relevant Ghost twin','native adapter independent validation','frozen research admission receipt']))
    print('All profile feature views prepared; scientific dispatch awaits exact research witnesses.')


def predict_all(records,labels,guard=lambda _:None):
    Backbone,Choice,_,_=engine();label={r['key']:r['action'] for r in labels}
    ts=lambda value:datetime.fromtimestamp(value/1000,tz=timezone.utc)
    cases={arm:[Choice(r['key'],r['writer'],ts(r['open_at']),ts(r['resolved_at']),
        np.asarray(r['features'][arm]),label[r['key']],r['prompt']) for r in records] for arm in ARMS}
    predictions=[]
    for index,row in enumerate(records):
        guard(dict(target=index,total=len(records)));at=ts(row['open_at']);out={}
        for arm in ARMS:
            fitted=Backbone.fit(cases[arm],until=at,dimensions=len(row['features'][arm][0]))
            if row['key'] in fitted.train_ids:raise ValueError('target entered fit')
            out[arm]=dict(probabilities=fitted.predict(row['writer'],row['features'][arm],at=at).tolist(),
                training_keys=list(fitted.train_ids),cold_start=not fitted.train_ids)
        predictions.append(dict(key=row['key'],writer=row['writer'],prompt=row['prompt'],arms=out))
    return predictions


def run(admission):
    plan=read(ROOT/'PLAN.json');validate_admission(admission,plan);check_pins(plan['pins']);limits()
    require_resources(resource_snapshot())
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(native=native_identity(),at=now(),plan_sha256=filehash(ROOT/'PLAN.json')))
    started=time.time();stop=threading.Event()
    def deadline():
        if stop.wait(plan['max_wall_seconds']):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='finite CPU limit'));os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-started>60:raise TimeoutError('supervision missing')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor mismatch')
        def guard(progress):
            require_resources(resource_snapshot());atomic(ROOT/'PROGRESS.json',dict(at=now(),progress=progress))
        records=read(ROOT/'FEATURES.json');labels=read(ROOT/'LABELS.json');pred=predict_all(records,labels,guard)
        y=np.array([r['action'] for r in labels]);scores={}
        for arm in ARMS:
            b,ll=losses([r['arms'][arm]['probabilities'] for r in pred],y)
            scores[arm]=dict(half_brier=b.tolist(),log_loss=ll.tolist())
        from runners.stage14_midweek.analyze_modal import paired
        comparisons={}
        for rival in ('baseline','donor'):
            comparisons['own_over_'+rival]=paired(records,np.array(scores[rival]['half_brier'])-scores['own']['half_brier'])
            comparisons['own_over_'+rival+'_log_loss']=paired(records,np.array(scores[rival]['log_loss'])-scores['own']['log_loss'])
        legacy=read(SOURCE/'modal-analysis-v2/PREDICTIONS.json')
        for rival in ('B-writer','B-mixlogit'):
            historical=[legacy[r['key']][rival]['scores']['half_brier'] for r in records]
            comparisons['own_over_historical_'+rival]=paired(records,np.array(historical)-scores['own']['half_brier'])
        screen=all(comparisons['own_over_'+a]['interval'][0]>.005 and comparisons['own_over_'+a]['crossed_interval'][0]>.005 for a in ('baseline','donor'))
        freeze(ROOT/'PREDICTIONS.json',pred);freeze(ROOT/'SCORES.json',scores)
        freeze(ROOT/'SUMMARY.json',dict(comparisons=comparisons,margin=.005,exposed=True,
            descriptive_useful_gain_screen=bool(screen),
            cold_starts={a:sum(r['arms'][a]['cold_start'] for r in pred) for a in ARMS},
            engine_admission=False,conditional_nonsimultaneous_intervals=True))
        check_pins(plan['pins'])
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={n:filehash(ROOT/n) for n in ('PREDICTIONS.json','SCORES.json','SUMMARY.json')},
            plan_sha256=filehash(ROOT/'PLAN.json'),provider_calls=0,write_through_required=True,engine_admission=False))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),error=str(exc),traceback=traceback.format_exc()));raise
    finally:stop.set()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);p.add_argument('--admission',type=Path);a=p.parse_args()
    if a.action=='run' and a.admission is None:p.error('scientific research admission is required')
    prepare() if a.action=='prepare' else run(a.admission)
