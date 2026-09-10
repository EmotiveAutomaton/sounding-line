"""Next released-edit tasks with complete project-held-out source partitions.

DESIGN CHECK: H08/X01/X02/X03/X05; LESSONS 2--5. NULL: reversed, missing or
discontinuous successors and copied current text cannot support prospective gain.
ALTERNATIVE: a verified next released category/location is forecast from the prior
editor state. Five fixed outer project folds, each with a different whole selection
project; remaining projects fit. Source events, invalid boundaries and pilot targets
are retained explicitly. Historically exposed corpus; no untouched confirmation.
"""
from collections import Counter
from runners.stage9.common import ROOT,digest,file_hash,read
from runners.stage9.scholawrite import CATEGORIES,LOCATIONS,visible
from runners.stage9.split_guard import Separation,normalized_evidence

KINDS={'schola_category':list(CATEGORIES),'schola_location':list(LOCATIONS)}


def projected(project):
    records=project['records'];by_ordinal={r['source_ordinal']:r for r in records};rows=[];excluded=[]
    if len(by_ordinal)!=len(records):raise ValueError('repeated source edit ordinal')
    for row in records:
        if not row['usable']:
            excluded.append({'key':row['key'],'reason':row['exclusion']});continue
        following=by_ordinal.get(row['next_source_ordinal'])
        if following is None or any(row[k]!=following[k] for k in ('unit','author','session')) or row['after']!=following['before']:
            raise ValueError('successor lacks same-author/project/session or exact text continuity')
        if not 0<row['gap_ms']<=30*60*1000:raise ValueError('successor time gap outside original source contract')
        if row['next_category']!=following['category'] or row['next_location']!=following['location']:
            raise ValueError('future target differs from canonical released event')
        views={v:visible(row,project['texts'],v) for v in ('artifact','record')}
        if any(digest(project['texts'][key])!=key for key in (row['before'],row['after'])):
            raise ValueError('canonical editor text digest differs')
        for kind,target in (('schola_category','next_category'),('schola_location','next_location')):
            if row[target] not in KINDS[kind]:raise ValueError('source-native successor support differs')
            rows.append({'key':digest(['s9-schola-next',row['key'],kind]),'source_key':row['key'],'source_ordinal':row['source_ordinal'],
                'target_source_ordinal':row['next_source_ordinal'],'unit':row['unit'],'source_group':'scholawrite:'+row['unit'],
                'stimulus':row['unit'],'author':row['author'],'session':row['session'],'kind':kind,'truth':row[target],
                'views':views,'current_text_sha256':digest(normalized_evidence(views['artifact']['document']))})
    return rows,excluded


def separate(rows,allocation,cross):
    selected={};exclusions=[]
    for lane in ('evaluation','development','train'):
        own=[r for r in rows if allocation[r['unit']]==lane]
        if not own:raise ValueError('missing required whole-project partition')
        if selected:
            others=[r for group in selected.values() for r in group]
            kept,_=cross.filter_fit({r['source_group'] for r in own},{r['source_group'] for r in others})
            texts={r['current_text_sha256'] for r in others};usable=[]
            for row in own:
                reason='source dependency crosses project fold' if row['source_group'] not in kept else 'copied normalized current text across fold' if row['current_text_sha256'] in texts else None
                if reason:exclusions.append({'key':row['key'],'source_key':row['source_key'],'lane':lane,'reason':reason})
                else:usable.append(row)
            own=usable
        if {r['kind'] for r in own}!=set(KINDS):raise ValueError('source separation exhausted a native successor task')
        selected[lane]=sorted(own,key=lambda r:(r['unit'],r['source_key'],r['kind']))
    return selected,exclusions


def inputs(scope,fold):
    if scope not in ('pilot','scientific') or type(fold) is not int or not 0<=fold<5:raise ValueError('explicit five-project source scope/fold required')
    prepared=ROOT/'private/prepared/scholawrite-v2';source=read(prepared/'IDENTITY.json');done=read(prepared/'COMPLETE.json');ledger=read(prepared/'LEDGER.json')
    if done['identity_sha256']!=digest(source) or done['source_counts_match'] is not True or done['projects']!=5 or len(ledger)!=5:
        raise ValueError('canonical ScholaWrite source completion differs')
    cross_root=ROOT/'private/prepared/cross-source-v2';cross=Separation.verified(cross_root)
    original=ROOT/'private/pilot-baseline/scholawrite-v1';baseline=read(original/'IDENTITY.json')
    old={r['project']:set(r['selected']) for r in baseline['selection']}
    projects=sorted((r['unit'] for r in ledger),key=lambda k:digest(['s9-schola-project-fold-order',k]))
    held,development=projects[fold],projects[(fold+1)%5]
    allocation={p:'evaluation' if p==held else 'development' if p==development else 'train' for p in projects}
    rows=[];excluded=[];source_paths={};selection=[]
    for item in sorted(ledger,key=lambda r:r['unit']):
        path=prepared/item['path']
        if file_hash(path)!=item['sha256']:raise ValueError('prepared project changed')
        source_paths[item['unit']]=file_hash(path);project=read(path);own,invalid=projected(project)
        if len(project['records'])!=item['attempted'] or len(own)!=2*item['usable']:raise ValueError('source attempts or native task counts differ')
        excluded.extend({'project':item['unit'],**r} for r in invalid)
        if scope=='pilot':
            selected={r['source_key'] for r in own if r['source_key'] in old[item['unit']]}
        else:
            # Stage9 timing/baseline targets and their successor events stay out of
            # scientific discovery, even though the entire source was historically exposed.
            raw={r['key']:r for r in project['records']}
            exposed={o for key in old[item['unit']] for o in (raw[key]['source_ordinal'],raw[key]['next_source_ordinal'])}
            eligible={r['source_key'] for r in own if r['source_ordinal'] not in exposed and r['target_source_ordinal'] not in exposed}
            selected=set(sorted(eligible,key=lambda k:digest(['s9-schola-scientific-target-order',k]))[:400])
        selection.append({'project':item['unit'],'selected_source_keys':sorted(selected),'scope':scope})
        for row in own:
            if row['source_key'] in selected:rows.append(row)
            else:excluded.append({'project':item['unit'],'key':row['key'],'source_key':row['source_key'],'reason':'outside fixed source sample or retained pilot exposure'})
    partitions,split_exclusions=separate(rows,allocation,cross);excluded.extend(split_exclusions)
    if scope=='pilot':
        for lane in ('development','evaluation'):
            keys=sorted({r['source_key'] for r in partitions[lane]},key=lambda k:digest(['s9-schola-pilot-boundary-order',k]))[:2]
            if not keys:raise ValueError('no separated source boundary for pilot')
            excluded.extend({'key':r['key'],'lane':lane,'reason':'bounded discarded execution sample'} for r in partitions[lane] if r['source_key'] not in keys)
            partitions[lane]=[r for r in partitions[lane] if r['source_key'] in keys]
    metadata={'prepared_complete_sha256':file_hash(prepared/'COMPLETE.json'),'ledger_sha256':file_hash(prepared/'LEDGER.json'),
        'cross_source_complete_sha256':file_hash(cross_root/'COMPLETE.json'),'original_baseline_identity_sha256':file_hash(original/'IDENTITY.json'),
        'source_projects':source_paths,'allocation':allocation,'fold':fold,'held_project':held,'selection_project':development,
        'selection':selection,'exclusions':excluded,'classes':KINDS,'crossed_stimulus':False,
        'counts':{lane:{'records':len(own),'projects':len({r['unit'] for r in own}),'boundaries':len({r['source_key'] for r in own}),
            'kind_counts':dict(Counter(r['kind'] for r in own)),'classes':{k:dict(Counter(r['truth'] for r in own if r['kind']==k)) for k in KINDS}} for lane,own in partitions.items()},
        'data_scope':'previously exposed corpus, five projects, project-scoped author IDs and annotator labels; next released edit, not next raw keystroke',
        'independent_unit':'whole project; two native targets and repeated source boundaries stay dependent',
        'reserve_payload_parsed':False,'scope':scope}
    return partitions,metadata
