"""Separate semantic-key interface; never repairs the original reader outputs.

DESIGN CHECK: LESSONS 3-5. NULL: invalid/non-unit allocations and wrong explicit
facts refuse admission; constant handling cannot pass varied known controls.
ALTERNATIVE: named-category probabilities preserve their literal values and exact
known targets. All original attempts stay immutable; one new interface attempt.
"""
from contextlib import contextmanager
from copy import deepcopy
import json
from . import gpu
from .reconstruction import ACTIONS, FIELDS, SLOTS, admission_fixture
from .scoring import probabilities
from .common import freeze, read

_request = gpu.request
_parse = gpu.parse


def allocation(labels):
    return dict(type='object', properties={k:dict(type='number',minimum=0,maximum=1) for k in labels}, required=list(labels), additionalProperties=False)


def schema():
    result=deepcopy(gpu.schema())
    result['properties']['handling']=allocation(ACTIONS)
    fact=result['properties']['facts']['items']
    for field,labels in FIELDS.items():fact['properties'][field]=allocation(labels)
    return result


def request(evidence,arm):
    result=deepcopy(_request(evidence,arm))
    result['format']=schema()
    text=result['messages'][1]['content']
    text=text.replace('Recorded handling order: accept, edit, dismiss, ignore.',
        'Handling is a probability object with keys accept, edit, dismiss, ignore.')
    text=text.replace('Category orders:', 'Required probability-object keys by field:')
    instruction=('\nEach categorical field is an OBJECT keyed by the category names, '
        'not an array of indices. Include every key with a probability in [0,1]; '
        'each object sums to one. Facts has one item for each slot, including '
        'absent operations. If explicit observed operations are supplied, report '
        'those observed categories and locations; absent, none, and unknown have '
        'different meanings. Otherwise retain uncertainty rather than inventing '
        'a missing history. Goal support remains four independent probabilities '
        'in the listed goal order, not a categorical distribution.\n')
    result['messages'][1]['content']=text.replace('\nEVIDENCE:\n',instruction+'\nEVIDENCE:\n')
    # Keep the original evidence admission. The larger named-key response has its
    # own declared budget and actual service-native prompt/response checks.
    result['options']['num_predict']=4096
    return result


def parse(response,length):
    if type(response.get('eval_count')) is not int or response['eval_count']>4096:
        raise ValueError('named-key response exceeds declared budget')
    if type(response.get('prompt_eval_count')) is not int or response['prompt_eval_count']>4096:
        raise ValueError('named-key native prompt exceeds declared budget')
    body=json.loads(response['message']['content'])
    def vector(value,labels):
        if not isinstance(value,dict) or set(value)!=set(labels):
            raise ValueError('categorical keys differ')
        values=[value[k] for k in labels]
        if probabilities(values,len(labels)) is None:raise ValueError('invalid literal named probabilities')
        return values
    body['handling']=vector(body['handling'],ACTIONS)
    for fact in body['facts']:
        for field,labels in FIELDS.items():fact[field]=vector(fact[field],labels)
    translated=deepcopy(response)
    translated['message']['content']=json.dumps(body)
    # Reuse the semantic validator after a lossless key-order map. Validate the
    # actual, unchanged service counts against this protocol's explicit budgets.
    return _parse(translated,length,response_budget=4096,prompt_budget=4096)


@contextmanager
def interface():
    old_request,old_parse=gpu.request,gpu.parse
    gpu.request,gpu.parse=request,parse
    try:yield
    finally:gpu.request,gpu.parse=old_request,old_parse


def fixtures():
    base=admission_fixture();base['views']['A']={'endpoint':base['views']['D']['endpoint']}
    result=[]
    for i,action in enumerate(ACTIONS):
        row=deepcopy(base);row['key']=f'healing-known-{action}';row['unit']=row['key']
        row['target']['handling']=action;row['views']['D']['observed_handling']=action
        if action in ('dismiss','ignore'):
            row['views']['D']['endpoint']=row['views']['D']['before'];row['views']['A']['endpoint']=row['views']['D']['endpoint']
            for f in row['target']['facts']:f.update(actor='unknown',operation='absent',relation='none',exact_spans=[])
        elif action=='edit':
            # Explicit changed categories, keeping the supplied location known.
            f=next(f for f in row['target']['facts'] if f['slot']=='entry')
            f.update(actor='human_writer',operation='content_edit',relation='modifies')
        row['views']['D']['observed_operations']=deepcopy(row['target']['facts'])
        row['control']='healing-explicit-known-answer'
        result.append(row)
    return result


def handle(card,out,raw,tick):
    from .worker import handle as original_handle
    with interface():
        result=original_handle(dict(card,action='qwen-batch'),out,raw,tick)
    if card['action']=='qwen-keyed-admission':
        controls=[r for r in result['rows'] if r.get('admission_control')=='healing-explicit-known-answer']
        admitted=(result['admitted'] and len(controls)==4 and
            all(r['scores']['handling']['correct']==1 and r['scores']['location']['strict']==1 and
                all(r['scores'][f]['correct']==1 for f in FIELDS) for r in controls))
        freeze(out/'ADMISSION.json',dict(admitted=bool(admitted),known_controls=len(controls),
            protocol='semantic-category-keys-v1',gate='all literal valid; all explicit known facts exact',
            original_failure_retained=True))
    return result


def summarize(card,out,raw,tick):
    from .reconstruction import summarize as summary, score_prediction
    records=[];expected={}
    for name in card['args']['blocks']:
        manifest=read(raw/'manifests'/f'{name}.json');args=manifest['args']
        rows={r['key']:r for r in read(raw/args['rows'])}
        primary={(k,v,a) for k in rows for v in args['views'] for a in ('direct','joint','without-goals','without-execution','equal-direct')}
        block=read(raw/'jobs'/name/'PREDICTIONS.json')['rows']
        actual=[(r['key'],r['view'],r['arm']) for r in block if not r['arm'].startswith('reader-')]
        if len(actual)!=len(set(actual)) or set(actual)!=primary:raise ValueError('primary reader census differs')
        derived={(r['key'],r['view'],'reader-'+a) for r in block if r['arm']=='joint' and not r['prediction'].get('invalid') for a in ('joint-execution','without-goal-coupling','shuffled-goal-coupling')}
        full=[(r['key'],r['view'],r['arm']) for r in block]
        if len(full)!=len(set(full)) or set(full)!=(primary|derived):raise ValueError('coupled reader census differs')
        for r in block:
            if r.get('scores') is None:raise ValueError('reader preflight excluded a frozen case')
            if score_prediction(rows[r['key']],r['prediction'],r['metadata'])!=r['scores']:raise ValueError('reader score replay differs')
        records.extend(block)
    result=summary(records)
    result['missing']=['Human local-goal accuracy unavailable without independent labels']
    result['invalid_primary_replies']=sum(r.get('prediction',{}).get('invalid',False) for r in records if not r['arm'].startswith('reader-'))
    result['coupling_scope']='Derived coupling comparisons exist only where the joint reader returned valid literal goal support; unavailable cases are counted separately, never treated as paired successes.'
    result['unavailable_coupling_cases']=sum(r.get('prediction',{}).get('invalid',False) for r in records if r['arm']=='joint')
    freeze(out/'ANALYSIS.json',result);return result
