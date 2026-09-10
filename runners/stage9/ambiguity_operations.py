"""Ordinary finite-history and future choices, with record access kept separate.

DESIGN CHECK: M05/X02/X05/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: selected history and unseen outcomes cannot change ordinary public inputs.
ALTERNATIVE: actual neural choices over identical offered histories preserve
calibrated uncertainty and predict useful continuations. Each question has its own
target; no forecast follows receipt of that target. Invalid calls remain assigned.
All options describe the same three actions in different orders, with no unique
historical label embedded in continuation wording. No source kernel is supplied.
"""
from .ambiguity_jobs import QUESTIONS,public_queries,targets
from .ambiguity_cases import construct
from .common import canonical,digest,distribution


def inputs(case):
    a=case['ambiguity'];queries=public_queries(case);out={}
    histories={h:' -> '.join(':'.join(e[k] for k in ('type','section','slot')) for e in events)
               for h,events in a['offered_histories'].items()}
    for q in QUESTIONS:
        which='record' if q.endswith('_record') else 'after' if q=='history_after' else 'before'
        query=queries[which]
        public={'work':query['evidence'],'offered_completed_histories':histories}
        if q=='history_after':public['observed_later_event_after_library_arrival']=query['observed_future']
        if q.startswith('future_'):
            public['future_context']='original unchanged' if q=='future_old' else 'library now available; announcement observed by maker'
            question='Predict the next action or stop before observing it.'
            options={key:' '+key for key in sorted(a['artifact']['support'])}
        else:
            question='Which complete historical action order produced the current three-mark artifact?'
            options={h:' '+histories[h] for h in sorted(histories)}
        out[q]={'prefix':'The complete offered histories each contain exactly these three successful actions; '
                'the observation is censored immediately after the third success.\n'+canonical(public)+'\n'+question+'\nAnswer:',
                'options':options}
    return out


def evaluate_unit(case,call):
    if construct(case)!=case['ambiguity']:raise ValueError('prepared ambiguity case changed')
    visible=inputs(case);truth=targets(case);questions={}
    for q in QUESTIONS:
        result=call(visible[q],{'operation':'choice'},q)
        if result['accepted']:
            p=result['prediction']['probs'];distribution(p)
            if set(p)!=set(visible[q]['options']):raise ValueError('neural ambiguity support differs')
        questions[q]={'call':result,'truth':truth[q],'support':sorted(visible[q]['options']),
                      'input_sha256':digest(visible[q])}
    return {'questions':questions,'source_template_sha256':case['ambiguity']['content_sha256'],
            'scope':'six separate historical/future questions; explicit process record is diagnostic'}
