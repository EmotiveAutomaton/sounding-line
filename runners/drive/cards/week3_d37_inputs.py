"""D37 source-only page/process separation with strict predecision clocks.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1-7 read 2026-10-29.
NULL/ALTERNATIVE keep the full prepared population. Own/future outcomes cannot
alter page or process inputs. Missing request latency is flagged; unknown joins,
bad clocks, duplicate keys or changed source hashes refuse. No fitted result.
"""
from collections import Counter
from pathlib import Path
import json,math,time
import numpy as np
from runners.stage14.common import REPO
from runners.stage9.coauthor import delta_ops
from . import menus_p4 as p4
from .timing_census import read,filehash
from .timing_p6 import write_equal,progress

CONFIG=dict(card='D37-inputs',schema=1,recent_ms=60000)
PROCESS=('log_request_seconds','request_missing','log_prior_hovers',
         'log_recent_inserted_codepoints','log_recent_deleted_utf16','log_recent_user_delta_events')


def process_features(events,rows,recent_ms=60000):
    times=[float(e['eventTimestamp']) for e in events]
    if not times or not all(math.isfinite(t) for t in times) or times!=sorted(times):raise ValueError('Invalid raw clock')
    by_ordinal={r['ordinal']:r for r in rows}
    if len(by_ordinal)!=len(rows) or len({r['key'] for r in rows})!=len(rows):raise ValueError('Duplicate prepared menu')
    if any(type(i) is not int or i<0 or i>=len(events) or events[i]['eventName']!='suggestion-open' for i in by_ordinal):raise ValueError('Invalid menu ordinal')
    requests=[];hovers=0;deltas=[];out=[]
    for ordinal,event in enumerate(events):
        name=event['eventName'];at=times[ordinal]
        if name=='suggestion-open':
            if ordinal in by_ordinal:
                row=by_ordinal[ordinal]
                if float(row['open_at'])!=at:raise ValueError('Prepared open clock differs')
                reason=None if len(requests)==1 else 'missing_request' if not requests else 'ambiguous_requests'
                latency=(at-requests[0])/1000 if reason is None else None
                recent=[x for x in deltas if x[0]>=at-recent_ms]
                values=[math.log1p(latency) if latency is not None else 0.,float(latency is None),
                        math.log1p(hovers),math.log1p(sum(x[1] for x in recent)),
                        math.log1p(sum(x[2] for x in recent)),math.log1p(len(recent))]
                out.append(dict(key=row['key'],ordinal=ordinal,process=values,request_missing_reason=reason))
            requests=[];hovers=0
        elif name=='suggestion-get':requests.append(at)
        elif name=='suggestion-hover':hovers+=1
        # Current menu and all later deltas enter history only AFTER its features.
        if event.get('eventSource')=='user' and event.get('textDelta') not in (None,''):
            ops=delta_ops(event['textDelta']);inserted=sum(len(o.get('insert','')) for o in ops);deleted=sum(o.get('delete',0) for o in ops)
            if type(deleted) is not int or deleted<0:raise ValueError('Invalid deletion count')
            if inserted or deleted:deltas.append((at,inserted,deleted))
    if {x['key'] for x in out}!={r['key'] for r in rows}:raise ValueError('Missing prepared menu')
    return out


def page_features(sessions,records,vectors):
    # P4's helper can form mixed fields, but only these content-only columns
    # leave this adapter. Tests poison all handling labels to verify isolation.
    copied=[dict(s,rows=[dict(r,session_end=s['end_at']) for r in s['rows']]) for s in sessions]
    rows,base,scalar,embedding=p4.prefix_features(copied,records,vectors)
    return rows,np.c_[base[:,1:4],scalar[:,:50]],embedding


def load(inputs):
    expected={'p4_complete','p4_plan','p4_landing','foundation_plan','foundation_complete','roster'}
    if set(inputs)!=expected:raise ValueError('Exact D37 source inputs required')
    complete,plan,landing=[read(inputs[k]) for k in ('p4_complete','p4_plan','p4_landing')]
    if (complete['status']!='COMPLETE' or filehash(inputs['p4_complete'])!=landing['terminal_sha256']
            or filehash(inputs['p4_plan'])!=landing['plan_sha256'] or not landing['source_and_output_hashes_verified']):raise ValueError('P4 source authentication failed')
    for key in ('sessions','records','vectors'):
        if filehash(plan['inputs'][key])!=landing['input_hashes'][key]:raise ValueError('P4 data changed')
    foundation=read(inputs['foundation_plan']);done=read(inputs['foundation_complete'])
    if done['status']!='COMPLETE' or done['plan_sha256']!=filehash(inputs['foundation_plan']):raise ValueError('Foundation plan changed')
    for path in (inputs['roster'],plan['inputs']['sessions']):
        p=Path(path).resolve();pins={str((REPO/k).resolve()):v for k,v in foundation['pins'].items()}
        if pins.get(str(p))!=filehash(p):raise ValueError('Foundation roster changed')
    return read(plan['inputs']['sessions']),read(plan['inputs']['records']),np.load(plan['inputs']['vectors'],allow_pickle=False,mmap_mode='r'),{r['session']:r for r in read(inputs['roster'])}


def build(inputs,config,output):
    if config!=CONFIG:raise ValueError('Frozen D37 input configuration required')
    sessions,records,vectors,roster=load(inputs)
    if (len(sessions),len({s['writer'] for s in sessions}),sum(len(s['rows']) for s in sessions))!=(1399,61,16855):raise ValueError('Original prepared census changed')
    rows,page,embedding=page_features(sessions,records,vectors);process={};source_hashes={};missing=Counter()
    for i,session in enumerate(sessions):
        meta=roster[session['session']];path=(REPO/meta['path']).resolve();path.relative_to(REPO)
        if filehash(path)!=meta['source_sha256']:raise ValueError('Raw log changed')
        events=[json.loads(line) for line in path.read_text(encoding='utf8').splitlines()]
        for item in process_features(events,session['rows'],config['recent_ms']):
            if item['key'] in process:raise ValueError('Duplicate cross-session key')
            process[item['key']]=item;missing[item['request_missing_reason'] or 'observed']+=1
        source_hashes[session['session']]=meta['source_sha256']
        if i%25==0:progress(Path(output)/'PROGRESS.json',dict(phase='raw-prefixes',sessions=i+1,total=len(sessions)))
    if set(process)!={r['key'] for r in rows}:raise ValueError('Process/content join differs')
    clean=[{k:r[k] for k in ('key','writer','session','prompt','ordinal','open_at','resolved_at','session_time','session_end','handling')} for r in rows]
    process_array=np.array([process[r['key']]['process'] for r in rows],float)
    splits,excluded=p4.chronological_partitions(sessions);eligible=[];partitions={}
    for writer in sorted(splits):
        split=p4.recipient_split(writer,splits)
        if split['reason'] is None and sum(len(s['rows']) for s in split['train'])>=8:
            eligible.append(writer)
            partitions[writer]={k:[s['session'] for s in split[k]] for k in ('train','own_train','calibration','test')}
            partitions[writer].update(cutoff=split['cutoff'],test_cutoff=split['test_cutoff'],excluded_future_training=split['excluded_future_training'],excluded_overlapping_calibration=split['excluded_overlapping_calibration'])
        else:excluded.append(dict(writer=writer,reason=split['reason'] or 'fewer than eight pooled training decisions'))
    summary=dict(rows=len(rows),sessions=len(sessions),writers=61,eligible_recipients=len(eligible),excluded_recipients=len(excluded),page_scalar_columns=page.shape[1],embedding_columns=embedding.shape[1],process_columns=list(PROCESS),request_support=dict(missing),all_prepared_rows_retained=True,scientific_admission=False,source_only=True)
    return dict(rows=clean,process_metadata=[dict(key=r['key'],request_missing_reason=process[r['key']]['request_missing_reason']) for r in rows],partitions=partitions,exclusions=excluded,raw_source_hashes=source_hashes,summary=summary),dict(page=page,embedding=embedding,process=process_array)


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    value,arrays=build(inputs,config,output)
    for name,a in arrays.items():
        if not np.isfinite(a).all():raise ValueError('Nonfinite prepared input')
        with (output/(name+'.npy')).open('xb') as stream:np.save(stream,a,allow_pickle=False)
    write_equal(output/'ROWS.json',value)
    write_equal(output/'SUMMARY.json',value['summary'])
    write_equal(output/'BINDING.json',dict(inputs={k:filehash(v) for k,v in inputs.items()},arrays={n:filehash(output/(n+'.npy')) for n in arrays}))
    return dict(status='complete',source_only=True)


def verify(output,inputs,config):
    output=Path(output);binding=read(output/'BINDING.json')
    if binding['inputs']!={k:filehash(v) for k,v in inputs.items()}:raise ValueError('Input bindings changed')
    value,arrays=build(inputs,config,output)
    if value!=read(output/'ROWS.json') or value['summary']!=read(output/'SUMMARY.json'):raise ValueError('Fresh full source replay differs')
    for name,a in arrays.items():
        if filehash(output/(name+'.npy'))!=binding['arrays'][name] or not np.array_equal(a,np.load(output/(name+'.npy'),allow_pickle=False)):raise ValueError('Fresh numeric input differs')
    return dict(verified=True,full_fresh_source_replay=True,source_only=True)
