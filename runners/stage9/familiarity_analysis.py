"""Balanced recognition and prospective profiles; makers, not cells, are units.

DESIGN CHECK: T02/X02/X06/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: constant familiar answers cannot beat balanced identity truth; equal routes
give zero. ALTERNATIVE: recognition and prospective gains can dissociate across
expectedness. Balance same/different inside every recognition unit, and average
each unit's log scores before selecting rivals or bootstrapping. All assigned
units and invalid/nonfinite components are retained. No discovery selection,
per-unit best rival, reserve access, or automatic scientific promotion.
"""
import argparse
import math
import time
from pathlib import Path

from .artifact_analysis import check_units,load_complete
from .common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from .familiarity_jobs import QUESTIONS
from .queue import inside,writer
from .revision_predictions import sources,reentry,finish
from .scoring import classify,log_score,paired_extended,score_json
from .training_jobs import cell_identity


def cells(row, questions):
    if set(row['questions'])!=set(QUESTIONS):raise ValueError('incomplete familiarity question grid')
    if not questions or len(set(questions))!=len(questions) or set(questions)-set(QUESTIONS):
        raise ValueError('explicit unique familiarity questions required')
    result=[row['questions'][q] for q in questions]
    if len({c['kind'] for c in result})!=1 or len({c['view'] for c in result})!=1:
        raise ValueError('different outcomes or access views cannot be pooled as one score')
    for q,c in zip(questions,result):
        index=int(q.split('|')[0][1:]);expected_view='artifact' if index<4 else 'process_record'
        expected_condition=('familiar' if index%4<2 else 'unfamiliar')+'|'+('expected' if index%2==0 else 'unexpected')
        if c['kind']!=q.split('|')[1] or c['view']!=expected_view or c['condition']!=expected_condition:
            raise ValueError('question metadata differs from its declared crossing')
    if result[0]['kind']=='recognition':
        pairs={}
        for c in result:
            familiar,stratum=c['condition'].split('|')
            truth='same' if familiar=='familiar' else 'different'
            if c['truth']!=truth or set(c['support'])!={'same','different'}:
                raise ValueError('recognition truth or complete binary support changed')
            pairs.setdefault(stratum,[]).append(truth)
        if any(sorted(v)!=['different','same'] for v in pairs.values()):
            raise ValueError('recognition requires balanced same/different truth within every source unit')
    return result


def scores(row, questions, model):
    selected=cells(row,questions)
    if any(c['validity'].get(model) is not True for c in selected):return None
    result=[]
    for c in selected:
        p=c['predictions'][model]
        if set(p)!=set(c['support']):raise ValueError('familiarity forecast has incomplete support')
        result.append(log_score(p,c['truth']))
    return result


def select(rows,expected,groups,package):
    check_units(rows,expected)
    if not groups:raise ValueError('explicit development groups required')
    output={}
    for name,group in groups.items():
        if set(group)!={'questions','eligible'} or not group['eligible'] or len(set(group['eligible']))!=len(group['eligible']):
            raise ValueError('incomplete development rival group')
        values={m:[] for m in group['eligible']};invalid=set()
        for row in rows:
            for model in values:
                observed=scores(row,group['questions'],model)
                if observed is None:invalid.add(row['unit'])
                else:values[model].append(math.fsum(observed)/len(observed))
        if invalid:
            output[name]={'accepted':False,'invalid_units':sorted(invalid),'assigned_units':len(expected)}
            continue
        means={m:math.fsum(v)/len(v) for m,v in values.items()}
        finite=[m for m in means if math.isfinite(means[m])]
        if not finite:raise ValueError('all development rivals assign zero to an actual target')
        output[name]={'accepted':True,'selected':sorted(finite,key=lambda m:(-means[m],m))[0],
            'eligible':group['eligible'],'questions':group['questions'],'scores':score_json(means),
            'units':sorted(expected),'role':'development','package_sha256':package,
            'rule':'highest equal-maker mean of within-maker question log scores; lexical exact ties'}
    return output


def evaluate(rows,expected,contrast,selection,package,role,draws=4000):
    check_units(rows,expected)
    if (set(contrast)!={'id','card','left','right','threshold','strata','required_controls','meaning'}
            or contrast['card']!='T02' or contrast['threshold']!=.05 or not contrast['meaning']
            or role not in ('pilot','discovery') or not contrast['required_controls']):
        raise ValueError('incomplete declared familiarity contrast')
    sides=[]
    for side in ('left','right'):
        item=dict(contrast[side])
        if set(item)=={'questions','selected_for'}:
            s=selection[item['selected_for']]
            if not s['accepted']:return {'id':contrast['id'],'disposition':'IMPLEMENTATION INVALID','assigned_units':len(expected),'scored_units':0}
            if (s['role']!='development' or s['package_sha256']!=package or set(expected)&set(s['units'])
                    or not set(item['questions'])<=set(s['questions'])):
                raise ValueError('development selection mismatch or reused source unit')
            item['model']=s['selected'];del item['selected_for']
        elif set(item)!={'questions','model'}:raise ValueError('explicit question set and model required')
        sides.append(item)
    projected,invalid=[],[]
    for row in rows:
        left,right=(scores(row,s['questions'],s['model']) for s in sides)
        if left is None or right is None:invalid.append(row['unit']);continue
        if len(left)!=len(right):raise ValueError('paired sides use different opportunity counts')
        a,b=(cells(row,s['questions'])[0] for s in sides)
        if a['kind']!=b['kind'] or a['view']!=b['view']:
            raise ValueError('contrast pools different target kinds or views')
        # Log scores are nonpositive, so each within-unit mean is well defined
        # on the extended reals. Preserve the direction of a one-sided zero;
        # only subtracting two negative infinities is undefined.
        left_mean,right_mean=math.fsum(left)/len(left),math.fsum(right)/len(right)
        difference=None if left_mean==right_mean==-math.inf else left_mean-right_mean
        projected.append({'unit':row['unit'],'difference':difference,**{k:row[k] for k in contrast['strata']}})
    if invalid:return {'id':contrast['id'],'disposition':'IMPLEMENTATION INVALID','assigned_units':len(expected),
                       'scored_units':0,'excluded_units':0,'invalid_units':invalid}
    summary=paired_extended(projected,draws=draws,seed=9011)
    by={k:{v:paired_extended([r for r in projected if r[k]==v],draws=draws,seed=9011)
           for v in sorted({r[k] for r in projected})} for k in contrast['strata']}
    return {'id':contrast['id'],'card':'T02','overall':summary,'strata':by,
        'disposition':classify(summary,threshold=.05,descriptive=role=='pilot'),'assigned_units':len(expected),
        'scored_units':len(expected),'excluded_units':0,'left':sides[0],'right':sides[1],
        'required_controls':contrast['required_controls'],'meaning':contrast['meaning'],'promotion_eligible':False,
        'input_sha256':digest(score_json(projected))}


def descriptions(rows,expected,draws=4000):
    """Separate conditional recognition/surprise summaries, never an aggregate."""
    check_units(rows,expected);result={}
    for index in range(8):
        q='q'+str(index);values={k:[] for k in ('probability_same','raw_surprise')};invalid=[]
        for row in rows:
            c=row['questions'][q+'|recognition'];m=row['metrics'][q]
            if not m['valid'] or c['validity'].get('inferred') is not True:
                invalid.append(row['unit']);continue
            for key,value in (('probability_same',c['predictions']['inferred']['same']),
                              ('raw_surprise',m['values']['raw_observation_surprise_nats'])):
                values[key].append({'unit':row['unit'],'difference':value if math.isfinite(value) else None})
        result[q]={'view':rows[0]['questions'][q+'|recognition']['view'],
            'condition':rows[0]['questions'][q+'|recognition']['condition'],'assigned_units':len(expected),
            'valid':not invalid,'invalid_units':invalid,
            'means':{k:paired_extended(v,draws=draws,seed=9011) for k,v in values.items()} if not invalid else {},
            'scope':'conditional diagnostic summaries; not a prospective gain or natural-frequency calibration'}
    return result


def run(directory,predictions,plan_path,operation,role,selection_path=None):
    start,cpu=time.monotonic(),time.process_time()
    directory,predictions,plan_path=map(inside,(directory,predictions,plan_path))
    namespace=ROOT/'private'/('familiarity-analysis-pilots' if role=='pilot' else 'scientific-familiarity-analysis')
    if (not directory.is_relative_to(namespace) or role not in ('pilot','development','discovery')
            or operation not in ('select','evaluate') or operation=='select' and role=='discovery'
            or operation=='evaluate' and role=='development'):
        raise ValueError('undeclared familiarity analysis scope')
    rows,expected,identity,done=load_complete(predictions,role)
    if identity['operation']!='familiarity-predictions-v1':raise ValueError('wrong familiarity prediction consumer')
    package=identity['model_completion_sha256'];plan=read(plan_path)
    if (set(plan)!={'operation','role','groups','contrasts','package_sha256'} or plan['role']!=role
            or plan['operation']!=operation or plan['package_sha256']!=package):
        raise ValueError('analysis plan differs from actual role, operation or fitted package')
    selection=None;selection_sha=None
    if selection_path is not None:
        selection_path=inside(selection_path);selected=read(selection_path);sd=read(selection_path.parent/'COMPLETE.json')
        if (selected['role']!=('pilot' if role=='pilot' else 'development') or selected['package_sha256']!=package
                or sd.get('execution_complete') is not True or sd['operation']!='select'
                or closure([REPO/p for p in sd['outputs']['files']])!=sd['outputs']
                or selected['prediction_source_sha256']!=identity['source']['sha256']):
            raise ValueError('development selection source or completion changed')
        selection=selected['selections'];selection_sha=file_hash(selection_path)
    own={'cell_identity':cell_identity(),'source':sources(),'operation':operation,'role':role,
        'scope':'pilot' if role=='pilot' else 'scientific','prediction_completion_sha256':file_hash(predictions/'COMPLETE.json'),
        'plan_sha256':file_hash(plan_path),'selection_sha256':selection_sha}
    with writer(directory):
        Units(directory,own);previous=reentry(directory,own)
        if previous is not None:return previous
        if operation=='select':
            if plan['contrasts'] or {q for g in plan['groups'].values() for q in g['questions']}!=set(QUESTIONS):
                raise ValueError('complete development question coverage required')
            result={'role':role,'package_sha256':package,'prediction_source_sha256':identity['source']['sha256'],
                    'selections':select(rows,expected,plan['groups'],package),'units':expected}
            output='SELECTION.json'
        else:
            contrasts=plan['contrasts']
            if (plan['groups'] or not contrasts or len({c['id'] for c in contrasts})!=len(contrasts)
                    or {q for c in contrasts for q in c['left']['questions']}!=set(QUESTIONS)):
                raise ValueError('complete manually enumerated familiarity profile required')
            result={'role':role,'package_sha256':package,
                'contrasts':[evaluate(rows,expected,c,selection,package,role) for c in contrasts],
                'conditional_descriptions':descriptions(rows,expected),'scientific_admission':False}
            output='CONTRASTS.json'
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
