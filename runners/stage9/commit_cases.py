"""Canonical repository-separated, disjoint description-menu source preparation.

DESIGN CHECK: H06/X01/X03/X05; LESSONS 2--5. NULL: repeated wording, linked
repositories or reused distractor repositories cannot manufacture independent
questions. ALTERNATIVE: complete source changes support a common four-description
menu, with every source allocation and exclusion preserved. Menus consume disjoint
repository components, including distractors. Reserve fingerprints are checked
without loading reserved source records. Scientific construction is separate from
the discarded pilot and never promotes source labels into historical intent.
"""
from collections import Counter
from runners.stage9.common import ROOT,digest,file_hash,read
from runners.stage9.commitbench import parse_diff,visible
from runners.stage9.commitbench_baseline import language,words
from runners.stage9.split_guard import Separation
from runners.stage9.text_overlap import words as normalized_words


def wording(text):
    return digest(' '.join(normalized_words(text)))


def partition(rows,allocation,cross,fingerprints):
    """Higher-priority evaluation and reserve descriptions never enter fitting."""
    if len({r['key'] for r in rows})!=len(rows):raise ValueError('duplicate canonical code change')
    if set(allocation.values())!={'train','development','evaluation'}:raise ValueError('all three source partitions required')
    raw={lane:[r for r in rows if allocation[r['unit']]==lane] for lane in ('train','development','evaluation')}
    reserve={g for g,v in cross.groups.items() if v['split']=='reserve'}
    reserve_dependencies=cross.connected(reserve)
    reserved_words={r['text_sha256'] for r in fingerprints if r['group'] in reserve_dependencies and 'candidate' in r['roles']}
    partitions={};ledger=[];groups={}
    for lane in ('evaluation','development','train'):
        forbidden=reserve_dependencies|set().union(*groups.values()) if groups else reserve_dependencies
        candidates={'commitbench:'+r['unit'] for r in raw[lane]}
        # Include long-overlap/identity dependencies of all stronger partitions.
        blocked=cross.connected(forbidden) if forbidden else set()
        held_words=reserved_words|{wording(r['message']) for other in partitions.values() for r in other}
        kept=[]
        for row in sorted(raw[lane],key=lambda r:r['key']):
            group='commitbench:'+row['unit'];reason=None
            if group in blocked:reason='repository identity or long evidence overlap with higher-priority partition/reserve'
            elif wording(row['message']) in held_words:reason='normalized complete candidate wording occurs in higher-priority partition/reserve'
            if reason:ledger.append({'key':row['key'],'unit':row['unit'],'lane':lane,'reason':reason})
            else:kept.append(row)
        if not kept:raise ValueError('separation exhausted a required code-change partition')
        partitions[lane]=kept;groups[lane]={'commitbench:'+r['unit'] for r in kept}
    for a,b in [('train','development'),('train','evaluation'),('development','evaluation')]:
        if groups[a]&groups[b] or {wording(r['message']) for r in partitions[a]}&{wording(r['message']) for r in partitions[b]}:
            raise ValueError('repository or candidate wording leakage remains')
    return partitions,ledger


def menus(rows,limit=0):
    """One target per disjoint four-repository menu; no distractor reuse."""
    if not rows or len({r['key'] for r in rows})!=len(rows):raise ValueError('nonempty unique source rows required')
    ordered=sorted(rows,key=lambda r:digest(['s9-commit-disjoint-menu-v1',r['key']]))
    used=set();assigned={};result=[]
    for row in ordered:
        if row['unit'] in used:continue
        if limit and len(result)>=limit:break
        eligible=[r for r in ordered if r['unit'] not in used|{row['unit']} and language(r)==language(row)
            and wording(r['message'])!=wording(row['message'])]
        eligible.sort(key=lambda r:(abs(len(words(r['message']))-len(words(row['message']))),digest(['s9-commit-distractor',row['key'],r['key']])))
        members=[row];own_groups={row['unit']};messages={wording(row['message'])}
        for candidate in eligible:
            if candidate['unit'] in own_groups or wording(candidate['message']) in messages:continue
            members.append(candidate);own_groups.add(candidate['unit']);messages.add(wording(candidate['message']))
            if len(members)==4:break
        if len(members)!=4:continue
        members.sort(key=lambda r:digest({'diff':row['diff'],'description':r['message'],'order':'v1'}))
        descriptions=[r['message'] for r in members];truth=str(descriptions.index(row['message']))
        key=digest(['s9-commit-menu-v1',row['key'],[r['key'] for r in members]])
        result.append({'key':key,'unit':row['unit'],'source_group':'commitbench:'+row['unit'],'language':language(row),
            'source_key':row['key'],'candidate_keys':[r['key'] for r in members],
            'candidate_units':[r['unit'] for r in members],'evidence':visible(row,descriptions),'truth':truth,
            'interpretation':'complete diff to released stated description; menu classification, not free generation or private maker intention'})
        used.update(own_groups)
        for member in members:assigned[member['key']]={'menu':key,'role':'target' if member['key']==row['key'] else 'distractor'}
    if not result:raise ValueError('no complete disjoint four-repository menu')
    ledger=[{'key':r['key'],'unit':r['unit'],**(assigned[r['key']] if r['key'] in assigned else {
        'role':'not_selected','reason':'repository already used in a disjoint menu' if r['unit'] in used else
        'bounded discarded pilot sample' if limit and len(result)>=limit else 'no remaining same-language three-repository distinct-description support'})} for r in ordered]
    all_groups=[g for r in result for g in r['candidate_units']]
    if len(all_groups)!=len(set(all_groups)) or len(all_groups)!=4*len(result):raise ValueError('shared target/distractor source dependency')
    return result,ledger


def inputs(scope):
    if scope not in ('pilot','scientific'):raise ValueError('explicit code-change source scope required')
    prepared=ROOT/'private/prepared/commitbench-v2';source=read(prepared/'IDENTITY.json');done=read(prepared/'COMPLETE.json')
    if digest(source)!=done['identity_sha256'] or not done['reserve_allocation_meets_fraction']:raise ValueError('canonical source completion differs')
    cross_root=ROOT/'private/prepared/cross-source-v2';cross=Separation.verified(cross_root)
    allocation_source=read(prepared/'SPLITS.json');rows=[];paths={}
    for lane in (('train','development') if scope=='pilot' else ('train','development','discovery')):
        path=prepared/lane/'RECORDS.json'
        if file_hash(path)!=done['files'][lane+'/RECORDS.json']:raise ValueError('prepared code change split differs')
        paths[lane]=file_hash(path)
        own=read(path)
        for row in own:
            if row['split']!=lane or allocation_source[row['unit']]!=lane or parse_diff(row['diff'])!=row['parsed']:
                raise ValueError('canonical code change or repository allocation differs')
        rows.extend(own)
    allocation={}
    if scope=='pilot':
        train_groups=sorted({r['unit'] for r in rows if r['split']=='train'},key=lambda g:digest(['s9-commit-pilot-fit',g]))
        fitting=set(train_groups[:3*len(train_groups)//4])
        for row in rows:allocation[row['unit']]='evaluation' if row['split']=='development' else 'train' if row['unit'] in fitting else 'development'
    else:
        for row in rows:allocation[row['unit']]={'train':'train','development':'development','discovery':'evaluation'}[row['split']]
        # Actual discarded pilot target/distractor groups cannot enter discovery.
        pilot=ROOT/'private/commit-case-pilots/v1/CASES.json'
        if not pilot.exists():raise ValueError('actual discarded source rehearsal required before science')
        excluded={g for lane in read(pilot).values() for r in lane for g in r['candidate_units']}
        if any(allocation.get(g)=='evaluation' for g in excluded):raise ValueError('discarded code-change source group entered discovery')
    split,excluded=partition(rows,allocation,cross,read(cross_root/'OVERLAPS.json')['fingerprint_inventory'])
    result={};sampling={}
    for lane in ('train','development','evaluation'):
        result[lane],sampling[lane]=menus(split[lane],0 if lane=='train' or scope=='scientific' else 2)
    metadata={'prepared_complete_sha256':file_hash(prepared/'COMPLETE.json'),'source_splits':paths,
        'cross_source_complete_sha256':file_hash(cross_root/'COMPLETE.json'),'allocation':allocation,
        'split_exclusions':excluded,'sampling':sampling,'source_attempt_counts':done['splits'],
        'counts':{lane:{'menus':len(own),'distinct_repositories':4*len(own),'languages':dict(Counter(r['language'] for r in own))} for lane,own in result.items()},
        'reserve_payload_parsed':False,'scope':scope,'independent_unit':'disjoint four-repository menu; one target and three nonreused distractor repositories',
        'candidate_matching':'same primary language, nearest complete-description word count, fixed content order; no target-dependent learned selection',
        'data_scope':'repository-held-out stated-description correspondence; no stable permitted individual maker IDs; no individual accumulation'}
    return result,metadata
