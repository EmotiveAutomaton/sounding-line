"""Exact final-surviving typed text for the existing AUTH cohort; no pairs/calls.

DESIGN CHECK: LESSONS 2-5; AUTH_SOURCE.md. NULL and ALTERNATIVE require exact
identity/provenance and full coverage. Missing/changed inputs refuse; no result
selects a session. Native examples cover Unicode, seams, exclusions and clipping.
"""
from collections import Counter
from pathlib import Path
import re,time
from runners.stage14.common import read,filehash,digest,atomic
from .timing_p6 import write_equal,gzip_equal,gzread
from .week4_plan_source_h1 import units
from .week4_drive_source import source as r2_source


def configuration(mode):
    if mode not in ('constructed','timing','full'):raise ValueError('fixed mode required')
    return dict(card='AUTH-source',mode=mode,seed=20261102,max_words=400,
                expected_sessions={'constructed':3,'timing':99,'full':990}[mode])


def project(timeline,independent=False):
    text=timeline['final_document'];spans=timeline['final_spans'];cursor=0;cp=0;runs=[];owners=[]
    if ''.join(s['text'] for s in spans)!=text:raise ValueError('incomplete final text')
    for s in spans:
        n=len(units(s['text']))
        if s['start_utf16']!=cursor or s['end_utf16']!=cursor+n:raise ValueError('invalid UTF16 provenance')
        if s['origin'] not in ('typed','prompt','accepted','accepted_edited','api_unknown'):raise ValueError('unknown origin')
        if s['origin']=='typed' and s['text']:
            if runs and runs[-1][1]==cp:runs[-1][1]=cp+len(s['text'])
            else:runs.append([cp,cp+len(s['text'])])
        owners.extend([s['origin']=='typed']*len(s['text']));cp+=len(s['text']);cursor+=n
    if independent:
        runs=[];start=None
        for i,typed in enumerate(owners+[False]):
            if typed and start is None:start=i
            if not typed and start is not None:runs.append([start,i]);start=None
    chunks=[dict(start_codepoint=a,end_codepoint=b,text=text[a:b]) for a,b in runs]
    joined='\n\n'.join(r['text'] for r in chunks);words=list(re.finditer(r'\S+',joined))
    payload=joined[:words[399].end()] if len(words)>400 else joined
    return dict(text=payload,typed_chunks=chunks,payload_words=len(re.findall(r'\S+',payload)),
                full_typed_words=len(words),seams=max(0,len(chunks)-1),text_sha256=digest(payload))


def fixtures():
    def make(parts):
        spans=[];offset=0
        for text,origin in parts:
            n=len(units(text));spans.append(dict(text=text,origin=origin,start_utf16=offset,end_utf16=offset+n));offset+=n
        return dict(final_document=''.join(t for t,_ in parts),final_spans=spans)
    return [make([('Prompt ','prompt'),('I  care \U0001f600','typed'),('!','typed'),(' model ','accepted'),('Tail.','typed')]),
            make([('Edited model','accepted_edited'),(' unknown','api_unknown')]),
            make([('  '+('word\t'*401),'typed')])]


def cohort(inputs):
    if set(inputs)!={'r2_root','r2_landing','fic1_root','fic1_landing'}:raise ValueError('fixed sources required')
    root=Path(inputs['fic1_root']);c=read(root/'COMPLETE.json');land=read(inputs['fic1_landing'])
    if not c['fresh_process_verified'] or not land['full_write_through'] or land['completion_sha256']!=filehash(root/'COMPLETE.json'):raise ValueError('unlanded FIC1 source')
    def checked(name):
        path=root/name
        if c['outputs'][name]!=filehash(path):raise ValueError('FIC1 source changed')
        return path
    checked('PLAN.json');index=read(checked('output/SESSION_INDEX.json'));result={}
    if len(index)!=990:raise ValueError('original selected cohort required')
    for row in index:
        path=(root/'output'/row['file']).resolve();path.relative_to((root/'output').resolve())
        if filehash(path)!=row['sha256'] or c['outputs']['output/'+row['file']]!=row['sha256']:raise ValueError('selected session changed')
        value=read(path)
        if value['session']!=row['session'] or row['session'] in result:raise ValueError('duplicate or changed session')
        result[row['session']]=value
    if len({v['writer'] for v in result.values()})!=24:raise ValueError('original writers required')
    return result


def source(inputs,n):
    selected=cohort(inputs);wanted=set(sorted(selected)[:n]);found=set()
    for row in r2_source({k:inputs[k] for k in ('r2_root','r2_landing')},1445):
        if row['session'] not in wanted:continue
        old=selected[row['session']]
        if any(row[k]!=old[k] for k in ('writer','genre')):raise ValueError('cohort identity differs')
        if row['record']['exact'] and row['record']['timeline']['final_document']!=old['final_document']['text']:raise ValueError('independent final document differs')
        found.add(row['session']);yield dict(row,prompt=old['prompt'],half=old['half'])
    if found!=wanted:raise ValueError('missing selected sessions')


def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('changed policy')
    out=Path(output);out.mkdir(parents=True,exist_ok=True);started=time.process_time();n=config['expected_sessions']
    if config['mode']=='constructed':
        if inputs:raise ValueError('fixture has no external source')
        expected=['I  care \U0001f600!\n\nTail.','','  '+('word\t'*399)+'word']
        for fixture,known in zip(fixtures(),expected):
            if project(fixture,verification)['text']!=known:raise ValueError('known-answer projection failed')
        stream=[dict(session=str(i),writer='fixture',genre='fixture',prompt=str(i),half=i%2,record=dict(exact=True,timeline=t)) for i,t in enumerate(fixtures())]
    else:stream=source(inputs,n)
    index=[];census=[];totals=Counter();unique=set()
    for row in stream:
        exact=row['record']['exact'];value=project(row['record']['timeline'],verification) if exact else None
        item=dict(**{k:row[k] for k in ('session','writer','genre','prompt','half')},source_exact=exact,source_reason=row['record'].get('reason'),typed=value)
        path=out/'sessions'/(digest(row['session'])+'.json.gz')
        if verification:
            if gzread(path)!=item:raise ValueError('independent source replay differs')
        else:gzip_equal(path,item)
        index.append(dict(session=row['session'],file=path.relative_to(out).as_posix(),sha256=filehash(path)))
        words=value['payload_words'] if value else 0
        census.append(dict(**{k:row[k] for k in ('session','writer','genre','prompt','half')},exact=exact,payload_words=words,payload_sha256=value['text_sha256'] if value else None))
        if words:unique.add(value['text_sha256'])
        totals.update(sessions=1,exact_sessions=int(exact),nonempty_texts=int(words>0),empty_or_inexact=int(words==0),payload_words=words)
        atomic(out/'PROGRESS.json',dict(done=len(index),total=n,phase='verify' if verification else 'execute'))
    if len(index)!=n:raise ValueError('incomplete source census')
    summary=dict(mode=config['mode'],counts=dict(totals),writers=len({r['writer'] for r in census}),unique_nonempty_texts=len(unique),scope='Exact final-surviving typed stretches joined by two newlines; first 400 whitespace words; deleted production excluded.',pair_allocation_prepared=False,paid_admission=False,scientific_admission=False,input_bindings={k:filehash(Path(v)/'COMPLETE.json') if k.endswith('_root') else filehash(v) for k,v in inputs.items()})
    for name,value in [('SUMMARY.json',summary),('INDEX.json',index),('PRIVATE_CENSUS.json',census)]:
        if verification:
            if read(out/name)!=value:raise ValueError('source summary differs')
        else:write_equal(out/name,value)
    if verification:return dict(verified=True,independent_codepoint_replay=True,scientific_admission=False)
    elapsed=time.process_time()-started;size=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    write_equal(out/'TIMING.json',dict(cpu_seconds=elapsed,completed_sessions=n,projected_full_cpu_seconds_with_fresh_verification=elapsed*990/n*4,projected_full_output_bytes=size*990/n*2))
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
