"""Source admission and retrospective episode projection, independent of outcomes.

DESIGN CHECK: LESSONS 2-5. NULL: changed offsets, crossed lineage or a prospective
endpoint refuses. ALTERNATIVE: source-bound retrospective episodes reproduce.
Previously used human sources remain descriptive; missing context is not invented.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from pathlib import Path
import json
import re
from .common import REPO,RAW,freeze,read,filehash,digest,atomic,now,limit_process
from .splits import components,partition,Union
from .scoring import validate_spans


def opai(raw=RAW):
    import pyarrow.parquet as pq
    ready=raw/'sources/OPAI_COMPLETE.json'
    if ready.exists():
        result=read(ready)
        for name,h in result['outputs'].items():
            if filehash(raw/name)!=h:raise ValueError('source output changed')
        return result
    sources={};paths=sorted((raw/'assets/opai').rglob('*.parquet'));pins={}
    for p in paths:
        receipt=read(p.with_name(p.name+'.download.json'))
        if filehash(p)!=receipt['sha256']:raise ValueError('input changed')
        pins[str(p.relative_to(REPO))]=receipt['sha256']
        for r in pq.read_table(p,columns=['document_hash_id','split','domain','version_index','text']).to_pylist():
            if r['version_index']!=0:continue
            key=r['document_hash_id'];meta={k:r[k] for k in ('text','split','domain')}
            if key in sources and sources[key]!=meta:raise ValueError('source identity has conflicting human seed')
            sources[key]=meta
    atomic(raw/'sources/PROGRESS.json',dict(at=now(),phase='lineage-near-duplicate-audit',human_sources=len(sources)))
    roots,conflicts,links=components(sources)
    chosen=set();caps={'train':200,'dev':400,'test':250}
    for split in caps:
        for domain in ('abstracts','essays','news','reports'):
            eligible=sorted({roots[k] for k,r in sources.items() if r['split']==split and r['domain']==domain and roots[k] not in conflicts},key=lambda k:digest(['S13-source',k]))
            chosen.update(eligible[:caps[split]])
    rows=[];seen=set();human=set();exclusions=Counter()
    for p in paths:
        for r in pq.read_table(p).to_pylist():
            unit=roots[r['document_hash_id']]
            if unit in conflicts:exclusions['cross-split-lineage']+=1;continue
            if unit not in chosen:exclusions['source-cap']+=1;continue
            if r['record_id'] in seen:continue
            if r['version_index']==0 and unit in human:continue
            if r['version_index']==0:human.add(unit)
            seen.add(r['record_id'])
            spans=json.loads(r['ai_spans_char'])
            try:
                validate_spans(spans,len(r['text']));location_valid=True
            except ValueError:
                location_valid=False;exclusions['invalid-location-truth-retained']+=1
            y=int(r['version_index']!=0)
            if not y and spans:raise ValueError('human seed has AI spans')
            rows.append(dict(key=r['record_id'],unit=unit,source_id=r['document_hash_id'],
                partition=partition(r['split'],unit),domain=r['domain'],generator=r['generator'] if y else 'human-seed',
                text=r['text'],label=y,spans=spans,location_truth_valid=location_valid,version=r['version_index'],operation=r['edit_operation'],
                coverage=r['ai_char_ratio'],evidence_track='A',exposure='new local benchmark; upstream model-training overlap unknown',
                writer_known=False,label_scope='any annotated AI participation; not sole authorship'))
    rows.sort(key=lambda r:(r['partition'],digest(r['key'])))
    out={}
    for part in ('train','development','calibration','reserve'):
        name='sources/opai-'+part+'.json';freeze(raw/name,[r for r in rows if r['partition']==part]);out[name]=filehash(raw/name)
    freeze(raw/'sources/OPAI_LINEAGE.json',dict(roots=roots,quarantined=sorted(conflicts),links=links,
        approximate_method='64 minhashes, 16 bands, exact candidate Jaccard >= .85; not exhaustive near-duplicate search',
        source_pins=pins,unknowns=['human writer identity absent','pretraining and detector training overlap not fully auditable'],exclusions=dict(exclusions)))
    out['sources/OPAI_LINEAGE.json']=filehash(raw/'sources/OPAI_LINEAGE.json')
    result=dict(status='complete',kind='source-admission',outputs=out,
        counts={part:dict(rows=len([r for r in rows if r['partition']==part]),units=len({r['unit'] for r in rows if r['partition']==part}),human=sum(r['label']==0 and r['partition']==part for r in rows)) for part in ('train','development','calibration','reserve')},
        spans='Unicode code point half-open offsets on exact released text',split_conflicts=len(conflicts),source_caps=caps)
    freeze(ready,result);return result


def coauthor(raw=RAW):
    from runners.stage9.coauthor import raw_inputs
    from runners.stage11.replay import replay
    from runners.stage11_1.targets import project,public
    ready=raw/'sources/COAUTHOR_COMPLETE.json'
    if ready.exists():
        result=read(ready)
        for name,h in result['outputs'].items():
            if filehash(raw/name)!=h:raise ValueError('source output changed')
        return result
    native_path=REPO/'results/phase_2_4_stage_11_1/raw/NATIVE_OPPORTUNITIES.json'
    native=read(native_path);paths,metadata,_=raw_inputs()
    lookup={digest({'coauthor-session':p.stem}):p for p in paths}
    union=Union()
    for lane,rs in native.items():
        for r in rs:union.join('writer:'+r['unit'],'prompt:'+r['stimulus'])
    byunit=defaultdict(set)
    for lane,rs in native.items():
        for r in rs:byunit[union.find('writer:'+r['unit'])].add(lane)
    if any(len(v)!=1 for v in byunit.values()):raise ValueError('inherited source split crosses writer/prompt component')
    eval_units=sorted([u for u,v in byunit.items() if 'evaluation' in v],key=lambda u:digest(['S13-calibration',u]))
    cal=set(eval_units[:max(1,len(eval_units)//3)])
    rows=[];pins={str(native_path.relative_to(REPO)):filehash(native_path)};exclusions=[]
    for lane,rs in native.items():
        grouped=defaultdict(list)
        for r in rs:grouped[r['session']].append(r)
        for session,items in sorted(grouped.items()):
            p=lookup[session];lines=p.read_text(encoding='utf-8').splitlines();reconstructed=replay(lines)
            pins[str(p.relative_to(REPO))]=filehash(p)
            if not reconstructed['reconstructed']:raise ValueError('native source no longer reconstructs')
            events={e['ordinal']:e for e in reconstructed['events']}
            for r in items:
                e=events[r['ordinal']]
                if not e['usable'] or e['decision']!=r['truth']:raise ValueError('native retrospective handling differs')
                if e['cutoff_ordinal']<=e['ordinal']:raise ValueError('non-retrospective episode boundary')
                try:
                    target=project(e,lines);pair=public(e,'alternatives');endpoint=public(e,'artifact')
                    for fact in target['facts']:validate_spans(fact['exact_spans'],len(pair['endpoint']))
                except (ValueError,UnicodeError) as exc:
                    exclusions.append(dict(key=r['key'],reason=str(exc)));continue
                unit=union.find('writer:'+r['unit'])
                part=('calibration' if unit in cal else 'reserve') if lane=='evaluation' else lane
                rows.append(dict(key=r['key'],unit=unit,writer=r['unit'],prompt=r['stimulus'],session=session,
                    partition=part,domain=r['domain'],ordinal=e['ordinal'],cutoff_ordinal=e['cutoff_ordinal'],
                    target=target,views={'A':endpoint,'B':dict(endpoint,public_context=None,context_available=False),
                        'C':pair,'D':dict(pair,observed_operations=target['facts'])},
                    exposure='historically exposed; descriptive reanalysis only',goal_ground_truth='unavailable',
                    goal_claim='local handling is not mental-goal ground truth'))
    outputs={}
    for part in ('train','development','calibration','reserve'):
        name='sources/coauthor-'+part+'.json';freeze(raw/name,sorted([r for r in rows if r['partition']==part],key=lambda r:r['key']));outputs[name]=filehash(raw/name)
    freeze(raw/'sources/COAUTHOR_LINEAGE.json',dict(source_pins=pins,components={u:sorted(v) for u,v in byunit.items()},exclusions=exclusions,rights='author-released research corpus; private analytical use, no text redistribution',boundary='after suggestion handling, before next suggestion menu/session end'))
    outputs['sources/COAUTHOR_LINEAGE.json']=filehash(raw/'sources/COAUTHOR_LINEAGE.json')
    result=dict(status='complete',kind='source-admission',outputs=outputs,counts={part:dict(rows=sum(r['partition']==part for r in rows),units=len({r['unit'] for r in rows if r['partition']==part})) for part in ('train','development','calibration','reserve')},
        scope='exposed human retrospective records; few connected components restrict calibration and generalization')
    freeze(ready,result);return result



def opai_extension(raw=RAW):
    """Unused original test components, fixed before new outcomes; conditional runway."""
    import pyarrow.parquet as pq
    lineage=read(raw/'sources/OPAI_LINEAGE.json');roots=lineage['roots'];quarantine=set(lineage['quarantined'])
    used={r['unit'] for part in ('train','development','calibration','reserve') for r in read(raw/f'sources/opai-{part}.json')};rows=[];seen=set();human=set()
    for p in sorted((raw/'assets/opai').rglob('*.parquet')):
        if filehash(p)!=read(p.with_name(p.name+'.download.json'))['sha256']:raise ValueError('source changed')
        for r in pq.read_table(p).to_pylist():
            unit=roots[r['document_hash_id']]
            if r['split']!='test' or unit in used or unit in quarantine or r['record_id'] in seen:continue
            if r['version_index']==0 and unit in human:continue
            if r['version_index']==0:human.add(unit)
            seen.add(r['record_id']);spans=json.loads(r['ai_spans_char'])
            try:validate_spans(spans,len(r['text']));valid=True
            except ValueError:valid=False
            y=int(r['version_index']!=0)
            rows.append(dict(key=r['record_id'],unit=unit,source_id=r['document_hash_id'],partition='conditional-reserve',domain=r['domain'],generator=r['generator'] if y else 'human-seed',text=r['text'],label=y,spans=spans,location_truth_valid=valid,version=r['version_index'],operation=r['edit_operation'],coverage=r['ai_char_ratio'],evidence_track='A',exposure='unused local source components, upstream model exposure unresolved',writer_known=False,label_scope='any annotated AI participation'))
    rows.sort(key=lambda r:digest(['conditional-extension',r['key']]))
    freeze(raw/'sources/opai-conditional-reserve.json',rows)
    result=dict(status='complete',rows=len(rows),units=len({r['unit'] for r in rows}),source_lineage_sha256=filehash(raw/'sources/OPAI_LINEAGE.json'),output_sha256=filehash(raw/'sources/opai-conditional-reserve.json'),scope='predeclared complete replication, eligible only after core and whole-family time admission; no favorable-sign stopping')
    freeze(raw/'sources/OPAI_EXTENSION_COMPLETE.json',result);return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source',choices=['opai','coauthor']);a=p.parse_args();limit_process()
    try:print(json.dumps(globals()[a.source](),sort_keys=True))
    except Exception as exc:
        atomic(RAW/'sources'/(a.source.upper()+'_FAILED-v2.json'),dict(status='failed',at=now(),error=type(exc).__name__+': '+str(exc)));raise
