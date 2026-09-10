"""Canonical B-roll people/scripts and genuine earlier-selection evidence.

DESIGN CHECK: H03/X01/X02/X03/X04/X05; LESSONS 2--5. NULL: a target script,
future trial, repeated person/script or wrong commission cannot enter history.
ALTERNATIVE: matched other people supply the same earlier script set and dose.
Selection targets remain in evaluator records. Scripts and people are independently
withheld; trial position is genuine presentation order, not a cross-person clock.
"""
from collections import Counter,defaultdict
from runners.stage9.common import ROOT,digest,file_hash,read
from runners.stage9.split_guard import Separation,disjoint_factors


def public_script(source):
    return {'support':list(source['support']),'pos':dict(source['pos']),'counts':dict(source['word_counts'])}


def public_history(rows,scripts):
    return [{'stimulus':public_script(scripts[r['script_key']]),'selected':list(r['labels'])} for r in rows]


def validate_rows(rows,scripts,person_split,lane):
    people=defaultdict(list)
    for row in rows:
        if person_split[row['person']]!=lane or row['script_key'] not in scripts:raise ValueError('source record crosses its original partition')
        if type(row['trial']) is not int or row['goal'] not in ('informative','entertaining'):raise ValueError('unknown commission or chronology')
        if len(row['labels'])!=len(scripts[row['script_key']]['support']) or any(type(y) is not int or y not in (0,1) for y in row['labels']):
            raise ValueError('canonical word opportunity support differs')
        people[row['person']].append(row)
    if len({r['key'] for r in rows})!=len(rows):raise ValueError('duplicate canonical selection identity')
    for own in people.values():
        if (len(own)!=len(scripts) or {r['trial'] for r in own}!=set(range(len(scripts)))
            or {r['script_key'] for r in own}!=set(scripts) or len({r['goal'] for r in own})!=1):
            raise ValueError('complete once-per-script person chronology required')
    return people


def earlier(row,person_rows,scripts,fit_scripts,limit=3):
    eligible=sorted([r for r in person_rows if r['trial']<row['trial'] and r['script_key'] in fit_scripts and r['usable']],key=lambda r:r['trial'],reverse=True)
    seen={digest(public_script(scripts[row['script_key']]))};selected=[];excluded=[]
    for own in eligible:
        key=digest(public_script(scripts[own['script_key']]))
        if key in seen:excluded.append({'key':own['key'],'reason':'target or duplicate public script view'});continue
        seen.add(key)
        if len(selected)<limit:selected.append(own)
    return sorted(selected,key=lambda r:r['trial']),excluded


def matched_other(row,history,pool,fit_people,scripts):
    if not history:return [],None
    wanted=[r['script_key'] for r in history]
    for person in sorted(fit_people,key=lambda p:digest(['s9-broll-matched-other',row['key'],p])):
        if person==row['person']:raise ValueError('target participant is in the fitted pool')
        choices={r['script_key']:r for r in pool[person] if r['usable'] and r['goal']==row['goal']}
        if set(wanted)<=set(choices):
            # A different participant's own recorded selections, presented in the
            # same script order as the target's earlier evidence. This is a matched
            # record intervention, not a claim of shared calendar time.
            return [choices[k] for k in wanted],person
    return None,None


def assemble(rows,scripts,allocation,fit_scripts,test_scripts,separation,pilot=False):
    if set(fit_scripts)&set(test_scripts) or not fit_scripts or not test_scripts:raise ValueError('disjoint fitting/test scripts required')
    pool=defaultdict(list)
    for row in rows:pool[row['person']].append(row)
    if set(pool)!=set(allocation) or set(allocation.values())!={'train','development','evaluation'}:raise ValueError('complete person allocation required')
    assigned={lane:{p for p,v in allocation.items() if v==lane} for lane in ('train','development','evaluation')}
    ledgers={}
    for lane,against in [('development',assigned['evaluation']),('train',assigned['development']|assigned['evaluation'])]:
        kept,ledger=separation.filter_fit({'broll_people:'+p for p in assigned[lane]},{'broll_people:'+p for p in against})
        assigned[lane]={p.removeprefix('broll_people:') for p in kept};ledgers[lane]=ledger
        if not assigned[lane]:raise ValueError('source separation exhausted a required participant partition')
    training=[r for p in sorted(assigned['train']) for r in pool[p] if r['usable'] and r['script_key'] in fit_scripts]
    if not training or {r['goal'] for r in training}!={'informative','entertaining'}:raise ValueError('training lacks a declared commission')
    fitting=[{'key':r['key'],'person':r['person'],'script':r['script_key'],'goal':r['goal'],
        'stimulus':public_script(scripts[r['script_key']]),'labels':list(r['labels'])} for r in training]
    lanes={};exclusions=[];attempted={}
    for lane in ('development','evaluation'):
        targets=sorted([r for p in assigned[lane] for r in pool[p] if r['script_key'] in test_scripts],key=lambda r:digest(['s9-broll-target-order',r['key']]))
        attempted[lane]=len(targets);cases=[]
        for row in targets:
            if not row['usable']:
                exclusions.append({'key':row['key'],'person':row['person'],'lane':lane,'reason':row['exclusion']});continue
            history,dropped=earlier(row,pool[row['person']],scripts,fit_scripts)
            other,other_person=matched_other(row,history,pool,assigned['train'],scripts)
            if other is None:
                exclusions.append({'key':row['key'],'person':row['person'],'lane':lane,'reason':'no wrong-person history with identical scripts, commission and dose'});continue
            public={'stimulus':public_script(scripts[row['script_key']]),'commission':row['goal']}
            cases.append({'key':row['key'],'unit':row['person'],'source_group':'broll_people:'+row['person'],
                'script':row['script_key'],'goal':row['goal'],'trial':row['trial'],'labels':list(row['labels']),
                'views':{'same_person':{**public,'history':public_history(history,scripts)},
                    'other_person':{**public,'history':public_history(other,scripts)}},
                'history_keys':[r['key'] for r in history],'history_trials':[r['trial'] for r in history],
                'history_scripts':[r['script_key'] for r in history],'other_history_keys':[r['key'] for r in other],
                'other_history_trials':[r['trial'] for r in other],'other_person':other_person,
                'history_exclusions':dropped,'earlier_trial_count':len(history),
                'other_history_scope':'same script order, dose and commission; other participant has its own presentation order'})
        if not cases:raise ValueError('no eligible assigned selection targets')
        checks=disjoint_factors(fitting,[{'person':r['unit'],'script':r['script']} for r in cases],('person','script'))
        if pilot:
            selected=[];used=set()
            for goal in ('informative','entertaining'):
                for row in cases:
                    if row['goal']==goal and row['unit'] not in used:
                        selected.append(row);used.add(row['unit']);break
            if len(selected)!=2:raise ValueError('pilot must exercise both commissions and independent people')
            cases=selected
        lanes[lane]=cases;ledgers[lane+'-fitting_factors']=checks
    return {'train':fitting,**lanes},{'allocation':allocation,'source_separation':ledgers,'exclusions':exclusions,
        'attempted_target_records':attempted,'counts':{k:len(v) for k,v in {'train':fitting,**lanes}.items()},
        'fitting_people':len({r['person'] for r in fitting}),'fit_scripts':sorted(fit_scripts),'test_scripts':sorted(test_scripts),
        'maximum_earlier_trials':3,'known_group_limit':'participant and script crossed; limited scripts do not license broad stimulus claims'}


def inputs(scope):
    if scope not in ('pilot','scientific'):raise ValueError('explicit selection scope required')
    source=ROOT/'private/prepared/broll-v1';identity=read(source/'IDENTITY.json');done=read(source/'COMPLETE.json')
    if done['identity_sha256']!=digest(identity):raise ValueError('canonical B-roll identity differs')
    baseline=read(ROOT/'private/pilot-baseline/broll-v1/IDENTITY.json')
    if baseline['source_identity']!=digest(identity):raise ValueError('prior source exposure differs')
    scripts=read(source/'SCRIPTS.json');development=read(source/'development.json')
    people=validate_rows(development,scripts,identity['person_split'],'development')
    ordered=sorted(people,key=lambda p:digest({'broll-development-fit':p}));cut=2*len(ordered)//3
    old_fit,old_test=ordered[:cut],ordered[cut:];paths=[source/'SCRIPTS.json',source/'development.json']
    if digest(sorted(old_fit))!=baseline['fit_people_sha256'] or digest(sorted(old_test))!=baseline['test_people_sha256']:
        raise ValueError('prior development participant allocation differs')
    if scope=='pilot':
        n=3*len(old_fit)//4;allocation={p:'train' for p in old_fit[:n]}|{p:'development' for p in old_fit[n:]}|{p:'evaluation' for p in old_test}
        rows=development
    else:
        discovery=read(source/'discovery.json');paths.append(source/'discovery.json')
        extra=validate_rows(discovery,scripts,identity['person_split'],'discovery')
        allocation={p:'train' for p in old_fit}|{p:'development' for p in old_test}|{p:'evaluation' for p in extra};rows=development+discovery
    fit_scripts={s for s,v in identity['script_split'].items() if v=='discovery'}
    test_scripts={s for s,v in identity['script_split'].items() if v=='development'}
    cross=Separation.verified(ROOT/'private/prepared/cross-source-v2')
    result,metadata=assemble(rows,scripts,allocation,fit_scripts,test_scripts,cross,pilot=scope=='pilot')
    return result,{**metadata,'canonical_identity_sha256':digest(identity),'source_files':{str(p):file_hash(p) for p in paths},
        'scope':'discarded exposed development-source execution pilot' if scope=='pilot' else 'fixed new-participant discovery on held-out development scripts; reserve excluded',
        'reserve_records_parsed':False,'cross_source_integrity_rehashes_all_original_inputs':True,
        'proper_score':'mean Bernoulli Brier over offered word types; selection overlap separate',
        'source_task':'recorded concept-word selection under stated commission; no inferred imagery or values'}
