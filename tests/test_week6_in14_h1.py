"""Small frozen constructed .h1 parity selector; no participant-source execution."""
import ast
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week6_in14_math_v1 as old
from runners.drive.cards import week6_in14_math_h1 as new
from runners.drive.cards import week6_in14_replay_h1 as replay
from runners.drive.cards import week6_in14_in16_run_v1 as oldrun
from runners.drive.cards import week6_in14_run_h1 as newrun
from runners.drive.cards import week6_in14_h1 as entry
from runners.drive.cards import week6_in14_in16_fixture_v1 as fixture
from runners.drive.cards import week5_engine_export_io as seal


def panel(lengths=(11, 7, 19, 4), columns=3, means=0., epsilon=None):
    rng = np.random.default_rng(141407)
    rows = []
    for i, n in enumerate(lengths):
        x = rng.normal(size=(n, columns))
        if epsilon is not None:
            x[:, -1] = x[:, 0] + epsilon * rng.normal(size=n)
        x += means * (i + 1)
        y = x @ np.arange(1, columns + 1) / 7 + i * .3 + rng.normal(0, .02, n)
        rows.extend({'prolific_id': f'w{i}', 'outcome': y[j],
                     **{f'x{k}': x[j, k] for k in range(columns)}} for j in range(n))
    return new.design(pd.DataFrame(rows), [f'x{k}' for k in range(columns)])


def parity(p, counts=None, path=None):
    expected, error = old.fit(p, counts, True)
    trace = {}; actual, other = replay.fit(p, counts, trace)
    assert other == error
    if expected is None:
        assert actual is None
    else:
        assert actual.keys() == expected.keys()
        assert np.allclose(list(actual.values()), list(expected.values()), atol=1e-7, rtol=0)
    assert new.fit(p, counts, True) == (actual, other)
    if path is not None:
        assert trace['path'] == path
    return trace


@pytest.mark.parametrize('counts', [None, {'w0': 3, 'w1': 0, 'w2': 1, 'w3': 5},
                                    {'w0': 0, 'w1': 4, 'w2': 0, 'w3': 0}])
def test_unequal_lengths_multiplicity_and_dropped_writers(counts):
    p = panel()
    trace = parity(p, counts, 'projected')
    chosen = {k: 1 for k in p['keys']} if counts is None else counts
    expected_rows = sum(len(y) - 1 for k, _, y in p['raw_blocks'] if chosen.get(k, 0) > 0)
    assert trace['projected_shape'] == [expected_rows, 3]


@pytest.mark.parametrize('lengths', [(1, 7, 11, 1), (1, 1, 1, 1), (2, 1)])
def test_one_row_and_underdetermined_writers(lengths):
    parity(panel(lengths), path='projected' if sum(n - 1 for n in lengths) >= 3 else 'dense')


@pytest.mark.parametrize('epsilon', [0., 1e-13, 1e-9])
def test_exact_and_near_rank_cases_retain_dense_decision(epsilon):
    parity(panel(epsilon=epsilon), path='dense')


def test_constant_columns_keep_original_unsupported_result():
    p = panel()
    for _, a, _ in p['raw_blocks']:
        a[:, 0] = 1.
    parity(p, path='dense')


@pytest.mark.parametrize('means', [1e5, 1e8])
def test_large_means_do_not_change_augmented_rank_units(means):
    parity(panel(means=means), path='dense')


@pytest.mark.parametrize('ratio,path', [(1e-6 - 1e-12, 'dense'), (1e-6, 'dense'),
                                       (1e-6 + 1e-12, 'projected')])
def test_strict_frozen_computation_guard(monkeypatch, ratio, path):
    monkeypatch.setattr(replay, 'rank_certificate', lambda *args: (ratio, 1., ratio))
    parity(panel(), path=path)


def test_empty_and_no_selected_writer_dispositions():
    parity(None, path='dense')
    parity(panel(), {}, 'dense')


def test_reference_cache_is_independent_and_protects_raw_inputs(monkeypatch):
    p = panel(); calls = []
    original_project = replay.project_block
    def count(a, b):
        calls.append(len(b)); return original_project(a, b)
    monkeypatch.setattr(replay, 'project_block', count)
    # Production's demeaned blocks are not a reference input.
    p['blocks'] = [(k, np.zeros_like(a), np.zeros_like(b)) for k, a, b in p['blocks']]
    parity(p, path='projected'); parity(p, {'w0': 2, 'w2': 3}, 'projected')
    assert len(calls) == len(p['raw_blocks'])
    assert all(not a.flags.writeable and not b.flags.writeable for _, a, b in p['raw_blocks'])


def test_fast_path_avoids_dense_and_projected_failure_falls_back(monkeypatch):
    p = panel(); expected = old.fit(p, None, True)
    with monkeypatch.context() as m:
        m.setattr(replay, 'dense', lambda *args: pytest.fail('unexpected large dummy solve'))
        parity(p, path='projected')
    monkeypatch.setattr(replay, 'rank_certificate', lambda *args: (_ for _ in ()).throw(np.linalg.LinAlgError('constructed')))
    assert replay.fit(p) == expected


@pytest.mark.parametrize('plant', [0., .5])
def test_actual_primary_and_reach_panels_all_terms_and_counts(plant):
    rows = fixture.carryover(plant, pairs=240, writers=8, seed=1414)
    panels = new.prepare(rows)
    assert len(panels['under10']['terms']) == 4
    assert len(panels['same_valence_reach']['terms']) > 4
    for counts in [None, {f'w{i:04}': i % 3 for i in range(8)}]:
        for name, p in panels.items():
            trace = parity(p, counts)
            if name == 'under10': assert trace['path'] == 'projected'
    production, error = new.fit(panels['under10'])
    expected, other = old.fit(panels['under10'])
    assert (production, error) == (expected, other)


def surveys():
    rng = np.random.default_rng(1414); rows = []
    prompts = ['anger', 'fear', 'sadness', 'guilt', 'shame', 'disgust', 'fear', 'anger']
    for writer in range(8):
        for i, prompt in enumerate(prompts):
            rows.append({'text_id': f'w{writer}t{i}', 'prolific_id': f'w{writer}',
                'emotion': prompt, 'timestamp': f'2021/01/01 12:{i*6:02}:00 PM CET',
                'round_number': 'round-2', 'source_qualified': True,
                'intensity': int(rng.integers(1, 6)), 'emotion_duration_rank': int(rng.integers(1, 6)),
                'N': 2. + writer / 3,
                **{feeling: int(rng.integers(1, 6)) for feeling in old.PRIOR}})
    return pd.DataFrame(rows)


def test_unmodified_seed_source_rows_and_checkpoint_prefix(tmp_path):
    frame = surveys(); identity = {'eligible_rounds': ['round-2'], 'constructed': True}
    config = {'source_scope': 'real-event-primary', 'draws': 2000, 'max_new_draws': 3}
    old_rows, old_counts = old.pairs(frame, identity['eligible_rounds'])
    new_rows, new_counts = new.pairs(frame, identity['eligible_rounds'])
    pd.testing.assert_frame_equal(old_rows, new_rows); assert old_counts == new_counts
    assert oldrun.settings('IN14', config) == newrun.settings('IN14', config)
    for j in (0, 1, 1999):
        assert oldrun.resample(['a', 'b', 'c'], 'IN14', j) == newrun.resample(['a', 'b', 'c'], 'IN14', j)
    for name, runner, independent in [('old', oldrun, False), ('new', newrun, False), ('replay', newrun, True)]:
        answer = runner.calculate('IN14', frame, identity, tmp_path/name, config, independent)
        assert answer['completed'] == 3 and answer['verified'] is False
    saved = {name: seal.read(tmp_path/name/'DRAWS.json') for name in ('old', 'new', 'replay')}
    assert saved['old']['point'] == saved['new']['point']
    assert saved['old']['draws'] == saved['new']['draws']
    newrun.common.compare(saved['new']['point'], saved['replay']['point'])
    newrun.common.compare(saved['new']['draws'], saved['replay']['draws'])


def test_semantic_diff_and_dependency_closure():
    def functions(module):
        return {n.name: n for n in ast.parse(Path(module.__file__).read_text()).body if isinstance(n, ast.FunctionDef)}
    before, after = functions(old), functions(new)
    assert before.keys() == after.keys()
    for name in before:
        if name != 'fit': assert ast.dump(before[name]) == ast.dump(after[name])
    class Mask(ast.NodeTransformer):
        def visit_If(self, node):
            if isinstance(node.test, ast.Name) and node.test.id == 'independent':
                node.body = [ast.Pass()]
            return self.generic_visit(node)
    assert ast.dump(Mask().visit(before['fit'])) == ast.dump(Mask().visit(after['fit']))
    before, after = functions(oldrun), functions(newrun)
    for name in before:
        if name != 'dependencies': assert ast.dump(before[name]) == ast.dump(after[name])
    dependencies = newrun.dependencies()
    for module in (new, replay, old, newrun, entry):
        assert str(Path(module.__file__).resolve()) in dependencies
    assert newrun.in16 is oldrun.in16 and replay.original is old
    assert replay.RCOND == 1e-11 and replay.FAST_RATIO == 1e-6
