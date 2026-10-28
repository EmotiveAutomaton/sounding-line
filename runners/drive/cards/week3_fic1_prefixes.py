"""Exact FIC1 word-budget profiles and reusable occurrence inputs; no scores.

DESIGN CHECK: LESSONS 3-5 reread for FIC1, 2026-10-27. Under NULL and
ALTERNATIVE, every original session, exact character identity and source seal
must agree. Prefixes count complete production occurrences, including deleted
words. An undersized profile remains unsupported, never padded or dropped.
Known answers include same-delta unselected words, Unicode, chronology and
JSON round trips. No identification, scientific control or AUTH request runs.
"""
from collections import Counter, defaultdict
import json
from pathlib import Path
import time

from runners.stage14.common import read,filehash,freeze,atomic,digest
from . import week_genre_features_paths as base
from . import week3_fic1_inputs as source
from . import week3_fic1_features as features
from .timing_p6 import gzread,gzip_equal
from .timing_pmap_source import completed,indexed,bound_record

CONFIG=dict(card='FIC1-prefixes',schema=1,mode='full',sessions=990,writers=24,
            word_limits=[500,1000,2000],order='original-profile-session-chronology')
CONSTRUCTED=dict(CONFIG,mode='constructed',sessions=24,writers=3,word_limits=[2,4,8])
TIMING=dict(CONFIG,mode='timing',timing_sessions=20)


def unit(metadata,words,audit,pairs,whole):
    source.validate_words(words)
    atoms=pairs['typed_atoms']
    if isinstance(atoms,dict):
        if set(atoms)!=set(range(len(atoms))): raise ValueError('noncontiguous typed atoms')
        pairs=dict(pairs,typed_atoms=[atoms[i] for i in range(len(atoms))])
    if not isinstance(pairs['typed_atoms'],list): raise ValueError('JSON-stable typed atom list required')
    word_indices=[r['index'] for r in words if r['is_word']]
    if not word_indices: raise ValueError('original selected session has no production words')
    if any(pairs[k]!=whole[k] for k in ('bigram_counts','bigram_intervals')):
        raise ValueError('unrestricted pair replay differs from PMAP')
    wc,pc=features.counts(words)
    if wc!=whole['word_counts'] or pc!=whole['punctuation_counts']:
        raise ValueError('complete word/punctuation counts differ')
    # Calling the exact occurrence selector validates all token-to-atom joins,
    # including identities after Unicode edits and later deletions.
    match=dict(token_stop_exclusive=len(words),original_token_count=len(words),
               word_indices=word_indices,typed_words=len(word_indices))
    base.subset(dict(words=words),match,audit,pairs)
    return dict(**metadata,words=words,audit=audit,pairs=pairs,
                typed_words=len(word_indices),whole={k:whole[k] for k in features.SUFFICIENT})


def take(u,count):
    if type(count) is not int or not 0<count<=u['typed_words']: raise ValueError('invalid exact word quota')
    if count==u['typed_words']:return dict(u['whole'],typed_words=count)
    selected=[w for w in u['words'] if w['is_word']][:count]
    match=dict(token_stop_exclusive=selected[-1]['index']+1,original_token_count=len(u['words']),
               word_indices=[w['index'] for w in selected],typed_words=count)
    part=base.subset(dict(words=u['words']),match,u['audit'],u['pairs'])
    return dict(part,tc_timing_mode=u['whole']['tc_timing_mode'])


def profile(units,limit,dictionary):
    if limit is not None and (type(limit) is not int or limit<=0): raise ValueError('invalid profile word budget')
    ordered=sorted(units,key=lambda u:(u['timestamp'],u['session']))
    if not ordered or len({u['session'] for u in ordered})!=len(ordered): raise ValueError('empty or repeated profile session')
    available=sum(u['typed_words'] for u in ordered)
    if limit is not None and available<limit:
        return dict(state='unsupported',requested_words=limit,available_words=available,selected_words=0,members=[],features=None)
    remaining=available if limit is None else limit;parts=[];members=[]
    for u in ordered:
        if not remaining: break
        count=min(remaining,u['typed_words']);parts.append(take(u,count))
        members.append(dict(session=u['session'],typed_words=count,whole_session=count==u['typed_words']))
        remaining-=count
    assert remaining==0
    wc,pc=Counter(),Counter();timing=dict(within_intervals=[],onset_intervals=[],bigram_intervals=defaultdict(list),tc_timing_mode='valid')
    for part in parts:
        wc.update(part['word_counts']);pc.update(part['punctuation_counts'])
        if part['tc_timing_mode']!='invalid':
            timing['within_intervals'].extend(part['within_intervals']);timing['onset_intervals'].extend(part['onset_intervals'])
            for key,values in part['bigram_intervals'].items():timing['bigram_intervals'][key].extend(values)
    return dict(state='prepared',requested_words=limit,available_words=available,
        selected_words=sum(p['typed_words'] for p in parts),members=members,
        features=dict(style=features.style(wc,pc,dictionary),rhythm=features.rhythm(timing,dictionary)))


def full_source(inputs):
    if set(inputs)!={'source_completion','revision_completion','feature_completion'}:
        raise ValueError('fixed complete prefix predecessors required')
    sc=Path(inputs['source_completion']).resolve();fc=Path(inputs['feature_completion']).resolve()
    for terminal,module in [(sc,'runners.drive.cards.week3_fic1_inputs'),(fc,'runners.drive.cards.week3_fic1_features')]:
        completed(terminal,terminal.parent/'PLAN.json')
        if read(terminal.parent/'PLAN.json')['module']!=module:raise ValueError('unexpected predecessor producer')
    sp=read(sc.parent/'PLAN.json');fp=read(fc.parent/'PLAN.json')
    if sp['config']!=source.CONFIG or fp['config']!=features.CONFIG or Path(fp['inputs']['source_completion']).resolve()!=sc:
        raise ValueError('source/feature configuration or lineage differs')
    base_inputs=dict(matching_completion=sp['inputs']['genre_completion'],revision_completion=inputs['revision_completion'])
    rows,matches,support,pc,pp,pmap,rc,revision=base.load(base_inputs)
    if Path(sp['inputs']['pmap_completion']).resolve()!=pc or Path(fp['inputs']['pmap_completion']).resolve()!=pc:
        raise ValueError('full-production predecessor differs')
    for rel in ('output/SESSION_INDEX.json','output/PROFILES.json'):completed(sc,sc.parent/rel)
    completed(fc,fc.parent/'output/SESSION_INDEX.json')
    ix=source.unique(read(sc.parent/'output/SESSION_INDEX.json'));fi=source.unique(read(fc.parent/'output/SESSION_INDEX.json'))
    if set(ix)!=set(fi) or set(ix)!={m['session'] for m in matches} or len(ix)!=CONFIG['sessions']:
        raise ValueError('original selected cohort differs')
    dictionary=read(pc.parent/'output/STYLE_DICTIONARY.json');words=source.unique(rows)
    roster=indexed(pp['raw_roster']);p2=indexed(pp['session_index']);pins=base.normalize_pins(read(pp['source_pins']))
    root=Path(pp['repo_root']).resolve();bindings={str(Path(v).resolve()):filehash(v) for v in inputs.values()}
    def stream():
        for match in sorted(matches,key=lambda m:m['session']):
            sid=match['session'];name,old=pmap[sid];completed(pc,pc.parent/name)
            source_path=sc.parent/'output'/ix[sid]['file'];completed(sc,source_path)
            feature_path=fc.parent/'output'/fi[sid]['file'];completed(fc,feature_path)
            if filehash(source_path)!=ix[sid]['sha256'] or filehash(feature_path)!=fi[sid]['sha256']:raise ValueError('source index hash differs')
            original=read(source_path);feature=gzread(feature_path)
            metadata={k:original[k] for k in (*features.IDENTITY,'genre','half','pair')}
            if any(match[k]!=metadata[k] or feature[k]!=metadata[k] for k in metadata):raise ValueError('original membership differs')
            if [{k:w[k] for k in source.WORD_FIELDS} for w in words[sid]['words']]!=original['typed_production']:
                raise ValueError('complete production occurrence identities differ')
            if feature['production']!={k:old[k] for k in features.SUFFICIENT}:raise ValueError('complete feature predecessor differs')
            timeline=bound_record(pp['session_index'],p2[sid]);revpath=rc.parent/'output'/revision[sid]['file'];completed(rc,revpath)
            rev=bound_record(rc.parent/'output/INDEX.json',revision[sid])
            raw=(root/roster[sid]['path']).resolve();raw.relative_to(root)
            canonical=root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':raw.stem})+'.json')
            for path,key in ((raw,'raw'),(canonical,'canonical')):
                h=filehash(path)
                if old['source_hashes'][key]!=h or pins.get(path.relative_to(root).as_posix())!=h:raise ValueError('original raw/canonical pin differs')
                bindings[str(path)]=h
            if rev['source_hashes']!={k:old['source_hashes'][k] for k in ('raw','p2','p6')}:raise ValueError('revision occurrence source differs')
            if any(rev[k]!=metadata[k] or old[k]!=metadata[k] for k in features.IDENTITY):raise ValueError('cross-producer identity differs')
            events=[json.loads(line) for line in raw.read_text(encoding='utf8').splitlines()]
            pairs=base.raw_pairs(events,timeline,read(canonical))
            for path in (source_path,feature_path,revpath):bindings[str(path.resolve())]=filehash(path)
            yield unit(metadata,words[sid]['words'],rev['revision_events'],pairs,old)
    return stream(),read(sc.parent/'output/PROFILES.json'),dictionary,bindings


def run(output,inputs,config,verification=False):
    if config not in (CONFIG,CONSTRUCTED,TIMING):raise ValueError('frozen prefix configuration required')
    started=time.process_time()
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('explicit constructed prefix fixture required')
        f=read(inputs['fixture']);profiles=f['profiles'];dictionary=f['dictionary']
        stream=(unit(u['metadata'],u['words'],u['audit'],u['pairs'],u['whole']) for u in f['units'])
        bindings={str(Path(inputs['fixture']).resolve()):filehash(inputs['fixture'])}
    else:stream,profiles,dictionary,bindings=full_source(inputs)
    loaded_cpu=time.process_time()-started
    def retain(path,value):
        if verification:
            actual=gzread(path) if path.suffix=='.gz' else read(path)
            if actual!=value:raise ValueError('complete prefix replay differs: '+path.name)
        elif path.suffix=='.gz':gzip_equal(path,value)
        else:freeze(path,value)
    index=[];identities={}
    for u in stream:
        sid=u['session']
        if sid in identities:raise ValueError('duplicate source session')
        identities[sid]={k:u[k] for k in ('writer','genre','half','timestamp','prompt','typed_words')}
        rel='sessions/'+digest(sid)+'.json.gz';path=output/rel;retain(path,u)
        index.append(dict(session=sid,file=rel,sha256=filehash(path)))
        atomic(output/'PROGRESS.json',dict(phase='verify-occurrences' if verification else 'occurrences',done=len(index),total=config['sessions']))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('yield at complete occurrence session')
        if config==TIMING and len(index)==config['timing_sessions']:break
    if config==TIMING:
        if len(index)!=config['timing_sessions']:raise ValueError('incomplete fixed timing quota')
        elapsed=time.process_time()-started
        summary=dict(card='FIC1-prefix-timing',timing_sessions=len(index),population_sessions=CONFIG['sessions'],
            complete_population=False,identification_computed=False,length_curve_scored=False,scientific_admission=False)
        for name,value in [('SESSION_INDEX.json',index),('BINDING.json',dict(config=config,inputs=bindings)),('SUMMARY.json',summary)]:retain(output/name,value)
        cost_path=output/('VERIFY_COST.json' if verification else 'EXECUTE_COST.json')
        if not cost_path.exists():freeze(cost_path,dict(load_cpu_seconds=loaded_cpu,total_cpu_seconds=elapsed,
            session_cpu_seconds=elapsed-loaded_cpu,sessions=len(index),population_sessions=CONFIG['sessions']))
        if verification:return dict(verified=True,complete_timing_replay=True,all_timed_occurrences_recomputed=True,complete_population=False)
        return dict(status='complete',complete_population=False,scientific_admission=False)
    if len(index)!=config['sessions'] or len({v['writer'] for v in identities.values()})!=config['writers']:raise ValueError('complete source population differs')
    groups={};seen=[];ix=source.unique(index);prefixes=[]
    for group in sorted(profiles,key=lambda g:(g['writer'],g['genre'],g['half'])):
        key=(group['writer'],group['genre'],group['half'])
        if key in groups or type(group['half']) is not int or group['half'] not in (0,1):raise ValueError('invalid profile partition')
        groups[key]=group
        expected=sorted([s for s,v in identities.items() if (v['writer'],v['genre'],v['half'])==key],key=lambda s:(identities[s]['timestamp'],s))
        if not expected or expected!=group['sessions']:raise ValueError('original chronological profile differs')
        units=[gzread(output/ix[s]['file']) for s in expected];seen.extend(expected)
        if group['full_typed_words']!=sum(u['typed_words'] for u in units):raise ValueError('original profile word count differs')
        prefixes.append(dict(writer=key[0],genre=key[1],half=key[2],
            levels={str(limit) if limit is not None else 'full':profile(units,limit,dictionary) for limit in [*config['word_limits'],None]}))
    expected_groups={(w,g,h) for w in {v['writer'] for v in identities.values()} for g in source.GENRES for h in (0,1)}
    if set(groups)!=expected_groups or Counter(seen)!=Counter(identities.keys()):raise ValueError('profile coverage differs')
    for w,g,h in expected_groups:
        if {identities[s]['prompt'] for s in groups[w,g,0]['sessions']} & {identities[s]['prompt'] for s in groups[w,g,1]['sessions']}:
            raise ValueError('prompt halves overlap')
    summary=dict(card=CONFIG['card'],constructed=config['mode']=='constructed',sessions=len(index),writers=config['writers'],profiles=len(prefixes),
        word_limits=config['word_limits'],support={level:dict(prepared=sum(x['levels'][level]['state']=='prepared' for x in prefixes),
        unsupported=sum(x['levels'][level]['state']=='unsupported' for x in prefixes)) for level in [*(str(n) for n in config['word_limits']),'full']},
        exact_occurrence_replay=True,reusable_full_occurrences_retained=True,identification_computed=False,length_curve_scored=False,
        scientific_admission=False,auth_requests_prepared=False)
    for name,value in [('SESSION_INDEX.json',index),('PROFILES.json',profiles),('PREFIX_FEATURES.json',prefixes),('DICTIONARY.json',dictionary),
                       ('BINDING.json',dict(config=config,inputs=bindings)),('SUMMARY.json',summary)]:retain(output/name,value)
    if verification:return dict(verified=True,complete_input_replay=True,all_occurrences_recomputed=True,all_prefixes_recomputed=True)
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
