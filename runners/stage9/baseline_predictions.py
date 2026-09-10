"""Independent cheap-comparator execution on the complete assigned source cohort.

DESIGN CHECK: C01/C05/C08/M01/M04/X01/X02/X05/X06/X11/X12;
LESSONS 3--5, CONTROLS 2/6. NULL: failed program inference cannot block a valid
ordinary comparator; missing calls, changed fitting or duplicate sources refuse.
ALTERNATIVE: every trained baseline predicts the same explicit prospective task
through its actual restricted capsule. Source outcomes never enter the capsule.
Bands: complete forecasts with component validity, or implementation refusal;
development selection and scientific capability are separate consumers.
"""
import argparse
from pathlib import Path
import time
from runners.stage9 import baseline_matrix_runtime
from runners.stage9.artifact_comparisons import model_inputs,queries,checkpoint_call
from runners.stage9.common import REPO,ROOT,Units,closure,digest,distribution,file_hash,freeze,read
from runners.stage9.neural_operations import case_inputs
from runners.stage9.queue import inside,verify_sources,writer
from runners.stage9.recipes import sampled_world
from runners.stage9.series_cases import content_identity
from runners.stage9.training_jobs import cell_identity

VIEWS=('artifact','process_record')


def discovery_forecasts(cases,rows,models,doses):
    """Project every assigned query/model into B01 without dropping failed calls."""
    assigned=[case['unit'] for case in cases]
    completed=[row['unit'] for row in rows]
    if (not assigned or len(set(assigned))!=len(assigned)
            or len(set(completed))!=len(completed) or set(completed)!=set(assigned)):
        raise ValueError('complete unique assigned baseline source grid required')
    by_unit={row['unit']:row for row in rows};output=[]
    for case in cases:
        row=by_unit[case['unit']]
        if row['role']!=case['role'] or row['truth']!=case['target']:
            raise ValueError('baseline forecast source role or truth changed')
        expected={view+'|'+query:(view,evidence) for view in VIEWS
                  for query,evidence in queries(case,view,doses).items()}
        if set(row['rows'])!=set(expected):
            raise ValueError('complete baseline query grid required')
        forecasts={}
        for query,(view,evidence) in expected.items():
            cell=row['rows'][query]
            keys={model+'|'+route for model in models['models'][view]
                  for route in ('population','brief','cheap-8.0','cheap-16.0','cheap-32.0')}
            if (not keys or set(cell['validity'])!=keys
                    or any(type(v) is not bool for v in cell['validity'].values())
                    or set(cell['predictions'])!={key for key in keys if cell['validity'][key]}):
                raise ValueError('complete explicit baseline model validity grid required')
            if (cell['evidence_sha256']!=digest(evidence) or cell['support']!=evidence['support']
                    or row['truth'] not in evidence['support']):
                raise ValueError('baseline forecast evidence or support changed')
            forecasts[query]={}
            for key in sorted(keys):
                probabilities=cell['predictions'].get(key)
                if cell['validity'][key]:
                    distribution(probabilities)
                    if set(probabilities)!=set(evidence['support']):
                        raise ValueError('baseline forecast probability support changed')
                forecasts[query][key]={'valid':cell['validity'][key],'probabilities':probabilities}
        output.append({'unit':row['unit'],'target':'next_recorded_event',
                       'truth':row['truth'],'forecasts':forecasts})
    return output


def unit_result(case,models,call,doses):
    rows={};costs=[]
    for view in VIEWS:
        query_set=queries(case,view,doses)
        bundle={'evidences':query_set,'models':models['models'][view],'population_types':models['types'][view]}
        result=call(bundle,view)
        costs.append({'operation':'baselines','view':view,'accepted':result['accepted'],
                      'wall_seconds':result['wall_s'],'capsule':result['capsule']})
        keys=[key+'|'+route for key in models['models'][view]
              for route in ('population','brief','cheap-8.0','cheap-16.0','cheap-32.0')]
        for query,evidence in query_set.items():
            predictions=result['prediction']['predictions'][query] if result['accepted'] else {}
            if result['accepted'] and set(predictions)!=set(keys):raise ValueError('cheap comparator grid incomplete')
            for probabilities in predictions.values():
                distribution(probabilities)
                if set(probabilities)!=set(evidence['support']):raise ValueError('baseline support changed')
            rows[view+'|'+query]={'predictions':predictions,'validity':dict.fromkeys(keys,result['accepted']),
                'quality':{},'evidence_sha256':digest(evidence),'support':evidence['support'],
                'unique_prior_works':len({digest(w) for w in evidence['earlier']})}
    return {'unit':case['unit'],'role':case['role'],'rows':rows,'costs':costs,'truth':case['target'],
        'domain':case['private_factors']['domain'],'purpose':case['private_factors']['purpose'],
        'assistance':'training-fitted public features and fixed bag-of-marks adaptation; no program or neural gate dependency'}


def context(directory,cases_path,models_path,scope,doses,*,cell,source=None):
    """Original input and fitting checks, shared with saved final reconstruction."""
    directory=inside(directory)
    folder='baseline-prediction-pilots' if scope=='pilot' else 'scientific-baseline-predictions'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/folder):
        raise ValueError('baseline output scope mismatch')
    cases,role,case_sha=case_inputs(cases_path,scope,2 if scope=='pilot' else 0)
    models=model_inputs(models_path,role)
    training=read(inside(models_path)/'artifact-PREPARED.json')
    training_sources={content_identity(sampled_world(u['lineage'],'both')) for u in training['units']}
    if any(content_identity(w) in training_sources for c in cases for w in c['source_worlds']):
        raise ValueError('training world reused in prospective baseline prediction')
    source=source if source is not None else closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
        REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    identity={'cell_identity':cell,'operation':'independent-baseline-predictions-v1','scope':scope,'role':role,
        'source':source,'cases':str(inside(cases_path)),'models':str(inside(models_path)),
        'cases_complete_sha256':case_sha,'model_completion_sha256':models['completion_sha256'],
        'selected_units':[c['unit'] for c in cases],'doses':list(doses)}
    return identity,cases,models


def run(directory,cases_path,models_path,scope,doses):
    started,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=inside(directory)
    identity,cases,models=context(directory,cases_path,models_path,scope,doses,cell=cell)
    source=identity['source'];role=identity['role']
    with writer(directory):
        units=Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('complete baseline prediction identity changed')
            return done
        rows=[]
        for case in cases:
            old=units.get(case['unit'])
            def call(bundle,view):
                return checkpoint_call(directory/'calls'/case['unit'][:16]/(view+'.json'),bundle,
                    lambda:baseline_matrix_runtime.execute(bundle,root=directory/'capsules'),resume_only=old is not None)
            row=unit_result(case,models,call,doses)
            if old is not None and row!=old:raise ValueError('saved complete baseline unit does not reconstruct')
            units.put(case['unit'],row);rows.append(row)
        freeze(directory/'PREDICTIONS.json',rows)
        freeze(directory/'FORECASTS.json',discovery_forecasts(cases,rows,models,doses))
        verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'role':role,'execution_complete':True,
            'assigned_units':len(cases),'completed_units':len(units.all()),'source':source,
            'wall_seconds':time.monotonic()-started,'parent_cpu_seconds':time.process_time()-cpu,
            'cpu_scope':'parent only; each child capsule has a separate wall receipt',
            'outputs':closure([directory/p for p in ('IDENTITY.json','PREDICTIONS.json','FORECASTS.json','units','calls','capsules')]),
            'scientific_admission':False,'scores_computed':False}
        if done['completed_units']!=len(cases):raise ValueError('extra or missing baseline units')
        freeze(directory/'COMPLETE.json',done);return done


def argument_parser():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',type=Path,required=True);p.add_argument('--models',type=Path,required=True)
    p.add_argument('--scope',choices=('pilot','scientific'),required=True);p.add_argument('--doses',type=int,nargs='+',default=[0,1,3,7])
    return p


if __name__=='__main__':
    a=argument_parser().parse_args();run(a.output,a.cases,a.models,a.scope,tuple(a.doses))
