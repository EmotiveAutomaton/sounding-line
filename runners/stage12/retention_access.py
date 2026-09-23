"""Prospective compression/access diagnostic on separate retention histories.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 6-7. NULL: an exact sufficient
posterior and full-history enumeration agree for every query; learned summaries
need not. ALTERNATIVE: correct supplied answers may still be misread, separating
access from information loss. Exact banks are explicitly privileged assistance,
not learned reconstruction. Acquisition, repeats, invalids and costs remain.
"""
import json
from .common import REPO, read, freeze, filehash, digest, distribution
from . import local_api
from .context_battery import text_for, independent, matched_timing_check
from .output_interface import adapt, profile_for_card

CONDITIONS = ('raw_history', 'unchanged_repeat', 'last_four', 'exact_state',
              'exact_bank', 'learned_account', 'learned_bank')
QUERIES = (1, 3)


def compile(out, card, pulse, raw):
    from runners.stage11_2.world import enumerate_predict
    roster = read(REPO / 'results/phase_2_4_stage_11_2/raw/fixture/dev-public.json')
    by = {r['unit']: r for r in roster}
    units = [by[k] for k in card['candidate_ids']]
    if len({r['cluster'] for r in units}) != len(units):
        raise ValueError('duplicate history construction')
    references = []
    for unit in units:
        weights = enumerate_predict(unit['history'], unit['queries'][0]['observation'])['weights']
        bank = {}
        for q in QUERIES:
            obs = unit['queries'][q]['observation']
            target = enumerate_predict(unit['history'], obs)['probabilities']
            compressed = enumerate_predict([], obs, prior=weights)['probabilities']
            direct = independent(unit['history'], obs)
            if any(abs(a-b) > 1e-12 for a,b in zip(target, compressed)):
                raise ValueError('sufficient posterior lost information')
            if any(abs(a-b) > 1e-12 for a,b in zip(target, direct)):
                raise ValueError('independent reference mismatch')
            bank[str(q)] = target
        references.append(dict(unit=unit['unit'], weights=weights, exact_bank=bank))
        pulse(phase='access-reference', completed=len(references), total=len(units))
    freeze(out / 'PUBLIC_UNITS.json', units)
    freeze(out / 'REFERENCE.json', references)
    freeze(out / 'MATRIX.json', dict(conditions=list(CONDITIONS), queries=list(QUERIES),
        calls_per_unit=17, acquisition_calls=3, evaluation_calls=14,
        bank_access='Both banks see query identities during acquisition; only exact bank receives computed reference answers.',
        state_access='Exact state is known-law posterior computation over public history; not inferred model state.',
        independent_unit='history content; both queries and all conditions remain paired',
        exposure='Existing exposed development fixture; separate from the first retention roster, not fresh project confirmation'))
    return dict(status='complete', kind='infrastructure', sources=len(units), maximum_calls=17*len(units),
        controls=dict(unique_histories=True, exact_sufficiency=True, independent_reference=True),
        files={n:filehash(out/n) for n in ('PUBLIC_UNITS.json','REFERENCE.json','MATRIX.json')})


def run(out, card, pulse, raw):
    from runners.stage11_2.world import rules, render_observation
    source = raw / 'jobs' / card['compile_card']
    by = {r['unit']:r for r in read(source / 'PUBLIC_UNITS.json')}
    units = [by[k] for k in card['candidate_ids']]
    refs = {r['unit']:r for r in read(source / 'REFERENCE.json')}
    admission = raw / 'jobs' / card['canary_card']
    if read(admission/'ADMISSION.json').get('reader_admitted') is not True:
        raise ValueError('reader not admitted')
    baseline = read(admission / 'ROWS.json')
    recorded, rows, timings = [], [], {'forecast':[], 'account':[]}

    def invoke(text, name, state, kind='forecast'):
        req = adapt(local_api.request(text, 4, kind), card.get('output_interface'))
        path = out / 'calls' / name
        result = local_api.call(req, 4, path, state, raw)
        recorded.append((req, path, result))
        timings[kind].append(result)
        if len(timings[kind]) % 5 == 0:
            timing = matched_timing_check(timings[kind][-5:], [r['call'] for r in baseline if r['call_class']==kind])
            freeze(out / ('TIMING-'+name+'.json'), timing)
            if timing['degraded']:
                raise RuntimeError('matched throughput degraded; retain incomplete unit')
        return result, read(path/'RAW.json')

    with local_api.service(out, profile_for_card(card, admission, card['profile']), raw) as state:
        for unit in units:
            key = unit['unit']; ref = refs[key]
            pulse(phase='access-acquisition', unit=key)
            account, body = invoke(text_for(unit, unit['history'], 0), key+'-account', state, 'account')
            if account['probabilities'] is None:
                raise ValueError('invalid acquisition; retain incomplete whole unit')
            account_text = json.loads(body['message']['content'])['analysis']
            bank = {}
            for q in QUERIES:
                result, _ = invoke(text_for(unit, unit['history'], q), key+'-bank-'+str(q), state)
                if result['probabilities'] is None:
                    raise ValueError('invalid bank acquisition; retain incomplete whole unit')
                bank[str(q)] = result['probabilities']
            freeze(out/(key+'-RECORDS.json'), dict(learned_account=account_text, learned_bank=bank,
                exact_state=ref['weights'], exact_bank=ref['exact_bank'], evidence_sha256=digest(unit['history'])))
            for q in QUERIES:
                obs = unit['queries'][q]['observation']
                question = rules(obs['world_family'])+'\nCurrent query: '+render_observation(obs, unit['rendering'])+'\nPredict probabilities in label order A, B, C, D.'
                base = text_for(unit, unit['history'], q)
                texts = dict(raw_history=base, unchanged_repeat=base,
                    last_four=text_for(unit, unit['history'][-4:], q),
                    exact_state='Exact known-law posterior from the earlier public history. Weights for (preferred column, trained): (left,no), (left,yes), (right,no), (right,yes): '+json.dumps(ref['weights'])+'\n'+question,
                    exact_bank='Privileged exact-program answers, computed from public history and supplied law. Bank: '+json.dumps(ref['exact_bank'])+'\nUse bank entry '+str(q)+'.\n'+question,
                    learned_account='Previously generated account, possibly mistaken:\n'+account_text+'\n'+question,
                    learned_bank='Previously generated answers, possibly mistaken. Bank: '+json.dumps(bank)+'\nUse bank entry '+str(q)+'.\n'+question)
                for condition in CONDITIONS:
                    pulse(phase='access-evaluation', unit=key, query=q, condition=condition)
                    result, _ = invoke(texts[condition], key+'-'+str(q)+'-'+condition, state)
                    rows.append(dict(unit=key, cluster=unit['cluster'], query=q, condition=condition,
                        **distribution(result['probabilities'], ref['exact_bank'][str(q)])))
    for req, path, result in recorded:
        if local_api.call(req, 4, path, {'uncertain':False}, raw) != result:
            raise ValueError('saved response replay differs')
    if len(recorded) != 17*len(units):
        raise ValueError('incomplete access roster')
    freeze(out/'ROWS.json', rows)
    return dict(status='complete', kind='scientific', sources=len(units), rows=len(rows), calls=len(recorded),
        scope='Declared finite-reference access/compression diagnostic; oracle assistance and query-aware acquisition explicit; no persistent-state or human claim',
        controls=dict(all_rivals=True, all_acquisition_charged=True, unchanged_repeat=True, raw_semantic_replay=True),
        files={'ROWS.json':filehash(out/'ROWS.json')})
