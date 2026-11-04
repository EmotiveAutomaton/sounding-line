"""S1 exact prior-history support; no recurrence outcome or scientific fit.

DESIGN CHECK: LESSONS2-5 and Week4 S1 reviewed 2026-11-02. Empty own history
is unsupported, never an arbitrary zero-token donor. Only sessions completed
strictly before the target may contribute. Exact D33 session/token matching
and deterministic trimming preserve boundaries. Null/alternative window labels
never influence matching. Failed source joins refuse, not silently intersect.
"""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,time
from .timing_d33_match import earlier,token_count
from .timing_d33_supported_counts import matched_other
from .timing_pmap_source import completed,bound_record
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .timing_census import read,filehash

def configuration(mode):
    if mode not in ('constructed','timing','full'):raise ValueError('Unknown history scope')
    return dict(card='S1-histories',mode=mode,seed=20261102,pilot_targets=20)

def match(by_writer,target):
    own=earlier(by_writer[target['writer']],target)
    if not own or sum(map(token_count,own))==0:
        return dict(target_session=target['session'],supported=False,reason='no nonempty strictly earlier own history',own_sessions=[r['session'] for r in own]),None
    proof,donor=matched_other(by_writer,target)
    if proof['supported']:
        assert proof['own_tokens']==proof['donor_tokens'] and len(donor)==len(own)
        assert all(s['end_at']<target['timestamp'] for s in donor+own)
    return proof,donor

def fixture():
    def row(s,w,n,start,end,p='p'):
        return dict(session=s,writer=w,prompt=p,timestamp=start,end_at=end,training_sequences=[['a']*n])
    records=[row('a0','a',4,0,1),row('b0','b',6,0,1),row('a1','a',5,10,11),row('b_future','b',99,9,12)]
    windows=[dict(session=r['session'],writer=r['writer'],windows=[dict(grams=[['a']*4],**{'class':'flow'})]) for r in records]
    return records,windows

def load(inputs,mode):
    if mode=='constructed':
        if inputs:raise ValueError('No human inputs in constructed mode')
        return fixture()
    if set(inputs)!={'p6_index','p6_completion','windows_completion'}:raise ValueError('Unexpected history inputs')
    completed(inputs['p6_completion'],inputs['p6_index']);index=read(inputs['p6_index'])
    wc=Path(inputs['windows_completion']);wp=wc.parent/'output/WINDOWS.json.gz'
    completed(wc,wp);completed(wc,wc.parent/'output/SUMMARY.json')
    records=[bound_record(inputs['p6_index'],r) for r in index];windows=gzread(wp)
    ids={r['session']:r['writer'] for r in records};wids={r['session']:r['writer'] for r in windows}
    if len(ids)!=len(records) or len(wids)!=len(windows) or ids!=wids or len(ids)!=1399:raise ValueError('Whole primary join differs')
    return records,windows

def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('Frozen history configuration required')
    started=time.process_time();records,windows=load(inputs,config['mode']);source_seconds=time.process_time()-started
    output=Path(output);by_writer=defaultdict(list);lookup={r['session']:r for r in records};wlookup={r['session']:r for r in windows}
    for r in records:by_writer[r['writer']].append(r)
    candidates=[r for r in records if any(w['grams'] and w['class'] in ('flow','hesitant') for w in wlookup[r['session']]['windows'])]
    # Cost-only selection: most prior sessions first, with no recurrence value.
    ordered=sorted(candidates,key=lambda r:(-len(earlier(by_writer[r['writer']],r)),-r['timestamp'],r['session']))
    targets=ordered[:config['pilot_targets']] if config['mode']=='timing' else sorted(candidates,key=lambda r:r['session'])
    counts=Counter();writer_counts=defaultdict(Counter);bindings=[];match_started=time.process_time()
    for i,target in enumerate(targets):
        proof,donor=match(by_writer,target)
        retained=None if donor is None else [dict(session=s['session'],writer=s['writer'],prompt=s['prompt'],timestamp=s['timestamp'],end_at=s['end_at'],training_sequences=s['training_sequences']) for s in donor]
        value=dict(proof=proof,donor=retained)
        path=output/'sessions'/(hashlib.sha256(target['session'].encode()).hexdigest()+'.json.gz')
        if verification:
            if gzread(path)!=value:raise ValueError('Exact history replay differs')
        else:gzip_equal(path,value)
        counts['supported_sessions' if proof['supported'] else 'unsupported_sessions']+=1
        if proof['supported']:
            writer_counts[target['writer']].update(w['class'] for w in wlookup[target['session']]['windows'] if w['grams'] and w['class'] in ('flow','hesitant'))
        bindings.append(dict(session=target['session'],sha256=filehash(path)))
        progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'history-support',done=i+1,total=len(targets)))
    summary=dict(mode=config['mode'],source_sessions=len(records),candidate_sessions=len(candidates),processed_sessions=len(targets),counts=dict(counts),
        writers_with_window_and_donor_floor=sum(c['flow']>=20 and c['hesitant']>=20 for c in writer_counts.values()) if config['mode']=='full' else None,
        required_writers=25,scientific_effect_computed=False,scope='Exact earlier-session count and token matched history support; complete nuisance join still required.')
    if config['mode']=='constructed':
        a=gzread(output/'sessions'/(hashlib.sha256(b'a1').hexdigest()+'.json.gz'))
        if a['proof']['donor_sessions']!=['b0'] or a['proof']['donor_tokens']!=4:raise ValueError('Known exact history differs')
    values={'SUMMARY.json':summary,'PRIVATE_SUPPORT.json':dict(writer_counts),'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},sources=bindings)}
    if verification:
        for n,v in values.items():
            if read(output/n)!=v:raise ValueError('History summary replay differs')
        return dict(verified=True,complete_source_replay=True)
    for n,v in values.items():write_equal(output/n,v)
    timing=dict(source_cpu_seconds=source_seconds,matching_cpu_seconds=time.process_time()-match_started,targets=len(targets),all_targets=len(candidates))
    timing['projected_full_cpu_seconds_with_fresh_verification']=2*(source_seconds+timing['matching_cpu_seconds']*len(candidates)/max(1,len(targets)))*1.5
    write_equal(output/'TIMING.json',timing)
    return dict(status='complete',scientific_admission=False)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
