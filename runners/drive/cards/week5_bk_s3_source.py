"""S3 authenticated event materialization and outcome-blind matching."""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib,json,math,time
from . import week4_revision_source_h1 as prior
from .week4_revision_utf16_h1 import text_of,apply_delta
from .week5_bk_s2_source import private_key
from .timing_events import source_sessions
from .timing_pmap_source import completed,bound_record
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_census import read,filehash
from runners.stage9.coauthor import units,delta_ops

SEED=20261102

def transform(doc,ids,ops,ordinal,user):
    out=[];identities=[];boundaries={};position=0;insertion=0;size=0
    for op_index,op in enumerate(ops):
        boundaries.setdefault(position,len(out))
        if 'insert' in op:
            value=units(op['insert']);out+=value
            if op_index and 'delete' in ops[op_index-1]:boundaries[position]=len(out)
            identities += [('typed' if user else 'other',ordinal,insertion+i) for i in range(len(value))]
            insertion+=len(value);size+=len(op['insert'])
        else:
            n=op.get('retain',op.get('delete'))
            if type(n)is not int or n<0 or position+n>len(doc):raise ValueError('Invalid UTF16 extent')
            if 'retain' in op:
                for j in range(position,position+n):boundaries.setdefault(j,len(out)+j-position)
                out+=doc[position:position+n];identities+=ids[position:position+n]
            else:
                size+=len(text_of(doc[position:position+n]))
                for j in range(position,position+n):boundaries.setdefault(j,len(out))
            position+=n
    for j in range(position,len(doc)+1):boundaries.setdefault(j,len(out)+j-position)
    out+=doc[position:];identities+=ids[position:];text_of(out)
    return out,identities,boundaries,size

def materialize(events,reference):
    stamps=[float(e['eventTimestamp'])/1000 for e in events]
    if not stamps or not all(math.isfinite(v) for v in stamps) or stamps!=sorted(stamps):raise ValueError('Invalid event clock')
    doc=units(events[0]['currentDoc']);ids=[('prompt',0,i) for i in range(len(doc))];prompt=text_of(doc).strip()
    indexed={r['ordinal']:r for r in reference['events']};rows=[];counts=Counter();duration=stamps[-1]-stamps[0];pending=False
    for ordinal,event in enumerate(events):
        if event['eventName']=='suggestion-select':pending=True
        ops=delta_ops(event.get('textDelta'))
        if not ops:continue
        user=event.get('eventSource')=='user';after,newids,bounds,size=transform(doc,ids,ops,ordinal,user)
        if pending and not user:
            before_text,after_text=text_of(doc),text_of(after)
            if not before_text.endswith('\n') or not after_text.startswith(before_text[:-1]) or not after_text.endswith('\n'):raise ValueError('Invalid accepted append')
            extra=len(after)-len(doc)
            if extra<0:raise ValueError('Negative accepted extent')
            newids=ids[:-1]+[('accepted',ordinal,i) for i in range(extra)]+ids[-1:];pending=False
        if user and ordinal in indexed:
            targets=indexed[ordinal]['targets'];reason=None
            if size<=3:reason='small_edit'
            elif not all(t['complete'] for t in targets):reason='incomplete_target'
            labels={int(t['distance_sentences']>=1) for t in targets}
            if not reason and len(labels)!=1:reason='mixed_local_nonlocal_event'
            values=[]
            for target in targets:
                a,b=target['content_start_utf16'],target['content_end_utf16'];aa,bb=bounds[a],bounds[b]
                edited=text_of(after[aa:bb]).strip()
                if not edited:reason='whole_sentence_deleted'
                before=text_of(doc[a:b]).strip();rest=text_of(doc[:a]+doc[b:]).strip()
                next_start=next((j for j in range(b,len(doc)) if doc[j]==10),None)
                next_end=next((j for j in range((next_start or len(doc))+1,len(doc)) if doc[j]==10),len(doc))
                paragraph=text_of(doc[next_start+1:next_end]).strip() if next_start is not None else ''
                values.append(dict(before=before,after=edited,rest_before=rest,next_paragraph=paragraph,prompt=prompt,
                                   position=a/max(1,len(doc)),_ids=set(newids[aa:bb])))
            if not reason and not all(t['fully_typed'] for t in targets):
                involved={identity[0] for t in targets for identity in ids[t['content_start_utf16']:t['content_end_utf16']]}
                reason='accepted_or_mixed_target' if 'accepted' in involved else 'prompt_or_api_target'
            if reason:counts[reason]+=1
            else:
                row=dict(ordinal=ordinal,nonlocal_edit=bool(next(iter(labels))),size=size,
                         seconds=stamps[ordinal]-stamps[0],remaining=stamps[-1]-stamps[ordinal],
                         decile=min(9,int(10*(stamps[ordinal]-stamps[0])/duration)) if duration else 0,targets=values)
                rows.append(row);counts['eligible_nonlocal' if row['nonlocal_edit'] else 'eligible_local']+=1
        doc,ids=after,newids
    if hashlib.sha256(text_of(doc).encode()).hexdigest()!=reference['final_document_sha256']:raise ValueError('S3 final document mismatch')
    mask=bytes(identity[0]=='typed' for identity in ids)
    if hashlib.sha256(mask).hexdigest()!=reference['final_typed_mask_sha256']:raise ValueError('S3 typed provenance mismatch')
    spans=prior.sentences(doc,[i if identity[0]=='typed' else None for i,identity in enumerate(ids)])
    final={identity:index for index,s in enumerate(spans) for identity in ids[s['content_start_utf16']:s['content_end_utf16']]}
    for row in rows:
        for target in row['targets']:
            mapped={final[i] for i in target.pop('_ids') if i in final}
            target['final_context_status']='unique_surviving_sentence' if len(mapped)==1 else 'deleted_or_ambiguous'
            target['rest_final']=''
            if len(mapped)==1:
                span=spans[next(iter(mapped))];target['rest_final']=text_of(doc[:span['content_start_utf16']]+doc[span['content_end_utf16']:]).strip()
    return rows,dict(counts)

def match(rows):
    bins=defaultdict(lambda:[[],[]]);pairs=[]
    for row in rows:bins[(row['writer'],row['size'],row['decile'])][int(row['nonlocal_edit'])].append(row)
    def order(row):return hashlib.sha256(f'{SEED}:{row["session"]}:{row["ordinal"]}'.encode()).hexdigest()
    for key,(local,nonlocal_) in sorted(bins.items()):
        for a,b in zip(sorted(nonlocal_,key=order),sorted(local,key=order)):pairs.append((a,b))
    return pairs

def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);allrows=[];counts=Counter();start=time.process_time()
    if config==dict(card='BK-S3-source',mode='constructed'):
        fixture=read(inputs['constructed_source'])
        if fixture.get('constructed') is not True:raise ValueError('Constructed source marker required')
        stream=[(dict(session='constructed',writer='constructed'),None,dict(domain='creative'),fixture['events'],fixture['reference'])];expected=1
    elif config==dict(card='BK-S3-source',mode='corpus',expected_sessions=1399):
        source=read(inputs['source_inputs']);complete=Path(inputs['revision_completion']);index=complete.parent/'output/INDEX.json';completed(complete,index)
        indexed={r['session']:r for r in read(index)};expected=1399
        if len(indexed)!=expected:raise ValueError('Full revision-source roster required')
        def stream_source():
            for row,timeline,meta in source_sessions(source,'raw_roster'):
                raw=Path(source['repo_root'])/meta['path'];events=[json.loads(s) for s in raw.read_text('utf8').splitlines() if s.strip()]
                reference=bound_record(index,indexed[row['session']])
                if reference['writer']!=row['writer']:raise ValueError('S3 writer mismatch')
                yield row,timeline,meta,events,reference
        stream=stream_source()
    else:raise ValueError('Frozen complete S3 source config required')
    salt=Path(inputs['salt']).read_bytes() if config['mode']=='corpus' else b'constructed-privacy-salt'
    for i,(row,timeline,meta,events,reference) in enumerate(stream):
        values,census=materialize(events,reference);counts.update(census)
        for value in values:value.update(writer=private_key(salt,row['writer']),session=private_key(salt,row['session']),genre=meta['domain'])
        allrows+=values;progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'source',sessions=i+1,total=expected))
        if not verification and i+1==max(1,math.ceil(expected*.05)):write_equal(output/'PILOT.json',dict(done=i+1,total=expected,cpu_seconds=time.process_time()-start))
        if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',reason='Complete S3 source-session boundary; new attempt restarts source')
    if i+1!=expected:raise ValueError('S3 source roster incomplete')
    pairs=match(allrows);selected={ (r['session'],r['ordinal']) for pair in pairs for r in pair }
    # The label reference must rematch the original candidate frame, so all
    # eligible events remain available even if unmatched in the observed arms.
    summary=dict(constructed=config['mode']=='constructed',sessions=expected,census=dict(counts),events=len(allrows),pairs=len(pairs),matched_events=len(selected),writers=len({a['writer'] for a,b in pairs}))
    if verification:
        if gzread(output/'PRIVATE_EVENTS.json.gz')!=allrows or read(output/'SUMMARY.json')!=summary:raise ValueError('S3 complete source replay mismatch')
        return dict(verified=True,complete_source_replay=True)
    gzip_equal(output/'PRIVATE_EVENTS.json.gz',allrows);write_equal(output/'SUMMARY.json',summary)
    return dict(status='complete',scientific_effect_computed=False)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
