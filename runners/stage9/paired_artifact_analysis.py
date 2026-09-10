"""Paired differences of prospective gains across two complete interventions.

DESIGN CHECK: T03/T04/X06/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: identical within-condition gains give zero even when absolute performance
differs. ALTERNATIVE: one intervention changes prospective gain more than the other.
Unmatched units, evidence, support, package or invalid required forecasts refuse.
Each condition uses its own actual target; no target is borrowed across futures.
Nonfinite gain interactions retain all assignments and receive no finite estimate.
Whole-cell inputs only; no reserve, selection, scientific promotion or new contrasts.
"""
import argparse
import math
import time
from pathlib import Path
from .artifact_analysis import load_complete,check_units
from .common import REPO,ROOT,digest,file_hash,freeze,read
from .queue import inside,writer
from .revision_predictions import sources,reentry,finish
from .training_jobs import cell_identity
from .scoring import log_score,paired_interval,classify,score_json


def evaluate(left,right,expected,contrast,*,role,draws=4000):
    fields={'id','card','left','right','threshold','strata','required_controls','meaning'}
    if (set(contrast)!=fields or role not in ('pilot','discovery') or contrast['threshold']!=.05
            or not contrast['meaning'] or not contrast['required_controls']):
        raise ValueError('incomplete paired-intervention contrast or scope')
    check_units(left,expected);check_units(right,expected)
    for side in ('left','right'):
        if set(contrast[side])!={'query','model','baseline'}:
            raise ValueError('paired intervention requires explicit query, model and baseline')
    right={r['unit']:r for r in right};projected=[];invalid=[]
    for a in sorted(left,key=lambda r:r['unit']):
        b=right[a['unit']];cells=[row['rows'][contrast[side]['query']] for row,side in ((a,'left'),(b,'right'))]
        if (cells[0]['evidence_sha256']!=cells[1]['evidence_sha256'] or set(cells[0]['support'])!=set(cells[1]['support'])
                or any(a[k]!=b[k] for k in contrast['strata'])):
            raise ValueError('paired interventions differ in original evidence, support or grouping')
        values=[];valid=True
        for row,cell,side in zip((a,b),cells,('left','right')):
            scores=[]
            for model in (contrast[side]['model'],contrast[side]['baseline']):
                if cell['validity'].get(model) is not True:
                    valid=False;continue
                p=cell['predictions'][model]
                if set(p)!=set(cell['support']):raise ValueError('paired prediction support changed')
                scores.append(log_score(p,row['truth']))
            values.append(scores)
        if not valid:
            invalid.append(a['unit']);continue
        finite=all(math.isfinite(v) for scores in values for v in scores)
        projected.append({'unit':a['unit'],'difference':(values[0][0]-values[0][1])-(values[1][0]-values[1][1]) if finite else None,
                          'raw_log_scores':values,**{k:a[k] for k in contrast['strata']}})
    if invalid:
        return {'id':contrast['id'],'disposition':'IMPLEMENTATION INVALID','invalid_units':invalid,
                'assigned_units':len(expected),'scored_units':0,'excluded_units':0}
    nonfinite=[r['unit'] for r in projected if r['difference'] is None]
    if nonfinite:
        return {'id':contrast['id'],'card':contrast['card'],'disposition':'DESCRIPTIVE','assigned_units':len(expected),
                'scored_units':len(expected),'excluded_units':0,'finite_estimate':False,'nonfinite_units':nonfinite,
                'unit_scores':score_json(projected),'reason':'nonfinite constituent log scores; no finite-only interaction estimate',
                'promotion_eligible':False}
    summary=paired_interval(projected,draws=draws,seed=9011)
    strata={key:{value:paired_interval([r for r in projected if r[key]==value],draws=draws,seed=9011)
                 for value in sorted({r[key] for r in projected})} for key in contrast['strata']}
    return {'id':contrast['id'],'card':contrast['card'],'overall':summary,'strata':strata,
            'disposition':classify(summary,threshold=.05,descriptive=role=='pilot'),'assigned_units':len(expected),
            'scored_units':len(expected),'excluded_units':0,'finite_estimate':True,'promotion_eligible':False,
            'required_controls':contrast['required_controls'],'meaning':contrast['meaning'],'input_sha256':digest(projected)}


def run(directory,left,right,plan_path,role):
    start,cpu=time.monotonic(),time.process_time()
    if role not in ('pilot','discovery'):raise ValueError('no reserve or development interaction analysis')
    directory,left,right,plan_path=map(inside,(directory,left,right,plan_path))
    namespace=ROOT/'private'/('paired-artifact-pilots' if role=='pilot' else 'scientific-paired-artifact-analysis')
    if not directory.is_relative_to(namespace):raise ValueError('paired analysis outside its role namespace')
    a,expected,ai,_=load_complete(left,role);b,other,bi,_=load_complete(right,role)
    if (set(expected)!=set(other) or ai['model_completion_sha256']!=bi['model_completion_sha256']
            or ai['source']!=bi['source']):
        raise ValueError('paired intervention package, source or independent-unit mismatch')
    plan=read(plan_path)
    if (set(plan)!={'role','package_sha256','contrasts'} or plan['role']!=role
            or plan['package_sha256']!=ai['model_completion_sha256'] or not plan['contrasts']
            or len({c['id'] for c in plan['contrasts']})!=len(plan['contrasts'])):
        raise ValueError('paired analysis differs from explicit complete plan')
    own={'operation':'paired-artifact-analysis-v1','cell_identity':cell_identity(),'scope':'pilot' if role=='pilot' else 'scientific',
         'role':role,'source':sources(),'left_complete_sha256':file_hash(left/'COMPLETE.json'),
         'right_complete_sha256':file_hash(right/'COMPLETE.json'),'plan_sha256':file_hash(plan_path)}
    with writer(directory):
        freeze(directory/'IDENTITY.json',own);prior=reentry(directory,own)
        if prior is not None:return prior
        result={'role':role,'package_sha256':plan['package_sha256'],
                'contrasts':[evaluate(a,b,expected,c,role=role) for c in plan['contrasts']]}
        freeze(directory/'CONTRASTS.json',score_json(result))
        return finish(directory,own,start,cpu,['CONTRASTS.json'],role=role,assigned_units=len(expected),
                      scientific_admission=False,disposition='DESCRIPTIVE')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('root','left','right','plan','role'):p.add_argument('--'+k,required=True)
    a=p.parse_args();run(Path(a.root),Path(a.left),Path(a.right),Path(a.plan),a.role)
