"""Complete prospective repair scoring and independent known-answer calibration.

DESIGN CHECK: C03/X01/X02/X09/X11; LESSONS 3--5, CONTROLS 6.
NULL: fluent stories, blind stopping, invalid probabilities, collateral changes,
selection reuse and partial cohorts cannot admit a local operator. ALTERNATIVE:
the exact executor passes every unchanged engineering threshold on a separate
known-answer battery before an unknown model is scored. Evaluate every attempt,
each domain and each view separately. An exact ceiling that cannot reach .05 nats
over the fixed strongest rival invalidates that capability test; do not lower it.
"""
from collections import Counter
from .common import REPO,digest,distribution,file_hash
from .competence import PACKAGE_FIELDS,repair_gate
from .local_repair import LABELS,consequence,repair_truth,task_case
from .repair_features import predict
from .repair_jobs import public_task
from .scoring import log_score,score_json


def battery_identity(view,domain,local_source):
    if view not in ('artifact','process_record') or domain not in ('essay','workshop_doc'):
        raise ValueError('explicit repair view and domain required')
    return digest({'definition':'s9-symbolic-local-repair-v1','view':view,'domain':domain,'task_source':local_source,
        'query_cut':'preconstruction geometric .35; reached boundary; original initial context',
        'action':'one free zero-clock action; executor supplies outcome only','consequences':list(LABELS)})


def package_identity(package,source,view,domain):
    tokenizer={k:v for k,v in package['base_files'].items() if k.startswith(('tokenizer','vocab','merges','special_tokens'))}
    if not tokenizer:raise ValueError('actual tokenizer file identity missing')
    local=source['files']['runners/stage9/local_repair.py']
    return {'domain':domain,'operation':'local_repair','assistance':'environment-produced outcome; free action; '+view,
        'model':package['model']+'; '+package['precision'],'revision':package['revision'],
        'adapter_sha256':package['adapter_sha256'],'tokenizer_sha256':digest(tokenizer),
        'renderer_sha256':digest({'local_task_source':local,'renderer':package['renderer'],'view':view}),
        'scorer_sha256':package['scorer_sha256'],
        'execution_interface_sha256':digest({'task':local,'execution':source['files']['runners/stage9/rollout_operations.py'],
            'generation':package['generation'],'maximum_new_tokens':package['max_new_tokens']})}


def row_for(case,view,prospective,repair,baseline,*,attempt_id=None):
    task=task_case(case,view)
    if not task['realized']:raise ValueError('declared repair task was not realized')
    truth=consequence(task);distribution(baseline)
    if set(baseline)!=set(LABELS):raise ValueError('strong comparator omitted consequence support')
    actual=repair_truth(task,repair);valid=prospective.get('accepted') is True and repair.get('accepted') is True
    left=None
    if prospective.get('accepted') is True:
        probs=prospective['prediction']['probs'];distribution(probs)
        if set(probs)!=set(LABELS):raise ValueError('prospective reader omitted consequence support')
        left=log_score(probs,truth)
    right=log_score(baseline,truth)
    difference=None if left is None or left==right==float('-inf') else left-right
    return {'attempt_id':attempt_id or case['unit'],'unit':digest(public_task(task)),'source_unit':case['unit'],'fixable':bool(actual['fixable']),
        'legal':bool(actual.get('legal',False)),'goal_improving':bool(actual['goal_improving']),
        'collateral_damage':bool(actual['collateral_damage']),'consequence_difference':difference,
        'valid':valid and actual.get('valid_execution') is True,'truth_verified':True,
        'consequence_truth':truth,'public_task_sha256':digest(public_task(task)),
        'prospective_log_score':left,'comparator_log_score':right,'execution':actual}


def control_answers(task,kind,prior):
    truth=consequence(task)
    if kind=='exact':
        probs={label:float(label==truth) for label in LABELS}
        line='00 '+' '.join(task['requested_mark'].split(':'))+' done'
    elif kind=='blind':probs=prior;line='00 stop'
    elif kind=='story':probs=prior;line='I understand the request and have improved the work while preserving everything else.'
    else:raise ValueError('undeclared known-answer control')
    return {'accepted':True,'prediction':{'probs':probs}},{'accepted':True,'prediction':{'text':line}}


def calibrate(cases,models,selection):
    if len(cases)<192 or len({c['unit'] for c in cases})!=len(cases):
        raise ValueError('complete independent calibration battery required')
    if any(c['role']!='pilot' for c in cases):raise ValueError('instrument calibration must use discarded cases')
    source=file_hash(REPO/'runners/stage9/local_repair.py');groups={};all_rows={}
    for view in ('artifact','process_record'):
        chosen=selection[view]['selected']
        if selection[view]['parameters_sha256']!=digest(models[view]):raise ValueError('selected consequence model changed')
        for domain in ('essay','workshop_doc'):
            subset=[c for c in cases if c['private_factors']['domain']==domain]
            if len(subset)<96:raise ValueError('incomplete independent domain calibration')
            key=view+'|'+domain;battery=battery_identity(view,domain,source)
            provisional={'battery_identity':battery,'exact_executor_pass':False,'blind_control_fail':False,'story_control_fail':False}
            gates={};rows={}
            for kind in ('exact','blind','story'):
                built=[]
                for case in subset:
                    task=task_case(case,view);visible=public_task(task)
                    baseline=predict(visible,models[view][chosen]);prior=predict(visible,models[view]['class_prior'])
                    prospective,repair=control_answers(task,kind,prior)
                    built.append(row_for(case,view,prospective,repair,baseline))
                package={**dict.fromkeys(PACKAGE_FIELDS,'known-answer-fixture'),'domain':domain,'operation':'local_repair',
                    'model':'exact-constructor-ceiling' if kind=='exact' else kind,'assistance':'known-answer fixture; '+view}
                # Compute measured criteria without assuming that this instrument
                # already passed. Its truth checks and rates are real executions.
                gate=repair_gate(package,built,len(built),battery,provisional)
                checks={k:v for k,v in gate['checks'].items() if k!='instrument_known_answers'}
                gates[kind]={'criteria':checks,'criteria_pass':all(checks.values()),'measured':gate}
                rows[kind]=built
            receipt={'battery_identity':battery,'exact_executor_pass':gates['exact']['criteria_pass'],
                'blind_control_fail':not gates['blind']['criteria_pass'],'story_control_fail':not gates['story']['criteria_pass']}
            receipt['accepted']=all(receipt[k] is True for k in ('exact_executor_pass','blind_control_fail','story_control_fail'))
            receipt['source_units']=len(subset);receipt['controls']=gates
            receipt['truth_counts']=dict(Counter(r['consequence_truth'] for r in rows['exact']))
            groups[key]=receipt;all_rows[key]=rows
    return {'groups':groups,'all_groups_accepted':all(r['accepted'] for r in groups.values()),
        'cases_sha256':digest(cases),'local_task_source':source,'models_sha256':digest(models),
        'selection_sha256':digest(selection),'independent_units':len(cases),
        'controls_scope':'exact executor has private truth; blind/story controls do not; these are instrument fixtures'},score_json(all_rows)


def evaluate(cases,view,package,source,neural_rows,baseline_rows,models,selection,instrument):
    if len(cases)!=len(neural_rows) or len(cases)!=len(baseline_rows) or len({c['unit'] for c in cases})!=len(cases):
        raise ValueError('incomplete or duplicate local repair evaluation')
    if selection[view]['parameters_sha256']!=digest(models[view]):raise ValueError('evaluation comparator selection changed')
    if (instrument['models_sha256']!=digest(models) or instrument['selection_sha256']!=digest(selection)
        or source['files']['runners/stage9/local_repair.py']!=instrument['local_task_source']):
        raise ValueError('local instrument belongs to different tasks, fitting or selection')
    rows={domain:[] for domain in ('essay','workshop_doc')}
    for case,neural,baseline in zip(cases,neural_rows,baseline_rows):
        if neural['unit']!=case['unit'] or baseline['unit']!=case['unit']:raise ValueError('local evaluation pairs different sources')
        result=neural['result'];task=task_case(case,view);visible=public_task(task)
        if result['public_task_sha256']!=task['public_task_sha256'] or result['consequence_truth']!=consequence(task):
            raise ValueError('saved neural repair task or truth differs')
        chosen=selection[view]['selected'];base=baseline['results'][view]
        if base['public_task_sha256']!=digest(visible) or base['truth']!=consequence(task):raise ValueError('baseline task or truth differs')
        probabilities=base['call']['prediction']['predictions'][chosen]
        if probabilities!=predict(visible,models[view][chosen]):raise ValueError('baseline differs from frozen learned comparator')
        row=row_for(case,view,result['prospective_call'],result['repair_call'],probabilities)
        if row['execution']!=result['repair_execution']:raise ValueError('repair execution does not reproduce')
        rows[case['private_factors']['domain']].append(row)
    gates={}
    for domain,subset in rows.items():
        if not subset:raise ValueError('local evaluation omits a declared domain')
        definition=battery_identity(view,domain,instrument['local_task_source'])
        known=instrument['groups'][view+'|'+domain]
        gates[domain]=repair_gate(package_identity(package,source,view,domain),subset,len(subset),definition,known)
    return {'capabilities':gates,'scope':'symbolic local operation only; no historical full-generator admission'},score_json(rows)
