"""Verified historical projection, immutable balanced cohort, CPU controls.

DESIGN CHECK: known-answer terminal replay gates both neural and cheap readers.
NULL: a changed source, prior label mismatch or crossed split blocks admission.
ALTERNATIVE: exact source-consistent projection preserves the existing eligible
partition. All exclusions remain explicit. Context screening precedes selection
and examines both method prompts without using outcomes or response quality.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import time
from runners.stage9.coauthor import raw_inputs, replay as old_replay
from runners.stage9.coauthor_cases import inputs
from .replay import replay
from .core import *


def balanced(rows, limit, cap):
    by=defaultdict(list)
    for row in sorted(rows,key=lambda r:digest(['stage11-cohort-1',r['key']])): by[row['writer']].append(row)
    order=sorted(by,key=lambda w:digest(['stage11-writer-1',w]))
    # Round robin writer components; source hash order within each writer.
    return [by[w][i] for i in range(cap) for w in order if len(by[w])>i][:limit]


def prepare(root=PRIVATE):
    if (root/'PREPARED.json').exists():
        saved=read(root/'PREPARED.json')
        if digest(read(root/'COHORT.json'))!=saved['cohort_digest']: raise ValueError('cohort changed')
        return saved
    start=time.perf_counter()
    # Thread creation is a conservative immutable start before the initial reading.
    began=datetime.fromtimestamp(int('01a0b4eb5ab6',16)/1000,timezone.utc)
    contract=dict(started_at=began.isoformat(),started_basis='current operating thread creation, preceding first work',
                  admissions_end=min(began+timedelta(hours=46),datetime(2026,9,20,13,tzinfo=timezone.utc)).isoformat(),
                  report_due=min(began+timedelta(hours=48),datetime(2026,9,20,15,tzinfo=timezone.utc)).isoformat(),
                  gpu_seconds=14400,total_calls=256,evaluation_calls=192,development_calls=32,pilot_calls=8,
                  transport_recovery_calls=24,gear=2,cpu='boost off, 90 percent maximum',
                  extension_rule='frozen remaining writers/episodes, complete matched blocks if cumulative service and elapsed caps permit; no outcome criterion')
    freeze(root/'CONTRACT.json',contract)
    native,metadata=inputs('scientific'); paths,meta,identity=raw_inputs()
    lookup={digest({'coauthor-session':p.stem}):p for p in paths}
    projected={}; exclusions=[]; source_audit=[]
    for key in sorted({r['session'] for lane in native.values() for r in lane}):
        path=lookup[key];lines=path.read_text(encoding='utf-8').splitlines()
        newer=replay(lines); older=old_replay(lines)
        if not newer['reconstructed'] or newer['final_document']!=older['final_document']:
            raise ValueError('historical adapter differs from native replay')
        if [(r['ordinal'],r['decision'],r['usable']) for r in newer['events']] != [(r['ordinal'],r['decision'],r['usable']) for r in older['events']]:
            raise ValueError('native handling changed')
        projected[key]={r['ordinal']:r for r in newer['events']}
        source_audit.append(dict(session=key,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                 events=newer['events_count'],agreement=True))
    cohort={}
    for lane,rows in native.items():
        eligible=[]
        for row in rows:
            event=projected[row['session']][row['ordinal']]
            if not event['usable'] or event['decision']!=row['truth'] or event['document']!=row['views']['artifact']['document']:
                raise ValueError('prepared/native identity mismatch')
            views={v:evidence(event,v) for v in VIEWS}
            try:
                for v in VIEWS:
                    for arm in ARMS: request_for(views[v],arm)
            except ValueError as exc:
                exclusions.append(dict(key=row['key'],lane=lane,reason=str(exc)));continue
            eligible.append(dict(key=row['key'],writer=row['unit'],prompt=row['stimulus'],session=row['session'],
                                 domain=row['domain'],ordinal=row['ordinal'],truth=row['truth'],views=views,event=event))
        chosen=balanced(eligible,96 if lane=='train' else 8 if lane=='development' else 48,
                        96 if lane=='train' else 8 if lane=='development' else 3)
        kept={r['key'] for r in chosen}
        exclusions += [dict(key=r['key'],lane=lane,reason='frozen balanced sample limit') for r in eligible if r['key'] not in kept]
        for i,r in enumerate(chosen): r['tranche']='initial' if lane!='evaluation' or i<24 else 'extension'
        cohort[lane]=chosen
    if not all(cohort.values()): raise ValueError('required retrospective partition empty')
    for a,b in [('train','development'),('train','evaluation'),('development','evaluation')]:
        for factor in ('writer','prompt','session'):
            if {r[factor] for r in cohort[a]} & {r[factor] for r in cohort[b]}: raise ValueError('partition crossing')
    freeze(root/'SOURCE.json',dict(metadata=metadata,identity=identity,audit=source_audit,exclusions=exclusions))
    freeze(root/'COHORT.json',cohort)
    model=fit(cohort['train']);freeze(root/'BASELINES.json',model)
    result=dict(status='PREPARED',cohort_digest=digest(cohort),baseline_digest=digest(model),
                counts={lane:dict(episodes=len(rows),writers=len({r['writer'] for r in rows}),
                                 domains=dict(Counter(r['domain'] for r in rows))) for lane,rows in cohort.items()},
                source_sessions=len(source_audit),context_exclusions=sum(r['reason']=='declared input ceiling exceeded' for r in exclusions),
                cpu_seconds=time.perf_counter()-start,
                validity='native labels and final-document agreement; no independent real final-document reference',
                exposure='historically exposed descriptive data')
    freeze(root/'PREPARED.json',result)
    return result
