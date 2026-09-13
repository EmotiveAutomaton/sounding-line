"""Outcome-blind source census and finite Round 1 block preparation.

DESIGN CHECK: LESSONS2-5; Round 1 sections2-6. NULL/ALTERNATIVE get the same
hash-ranked writer-balanced roster. One human opportunity enters once, using
process records. Actual equal-length donors precede their source cutoffs under
the original validated adapter. Only selected public tasks and permitted
training labels enter cloud bundles; evaluator targets stay local.
"""
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict,replace
import argparse
import hashlib
from pathlib import Path
from . import gear3_batch as batch,ghost,human_history,human_programs,ollama
from .contracts import digest
from .human_effort_evaluation import metadata
from .queue import read
from .reader import from_record
from .reading_source import persist


def ordered(records,identities):
    groups=defaultdict(list)
    for r in records:groups[identities[r['task_id']]['writer_component']].append(r)
    for g in groups:groups[g].sort(key=lambda r:digest(['G3-round1-order',r['task_id']]))
    keys=sorted(groups,key=lambda g:digest(['G3-round1-writers',g]))
    return [groups[g][i] for i in range(max(map(len,groups.values()),default=0)) for g in keys if i<len(groups[g])]


def human_source(root):
    frozen=read(root/'FROZEN.json');files={};lanes={};groups={}
    for phase in ('train','evaluation'):
        public=read(root/(phase+'-public.json'))
        if digest(public)!=frozen['public_sha256'][phase]:raise ValueError('original public source changed')
        groups[phase]=metadata(root,phase,frozen)
        lanes[phase]=[r for r in public['tasks'] if r['evidence_view']=='process-record']
        for r in lanes[phase]:human_programs.features(from_record(r))
        for name in (phase+'-public.json',phase+'-evaluator.json'):
            files[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
    if {r['source_event'] for r in groups['train'].values()} & {r['source_event'] for r in groups['evaluation'].values()}:
        raise ValueError('training and target source events overlap')
    labels=read(root/'train-evaluator.json')
    if digest(labels)!=frozen['evaluator_sha256']['train']:raise ValueError('training labels changed')
    # Preserve the existing complete training pool, including its labelled views.
    # Only the evaluation population counts each opportunity once.
    training={'public':read(root/'train-public.json')['tasks'],
              'answers':[{k:r[k] for k in ('task_id','correct_choice','writer_component','source_event','prompt_component')} for r in labels['targets']]}
    evaluation=ordered(lanes['evaluation'],groups['evaluation'])
    if len({groups['evaluation'][r['task_id']]['source_event'] for r in evaluation})!=len(evaluation):
        raise ValueError('human opportunities counted twice')
    pairs,exclusions=human_history.pair_histories([from_record(r) for r in evaluation],groups['evaluation'])
    return {'frozen_sha256':digest(frozen),'files':files,'training':training,'evaluation':evaluation,
            'groups':groups,'history_pairs':pairs,'history_exclusions':exclusions,'exposure':frozen['source_exposure']}


def ghost_source(root,prepared,operation):
    frozen=read(prepared/'FROZEN.json');allocation=read(prepared/'ALLOCATION.json')
    if digest(allocation)!=frozen['allocation_sha256']:raise ValueError('original Ghost allocation changed')
    public_rows,_=ghost.envelopes(root);lookup={r['envelope']['task_id']:r for r in public_rows}
    archive=read(root/'ARCHIVE_MEMBER_MANIFEST.json')['files']
    selected=[];training={};files={}
    for lane in ('train','development','evaluation'):
        path=prepared/(lane+'-public.json')
        if not path.exists():continue
        public=read(path)
        if digest(public)!=frozen['public_sha256'][lane]:raise ValueError('original Ghost tasks changed')
        files[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        rows=[]
        for record in public['tasks']:
            task=from_record(record);row=lookup[task.task_id];env=row['envelope']
            member='public/observations/'+task.task_id+'.json'
            if hashlib.sha256((root/member).read_bytes()).hexdigest()!=archive[member]['sha256']:
                raise ValueError('native public observation changed')
            if task!=ghost.task_from(env) or env['declared_context']['operation']!=operation:
                raise ValueError('Ghost task projection changed')
            rows.append({'record':record,'envelope':env,'group':row['case_id']})
        if lane=='train':
            labels=read(prepared/'train-evaluator.json')
            if digest(labels)!=frozen['evaluator_sha256']['train']:raise ValueError('Ghost training labels changed')
            fields=('task_id','correct_choice','case_id')
            training={'public':public['tasks'],'answers':[{k:r[k] for k in fields} for r in labels['targets']]}
        else:selected.extend(rows)
    # Preserve targets: a case can contain several different questions, but an
    # identical public question is counted once. Model calls never create cases.
    unique={}
    for row in sorted(selected,key=lambda r:digest(['G3-round1-Ghost',r['record']['task_id']])):
        key=(row['group'],digest(from_record(row['record']).public()))
        unique.setdefault(key,row)
    return {'selected':list(unique.values()),'training':training,'files':files,
            'frozen_sha256':digest(frozen),'exposure':frozen['scope'],'excluded_pilot_cases':allocation['excluded_pilot_cases']}


def census(local_repo,output):
    base=local_repo/'results/phase_2_4_stage_10/raw';root=base/'interface-v3/ghost-public'
    # Already-produced local banks only. Never take future local reserve cases.
    for name in ('coauthor-evaluation-v1/COMPLETE.json','ghost-opportunity-development-v1/COMPLETE.json',
                 'reading-science-v1/COMPLETE.json'):
        if not (base/name).is_file():raise ValueError('local source bank has not completed: '+name)
    human=human_source(base/'coauthor-screen-v1')
    native={op:ghost_source(root,base/prepared,op) for op,prepared in
            [('opportunity','ghost-opportunity-screen-v1'),('reading','reading-screen-v1')]}
    counts={'human_opportunities':len(human['evaluation']),
            'human_writers':len({human['groups']['evaluation'][r['task_id']]['writer_component'] for r in human['evaluation']}),
            'matched_history_opportunities':len(human['history_pairs']),
            'ghost_tasks':{k:len(v['selected']) for k,v in native.items()}}
    result={'schema':'gear3.census.1','human':human,'ghost':native,'counts':counts,
            'second_human_source':'DEFERRED: no second Stage 10 human adapter was validated at this handoff',
            'truth_access':'original evaluator-byte identity projection only; evaluation answers were not returned or used'}
    persist(output/'CENSUS.json',result)
    return result


def make_block(node,number,rows,training,profiles,source_hashes,condition='ordinary'):
    # One source family, evidence condition and question per block.
    key=f'{node}-{condition}-{number:03d}'
    methods={'R0','R2','R3'} if node=='P' and rows[0]['record']['family']=='ghost-opportunity' else batch.METHODS[node]
    result={'schema':batch.SCHEMA,'block_id':key,'node':node,'profiles':profiles,'tasks':rows,'training':training,
        'source_hashes':source_hashes,'scope':'G3-S10-READER-1; '+condition+'; descriptive exposed-source screen',
        'units':[{'task_id':r['record']['task_id'],'model':model,'arm':arm}
                 for model in ('9b','27b') for r in rows for arm in sorted(methods)]}
    batch.validate(result)
    return result


def roster(c,*,human_n=64,ghost_n=12,history_n=24,memory_human_n=24,memory_ghost_n=6):
    limits=(human_n,ghost_n,history_n,memory_human_n,memory_ghost_n)
    if any(type(x)is not int or x<0 for x in limits) or any(a>b for a,b in zip(limits,(64,12,24,24,6))):
        raise ValueError('roster exceeds commissioned target')
    h=c['human'];humans=h['evaluation'][:human_n]
    human_rows=[{'record':r,'envelope':None,'group':h['groups']['evaluation'][r['task_id']]['writer_component']} for r in humans]
    # Interleave the two already-admitted Ghost families without treating calls as sources.
    lists=[c['ghost'][k]['selected'] for k in ('opportunity','reading')]
    native=[a[i] for i in range(max(map(len,lists),default=0)) for a in lists if i<len(a)][:ghost_n]
    a=human_rows+native;ids={r['record']['task_id'] for r in a}
    rank={r['record']['task_id']:i for i,r in enumerate(human_rows)}
    pairs=sorted((p for p in h['history_pairs'] if p['original']['task_id'] in ids),
                 key=lambda p:rank[p['original']['task_id']])[:history_n]
    b=[];donors={};sources={r['task_id']:r for r in h['evaluation']}
    for p in pairs:
        original=from_record(p['original']);donor=sources[p['donor_task_id']]
        g=h['groups']['evaluation'][p['donor_task_id']]
        donors[original.task_id]={'group':p['donor_writer'],'dependencies':['prompt:'+g['prompt_component']],
            'public':from_record(donor).public(),'source_record_sha256':digest(donor)}
        for condition in ('other-writer','artifact-only'):
            task=from_record(p['altered']) if condition=='other-writer' else replace(original,evidence_view='artifact',
                evidence={k:v for k,v in original.evidence.items() if k!='earlier_handling'})
            b.append({'condition':condition,'row':{'record':asdict(task),'envelope':None,'group':p['original_writer']}})
    memory=human_rows[:memory_human_n]+[r for r in native if r['record']['family']=='ghost-reading'][:memory_ghost_n]
    return {'A':a,'B':b,'C':memory,'history_donors':donors,
            'D_candidates':[{'record':r,'envelope':None,'group':h['groups']['evaluation'][r['task_id']]['writer_component']} for r in h['evaluation'][human_n:]]+
                [r for part in lists for r in part if r['record']['task_id'] not in ids]}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--local-repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=census(a.local_repo.resolve(),a.output)
    print(result['counts'])
