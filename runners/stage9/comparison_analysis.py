"""Evaluator-side complete-grid contrasts and frozen development rival selection.

DESIGN CHECK: M01/C08/X06/X11; LESSONS 3--5. NULL: equal forecasts give zero
gain; a shuffled or stronger cheap predictor can defeat a richer model. ALTERNATIVE:
a real prospective probability advantage yields a positive paired contrast. Missing
units, components, support or eligible rivals refuse analysis; no selected valid-only
subset. One rival is selected on development, never the per-target best comparator.
Bands are the shared Stage 9 exhaustive paired-score dispositions. No p-values here.
"""
from collections import Counter,defaultdict
import math

from .common import digest,distribution
from .scoring import classify,log_score,paired_extended,score_json


def complete_rows(rows, expected_units, required_predictions):
    rows = list(rows)
    expected_units = list(expected_units)
    if not expected_units or len(expected_units)!=len(set(expected_units)):
        raise ValueError('nonempty unique complete unit allocation required')
    if len(rows)!=len(expected_units) or {r['unit'] for r in rows}!=set(expected_units):
        raise ValueError('incomplete or duplicated independent units')
    if not required_predictions or len(required_predictions)!=len(set(required_predictions)):
        raise ValueError('explicit unique comparator inventory required')
    for row in rows:
        if row.get('valid') is not True:
            raise ValueError('invalid component; no finite-only or valid-only analysis')
        if not set(required_predictions)<=set(row['predictions']):
            raise ValueError('required comparator missing from row')
        reference = None
        for key in required_predictions:
            pred = distribution(row['predictions'][key])
            if row['truth'] not in pred or (reference is not None and set(pred)!=reference):
                raise ValueError('paired target or complete support mismatch')
            reference=set(pred)
    return rows


def select_rival(rows,expected_units,eligible,*,role,package_sha256):
    if role!='development' or not isinstance(package_sha256,str) or len(package_sha256)!=64:
        raise ValueError('rival selection requires development and a fixed package identity')
    rows=complete_rows(rows,expected_units,eligible)
    scores={key:math.fsum(log_score(r['predictions'][key],r['truth']) for r in rows)/len(rows) for key in eligible}
    # Zero forecasts remain legitimate failed rivals, never clipped at their truth.
    finite=[key for key in eligible if math.isfinite(scores[key])]
    if not finite:
        raise ValueError('all development rivals assign a zero to a recorded target')
    selected=sorted(finite,key=lambda key:(-scores[key],key))[0]
    return {'kind':'s9-development-rival-v1','role':role,'selected':selected,
            'eligible':list(eligible),'scores':score_json(scores),'units':sorted(expected_units),
            'package_sha256':package_sha256,'input_sha256':digest(rows),
            'rule':'highest equal-independent-unit mean log score; lexical key breaks exact ties',
            'selection_scope':'one frozen comparator; no per-target best-of oracle'}


def contrast(rows,expected_units,*,left,right,threshold=.05,seed=9011,draws=4000,
             selection=None,package_sha256=None,strata=('domain',)):
    if left==right:
        raise ValueError('contrast must name distinct routes')
    if selection is not None:
        if (selection.get('kind')!='s9-development-rival-v1' or selection.get('role')!='development' or
            selection.get('package_sha256')!=package_sha256 or right!=selection.get('selected')):
            raise ValueError('selected rival belongs to another contrast or package')
        if set(expected_units)&set(selection['units']):
            raise ValueError('development selection units entered the held-out contrast')
    rows=complete_rows(rows,expected_units,[left,right])
    paired=[]
    for row in rows:
        a=log_score(row['predictions'][left],row['truth'])
        b=log_score(row['predictions'][right],row['truth'])
        paired.append({'unit':row['unit'],'difference':None if a==b==-math.inf else a-b,
                       **{key:row[key] for key in strata}})
    result=paired_extended(paired,seed=seed,draws=draws)
    result['disposition']=classify(result,threshold=threshold)
    grouped={}
    for key in strata:
        values=defaultdict(list)
        for row in paired:
            values[str(row[key])].append(row)
        grouped[key]={name:paired_extended(records,seed=seed,draws=draws) for name,records in sorted(values.items())}
    return {'left':left,'right':right,'practical_threshold_nats':threshold,'overall':result,'strata':grouped,
            'target_counts':dict(Counter(r['truth'].split(':')[0] for r in rows)),
            'input_sha256':digest(rows),'selection_sha256':digest(selection) if selection else None,
            'complete_independent_units':len(rows),'excluded_targets':0,
            'meaning':'prospective log-score contrast; neither raw surprise nor unique historical identification'}
