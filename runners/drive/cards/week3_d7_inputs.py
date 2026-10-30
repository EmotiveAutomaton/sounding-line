"""D7 complete visible-menu duration and pre-opening content preparation.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 read 2026-10-29. NULL and
ALTERNATIVE retain every prepared menu; this source emits no effect. Raw
visible episodes must reproduce D6 exactly. Censoring stays explicit, hidden
intervals excluded, choice-independent novelty uses every offered option.
Wrong joins, changed hashes, nonunit vectors and bad clocks refuse. No gaze,
expected information or preference mechanism is inferred from these fields.
"""
from collections import Counter
from pathlib import Path
import json, math, time
import numpy as np
from runners.stage14.common import REPO,read,filehash,freeze,atomic
from . import events_d6 as d6
from . import events_d28 as d28

CONFIG=dict(card='D7-inputs',schema=1)


def content(record,vectors,menu):
    if len(record['options'])!=len(menu) or not menu:raise ValueError('Option coverage differs')
    indices=[record['context'],*record['options']]
    if any(type(i) is not int or not 0<=i<len(vectors) for i in indices):raise ValueError('Vector index differs')
    a=np.asarray(vectors[indices],float)
    if a.ndim!=2 or not np.isfinite(a).all() or not np.allclose(np.linalg.norm(a,axis=1),1,rtol=0,atol=1e-5):raise ValueError('Unit finite vectors required')
    cosine=a[1:]@a[0]
    if len(record['cosine'])!=len(menu) or not np.allclose(cosine,record['cosine'],rtol=0,atol=1e-6):raise ValueError('Archived cosine differs')
    novelty=(1-np.clip(cosine,-1,1)).tolist()
    return dict(option_novelty=novelty,mean_novelty=float(np.mean(novelty)),mean_option_characters=float(np.mean([len(t) for t in menu])))


def prepare_session(events,session,p2,domain,saved,records,vectors):
    fresh=d6.extract_session(events,session,p2,domain)['rows']
    def keyed(rows):
        out={r['key']:r for r in rows}
        if len(out)!=len(rows):raise ValueError('Duplicate menu key')
        return out
    actual,previous=keyed(fresh),keyed(saved)
    if actual!=previous:raise ValueError('Raw visible-episode replay differs')
    start=float(session['timestamp']);end=float(session['end_at'])
    if not math.isfinite(start) or not math.isfinite(end) or end<start:raise ValueError('Session clock differs')
    out=[]
    for index,row in enumerate(sorted(session['rows'],key=lambda r:(r['ordinal'],r['key']))):
        event=actual[row['key']];record=records[row['key']]
        if any(record[k]!=session[k] or event[k]!=session[k] for k in ('writer','session')):raise ValueError('Menu identity differs')
        at=float(events[row['ordinal']]['eventTimestamp'])
        if at!=float(row['open_at']) or not start<=at<=end:raise ValueError('Opening clock differs')
        if row['handling'] not in ('accept','edit','dismiss','ignore'):raise ValueError('Handling differs')
        seconds=event['dwell_seconds']
        if not math.isfinite(seconds) or seconds<0:raise ValueError('Invalid duration')
        out.append(dict(key=row['key'],writer=session['writer'],session=session['session'],prompt=session['prompt'],domain=domain,
            session_start=start,session_end=end,open_at=at,menu_ordinal=index,source_ordinal=row['ordinal'],
            elapsed_seconds=(at-start)/1000,handling=row['handling'],accepted=row['handling'] in ('accept','edit'),
            menu_size=len(row['menu']),dwell_seconds=seconds,dwell_observed=event['dwell_observed'],
            visible_episodes=event['visible_episodes'],reopenings=len(event['visible_episodes'])-1,
            hover_events=len(event['hover_sequence']),keyboard_events=len(event['keyboard_sequence']),
            **content(record,vectors,row['menu'])))
    return out


def load(inputs):
    # Reuse only the authenticated source adapter, never D28's scientific test.
    sessions,menus,records,saved,vectors=d28.source(inputs)
    binding=read(inputs['d6_inputs']);paths=binding['paths']
    for p,h in binding['pins'].items():
        if filehash(p)!=h:raise ValueError('D6 source pin changed')
    d6.interface_review(paths['interface_audit'])
    roster={r['session']:r for r in read(paths['source_roster'])}
    index={r['session']:r for r in read(paths['p2_index'])}
    if set(index)!={s['session'] for s in sessions} or not set(index)<=set(roster):raise ValueError('Source census differs')
    if (len(sessions),len({s['writer'] for s in sessions}),len(menus))!=(1399,61,16855):raise ValueError('Original prepared population required')
    return sessions,records,saved,vectors,roster,index,paths


def compute(output,inputs,config,verify=False):
    if config!=CONFIG:raise ValueError('Frozen D7 source configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    binding=dict(inputs={k:filehash(v) for k,v in inputs.items()},config=config)
    if (output/'BINDING.json').exists() and read(output/'BINDING.json')!=binding:raise ValueError('Input binding changed')
    sessions,records,saved,vectors,roster,index,paths=load(inputs)
    rows=[];units=[];started=time.process_time()
    for i,s in enumerate(sorted(sessions,key=lambda x:x['session'])):
        meta=roster[s['session']];item=index[s['session']]
        if meta['writer']!=s['writer'] or item['writer']!=s['writer']:raise ValueError('Writer join differs')
        raw=(Path(paths['source_root'])/meta['path']).resolve();raw.relative_to(REPO)
        p2=(Path(paths['p2_index']).parent/item['file']).resolve();p2.relative_to(Path(paths['p2_index']).parent.resolve())
        if filehash(raw)!=meta['source_sha256'] or filehash(p2)!=item['sha256']:raise ValueError('Raw/P2 source changed')
        events=[json.loads(line) for line in raw.read_text(encoding='utf8').splitlines()]
        unit=prepare_session(events,s,read(p2),meta['domain'],[saved[r['key']] for r in s['rows']],records,vectors)
        name='sessions/'+s['session']+'.json'
        if verify:
            if read(output/name)!=unit:raise ValueError('Fresh D7 session replay differs')
        else:freeze(output/name,unit)
        rows.extend(unit);units.append(dict(session=s['session'],file=name,source_sha256=meta['source_sha256'],p2_sha256=item['sha256'],sha256=filehash(output/name)))
        if i%25==0:atomic(output/'PROGRESS.json',dict(phase='verify-source' if verify else 'source',done=i+1,total=len(sessions)))
        if not verify and i+1==math.ceil(.1*len(sessions)) and not (output/'FIRST_TENTH.json').exists():
            freeze(output/'FIRST_TENTH.json',dict(sessions=i+1,projected_cpu_seconds=max(.001,2*(time.process_time()-started)*len(sessions)/(i+1)),scope='Full source construction plus fresh replay only; no statistical projection'))
        if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():raise InterruptedError('D7 source yields at session boundary')
    summary=dict(sessions=len(sessions),writers=len({s['writer'] for s in sessions}),menus=len(rows),handling_counts=dict(sorted(Counter(r['handling'] for r in rows).items())),observed_durations=sum(r['dwell_observed'] for r in rows),censored_durations=sum(not r['dwell_observed'] for r in rows),menus_with_reopenings=sum(r['reopenings']>0 for r in rows),all_prepared_rows_retained=True,raw_D6_replay_equal=True,source_only=True,scientific_admission=False,effect_computed=False,scope='Visible menu duration and pre-opening embedding dissimilarity; not gaze or expected information')
    values={'BINDING.json':binding,'ROWS.json':rows,'SOURCE_UNITS.json':units,'SUMMARY.json':summary}
    for name,value in values.items():
        if verify:
            if read(output/name)!=value:raise ValueError('Complete D7 source replay differs')
        else:freeze(output/name,value)
    return dict(verified=True,full_fresh_source_replay=True,source_only=True) if verify else dict(status='complete',source_only=True,summary=summary)


def execute(output,inputs,config):return compute(output,inputs,config)
def verify(output,inputs,config):return compute(output,inputs,config,True)
