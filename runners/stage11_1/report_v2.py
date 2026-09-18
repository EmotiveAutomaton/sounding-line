"""Whole-cell replay and comparison; never score an unfinished producer.

DESIGN CHECK: LESSONS 2-5. NULL: incomplete cells and changed responses cannot
enter a comparison; exact replay makes no model call. ALTERNATIVE: independent
methods on an identical roster retain separate proper scores, costs and utility.
"""
import argparse
import hashlib
from pathlib import Path
from .common import PRIVATE,read,freeze,digest
from .run_v2 import call,chain,source_pin
from .models_v2 import retained
from .score import episode,summarize
from .cheap import fit,predict


def analysis_pin():
    return {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
        ['runners/stage11_1/score.py','runners/stage11_1/cheap.py','runners/stage11_1/report_v2.py','runners/stage11_1/METHOD-v2.md']}


def analyze(job_id,root=PRIVATE):
    job=read(root/'jobs'/job_id/'JOB.json');complete=read(root/'jobs'/job_id/'COMPLETE.json')
    if complete['status']!='COMPLETE':raise ValueError('unfinished producer cannot be scored')
    if complete['sources']!=source_pin():raise ValueError('producer source identity differs')
    freeze(root/'ANALYSIS_PIN-v2.json',analysis_pin())
    if read(root/'ANALYSIS_PIN-v2.json')!=analysis_pin():raise ValueError('analysis changed')
    cohort=read(root/job.get('cohort_file','COHORT-S1.json'));lookup={r['key']:r for rows in cohort.values() for r in rows}
    own=[lookup[k] for k in job['keys']];model=fit(cohort['train']);freeze(root/'CHEAP_FIT.json',model)
    cells=[];private=[]
    for view in job['views']:
        for method in job['methods']+['alignment','marginal']:
            results=[];costs=[]
            for row in own:
                if method in ('alignment','marginal'):
                    forecast,detail=predict(row['views'][view],model,aligned=method=='alignment')
                    costs.append(dict(wall_seconds=None,input_tokens=0,output_tokens=0))
                else:
                    intermediate=None;parts=[]
                    for i,kind in enumerate(chain(method)):
                        path=root/'calls'/job_id/row['key']/view/method/str(i)
                        if not (path/'ATTEMPT.json').exists():raise ValueError('missing attempt; report never dispatches')
                        saved=call(path,row['views'][view],kind,job['branch'],intermediate,threads=job['threads'],fake=complete['fake'])
                        intermediate=retained(saved['forecast']);parts.append(saved)
                    forecast=parts[-1]['forecast'];detail=None
                    costs.append({k:sum(p['cost'][k] for p in parts) for k in ('wall_seconds','input_tokens','output_tokens')})
                scored=episode(row,forecast);results.append(scored)
                private.append(dict(method=method,view=view,score=scored,alignment_detail=detail))
            aggregate=summarize(results)
            aggregate['cost']=dict(logical_calls_per_episode=len(chain(method)) if method not in ('alignment','marginal') else 0,
                wall_seconds=sum(c['wall_seconds'] for c in costs) if all(c['wall_seconds'] is not None for c in costs) else None,
                input_tokens=sum(c['input_tokens'] for c in costs),output_tokens=sum(c['output_tokens'] for c in costs),
                cpu_timing='not measured in the replay scorer' if method in ('alignment','marginal') else None)
            cells.append(dict(method=method,view=view,**aggregate))
    result=dict(status='COMPLETE',job=job_id,branch=job['branch'],partition=job['partition'],cells=cells,
        pursuit=job['pursuit'],warrant=job['warrant'],next_action=job['next_action'],analysis_pin=analysis_pin(),
        units='constructed instrument rehearsal' if complete['fake'] else 'historically exposed human records; writer-weighted descriptive comparisons')
    freeze(root/'analysis'/job_id/'ROWS.json',private);freeze(root/'analysis'/job_id/'COMPLETE.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('job');args=p.parse_args();print(analyze(args.job))
