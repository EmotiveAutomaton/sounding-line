import copy
import math
from pathlib import Path

import pytest

from runners.stage9 import confirmation_freeze as subject
from runners.stage9 import common
from runners.stage9.common import digest, file_hash, read, write


LAYOUT = {key: [key] for key in ('unit', 'target', 'truth', 'valid')}


def test_pairing_recomputes_proper_score_and_never_drops_invalid_targets():
    rows = [{'unit': 'u', 'target': 't', 'truth': 'a', 'valid': True,
             'left': {'a': .8, 'b': .2}, 'right': {'a': .5, 'b': .5}}]
    left = LAYOUT | {'probabilities': ['left']}
    right = LAYOUT | {'probabilities': ['right']}
    result = subject.paired_rows(rows, rows, left, right, None)
    assert result[0]['difference'] == pytest.approx(math.log(.8 / .5))
    for bad in ([], rows * 2, [rows[0] | {'valid': False}], [rows[0] | {'truth': 'b'}],
                [rows[0] | {'unit': 'other'}], [rows[0] | {'right': {'a': 0., 'b': 1.}}]):
        with pytest.raises(ValueError):
            subject.paired_rows(rows, bad, left, right, None)


def allocation():
    return [{'unit': 'u'+str(i), 'role': 'discovery' if i < 3 else 'reserve',
             'content_sha256': digest(['content', i])} for i in range(103)]


def test_reserve_is_fixed_metadata_and_cannot_reuse_source_or_content():
    rows = allocation()
    result = subject.reserve_units(rows, ['u0', 'u1', 'u2'], 60, 9177, 'claim')
    assert len(result) == len(set(result)) == 60 and not set(result) & {'u0', 'u1', 'u2'}
    assert result == subject.reserve_units(list(reversed(rows)), ['u0', 'u1', 'u2'], 60, 9177, 'claim')
    for bad in (rows + [rows[0]], [rows[0] | {'role': 'reserve'}, *rows[1:]],
                [rows[0], rows[1] | {'content_sha256': rows[0]['content_sha256']}, *rows[2:]],
                [rows[0] | {'truth': 'reserved answer'}, *rows[1:]]):
        with pytest.raises(ValueError):
            subject.reserve_units(bad, ['u0', 'u1', 'u2'], 60, 9177, 'claim')


def environment(tmp_path, monkeypatch):
    import runners.stage9.launch as launch
    monkeypatch.setattr(common, 'REPO', tmp_path)
    monkeypatch.setattr(launch, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'inside', lambda p: Path(p).resolve())
    write(tmp_path / 'allocation.json', allocation())
    write(tmp_path / 'threshold.json', {'threshold': .05, 'scope': 'known fixture'})
    pointers = {name: {'path': name+'.json', 'sha256': file_hash(tmp_path / (name+'.json'))}
                for name in ('allocation', 'threshold')}
    jobs, snapshot = {}, {}
    for seed in (9001, 9002, 9003):
        path = tmp_path / str(seed)
        fit_sha = digest(['synthetic-seed-binding', seed])
        write(path / 'IDENTITY.json', {'role': 'pilot', 'training_complete_sha256': fit_sha})
        write(path / 'TRAINING.json', {'seed': seed, 'training_complete_sha256': fit_sha, 'synthetic_seed_metadata': True})
        write(path / 'GATE.json', {'accepted': True})
        write(path / 'PACKAGE.json', {'scope': 'known fixture; no trained model'})
        rows = [{'unit': 'u'+str(i), 'target': 't', 'truth': 'a', 'valid': True,
                 'left': {'a': p, 'b': 1-p}, 'right': {'a': .5, 'b': .5}}
                for i, p in enumerate((.4, .5, .6))]
        write(path / 'ROWS.json', rows)
        done = {'execution_complete': True, 'identity_sha256': digest(read(path / 'IDENTITY.json')),
                'outputs': common.closure(list(path.glob('*.json')))}
        write(path / 'COMPLETE.json', done)
        jobs[str(seed)] = {'produces': str(seed)+'/COMPLETE.json', 'module': 'runners.stage9.confirmation_fixture'}
        snapshot[str(seed)] = {'status': 'COMPLETE'}
    def ref(seed, name):
        return {'job': str(seed), 'path': str(seed)+'/'+name+'.json'}
    candidate = {'question': 'Known fixture claim', 'target': 'proper_log_score', 'contrast': 'left minus right',
        'view': 'same visible task', 'unit': 'independent fixture source', 'priority': 'serious_rival',
        'claim_kind': 'negative', 'practical_threshold': .05, 'threshold_evidence': pointers['threshold'],
        'gate_scope': 'known fixture only', 'gates': [{'evidence': ref(9001, 'GATE'), 'field': ['accepted']}],
        'reader_packages': [ref(9001, 'PACKAGE')], 'strongest_adversary': 'fixed one-half probabilities',
        'seed_forecasts': {str(s): {'left': ref(s, 'ROWS'), 'right': ref(s, 'ROWS')} for s in (9001,9002,9003)},
        'seed_evidence': {str(s): {'training': ref(s, 'TRAINING'), 'forecast_identity': ref(s, 'IDENTITY')}
                          for s in (9001,9002,9003)},
        'layouts': {'left': LAYOUT | {'probabilities': ['left']}, 'right': LAYOUT | {'probabilities': ['right']}},
        'allocation': pointers['allocation']}
    policy = {'version': 1, 'candidate_order': ['candidate'], 'candidates': {'candidate': candidate}, 'reserve_order_seed': 9177}
    review = {'selected': ['candidate'], 'reasons': {'candidate': 'A negative rival-discriminating fixture stays eligible.'}}
    return policy, review, jobs, snapshot


def test_negative_claim_and_empty_selection_retain_complete_review(tmp_path, monkeypatch):
    policy, review, jobs, snapshot = environment(tmp_path, monkeypatch)
    result = subject.review_packets(policy, review, jobs, snapshot, 'pilot')
    assert result['selected_count'] == 1 and not result['scientific_confirmation']
    assert result['selected'][0]['planning']['discovery']['n_units'] == 3
    assert result['selected'][0]['planning']['discovery']['seeds'] == [9001,9002,9003]
    assert result['selected'][0]['candidate']['claim_kind'] == 'negative'
    empty = subject.review_packets(policy, review | {'selected': []}, jobs, snapshot, 'pilot')
    assert empty['selected_count'] == 0 and empty['review']['reasons'] == review['reasons']


@pytest.mark.parametrize('fault', ['missing_seed', 'seed_substitution', 'missing_review', 'failed_producer',
                                  'wrong_role', 'changed_forecast', 'unbound_output', 'too_many_claims'])
def test_freeze_refuses_incomplete_or_misbound_evidence(tmp_path, monkeypatch, fault):
    policy, review, jobs, snapshot = environment(tmp_path, monkeypatch)
    c = policy['candidates']['candidate']
    if fault == 'missing_seed':
        del c['seed_forecasts']['9003']
    elif fault == 'seed_substitution':
        c['seed_evidence']['9003'] = copy.deepcopy(c['seed_evidence']['9001'])
    elif fault == 'missing_review':
        review['reasons'] = {}
    elif fault == 'failed_producer':
        snapshot['9001']['status'] = 'FAILED'
    elif fault in ('wrong_role', 'changed_forecast'):
        name = 'IDENTITY' if fault == 'wrong_role' else 'ROWS'
        path = tmp_path / '9001' / (name+'.json')
        value = read(path)
        if fault == 'wrong_role':
            value['role'] = 'development'
        else:
            value[0]['left'] = {'a': .9, 'b': .1}
        write(path, value)
        if fault == 'wrong_role':
            done = read(path.parent / 'COMPLETE.json')
            done['identity_sha256'] = digest(value)
            done['outputs'] = common.closure([tmp_path / p for p in done['outputs']['files']])
            write(path.parent / 'COMPLETE.json', done)
    elif fault == 'unbound_output':
        write(tmp_path / 'unbound.json', read(tmp_path / '9001/ROWS.json'))
        c['seed_forecasts']['9001']['left']['path'] = 'unbound.json'
    else:
        review['selected'] = ['candidate'] * 4
    with pytest.raises(ValueError):
        subject.review_packets(policy, review, jobs, snapshot, 'pilot')


def test_live_gate_boolean_and_wrong_seed_value_are_checked(tmp_path, monkeypatch):
    policy, review, jobs, snapshot = environment(tmp_path, monkeypatch)
    for name, value in [('GATE', {'accepted': {'accepted': True}}),
                        ('GATE', {'accepted': False}),
                        ('TRAINING', {'seed': 9002, 'training_complete_sha256': digest(['synthetic-seed-binding',9001]),
                                      'synthetic_seed_metadata': True})]:
        path = tmp_path / '9001' / (name+'.json')
        original = path.read_bytes()
        write(path, value)
        done = read(path.parent / 'COMPLETE.json')
        done['outputs'] = common.closure([tmp_path / p for p in done['outputs']['files']])
        write(path.parent / 'COMPLETE.json', done)
        with pytest.raises(ValueError):
            subject.review_packets(policy, review, jobs, snapshot, 'pilot')
        path.write_bytes(original)
        done['outputs'] = common.closure([tmp_path / p for p in done['outputs']['files']])
        write(path.parent / 'COMPLETE.json', done)
