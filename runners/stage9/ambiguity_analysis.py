"""Complete ambiguity profiles with independently selected rivals per question.

DESIGN CHECK: M05/X02/X05/X06/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: equal forecasts give zero; cross-target pooling, missing questions, source
reuse or invalid required calls cannot produce a finite valid comparison.
ALTERNATIVE: held-out history calibration and useful future forecasts can differ.
The six histories are alternatives within one world, never independent samples.
No reserve access or automatic scientific promotion; the caller enumerates contrasts.
"""
import argparse
import copy
import time
from pathlib import Path
from .ambiguity_jobs import QUESTIONS
from .artifact_analysis import load_complete,check_units,select,evaluate
from .common import REPO,ROOT,Units,read,freeze,closure,digest,file_hash
from .queue import inside,writer
from .revision_predictions import sources,reentry,finish
from .training_jobs import cell_identity
from .scoring import score_json


def project(rows,question,neural=None):
    if question not in QUESTIONS:raise ValueError('unknown ambiguity question')
    expected=[r['unit'] for r in rows];check_units(rows,expected)
    others={}
    if neural is not None:
        check_units(neural,expected);others={r['unit']:r for r in neural}
    result=[]
    for row in rows:
        if set(row['questions'])!=set(QUESTIONS):raise ValueError('incomplete ambiguity question grid')
        item=copy.deepcopy(row['questions'][question]);truth=item.pop('truth')
        if others:
            other=others[row['unit']]
            if (other['operation']!='ambiguity' or other['case_sha256']!=row['case_sha256']
                    or other['domain']!=row['domain'] or other['role']!=row['role']
                    or other['result']['source_template_sha256']!=row['source_template_sha256']
                    or set(other['result']['questions'])!=set(QUESTIONS)):
                raise ValueError('neural and numerical ambiguity sources differ')
            q=other['result']['questions'][question]
            if q['truth']!=truth or q['support']!=item['support']:raise ValueError('question target or support differs')
            item['validity']['neural']=q['call']['accepted']
            if q['call']['accepted']:item['predictions']['neural']=q['call']['prediction']['probs']
        result.append({'unit':row['unit'],'truth':truth,'rows':{question:item},
                       'domain':row['domain'],'purpose':row['purpose']})
    return result


def profile(rows,expected,contrasts,selection,package,role,neural=None,draws=4000):
    check_units(rows,expected);results=[]
    for contrast in contrasts:
        left,right=contrast['left']['query'],contrast['right']['query']
        if left!=right:raise ValueError('ambiguity comparison cannot pool different question targets')
        results.append(evaluate(project(rows,left,neural),expected,contrast,selection=selection,
                                package=package,role=role,draws=draws))
    return {'contrasts':results,'scope':'each question uses its own historical or future truth; worlds are independent units',
            'scientific_admission':False}


def run(directory,predictions,plan_path,operation,role,selection_path=None,neural_path=None):
    start,cpu=time.monotonic(),time.process_time()
    directory,predictions,plan_path=inside(directory),inside(predictions),inside(plan_path)
    namespace=ROOT/'private'/('ambiguity-analysis-pilots' if role=='pilot' else 'scientific-ambiguity-analysis')
    if (not directory.is_relative_to(namespace) or role not in ('pilot','development','discovery')
            or operation not in ('select','evaluate') or operation=='select' and role=='discovery'
            or operation=='evaluate' and role=='development'):
        raise ValueError('undeclared ambiguity analysis scope')
    rows,expected,identity,done=load_complete(predictions,role)
    if identity['operation']!='ambiguity-predictions-v1':raise ValueError('wrong numerical consumer')
    package=identity['model_completion_sha256'];plan=read(plan_path)
    if (set(plan)!={'operation','role','queries','contrasts','package_sha256'} or plan['role']!=role
            or plan['operation']!=operation or plan['package_sha256']!=package):
        raise ValueError('analysis plan differs from the actual operation, role or fitted package')
    neural=None;neural_sha=None
    if neural_path is not None:
        if operation!='evaluate':raise ValueError('neural results cannot select their own rival')
        neural_path=inside(neural_path);nd=read(neural_path/'COMPLETE.json');ni=read(neural_path/'IDENTITY.json')
        if (nd.get('execution_complete') is not True or ni['operation']!='ambiguity' or ni['role']!=role
                or nd['identity_sha256']!=digest(ni) or nd['cell_identity']!=ni['cell_identity']
                or closure([REPO/p for p in nd['outputs']['files']])!=nd['outputs']
                or ni['cases_complete_sha256']!=identity['case_completion_sha256']
                or set(ni['units'])!=set(expected) or nd['completed_units']!=len(expected)):
            raise ValueError('neural producer incomplete, changed or differently assigned')
        store=Units(neural_path,ni)
        neural=[store.get(unit) for unit in ni['units']];neural_sha=file_hash(neural_path/'COMPLETE.json')
        if any(row is None for row in neural):raise ValueError('neural producer omits a committed unit')
    selection=None;selection_sha=None
    if selection_path is not None:
        selection_path=inside(selection_path);selected=read(selection_path);sd=read(selection_path.parent/'COMPLETE.json')
        if (selected['role']!=('pilot' if role=='pilot' else 'development') or selected['package_sha256']!=package
                or sd.get('execution_complete') is not True or sd['operation']!='select'
                or closure([REPO/p for p in sd['outputs']['files']])!=sd['outputs']
                or selected['prediction_source_sha256']!=identity['source']['sha256']):
            raise ValueError('development selection closure or source differs')
        selection=selected['selections'];selection_sha=file_hash(selection_path)
    own={'cell_identity':cell_identity(),'source':sources(),'operation':operation,'scope':'pilot' if role=='pilot' else 'scientific',
         'role':role,'prediction_completion_sha256':file_hash(predictions/'COMPLETE.json'),
         'plan_sha256':file_hash(plan_path),'neural_completion_sha256':neural_sha,'selection_sha256':selection_sha}
    with writer(directory):
        Units(directory,own);prior=reentry(directory,own)
        if prior is not None:return prior
        if operation=='select':
            if plan['contrasts'] or set(plan['queries'])!=set(QUESTIONS):raise ValueError('complete development question list required')
            selections={q:select(project(rows,q),expected,{q:models},package)[q] for q,models in plan['queries'].items()}
            result={'role':role,'package_sha256':package,'prediction_source_sha256':identity['source']['sha256'],
                    'selections':selections,'units':expected};output='SELECTION.json'
        else:
            contrasts=plan['contrasts']
            if (plan['queries'] or not contrasts or len({c['id'] for c in contrasts})!=len(contrasts)
                    or {c['left']['query'] for c in contrasts}!=set(QUESTIONS)):
                raise ValueError('complete explicitly enumerated ambiguity profile required')
            result={'role':role,'package_sha256':package,**profile(rows,expected,contrasts,selection,package,role,neural)}
            output='CONTRASTS.json'
        freeze(directory/output,score_json(result))
        return finish(directory,own,start,cpu,[output],role=role,operation=operation,assigned_units=len(expected),
                      scientific_admission=False)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('root','predictions','plan'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--operation',choices=('select','evaluate'),required=True)
    p.add_argument('--role',choices=('pilot','development','discovery'),required=True)
    for k in ('selection','neural'):p.add_argument('--'+k,type=Path)
    a=p.parse_args();run(a.root,a.predictions,a.plan,a.operation,a.role,a.selection,a.neural)
