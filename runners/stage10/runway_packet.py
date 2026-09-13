"""Finite queue disposition, costs and private final-review packet assembly.

DESIGN CHECK: LESSONS3-5. Under either hypothesis all reviewed jobs receive
one disposition. Missing evidence is explicit, never reported as success.
Agent/theory interpretation remains required; this does not auto-ratify claims.
"""
import argparse
from datetime import datetime
from pathlib import Path
from .queue import read
from .contracts import digest
from .ollama import write_new,now
from .revision_bank import sha,finish


def assemble(plan_path,queue,output):
    plan=read(plan_path);rows=[];sources={plan_path.as_posix():sha(plan_path)};analyses=[];examples=[]
    for job in plan['jobs']:
        if Path(job['output']).resolve()==output.resolve():continue
        saved=queue/'jobs'/(job['id']+'.json')
        if not saved.exists():raise ValueError('not at final reviewed queue boundary: '+job['id'])
        record=read(saved);sources[saved.as_posix()]=sha(saved)
        if record['job_sha256']!=digest(job):raise ValueError('queue job differs from frozen plan')
        seconds=(datetime.fromisoformat(record['finished_at'])-datetime.fromisoformat(record['started_at'])).total_seconds()
        row={'id':job['id'],'status':record['status'],'resource':job['resource'],'elapsed_seconds':seconds,'purpose':job['purpose'],
            'output':job['output'],'blocked_by':record.get('blocked_by',[]),'reason':record.get('reason')};rows.append(row)
        if record['status']!='COMPLETE':continue
        root=Path(job['output'])
        for name,expected in record['files'].items():
            p=root/name
            if not p.resolve().is_relative_to(root.resolve()) or sha(p)!=expected:raise ValueError('completed job output changed: '+job['id'])
        result=root/'RESULT.json'
        if result.exists():sources[result.as_posix()]=sha(result);analyses.append({'job':job['id'],'path':result.as_posix(),'sha256':sha(result)})
        roster=root/'ROSTER.json'
        if roster.exists():
            value=read(roster);attempts=value.get('rows',value.get('routes',[]));selected={}
            for item in sorted(attempts,key=lambda x:digest(x)):
                result=item.get('result',{});key=(item.get('arm'),result.get('status'))
                if key not in selected:selected[key]=item
            examples.extend({'job':job['id'],'selection':'first fixed-hash example per arm/status; not selected by accuracy','attempt':v} for v in selected.values())
    result={'schema':'stage10.runway-review.1','at':now(),'jobs':rows,'analyses':analyses,'sources':sources,
        'all_jobs_succeeded':all(r['status']=='COMPLETE' for r in rows),'scientific_verdict':False,'final_stage_packet':False,
        'cost_scope':'new native job elapsed time by declared resource; not measured GPU utilization, model callback cost or total agent setup. Historical reused predictions are charged in their original receipts, not again.',
        'dispositions':[
          {'branch':'recipient effects','status':'source unavailable','reason':'The reviewed V16 packet exposes no recipient/audience intervention interface; no human recipient labels are supplied. Do not invent a weaker world or call behavioral prediction recipient-effect recovery.'},
          {'branch':'larger external models','status':'held by owner','reason':'Gear 3 is not released.'},
          {'branch':'additional optional corpus','status':'deferred','reason':'The prepared second human source and existing local comparator take priority; no new corpus acquisition is needed to keep the commissioned local bank running.'}],
        'next':'inspect every complete cell, retained failures and execution readouts; finish FINDINGS/theory/TODO write-through and the single curator packet. No automatic new queue.'}
    output.mkdir(parents=True,exist_ok=False);write_new(output/'RESULT.json',result);write_new(output/'WORKED_EXAMPLE_CANDIDATES.json',examples)
    lines=['# Stage 10 local final-review packet','','Private assembly; human-facing scientific synthesis and write-through remain required.','',
        'Each row is one frozen job. Elapsed seconds measure native job duration, not GPU utilization. Failed and blocked work remains visible.','',
        '| Job | Status | Resource | Elapsed seconds |','|---|---|---|---:|']
    lines += [f"| {r['id']} | {r['status']} | {r['resource']} | {r['elapsed_seconds']:.1f} |" for r in rows]
    lines += ['','Complete numerical tables and exact raw bindings:','']+[f"- {a['job']}: `{a['path']}`" for a in analyses]
    lines += ['','Disposition notes:','']+[f"- {d['branch']}: {d['status']}. {d['reason']}" for d in result['dispositions']]
    (output/'DRAFT.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    return finish(output,digest([plan,sources]),{'scientific_verdict':False,'all_jobs_succeeded':result['all_jobs_succeeded']})


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['plan','queue','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try:assemble(a.plan,a.queue,a.output)
    except Exception as exc:
        if not (a.output/'FAILED.json').exists():write_new(a.output/'FAILED.json',{'at':now(),'error':repr(exc)})
        raise
