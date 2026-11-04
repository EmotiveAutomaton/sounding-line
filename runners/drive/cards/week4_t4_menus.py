"""T4 opened-menu census, canonical choices and strictly observed past state.

DESIGN CHECK: Week4 T4/0.5, LESSONS2-5 reviewed in Week4 build. Known
canonical choice must overrule a misleading selection field; dismissal is an
alternative, ignore is not dismissal. Unresolved/future menus cannot enter
past state. This pass fits no model and supplies no predictive effect.
"""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,time,heapq
from runners.stage9.common import digest
from .timing_census import read,filehash
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .events_p5 import sentence_bounds

def configuration(mode):
    if mode not in ('constructed','timing','full'):raise ValueError('Unknown menu scope')
    return dict(card='T4-menus',mode=mode,seed=20261102,pilot_sessions=140)

def canonical_menu(row,canonical):
    if not canonical['usable'] or row['ordinal']!=canonical['ordinal'] or row['handling']!=canonical['decision']:raise ValueError('Canonical menu join differs')
    options=canonical['options']
    if [o['original'] for o in options]!=row['menu']:raise ValueError('Canonical offered text/order differs')
    selected=[i for i,o in enumerate(options) if o['index'] in canonical['matched_option_indices']]
    if row['handling'] in ('accept','edit'):
        if len(selected)!=1 or not canonical['verified_insertion']:raise ValueError('No unique inserted option')
        choice=selected[0]
    elif row['handling']=='dismiss':
        if selected:raise ValueError('Dismissal has selected option')
        choice=len(options)
    elif row['handling']=='ignore':
        if selected:raise ValueError('Ignored menu has selected option')
        choice=None
    else:raise ValueError('Unknown canonical handling')
    spans=list(sentence_bounds(row['document']));context=row['document'][slice(*spans[-1])] if spans else ''
    return dict(key=row['key'],ordinal=row['ordinal'],session=row['session'],writer=row['writer'],prompt=row['prompt'],
        open_at=row['open_at'],resolved_at=row['resolved_at'],handling=row['handling'],options=row['menu'],
        original_option_ids=[o['index'] for o in options],choice=choice,dismissal_index=len(options),
        preceding_visible_sentence=context,context_empty=not bool(context.strip()))

def past_state(sessions):
    by=defaultdict(list);roster=defaultdict(list)
    for s in sessions:
        roster[s['writer']].append(s)
        by[s['writer']].extend(s['menus'])
    for writer,menus in by.items():
        ordered=sorted(menus,key=lambda r:(r['open_at'],r['session'],r['ordinal']))
        resolved=sorted((r for r in menus if r['resolved_at'] is not None),key=lambda r:(r['resolved_at'],r['session'],r['ordinal']))
        for r in resolved:
            if r['resolved_at']<r['open_at']:raise ValueError('Menu resolves before opening')
        observed=[];at=0;last_accept=None
        for r in ordered:
            while at<len(resolved) and resolved[at]['resolved_at']<r['open_at']:
                prior=resolved[at];observed.append(prior)
                if prior['handling'] in ('accept','edit'):last_accept=prior['resolved_at']
                at+=1
            previous=observed[-5:]
            r['previous_five_count']=len(previous)
            r['previous_five_acceptance']=sum(x['handling'] in ('accept','edit') for x in previous)/5 if len(previous)==5 else None
            r['seconds_since_last_acceptance']=(r['open_at']-last_accept)/1000. if last_accept is not None else None
            r['state_supported']=len(previous)==5 and last_accept is not None
        ss=sorted(roster[writer],key=lambda s:(s['timestamp'],s['session']));cut=len(ss)//2
        first_test=ss[cut]['timestamp'] if cut<len(ss) else None
        for i,s in enumerate(ss):
            s['half']='train' if i<cut else 'test'
            s['overlaps_later_half']=i<cut and first_test is not None and s['end_at']>=first_test
    return sessions

def fixture():
    sessions=[]
    for session in range(2):
        menus=[]
        for i in range(4):
            number=4*session+i;handling='accept' if number%3==0 else 'dismiss' if number%3==1 else 'ignore'
            row=dict(key=str(number),ordinal=number+1,session=str(session),writer='a',prompt='p',open_at=1000*number,resolved_at=1000*number+500,
                handling=handling,menu=['wrong logged selection','actual choice'],document='First sentence. Last sentence.',inserted='wrong logged selection')
            canonical=dict(usable=True,ordinal=number+1,decision=handling,options=[dict(index=7,original=row['menu'][0]),dict(index=3,original=row['menu'][1])],
                matched_option_indices=[3] if handling=='accept' else [],verified_insertion=handling=='accept')
            menus.append(canonical_menu(row,canonical))
        sessions.append(dict(session=str(session),writer='a',genre='constructed',prompt='p',timestamp=session*4000,end_at=session*4000+3500,menus=menus))
    return sessions

def load(inputs,mode):
    if mode=='constructed':
        if inputs:raise ValueError('No human inputs in construction')
        return fixture(),[]
    if set(inputs)!={'source_inputs'}:raise ValueError('Exact frozen registry required')
    source=read(inputs['source_inputs']);root=Path(source['repo_root']);foundation=read(source['foundation_plan']);complete=read(source['foundation_complete'])
    if complete['plan_sha256']!=filehash(source['foundation_plan']):raise ValueError('Foundation binding differs')
    for name in ('prepared_sessions','raw_roster','source_pins'):
        if foundation['pins'][Path(source[name]).relative_to(root).as_posix()]!=filehash(source[name]):raise ValueError('Frozen menu metadata changed')
    pins=read(source['source_pins']);prepared={s['session']:s for s in read(source['prepared_sessions'])};raw={s['session']:s for s in read(source['raw_roster'])}
    index=read(source['session_index'])
    if complete['outputs'].get(Path(source['session_index']).relative_to(Path(source['foundation_complete']).parent).as_posix())!=filehash(source['session_index']):raise ValueError('Primary session index changed')
    if len(index)!=1399 or len({r['session'] for r in index})!=1399:raise ValueError('Whole primary roster required')
    selected=sorted(index,key=lambda r:r['session'])
    if mode=='timing':selected=selected[:140]
    sessions=[];bindings=[]
    for item in selected:
        sid=item['session'];s=prepared[sid];meta=raw[sid];rawpath=root/meta['path']
        path=root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':rawpath.stem})+'.json')
        if pins.get(path.relative_to(root).as_posix())!=filehash(path):raise ValueError('Canonical source pin differs')
        canonical=read(path)
        if not canonical['usable'] or not canonical['reconstructed'] or canonical['errors']:raise ValueError('Canonical session not usable')
        choices={r['ordinal']:r for r in canonical['events'] if r['usable']}
        if set(choices)!={r['ordinal'] for r in s['rows']}:raise ValueError('Opened-menu coverage differs')
        if s['writer']!=item['writer'] or s['writer']!=meta['writer']:raise ValueError('Writer join differs')
        menus=[canonical_menu(r,choices[r['ordinal']]) for r in s['rows']]
        sessions.append(dict(session=sid,writer=s['writer'],prompt=s['prompt'],genre=meta['domain'],timestamp=s['timestamp'],end_at=s['end_at'],menus=menus))
        bindings.append(dict(session=sid,canonical_sha256=filehash(path)))
    return sessions,bindings

def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('Frozen menu configuration required')
    started=time.process_time();sessions,bindings=load(inputs,config['mode']);past_state(sessions)
    counts=Counter();writers=defaultdict(Counter)
    for s in sessions:
        for r in s['menus']:
            counts[r['handling']]+=1;counts['state_supported']+=r['state_supported'];counts['empty_context']+=r['context_empty']
            eligible=r['choice'] is not None and r['state_supported'] and not r['context_empty'] and not s['overlaps_later_half']
            r['source_supported']=eligible
            if eligible:writers[s['writer']][s['half']]+=1
    summary=dict(mode=config['mode'],sessions=len(sessions),writers=len(writers),counts=dict(counts),
        supported_writers_before_embedding_history=sum(c['train']>=20 and c['test']>=20 for c in writers.values()) if config['mode']=='full' else None,
        required_writers=25,scientific_effect_computed=False,scope='Canonical choice and past-state source census only; complete embedding-history support and fitting remain.')
    output=Path(output);values={'SUMMARY.json':summary,'PRIVATE_SUPPORT.json':dict(writers),'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},sources=bindings)}
    import json
    if verification:
        if gzread(output/'MENUS.json.gz')!=sessions:raise ValueError('Complete menu replay differs')
        for n,v in values.items():
            if read(output/n)!=json.loads(json.dumps(v)):raise ValueError('Menu aggregate replay differs')
        return dict(verified=True,complete_source_replay=True)
    for n,v in values.items():write_equal(output/n,v)
    gzip_equal(output/'MENUS.json.gz',sessions)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started,projected_full_cpu_seconds_with_fresh_verification=3*(time.process_time()-started)*1399/max(1,len(sessions))))
    return dict(status='complete',scientific_admission=False)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
