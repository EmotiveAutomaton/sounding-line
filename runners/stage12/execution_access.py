"""Frozen supplied-answer execution diagnostic; no acquisition or fitting.

DESIGN CHECK: LESSONS 3-5, CONTROLS 6-7. NULL: valid wrong-entry or
permuted vectors fail fidelity. ALTERNATIVE: literal correct copies agree
with the declared rounded reference. Exact state and full-history programs
agree before generation. Invalids, repeated calls and all costs persist.
"""
import json
import math
from .common import REPO, read, freeze, filehash, digest, distribution
from . import local_api
from .context_battery import text_for, independent, matched_timing_check
from .output_interface import adapt, profile_for_card

CONDITIONS = ('raw_history', 'unchanged_repeat', 'exact_state',
              'bank_predict', 'bank_copy', 'selected_predict', 'selected_copy')
QUERIES = (1, 3)


def rounded_answer(probabilities):
    if not distribution(probabilities, [1., 0., 0., 0.])['valid']:
        raise ValueError('invalid reference')
    counts = [math.floor(v * 1000) for v in probabilities]
    order = sorted(range(4), key=lambda i: (-(probabilities[i]*1000-counts[i]), i))
    for i in order[:1000-sum(counts)]:
        counts[i] += 1
    return [v / 1000 for v in counts]


def fidelity(probabilities, answer):
    if not distribution(probabilities, answer)['valid']:
        return dict(execution_valid=False, copied_exactly=False, execution_l1=None)
    error = sum(abs(a-b) for a,b in zip(probabilities, answer))
    return dict(execution_valid=True, copied_exactly=error < 1e-9, execution_l1=error)


def compile(out, card, pulse, raw):
    from runners.stage11_2.world import enumerate_predict, rules, render_observation
    roster = read(REPO/'results/phase_2_4_stage_11_2/raw/fixture/dev-public.json')
    by = {r['unit']: r for r in roster}
    units = [by[k] for k in card['candidate_ids']]
    if len({r['cluster'] for r in units}) != len(units):
        raise ValueError('duplicate history content')
    requests, targets, references = [], [], []
    for unit in units:
        weights = enumerate_predict(unit['history'], unit['queries'][0]['observation'])['weights']
        exact, bank = {}, {}
        for q in QUERIES:
            obs = unit['queries'][q]['observation']
            target = enumerate_predict(unit['history'], obs)['probabilities']
            state = enumerate_predict([], obs, prior=weights)['probabilities']
            reference = independent(unit['history'], obs)
            if any(abs(a-b)>1e-12 for a,b in zip(target, state)) or any(abs(a-b)>1e-12 for a,b in zip(target, reference)):
                raise ValueError('exact reference disagreement')
            exact[str(q)] = target
            bank[str(q)] = rounded_answer(target)
        references.append(dict(unit=unit['unit'], cluster=unit['cluster'], weights=weights,
                               exact=exact, rounded_bank=bank))
        for q in QUERIES:
            obs = unit['queries'][q]['observation']
            question = rules(obs['world_family'])+'\nCurrent query: '+render_observation(obs, unit['rendering'])+'\nLabel order: A, B, C, D.'
            selected = {str(q): bank[str(q)]}
            base = text_for(unit, unit['history'], q)
            texts = dict(raw_history=base, unchanged_repeat=base,
                exact_state='Exact known-law posterior over (left,no), (left,yes), (right,no), (right,yes): '+json.dumps(weights)+'\n'+question+'\nPredict the probabilities.')
            for scope, supplied in (('bank', bank), ('selected', selected)):
                shared = ('Privileged exact-program answers rounded to three decimals with their sum preserved. '
                          'These are supplied answers, not your reconstructed state. Bank: '+json.dumps(supplied)+
                          '\nUse entry '+str(q)+'.\n'+question)
                texts[scope+'_predict'] = shared+'\nPredict the probabilities using the supplied answer.'
                texts[scope+'_copy'] = shared+'\nExecute the lookup: copy the four numbers in entry '+str(q)+' into probabilities, unchanged and in order. Do not recompute the answer.'
            for condition in CONDITIONS:
                ident = digest(['S12-execution-v1', unit['unit'], q, condition])
                req = adapt(local_api.request(texts[condition], 4), card['output_interface'])
                requests.append(dict(id=ident, unit=unit['unit'], cluster=unit['cluster'], query=q,
                                     condition=condition, request=req))
                targets.append(dict(id=ident, target=exact[str(q)], supplied_answer=bank[str(q)]))
        pulse(phase='execution-reference', completed=len(references), total=len(units))
    diverse = sum(r['rounded_bank']['1'] != r['rounded_bank']['3'] for r in references)
    if diverse < min(4, len(units)):
        raise ValueError('insufficient distinct query entries for lookup diagnostic')
    freeze(out/'REQUESTS.json', requests)
    freeze(out/'EVALUATOR_ONLY.json', targets)
    freeze(out/'REFERENCES.json', references)
    freeze(out/'MATRIX.json', dict(conditions=list(CONDITIONS), queries=list(QUERIES),
        calls_per_unit=14, acquisition_calls=0, total_calls=len(requests), distinct_entry_histories=diverse,
        exposure='existing exposed development fixture; no fresh confirmation',
        support='paired history content; oracle assistance and rounding separately identified'))
    return dict(status='complete', kind='infrastructure', sources=len(units), maximum_calls=len(requests),
        controls=dict(unique_histories=True, exact_sufficiency=True, independent_reference=True,
                      nonconstant_query_answers=True, explicit_assistance=True),
        files={n:filehash(out/n) for n in ('REQUESTS.json','EVALUATOR_ONLY.json','REFERENCES.json','MATRIX.json')})


def run(out, card, pulse, raw):
    source = raw/'jobs'/card['compile_card']
    requests = [r for r in read(source/'REQUESTS.json') if r['unit'] in card['candidate_ids']]
    targets = {r['id']:r for r in read(source/'EVALUATOR_ONLY.json')}
    if len(requests) != 14*len(card['candidate_ids']) or digest(requests) != card['effective_requests_digest']:
        raise ValueError('execution request roster differs')
    admission = raw/'jobs'/card['canary_card']
    if read(admission/'ADMISSION.json').get('reader_admitted') is not True:
        raise ValueError('reader not admitted')
    baseline = [r['call'] for r in read(admission/'ROWS.json') if r['call_class']=='forecast']
    recorded, rows = [], []
    with local_api.service(out, profile_for_card(card, admission, card['profile']), raw) as state:
        for index, r in enumerate(requests):
            pulse(phase='execution-access', completed=index, total=len(requests))
            path = out/'calls'/r['id']
            result = local_api.call(r['request'], 4, path, state, raw)
            recorded.append((r, path, result))
            timing = matched_timing_check([result], baseline)
            freeze(out/('TIMING-'+r['id']+'.json'), timing)
            if timing['degraded']:
                raise RuntimeError('matched throughput degraded; retain incomplete unit')
            target = targets[r['id']]
            p = result['probabilities']
            rows.append(dict(id=r['id'], unit=r['unit'], cluster=r['cluster'], query=r['query'],
                condition=r['condition'], probabilities=p, **distribution(p, target['target']),
                **fidelity(p, target['supplied_answer']),
                rounded_reference_score=distribution(target['supplied_answer'], target['target']),
                exact_reference_score=distribution(target['target'], target['target']),
                uniform_score=distribution([.25]*4, target['target'])))
    for r, path, result in recorded:
        if local_api.call(r['request'], 4, path, {'uncertain':False}, raw) != result:
            raise ValueError('execution raw semantic replay differs')
    freeze(out/'ROWS.json', rows)
    return dict(status='complete', kind='scientific', sources=len(card['candidate_ids']),
        calls=len(recorded), rows=len(rows),
        scope='Supplied-answer execution versus prediction; exposed constructed histories, no persistent-state or human claim',
        controls=dict(all_rivals=True, unchanged_repeat=True, raw_semantic_replay=True, invalids_retained=True),
        files={'ROWS.json':filehash(out/'ROWS.json')})
