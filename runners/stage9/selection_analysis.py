"""Before/after acquisition calibration with independent makers as units.

DESIGN CHECK: S03/S04/X05/X06/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: repeated/irrelevant evidence has no true information gain; realized changes
can be negative. ALTERNATIVE: predicted gains track actual unseen-target gains.
Never clamp negative changes or discard zero forecasts. Every assigned path is
required and every purchased transition is checked; invalid paths invalidate their
profile. Cost-adjusted stopping is separate from raw prediction and observation
cost. Descriptive calibration is not a new scientific promotion threshold.
"""
import argparse
import math
import time
from pathlib import Path
from .artifact_analysis import check_units,load_complete
from .common import ROOT,Units,digest,file_hash,freeze
from .queue import inside,writer
from .revision_predictions import sources,reentry,finish
from .scoring import log_score,paired_extended,score_json
from .selection_jobs import STRATEGIES,STOP_COSTS
from .training_jobs import cell_identity


def difference(a,b):
    return None if a==b and not math.isfinite(a) else a-b


def mean(values):
    if not values or None in values:return None
    if math.inf in values and -math.inf in values:return None
    return math.fsum(values)/len(values)


def transitions(row,view,strategy):
    trace=row['traces'][view+'|'+strategy];steps=trace['steps']
    if not trace['valid'] or not steps or any(not s['accepted'] for s in steps):return None
    if (trace['allow_stop'] or trace['strategy']!=strategy or trace['cost_nats']!=0
            or steps[0]['purchased'] or not steps[-1]['output']['stop']):
        raise ValueError('fixed acquisition path lacks its declared beginning or complete ending')
    result=[]
    for index,(before,after) in enumerate(zip(steps,steps[1:])):
        a,b=before['output'],after['output'];chosen=a['selected']
        if (before['step']!=index or after['step']!=index+1 or a['stop']
                or chosen in before['purchased'] or chosen not in a['calculations']
                or set(after['purchased'])!=set(before['purchased'])|{chosen}
                or len(after['purchased'])!=len(before['purchased'])+1
                or a['purchased_observations']!=index or b['purchased_observations']!=index+1):
            raise ValueError('next observation did not follow the saved pre-purchase decision')
        predicted=a['calculations'][chosen]
        actual_gain=difference(log_score(b['prediction'],row['truth']),log_score(a['prediction'],row['truth']))
        result.append({'predicted_model_information':predicted['expected_model_information_nats'],
            'realized_model_entropy_reduction':a['model_entropy_nats']-b['model_entropy_nats'],
            'predicted_future_gain':predicted['expected_future_log_gain_nats'],
            'realized_future_gain':actual_gain})
    return result


def describe(rows,expected,*,draws=4000):
    check_units(rows,expected);profiles={}
    for view in ('artifact','process_record'):
        for strategy in STRATEGIES:
            points={};invalid=[]
            for row in rows:
                values=transitions(row,view,strategy)
                if values is None:invalid.append(row['unit'])
                else:points[row['unit']]=values
            key=view+'|'+strategy
            if invalid:
                profiles[key]={'disposition':'IMPLEMENTATION INVALID','assigned_units':len(expected),
                    'invalid_units':invalid,'scored_units':0,'excluded_units':0};continue
            metrics={}
            for metric in ('predicted_model_information','realized_model_entropy_reduction','predicted_future_gain','realized_future_gain'):
                units=[{'unit':u,'difference':mean([v[metric] for v in values])} for u,values in points.items()]
                metrics[metric]=paired_extended(units,draws=draws,seed=9011)
            for name,left,right in (('future_prediction_error','predicted_future_gain','realized_future_gain'),
                                    ('model_information_error','predicted_model_information','realized_model_entropy_reduction')):
                units=[{'unit':u,'difference':mean([None if v[right] is None else difference(v[left],v[right]) for v in values])}
                       for u,values in points.items()]
                metrics[name]=paired_extended(units,draws=draws,seed=9011)
            profiles[key]={'disposition':'DESCRIPTIVE','assigned_units':len(expected),'scored_units':len(expected),
                'excluded_units':0,'purchased_transitions':sum(map(len,points.values())),
                'metrics':metrics,'unit_transition_sha256':digest(score_json(points)),
                'weighting':'average purchased transitions within each maker, then equal independent makers',
                'scope':'conditional empirical calibration of fitted-model predictions; no error threshold or automatic promotion'}
        for cost in STOP_COSTS:
            units=[];invalid=[];cost_rows=[]
            for row in rows:
                stopped=row['rows'][view+'|future-stop-'+str(cost)+'|stopped']
                full=row['rows'][view+'|future_prediction|7']
                if not stopped['validity']['program'] or not full['validity']['program']:
                    invalid.append(row['unit']);continue
                gain=difference(log_score(stopped['predictions']['program'],row['truth']),log_score(full['predictions']['program'],row['truth']))
                saved=full['purchase_cost']-stopped['purchase_cost']
                if stopped['preview_cost']!=full['preview_cost'] or saved<0 or not full['full_view']:
                    raise ValueError('stopping comparison lacks shared preview cost or full observation endpoint')
                units.append({'unit':row['unit'],'difference':None if gain is None else gain+saved*cost})
                cost_rows.append({'unit':row['unit'],'saved_purchases':saved})
            profiles[view+'|stopping-utility-'+str(cost)]=({'disposition':'IMPLEMENTATION INVALID',
                'assigned_units':len(expected),'scored_units':0,'invalid_units':invalid,'excluded_units':0} if invalid else
                {'disposition':'DESCRIPTIVE','assigned_units':len(expected),'scored_units':len(expected),'excluded_units':0,
                 'cost_nats_per_purchase':cost,'cost_adjusted_log_score_difference':paired_extended(units,draws=draws,seed=9011),
                 'saved_purchases':cost_rows,'scope':'stopped versus continued future-gain policy; raw quality remains in separate prospective profiles'})
    return profiles


def run(directory,predictions,role):
    start,cpu=time.monotonic(),time.process_time()
    if role not in ('pilot','discovery'):raise ValueError('no development or reserve calibration')
    directory,predictions=map(inside,(directory,predictions))
    namespace=ROOT/'private'/('selection-calibration-pilots' if role=='pilot' else 'scientific-selection-calibration')
    if not directory.is_relative_to(namespace):raise ValueError('selection calibration outside its role namespace')
    rows,expected,identity,done=load_complete(predictions,role)
    if identity['operation']!='selection-predictions-v1':raise ValueError('calibration requires actual sequential selection predictions')
    own={'operation':'selection-calibration-v1','cell_identity':cell_identity(),'scope':'pilot' if role=='pilot' else 'scientific',
        'role':role,'source':sources(),'prediction_complete_sha256':file_hash(predictions/'COMPLETE.json'),
        'model_completion_sha256':identity['model_completion_sha256'],'costs_nats':list(STOP_COSTS)}
    with writer(directory):
        Units(directory,own);prior=reentry(directory,own)
        if prior is not None:return prior
        profiles=describe(rows,expected)
        freeze(directory/'CALIBRATION.json',score_json(profiles))
        return finish(directory,own,start,cpu,['CALIBRATION.json'],role=role,assigned_units=len(expected),
            scientific_admission=False,disposition='DESCRIPTIVE')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('root','predictions','role'):p.add_argument('--'+k,required=True)
    a=p.parse_args();run(Path(a.root),Path(a.predictions),a.role)
