"""Deterministic post-pilot affordable prefix and pre-outcome analysis freeze.

DESIGN CHECK: LESSONS3-5. Both hypotheses receive the same identity-ranked
complete paired blocks. Actual pilot timing plus 25 percent and explicit startup/
export allowance determines admission. No score selects a branch or outcome.
"""
from collections import defaultdict
from copy import deepcopy
import argparse,hashlib,json,math,zipfile
from pathlib import Path
from runners.gear3_campaign import CampaignLedger,authoritative_ledger
from runners.gear3_plan import validate_pilot,affordable_jobs,validate_plan
from runners.gear3_round1 import account_backstop
from . import gear3_inputs as inputs,gear3_batch as batch,gear3_bundle as bundle,gear3_readouts
from . import human_baselines,human_memory,human_memory_routes,reading_memory,gear3_memory,ollama
from .contracts import digest,canonical
from .reader import from_record
from .queue import read
from .reading_source import persist


def paired_preflight(rows,training,profiles,native):
    receipts=[];learned=None
    for row in rows:
        task=from_record(row['record']);pool=training[task.family]
        if task.family=='coauthor-handling':
            if learned is None:learned=human_memory.induce(pool['public'],pool['answers'])
            library=learned
        else:
            library=reading_memory.induce(native,pool['public'],pool['answers'],
                     prior_observations=task.evidence['permitted_prior_artifacts'],prior_group=row['group'])
        for model,value in profiles.items():
            profile=ollama.ReaderProfile(**value);representations={};selections={}
            for name in ('grounded','opaque'):
                if task.family=='coauthor-handling':
                    rep,selected=human_memory_routes.representation_for(task,pool['public'],pool['answers'],library,'R4-'+name,profile=profile)
                else:
                    rep,selected=gear3_memory.paired_representation(task,row['envelope'],pool['public'],pool['answers'],library,profile,name)
                representations[name]=rep;selections[name]=selected
            def stripped(v):
                if isinstance(v,list):return [stripped(x) for x in v]
                return {k:stripped(x) for k,x in v.items() if k!='description'} if isinstance(v,dict) else v
            if stripped(representations['grounded'])!=representations['opaque']:raise ValueError('naming pair differs beyond descriptions')
            receipts.append({'task_id':task.task_id,'model':model,'grounded_sha256':digest(representations['grounded']),
                             'opaque_sha256':digest(representations['opaque']),'grounded_bytes':len(canonical(representations['grounded']).encode()),
                             'selections':selections,'identical_except_descriptions':True})
    return receipts


def consumer_sources(repo):
    names=['runners/gear3_plan.py','runners/stage10/gear3_freeze.py','runners/stage10/gear3_consumer.py',
           'runners/stage10/gear3_readouts.py','runners/stage10/gear3_comparison.py','runners/stage10/comparison.py',
           'runners/stage10/human_baselines.py','runners/stage10/gear3_replay.py','runners/stage10/gear3_batch.py',
           'runners/stage10/reading_source.py','runners/stage10/human_programs.py','runners/stage10/contracts.py']
    return {p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in names}


def freeze_analysis(repo,local_root,candidate,census,manifests,selection,evaluator_dir):
    base=local_root/'results/phase_2_4_stage_10/raw';locations={};meta={}
    needed={r['record']['task_id'] for _,m,_ in manifests for r in m['tasks']}
    native=base/'interface-v3/ghost-public';public_manifest=read(native/'PUBLIC_MANIFEST.json')
    case_members={c['case_id']:c['tasks_in_recorded_order'] for c in public_manifest['cases']}
    original_export=local_root.parents[1]/'AI and Intentionality/Ghost Scale Simulation/ghost-scale-sim/results/v16/transfer-fixture-2'
    original_manifest=(original_export/'RAW_MANIFEST.json').read_bytes();raw_manifest=json.loads(original_manifest)
    if hashlib.sha256(original_manifest).hexdigest()!=read(base/'ghost-opportunity-screen-v1/SOURCE.json')['raw_manifest_sha256']:
        raise ValueError('original Ghost evaluator inventory changed')
    for family,folder,phases in [('coauthor-handling','coauthor-screen-v1',['evaluation']),
             ('ghost-opportunity','ghost-opportunity-screen-v1',['development','evaluation']),('ghost-reading','reading-screen-v1',['development','evaluation'])]:
        prepared=base/folder;frozen=read(prepared/'FROZEN.json')
        for phase in phases:
            public=prepared/(phase+'-public.json')
            if not public.exists():continue
            data=read(public)
            if digest(data)!=frozen['public_sha256'][phase]:raise ValueError('public analysis source changed')
            if family.startswith('ghost-'):
                allocation=read(prepared/'ALLOCATION.json');groups={r['task_id']:r['case_id'] for r in allocation['tasks']}
                for record in data['tasks']:
                    tid=record['task_id']
                    if tid not in needed:continue
                    case=groups[tid];member='private/'+case+'-evaluation.json';raw=(original_export/member).read_bytes()
                    expected=raw_manifest['files'][member]
                    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('original private Ghost evaluator changed')
                    target=evaluator_dir/(case+'.json');target.parent.mkdir(parents=True,exist_ok=True)
                    if target.exists() and target.read_bytes()!=raw:raise ValueError('retained original evaluator differs')
                    if not target.exists():target.write_bytes(raw)
                    locations[tid]={'record':record,'evaluator':{'root':'campaign','kind':'ghost-native','path':target.relative_to(repo).as_posix(),
                        'sha256':expected,'case_id':case,'case_task_ids':case_members[case],'original_manifest_sha256':hashlib.sha256(original_manifest).hexdigest()},
                        'metadata':{'group':case,'event':tid,'session':None,'dependencies':['constructor:'+census['ghost'][family.removeprefix('ghost-')]['frozen_sha256']]}}
                continue
            evaluator=prepared/(phase+'-evaluator.json');raw=evaluator.read_bytes()
            if hashlib.sha256(raw.rstrip(b'\n')).hexdigest()!=frozen['evaluator_sha256'][phase]:raise ValueError('original evaluator seal changed')
            # Outcomes are discarded during parsing; only these identities escape.
            allowed={'targets','task_id','writer_component','prompt_component','source_event','session','ordinal','case_id'}
            identities=json.loads(raw,object_pairs_hook=lambda ps:{k:v for k,v in ps if k in allowed})['targets']
            by_id={x['task_id']:x for x in identities}
            if len(by_id)!=len(identities):raise ValueError('duplicate evaluator identity')
            for record in data['tasks']:
                tid=record['task_id'];g=by_id[tid]
                locations[tid]={'record':record,'evaluator':{'path':evaluator.relative_to(local_root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()},
                    'metadata':{'group':g['writer_component'] if family=='coauthor-handling' else g['case_id'],
                        'event':g['source_event'] if family=='coauthor-handling' else tid,
                        'session':g.get('session'),
                        'dependencies':['prompt:'+g['prompt_component']] if family=='coauthor-handling' else ['constructor:'+census['ghost'][family.removeprefix('ghost-')]['frozen_sha256']]}}
    blocks=[];targets={}
    for invocation,m,condition in manifests:
        ids=[r['record']['task_id'] for r in m['tasks']]
        for tid in ids:targets[tid]=locations[tid]
        t=from_record(m['tasks'][0]['record'])
        cell=digest([m['node'],condition,t.family,t.evidence_view,t.question,t.contributor_role,t.exposure])
        blocks.append({'invocation':invocation,'block_id':m['block_id'],'manifest_sha256':digest(m),'task_ids':ids,
                       'node':m['node'],'condition':condition,'cell':cell})
    training=census['human']['training'];fitted=human_baselines.fit(training['public'],training['answers'])
    return {'schema':'gear3.analysis.1','readout':gear3_readouts.DEFINITION,'targets':targets,
            'history_donors':{tid:d for tid,d in candidate['history_donors'].items() if tid in targets},
            'selection':selection,'blocks':blocks,'consumer_sources':consumer_sources(repo),
            'cheap_controls':{'sources':human_baselines.identity(),'training':training,'fitted':fitted,'fit_sha256':digest(fitted)},
            'local_source_root_sha256':digest(str(local_root.resolve()))}


def grouped(rows):
    groups={}
    for row in rows:
        t=from_record(row['record']);key=(t.family,t.evidence_view,t.question)
        groups.setdefault(key,[]).append(row)
    result=[]
    for key,part in groups.items():
        size=8 if key[0]=='coauthor-handling' else 4
        result.extend(part[i:i+size] for i in range(0,len(part),size))
    return result


def estimate(blocks,pilot,startup=300,export=60):
    timings=defaultdict(list)
    for r in pilot['route_timings']:timings[(r['family'],r['model'],r['arm'])].append(r['seconds'])
    observed=sum(r['seconds'] for r in pilot['route_timings'])
    nonunit=max(0,pilot['service_duration_seconds']-observed)
    # Includes actual repeated model load/unload and commits, plus conservative
    # fixed startup/export allowances absent from individual route timings.
    seconds=0
    for m in blocks:
        family=m['tasks'][0]['record']['family']
        for u in m['units']:
            values=timings.get((family,u['model'],u['arm']))
            if not values:raise ValueError('no measured literal route demand')
            seconds+=max(values)
        seconds+=nonunit  # intentionally one entire observed pilot overhead per block
    return math.ceil(1.25*(seconds+startup+export))


def freeze(repo,local_root,prepared,pilot_path,account_path,output):
    if output.exists():raise ValueError('new immutable PLAN destination required')
    account=account_backstop(account_path);ledger=CampaignLedger(authoritative_ledger(repo))
    native=local_root/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public'
    with ledger.transaction() as data:data=deepcopy(data)
    pilot=validate_pilot(repo,pilot_path,data,native)
    candidate=read(prepared/'CANDIDATES.json');c=read(prepared/'sources/CENSUS.json');receipt=read(prepared/'PREPARATION.json')
    if digest(candidate)!=receipt['candidate_roster_sha256'] or digest(c)!=receipt['source_census_sha256']:
        raise ValueError('pre-pilot candidate or source census changed')
    if digest(candidate)!=digest(inputs.roster(c)):raise ValueError('candidate order or sampling caps differ')
    source=bundle.source_closure(repo)
    if source!=pilot['execution_sources']:raise ValueError('literal pilot and scientific execution closure differ')
    profiles=pilot['profiles'];valid={tuple(x) for x in pilot['valid_routes']};selected={k:[] for k in 'ABCD'}
    training={'coauthor-handling':c['human']['training'],'ghost-reading':c['ghost']['reading']['training']}
    jobs=[];bound=[];excluded=[];a_owner={};c_preflight=[];number=0
    for node in 'ABCD':
        rows=([('ordinary',x) for x in candidate[node]] if node in {'A','C'} else
              [(x['condition'],x['row']) for x in candidate['B']] if node=='B' else [('ordinary',x) for x in candidate['D_candidates']])
        conditions={}
        for condition,row in rows:conditions.setdefault(condition,[]).append(row)
        if node=='B':conditions={'other-writer':conditions.get('other-writer',[])}
        for condition,part in conditions.items():
            eligible=[]
            for row in part:
                tid=row['record']['task_id'];family=row['record']['family']
                reason=('A counterpart not admitted' if node in {'B','C'} and tid not in a_owner else
                        'literal route not admitted' if any((family,model,arm) not in valid for model in profiles for arm in batch.METHODS[node]) else None)
                if reason:excluded.append({'node':node,'condition':condition,'task_id':tid,'reason':reason})
                else:eligible.append(row)
            # Prefix within every fixed source stratum, without selecting by result.
            stopped=False
            for chunk in grouped(eligible):
                if stopped:
                    excluded.extend({'node':node,'condition':condition,'task_id':r['record']['task_id'],'reason':'unadmitted prefix tail'} for r in chunk);continue
                number+=1;family=chunk[0]['record']['family'];pool={family:training[family]} if family in training else {}
                m=inputs.make_block(node,number,chunk,pool,profiles,source,condition)
                identifier='science-'+node.lower()+'-'+str(number).zfill(3)
                blocks=[m]
                if node=='B':
                    alternate={x['row']['record']['task_id']:x['row'] for x in candidate['B'] if x['condition']=='artifact-only'}
                    blocks.append(inputs.make_block(node,number,[alternate[r['record']['task_id']] for r in chunk],pool,profiles,source,'artifact-only'))
                seconds=estimate(blocks,pilot);deps=sorted({a_owner[r['record']['task_id']] for r in chunk}) if node in {'B','C'} else []
                job={'invocation':identifier,'node':node,'bundle':'pending','bundle_sha256':'pending','seconds':seconds,'startup_seconds':300,
                     'overhead_cents':25,'dependencies':deps,'failure_domain':node+'-'+family}
                try:
                    affordable_jobs(jobs+[job],data,account)
                    checked=paired_preflight(chunk,pool,profiles,native) if node=='C' else []
                except ValueError as exc:
                    excluded.extend({'node':node,'condition':condition,'task_id':r['record']['task_id'],'reason':str(exc)} for r in chunk);stopped=True;continue
                path=output/'bundles'/identifier;proof=bundle.build(repo,blocks,native,path,mode='science',profiles=profiles,server_version='0.32.14')
                job.update(bundle=(path/'INPUT.zip').relative_to(repo).as_posix(),bundle_sha256=proof['archive_sha256']);jobs.append(job);bound.extend((identifier,b,condition if i==0 else 'artifact-only') for i,b in enumerate(blocks));c_preflight.extend(checked)
                selected[node].extend(r['record']['task_id'] for r in chunk)
                if node=='A':a_owner.update({r['record']['task_id']:identifier for r in chunk})
    if not jobs or not selected['A']:raise ValueError('no complete affordable admitted core')
    selection={'candidate_counts':c['counts'],'candidate_roster_sha256':digest(candidate),'admitted':selected,'excluded':excluded,
               'sampling':'A at most 8 events/writer; B at most 2 initial events/writer per condition; Ghost cases before additional queries',
               'C_preflight':c_preflight,'second_human_source':c['second_human_source'],'outcomes_used':False}
    analysis=freeze_analysis(repo,local_root,candidate,c,bound,selection,output/'evaluators');persist(output/'ANALYSIS.json',analysis)
    plan={'schema':'gear3.execution_plan.2','approval':'Owner September 13 conditional rollout after panel repairs and final validation; $50 ceiling and lower account limits retained',
          'pilot':pilot_path.relative_to(repo).as_posix(),'pilot_sha256':digest(pilot),'jobs':jobs,
          'allowed_bundle_sha256':[j['bundle_sha256'] for j in jobs],'analysis':(output/'ANALYSIS.json').relative_to(repo).as_posix(),
          'analysis_sha256':digest(analysis),'affordability':affordable_jobs(jobs,data,account)}
    validate_plan(repo,plan,account,data,native);persist(output/'PLAN.json',plan)
    return plan


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('local-repo','prepared','pilot','account','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=freeze(Path(__file__).resolve().parents[2],a.local_repo.resolve(),a.prepared,a.pilot,a.account,a.output)
    print({'status':'FROZEN','jobs':len(r['jobs']),'additional_cents':r['affordability']['additional_cents']})
