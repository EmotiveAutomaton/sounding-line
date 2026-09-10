"""Canonical HUMAN revision cases; labels and future drafts remain outside readers.

DESIGN CHECK: H02/X01/X02/X05; LESSONS 2--5, canonical units and future targets.
NULL: a wrong revision link, copied future text, missing annotation support or
split-crossing lineage must refuse. ALTERNATIVE: genuine successive versions
support a whole-current-draft forecast, with before/after access separate.
The primary target follows every released major-intent label, one per edit;
all raw annotator votes are retained separately, not flattened into new units.
Pilot allocation uses already exposed fitting/development groups only. No
reserve or discovery record is parsed for case construction; the existing cross-
source integrity check still rehashes all its original input files.
"""
from collections import Counter
from pathlib import Path
from runners.stage9.common import ROOT,digest,file_hash,read
from runners.stage9.data import INTENTS
from runners.stage9.revision_cases import separate
from runners.stage9.split_guard import Separation

STUDIES=('within','leave-arxiv','leave-news','leave-wiki')


def iterater_rows(records,links):
    by_key={r['key']:r for r in records}
    if not records or len(by_key)!=len(records):raise ValueError('missing or duplicate canonical revision')
    output=[]
    for row in records:
        if row['source']!='IteraTeR-HUMAN-doc' or type(row['revision_depth']) is not int:
            raise ValueError('only canonical human-labelled document revisions are supported')
        if not row['labels'] or len(row['labels'])!=len(row['raw_votes']) or len(row['labels'])!=len(row['edits']):
            raise ValueError('complete canonical edits and disagreement records required')
        for label,votes,edit in zip(row['labels'],row['raw_votes'],row['edits']):
            if label not in INTENTS or not votes or any(v not in INTENTS for v in votes):
                raise ValueError('missing or unknown released annotation')
            if label!=edit['major_intent'] or votes!=edit['raw_intents']:
                raise ValueError('prepared annotation differs from its canonical edit')
        if any(not isinstance(row[k],str) for k in ('before','artifact','domain','group','independent_unit')):
            raise ValueError('invalid public text or source grouping')
        output.append({'key':digest(['iterater-retrospective',row['key']]),'unit':row['independent_unit'],
            'source_group':'iterater:'+row['independent_unit'],'domain':row['domain'],
            'task':'retrospective','cycle':str(row['revision_depth']),
            'labels':list(row['labels']),'raw_votes':[list(v) for v in row['raw_votes']],
            'record_source_keys':[row['key']],
            'views':{'artifact':{'text':row['artifact']},'pair':{'before':row['before'],'after':row['artifact']}},
            'annotation_scope':'one released major-intent target per canonical edit; raw votes retained; document lineage is independent unit'})
    seen=set()
    for link in links:
        pair=(link['current'],link['future'])
        if pair in seen or any(k not in by_key for k in pair):raise ValueError('duplicate or missing linked revision')
        seen.add(pair);current,future=(by_key[k] for k in pair)
        if (current['independent_unit']!=future['independent_unit'] or current['split']!=future['split']
            or current['split']!=link['split'] or current['artifact']!=future['before']
            or future['revision_depth']!=current['revision_depth']+1):
            raise ValueError('genuine same-lineage consecutive revision link required')
        output.append({'key':digest(['iterater-future',*pair]),'unit':current['independent_unit'],
            'source_group':'iterater:'+current['independent_unit'],'domain':current['domain'],
            'task':'future','cycle':str(current['revision_depth'])+'->'+str(future['revision_depth']),
            'labels':list(future['labels']),'raw_votes':[list(v) for v in future['raw_votes']],
            'record_source_keys':list(pair),
            'views':{'artifact':{'text':current['artifact']},'record':{'before':current['before'],
                'after':current['artifact'],'earlier_labels':list(current['labels'])}},
            'annotation_scope':'one whole-current-draft forecast; all canonical later-edit major intents; no future-selected excerpt'})
    if len({r['key'] for r in output})!=len(output):raise ValueError('repeated task identity')
    return output


def pilot_inputs(limit=True):
    prepared=ROOT/'private/prepared/iterater-v2';identity=read(prepared/'IDENTITY.json')
    receipt=read(ROOT/'intake/ITERATER_GROUP_REPAIR.json')
    if receipt['identity_sha256']!=digest(identity):raise ValueError('reconciled source identity differs')
    paths=[prepared/lane/name for lane in ('train','development') for name in ('records.json','future_links.json')]
    records=[];links=[]
    cross=Separation.verified(ROOT/'private/prepared/cross-source-v2')
    for lane in ('train','development'):
        own=read(prepared/lane/'records.json');next_links=read(prepared/lane/'future_links.json')
        if any(r['split']!=lane or identity['allocation'][r['independent_unit']]!=lane for r in own):
            raise ValueError('pilot source crosses its exposed source allocation')
        records.extend(own);links.extend(next_links)
    rows=iterater_rows(records,links);groups={r['unit'] for r in rows}
    future_groups=sorted({r['unit'] for r in rows if r['task']=='future'},key=lambda k:digest(['s9-itera-discarded-future-pilot',k]))
    if len(future_groups)<3:raise ValueError('pilot lacks independently grouped fitting, selection and future evaluation sources')
    # Allocation depends on source identity and availability, never label values.
    allocation={future_groups[0]:'development',future_groups[1]:'evaluation'}
    allocation.update({k:'train' for k in future_groups[2:]})
    for key in sorted(groups-set(future_groups)):
        bucket=int(digest(['s9-itera-discarded-pilot',key])[:8],16)%10
        allocation[key]='train' if bucket<7 else 'development' if bucket<9 else 'evaluation'
    lanes,separation=separate(rows,allocation,cross)
    for lane in ('development','evaluation') if limit else ():
        chosen=[]
        for task in ('retrospective','future'):
            own=sorted([r for r in lanes[lane] if r['task']==task],key=lambda r:digest(['s9-itera-pilot-task',r['key']]))
            used=set()
            for row in own:
                if row['unit'] in used:continue
                chosen.append(row);used.add(row['unit'])
                if len(used)==(2 if task=='retrospective' else 1):break
            if not used:raise ValueError('source separation exhausted a required pilot task')
        lanes[lane]=chosen
    return lanes,{'prepared_identity_sha256':digest(identity),'prepared_files':{str(p):file_hash(p) for p in paths},
        'allocation':allocation,'separation':separation,'raw_annotation_disagreement_retained':True,
        'scope':'discarded execution pilot from previously exposed train/development only',
        'discovery_or_reserve_records_parsed_for_cases':False,
        'cross_source_integrity_rehashes_all_original_inputs':True,'fresh_confirmation_eligible':False,
        'counts':{lane:dict(Counter(r['task'] for r in own)) for lane,own in lanes.items()}}


def study_partitions(rows,allocation,separation,study):
    """Keep fixed source partitions; no fitting or selection target-domain labels.

    Transfer excludes whole ambiguous/mixed-domain lineages and the held-out
    domain from both training and rival selection. Missing genuine future links
    produce a separate not-run disposition, never a fabricated successor.
    """
    if study not in STUDIES:raise ValueError('unknown HUMAN study')
    if set(allocation)!={r['unit'] for r in rows}:raise ValueError('source allocation differs')
    by_group={}
    for row in rows:by_group.setdefault(row['unit'],set()).add(row['domain'])
    excluded=[];selected=[];held=study.removeprefix('leave-') if study!='within' else None
    for row in rows:
        reason=None;domains=by_group[row['unit']];lane=allocation[row['unit']]
        if held:
            if len(domains)!=1 or not domains<={'arxiv','news','wiki'}:reason='unknown or mixed-domain source lineage'
            elif lane=='evaluation' and domains!={held}:reason='evaluation is confined to the declared held-out domain'
            elif lane!='evaluation' and held in domains:reason='target domain withheld from training and rival selection'
        if reason:excluded.append({'key':row['key'],'unit':row['unit'],'task':row['task'],'reason':reason})
        else:selected.append(row)
    assigned={r['unit']:allocation[r['unit']] for r in selected}
    if set(assigned.values())!={'train','development','evaluation'}:
        raise ValueError('declared domain study lacks a source partition')
    lanes,ledger=separate(selected,assigned,separation,required_tasks=('retrospective',))
    dispositions={};inactive=[]
    for task in ('retrospective','future'):
        counts={lane:sum(r['task']==task for r in own) for lane,own in lanes.items()}
        ready=all(counts.values())
        dispositions[task]={'disposition':'READY' if ready else 'NOT RUN WITH REASON','eligible_records':counts,
            'reason':None if ready else 'no genuine eligible task in '+', '.join(k for k,v in counts.items() if not v)}
        if not ready:
            for lane,own in lanes.items():
                inactive.extend({'lane':lane,'case':r,'reason':dispositions[task]['reason']} for r in own if r['task']==task)
                lanes[lane]=[r for r in own if r['task']!=task]
    active=[task for task,d in dispositions.items() if d['disposition']=='READY']
    assert 'retrospective' in active
    return lanes,{'study':study,'allocation':assigned,'active_tasks':active,'task_dispositions':dispositions,
        'domain_exclusions':excluded,'source_separation':ledger,'unavailable_task_cases':inactive,
        'counts':{lane:{task:sum(r['task']==task for r in own) for task in ('retrospective','future')} for lane,own in lanes.items()},
        'target_domain_excluded_from_fitting_and_selection':bool(held)}


def study_inputs(scope,study):
    if study not in STUDIES or scope not in ('pilot','scientific'):raise ValueError('unknown HUMAN study scope')
    cross=Separation.verified(ROOT/'private/prepared/cross-source-v2')
    if scope=='pilot':
        original,metadata=pilot_inputs(limit=False);rows=[r for own in original.values() for r in own]
        allocation={r['unit']:lane for lane,own in original.items() for r in own}
    else:
        prepared=ROOT/'private/prepared/iterater-v2';identity=read(prepared/'IDENTITY.json')
        receipt=read(ROOT/'intake/ITERATER_GROUP_REPAIR.json')
        if receipt['identity_sha256']!=digest(identity):raise ValueError('reconciled HUMAN source changed')
        records=[];links=[];paths=[]
        for lane in ('train','development','discovery'):
            path=prepared/lane/'records.json';own=read(path);paths.append(path)
            path=prepared/lane/'future_links.json';next_links=read(path);paths.append(path)
            if any(r['split']!=lane or identity['allocation'][r['independent_unit']]!=lane for r in own):
                raise ValueError('prepared source crosses its fixed allocation')
            records.extend(own);links.extend(next_links)
        rows=iterater_rows(records,links)
        allocation={r['independent_unit']:('evaluation' if r['split']=='discovery' else r['split']) for r in records}
        # Original reserved aliases must not enter a discovery target or a fitted model.
        reserve={g for g,data in cross.groups.items() if data['split']=='reserve'}
        forbidden=cross.connected(reserve);retained=[];reserve_exclusions=[]
        for row in rows:
            if row['source_group'] in forbidden:reserve_exclusions.append({'key':row['key'],'unit':row['unit'],'reason':'connected to a reserved source group'})
            else:retained.append(row)
        rows=retained;allocation={r['unit']:allocation[r['unit']] for r in rows}
        metadata={'prepared_identity_sha256':digest(identity),'prepared_files':{str(p):file_hash(p) for p in paths},
            'original_allocation_sha256':digest(identity['allocation']),'reserve_dependency_exclusions':reserve_exclusions,
            'reserve_records_parsed_for_cases':False,'cross_source_integrity_rehashes_all_original_inputs':True,
            'scope':'IteraTeR HUMAN fixed training/development/discovery lineages; reserve excluded; source-specific annotation agreement',
            'raw_annotation_disagreement_retained':True,'fresh_confirmation_eligible':False}
    lanes,study_metadata=study_partitions(rows,allocation,cross,study)
    if scope=='pilot':
        for lane in ('development','evaluation'):
            selected=[]
            for task in study_metadata['active_tasks']:
                candidates=sorted([r for r in lanes[lane] if r['task']==task],key=lambda r:digest(['s9-human-study-pilot',r['key']]))
                used=set()
                for row in candidates:
                    if row['unit'] in used:continue
                    selected.append(row);used.add(row['unit'])
                    if len(used)==2:break
            lanes[lane]=selected
        study_metadata['counts']={lane:{task:sum(r['task']==task for r in own) for task in ('retrospective','future')} for lane,own in lanes.items()}
    return lanes,{**metadata,**study_metadata,'scope':metadata['scope']+'; study '+study}


def run(directory,scope,study=None):
    import time
    from runners.stage9.common import REPO,Units,closure,freeze
    from runners.stage9.queue import inside,verify_sources,writer
    from runners.stage9.revision_predictions import sources
    from runners.stage9.training_jobs import cell_identity
    start,cpu=time.monotonic(),time.process_time();directory=inside(directory);cell=cell_identity()
    prefix='revision-case-pilots' if scope=='pilot' else 'scientific-revision-case'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):
        raise ValueError('explicit HUMAN case scope required')
    if scope=='scientific' and study is None:raise ValueError('scientific HUMAN study must be declared')
    lanes,metadata=pilot_inputs() if study is None else study_inputs(scope,study);source=sources()
    identity={'cell_identity':cell,'operation':'iterater-actual-revision-cases-v1','scope':scope,'source':source,
        'classes':list(INTENTS),'allocation':metadata['allocation'],'metadata_sha256':digest(metadata),
        'cross_source_complete_sha256':file_hash(ROOT/'private/prepared/cross-source-v2/COMPLETE.json'),
        'data_scope':metadata['scope'],'target':'released major-intent annotation agreement; disagreement retained',
        **({k:metadata[k] for k in ('study','active_tasks','task_dispositions')} if study is not None else {})}
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('completed HUMAN cases changed')
            return done
        freeze(directory/'CASES.json',lanes);freeze(directory/'METADATA.json',metadata)
        verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,
            'counts':metadata['counts'],'scope':scope,'reserve_groups':0,'scientific_admission':False,
            'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/p for p in ('IDENTITY.json','CASES.json','METADATA.json')])}
        freeze(directory/'COMPLETE.json',done);return done


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    p.add_argument('--study',choices=STUDIES);a=p.parse_args();run(a.output,a.scope,a.study)
