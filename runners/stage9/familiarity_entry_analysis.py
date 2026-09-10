"""Paired future quality and observation cost for the complete entry cross.

DESIGN CHECK: T02/S02/X02/X05/X06/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: identical routes have zero paired gain; omitted conditions and invalid calls
cannot manufacture a complete grid. ALTERNATIVE: an entry route can improve future
quality or save purchases; these quantities are reported separately. Select each
cheap rival once on development and retain every independent maker at evaluation.
Average conditions within makers before bootstrap; never count them as independent.
Each condition carries its own actual future, matched across familiarity within
expectedness. Zero forecast probability stays an infinite loss, not an exclusion.
Recognition diagnostics here do not replace the separate controlled T02 analysis.
"""
import argparse
import math
import time
from pathlib import Path

from .artifact_analysis import check_units,load_complete
from .common import ROOT,Units,closure,digest,file_hash,freeze,read,REPO
from .familiarity_cases import CONDITIONS
from .selection_reader import STRATEGIES
from .selection_jobs import STOP_COSTS
from .queue import inside,writer
from .revision_predictions import sources,reentry,finish
from .scoring import classify,log_score,paired_extended,score_json
from .training_jobs import cell_identity

QUERIES=tuple(v+'|'+s+'|'+str(b) for v in ('artifact','process_record') for s in STRATEGIES for b in (0,1,3)) + tuple(
    v+'|future-stop-'+str(c)+'|stopped' for v in ('artifact','process_record') for c in STOP_COSTS)


def cells(row,conditions,query):
    if (set(row['conditions'])!=set(CONDITIONS) or query not in QUERIES or not conditions
            or len(set(conditions))!=len(conditions) or set(conditions)-set(CONDITIONS)):
        raise ValueError('incomplete or undeclared entry condition/query grid')
    for condition,record in row['conditions'].items():
        if record['unit']!=row['unit'] or set(record['rows'])!=set(QUERIES):
            raise ValueError('entry source unit or complete query grid changed')
        for name,cell in record['rows'].items():
            view,path,budget=name.split('|')
            if (cell['view']!=view or cell['path']!=path or str(cell['requested_budget'])!=budget
                    or cell['preview_cost']!=3 or type(cell['purchase_cost']) is not int
                    or not 0<=cell['purchase_cost']<=3):
                raise ValueError('entry query metadata or observation cost changed')
    for stratum in ('expected','unexpected'):
        if row['conditions']['familiar|'+stratum]['truth']!=row['conditions']['unfamiliar|'+stratum]['truth']:
            raise ValueError('matched familiarity conditions have different actual futures')
    return [(row['conditions'][c]['rows'][query],row['conditions'][c]['truth']) for c in conditions]


def measurements(row,side):
    selected=cells(row,side['conditions'],side['query']);model=side['model']
    if any(c['validity'].get(model) is not True for c,_ in selected):return None
    values=[]
    for c,truth in selected:
        p=c['predictions'][model]
        if set(p)!=set(c['support']):raise ValueError('entry forecast support changed')
        values.append(log_score(p,truth))
    return {'quality':math.fsum(values)/len(values),
            'purchases':math.fsum(c['purchase_cost'] for c,_ in selected)/len(selected)}


def select(rows,expected,groups,package):
    check_units(rows,expected)
    if not groups:raise ValueError('explicit entry development groups required')
    results={}
    for name,g in groups.items():
        if set(g)!={'conditions','query','eligible'} or not g['eligible'] or len(set(g['eligible']))!=len(g['eligible']):
            raise ValueError('invalid entry development rival group')
        values={m:[] for m in g['eligible']};invalid=set()
        for row in rows:
            for model in values:
                r=measurements(row,{'conditions':g['conditions'],'query':g['query'],'model':model})
                if r is None:invalid.add(row['unit'])
                else:values[model].append(r['quality'])
        if invalid:
            results[name]={'accepted':False,'invalid_units':sorted(invalid),'assigned_units':len(expected)};continue
        means={m:math.fsum(x)/len(x) for m,x in values.items()}
        finite=[m for m in means if math.isfinite(means[m])]
        if not finite:raise ValueError('all entry development rivals assign zero to a true target')
        results[name]={'accepted':True,'selected':min(finite,key=lambda m:(-means[m],m)),
            'query':g['query'],'conditions':g['conditions'],'eligible':g['eligible'],'scores':score_json(means),
            'units':sorted(expected),'role':'development','package_sha256':package}
    return results


def evaluate(rows,expected,contrast,selection,package,role,draws=4000):
    check_units(rows,expected)
    if (set(contrast)!={'id','card','left','right','threshold','strata','required_controls','meaning'}
            or contrast['card']!='T02' or contrast['threshold']!=.05 or not contrast['meaning']
            or not contrast['required_controls'] or role not in ('pilot','discovery')):
        raise ValueError('incomplete entry contrast')
    sides=[]
    for side in ('left','right'):
        item=dict(contrast[side])
        if set(item)=={'conditions','query','selected_for'}:
            s=selection[item['selected_for']]
            if not s['accepted']:return {'id':contrast['id'],'disposition':'IMPLEMENTATION INVALID','assigned_units':len(expected),'scored_units':0,'excluded_units':0}
            if (s['role']!='development' or s['package_sha256']!=package or set(expected)&set(s['units'])
                    or item['query']!=s['query'] or not set(item['conditions'])<=set(s['conditions'])):
                raise ValueError('entry development selection mismatch or reused source')
            item['model']=s['selected'];del item['selected_for']
        elif set(item)!={'conditions','query','model'}:raise ValueError('explicit entry side required')
        sides.append(item)
    if (len(sides[0]['conditions'])!=len(sides[1]['conditions'])
            or sides[0]['query'].split('|')[0]!=sides[1]['query'].split('|')[0]):
        raise ValueError('entry sides mix access views or opportunity counts')
    projected,costs,invalid=[],[],[]
    for row in rows:
        left,right=(measurements(row,s) for s in sides)
        if left is None or right is None:invalid.append(row['unit']);continue
        a,b=left['quality'],right['quality'];d=None if a==b==-math.inf else a-b
        projected.append({'unit':row['unit'],'difference':d,**{k:row[k] for k in contrast['strata']}})
        costs.append({'unit':row['unit'],'difference':right['purchases']-left['purchases']})
    if invalid:return {'id':contrast['id'],'disposition':'IMPLEMENTATION INVALID','assigned_units':len(expected),
        'scored_units':0,'excluded_units':0,'invalid_units':invalid}
    quality=paired_extended(projected,draws=draws,seed=9011)
    return {'id':contrast['id'],'card':'T02','overall':quality,
        'strata':{k:{v:paired_extended([r for r in projected if r[k]==v],draws=draws,seed=9011)
                     for v in sorted({r[k] for r in projected})} for k in contrast['strata']},
        'purchase_saving':paired_extended(costs,draws=draws,seed=9011),
        'cost_meaning':'positive means the left route buys fewer observations; three common previews per condition',
        'disposition':classify(quality,threshold=.05,descriptive=role=='pilot'),'assigned_units':len(expected),
        'scored_units':len(expected),'excluded_units':0,'left':sides[0],'right':sides[1],
        'required_controls':contrast['required_controls'],'meaning':contrast['meaning'],'promotion_eligible':False,
        'input_sha256':digest(score_json({'quality':projected,'costs':costs}))}


def run(directory,predictions,plan_path,operation,role,selection_path=None):
    start,cpu=time.monotonic(),time.process_time()
    directory,predictions,plan_path=map(inside,(directory,predictions,plan_path))
    namespace=ROOT/'private'/('familiarity-entry-analysis-pilots' if role=='pilot' else 'scientific-familiarity-entry-analysis')
    if (not directory.is_relative_to(namespace) or role not in ('pilot','development','discovery')
            or operation not in ('select','evaluate') or operation=='select' and role=='discovery'
            or operation=='evaluate' and role=='development'):
        raise ValueError('undeclared entry analysis scope')
    rows,expected,identity,done=load_complete(predictions,role)
    if identity['operation']!='familiarity-entry-predictions-v1':raise ValueError('wrong entry prediction consumer')
    package=identity['model_completion_sha256'];plan=read(plan_path)
    if (set(plan)!={'operation','role','groups','contrasts','package_sha256'} or plan['role']!=role
            or plan['operation']!=operation or plan['package_sha256']!=package):
        raise ValueError('entry analysis plan differs from role or fitted package')
    selection=None;selection_sha=None
    if selection_path is not None:
        selection_path=inside(selection_path);selected=read(selection_path);sd=read(selection_path.parent/'COMPLETE.json')
        if (selected['role']!=('pilot' if role=='pilot' else 'development') or selected['package_sha256']!=package
                or sd.get('execution_complete') is not True or sd['operation']!='select'
                or closure([REPO/p for p in sd['outputs']['files']])!=sd['outputs']
                or selected['prediction_source_sha256']!=identity['source']['sha256']):
            raise ValueError('entry development selection source or completion changed')
        selection=selected['selections'];selection_sha=file_hash(selection_path)
    own={'cell_identity':cell_identity(),'source':sources(),'operation':operation,'role':role,
        'scope':'pilot' if role=='pilot' else 'scientific','prediction_completion_sha256':file_hash(predictions/'COMPLETE.json'),
        'plan_sha256':file_hash(plan_path),'selection_sha256':selection_sha}
    with writer(directory):
        Units(directory,own);previous=reentry(directory,own)
        if previous is not None:return previous
        if operation=='select':
            covered={(c,g['query']) for g in plan['groups'].values() for c in g['conditions']}
            if plan['contrasts'] or covered!={(c,q) for c in CONDITIONS for q in QUERIES}:
                raise ValueError('complete entry development coverage required')
            result={'role':role,'package_sha256':package,'prediction_source_sha256':identity['source']['sha256'],
                'selections':select(rows,expected,plan['groups'],package),'units':expected};output='SELECTION.json'
        else:
            contrasts=plan['contrasts'];covered={(c,x['left']['query']) for x in contrasts for c in x['left']['conditions']}
            if (plan['groups'] or not contrasts or len({x['id'] for x in contrasts})!=len(contrasts)
                    or covered!={(c,q) for c in CONDITIONS for q in QUERIES}):
                raise ValueError('complete manually enumerated entry profiles required')
            result={'role':role,'package_sha256':package,
                'contrasts':[evaluate(rows,expected,c,selection,package,role) for c in contrasts],
                'scientific_admission':False};output='CONTRASTS.json'
        freeze(directory/output,score_json(result))
        return finish(directory,own,start,cpu,[output],role=role,operation=operation,
                      assigned_units=len(expected),scientific_admission=False)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('root','predictions','plan'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--operation',choices=('select','evaluate'),required=True)
    p.add_argument('--role',choices=('pilot','development','discovery'),required=True)
    p.add_argument('--selection',type=Path)
    a=p.parse_args();run(a.root,a.predictions,a.plan,a.operation,a.role,a.selection)
