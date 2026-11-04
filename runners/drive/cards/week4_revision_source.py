"""S2 revision-source preflight, with no scientific contrast.

DESIGN CHECK: LESSONS 2-5 reread 2026-11-03. Exact replay, Unicode and
provenance must hold under null and alternative. Interior earlier-sentence
edits count; prompt/API/continuation cases cannot become typed revisions.
Counts are an upper-bound source census, never analytical support admission.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,math,re,time
from runners.stage9.coauthor import units,text_of,delta_ops,apply_delta
from .events_p5 import sentence_bounds,BOUNDARY
from .timing_events import source_sessions
from .timing_pmap_source import completed
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .timing_census import read,filehash


def configuration(mode):
    if mode not in ('constructed','timing','full'):raise ValueError('Frozen source mode required')
    return dict(card='S2-source',mode=mode,expected_sessions={'constructed':1,'timing':140,'full':1399}[mode],seed=20261102)


def sentences(doc,owners,ops=None):
    text=text_of(doc);offset=[0]
    if text.isascii():offset=range(len(text)+1)
    else:
        for c in text:offset.append(offset[-1]+(2 if ord(c)>65535 else 1))
    boundaries={m.end() for m in BOUNDARY.finditer(text)};out=[]
    for a,b in sentence_bounds(text):
        left=a
        while left<b and text[left].isspace():left+=1
        right=b
        while right>left and text[right-1].isspace():right-=1
        out.append(dict(start_utf16=offset[a],end_utf16=offset[b],content_start_utf16=offset[left],content_end_utf16=offset[right],
            text=text[a:b],_characters=(left,right),
            complete=b in boundaries or bool(re.search(r'''[.!?]["'\u2019\u201d)]*$''',text[left:right]))))
    for i,s in enumerate(out):s.update(sentence_index=i,distance_sentences=len(out)-1-i)
    selected=set(touches(ops,out)) if ops is not None else set(range(len(out)))
    for i,s in enumerate(out):
        left,right=s.pop('_characters')
        if i not in selected:continue
        used=[o for j in range(left,right) if not text[j].isspace() for o in owners[offset[j]:offset[j+1]]]
        typed=sum(o is not None for o in used)
        s.update(nonspace_utf16=len(used),typed_nonspace_utf16=typed,fully_typed=bool(used) and typed==len(used),typed_insertion_ordinals=sorted({o for o in used if o is not None}))
    return out


def touches(ops,spans):
    position=0;hit={}
    for number,op in enumerate(ops):
        if 'retain' in op:position+=op['retain'];continue
        count=op.get('delete',0);insert=op.get('insert','')
        if not count and not insert:continue
        for i,s in enumerate(spans):
            a,b=s['content_start_utf16'],s['content_end_utf16']
            overlaps=position<b and position+count>a if count else a<position<b
            if overlaps:hit.setdefault(i,[]).append(dict(operation=number,position_utf16=position,deleted_utf16=count,inserted_utf16=len(units(insert))))
        position+=count
    return hit


def extract(events):
    if not events or events[0]['eventName']!='system-initialize':raise ValueError('Initialization required')
    stamps=[float(e['eventTimestamp']) for e in events]
    if not all(math.isfinite(t) for t in stamps) or stamps!=sorted(stamps):raise ValueError('Invalid source chronology')
    doc=units(events[0]['currentDoc']);owners=[None]*len(doc);records=[];counts=Counter();pending=False
    for ordinal,e in enumerate(events):
        if e['eventName']=='suggestion-select':pending=True
        ops=delta_ops(e.get('textDelta'))
        if not ops:continue
        changed=any(o.get('delete',0) or o.get('insert','') for o in ops)
        user=e.get('eventSource')=='user'
        before=doc;oldowners=owners
        after,newowners,_=apply_delta(doc,owners,e.get('textDelta'),insertion_owner=ordinal if user else None)
        if pending and not user:
            oldtext,newtext=text_of(before),text_of(after)
            if not oldtext.endswith('\n') or not newtext.startswith(oldtext[:-1]) or not newtext.endswith('\n'):raise ValueError('Noncanonical accepted append')
            extra=len(after)-len(before)
            if extra<0:raise ValueError('Negative accepted span')
            newowners=oldowners[:-1]+[None]*extra+oldowners[-1:];pending=False
        if changed:
            counts['user_text_changes' if user else 'nonuser_text_changes']+=1
            if user:
                spans=sentences(before,oldowners,ops);hit=touches(ops,spans);targets=[]
                for i,changes in sorted(hit.items()):
                    target=dict(spans[i],changes=changes)
                    target['candidate_nonlocal_typed']=target['fully_typed'] and target['complete'] and target['distance_sentences']>=1
                    targets.append(target)
                if not targets:counts['user_changes_without_prior_sentence_interior']+=1
                else:
                    counts['user_changes_touching_prior_sentence']+=1
                    counts['candidate_nonlocal_events']+=int(any(s['candidate_nonlocal_typed'] for s in targets))
                    counts['candidate_nonlocal_sentence_targets']+=sum(s['candidate_nonlocal_typed'] for s in targets)
                    counts['mixed_or_nontyped_sentence_targets']+=sum(not s['fully_typed'] for s in targets)
                    counts['incomplete_sentence_targets']+=sum(not s['complete'] for s in targets)
                    records.append(dict(ordinal=ordinal,seconds=(stamps[ordinal]-stamps[0])/1000,
                        remaining_seconds=(stamps[-1]-stamps[ordinal])/1000,
                        recorded_cursor=e.get('currentCursor'),recorded_cursor_valid_post_edit=type(e.get('currentCursor')) is int and 0<=e['currentCursor']<=len(after),
                        before_utf16=len(before),after_utf16=len(after),targets=targets))
        doc,owners=after,newowners
    return dict(events=records,census=dict(counts),final_document_sha256=hashlib.sha256(text_of(doc).encode()).hexdigest(),
        final_typed_mask_sha256=hashlib.sha256(bytes(o is not None for o in owners)).hexdigest())


def fixture():
    def event(name,t,**kw):return dict(eventName=name,eventTimestamp=t*1000,eventSource='user',**kw)
    text='First \U0001f600 typed sentence. Second typed sentence. Last fragment'
    return [event('system-initialize',0,currentDoc='\n'),
        event('text-insert',1,textDelta={'ops':[{'insert':text}]}),
        event('text-insert',2,textDelta={'ops':[{'retain':6},{'insert':'new '}]}),
        event('text-delete',3,textDelta={'ops':[{'retain':6},{'delete':4}]}),
        event('text-insert',4,textDelta={'ops':[{'retain':len(units(text))},{'insert':' end'}]}),
        event('system-finish',5)]


def run(output,inputs,config,verification=False):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen source configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time();index=[];counts=Counter();writers=set();candidate_writers=set();bindings=[]
    if config['mode']=='constructed':
        if inputs:raise ValueError('No human inputs in constructed mode')
        stream=[(dict(session='fixture',writer='fixture'),None,dict(domain='constructed'),fixture())];r2_index={}
    else:
        if set(inputs)!={'source_inputs','r2_completion'}:raise ValueError('Source and R2 completion required')
        source=read(inputs['source_inputs']);r2=Path(inputs['r2_completion']);r2out=r2.parent/'output'
        completed(r2,r2out/'INDEX.json');items=read(r2out/'INDEX.json');r2_index={r['session']:r for r in items}
        if len(items)!=len(r2_index) or len(items)!=1445:raise ValueError('Full R2 archive roster required')
        def raw_stream():
            for row,timeline,meta in source_sessions(source,'raw_roster'):
                raw=Path(source['repo_root'])/meta['path']
                events=[json.loads(s) for s in raw.read_text(encoding='utf8').splitlines() if s.strip()]
                yield row,timeline,meta,events
        stream=raw_stream()
    for i,(row,timeline,meta,events) in enumerate(stream):
        if i>=config['expected_sessions']:break
        value=extract(events)
        if timeline is not None:
            rr=r2_index[row['session']];path=r2out/rr['file']
            if filehash(path)!=rr['sha256']:raise ValueError('R2 session changed')
            r2session=gzread(path)
            if r2session['writer']!=row['writer'] or not r2session['record']['exact']:raise ValueError('R2 exact writer join failed')
            reference=r2session['record']['timeline']
            if value['final_document_sha256']!=hashlib.sha256(reference['final_document'].encode()).hexdigest() or reference['final_document']!=timeline['final_document']:raise ValueError('Final source replay differs')
            mask=bytes(s['origin']=='typed' for s in reference['final_spans'] for _ in units(s['text']))
            if hashlib.sha256(mask).hexdigest()!=value['final_typed_mask_sha256']:raise ValueError('R2 typed provenance differs')
        value.update(session=row['session'],writer=row['writer'],genre=meta['domain'])
        path=output/'sessions'/(hashlib.sha256(row['session'].encode()).hexdigest()+'.json.gz')
        if verification:
            if gzread(path)!=value:raise ValueError('Revision source replay differs')
        else:gzip_equal(path,value)
        index.append(dict(session=row['session'],file=path.relative_to(output).as_posix(),sha256=filehash(path)))
        counts.update(value['census']);writers.add(row['writer'])
        if value['census'].get('candidate_nonlocal_events',0):candidate_writers.add(row['writer'])
        bindings.append(dict(session=row['session'],raw_sha256=meta.get('source_sha256'),prepared_sha256=row.get('sha256')))
        progress(output/'PROGRESS.json',dict(phase='verify-source' if verification else 'source',done=i+1,total=config['expected_sessions']))
    if len(index)!=config['expected_sessions'] or len({r['session'] for r in index})!=len(index):raise ValueError('Source population incomplete or duplicated')
    if config['mode']=='constructed' and counts['candidate_nonlocal_events']!=2:raise ValueError('Known revision count differs')
    summary=dict(card='S2-source',mode=config['mode'],sessions=len(index),writers=len(writers),census=dict(counts),candidate_writers=len(candidate_writers),
        archive_only_sessions=len(r2_index)-len(index) if config['mode']=='full' else None,
        required_analytical_events=300,required_analytical_writers=25,analytical_support_admitted=False,scientific_effect_computed=False,
        scope='Upper-bound source candidates only; first-production denominator, timing and future-link consumer remain required')
    values={'SUMMARY.json':summary,'INDEX.json':index,'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},sources=bindings)}
    if verification:
        for name,value in values.items():
            if read(output/name)!=value:raise ValueError('Complete source summary differs: '+name)
        return dict(verified=True,complete_source_replay=True)
    for name,value in values.items():write_equal(output/name,value)
    timing=output/'TIMING.json'
    if timing.exists():
        prior=read(timing)
        if prior['sessions']!=len(index) or not math.isfinite(prior['cpu_seconds']) or prior['cpu_seconds']<0:raise ValueError('Invalid retained source timing')
    else:write_equal(timing,dict(cpu_seconds=time.process_time()-start,sessions=len(index)))
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
