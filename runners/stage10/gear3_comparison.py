"""Declared Round 1 contrasts, without relaxing ordinary paired evidence checks.

DESIGN CHECK: LESSONS3-5; Round 1 sections3-4. NULL: identical forecasts
produce zero benefit and interaction, invariant to order and writer replication.
ALTERNATIVE: better true-outcome support improves proper scores. Invalids retain
worst system loss; zero support retains infinite log loss. Only the prescribed
history delta is admitted; common donor/prompt components bind both sides.
"""
from copy import deepcopy
from . import comparison
from .contracts import digest


def indexed(cell):
    rows={r['task_id']:r for r in cell['rows']}
    if not rows or len(rows)!=len(cell['rows']) or len(rows)!=cell['summary']['attempted']:
        raise ValueError('empty, duplicated or incomplete contrast')
    return rows


def interaction(cells):
    """[L27 R2 - L27 R3] - [L9 R2 - L9 R3], source balanced."""
    if set(cells)!={'9b-R2','9b-R3','27b-R2','27b-R3'}:
        raise ValueError('all four predeclared cells required')
    rows={k:indexed(v) for k,v in cells.items()}
    reference=rows['9b-R2']
    if any(set(r)!=set(reference) for r in rows.values()):
        raise ValueError('interaction cells have different rosters')
    for cell in cells.values():
        comparison.paired(cells['9b-R2'],cell)
    contrasts=[]
    for key,x in reference.items():
        r={k:v[key] for k,v in rows.items()}
        benefit=lambda model:r[model+'-R2']['brier_system']-r[model+'-R3']['brier_system']
        log=[r[k]['log_loss'] for k in ('27b-R2','27b-R3','9b-R2','9b-R3')]
        contrasts.append({'group':x['group'],'component':x['component'],
            'interaction':benefit('27b')-benefit('9b'),
            'finite_log_interaction':log[0]-log[1]-log[2]+log[3] if all(type(v) in (int,float) for v in log) else None})
    return {'definition':'[L27 R2 - L27 R3] - [L9 R2 - L9 R3]; positive favors larger-reader reconstruction benefit',
            'brier':comparison.uncertainty(contrasts,'interaction'),
            'finite_log':comparison.uncertainty(contrasts,'finite_log_interaction'),
            'within_model':{m:comparison.paired(cells[m+'-R3'],cells[m+'-R2']) for m in ('9b','27b')},
            'direct_model_package_difference':comparison.paired(cells['27b-R2'],cells['9b-R2']),
            'scope':'descriptive package comparison; parameter count is not isolated; no human-mechanism or confirmatory claim'}


def history_contrast(correct,intervened,*,condition,donors):
    """Positive means correct history helps; source events/options/truth stay fixed.

    donors is the outcome-blind PLAN projection, keyed by task ID, containing the
    actual full pre-cutoff donor record digest/history, group and dependencies.
    No evaluator field enters this projection. Both sides use its common graph.
    """
    if condition not in {'other-writer','artifact-only'}:
        raise ValueError('undeclared history intervention')
    left,right=indexed(correct),indexed(intervened)
    expected_dimensions=list(correct['summary']['dimensions'])
    if condition=='artifact-only':expected_dimensions[1]='artifact'
    if intervened['summary']['dimensions']!=expected_dimensions or correct['summary']['population']!=intervened['summary']['population']:
        raise ValueError('history comparison changed family, exposure, role or population')
    if set(left)!=set(right) or set(donors)!=set(left):
        raise ValueError('history intervention/donor roster differs')
    a,b=deepcopy(correct),deepcopy(intervened)
    common=[];bindings=[]
    for key in sorted(left):
        x,y=left[key],right[key];donor=donors[key]
        if any(x[k]!=y[k] for k in ('truth','group','event')):
            raise ValueError('history intervention changed target or source identity')
        if set(donor)!={'group','dependencies','public','source_record_sha256'} or donor['group']==x['group']:
            raise ValueError('actual other-writer donor required')
        original=x['public'];altered=y['public'];expected=deepcopy(original)
        if original['evidence_view']!='process-record': raise ValueError('original history view required')
        history=original['evidence']['earlier_handling']
        donor_history=donor['public']['evidence']['earlier_handling']
        if donor['public']['evidence_view']!='process-record' or not history or len(history)!=len(donor_history):
            raise ValueError('unaltered equal-length predecision donor required')
        if len(donor['source_record_sha256'])!=64: raise ValueError('missing donor source binding')
        if condition=='other-writer':expected['evidence']['earlier_handling']=donor_history
        else:
            expected['evidence'].pop('earlier_handling');expected['evidence_view']='artifact'
        if expected!=altered:raise ValueError('history intervention exceeds declared evidence delta')
        dependencies=sorted(set(x['dependencies']+y['dependencies']+donor['dependencies']+
                                ['writer:'+x['group'],'writer:'+donor['group']]))
        common.append({'task_id':key,'group':x['group'],'dependencies':dependencies})
        bindings.append({'task_id':key,'correct_public':digest(original),'intervened_public':digest(altered),
                         'donor_record':donor['source_record_sha256'],'delta':condition})
    graph=comparison.components(common);metadata={r['task_id']:r for r in common}
    # Scoped projection AFTER validating and retaining the exact changed fields.
    # Originals remain untouched. The ordinary scorer still rejects these inputs.
    for cell in (a,b):
        cell['summary']['population']=a['summary']['population']
        cell['summary']['dimensions']=a['summary']['dimensions']
        for row in cell['rows']:
            key=row['task_id'];row['public']=left[key]['public']
            row['dependencies']=metadata[key]['dependencies'];row['component']=graph[row['group']]
    result=comparison.paired(a,b)
    result.update(condition=condition,validated_delta_bindings=bindings,common_components=graph,
                  scope='complete fixed-R0 or fixed-R3 contrast; donor-linked descriptive uncertainty')
    return result
