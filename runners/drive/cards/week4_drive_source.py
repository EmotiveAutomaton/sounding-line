"""Completed R2 -> private DRIVE text pairs and V3 opportunity census.

DESIGN CHECK: LESSONS 2-5 read 2026-11-05; DRIVE_SOURCE.md frozen first.
NULL/ALTERNATIVE: source provenance and full replay must be exact in both.
Support below 200 per half for 25 writers refuses main; passing is only an
opportunity count, never scientific or paid admission. No deleted-text claim.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import re
import time
from runners.stage14.common import read, filehash, digest, atomic
from .timing_p6 import write_equal, gzip_equal, gzread
from .events_p5 import sentence_bounds, BOUNDARY
from .week4_plan_source_h1 import units, text_of


def configuration(mode):
    if mode not in ('constructed', 'timing', 'full'):
        raise ValueError('Fixed source mode required')
    return dict(card='DRIVE-source', mode=mode, seed=20261102,
                expected_sessions={'constructed':3, 'timing':145, 'full':1445}[mode])


def project(timeline, independent=False):
    text = timeline['final_document']; spans = timeline['final_spans']
    if ''.join(s['text'] for s in spans) != text:
        raise ValueError('Provenance text does not cover document')
    positions = []; cursor = 0
    for span in spans:
        width = len(units(span['text']))
        if span['start_utf16'] != cursor or span['end_utf16'] != cursor + width:
            raise ValueError('Provenance offsets disagree')
        if span['origin'] not in ('typed','prompt','accepted','accepted_edited','api_unknown'):
            raise ValueError('Unknown provenance')
        cursor += width
        positions.extend([span['origin']] * width)
    if independent:
        # Alternate assembly: spans expand to codepoints before segmentation.
        owners = [span['origin'] for span in spans for _ in span['text']]
        ends = [m.end() for m in re.finditer(BOUNDARY.pattern, text)] + [len(text)]
        pairs = []; start = 0
        for end in ends:
            if text[start:end].strip(): pairs.append((start, end))
            start = end
    else:
        owners = []; offset = 0
        for char in text:
            width = len(units(char)); part = positions[offset:offset+width]
            if len(part) != width or len(set(part)) != 1:
                raise ValueError('Split codepoint provenance')
            owners.append(part[0]); offset += width
        pairs = list(sentence_bounds(text))
    result = []; previous = ''
    for number, (a,b) in enumerate(pairs):
        kinds = Counter(owners[j] for j in range(a,b) if not text[j].isspace())
        typed = bool(kinds) and set(kinds) == {'typed'}
        result.append(dict(sentence_index=number, start_codepoint=a, end_codepoint=b,
                           sentence=text[a:b], preceding_sentence=previous,
                           writer_typed=typed, origin_counts=dict(sorted(kinds.items()))))
        previous = text[a:b]
    return result


def payload(row):
    return {k:row[k] for k in ('sentence','preceding_sentence')}


def support(rows):
    groups = defaultdict(list)
    for row in rows: groups[(row['writer'],row['genre'])].append(row)
    counts = {}; by_writer = defaultdict(lambda:[0,0])
    genres = defaultdict(list)
    for (writer,genre), sessions in sorted(groups.items()):
        sessions.sort(key=lambda s:hashlib.sha256(('20261102|'+s['session']).encode()).hexdigest())
        halves = [sum(s['eligible'] for s in sessions[side::2]) for side in (0,1)]
        counts[digest([writer,genre])] = dict(writer=writer,genre=genre,halves=halves,
            sessions=[s['session'] for s in sessions])
        for i in (0,1): by_writer[writer][i] += halves[i]
        genres[genre].append(halves)
    def stats(values):
        values=list(values)
        return dict(writers=len(values),writers_with_400_total=sum(sum(v)>=400 for v in values),
                    writers_with_200_each_half=sum(min(v)>=200 for v in values))
    return dict(pooled=stats(by_writer.values()),by_genre={g:stats(v) for g,v in sorted(genres.items())}), counts


def fixtures():
    def item(parts):
        spans=[];pos=0
        for text,kind in parts:
            n=len(units(text));spans.append(dict(text=text,origin=kind,start_utf16=pos,end_utf16=pos+n));pos+=n
        return dict(final_document=''.join(t for t,_ in parts),final_spans=spans)
    return [item([('Prompt. ','prompt'),('I care \U0001f600. Next tail','typed')]),
            item([('Mine ','typed'),('and model. ','accepted'),('Fresh.','typed')]),
            item([('\n','prompt')])]


def source(inputs, limit):
    if set(inputs) != {'r2_root','r2_landing'}: raise ValueError('Exact completed source binding required')
    root=Path(inputs['r2_root']); complete=read(root/'COMPLETE.json'); landing=read(inputs['r2_landing'])
    if not complete['fresh_process_verified'] or not landing['full_write_through'] or landing['complete_sha256'] != filehash(root/'COMPLETE.json'):
        raise ValueError('R2 completion not fully landed')
    if complete['outputs']['PLAN.json'] != filehash(root/'PLAN.json'):
        raise ValueError('R2 plan changed')
    indexpath=root/'output/INDEX.json'
    if complete['outputs']['output/INDEX.json'] != filehash(indexpath):raise ValueError('R2 index changed')
    index=read(indexpath)
    if len(index)!=1445 or len({r['session'] for r in index})!=1445:raise ValueError('R2 roster differs')
    for entry in sorted(index,key=lambda r:r['session'])[:limit]:
        path=(root/'output'/entry['file']).resolve();path.relative_to((root/'output').resolve())
        if filehash(path)!=entry['sha256'] or complete['outputs']['output/'+entry['file']]!=entry['sha256']:
            raise ValueError('R2 session changed')
        row=gzread(path)
        if row['session']!=entry['session']:raise ValueError('Session binding changed')
        yield row


def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('Configuration changed')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time()
    mode=config['mode']; n=config['expected_sessions']; index=[]; census=[]; totals=Counter();unique=set()
    if mode=='constructed':
        if inputs:raise ValueError('No corpus in constructed validation')
        stream=[dict(session=str(i),writer='constructed',genre='constructed',record=dict(exact=True,timeline=t)) for i,t in enumerate(fixtures())]
    else:stream=source(inputs,n)
    for entry in stream:
        record=entry['record'];exact=record['exact']
        rows=project(record['timeline'],verification) if exact else []
        eligible=[r for r in rows if r['writer_typed']]
        for r in eligible:unique.add(digest(payload(r)))
        value=dict(session=entry['session'],writer=entry['writer'],genre=entry['genre'],
                   source_exact=exact,source_reason=record.get('reason'),sentences=rows)
        path=output/'sessions'/(hashlib.sha256(entry['session'].encode()).hexdigest()+'.json.gz')
        if verification:
            if gzread(path)!=value:raise ValueError('Independent sentence/provenance reconstruction differs')
        else:gzip_equal(path,value)
        index.append(dict(file=path.relative_to(output).as_posix(),sha256=filehash(path)))
        census.append(dict(session=entry['session'],writer=entry['writer'],genre=entry['genre'],eligible=len(eligible)))
        totals.update(sessions=1,exact_sessions=int(exact),excluded_sessions=int(not exact),segments=len(rows),eligible=len(eligible),excluded_segments=len(rows)-len(eligible))
        atomic(output/'PROGRESS.json',dict(done=len(index),total=n,phase='verify' if verification else 'execute'))
    if len(index)!=n:raise ValueError('Incomplete census')
    supported,private=support(census)
    summary=dict(mode=mode,counts=dict(totals),unique_payloads=len(unique),support=supported,
        scope='Final-surviving P5 sentence segments only, not all produced/deleted sentences; opportunities before model coding.',
        case_gate_opportunities_only=supported['pooled']['writers_with_200_each_half']>=25,
        scientific_admission=False,paid_admission=False,
        input_bindings={k:filehash(Path(v)/'COMPLETE.json') if k=='r2_root' else filehash(v) for k,v in inputs.items()})
    if mode=='constructed':
        if totals['eligible']!=3 or totals['excluded_segments']!=2 or totals['segments']!=5:
            raise ValueError('Known-answer fixture differs')
    for name,value in [('SUMMARY.json',summary),('INDEX.json',index),('PRIVATE_SUPPORT.json',private)]:
        if verification:
            if read(output/name)!=value:raise ValueError('Complete source aggregation differs: '+name)
        else:write_equal(output/name,value)
    if verification:return dict(verified=True,independent_projection=True,scientific_admission=False)
    elapsed=time.process_time()-start
    size=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    write_equal(output/'TIMING.json',dict(cpu_seconds=elapsed,completed_sessions=n,
        projected_full_cpu_seconds_with_fresh_verification=elapsed*(1445/n)*4,
        projected_full_output_bytes=size*(1445/n)*2))
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
