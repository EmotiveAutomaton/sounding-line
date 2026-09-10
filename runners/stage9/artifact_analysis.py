"""Complete-grid development selection and explicitly listed prospective contrasts.

DESIGN CHECK: M01/M04/C08/X06/X11; LESSONS 3--5, CONTROLS 2/6.
NULL: equal forecasts give zero, and a stronger cheap rival defeats the richer
model. ALTERNATIVE: a complete held-out paired advantage survives its declared
controls. Invalid required components retain all units but yield no score.
No per-target best comparator, no discovery selection, no reserve access here.
"""
import argparse
from datetime import datetime,timezone
import math
import os
from pathlib import Path
import time

from .artifact_comparisons import contrast_rows
from .common import REPO,closure,digest,file_hash,freeze,read
from .comparison_analysis import complete_rows,select_rival
from .queue import inside,verify_sources,writer
from .scoring import classify,log_score,paired_extended,score_json


def load_complete(directory,role):
    directory=inside(directory);done=read(directory/'COMPLETE.json');identity=read(directory/'IDENTITY.json')
    if (done.get('execution_complete') is not True or done['role']!=role or
        done['identity_sha256']!=digest(identity) or done['assigned_units']!=done['completed_units']):
        raise ValueError('prediction consumer is incomplete or belongs to another role')
    if closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
        raise ValueError('prediction data, capsule or unit closure changed')
    rows=read(directory/'PREDICTIONS.json')
    expected=identity['selected_units']
    if len(rows)!=len(expected) or {r['unit'] for r in rows}!=set(expected):
        raise ValueError('prediction output omits or duplicates an assigned unit')
    return rows,expected,identity,done


def check_units(rows,expected):
    if (not expected or len(expected)!=len(set(expected)) or len(rows)!=len(expected) or
        {r['unit'] for r in rows}!=set(expected)):
        raise ValueError('incomplete or duplicated independent unit allocation')


def select(rows,expected,eligible,package):
    """One selection per explicit view/query and declared rival set."""
    check_units(rows,expected)
    if not eligible:raise ValueError('no explicitly eligible rival queries')
    output={}
    for query,models in eligible.items():
        projected=contrast_rows(rows,query,models)
        invalid=[r['unit'] for r in projected if not r['valid']]
        if invalid:
            output[query]={'accepted':False,'invalid_units':invalid,'assigned_units':len(expected),
                           'disposition':'IMPLEMENTATION INVALID','reason':'required development rival invalid'}
        else:
            output[query]={'accepted':True,'selection':select_rival(projected,expected,models,
                                role='development',package_sha256=package)}
    return output


def evaluate(rows,expected,contrast,*,selection,package,role='discovery',draws=4000):
    """The caller enumerates comparisons; this function never invents a card."""
    check_units(rows,expected)
    if set(contrast)!={'id','card','left','right','threshold','strata','required_controls','meaning'}:
        raise ValueError('incomplete or undeclared contrast fields')
    if role not in ('discovery','pilot'):raise ValueError('confirmation uses its frozen separate handler')
    if not contrast['meaning'] or contrast['threshold']!=.05:raise ValueError('frozen prospective contrast meaning and threshold required')
    left,right=dict(contrast['left']),dict(contrast['right'])
    for side in (left,right):
        if set(side)=={'query','selected_for'}:
            item=selection[side['selected_for']]
            if not item['accepted']:
                return {'id':contrast['id'],'disposition':'IMPLEMENTATION INVALID','reason':'required development selection invalid',
                        'assigned_units':len(expected),'scored_units':0}
            receipt=item['selection']
            if (receipt['package_sha256']!=package or receipt['role']!='development' or
                set(expected)&set(receipt['units'])):
                raise ValueError('development selection mismatch or unit reuse')
            side['model']=receipt['selected'];del side['selected_for']
        elif set(side)!={'query','model'}:raise ValueError('explicit query and model or development selection required')
    projected=[]
    for row in rows:
        a,b=row['rows'][left['query']],row['rows'][right['query']]
        valid=a['validity'].get(left['model']) is True and b['validity'].get(right['model']) is True
        projected.append({'unit':row['unit'],'truth':row['truth'],'valid':valid,
            'predictions':({'left':a['predictions'][left['model']],'right':b['predictions'][right['model']]} if valid else {}),
            **{key:row[key] for key in contrast['strata']}})
    invalid=[r['unit'] for r in projected if not r['valid']]
    if invalid:
        return {'id':contrast['id'],'disposition':'IMPLEMENTATION INVALID','reason':'required prediction/precision component invalid',
                'invalid_units':invalid,'assigned_units':len(expected),'scored_units':0,'excluded_units':0}
    complete_rows(projected,expected,['left','right'])
    differences=[]
    for row in projected:
        a=log_score(row['predictions']['left'],row['truth']);b=log_score(row['predictions']['right'],row['truth'])
        differences.append({'unit':row['unit'],'difference':None if a==b==-math.inf else a-b,
                            **{key:row[key] for key in contrast['strata']}})
    summary=paired_extended(differences,draws=draws,seed=9011)
    by_stratum={key:{value:paired_extended([r for r in differences if r[key]==value],draws=draws,seed=9011)
                     for value in sorted({r[key] for r in differences})} for key in contrast['strata']}
    return {'id':contrast['id'],'card':contrast['card'],'left':left,'right':right,'overall':summary,
            'disposition':classify(summary,threshold=.05,descriptive=role=='pilot'),'strata':by_stratum,
            'assigned_units':len(expected),'scored_units':len(expected),'excluded_units':0,
            'required_controls':contrast['required_controls'],'promotion_eligible':False,
            'promotion_reason':'separate card adjudication must verify every required control and capability',
            'meaning':contrast['meaning'],'input_sha256':digest(projected)}


def run(directory,predictions,plan_path,*,operation,role,selection_path=None):
    started,cpu=time.monotonic(),time.process_time()
    if role not in ('pilot','development','discovery'):raise ValueError('no reserve access in this handler')
    if operation=='select' and role not in ('development','pilot'):raise ValueError('discovery cannot select a rival')
    if operation=='evaluate' and role not in ('discovery','pilot'):raise ValueError('development cannot supply a held-out contrast')
    cell=os.environ.get('S9_CELL_IDENTITY')
    if role!='pilot' and (not cell or len(cell)!=64):raise ValueError('scientific analysis requires an identified queue cell')
    directory=inside(directory);predictions=inside(predictions);plan_path=inside(plan_path)
    rows,expected,identity,completion=load_complete(predictions,role)
    package=identity['model_completion_sha256'];plan=read(plan_path)
    if set(plan)!={'operation','role','queries','contrasts','package_sha256'} or plan['operation']!=operation or plan['role']!=role or plan['package_sha256']!=package:
        raise ValueError('analysis plan differs from actual operation/role/package')
    source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
                    REPO/'runners/__init__.py',REPO/'runners/readout_repair.py'])
    selection=None
    if selection_path:
        selection_path=inside(selection_path);selected=read(selection_path)
        if selected['role']!=('pilot' if role=='pilot' else 'development') or selected['package_sha256']!=package:
            raise ValueError('rival selection is from the wrong split or model package')
        selection_done=read(selection_path.parent/'COMPLETE.json')
        if (selection_done['operation']!='select' or selection_done.get('execution_complete') is not True or
            closure([REPO/p for p in selection_done['outputs']['files']])!=selection_done['outputs'] or
            selected['prediction_source_sha256']!=identity['source']['sha256']):
            raise ValueError('selection closure or prediction source differs from the held-out package')
        selection=selected['selections']
    own={'operation':operation,'role':role,'cell_identity':cell,'source':source,
         'prediction_completion_sha256':file_hash(predictions/'COMPLETE.json'),'plan_sha256':file_hash(plan_path),
         'selection_sha256':file_hash(selection_path) if selection_path else None}
    with writer(directory):
        freeze(directory/'IDENTITY.json',own)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(own) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('analysis completion changed')
            return done
        if operation=='select':
            if plan['contrasts']:raise ValueError('selection may not evaluate scientific contrasts')
            result={'role':role,'package_sha256':package,'prediction_source_sha256':identity['source']['sha256'],
                    'selections':select(rows,expected,plan['queries'],package),
                    'units':expected,'scope':'discarded operation rehearsal' if role=='pilot' else 'development-only rival selection'}
            output=directory/'SELECTION.json'
        elif operation=='evaluate':
            if plan['queries'] or not plan['contrasts'] or len({c['id'] for c in plan['contrasts']})!=len(plan['contrasts']):
                raise ValueError('nonempty unique manually enumerated contrast list required')
            result={'role':role,'package_sha256':package,'contrasts':[evaluate(rows,expected,c,selection=selection,package=package,role=role)
                    for c in plan['contrasts']]};output=directory/'CONTRASTS.json'
        else:raise ValueError('unknown explicit analysis operation')
        freeze(output,score_json(result));verify_sources(source)
        done={'at':datetime.now(timezone.utc).isoformat(),'identity_sha256':digest(own),'cell_identity':cell,'source':source,
              'role':role,'execution_complete':True,'operation':operation,'assigned_units':len(expected),
              'outputs':closure([output]),'wall_seconds':time.monotonic()-started,'cpu_seconds':time.process_time()-cpu,
              'gpu_seconds':0,'scientific_promotion':False}
        freeze(directory/'COMPLETE.json',done);return done


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('root','predictions','plan','operation','role'):parser.add_argument('--'+key,required=True)
    parser.add_argument('--selection')
    args=parser.parse_args()
    run(Path(args.root),Path(args.predictions),Path(args.plan),operation=args.operation,role=args.role,
        selection_path=Path(args.selection) if args.selection else None)
    print('Complete-grid analysis produced; card controls and scientific warrant remain separate.',flush=True)


if __name__=='__main__':main()
