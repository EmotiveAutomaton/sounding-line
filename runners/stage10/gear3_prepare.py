"""Prepare the discarded pilot and candidate study without cloud or outcome access.

DESIGN CHECK: LESSONS2-5. Source identities and held-out pilot events are checked
before any dispatch. Full paired rosters and existing cheap controls are retained;
null and alternative get the same frozen selection. Candidate sizes are ceilings,
not scientific admission; measured pilot demand determines the affordable PLAN.
"""
import argparse
from dataclasses import asdict,replace
from pathlib import Path
from . import gear3_inputs as inputs,gear3_bundle as bundle,gear3_batch as batch,ghost,human_baselines,ollama
from .contracts import digest
from .queue import read
from .reader import from_record
from .reading_source import persist


def prepare(local_repo,output):
    repo=Path(__file__).resolve().parents[2];native=local_repo/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public'
    c=inputs.census(local_repo,output/'sources');source=bundle.source_closure(repo)
    profiles={k:asdict(ollama.ReaderProfile('qwen3.5:'+k,batch.PINS[k],'0.32.14')) for k in batch.PINS}
    candidate=inputs.roster(c);persist(output/'CANDIDATES.json',candidate)
    training=c['human']['training'];identities=c['human']['groups']['train']
    ranked=sorted((r for r in training['public'] if r['evidence_view']=='process-record'),
                  key=lambda r:(-len(str(r).encode('utf8')),r['task_id']))
    selected=ranked[:2];events={identities[r['task_id']]['source_event'] for r in selected}
    retained={r['task_id'] for r in training['public'] if identities[r['task_id']]['source_event'] not in events}
    pilot_training={'public':[r for r in training['public'] if r['task_id'] in retained],
                    'answers':[r for r in training['answers'] if r['task_id'] in retained]}
    human_rows=[{'record':r,'envelope':None,'group':identities[r['task_id']]['writer_component']} for r in selected]
    blocks=[inputs.make_block('P',1,human_rows,{'coauthor-handling':pilot_training},profiles,source,'literal-human')]
    all_native,_=ghost.envelopes(native)
    for number,(operation,pilot_case) in enumerate([('opportunity','318c3dff39044fb78a1be45b83db3777'),('reading','bf1690a65f214c978ebf6d5a1020d3e5')],2):
        row=next(r for r in all_native if r['case_id']==pilot_case and r['envelope']['declared_context']['operation']==operation)
        task=ghost.task_from(row['envelope']);rows=[{'record':asdict(task),'envelope':row['envelope'],'group':row['case_id']}]
        permitted={'ghost-reading':c['ghost']['reading']['training']} if operation=='reading' else {}
        blocks.append(inputs.make_block('P',number,rows,permitted,profiles,source,'literal-'+operation))
    # An explicit constructed boundary request checks maximum permitted input
    # handling and observed memory. It supplies no effect or throughput estimate.
    original=from_record(selected[0]);task=replace(original,task_id=digest(['G3-P-context-boundary'])[:32],
        evidence_view='artifact',evidence={k:v for k,v in original.evidence.items() if k!='earlier_handling'})
    low,high=1,17000
    while low<high:
        middle=(low+high+1)//2;probe=replace(task,evidence={**task.evidence,'document':'x '*middle})
        try:ollama.request_for(probe,profile=ollama.ReaderProfile(**profiles['27b']))
        except ValueError:high=middle-1
        else:low=middle
    task=replace(task,evidence={**task.evidence,'document':'x '*low})
    stress=inputs.make_block('P',4,[{'record':asdict(task),'envelope':None,'group':'constructed-context-boundary'}],
        {'coauthor-handling':pilot_training},profiles,source,'context-boundary')
    stress['units']=[u for u in stress['units'] if u['arm']=='R0'];batch.validate(stress);blocks.append(stress)
    # The full fitted baseline is shared by all cloud model contrasts. Labels
    # used here belong solely to the original permitted training population.
    fitted=human_baselines.fit(training['public'],training['answers']);predictions=[];seen=set()
    for condition,rows in [('ordinary',candidate['A']+candidate['C']+candidate['D_candidates'])]+[(kind,[x['row'] for x in candidate['B'] if x['condition']==kind]) for kind in ('other-writer','artifact-only')]:
        for row in rows:
            task=from_record(row['record'])
            if task.family!='coauthor-handling' or (condition,task.task_id) in seen:continue
            seen.add((condition,task.task_id))
            for arm in human_baselines.ARMS:predictions.append({'task_id':task.task_id,'condition':condition,'arm':arm,
                'task_public':task.public(),'status':'VALID','forecast':human_baselines.predict(task,fitted,arm)})
    persist(output/'CHEAP_CONTROLS.json',{'sources':human_baselines.identity(),'fitted':fitted,'predictions':predictions,'evaluation_answers_used':False})
    cache=bundle.build(repo,[],native,output/'cache',mode='cache',profiles=profiles,server_version='0.32.14')
    literal=bundle.build(repo,blocks,native,output/'pilot',mode='science',profiles=profiles,server_version='0.32.14')
    bundle.validate_input(output/'cache/INPUT.zip',repo,native);bundle.validate_input(output/'pilot/INPUT.zip',repo,native)
    receipt={'schema':'gear3.preparation.1','status':'READY_FOR_DISCARDED_PILOT_AFTER_ACCOUNT_BACKSTOP',
        'at':ollama.now(),'source_counts':c['counts'],'candidate_roster_sha256':digest(candidate),'source_census_sha256':digest(c),
        'pilot_units':sum(len(b['units']) for b in blocks),'pilot_blocks':[{'block_id':b['block_id'],'units':len(b['units']),'sha256':digest(b)} for b in blocks],
        'cache_archive_sha256':cache['archive_sha256'],'pilot_archive_sha256':literal['archive_sha256'],
        'profiles':profiles,'execution_source_hashes':source,'cheap_control_forecasts':len(predictions),
        'pilot_training_events_excluded':len(events),'constructed_context_boundary_not_for_scientific_effects':True,
        'science_status':'not admitted or dispatched; size/freeze after measured pilot',
        'second_human_source':c['second_human_source'],'account_backstop':'pending actual workspace limits, credits and sharing information'}
    persist(output/'PREPARATION.json',receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--local-repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=prepare(a.local_repo.resolve(),a.output)
    print({k:r[k] for k in ('status','source_counts','pilot_units','cheap_control_forecasts')})
