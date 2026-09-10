"""Versioned CommitBench split repair using new groups before scientific lock.

DESIGN CHECK: LESSONS 3-5; I02/X01. NULL: new rows from old fitted repositories
must not become untouched, and failed diffs must not inflate eligible reserve size.
ALTERNATIVE: new complete records can fill exactly the missing reserve allocation
while old training/development/pilot/reserve roles are preserved. Duplicate joins
propagate the strongest old exposure before any new allocation. Insufficient fresh
groups fail explicitly. No predictive scores or class performance select groups.
"""
from collections import Counter,defaultdict
import math
import time
from runners.stage9.common import ROOT,REPO,closure,digest,file_hash,freeze,read
from runners.stage9.commitbench import PIN,components,parse_diff,validate_page

LANES=('pilot','train','development','discovery','reserve')
PRIORITY={'pilot':0,'train':1,'development':2,'reserve':3,'discovery':4}


def allocate(groups,eligible,prior):
    """prior maps each NEW component to all old allocations joining it."""
    groups=set(groups);eligible=set(eligible)
    if not eligible<=groups or not set(prior)<=groups:
        raise ValueError('unknown source group in allocation')
    if any(not values or not set(values)<=set(LANES) for values in prior.values()):
        raise ValueError('invalid old exposure')
    result={g:min(values,key=PRIORITY.get) for g,values in prior.items()}
    fixed_reserve={g for g,lane in result.items() if lane=='reserve' and g in eligible}
    denominator=len(eligible-{g for g,lane in result.items() if lane=='pilot'})
    target=math.ceil(.30*denominator)
    needed=max(0,target-len(fixed_reserve))
    fresh=sorted(eligible-set(prior),key=lambda g:digest(['commitbench-reserve-repair-v2',g]))
    if len(fresh)<needed:
        raise ValueError('insufficient genuinely new eligible components for reserve target')
    new_reserve=set(fresh[:needed])
    for g in groups-set(result):
        result[g]='reserve' if g in new_reserve else 'discovery'
    if any(result[g] in ('reserve','discovery') and set(values)&{'pilot','train','development'}
           for g,values in prior.items()):
        raise ValueError('exposed component entered untouched pool')
    return result,{'eligible_nonpilot_components':denominator,'reserve_target':target,
        'retained_eligible_reserve_components':len(fixed_reserve),'new_eligible_reserve_components':len(new_reserve),
        'eligible_reserve_components':sum(g in eligible and lane=='reserve' for g,lane in result.items()),
        'genuinely_new_eligible_components':len(fresh),
        'prior_reserve_components_lost_to_exposure':sum('reserve' in values and result[g]!='reserve' for g,values in prior.items()),
        'rule':'retain old roles after exposure-priority duplicate grouping; allocate the reserve shortfall from new eligible components by fixed hash order; remaining new groups discovery'}


def prepare():
    started=time.time();out=ROOT/'private/prepared/commitbench-v2'
    old=read(ROOT/'intake/COMMITBENCH_SOURCE_SLICE.json')
    extension=read(ROOT/'intake/COMMITBENCH_SOURCE_EXTENSION.json')
    if old['pin']!=PIN or extension['pin']!=PIN or old['rows']!=1200 or extension['rows']!=1200:
        raise ValueError('unregistered source slice')
    if file_hash(ROOT/'intake/COMMITBENCH_SOURCE_SLICE.json')!=extension['parent_slice_sha256']:
        raise ValueError('parent slice mismatch')
    identity={'sources':closure([REPO/'runners/stage9'/n for n in ('commitbench_allocation.py','commitbench.py','common.py')]),
        'parent_preparation':closure([ROOT/'private/prepared/commitbench-v1']),
        'source_slice_sha256':file_hash(ROOT/'intake/COMMITBENCH_SOURCE_SLICE.json'),
        'extension_sha256':file_hash(ROOT/'intake/COMMITBENCH_SOURCE_EXTENSION.json'),
        'prior_baseline_sha256':file_hash(ROOT/'intake/COMMITBENCH_BASELINE.json'),
        'reserve_target_fraction':.30,'evaluation':'none; all old source and scores preserved',
        'scope':'same complete-diff/stated-message task, no person identity reconstruction'}
    freeze(out/'IDENTITY.json',identity)
    if (out/'COMPLETE.json').exists():return read(out/'COMPLETE.json')
    try:
        rows=[];old_rows=[];ordinals=set()
        for is_old,pages in ((True,old['pages']),(False,extension['new_pages'])):
            for page in pages:
                receipt=page['receipt'];path=ROOT/'private/intake/objects'/receipt['sha256']
                if file_hash(path)!=receipt['sha256'] or not receipt['complete_eof']:
                    raise ValueError('changed or incomplete input')
                offsets=set(range(page['offset'],page['offset']+100))
                if offsets&ordinals:raise ValueError('overlapping source page')
                ordinals.update(offsets)
                fetched=validate_page(read(path),page['headers'],page['offset'],old['total_source_rows'])
                rows.extend(fetched)
                if is_old:old_rows.extend(fetched)
        if len(rows)!=2400:raise ValueError('source extension count mismatch')
        old_components=components(old_rows);new_components=components(rows)
        old_splits=read(ROOT/'private/prepared/commitbench-v1/SPLITS.json')
        prior=defaultdict(set);mapping={}
        for project,original in old_components.items():
            old_unit=digest({'repository-component':original})
            new_unit=digest({'repository-component':new_components[project]})
            if old_unit in mapping and mapping[old_unit]!=new_unit:raise ValueError('one old unit split')
            mapping[old_unit]=new_unit;prior[new_unit].add(old_splits[old_unit])
        attempts=[];records=[];seen={};duplicate_rows=[]
        for row in rows:
            group=new_components[row['project']];unit=digest({'repository-component':group})
            key=digest({'commit':row['hash'],'project':row['project']})
            if key in seen:
                if seen[key]!=row:raise ValueError('conflicting released commit identity')
                duplicate_rows.append(key)
                continue
            seen[key]=row;reason=None;parsed=None
            try:parsed=parse_diff(row['diff'])
            except ValueError as exc:reason=str(exc)
            attempts.append({'key':key,'unit':unit,'exclusion':reason})
            if reason:continue
            records.append(row|{'key':key,'unit':unit,'source_split':row['split'],'parsed':parsed,
                'languages':row['diff_languages'].split(','),'content_sha256':digest(row['diff'])})
        units={digest({'repository-component':g}) for g in new_components.values()}
        eligible={r['unit'] for r in records}
        splits,allocation=allocate(units,eligible,prior)
        for row in attempts+records:row['split']=splits[row['unit']]
        # Verify every old usable row survives with the same task content. Only
        # documented component identity/exposure propagation may differ.
        by_key={r['key']:r for r in records};preserved=0
        for lane in LANES:
            for row in read(ROOT/'private/prepared/commitbench-v1'/lane/'RECORDS.json'):
                replacement=by_key[row['key']]
                if {k:v for k,v in row.items() if k not in ('unit','split')}!={k:v for k,v in replacement.items() if k not in ('unit','split')}:
                    raise ValueError('old task text or metadata changed')
                if replacement['unit']!=mapping[row['unit']]:raise ValueError('old unit identity mismatch')
                preserved+=1
        freeze(out/'ATTEMPTS.json',attempts);freeze(out/'SPLITS.json',splits)
        freeze(out/'GROUP_REPAIR.json',{'old_to_new':mapping,'prior_allocations':{g:sorted(s) for g,s in prior.items()},
            'eligible_components':sorted(eligible),'allocation_receipt':allocation})
        for lane in LANES:freeze(out/lane/'RECORDS.json',[r for r in records if r['split']==lane])
        result={'identity_sha256':digest(identity),'completed_at':time.time(),'elapsed_seconds':time.time()-started,
            'source_rows':len(rows),'duplicate_source_rows':len(duplicate_rows),'attempts':len(attempts),
            'usable':len(records),'exclusions':dict(Counter(r['exclusion'] for r in attempts if r['exclusion'])),
            'repositories':len(new_components),'repository_components':len(units),'eligible_components':len(eligible),
            'allocation':allocation,'old_usable_records_preserved':preserved,
            'splits':{lane:{'attempts':sum(r['split']==lane for r in attempts),'usable':sum(r['split']==lane for r in records),
                'components':sum(s==lane for s in splits.values()),
                'eligible_components':sum(s==lane and g in eligible for g,s in splits.items())} for lane in LANES},
            'files':{p.relative_to(out).as_posix():file_hash(p) for p in
                [out/'ATTEMPTS.json',out/'SPLITS.json',out/'GROUP_REPAIR.json']+[out/lane/'RECORDS.json' for lane in LANES]},
            'reserve_allocation_meets_fraction':allocation['eligible_reserve_components']>=allocation['reserve_target'],
            'scientific_split_accepted':False,'remaining':['expanded cross-source/near-duplicate closure','scientific consumer enforcement']}
        freeze(out/'COMPLETE.json',result);freeze(ROOT/'intake/COMMITBENCH_PREPARATION_V2.json',result)
        return result
    except Exception as exc:
        freeze(out/'FAILED.json',{'identity_sha256':digest(identity),'at':time.time(),
                                 'elapsed_seconds':time.time()-started,'error':str(exc)})
        raise


if __name__=='__main__':print(prepare())

