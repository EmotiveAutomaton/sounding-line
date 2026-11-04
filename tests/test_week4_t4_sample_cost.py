import copy
import json
import numpy as np
import pytest
from runners.drive.cards import week4_t4_sample_cost as cost
from runners.drive.cards import week4_t4_inputs as source
from runners.drive.cards import week4_t4_matched_cost as original
from runners.drive.cards import week4_t4_kernel_h1 as kernel
from runners.stage14.common import filehash


def test_known_selection_and_whole_unit_retention():
    rows = cost.fixture()
    packed, manifest = cost.pack_sample(rows, [str(i) for i in range(6)], 3, 2)
    assert manifest['stratum_selected'] == {'a': 2, 'b': 1}
    chosen = set(manifest['selected_writers'])
    assert set(packed['train']['keys'] + packed['test']['keys']) == {r['key'] for r in rows if r['writer'] in chosen}
    assert len(packed['train']['w']) == len(packed['test']['w']) == 12
    assert set(packed['train']['w']) == set(range(3))
    assert cost.pack_sample(list(reversed(rows)), list(reversed([str(i) for i in range(6)])), 3, 2) == (packed, manifest)
    assert all(cost.known_answers().values())


def test_distinct_sessions_define_genre_not_menu_counts():
    rows = [dict(writer='w', session='s1', genre='a'), dict(writer='w', session='s2', genre='b'),
            dict(writer='w', session='s3', genre='b'), dict(writer='z', session='z1', genre='a')]
    a = cost.selection(rows, ['z', 'w'], 2)
    b = cost.selection(rows + [rows[0]] * 100, ['z', 'w'], 2)
    assert a == b and a['stratum_population'] == {'a': 1, 'b': 1}
    with pytest.raises(ValueError, match='genre'):
        cost.selection(rows + [dict(writer='w', session='s1', genre='b')], ['z', 'w'], 2)
    for size in (0, 3, 1.5):
        with pytest.raises(ValueError):
            cost.selection(rows, ['z', 'w'], size)
    with pytest.raises(ValueError):
        cost.selection(rows, ['z', 'missing'], 1)


def test_labels_and_heldout_features_do_not_affect_training():
    rows = cost.fixture()
    p, m = cost.pack_sample(rows, [str(i) for i in range(6)], 3, 2)
    changed = copy.deepcopy(rows)
    for row in changed:
        row['choice'] = row['dismissal_index']
        if row['half'] == 'test':
            row['features'][0][0] += 1000
            row['state'][0] += 1000
    q, n = cost.pack_sample(changed, [str(i) for i in range(6)], 3, 2)
    assert m == n and p['scaling'] == q['scaling']
    for law in (False, True):
        a, b = original.generated(p, 20261102, law), original.generated(q, 20261102, law)
        assert all(np.array_equal(a[k], b[k]) for k in a)
    with pytest.raises(ValueError, match='floor'):
        cost.pack_sample(rows, [str(i) for i in range(6)], 3, 5)


def test_complete_fit_replay_and_certificate(tmp_path):
    config = cost.configuration('constructed')
    cost.execute(tmp_path, {}, config)
    assert cost.verify(tmp_path, {}, config)['complete_selection_replay']
    fits = json.loads((tmp_path / 'PRIVATE_FITS.json').read_text())
    for case in fits:
        for arm in ('shared', 'individual'):
            fit = case[arm]
            assert fit['reference_projected_gradient'] <= 1e-5
            assert abs(fit['reference_objective'] - fit['objective']) <= 1e-9
    value = json.loads((tmp_path / 'PRIVATE_SELECTION.json').read_text())
    value['selected_writers'][0] = 'changed'
    (tmp_path / 'PRIVATE_SELECTION.json').write_text(json.dumps(value))
    with pytest.raises(ValueError, match='replay'):
        cost.verify(tmp_path, {}, config)
    with pytest.raises(ValueError, match='configuration'):
        cost.execute(tmp_path, {}, dict(config, sample_writers=24))


def producers(tmp_path):
    rows = []
    for writer in range(30):
        for half, start in (('train', 0), ('test', 100)):
            for i in range(20):
                row = copy.deepcopy(source.fixture()[i % 4])
                row.update(key=f'{writer}-{half}-{i}', writer=str(writer), session=f'{writer}-{half}',
                           half=half, open_at=start+i, genre='a' if writer < 15 else 'b')
                rows.append(row)
    packed = source.assemble(rows)
    roots = {key: tmp_path / key for key in ('inputs', 'history', 'bank', 'kernel')}
    for root in roots.values():
        (root / 'output').mkdir(parents=True)
    def freeze(name, outputs):
        root = roots[name]
        (root / 'COMPLETE.json').write_text(json.dumps(dict(status='COMPLETE', fresh_process_verified=True,
            outputs={n: filehash(root/n) for n in outputs})))
    source.gzip_equal(roots['history'] / 'output/FEATURES.json.gz', rows)
    source.write_equal(roots['history'] / 'output/SUMMARY.json', dict(mode='full'))
    source.write_equal(roots['history'] / 'output/PRIVATE_SUPPORT.json', dict(supported_writers=packed['writers']))
    freeze('history', ['output/FEATURES.json.gz', 'output/SUMMARY.json', 'output/PRIVATE_SUPPORT.json'])
    source.gzip_equal(roots['inputs'] / 'output/PRIVATE_DATA.json.gz', packed)
    source.write_equal(roots['inputs'] / 'output/SUMMARY.json', dict(packed['summary'], mode='full'))
    source.write_equal(roots['inputs'] / 'PLAN.json', dict(module='runners.drive.cards.week4_t4_inputs',
        config=source.configuration('full'), inputs=dict(history_completion=str(roots['history'] / 'COMPLETE.json'))))
    freeze('inputs', ['PLAN.json', 'output/PRIVATE_DATA.json.gz', 'output/SUMMARY.json'])
    for name in ('bank', 'kernel'):
        source.write_equal(roots[name] / 'output/SUMMARY.json', dict(complete_bank=True, bank_gate=True, worlds=40))
    freeze('bank', ['output/SUMMARY.json'])
    source.write_equal(roots['kernel'] / 'PLAN.json', dict(module='runners.drive.cards.week4_t4_kernel_h1', config=kernel.configuration('full')))
    freeze('kernel', ['PLAN.json', 'output/SUMMARY.json'])
    return {key+'_completion': str(roots[key] / 'COMPLETE.json') for key in ('inputs', 'bank', 'kernel')}, roots, freeze


def test_actual_producer_boundary_and_history_tamper(tmp_path):
    inputs, roots, freeze = producers(tmp_path)
    packed, manifest = cost.load(inputs)
    assert len(packed['writers']) == 25 and manifest['population_writers'] == 30
    assert manifest['stratum_selected'] == {'a': 13, 'b': 12}
    assert len(packed['train']['keys']) == len(packed['test']['keys']) == 500
    (roots['history'] / 'output/PRIVATE_SUPPORT.json').write_text('{}')
    with pytest.raises(ValueError, match='changed'):
        cost.load(inputs)


def test_failed_or_resealed_false_kernel_refused(tmp_path):
    inputs, roots, freeze = producers(tmp_path)
    (roots['kernel'] / 'output/SUMMARY.json').write_text(json.dumps(dict(complete_bank=True, bank_gate=False, worlds=40)))
    freeze('kernel', ['PLAN.json', 'output/SUMMARY.json'])
    with pytest.raises(ValueError, match='validation'):
        cost.load(inputs)
    (roots['kernel'] / 'COMPLETE.json').write_text(json.dumps(dict(status='FAILED', fresh_process_verified=False)))
    with pytest.raises(ValueError):
        cost.load(inputs)
