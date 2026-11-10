"""S2 isolated canonical-append ancestry repair; original scientific mapping.

Full-document Quill append encodings restore original IDs and clear temporary
replacement ancestry from newly appended API IDs. Original source is retained.

DESIGN CHECK: LESSONS2-5, CONTROLS1-7 and Week4 S2/0.5. Stable insertion
identities retain deleted first productions and distinguish later versions.
Outcome provenance is initial typed production, not final survival. AI-only
edits remain competing events; they never count as user revisions.
"""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib,hmac,json,math,re,time
import numpy as np
from runners.stage9.coauthor import units,delta_ops
from .week4_revision_utf16_h1 import text_of
from . import week4_revision_source_h1 as revision
from .week4_timing_ruler import stretch_hesitancy,thirds
from .week4_typed_windows import produced_words
from .timing_text import TOKEN,WORD
from .timing_pmap_source import completed,bound_record
from .timing_events import source_sessions
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress

SEED=20261102

def private_key(salt,value):return hmac.new(salt,value.encode(),hashlib.sha256).hexdigest()

def project(events,p6,intervals,prior_revision):
    if not events or events[0]['eventName']!='system-initialize':raise ValueError('Initialization required')
    stamps=[float(e['eventTimestamp'])/1000 for e in events]
    if not all(map(math.isfinite,stamps)) or stamps!=sorted(stamps):raise ValueError('Invalid source chronology')
    doc=units(events[0]['currentDoc']);identities=[None]*len(doc);membership=defaultdict(set)
    produced=[];seen=set();census=Counter();pairs=defaultdict(list);pending=False
    original_words,word_counts=produced_words(p6['words']);census.update(word_counts)
    word_by_onset={w['ordinal']:w for w in original_words}
    timed={r['ordinal']:r for r in intervals};revisions={r['ordinal']:r for r in prior_revision['events']}
    if len(timed)!=len(intervals):raise ValueError('Duplicate timing interval')
    def members_at(ids,position):
        if not 0<position<len(ids):return set()
        left=position-1;right=position
        while left>=0 and ids[left] is None and chr(doc[left]).isspace():left-=1
        while right<len(ids) and ids[right] is None and chr(doc[right]).isspace():right+=1
        return membership.get(ids[left],set()) & membership.get(ids[right],set()) if left>=0 and right<len(ids) else set()
    for ordinal,event in enumerate(events):
        if event['eventName']=='suggestion-select':pending=True
        ops=delta_ops(event.get('textDelta'))
        if not ops:continue
        user=event.get('eventSource')=='user';before=doc;oldids=identities
        out=[];newids=[];position=0;insert_index=0;hits=defaultdict(set);new_members=[]
        # Mapping each delta operation separately avoids linking an edit in one
        # merged sentence region to every earlier sentence in that region.
        for op_index,op in enumerate(ops):
            if 'retain' in op:
                n=op['retain']
                if type(n)is not int or n<0 or position+n>len(doc):raise ValueError('Invalid retain')
                out.extend(doc[position:position+n]);newids.extend(identities[position:position+n]);position+=n;continue
            touched=members_at(identities,position)
            if 'delete' in op:
                n=op['delete']
                if type(n)is not int or n<0 or position+n>len(doc):raise ValueError('Invalid delete')
                for identity in identities[position:position+n]:touched |= membership.get(identity,set())
                # A deletion is an overlap even at a sentence's first character.
                for candidate in touched:hits[candidate].add(op_index)
                position+=n
            else:
                values=units(op['insert']);ids=[(ordinal,insert_index+i) if user else ('api',ordinal,insert_index+i) for i in range(len(values))]
                # Quill may encode replacement as insert-then-delete at the
                # same old cursor. Inherit the replaced span in either order.
                if op_index+1<len(ops) and 'delete' in ops[op_index+1]:
                    n=ops[op_index+1]['delete']
                    if type(n)is not int or n<0 or position+n>len(doc):raise ValueError('Invalid replacement delete')
                    for identity in identities[position:position+n]:touched |= membership.get(identity,set())
                # A replacement may follow a deletion of the old complete span.
                if op_index and 'delete' in ops[op_index-1]:
                    touched |= {candidate for candidate,operations in hits.items() if op_index-1 in operations}
                for candidate in touched:hits[candidate].add(op_index)
                for identity in ids:new_members.append((identity,set(touched)))
                out.extend(values);newids.extend(ids);insert_index+=len(values)
                if user and len(values)==1 and position>0 and ordinal in timed:
                    previous=chr(doc[position-1]);current=op['insert']
                    if previous.isalpha() and current.isalpha():pairs[(previous+current).casefold()].append(timed[ordinal]['interval_seconds'])
        out.extend(doc[position:]);newids.extend(identities[position:]);after_text=text_of(out)
        if pending and not user:
            old_text=text_of(before)
            if not old_text.endswith('\n') or not after_text.startswith(old_text[:-1]) or not after_text.endswith('\n'):raise ValueError('Noncanonical accepted append')
            extra=len(out)-len(before)
            if extra<0:raise ValueError('Invalid accepted extent')
            newids=oldids[:-1]+[('api',ordinal,i) for i in range(extra)]+oldids[-1:];pending=False
            # Canonical acceptance restores the unchanged prefix; newly appended
            # API identities inherit no temporary full-replacement ancestry.
            new_members=[]
        record=revisions.get(ordinal)
        for candidate,operations in hits.items():
            target=produced[candidate]
            if user:
                matched=[]
                for sentence in (record or {}).get('targets',[]):
                    if operations & {c['operation'] for c in sentence['changes']} and sentence['complete'] and sentence['distance_sentences']>=1:
                        matched.append(sentence)
                if matched:
                    # Paragraph distance uses the actual old delta anchor. API
                    # text is context here, not evidence of user authorship.
                    positions=[c['position_utf16'] for sentence in matched for c in sentence['changes'] if c['operation'] in operations]
                    paragraphs=max(text_of(before[p:]).rstrip().count('\n') for p in positions)
                    target['later_revisions'].append(dict(ordinal=ordinal,lag_seconds=stamps[ordinal]-target['completed_seconds_absolute'],
                          paragraph_nonlocal=paragraphs>=1,current_target_fully_typed=any(s['fully_typed'] for s in matched)))
            else:target['intervening_nonuser_edit']=True
        for identity,linked in new_members:
            if linked:membership[identity].update(linked);seen.add(identity)
        doc,identities=out,newids
        # New complete sentences can appear at punctuation/newline boundaries.
        # Ordinary interiors cannot create a new first-production denominator.
        if not any(any(c in op.get('insert','') for c in '.!?\n') for op in ops):continue
        owners=[identity[0] if identity is not None and isinstance(identity[0],int) else None for identity in identities]
        spans=revision.sentences(doc,owners)
        for span in spans:
            if not span['complete'] or not span['fully_typed']:continue
            a,b=span['content_start_utf16'],span['content_end_utf16'];ids=set(identities[a:b])-{None}
            if ids & seen:continue
            seen.update(ids);census['first_complete_typed_sentences']+=1
            content=text_of(doc[a:b]);offset=[0]
            for char in content:offset.append(offset[-1]+len(units(char)))
            words=[];onsets=[];reason=None
            for token in TOKEN.finditer(content):
                if not WORD.fullmatch(token.group()):continue
                identity=identities[a+offset[token.start()]];birth=identity[0]
                word=word_by_onset.get(birth);timing=timed.get(birth)
                if word is None or word['token']!=token.group().casefold() or word['completed_ordinal']>ordinal:
                    reason='missing_first_word_identity';break
                if timing is None or not timing['onset']:
                    if words:reason='missing_onset_timing';break
                    # The first word's onset is excluded by the commissioned
                    # stretch rule, so its absent interval is not invented.
                    timing=dict(onset=True,interval_seconds=0.,fast=0.,first_onset_unobserved=True)
                words.append(word);onsets.append(timing)
            if not reason and (len(words)<2 or any(b['ordinal']<=a['ordinal'] for a,b in zip(words,words[1:]))):reason='nonforward_or_short_production'
            hs=stretch_hesitancy(onsets) if not reason else dict(state=reason,hesitancy=None)
            first=words[0]['seconds']-stamps[0] if words else stamps[ordinal]-stamps[0]
            item=dict(sentence_index=len(produced),text=content,completed_ordinal=ordinal,completed_seconds_absolute=stamps[ordinal],
                start_seconds=first,remaining_seconds=stamps[-1]-stamps[ordinal],distance_sentences=span['distance_sentences'],
                paragraph_start=not text_of(doc[:a]).strip() or text_of(doc[:a]).rstrip(' \t').endswith('\n'),
                sentence_boundary=1,words=[{k:w.get(k) for k in ('token','ordinal','length','population_log_frequency')} for w in words],
                word_count=len(words),timing_state=hs['state'],hesitancy=hs['hesitancy'],intervening_nonuser_edit=False,later_revisions=[])
            produced.append(item)
            for identity in ids:membership[identity].add(item['sentence_index'])
            census['timing_'+hs['state']]+=1
    final=text_of(doc)
    if hashlib.sha256(final.encode()).hexdigest()!=prior_revision['final_document_sha256']:raise ValueError('Full revision replay final document differs')
    mask=bytes(identity is not None and isinstance(identity[0],int) for identity in identities)
    if hashlib.sha256(mask).hexdigest()!=prior_revision['final_typed_mask_sha256']:raise ValueError('Full revision replay typed provenance differs')
    if final!=p6.get('final_document',final):raise ValueError('P6 final document differs')
    for row in produced:
        if any(r['lag_seconds']<=0 for r in row['later_revisions']):raise ValueError('Nonfuture revision linkage')
    return produced,dict(census),dict(pairs)

def classify_and_controls(sessions):
    by_writer=defaultdict(list);bigram=defaultdict(lambda:defaultdict(list));words=defaultdict(list)
    for session in sessions:
        by_writer[session['writer']].extend(r for r in session['sentences'] if r['timing_state']=='eligible')
        for key,value in session.pop('bigram_intervals').items():bigram[session['writer']][key].extend(value)
        words[session['writer']].append(session)
    for writer,rows in by_writer.items():
        labels,cuts=thirds([r['hesitancy'] for r in rows])
        for row,label in zip(rows,labels):row['class']=label
    for writer,group in words.items():
        medians={k:float(np.median(v)) for k,v in bigram[writer].items()};all_intervals=[v for values in bigram[writer].values() for v in values]
        fallback=float(np.median(all_intervals)) if all_intervals else None
        history=Counter();total=0
        for session in sorted(group,key=lambda s:(s['timestamp'],s['session'])):
            allwords=session.pop('first_words');births={}
            for word in sorted(allwords,key=lambda w:w['ordinal']):
                births[word['ordinal']]=math.log((history[word['token']]+1)/(total+len(history)+1))
                history[word['token']]+=1;total+=1
            for row in session['sentences']:
                if row['timing_state']!='eligible':continue
                ws=row['words'];freq=[w['population_log_frequency'] for w in ws]
                if any(x is None or not math.isfinite(x) for x in freq):row['timing_state']='missing_population_frequency';continue
                pair_values=[medians.get(w['token'][i:i+2],fallback) for w in ws for i in range(len(w['token'])-1)]
                if not pair_values or any(x is None or x<=0 for x in pair_values):row['timing_state']='missing_bigram_ruler';continue
                row['controls']=dict(sentence_length=len(ws),mean_word_length=float(np.mean([w['length'] for w in ws])),
                    population_log_frequency=float(np.mean(freq)),own_prior_log_frequency=float(np.mean([births[w['ordinal']] for w in ws])),
                    bigram_log_seconds=float(np.mean(np.log(pair_values))),paragraph_boundary=int(row['paragraph_start']),
                    sentence_boundary=1,time_on_task_minutes=row['start_seconds']/60,session_order=session['session_order'],
                    distance_sentences=row['distance_sentences'],remaining_minutes=row['remaining_seconds']/60)

def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time()
    if config=={'card':'BK-S2-inputs','seed':SEED,'mode':'constructed'}:
        fixture=read(inputs['constructed_source'])
        if fixture.get('constructed') is not True:raise ValueError('Constructed source marker required')
        values,counts,pairs=project(fixture['events'],fixture['p6'],fixture['intervals'],fixture['revision'])
        original,_=produced_words(fixture['p6']['words'])
        sessions=[dict(session='constructed-session',writer='constructed-writer',genre='creative',timestamp=0,session_order=0,
                       sentences=values,bigram_intervals=pairs,first_words=original)]
        if (output/'YIELD_REQUEST.json').exists():
            write_equal(output/('VERIFY_CHECKPOINT.json' if verification else 'CHECKPOINT.json'),dict(sessions=1,restart_from_authenticated_input_required=True))
            return dict(status='yielded',reason='S2 owner request at complete constructed session boundary')
        classify_and_controls(sessions)
        result=dict(constructed=True,counts=counts)
        if verification:
            if sessions!=gzread(output/'PRIVATE_SENTENCES.json.gz') or result!=read(output/'SUMMARY.json'):raise ValueError('Constructed complete S2 source replay differs')
            return dict(verified=True,all_source_cells_replayed=True,constructed=True)
        gzip_equal(output/'PRIVATE_SENTENCES.json.gz',sessions);write_equal(output/'SUMMARY.json',result)
        return dict(status='complete',constructed=True)
    if config!={'card':'BK-S2-inputs','seed':SEED,'expected_sessions':1399}:raise ValueError('Frozen complete S2 source configuration required')
    rev=Path(inputs['revision_completion']);revroot=rev.parent/'output';completed(rev,revroot/'INDEX.json')
    revindex={r['session']:r for r in read(revroot/'INDEX.json')}
    completed(inputs['p6_completion'],inputs['p6_index']);pindex={r['session']:r for r in read(inputs['p6_index'])}
    timing=Path(inputs['timing_completion']);tr=timing.parent/'output'
    for name in ('PRIVATE_ROSTER.json','INTERVALS.json.gz'):completed(timing,tr/name)
    roster={r['session']:r for r in read(tr/'PRIVATE_ROSTER.json')};intervals=gzread(tr/'INTERVALS.json.gz')
    if len(revindex)!=1399 or set(revindex)!=set(pindex) or set(pindex)!=set(roster) or set(roster)!=set(intervals):raise ValueError('S2 complete source population mismatch')
    source=read(inputs['source_inputs']);salt=Path(inputs['salt']).read_bytes();sessions=[];census=Counter()
    for i,(row,timeline,meta) in enumerate(source_sessions(source,'raw_roster')):
        session=row['session'];old=bound_record(revroot/'INDEX.json',revindex[session]);p6=bound_record(inputs['p6_index'],pindex[session])
        if p6['writer']!=row['writer'] or old['writer']!=row['writer'] or roster[session]['writer']!=row['writer']:raise ValueError('S2 writer identity mismatch')
        raw=Path(source['repo_root'])/meta['path'];events=[json.loads(line) for line in raw.read_text('utf8').splitlines() if line.strip()]
        values,counts,pairs=project(events,p6,intervals[session],old);census.update(counts)
        original,_=produced_words(p6['words'])
        sessions.append(dict(session=private_key(salt,session),writer=private_key(salt,row['writer']),genre=meta['domain'],
            timestamp=p6['timestamp'],session_order=roster[session]['session_order'],sentences=values,bigram_intervals=pairs,first_words=original))
        progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'prepare',sessions=i+1,total=1399))
        if not verification and i+1==70:write_equal(output/'PILOT.json',dict(sessions=70,total=1399,cpu_seconds=time.process_time()-start,forecast_cpu_seconds=(time.process_time()-start)*1399/70))
        if (output/'YIELD_REQUEST.json').exists():
            write_equal(output/('VERIFY_CHECKPOINT.json' if verification else 'CHECKPOINT.json'),dict(sessions=i+1,restart_from_authenticated_input_required=True))
            return dict(status='yielded',reason='S2 owner request; new attempt restarts bounded complete source')
    if len(sessions)!=1399:raise ValueError('S2 raw source incomplete')
    classify_and_controls(sessions)
    summary=dict(card='BK-S2-inputs',sessions=len(sessions),writers=len({s['writer'] for s in sessions}),census=dict(census),scientific_effect_computed=False,
                 primary_provenance='wholly typed at first complete production; subsequent mixed status does not remove the initial unit',
                 old_census_scope_correction='Old candidate census bounds only currently-wholly-typed targets, not all first-production units')
    binding=dict(inputs={k:filehash(v) for k,v in inputs.items()},config=config)
    if verification:
        if summary!=read(output/'SUMMARY.json') or binding!=read(output/'BINDING.json') or sessions!=gzread(output/'PRIVATE_SENTENCES.json.gz'):raise ValueError('Complete S2 source replay differs')
        return dict(verified=True,all_source_cells_replayed=True)
    gzip_equal(output/'PRIVATE_SENTENCES.json.gz',sessions);write_equal(output/'SUMMARY.json',summary);write_equal(output/'BINDING.json',binding)
    return dict(status='complete',scientific_effect_computed=False)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
