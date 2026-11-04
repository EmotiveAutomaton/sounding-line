"""T3 final typed skeleton source and dated-half support, without a fitted effect.

DESIGN CHECK: Week4 T3; LESSONS2-5 reviewed 2026-11-02. NULL and ALTERNATIVE
use identical word, split and support rules. Exact source joins and known
boundary/count fixtures guard leakage and false support, not an effect's sign.
Below-floor or overlapping halves are unsupported, never scientific nulls.
Full event-channel, library, matching and reference work remains downstream.
"""
from pathlib import Path
from collections import Counter,defaultdict
import math,time
from .timing_pmap_source import completed,bound_record
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .timing_census import read,filehash
from .timing_text import WORD


def configuration(mode):
    if mode not in ('constructed','full'):raise ValueError('Unknown T3 source mode')
    return dict(card='T3-source',mode=mode,seed=20261102,min_tokens_each=2000,min_writers=25,dictionary_words=150)


def skeletons(sequences,dictionary):
    out=[]
    for seq in sequences:
        current=[]
        for token in seq:
            if WORD.fullmatch(token):current.append(token if token in dictionary else '<content>')
            elif token in ('.','!','?') and current:out.append(current);current=[]
        if current:out.append(current)
    return out


def split_support(records):
    ids=set();by_writer=defaultdict(list)
    for r in records:
        if r['session'] in ids:raise ValueError('Duplicate session')
        ids.add(r['session'])
        if not all(math.isfinite(r[k]) for k in ('timestamp','end_at')) or r['end_at']<r['timestamp']:raise ValueError('Invalid session chronology')
        by_writer[r['writer']].append(r)
    support={};counts=Counter()
    for writer,rows in sorted(by_writer.items()):
        ordered=sorted(rows,key=lambda r:(r['timestamp'],r['session']));cut=len(ordered)//2
        train,test=ordered[:cut],ordered[cut:]
        ntrain=sum(r['tokens'] for r in train);ntest=sum(r['tokens'] for r in test)
        separated=bool(train and test and max(r['end_at'] for r in train)<min(r['timestamp'] for r in test))
        token_floor=ntrain>=2000 and ntest>=2000
        reasons=[]
        if not train or not test:reasons.append('empty_session_half')
        if ntrain<2000:reasons.append('training_token_floor')
        if ntest<2000:reasons.append('evaluation_token_floor')
        if not separated:reasons.append('halves_not_strictly_separated')
        counts.update(reasons)
        counts['token_floor_writers']+=int(token_floor);counts['supported_writers']+=int(token_floor and separated)
        def half(part):
            return dict(sessions=[r['session'] for r in part],tokens=sum(r['tokens'] for r in part),
                        prompts=dict(sorted(Counter(r['prompt'] for r in part).items())),
                        genres=dict(sorted(Counter(r['genre'] for r in part).items())))
        support[writer]=dict(training=half(train),evaluation=half(test),token_floor=token_floor,strictly_separated=separated,
                             supported=token_floor and separated,reasons=reasons)
    return support,dict(counts)


def fixture():
    dictionary={'the','a'};records=[]
    for w in range(26):
        for s in range(4):
            n=999 if w==25 and s==3 else 1000
            records.append(dict(session=f'w{w:02d}s{s}',writer=f'w{w:02d}',prompt='known',genre='constructed',
                timestamp=10*s,end_at=10*s+1,training_sequences=[['the','word']*(n//2)+(['the'] if n%2 else [])]))
    return records,dictionary


def run(output,inputs,config,verification=False):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen T3 source configuration required')
    started=time.process_time();output=Path(output);bindings=[]
    if config['mode']=='constructed':
        if inputs:raise ValueError('Constructed source cannot read human inputs')
        records,dictionary=fixture()
    else:
        if set(inputs)!={'p6_index','p6_completion','windows_completion'}:raise ValueError('Exact T3 source inputs required')
        completed(inputs['p6_completion'],inputs['p6_index']);index=read(inputs['p6_index'])
        wc=Path(inputs['windows_completion']);wp=wc.parent/'output/WINDOWS.json.gz';dp=wc.parent/'output/FROZEN_DICTIONARY.json'
        completed(wc,wp);completed(wc,dp);windows=gzread(wp);dictionary=set(read(dp)['words'])
        if len(dictionary)!=150:raise ValueError('Original frozen dictionary required')
        roster={r['session']:r for r in windows}
        if len(index)!=1399 or len(roster)!=1399 or len(windows)!=1399 or {r['session'] for r in index}!=set(roster):raise ValueError('Complete primary roster required')
        records=[]
        for row in index:
            record=bound_record(inputs['p6_index'],row);meta=roster[row['session']]
            if any(record[k]!=meta[k] for k in ('session','writer','prompt','timestamp','end_at')):raise ValueError('Exact source metadata join differs')
            records.append(dict(record,genre=meta['genre']))
            bindings.append(dict(session=row['session'],source_sha256=row['sha256']))
    prepared=[]
    for i,r in enumerate(sorted(records,key=lambda r:r['session'])):
        seq=skeletons(r['training_sequences'],dictionary)
        prepared.append(dict(**{k:r[k] for k in ('session','writer','prompt','genre','timestamp','end_at')},
                             sequences=seq,tokens=sum(map(len,seq))))
        if (i+1)%25==0:progress(output/'PROGRESS.json',dict(phase='verify-source' if verification else 'source',done=i+1,total=len(records)))
    support,counts=split_support(prepared)
    summary=dict(source_sessions=len(prepared),source_writers=len(support),skeleton_tokens=sum(r['tokens'] for r in prepared),
                 counts=counts,required_writers=25,minimum_tokens_each=2000,
                 source_floor_met=counts.get('supported_writers',0)>=25,
                 scientific_effect_computed=False,donor_support_checked=False,event_channel_prepared=False,
                 scope='Final writer-typed skeleton source and dated-half support only; no compression or reuse outcome')
    if config['mode']=='constructed' and (counts['supported_writers']!=25 or support['w25']['evaluation']['tokens']!=1999):raise ValueError('Known exact floor differs')
    values={'SUMMARY.json':summary,'PRIVATE_SUPPORT.json':support,'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},sources=bindings)}
    if verification:
        for name,value in values.items():
            if read(output/name)!=value:raise ValueError('Complete T3 source replay differs: '+name)
        if gzread(output/'PRIVATE_SEQUENCES.json.gz')!=prepared:raise ValueError('Complete skeleton replay differs')
        return dict(verified=True,complete_source_replay=True)
    for name,value in values.items():write_equal(output/name,value)
    gzip_equal(output/'PRIVATE_SEQUENCES.json.gz',prepared)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started,sessions=len(prepared)))
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
