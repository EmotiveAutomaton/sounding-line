from pathlib import Path

import pytest

from runners.stage9 import neural_operations, recipe_selection, selected_recipe
from runners.stage9.common import closure, digest, read, write
from runners.stage9.training_jobs import FITS


@pytest.fixture
def selected(tmp_path, monkeypatch):
    monkeypatch.setattr(selected_recipe, 'ROOT', tmp_path)
    monkeypatch.setattr(selected_recipe, 'inside', lambda path: Path(path).resolve())
    monkeypatch.setattr(selected_recipe, 'training_root', lambda f, r, s: tmp_path / f / r / str(s))
    rows = [{'family': f, 'recipe': r, 'seed': s, 'status': 'COMPLETE',
             'score': -1. if r == 'both_expert' else (-.01 if s == 9001 else -10.),
             'development_sha256': f, 'adapter_sha256': f + r + str(s), 'complete_sha256': f + r + str(s) + '-fit'}
            for f, r, s in FITS]
    monkeypatch.setattr(recipe_selection, 'fitting_rows', lambda *args: (rows, 'm' * 64))
    def package(path, family, scope):
        recipe, seed = path.parent.name, int(path.name)
        row = next(r for r in rows if (r['family'], r['recipe'], r['seed']) == (family, recipe, seed))
        return path / 'adapter', row['adapter_sha256'], row['complete_sha256']
    monkeypatch.setattr(neural_operations, 'training_package', package)
    directory = tmp_path / 'private/scientific-recipe-selection/v1'
    def commit():
        identity = {'cell_identity': 'c' * 64, 'operation': 'development-recipe-selection-v1', 'scope': 'scientific',
                    'fitting_manifest_sha256': 'm' * 64, 'fitting_rows_sha256': digest(rows)}
        result = recipe_selection.choose(rows, 'scientific')
        write(directory / 'IDENTITY.json', identity)
        write(directory / 'FITTING_ROWS.json', rows)
        write(directory / 'SELECTION.json', result)
        reseal()
    def reseal():
        identity = read(directory / 'IDENTITY.json')
        result = read(directory / 'SELECTION.json')
        write(directory / 'COMPLETE.json', {'cell_identity': identity['cell_identity'], 'identity_sha256': digest(identity),
              'execution_complete': True, 'development_only': True, 'scientific_admission': False,
              'families': {f: {k: g[k] for k in ('selected', 'selected_recipe', 'selected_seeds', 'reason')}
                           for f, g in result['families'].items()},
              'outputs': closure([directory / n for n in ('IDENTITY.json', 'FITTING_ROWS.json', 'SELECTION.json')])})
    commit()
    return directory, rows, commit, reseal


def resolve(fixture, seed=9001, family='qwen', scope='scientific'):
    directory = fixture[0]
    return selected_recipe.resolve(directory, directory / 'fits.json', directory / 'queue', family, seed, scope)


@pytest.mark.parametrize('seed', [9001, 9002, 9003])
def test_selects_recipe_mean_and_retains_each_original_seed(selected, seed):
    training, identity = resolve(selected, seed)
    assert training.parts[-3:] == ('qwen', 'both_expert', str(seed))
    assert identity['selected_seeds'] == [9001, 9002, 9003]
    assert identity['seed'] == seed and identity['recipe'] == 'both_expert'


@pytest.mark.parametrize('seed,scope', [(True, 'scientific'), (9001., 'scientific'), (997901, 'scientific'),
                                        (9001, 'pilot'), (9001, 'invented')])
def test_wrong_seed_or_scope_refuses(selected, seed, scope):
    with pytest.raises(ValueError, match='declared family'):
        resolve(selected, seed, scope=scope)


def test_partial_and_absent_recipe_never_selects_surviving_seed(selected):
    _, rows, commit, _ = selected
    for row in rows:
        if row['family'] == 'qwen' and row['seed'] == 9003:
            row['status'] = 'FAILED'
    commit()
    with pytest.raises(ValueError, match='no complete selected'):
        resolve(selected)
    assert resolve(selected, family='smollm')[1]['selected_seeds'] == [9001, 9002, 9003]


@pytest.mark.parametrize('attack', ['winner', 'rows', 'manifest', 'summary', 'output', 'incomplete'])
def test_rehashed_inconsistent_selection_refuses(selected, attack):
    directory, _, _, reseal = selected
    if attack == 'winner':
        result = read(directory / 'SELECTION.json')
        result['families']['qwen']['selected_recipe'] = 'both_mixed'
        write(directory / 'SELECTION.json', result)
    elif attack == 'rows':
        rows = read(directory / 'FITTING_ROWS.json'); rows[0]['score'] += 1
        write(directory / 'FITTING_ROWS.json', rows)
    elif attack == 'manifest':
        identity = read(directory / 'IDENTITY.json'); identity['fitting_manifest_sha256'] = 'wrong'
        write(directory / 'IDENTITY.json', identity)
    reseal()
    done = read(directory / 'COMPLETE.json')
    if attack == 'summary': done['families']['qwen']['selected_seeds'] = [9001]
    if attack == 'output': done['outputs'] = closure([directory / 'IDENTITY.json'])
    if attack == 'incomplete': done['execution_complete'] = False
    write(directory / 'COMPLETE.json', done)
    with pytest.raises(ValueError, match='selection'):
        resolve(selected)


def test_changed_checkpoint_refuses_before_reader_execution(selected, monkeypatch):
    monkeypatch.setattr(neural_operations, 'training_package', lambda *args: (None, 'changed', 'changed'))
    with pytest.raises(ValueError, match='training package differs'):
        resolve(selected)


@pytest.mark.parametrize('bundle,training,kind', [((None, 'm', 'q', 9001), None, 'fitted'),
    (('s', None, 'q', 9001), None, 'fitted'), (('s', 'm', None, 9001), None, 'fitted'),
    (('s', 'm', 'q', None), None, 'fitted'), (('s', 'm', 'q', 9001), 'other', 'fitted'),
    (('s', 'm', 'q', 9001), None, 'archive'), (('s', 'm', 'q', 9001), None, 'base')])
def test_ambiguous_execution_arguments_refuse(bundle, training, kind):
    with pytest.raises(ValueError, match='selected execution'):
        selected_recipe.execution_selection(*bundle, training=training, package_kind=kind, family='qwen', scope='scientific')


def test_existing_direct_path_is_preserved():
    assert selected_recipe.execution_selection(None, None, None, None, training=Path('fit'),
        package_kind='fitted', family='qwen', scope='scientific') == (Path('fit'), None)


def mapping(fixture):
    path = fixture[0] / 'CALIBRATIONS.json'
    rows = [{'family': f, 'recipe': r, 'seed': s, 'calibration': str(path.parent / f / r / str(s))} for f, r, s in FITS]
    write(path, {'scope': 'scientific', 'calibrations': rows})
    _, selection = resolve(fixture, 9002)
    identity = {'scope': 'scientific', 'family': 'qwen', 'package_kind': 'fitted', 'recipe_selection': selection,
                'adapter_sha256': selection['adapter_sha256'], 'training_complete_sha256': selection['training_complete_sha256']}
    return path, identity


def test_calibration_uses_selected_recipe_and_exact_seed_without_other_outcomes(selected):
    path, identity = mapping(selected)
    calibration, provenance = selected_recipe.calibration_path(path, identity, 'scientific')
    assert calibration.parts[-3:] == ('qwen', 'both_expert', '9002')
    assert provenance['recipe_selection'] == identity['recipe_selection']
    assert not calibration.exists()  # Resolution never reads another package's outcome.


@pytest.mark.parametrize('attack', ['missing', 'duplicate', 'scope', 'seed', 'target', 'checkpoint', 'unselected'])
def test_calibration_map_and_target_substitution_refuse(selected, attack):
    path, identity = mapping(selected); plan = read(path)
    if attack == 'missing': plan['calibrations'].pop()
    if attack == 'duplicate': plan['calibrations'][0]['calibration'] = plan['calibrations'][1]['calibration']
    if attack == 'scope': plan['scope'] = 'pilot'
    if attack == 'seed': identity['recipe_selection']['seed'] = 9003
    if attack == 'target': identity['family'] = 'smollm'
    if attack == 'checkpoint': identity['adapter_sha256'] = 'different'
    if attack == 'unselected': del identity['recipe_selection']
    write(path, plan)
    with pytest.raises(ValueError): selected_recipe.calibration_path(path, identity, 'scientific')


def test_neural_runner_resolves_before_inference_and_records_selection(selected, monkeypatch):
    directory = selected[0]; captured = {}
    monkeypatch.setattr(neural_operations, 'ROOT', directory)
    monkeypatch.setattr(neural_operations, 'inside', lambda p: Path(p).resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY', 'a' * 64)
    monkeypatch.setattr(neural_operations, 'case_inputs', lambda *args: ([], 'discovery', 'cases'))
    class Captured(Exception): pass
    def capture(path, identity):
        captured.update(identity); raise Captured()
    monkeypatch.setattr(neural_operations, 'Units', capture)
    with pytest.raises(Captured):
        neural_operations.run(directory / 'private/scientific-neural-operations/test', operation='supplied_kernel',
            family='qwen', training=None, cases=directory, scope='scientific', recipe_selection=directory,
            selection_manifest=directory / 'fits.json', selection_queue=directory / 'queue', selection_seed=9002)
    assert captured['recipe_selection']['seed'] == 9002
    assert captured['recipe_selection']['selected_seeds'] == [9001, 9002, 9003]
    assert captured['adapter_sha256'] == captured['recipe_selection']['adapter_sha256']
