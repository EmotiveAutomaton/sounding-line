"""Round 34 writer-weighted timing ratios from authenticated local CoAuthor logs."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
import numpy as np
from .batch_runtime import read, freeze, filehash, atomic, now
from .week3_pieces_input import checked_clock, location
from .timing_p6 import gzread
from .timing_events import source_sessions
from runners.stage9.coauthor import apply_delta, delta_ops, text_of, units
from .week6_person_small_v1 import ROOT_NAME,MANIFEST


def request_pauses(events):
    clocks=checked_clock(events)
    doc=units(events[0]['currentDoc'])
    last=None
    omitted=Counter()
    matched=[]
    for ix,event in enumerate(events[1:],1):
        name=event['eventName']
        if name=='suggestion-get':
            cursor=event.get('currentCursor')
            if last is None:omitted['no_preceding_single_insert']+=1
            elif type(cursor) is not int or not 0<=cursor<=len(doc):omitted['cursor_unavailable']+=1
            elif clocks[ix]<=last:omitted['nonpositive_time']+=1
            else:
                end=len(doc)-int(bool(doc) and doc[-1]==10)
                key=location(text_of(doc[:cursor]),cursor<end)
                matched.append((key,clocks[ix]-last))
        if name.startswith('suggestion-'):last=None
        delta=event.get('textDelta');ops=delta_ops(delta)
        if not ops:continue
        inserted=''.join(x['insert'] for x in ops if 'insert' in x)
        removed=sum(x.get('delete',0) for x in ops)
        doc,_,_=apply_delta(doc,[None]*len(doc),delta)
        last=clocks[ix] if event.get('eventSource')=='user' and len(inserted)==1 and not removed else None
    return matched,omitted


def session_controls(session):
    groups=defaultdict(list)
    for x in session['intervals']:
        if x['target']=='single_character_insert' and x['location'] in ('before_word','within_word','before_sentence','before_paragraph','before_revision'):
            v=x['interval_seconds']
            if not np.isfinite(v) or v<=0:raise ValueError('Invalid canonical pause')
            groups[x['location']].append(v)
    return groups


def writer_ratios(controls,requests,card):
    ratios=[];support=Counter()
    for writer,groups in sorted(controls.items()):
        if card=='WLG1':
            start=[x for (genre,k),v in groups.items() if k=='before_sentence' for x in v]
            other=[x for (genre,k),v in groups.items() if k=='before_word' for x in v]
        else:
            medians={key:median(v) for key,v in groups.items() if v}
            start=[];other=[]
            for key,v in requests.get(writer,[]):
                if key not in medians:support['unmatched_requests']+=1;continue
                start.append(v);other.append(medians[key])
        if start and other:
            ratios.append(median(start)/median(other))
            support['start_samples']+=len(start);support['comparison_samples']+=len(other)
        else:support['excluded_writers']+=1
    support['source_writers']=len(controls);support['included_writers']=len(ratios)
    return np.array(ratios),dict(sorted(support.items()))


def compute(values,seed,verify):
    if not len(values):return dict(estimate=None,interval=None,valid_draws=0),[]
    rng=np.random.default_rng(seed);draws=[]
    for _ in range(40):
        idx=rng.integers(0,len(values),(50,len(values)))
        draws.extend([float(median(values[i])) for i in idx] if verify else np.median(values[idx],axis=1).tolist())
    return dict(estimate=float(median(values)),interval=np.quantile(draws,[.025,.975]).tolist(),bootstrap_sd=float(np.std(draws,ddof=1)),valid_draws=len(draws)),draws


def run(output,inputs,config,verify):
    r=Path(__file__).resolve().parents[3];output=Path(output)
    root=Path(inputs['data_root'])
    if root.name!=ROOT_NAME or filehash(root/'DRT1_MANIFEST.json')!=MANIFEST:raise ValueError('Changed temporary source root')
    def local(p):
        # Test the path lexically before any I/O, including resolution of a possible UNC path.
        p=Path(p)
        if not p.is_absolute() or not p.is_relative_to(r):raise ValueError('Source is outside the repository')
        p=p.resolve(strict=True);p.relative_to(r)
        return p
    card=config['card']
    if card not in ('WLG1','WLG2'):raise ValueError('Unknown writing study')
    terminal=local(inputs['pp1_receipt']);prior=read(terminal)
    source=local(terminal.parent/'output/PP1_INTERVALS.json.gz')
    if not prior['fresh_process_verified'] or filehash(source)!=prior['outputs']['output/PP1_INTERVALS.json.gz']:raise ValueError('Canonical interval input changed')
    phase=output/('verify' if verify else 'execute');phase.mkdir(exist_ok=True,parents=True)
    controls=defaultdict(lambda:defaultdict(list));requests=defaultdict(list);roster={};omitted=Counter()
    support_writers=set()
    for row in gzread(source):
        writer=row['writer'];genre=row['genre'];groups=controls[writer]
        for k,vs in session_controls(row).items():groups[genre,k].extend(vs)
        if row['session'] in roster:raise ValueError('Duplicate session')
        roster[row['session']]=(writer,genre)
    if card=='WLG2':
        src=read(local(inputs['wb_plan']))['inputs']
        for path in src.values():local(path)
        if local(src['repo_root'])!=r:raise ValueError('Different repository')
        for row in read(src['raw_roster']):local(r/row['path'])
        seen=set()
        for index,timeline,meta in source_sessions(src,'raw_roster'):
            sid=index['session'];writer,genre=roster[sid]
            if writer!=timeline['writer'] or sid in seen:raise ValueError('Changed writer roster')
            seen.add(sid);support_writers.add(writer)
            path=local(r/meta['path'])
            events=[json.loads(line) for line in path.read_text('utf8').splitlines()]
            req,excluded=request_pauses(events);omitted.update(excluded)
            for k,v in req:requests[writer].append(((genre,k),v))
            if len(seen)%25==0:
                atomic(phase/'PROGRESS.json',dict(at=now(),sessions=len(seen),writers_reached=len(support_writers),temporary_root=ROOT_NAME,manifest_sha256=MANIFEST))
                if any((output/name).exists() for name in ('YIELD_REQUEST.json','STOP_REQUEST.json')):
                    return dict(status='yielded',verified=False,scientific_result_complete=False)
        if set(roster)!=seen:raise ValueError('Missing request histories')
    atomic(phase/"SOURCE_PROGRESS.json",dict(at=now(),writers_reached=len(controls) if card=="WLG1" else len(support_writers),sessions=len(roster),temporary_root=ROOT_NAME,manifest_sha256=MANIFEST))
    values,support=writer_ratios(controls,requests,card)
    results,draws=compute(values,2026112101+int(card[-1]),verify)
    final=dict(card=card,temporary_root=ROOT_NAME,manifest_sha256=MANIFEST,metrics=results,support=support,excluded_request_reasons=dict(omitted),sessions=len(roster))
    if verify:
        from .week5_rr3_v1 import compare_record
        compare_record(read(output/'execute/ENGINE_RESULT.json'),final)
        compare_record(read(output/'execute/DRAWS.json'),draws)
    freeze(phase/'DRAWS.json',draws);freeze(phase/'ENGINE_RESULT.json',final)
    return dict(status='verified' if verify else 'computed',verified=verify,scientific_result_complete=verify,engine_sha256=filehash(phase/'ENGINE_RESULT.json'))


def execute(output,inputs,config):return run(output,inputs,config,False)


def verify(output,inputs,config):return run(output,inputs,config,True)
