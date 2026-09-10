"""Public-input-only local consequence comparators.

DESIGN CHECK: C03/X02/X03/X09/X11; LESSONS 3--5, CONTROLS 6.
NULL: hidden state, labels, filenames and future events are refused as inputs;
constant features cannot learn independent consequences. ALTERNATIVE: visible
repetition, tool evidence and structure distinguish consequences where observable.
Rules predict from initial context or last observed tool use; neither reads the
producer's true current clock. Fitted probabilities are used as returned, no floor.
"""
import math
from .artifact_view import TYPES,all_header_actions,validate_work

LABELS=('done','failed','illegal','stopped')
VERSION='s9-repair-features-v1'


def validate(evidence):
    if set(evidence)!={'view','current','requested_mark','proposed_edit'}:
        raise ValueError('undeclared local comparator information')
    validate_work(evidence['current'],evidence['view'])
    actions=all_header_actions(evidence['current']['context'])
    if evidence['requested_mark'] not in actions or evidence['proposed_edit'] not in {'stop',*actions}:
        raise ValueError('local request outside declared action structure')
    return evidence


def rule(evidence,observed=False):
    validate(evidence)
    current=evidence['current'];proposed=evidence['proposed_edit']
    if proposed=='stop':return 'stopped'
    if proposed in current['marks']:return 'illegal'
    kind=proposed.split(':')[0]
    required={'cite':'library','consult':'source_access'}.get(kind)
    if required is None:return 'done'
    available=current['context']['tools'][required]
    if observed:
        # Successful marks and explicit failed attempts are observations, not
        # proof that a tool could not subsequently change.
        if any(m.split(':')[0]==kind for m in current['marks']):available=True
        if evidence['view']=='process_record':
            for event in current['events']:
                if event['type']==kind:available=event['outcome']=='done'
    return 'done' if available else 'failed'


def features(evidence):
    validate(evidence)
    current=evidence['current'];context=current['context'];proposed=evidence['proposed_edit']
    kind=proposed.split(':')[0]
    result={'bias':1.,'marks':len(current['marks'])/128.,'sections':len(context['sections'])/16.,
        'slots':sum(len(s['slots']) for s in context['sections'])/128.,
        'proposed_already_done':float(proposed in current['marks']),
        'library':float(context['tools']['library']),'source_access':float(context['tools']['source_access']),
        'tight_deadline':float(context['deadline']=='tight'),
        'process_view':float(evidence['view']=='process_record')}
    for name in ('peer','self','editor'):result['audience_'+name]=float(context['audience']==name)
    for name in (*TYPES,'stop'):
        result['proposed_'+name]=float(kind==name)
        result['marks_'+name]=sum(m.split(':')[0]==name for m in current['marks'])/32.
    for observed in (False,True):
        prediction=rule(evidence,observed)
        for label in LABELS:result['rule_'+str(observed)+'_'+label]=float(prediction==label)
    if evidence['view']=='process_record':
        result['events']=len(current['events'])/128.
        for name in TYPES:
            result['failed_'+name]=sum(e['type']==name and e['outcome']=='failed' for e in current['events'])/32.
    # Literal topic, section/slot names, unit IDs and inferred hidden clocks are
    # deliberately absent; names only participate in public equality tests.
    return result


def probabilities(logits):
    if set(logits)!=set(LABELS) or any(not math.isfinite(v) for v in logits.values()):
        raise ValueError('invalid complete consequence logits')
    maximum=max(logits.values());weights={k:math.exp(v-maximum) for k,v in logits.items()}
    total=math.fsum(weights.values());return {k:v/total for k,v in weights.items()}


def predict(evidence,parameters):
    validate(evidence)
    if parameters.get('version')!=VERSION or parameters.get('labels')!=list(LABELS):
        raise ValueError('undeclared consequence model')
    method=parameters['method']
    if method=='class_prior':result=parameters['prior']
    elif method in ('initial_rule','observed_rule'):
        result=parameters['rows'][rule(evidence,method=='observed_rule')]
    elif method=='logistic':
        values=features(evidence)
        result=probabilities({label:math.fsum(value*parameters['weights'][label].get(key,0.) for key,value in values.items()) for label in LABELS})
    else:raise ValueError('unknown cheap consequence method')
    if (set(result)!=set(LABELS) or any(type(v) not in (float,int) or not math.isfinite(v) or v<0 for v in result.values())
        or abs(math.fsum(result.values())-1)>1e-8):raise ValueError('invalid learned consequence distribution')
    return dict(result)
