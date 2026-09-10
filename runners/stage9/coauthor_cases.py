"""Prospective source-defined suggestion handling with crossed source separation.

DESIGN CHECK: H07/X01/X02/X03/X05; LESSONS 2--5. NULL: a future event,
duplicate writer-text component, shared prompt or discarded pilot group cannot
become independent test evidence. ALTERNATIVE: an actually prior reconstructed
draft and completed handling history support a new source-defined opportunity.
Every source/chronology exclusion stays in the ledger. All data were historically
exposed; this supplies descriptive prediction, never untouched confirmation or
a uniquely human intention in mixed human/model writing.
"""
from collections import Counter
from runners.stage9.common import ROOT,digest,file_hash,read
from runners.stage9.coauthor import DECISIONS,project
from runners.stage9.split_guard import Separation,disjoint_factors


def components(cross,corpus):
    groups={g for g,v in cross.groups.items() if v['corpus']==corpus};mapping={}
    for group in sorted(groups):
        if group in mapping:continue
        related=cross.connected({group})&groups;key=digest(sorted(related))
        for own in related:mapping[own]=key
    return mapping


def allocate(ledger,cross,scope,pilot_groups=()):
    if scope not in ('pilot','scientific'):raise ValueError('explicit prospective source scope required')
    people=components(cross,'coauthor');prompts=components(cross,'coauthor_prompts')
    dev={people['coauthor:'+r['writer']] for r in ledger if r.get('split')=='development'}
    discovered={people['coauthor:'+r['writer']] for r in ledger if r.get('split')=='discovery'}
    excluded=set(pilot_groups)
    allocation={}
    if scope=='pilot':
        ordered=sorted(dev,key=lambda x:digest(['s9-coauthor-pilot-partition',x]));n=len(ordered)
        if n<5:raise ValueError('too few independent exposed writer components for discarded rehearsal')
        for i,key in enumerate(ordered):allocation[key]='train' if i<3*n//5 else 'development' if i<4*n//5 else 'evaluation'
    else:
        # Preserve original writer roles; shared components cannot straddle them.
        fit_pool=dev-discovered;eval_pool=discovered-excluded
        ordered=sorted(fit_pool,key=lambda x:digest(['s9-coauthor-scientific-development-partition',x]))
        if len(ordered)<3 or not eval_pool:raise ValueError('source/pilot separation exhausted a required writer partition')
        for i,key in enumerate(ordered):allocation[key]='train' if i<2*len(ordered)//3 else 'development'
        for key in eval_pool:allocation[key]='evaluation'
    prompt_order=sorted(set(prompts.values()),key=lambda x:digest(['s9-coauthor-prompt-partition',x]));n=len(prompt_order)
    if n<5:raise ValueError('too few independent prompt components')
    prompt_allocation={key:'train' if i<3*n//5 else 'development' if i<4*n//5 else 'evaluation' for i,key in enumerate(prompt_order)}
    return people,prompts,allocation,prompt_allocation


def session_rows(session):
    if not session['usable']:raise ValueError('unusable source session cannot yield forecasts')
    history=[];rows=[];excluded=[];seen=set();last=-1
    for event in session['events']:
        ordinal=event['ordinal']
        if type(ordinal) is not int or ordinal<=last or ordinal in seen:raise ValueError('source opportunity chronology repeats or reverses')
        last=ordinal;seen.add(ordinal)
        key=digest({'session':session['key'],'event':ordinal})
        if not event['usable']:
            excluded.append({'key':key,'reason':'unsupported replay or handling semantics'});continue
        if event['decision'] not in DECISIONS or not event['options']:raise ValueError('native handling support or offered menu missing')
        artifact=project(event,'artifact');record=project(event,'record',history)
        if record['earlier_handling']!=[r['truth'] for r in rows]:raise ValueError('prior handling chronology differs')
        rows.append({'key':key,'writer':session['writer'],'prompt':session['prompt'],'session':session['key'],
            'domain':session['domain'],'ordinal':ordinal,'kind':'coauthor','truth':event['decision'],
            'views':{'artifact':artifact,'record':record},'prior_source_ordinals':[r['ordinal'] for r in history],
            'mixed_agency':'displayed suggestions are model-authored; outcome is the released subsequent handling classification'})
        history.append(event)
    return rows,excluded


def inputs(scope):
    prepared=ROOT/'private/prepared/coauthor-v2';identity=read(prepared/'IDENTITY.json');done=read(prepared/'COMPLETE.json')
    if done['identity_sha256']!=digest(identity) or done['reserve_groups']!=0:raise ValueError('canonical CoAuthor source identity differs')
    cross_root=ROOT/'private/prepared/cross-source-v2';cross=Separation.verified(cross_root);ledger=read(prepared/'LEDGER.json')
    pilot_groups=[]
    if scope=='scientific':
        pilot=ROOT/'private/record-case-pilots/coauthor-v1/CASES.json'
        if not pilot.exists():raise ValueError('complete discarded CoAuthor source rehearsal required before science')
        pilot_groups=sorted({r['unit'] for own in read(pilot).values() for r in own})
    people,prompts,allocation,prompt_allocation=allocate(ledger,cross,scope,pilot_groups)
    result={k:[] for k in ('train','development','evaluation')};excluded=[];source_files={};attempts=Counter()
    for item in sorted(ledger,key=lambda r:r['key']):
        if not item.get('usable'):
            excluded.append({'session':item['key'],'reason':item.get('reason','unusable source session')});continue
        if scope=='pilot' and item['split']!='development':continue
        group=people['coauthor:'+item['writer']];prompt=prompts['coauthor_prompts:'+item['prompt']]
        lane=allocation.get(group)
        if lane is None or prompt_allocation[prompt]!=lane:
            excluded.append({'session':item['key'],'reason':'writer/prompt mismatch or source/pilot-dependent component'});continue
        path=prepared/'sessions'/(item['key']+'.json');session=read(path);source_files[item['key']]=file_hash(path)
        if any(session[k]!=item[k] for k in ('key','writer','prompt','domain','split','usable','source_checks')):raise ValueError('session roster fields differ')
        own,invalid=session_rows(session);attempts[lane]+=len(session['events']);excluded.extend({'lane':lane,**r} for r in invalid)
        result[lane].extend({**r,'unit':group,'stimulus':prompt,'source_group':'coauthor:'+r['writer']} for r in own)
    pilot_sampling={}
    for lane in result:
        result[lane].sort(key=lambda r:digest(['s9-coauthor-target-order',r['key']]))
        if not result[lane]:raise ValueError('no valid source opportunity in required writer/prompt partition')
    if scope=='pilot':
        for lane in ('development','evaluation'):
            selected=[];groups=set();prompt_groups=set()
            for row in result[lane]:
                if row['unit'] in groups or row['stimulus'] in prompt_groups:continue
                selected.append(row);groups.add(row['unit']);prompt_groups.add(row['stimulus'])
                if len(selected)==2:break
            if not selected:raise ValueError('pilot has no valid separated source opportunity')
            pilot_sampling[lane]={'maximum_requested':2,'selected':len(selected),
                'available_writer_components':len({r['unit'] for r in result[lane]}),
                'available_prompt_components':len({r['stimulus'] for r in result[lane]}),
                'scope':'execution-only rehearsal; fewer than two independent pairs retained explicitly, no population estimate'}
            kept={r['key'] for r in selected};excluded.extend({'key':r['key'],'lane':lane,'reason':'bounded discarded execution sample'} for r in result[lane] if r['key'] not in kept)
            result[lane]=selected
    for a,b in [('train','development'),('train','evaluation'),('development','evaluation')]:
        disjoint_factors(result[a],result[b],('unit','stimulus'))
        keep,_=cross.filter_fit({r['source_group'] for r in result[a]},{r['source_group'] for r in result[b]})
        if set(keep)!={r['source_group'] for r in result[a]}:raise ValueError('unresolved source dependency crosses prospective partitions')
    metadata={'prepared_complete_sha256':file_hash(prepared/'COMPLETE.json'),'ledger_sha256':file_hash(prepared/'LEDGER.json'),
        'source_sessions':source_files,'cross_source_complete_sha256':file_hash(cross_root/'COMPLETE.json'),
        'writer_component_allocation':allocation,'prompt_component_allocation':prompt_allocation,'pilot_component_exclusions':pilot_groups,
        'counts':{lane:{'records':len(own),'writer_components':len({r['unit'] for r in own}),'writers':len({r['writer'] for r in own}),
            'prompt_components':len({r['stimulus'] for r in own}),'classes':dict(Counter(r['truth'] for r in own))} for lane,own in result.items()},
        'attempted_opportunities':dict(attempts),'exclusions':excluded,'pilot_sampling':pilot_sampling,'classes':{'coauthor':list(DECISIONS)},
        'data_scope':'all historically exposed; source-defined mixed-agency handling, no untouched confirmation',
        'independent_unit':'connected writer/text component crossed with prompt component; repeated session opportunities averaged within source',
        'reserve_payload_parsed':False,'scope':scope}
    return result,metadata
