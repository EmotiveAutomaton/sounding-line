"""Actual source-series predictions for the five purpose treatments.

DESIGN CHECK: M03/X01/X02/X05/X06/X11; LESSONS 3--5. NULL: hidden future
changes cannot change ordinary reader inputs; invalid components stay unscored.
ALTERNATIVE: independently fitted purpose policies support distinct complete
forecasts with true/false information confined to explicitly supplied diagnostics.
All opportunities stay assigned, with separate development selection and held-out
analysis delegated to artifact_analysis. No reserve access or automatic promotion.
"""
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
import time

from . import baseline_matrix_runtime, comparison_runtime
from .artifact_comparisons import checkpoint_call, model_inputs, validate_cases
from .artifact_training import sampled_world
from .common import REPO, ROOT, Units, closure, digest, distribution, file_hash, freeze, read
from .queue import inside, verify_sources, writer
from .revision_predictions import sources
from .series_cases import content_identity, dose_view
from .training_jobs import cell_identity

DOSES = (0, 7)
ORDINARY = ('purpose_agnostic', 'inferred_distribution', 'single_purpose')


def inputs(cases_path, models_path, role, pilot_units=None, pilot_offset=0):
    cases_path, models_path = inside(cases_path), inside(models_path)
    prepared = read(cases_path.parent/'COMPLETE.json')
    if prepared.get('accepted') is not True or prepared['role'] != role:
        raise ValueError('purpose source preparation failed or has a different role')
    if closure([REPO/p for p in prepared['outputs']['files']]) != prepared['outputs']:
        raise ValueError('purpose source outputs changed')
    cases = read(cases_path)
    if pilot_units is not None:
        if (role != 'pilot' or type(pilot_units) is not int or type(pilot_offset) is not int or
                pilot_units < 1 or pilot_offset < 0 or pilot_units+pilot_offset > len(cases)):
            raise ValueError('only a discarded pilot can select a bounded source subset')
        cases = sorted(cases,key=lambda c:digest({'purpose_pilot_order':c['unit']}))[pilot_offset:pilot_offset+pilot_units]
    elif pilot_offset:
        raise ValueError('pilot offset requires an explicit pilot subset')
    validate_cases(cases,role)
    package = model_inputs(models_path,role)
    fitting = read(models_path/'artifact-PREPARED.json')
    training = {content_identity(sampled_world(u['lineage'],'both')) for u in fitting['units']}
    if any(content_identity(w) in training for c in cases for w in c['source_worlds']):
        raise ValueError('fitting world reused in purpose prediction')
    audit = read(models_path/'LIBRARY_FIT.json')['cohorts']
    # These are training-cohort labels, justified by the separately validated
    # fitted package. The query's actual purpose is not present in ordinary input.
    purpose_groups = {c:audit[c]['purpose_training_cohort'] for c in package['library']['candidates']}
    labels = sorted(set(purpose_groups.values()))
    if any(c['private_factors']['purpose'] not in labels for c in cases):
        raise ValueError('query purpose missing from declared diagnostic support')
    return cases, package, purpose_groups


def forecast_unit(case, package, purpose_groups, directory, *, resume_only=False):
    directory=Path(directory); rows={}; costs=[]
    queries={'dose'+str(d):dose_view(case,d,'process_record') for d in DOSES}
    base_input={'evidences':queries,'models':package['models']['process_record'],
                'population_types':package['types']['process_record']}
    base=checkpoint_call(directory/'baselines.json',base_input,
        lambda:baseline_matrix_runtime.execute(base_input,root=directory/'caps-baseline'),resume_only=resume_only)
    costs.append({'operation':'baselines','accepted':base['accepted'],'wall_seconds':base['wall_s'],'capsule':base['capsule']})
    labels=sorted(set(purpose_groups.values()));truth=case['private_factors']['purpose']
    false=labels[(labels.index(truth)+1)%len(labels)]
    for name,query in queries.items():
        predictions={};validity={};evidence_hashes={};quality={}
        for model in package['models']['process_record']:
            for route in ('population','brief','cheap-8.0','cheap-16.0','cheap-32.0'):
                key=model+'|'+route;validity[key]=base['accepted'];evidence_hashes[key]=digest(base_input)
                if base['accepted']:predictions[key]=base['prediction']['predictions'][name][key]
        ordinary={'evidence':query,**package['library'],'purpose_groups':purpose_groups,'mode':'ordinary'}
        for mode in ('ordinary','supplied_true','supplied_false'):
            bundle=dict(ordinary)
            if mode != 'ordinary':
                chosen=truth if mode=='supplied_true' else false
                bundle.update(mode='supplied',supplied_purpose={p:float(p==chosen) for p in labels})
            result=checkpoint_call(directory/(name+'-'+mode+'.json'),bundle,
                lambda:comparison_runtime.execute(bundle,operation='purpose_comparison',budget=800000,
                                                   root=directory/'caps-purpose'),resume_only=resume_only)
            costs.append({'operation':mode,'dose':name,'accepted':result['accepted'],
                          'wall_seconds':result['wall_s'],'capsule':result['capsule']})
            for key in ORDINARY if mode=='ordinary' else (mode,):
                validity[key]=result['accepted'];evidence_hashes[key]=digest(bundle)
                if result['accepted']:
                    forecast=result['prediction']['predictions'][key if mode=='ordinary' else 'supplied']
                    validity[key]=forecast['exact_within_declared_model'] is True
                    if validity[key]:predictions[key]=forecast['prediction']
                    quality[key]={'exact_within_declared_model':forecast['exact_within_declared_model'],
                                  'supplied_query_purpose':mode!='ordinary'}
        for prediction in predictions.values():
            distribution(prediction)
            if set(prediction)!=set(query['support']):raise ValueError('purpose prediction support changed')
        rows['process_record|'+name]={'predictions':predictions,'validity':validity,'quality':quality,
            'evidence_sha256':digest(query),'support':query['support'],
            'model_input_sha256':evidence_hashes,'unique_prior_works':len({digest(w) for w in query['earlier']})}
    return {'unit':case['unit'],'role':case['role'],'truth':case['target'],'rows':rows,'costs':costs,
            'domain':case['private_factors']['domain'],'purpose':truth,
            'supplied_false_purpose':false,'assistance':'fitted executable process model; supplied arms explicitly privileged'}


def context(directory,cases_path,models_path,role,*,cell,source=None,
            pilot_units=None,pilot_offset=0,consumer='purpose'):
    """Original input, identity and dispatch construction; no output writer."""
    if role not in ('pilot','development','discovery'):raise ValueError('no reserve access in purpose prediction')
    if consumer not in ('purpose','proposal','transfer','goal','cue','ambiguity','constraint','familiarity','selection','familiarity-entry'):raise ValueError('unknown explicit maker consumer')
    forecast_function=forecast_unit
    if consumer=='proposal':
        from .proposal_jobs import forecast_unit as forecast_function
    elif consumer=='transfer':
        from .transfer_jobs import forecast_unit as forecast_function
    elif consumer=='goal':
        from .goal_jobs import forecast_unit as forecast_function
    elif consumer=='cue':
        from .cue_jobs import forecast_unit as forecast_function
    elif consumer=='ambiguity':
        from .ambiguity_jobs import forecast_unit as forecast_function
    elif consumer=='constraint':
        from .constraint_jobs import forecast_unit as forecast_function
    elif consumer=='familiarity':
        from .familiarity_jobs import forecast_unit as forecast_function
    elif consumer=='selection':
        from .selection_jobs import forecast_unit as forecast_function
    elif consumer=='familiarity-entry':
        from .familiarity_entry_jobs import forecast_unit as forecast_function
    directory=inside(directory)
    namespace=ROOT/'private'/(consumer+'-prediction-pilots' if role=='pilot' else 'scientific-'+consumer+'-predictions')
    if not directory.is_relative_to(namespace):raise ValueError('purpose output outside its declared role namespace')
    cases,package,purposes=inputs(cases_path,models_path,role,pilot_units,pilot_offset)
    identity={'operation':consumer+'-predictions-v1','role':role,'cell_identity':cell,'source':sources() if source is None else source,
        'cases_sha256':file_hash(cases_path),'case_completion_sha256':file_hash(Path(cases_path).parent/'COMPLETE.json'),
        'model_completion_sha256':package['completion_sha256'],'purpose_groups_sha256':digest(purposes),
        'selected_units':[c['unit'] for c in cases],'doses':list(DOSES) if consumer=='purpose' else [0] if consumer=='ambiguity' else [1] if consumer=='constraint' else [3] if consumer in ('familiarity','familiarity-entry') else [7],'budget_per_evaluation_call':800000,
        'supplied_false_policy':'next training purpose in sorted cyclic catalogue' if consumer=='purpose' else None,
        'unqualified_artifact_disposition':('bounded action-budget observation has separate exact-model qualification; long-artifact envelope stays failed'
            if consumer in ('constraint','familiarity','selection','familiarity-entry') else 'NOT RUN WITH REASON: previously failed numerical envelope')}
    return identity,cases,package,purposes,forecast_function


def run(directory,cases_path,models_path,role,*,pilot_units=None,pilot_offset=0,consumer='purpose'):
    start,cpu=time.monotonic(),time.process_time()
    cell=cell_identity() if role!='pilot' else os.environ.get('S9_CELL_IDENTITY')
    directory=inside(directory)
    identity,cases,package,purposes,forecast_function=context(directory,cases_path,models_path,role,
        cell=cell,pilot_units=pilot_units,pilot_offset=pilot_offset,consumer=consumer)
    with writer(directory):
        units=Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('purpose completion changed')
            return done
        rows=[]
        for case in cases:
            key={'unit':case['unit']};saved=units.get(key)
            actual=forecast_function(case,package,purposes,directory/'calls'/digest(key)[:12],resume_only=saved is not None)
            if saved is not None and saved!=actual:raise ValueError('purpose readouts differ from committed capsule outputs')
            if saved is None:units.put(key,actual)
            rows.append(actual)
        freeze(directory/'PREDICTIONS.json',rows);verify_sources(identity['source'])
        done={'at':datetime.now(timezone.utc).isoformat(),'identity_sha256':digest(identity),'source':identity['source'],
            'cell_identity':cell,'role':role,'execution_complete':True,'assigned_units':len(cases),'completed_units':len(rows),
            'wall_seconds':time.monotonic()-start,'cpu_seconds':time.process_time()-cpu,'gpu_seconds':0,
            'cpu_scope':'parent excludes restricted readers','scientific_promotion':False,
            'outputs':closure([directory/'PREDICTIONS.json',directory/'units',directory/'calls'])}
        freeze(directory/'COMPLETE.json',done);return done


def argument_parser():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('root','cases','models','role'):p.add_argument('--'+k,required=True)
    p.add_argument('--pilot-units',type=int);p.add_argument('--pilot-offset',type=int,default=0)
    p.add_argument('--consumer',choices=('purpose','proposal','transfer','goal','cue','ambiguity','constraint','familiarity','selection','familiarity-entry'),default='purpose')
    return p


if __name__=='__main__':
    a=argument_parser().parse_args();run(Path(a.root),Path(a.cases),Path(a.models),a.role,pilot_units=a.pilot_units,pilot_offset=a.pilot_offset,consumer=a.consumer)
