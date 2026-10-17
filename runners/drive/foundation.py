"""Finite P2/S0 preparation with canonical source equality and monitor handshake.

DESIGN CHECK: LESSONS 3-5 read 2026-10-16. NULL: changed roster, bad chronology,
replay mismatch, missing labels or resource floors stop without publishing a
reference. ALTERNATIVE: canonical source equality and aggregate conservation
produce authenticated descriptive inputs. One attempt; no auto retry or scoring.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '1'
import argparse, csv, json, sys, threading, time, traceback
from collections import Counter
from pathlib import Path
import numpy as np
from runners.stage14.common import REPO, read, freeze, atomic, pins, check_pins, filehash, digest, now, limits
from runners.stage9.common import digest as legacy_digest
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import resource_snapshot, require_resources
from .timeline import rebuild

ROOT = REPO/'results/phase_2_4_stage_15/raw/drive-foundation-v1'
PREPARED = REPO/'results/phase_2_4_stage_15/raw/phase0-v1/prepared'
DICES = REPO/'results/phase_2_4_stage_15/raw/intake-v2/dices350/source.csv'
ROSTER = REPO/'results/phase_2_4_stage_14/raw/jobs/H01-replay-census-v1/ROSTER.json'
ACTIONS = ('accept','edit','dismiss','ignore')


def quantiles(values):
    a = np.asarray(values, float)
    if len(a)==0 or not np.isfinite(a).all() or np.any(a<0): raise ValueError('invalid nonnegative empirical values')
    p = [0,.01,.05,.1,.25,.5,.75,.9,.95,.99,1]
    return dict(probabilities=p, values=np.quantile(a,p).tolist())


def split_roster(sessions):
    """Freeze acquisition separately; no future session can enter earlier history."""
    writers = sorted({s['writer'] for s in sessions}); assignments=[]; excluded=[]
    for w in writers:
        ss=sorted((s for s in sessions if s['writer']==w),key=lambda s:(s['timestamp'],s['session']))
        a,b=int(.6*len(ss)),int(.8*len(ss))
        if a<3 or b-a<1 or len(ss)-b<1:
            excluded.append(dict(writer=w,reason='fewer than 3/1/1 chronological sessions'));continue
        for i,s in enumerate(ss):
            assignments.append(dict(session=s['session'],writer=w,partition='train' if i<a else 'calibration' if i<b else 'test',
                timestamp=s['timestamp'],end_at=s['end_at'],rows=len(s['rows']),
                eligible_history=[t['session'] for t in ss[:i] if t['end_at']<s['timestamp']]))
    return dict(assignments=assignments,excluded=excluded,rule='writer chronological 60/20/20; at least 3/1/1; strict ended history',
                historical_exposure=True,unseen_confirmation=False)


def prepare():
    if (ROOT/'PLAN.json').exists(): raise ValueError('already prepared; inspect, do not replace')
    limits(); require_resources(resource_snapshot())
    src=[REPO/p for p in ('runners/drive/foundation.py','runners/drive/timeline.py','runners/drive/statistics.py',
        'runners/stage9/coauthor.py','runners/stage9/common.py','runners/stage9/process_identity.py',
        'runners/stage14/common.py','runners/next_round/queue.py','tests/test_drive.py',
        'docs/design/stage-15/drive/EXECUTION.md','docs/design/stage-15/drive/PACKET.md')]
    src += [PREPARED/p for p in ('SESSIONS.json','SOURCE_PINS.json','CENSUS.json','EXCLUSIONS.json')]
    src += [DICES, ROSTER, REPO/'results/phase_2_4_stage_9/intake/COAUTHOR_TASK_SOURCE.json']
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(src),tasks=['P2','S0-T1','S0-T4','P4-roster'],
        max_wall_seconds=14400,max_output_bytes=8*1024**3,provider_calls=0,model_calls=0,
        approval_sha256=filehash(REPO/'.agent-state/drive-20261016/APPROVAL.json'),scientific_admission=False))
    print('Prepared finite foundation; no dataset processed yet.')


def t4(source):
    by_rater,by_item,counts=Counter(),Counter(),Counter(); pairs=set()
    with source.open(encoding='utf8',newline='') as stream:
        for row in csv.DictReader(stream):
            label=row['Q_overall']
            if label not in ('Yes','No','Unsure'):raise ValueError('invalid nominal rating')
            key=(row['rater_id'],row['item_id'])
            if key in pairs:raise ValueError('duplicate rater/item')
            pairs.add(key);by_rater[key[0]]+=1;by_item[key[1]]+=1;counts[label]+=1
    if (len(by_rater),len(by_item),len(pairs))!=(123,350,43050):raise ValueError('released complete panel changed')
    return dict(raters=len(by_rater),items=len(by_item),ratings_per_rater=sorted(by_rater.values()),
        raters_per_item=sorted(by_item.values()),rating_semantics='nominal_yes_no_unsure',
        rating_marginals=[counts[k]/len(pairs) for k in ('Yes','No','Unsure')]),dict(target='Q_overall',
        label_order=['Yes','No','Unsure'],ratings=len(pairs),counts=dict(counts),
        sensitivity_104='BLOCKED: actual paper quality-exclusion roster must be pinned; no invented subset')


def compute(root, guard):
    sessions=read(PREPARED/'SESSIONS.json'); source_pins=read(PREPARED/'SOURCE_PINS.json')
    guard('source_integrity',0);check_pins(source_pins)
    roster={s['session']:s for s in read(ROSTER)}
    if len(sessions)!=1399 or len({s['writer'] for s in sessions})!=61:raise ValueError('Phase 0 roster changed')
    freeze(root/'SPLITS.json',split_roster(sessions))
    writer_sessions,writer_records,menus,handling,timing,origins=Counter(),Counter(),Counter(),Counter(),Counter(),Counter()
    latencies=[];keystrokes=[];records=[];output_bytes=0;edit_count=delta_count=0
    for index,s in enumerate(sessions):
        guard('timeline',dict(done=index,total=len(sessions)))
        meta=roster[s['session']];raw=REPO/meta['path']
        if filehash(raw)!=meta['source_sha256']:raise ValueError('source changed')
        events=[json.loads(line) for line in raw.read_text(encoding='utf8').splitlines()]
        out=rebuild(events,s['rows'])
        legacy=REPO/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(legacy_digest({'coauthor-session':raw.stem})+'.json')
        saved=read(legacy)
        if not saved['usable'] or saved['final_document']!=out['final_document']:raise ValueError('canonical final replay differs')
        expected={r['ordinal']:r['decision'] for r in saved['events'] if r['usable']}
        if {r['ordinal']:r['handling'] for r in out['decisions']}!=expected:raise ValueError('canonical decision set differs')
        out.update(session=s['session'],writer=s['writer'],prompt=s['prompt'],source_sha256=meta['source_sha256'])
        dest=root/'sessions'/(s['session']+'.json');freeze(dest,out);output_bytes+=dest.stat().st_size
        if output_bytes>8*1024**3:raise ValueError('output byte ceiling')
        writer_sessions[s['writer']]+=1;writer_records[s['writer']]+=len(out['decisions'])
        delta_count+=len(out['deltas']);edit_count+=len(out['edits'])
        for span in out['final_spans']:origins[span['origin']]+=span['end_utf16']-span['start_utf16']
        for row in out['decisions']:
            menus[row['menu_size']]+=1;handling[row['handling']]+=1;timing[row['latency_kind']]+=1
            latencies.append(row['latency_seconds']);keystrokes.append(row['typed_since_previous_decision'])
        records.append(dict(session=s['session'],writer=s['writer'],file=str(dest.relative_to(root)).replace('\\','/'),sha256=filehash(dest)))
    freeze(root/'SESSION_INDEX.json',records)
    revision=read(REPO/'results/phase_2_4_stage_9/intake/COAUTHOR_TASK_SOURCE.json')['revision']['sha']
    n=sum(handling.values());ww=sorted(writer_sessions)
    agg=dict(makers=len(ww),sessions=len(sessions),decisions=n,records_per_maker=[writer_records[w] for w in ww],
        sessions_per_maker=[writer_sessions[w] for w in ww],options_per_decision={str(k):v for k,v in sorted(menus.items()) if k>=2},
        latency_quantiles_s=quantiles(latencies),keystroke_quantiles=quantiles(keystrokes),handling_marginals=[handling[a]/n for a in ACTIONS])
    note=dict(handling_order=list(ACTIONS),true_menu_histogram={str(k):v for k,v in sorted(menus.items())},
        timing_counts=dict(timing),latency_convention='observed last select/close; ignore first user-insert proxy, otherwise censored next menu/end; not an internal decision clock',
        typed_unit='Unicode codepoints in user inserts since preceding decision endpoint; deltas may contain multiple characters',
        original_inputs_sha256=filehash(PREPARED/'SOURCE_PINS.json'),final_origin_utf16_counts=dict(origins),
        observed_delta_events=delta_count,edit_windows=edit_count,history='Phase 0 exposed roster; no sealed confirmation records',
        independent_final_document=False,output_bytes=output_bytes)
    guard('aggregates',dict(sessions=len(sessions)))
    source=dict(aggregates=agg,method=note,upstream_revision=revision)
    freeze(root/'T1_SOURCE.json',source)
    freeze(root/'T1.json',dict(source=dict(revision=revision,sha256=filehash(root/'T1_SOURCE.json'),citation='CoAuthor released logs; Phase 0 exposed UTF-16 replay; measured summary T1_SOURCE.json'),aggregates=agg))
    agg4,note4=t4(DICES);revision4='b5596d9edd585361967991a591abc7b11fb1f7a3'
    freeze(root/'T4_SOURCE.json',dict(aggregates=agg4,method=note4,upstream_sha256=filehash(DICES),upstream_revision=revision4))
    freeze(root/'T4.json',dict(source=dict(revision=revision4,sha256=filehash(root/'T4_SOURCE.json'),citation='DICES-350 released 123-rater panel, Q_overall; measured summary T4_SOURCE.json'),aggregates=agg4))
    freeze(root/'CENSUS.json',dict(sessions=len(sessions),writers=len(ww),decisions=n,delta_events=delta_count,
        edit_windows=edit_count,timing_counts=dict(timing),output_bytes=output_bytes,canonical_final_replay_equal=True,
        provider_spend_cents=0,scientific_admission=False))


def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    started=time.time();stop=threading.Event();current={'task':'monitor handshake'}
    def guard(task,progress):
        current['task']=task;snap=resource_snapshot();require_resources(snap)
        if time.time()-started>plan['max_wall_seconds']:raise TimeoutError('finite allowance')
        atomic(ROOT/'PROGRESS.json',dict(at=now(),task=task,progress=progress,resources=snap))
    def deadline():
        if stop.wait(plan['max_wall_seconds']):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),task=current['task'],reason='finite wall ceiling'))
        os._exit(124)
    threading.Thread(target=deadline,daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-started>90:raise TimeoutError('native watch not registered')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor binding')
        compute(ROOT,guard);check_pins(plan['pins'])
        outputs={p.relative_to(ROOT).as_posix():filehash(p) for p in ROOT.rglob('*.json') if p.name not in ('PROGRESS.json','MONITOR_READY.json')}
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs=outputs,plan_sha256=filehash(ROOT/'PLAN.json'),
            wall_seconds=time.time()-started,scientific_admission=False,write_through_required=True))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),task=current['task'],error=str(exc),traceback=traceback.format_exc()))
        raise
    finally:stop.set()


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);args=ap.parse_args()
    prepare() if args.action=='prepare' else run()
