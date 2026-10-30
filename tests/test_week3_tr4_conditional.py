import copy
import json
import numpy as np
import pytest
from runners.drive.cards import week3_tr4_conditional as c
from runners.drive.cards import week3_tr4_conditional_worlds as w
from runners.drive.cards import week3_tr4_comparison as old


def test_exact_orbit_ties_and_offset():
    out = w.known_answers()
    assert len(out['exact_orbit_statistics']) == 24
    assert sum(p < .05 for p in out['exact_orbit_probabilities']) <= 1
    assert out['rank_offset_probability'] == .6
    assert c.probability(7., [7.] * 200) == 1
    with pytest.raises(ValueError): c.probability(1., [np.nan])


def test_conditional_shuffles_preserve_missingness_and_all_cells():
    census = w.construct('prompt_block', 2026103997)['census']
    census['rows'][0]['counts'] = dict.fromkeys(old.CLASSES, 0)
    groups, retained = old.prepare(census)
    rng = np.random.default_rng(2)
    for g in groups:
        for _ in range(5):
            changed = c.shuffle(g, rng)
            assert np.array_equal(changed.sum(axis=1), g['data'].sum(axis=1))
            for indices in c.cells(g):
                assert sorted(map(tuple, changed[indices])) == sorted(map(tuple, g['data'][indices]))
    assert len(retained) == 432


def test_world_truth_and_disjoint_seeds():
    assert len(w.WORLDS) == len(set(seed for _, seed in w.WORLDS)) == 80
    for family in w.FAMILIES:
        world = w.construct(family, 2026103996)
        assert world == w.construct(family, 2026103996)
        groups, _ = old.prepare(world['census'])
        truth = {x['session']:np.array(x['probabilities']) for x in world['truth']}
        for g in groups:
            for x in truth.values(): assert np.all(x > 0) and np.isclose(x.sum(), 1)
            for indices in c.cells(g):
                if family in ('stationary','prompt_block'):
                    values = [truth[g['rows'][i]['session']] for i in indices]
                    assert all(np.array_equal(values[0], v) for v in values)
            dose = np.abs(truth[g['rows'][0]['session']] - truth[g['rows'][12]['session']]).sum() / 2
            assert dose == pytest.approx({'stationary':0,'prompt_block':.3,'drift_15':.15,'drift_30':.3}[family])


def test_fixed_writers_remain_in_primary_population_and_old_forecast_matches():
    census = w.construct('stationary', 2026103995)['census']
    for r in census['rows']:
        if r['writer'] == 'w04':
            r['counts'] = dict(zip(old.CLASSES, [100,100,100,100]))
    result = c.analyze(census, 3, 11)
    assert result['primary']['writers'] == 14
    assert result['primary']['movable_writers'] == 13
    assert len(result['retained']) == 432
    groups, _ = old.prepare(census)
    parameters = old.tune(groups)
    for g, actual in zip([g for g in groups if g['half'] == 'test'], result['writer_losses']):
        expected = old.primary(g, all_models=True, parameters=parameters)
        assert actual['gain'] == pytest.approx(expected['gain'], abs=1e-14)


def test_native_reentry_corruption_and_scope_refusal(tmp_path):
    landing = tmp_path/'parent.json'
    landing.write_text(json.dumps(dict(full_write_through=True, id='S15-TR4-20261027')), encoding='utf8')
    inputs = dict(parent_landing=str(landing))
    output = tmp_path/'out'
    assert w.execute(output, inputs, w.CONFIGS['constructed'])['status'] == 'complete'
    assert w.verify(output, inputs, w.CONFIGS['constructed'])['complete_input_replay']
    damaged = json.loads((output/'SUMMARY.json').read_text())
    damaged['rank_offset_probability'] = 0
    (output/'SUMMARY.json').write_text(json.dumps(damaged), encoding='utf8')
    with pytest.raises(ValueError, match='replay'): w.verify(output, inputs, w.CONFIGS['constructed'])
    with pytest.raises(ValueError, match='configuration'): w.execute(output, inputs, dict(mode='main', worlds=[]))


def test_calibration_gate_boundaries():
    cells = [dict(family=f, result=dict(primary=dict(status='not_detected'))) for f, _ in w.WORLDS]
    for cell in [x for x in cells if x['family'] == 'drift_30'][:7]:
        cell['result']['primary']['status'] = 'positive_conditional_order'
    for cell in [x for x in cells if x['family'] == 'stationary'][:3]:
        cell['result']['primary']['status'] = 'positive_conditional_order'
    assert w.summarize(cells)['calibration_pass']
    damaged = copy.deepcopy(cells)
    damaged[3]['result']['primary']['status'] = 'positive_conditional_order'
    assert not w.summarize(damaged)['calibration_pass']
    assert not w.summarize(cells[:-1])['calibration_pass']
