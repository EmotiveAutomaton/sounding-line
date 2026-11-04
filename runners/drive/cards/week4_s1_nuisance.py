"""S1 authenticated nuisance support; no recurrence outcome or effect.

DESIGN CHECK: Week4 0.5/S1; LESSONS2-5 read in this build. Known actual
insertion geometry must separate typed, prompt and API predecessors, preserve
UTF16 and paragraph boundaries, and refuse mismatched timing endpoints.
Missing controls exclude explicitly, never become zeros. Window labels cannot
choose the source or nuisance rule. Full verification reconstructs all values.
"""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,math,statistics,time
from runners.stage9.coauthor import apply_delta,units,text_of
from .timing_pmap_source import completed,bound_record
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_census import read,filehash
from .timing_d33_match import earlier

NAMES=('word_length','population_log_frequency','own_log_frequency','sentence_boundary',
       'paragraph_boundary','own_pair_log_median','time_on_task','session_order')

def configuration(mode):
    if mode not in ('constructed','timing','full'):raise ValueError('Unknown nuisance scope')
    return dict(card='S1-nuisance',mode=mode,seed=20261102,pilot_sessions=12)

def onset_geometry(typing,targets):
    """Actual immediately preceding document atom, not the word's first pair."""
    doc=units(typing['initial_document']);owners=[None]*len(doc);meta={};result={}
    for edit in typing['edits']:
        ordinal=edit['ordinal'];inserted=''.join(o['insert'] for o in edit['operations'] if 'insert' in o)
        meta[ordinal]=(edit['source'],inserted)
        doc,owners,_=apply_delta(doc,owners,{'ops':edit['operations']},insertion_owner=ordinal)
        if ordinal not in targets:continue
        if edit['source']!='user' or len(inserted)!=1:
            result[ordinal]=dict(state='unsupported',reason='not single typed onset');continue
        pos=owners.index(ordinal);prefix=text_of(doc[:pos]);previous=owners[pos-1] if pos else None
        source,chars=meta.get(previous,(None,''))
        if previous is None or source!='user' or len(chars)!=1 or not prefix:
            result[ordinal]=dict(state='unsupported',reason='predecessor not one typed atom');continue
        pair=prefix[-1].casefold()+inserted.casefold()
        if len(prefix[-1].casefold())!=1 or len(inserted.casefold())!=1:
            result[ordinal]=dict(state='unsupported',reason='casefold changes pair width');continue
        if previous!=targets[ordinal]['previous_ordinal']:
            result[ordinal]=dict(state='unsupported',reason='adjacent atom differs from timing endpoint');continue
        result[ordinal]=dict(state='supported',pair=pair,paragraph_boundary=not prefix.rsplit('\n',1)[-1].strip())
    if text_of(doc)!=typing['final_document']:raise ValueError('Exact edit replay differs')
    if set(result)!=set(targets):raise ValueError('Missing requested onset in edit stream')
    return result

def features(window,record,geometry,medians,own_counts,own_total,session_order):
    lookup={w['index']:w for w in record['words']};words=[lookup[i] for i in window['indices']]
    if [w['ordinal'] for w in words]!=window['ordinals']:raise ValueError('Window occurrence changed')
    if own_total<=0:return None,'empty own frequency history'
    internal=window['ordinals'][1:];pairs=[];paragraphs=[]
    for ordinal in internal:
        g=geometry.get(ordinal)
        if not g or g['state']!='supported':return None,'missing exact onset pair'
        median=medians.get(g['pair'])
        if median is None or median<=0:return None,'missing positive own pair median'
        pairs.append(math.log(median));paragraphs.append(int(g['paragraph_boundary']))
    if not pairs:return None,'no internal onsets'
    # Frequencies use completed earlier sessions only, without target/future words.
    # Floor one unseen occurrence matches the inherited population-frequency rule.
    value=[statistics.mean(w['length'] for w in words),statistics.mean(w['population_log_frequency'] for w in words),
           statistics.mean(math.log(max(own_counts[w['token']],1)/own_total) for w in words),
           statistics.mean(int(w['sentence_start']) for w in words[1:]),statistics.mean(paragraphs),statistics.mean(pairs),
           words[0]['seconds']-record['timestamp'],session_order]
    if not all(map(math.isfinite,value)) or value[-2]<0:raise ValueError('Invalid nuisance value')
    return value,None

def known_check():
    edits=[dict(ordinal=1,source='user',operations=[dict(insert='a')]),
           dict(ordinal=2,source='user',operations=[dict(retain=1),dict(insert=' ')]),
           dict(ordinal=3,source='user',operations=[dict(retain=2),dict(insert='b')]),
           dict(ordinal=4,source='api',operations=[dict(retain=3),dict(insert='x')]),
           dict(ordinal=5,source='user',operations=[dict(retain=4),dict(insert='c')]),
           dict(ordinal=6,source='user',operations=[dict(retain=5),dict(insert='\n')]),
           dict(ordinal=7,source='user',operations=[dict(retain=6),dict(insert='é')])]
    typing=dict(initial_document='',edits=edits,final_document='a bxc\né')
    targets={i:dict(previous_ordinal=i-1) for i in (1,3,5,7)};g=onset_geometry(typing,targets)
    assert g[1]['state']==g[5]['state']=='unsupported'
    assert g[3]['pair']==' b' and not g[3]['paragraph_boundary']
    assert g[7]['pair']=='\né' and g[7]['paragraph_boundary']
    targets[3]['previous_ordinal']=1;assert onset_geometry(typing,targets)[3]['state']=='unsupported'
    words=[dict(index=i,ordinal=o,token=t,length=1,population_log_frequency=-2.,sentence_start=bool(i),seconds=10.+i) for i,(o,t) in enumerate(((1,'a'),(3,'b')))]
    window=dict(indices=[0,1],ordinals=[1,3]);record=dict(words=words,timestamp=10.)
    x,reason=features(window,record,g,{' b':.5},Counter(a=3,b=1),4,2)
    assert reason is None and x==[1.,-2.,(math.log(.75)+math.log(.25))/2,1.,0.,math.log(.5),0.,2]
    assert features(window,record,g,{},Counter(a=3,b=1),4,2)[0] is None
    return dict(typed_space_pair=True,api_predecessor_refused=True,initial_predecessor_refused=True,paragraph=True,endpoint_mismatch_refused=True,known_feature_vector=True,missing_ruler_refused=True)

def load(inputs):
    if set(inputs)!={'histories_completion','typing_completion','pmap_completion'}:raise ValueError('Exact inputs required')
    hc=Path(inputs['histories_completion']);hp=read(hc.parent/'PLAN.json');hs=hc.parent/'output'
    completed(hc,hs/'SUMMARY.json');summary=read(hs/'SUMMARY.json')
    if summary['mode']!='full':raise ValueError('Full history preparation required')
    p6=hp['inputs']['p6_index'];completed(hp['inputs']['p6_completion'],p6)
    records=[bound_record(p6,r) for r in read(p6)];wc=Path(hp['inputs']['windows_completion'])
    completed(wc,wc.parent/'output/WINDOWS.json.gz');windows=gzread(wc.parent/'output/WINDOWS.json.gz')
    wp=read(wc.parent/'PLAN.json');tc=Path(wp['inputs']['timing_completion'])
    completed(tc,tc.parent/'output/INTERVALS.json.gz');intervals=gzread(tc.parent/'output/INTERVALS.json.gz')
    by_writer=defaultdict(list);medians=defaultdict(lambda:defaultdict(list));bindings=[]
    for r in records:by_writer[r['writer']].append(r)
    for path in sorted((Path(inputs['pmap_completion']).parent/'output/sessions').glob('*.json.gz')):
        completed(inputs['pmap_completion'],path);bag=gzread(path)
        for pair,values in bag['bigram_intervals'].items():medians[bag['writer']][pair].extend(values)
        bindings.append(dict(session=bag['session'],sha256=filehash(path)))
    ids={r['session']:r['writer'] for r in records};wids={r['session']:r['writer'] for r in windows}
    if len(ids)!=1399 or ids!=wids or set(ids)!=set(intervals) or set(ids)!={b['session'] for b in bindings}:raise ValueError('Exact population join failed')
    medians={w:{k:statistics.median(v) for k,v in d.items() if v} for w,d in medians.items()}
    return records,windows,intervals,by_writer,medians

def run(output,inputs,config,verification=False):
    if config!=configuration(config['mode']):raise ValueError('Frozen nuisance configuration required')
    output=Path(output);start=time.process_time();checks=known_check()
    if config['mode']=='constructed':
        if inputs:raise ValueError('No corpus in constructed check')
        values={'SUMMARY.json':dict(known_checks=checks,scientific_effect_computed=False)}
    else:
        records,windows,intervals,by_writer,medians=load(inputs);lookup={r['session']:r for r in records}
        hc=Path(inputs['histories_completion']);typing=Path(inputs['typing_completion']);candidates=[];counts=Counter();support=defaultdict(Counter)
        for session in windows:
            sid=session['session'];path=hc.parent/'output/sessions'/(hashlib.sha256(sid.encode()).hexdigest()+'.json.gz')
            if not path.exists():counts['no_informative_window_sessions']+=1;continue
            completed(hc,path)
            if not gzread(path)['proof']['supported']:counts['no_history_sessions']+=1;continue
            tpath=typing.parent/'output/sessions'/(hashlib.sha256(sid.encode()).hexdigest()+'.json.gz')
            candidates.append((session,tpath))
        total_candidates=len(candidates)
        if config['mode']=='timing':candidates=sorted(candidates,key=lambda s:(-s[1].stat().st_size,s[0]['session']))[:config['pilot_sessions']]
        source_seconds=time.process_time()-start;started=time.process_time();bindings=[]
        for i,(session,tpath) in enumerate(candidates):
            completed(typing,tpath);typed=gzread(tpath);sid=session['session'];record=lookup[sid]
            if (typed['session'],typed['writer'])!=(sid,session['writer']):raise ValueError('Typing identity mismatch')
            candidates_windows=[w for w in session['windows'] if w['grams'] and w['class'] in ('flow','hesitant')]
            requested={o for w in candidates_windows for o in w['ordinals'][1:]};times={r['ordinal']:r for r in intervals[sid] if r['onset'] and r['ordinal'] in requested}
            if set(times)!=requested:raise ValueError('Missing frozen onset interval')
            geometry=onset_geometry(typed,times);own=Counter(w['token'] for r in earlier(by_writer[session['writer']],record) for w in r['words'] if w['is_word']);rows=[]
            for window in candidates_windows:
                x,reason=features(window,record,geometry,medians[session['writer']],own,sum(own.values()),session['session_order'])
                rows.append(dict(start_ordinal=window['start_ordinal'],nuisance=x,exclusion=reason))
                counts[reason or 'eligible_windows']+=1
                if x is not None:support[session['writer']][window['class']]+=1
            dest=output/'sessions'/(hashlib.sha256(sid.encode()).hexdigest()+'.json.gz');value=dict(session=sid,writer=session['writer'],rows=rows)
            if verification:
                if gzread(dest)!=value:raise ValueError('Nuisance replay differs')
            else:gzip_equal(dest,value)
            bindings.append(dict(session=sid,typing_sha256=filehash(tpath),nuisance_sha256=filehash(dest)))
            progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'nuisances',done=i+1,total=len(candidates)))
        summary=dict(mode=config['mode'],sessions=len(candidates),counts=dict(counts),names=NAMES,known_checks=checks,
            supported_writers=sum(v['flow']>=20 and v['hesitant']>=20 for v in support.values()) if config['mode']=='full' else None,
            required_writers=25,scientific_effect_computed=False,scope='Inherited nuisance and source support only; no recurrence scoring.')
        values={'SUMMARY.json':summary,'PRIVATE_SUPPORT.json':dict(support),'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},sources=bindings)}
        if not verification:write_equal(output/'TIMING.json',dict(source_cpu_seconds=source_seconds,session_cpu_seconds=time.process_time()-started,
            projected_full_cpu_seconds_with_fresh_verification=3*(source_seconds+(time.process_time()-started)*total_candidates/max(1,len(candidates)))))
    for name,value in values.items():
        if verification:
            # JSON roundtrip normalizes the immutable tuple of column names.
            import json
            if read(output/name)!=json.loads(json.dumps(value)):raise ValueError('Nuisance summary replay differs')
        else:write_equal(output/name,value)
    return dict(verified=True,complete_source_replay=True) if verification else dict(status='complete',scientific_admission=False)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
