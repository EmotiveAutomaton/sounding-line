"""T2 final-sentence ancestry and process labels, before any feature fitting.

DESIGN CHECK: Week4 T2/defaults and Week5 BK/K-M; LESSONS2-5 and
CONTROLS1-7. Unique ancestry is required for first-production labels. Missing,
merged and deleted units remain a census, never negative process labels.
"""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib,json,time
from runners.stage9.coauthor import units,delta_ops
from . import week4_revision_source_h1 as revision
from .week4_revision_utf16_h1 import text_of
from .week5_bk_s2_source import private_key
from .timing_events import source_sessions
from .timing_pmap_source import completed,bound_record
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_census import read,filehash

SEED=20261102
ORIGINS={'typed','prompt','accepted','accepted_edited','api_unknown'}


def materialize(events,first_units,reference,timeline):
    if not events or events[0]['eventName']!='system-initialize':raise ValueError('Initialization required')
    stamps=[float(e['eventTimestamp']) for e in events]
    if stamps!=sorted(stamps) or any(not __import__('math').isfinite(s) for s in stamps):raise ValueError('Invalid source chronology')
    doc=units(events[0]['currentDoc']);identities=[None]*len(doc);members=defaultdict(set);seen=set();discovered=[];pending=False
    by_ordinal=defaultdict(list)
    for unit in first_units:by_ordinal[unit['completed_ordinal']].append(unit)
    def inside(position):
        if not 0<position<len(identities):return set()
        a,b=position-1,position
        while a>=0 and identities[a] is None and chr(doc[a]).isspace():a-=1
        while b<len(identities) and identities[b] is None and chr(doc[b]).isspace():b+=1
        return members.get(identities[a],set()) & members.get(identities[b],set()) if a>=0 and b<len(identities) else set()
    for ordinal,event in enumerate(events):
        if event['eventName']=='suggestion-select':pending=True
        ops=delta_ops(event.get('textDelta'))
        if not ops:continue
        user=event.get('eventSource')=='user';out=[];newids=[];position=0;insert_index=0;deleted=set();new_members=[]
        for op_index,op in enumerate(ops):
            if 'retain' in op:
                n=op['retain']
                if type(n)is not int or n<0 or position+n>len(doc):raise ValueError('Invalid retain')
                out+=doc[position:position+n];newids+=identities[position:position+n];position+=n;deleted=set();continue
            touched=inside(position)
            if 'delete' in op:
                n=op['delete']
                if type(n)is not int or n<0 or position+n>len(doc):raise ValueError('Invalid delete')
                for identity in identities[position:position+n]:touched |= members.get(identity,set())
                deleted=touched;position+=n
            else:
                if op_index and 'delete' in ops[op_index-1]:touched |= deleted
                if op_index+1<len(ops) and 'delete' in ops[op_index+1]:
                    n=ops[op_index+1]['delete']
                    if type(n)is not int or n<0 or position+n>len(doc):raise ValueError('Invalid replacement')
                    for identity in identities[position:position+n]:touched |= members.get(identity,set())
                value=units(op['insert']);ids=[(ordinal,insert_index+i) if user else ('api',ordinal,insert_index+i) for i in range(len(value))]
                out+=value;newids+=ids;insert_index+=len(value);new_members += [(identity,set(touched)) for identity in ids]
        out+=doc[position:];newids+=identities[position:];text_of(out)
        if pending and not user:
            before,after=text_of(doc),text_of(out);extra=len(out)-len(doc)
            if not before.endswith('\n') or not after.startswith(before[:-1]) or not after.endswith('\n') or extra<0:raise ValueError('Noncanonical accepted append')
            newids=identities[:-1]+[('api',ordinal,i) for i in range(extra)]+identities[-1:];pending=False
            # Canonical acceptance is an append even if Quill encodes a whole
            # document replacement. Restored old IDs keep old ancestry; new
            # accepted IDs must not inherit temporary replacement ancestry.
            new_members=[]
        for identity,linked in new_members:
            if linked:members[identity].update(linked);seen.add(identity)
        doc,identities=out,newids
        if not any(any(c in op.get('insert','') for c in '.!?\n') for op in ops):continue
        found=[]
        owners=[identity[0] if identity is not None and isinstance(identity[0],int) else None for identity in identities]
        for span in revision.sentences(doc,owners):
            if not span['complete'] or not span['fully_typed']:continue
            a,b=span['content_start_utf16'],span['content_end_utf16'];ids=set(identities[a:b])-{None}
            if ids & seen:continue
            seen.update(ids);index=len(discovered);content=text_of(doc[a:b]);found.append((index,content));discovered.append((ordinal,content))
            for identity in ids:members[identity].add(index)
        expected=[(r['sentence_index'],r['text']) for r in by_ordinal[ordinal]]
        if found!=expected:raise ValueError('T2 first-production ancestry disagrees with S2')
    if discovered!=[(r['completed_ordinal'],r['text']) for r in first_units]:raise ValueError('T2 first-production population differs')
    final=text_of(doc)
    if final!=timeline['final_document'] or hashlib.sha256(final.encode()).hexdigest()!=reference['final_document_sha256']:raise ValueError('T2 final document mismatch')
    mask=bytes(identity is not None and isinstance(identity[0],int) for identity in identities)
    if hashlib.sha256(mask).hexdigest()!=reference['final_typed_mask_sha256']:raise ValueError('T2 final typed mask differs')
    origins=[];cursor=0
    for span in timeline['final_spans']:
        if span['origin'] not in ORIGINS:raise ValueError('Unknown R2 origin')
        values=units(span['text'])
        if span.get('start_utf16',cursor)!=cursor or span.get('end_utf16',cursor+len(values))!=cursor+len(values):raise ValueError('R2 provenance extent differs')
        origins += [span['origin']]*len(values);cursor+=len(values)
    if ''.join(s['text'] for s in timeline['final_spans'])!=final or len(origins)!=len(doc):raise ValueError('R2 provenance coverage differs')
    if bytes(o=='typed' for o in origins)!=mask:raise ValueError('R2 final typed provenance differs')
    spans=revision.sentences(doc,[i if o=='typed' else None for i,o in enumerate(origins)])
    rows=[];census=Counter();surviving=Counter()
    for index,span in enumerate(spans):
        a,b=span['content_start_utf16'],span['content_end_utf16'];text=text_of(doc[a:b])
        if not text.strip():continue
        ancestors=set().union(*(members.get(identity,set()) for identity in identities[a:b]));surviving.update(ancestors)
        used={origins[i] for i in range(a,b) if not chr(doc[i]).isspace()}
        origin='typed' if used=={'typed'} else 'accepted' if used and used<={'accepted','accepted_edited'} else 'prompt' if used=={'prompt'} else 'api_unknown' if used=={'api_unknown'} else 'mixed'
        census['final_'+origin]+=1;census['ancestor_count_'+str(min(2,len(ancestors)))]+=1
        labels=dict(a=None,b=None,c=0 if origin=='typed' else 1 if origin=='accepted' else None);state='unique' if len(ancestors)==1 else 'absent' if not ancestors else 'multiple'
        if len(ancestors)==1:
            unit=first_units[next(iter(ancestors))];labels['b']=int(bool(unit['later_revisions']))
            # S2 assigns thirds before its regression-covariate checks. A
            # missing S2 nuisance does not erase an observed target class.
            if unit.get('class') in ('flow','hesitant'):labels['a']=int(unit['class']=='hesitant')
            else:census['unique_ancestor_without_a_timing']+=1
        rows.append(dict(index=index,text=text,position=index/max(1,len(spans)-1),origin=origin,ancestry=state,ancestor_indices=sorted(ancestors),labels=labels,complete=span['complete']))
    census['first_production_units']=len(first_units);census['initial_units_without_final_feature']=sum(i not in surviving for i in range(len(first_units)))
    census['initial_units_split_across_final_sentences']=sum(n>1 for n in surviving.values())
    return rows,dict(census)


def stream(inputs,config):
    if config['mode']=='constructed':
        data=read(inputs['constructed_source'])
        if data.get('constructed') is not True:raise ValueError('Constructed input marker required')
        for i,item in enumerate(data['sessions']):yield dict(session='constructed-'+str(i),writer='constructed-'+str(i),genre='creative'),lambda item=item:item
        return
    source=read(inputs['source_inputs']);salt=Path(inputs['salt']).read_bytes();s2=Path(inputs['s2_completion']);path=s2.parent/'output/PRIVATE_SENTENCES.json.gz';completed(s2,path)
    sessions={r['session']:r for r in gzread(path)}
    rev=Path(inputs['revision_completion']);ri=rev.parent/'output/INDEX.json';completed(rev,ri);revindex={r['session']:r for r in read(ri)}
    r2=Path(inputs['r2_completion']);r2i=r2.parent/'output/INDEX.json';completed(r2,r2i);r2index={r['session']:r for r in read(r2i)}
    if len(sessions)!=1399 or len(revindex)!=1399 or len(r2index)!=1445:raise ValueError('T2 complete population required')
    for row,timeline,meta in source_sessions(source,'raw_roster'):
        session=private_key(salt,row['session']);writer=private_key(salt,row['writer']);first=sessions[session]
        if first['writer']!=writer:raise ValueError('T2 S2 writer mismatch')
        def payload(row=row,meta=meta,first=first):
            ref=bound_record(ri,revindex[row['session']]);r=bound_record(r2i,r2index[row['session']])
            if ref['writer']!=row['writer'] or r['writer']!=row['writer'] or not r['record']['exact']:raise ValueError('T2 exact provenance join failed')
            events=[json.loads(s) for s in (Path(source['repo_root'])/meta['path']).read_text('utf8').splitlines() if s.strip()]
            return dict(events=events,first_units=first['sentences'],reference=ref,timeline=r['record']['timeline'])
        yield dict(session=session,writer=writer,genre=meta['domain']),payload


def run(output,inputs,config,verification=False):
    expected=config.get('expected_sessions');quantum=config.get('max_new_draws')
    if config!=dict(card='BK-T2-source',mode=config.get('mode'),expected_sessions=expected,max_new_draws=quantum) or config['mode'] not in ('corpus','constructed') or type(expected)is not int or expected<1 or type(quantum)is not int or quantum<1:raise ValueError('Frozen source configuration required')
    if config['mode']=='corpus' and expected!=1399:raise ValueError('Full corpus required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);binding=dict(inputs={k:filehash(v) for k,v in inputs.items()},config={k:v for k,v in config.items() if k!='max_new_draws'})
    if verification:
        if read(output/'BINDING.json')!=binding:raise ValueError('T2 source binding differs')
    else:write_equal(output/'BINDING.json',binding)
    rows=[];census=Counter();new=0;started=time.process_time()
    for i,(identity,payload) in enumerate(stream(inputs,config)):
        path=output/'sessions'/f'{i:05d}.json.gz'
        if path.exists() and not verification:
            value=gzread(path)
            if value['identity']!=identity:raise ValueError('T2 cached identity differs')
        else:
            values,counts=materialize(**payload());value=dict(identity=identity,rows=values,census=counts);new+=1
            if verification:
                if value!=gzread(path):raise ValueError('T2 fresh source projection differs')
            else:gzip_equal(path,value)
        rows += [{**r,**identity} for r in value['rows']];census.update(value['census'])
        progress(output/'PROGRESS.json',dict(done=i+1,total=expected,new_sessions=new,phase='verify' if verification else 'source'))
        if not verification and i+1==max(1,(expected+19)//20) and not (output/'PILOT.json').exists():write_equal(output/'PILOT.json',dict(done=i+1,total=expected,cpu_seconds=time.process_time()-started))
        if (output/'YIELD_REQUEST.json').exists() or not verification and new>=quantum and i+1<expected:
            progress(output/('VERIFY_CHECKPOINT.json' if verification else 'CHECKPOINT.json'),dict(done=i+1,total=expected,full_verification=False))
            return dict(status='yielded',reason='T2 complete source session boundary')
    if i+1!=expected:raise ValueError('Incomplete T2 source')
    summary=dict(sessions=expected,sentences=len(rows),writers=len({r['writer'] for r in rows}),census=dict(census),scientific_effect_computed=False,constructed=config['mode']=='constructed')
    if verification:
        if rows!=gzread(output/'PRIVATE_SENTENCES.json.gz') or summary!=read(output/'SUMMARY.json'):raise ValueError('T2 complete source differs')
        return dict(verified=True,all_source_sessions_recomputed=True)
    gzip_equal(output/'PRIVATE_SENTENCES.json.gz',rows);write_equal(output/'SUMMARY.json',summary);return dict(status='complete')


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
