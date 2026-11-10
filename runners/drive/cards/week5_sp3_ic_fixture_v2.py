"""Qualification successor independently replaying SP3's arithmetic witness.

All numeric handlers, doses, worlds and bootstrap arrays are preserved. New
checks bind each source/case, every checkpoint and both arithmetic executions.
"""
from pathlib import Path
import numpy as np
from . import week5_sp3_ic_fixture as original
from . import week5_qualification_io as publication

NAMES = tuple(f'{dose}-{world:03d}.npz' for dose in (-2, -1, 0, 1, 2) for world in range(100))


def world_bank(output, complete=False):
    root = Path(output) / 'worlds'
    actual = {path.name for path in root.glob('*') if path.is_file()}
    names = [name for name in NAMES if name in actual]
    if names != list(NAMES[:len(names)]):
        raise ValueError('SP3 world bank is not a complete ordered prefix')
    expected = set(names) | {Path(name).with_suffix('.sha256.json').name for name in names}
    if actual != expected or (complete and len(names) != 500):
        raise ValueError('SP3 world bank has missing, orphaned or extra records')
    for name in names:
        path = root / name
        seal = original.json.loads(path.with_suffix('.sha256.json').read_text('utf8'))
        if publication.sha(path) != seal['sha256']:
            raise ValueError('SP3 world checkpoint changed')
        with np.load(path, allow_pickle=False) as data:
            if set(data.files) != {'values', 'point'} or data['values'].shape != (2000,) or not np.isfinite(data['values']).all() or not np.isfinite(data['point']).all():
                raise ValueError('SP3 world must retain every finite bootstrap estimate')
    return names


def execute(output, inputs, config):
    output = Path(output)
    if set(inputs) != {'data', 'fixture_manifest'} or set(config) - {'case', 'max_wall_seconds'}:
        raise ValueError('Exact SP3 constructed qualification contract required')
    original.check_inputs(inputs, config)
    world_bank(output)
    with publication.publication([(original.parent, 'write')]):
        result = original.execute(output, inputs, config)
        names = world_bank(output, result.get('status') != 'yielded')
        publication.write_json(output / 'QUALIFICATION_PROGRESS.json', dict(phase='SP3_full_sensitivity', completed=len(names), total=500,
            worlds_per_dose=100, refits_per_world=2000, execute_pilot_complete=len(names) >= 25,
            original_wrapper_sha256=publication.sha(original.__file__), publication_adapter_sha256=publication.sha(publication.__file__)))
    return result


def verify(output, inputs, config):
    output = Path(output)
    actual = execute(output / 'independent-replay', inputs, config)
    if actual.get('status') == 'yielded':
        return actual | dict(verified=False)
    read = lambda path: original.json.loads(path.read_text('utf8'))
    if actual != read(output / 'RESULT.json') or read(output / 'ARITHMETIC.json') != read(output / 'independent-replay/ARITHMETIC.json'):
        raise ValueError('Full SP3 numerical or independent arithmetic proof differs')
    left, right = world_bank(output, True), world_bank(output / 'independent-replay', True)
    if left != right:
        raise ValueError('Full SP3 world roster differs')
    for name in left:
        with np.load(output / 'worlds' / name, allow_pickle=False) as a, np.load(output / 'independent-replay/worlds' / name, allow_pickle=False) as b:
            if any(not np.array_equal(a[key], b[key]) for key in a.files):
                raise ValueError('Every SP3 world and bootstrap value must replay')
    if actual['sensitivity_pass'] != (config['case'] == 'exact'):
        raise ValueError('SP3 known sensitivity pass/failure differs')
    if config['case'] == 'exact':
        for row in actual['effects']:
            if not np.allclose(row['estimate_quantiles'], row['injected_slope'], rtol=0, atol=1e-8):
                raise ValueError('SP3 known signed or null slope differs')
    return dict(verified=True, constructed_expected_sensitivity_verified=True, full_100_worlds_all_2000_draws=True,
                independent_arithmetic_replayed=True, all_worlds_and_draws_replayed=True)
