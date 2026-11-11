"""Original IN sensitivity with isolated publication and complete replay checks.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7 reread. Exact constructed nulls
must remain zero and signed alternatives recover their fixed dose; high noise
must retain its failed sensitivity gate. Every world and refit remains fixed.
Changed, orphaned or non-prefix checkpoints fail closed. An original numerical
failure remains an invalid result, never a shortened successful calibration.
"""
from pathlib import Path
import json
from . import week5_in_followup as original
from . import week5_qualification_io as publication

NAMES = tuple(f'{dose}-{world:03d}.json' for dose in (-2, -1, 0, 1, 2) for world in range(100))


def world_bank(output, complete=False):
    root = Path(output) / 'worlds'
    actual = {p.name for p in root.glob('*') if p.is_file()}
    names = [name for name in NAMES if name in actual]
    expected = set(names) | {Path(name).with_suffix('.seal.json').name for name in names}
    if names != list(NAMES[:len(names)]) or actual != expected or (complete and len(names) != 500):
        raise ValueError('IN bank has missing, orphaned, extra or non-prefix records')
    records = {}
    for index, name in enumerate(names):
        path = root / name
        seal = json.loads(path.with_suffix('.seal.json').read_text('utf8'))
        if publication.sha(path) != seal['sha256']:
            raise ValueError('IN checkpoint changed')
        record = json.loads(path.read_text('utf8'))
        fit = record['fit']
        if not isinstance(record.get('binding'), str) or len(record['binding']) != 64:
            raise ValueError('IN world lacks its original source binding')
        if fit.get('status') == 'ok':
            if fit.get('draws') != 2000:
                raise ValueError('IN world lacks all 2,000 refits')
        elif complete or index != len(names) - 1:
            raise ValueError('IN bank continues after a failed fit')
        records[name] = record
    return records


def numerical_config(output, config):
    if set(config) - {'worlds', 'draws'} or config.get('worlds', 100) != 100 or config.get('draws', 2000) != 2000:
        raise ValueError('Full fixed IN sensitivity grid required')
    count = len(world_bank(output))
    return dict(worlds=100, draws=2000, max_new_worlds=25 - count if count < 25 else 500)


def calibrate(x, y, clusters, contrast, bar, config, output):
    """Same numerical entry for human matrices and constructed failure control."""
    output = Path(output)
    cfg = numerical_config(output, config)
    with publication.publication([(original.core, 'write_json')]):
        result = original.calibrate(x, y, clusters, contrast, bar, cfg, output)
    world_bank(output, complete=result.get('status') == 'ok')
    return result


def contract(inputs, config):
    phase = config.get('phase')
    keys = {'generation'} if phase == 'IN3.ic' else {'generation', 'validation'} if phase == 'IN4.ic' else set()
    if not keys or set(inputs) != keys or set(config) - {'phase', 'worlds', 'draws'}:
        raise ValueError('Exact registered IN sensitivity inputs and configuration required')
    return {k: v for k, v in config.items() if k != 'phase'}


def execute(output, inputs, config):
    output = Path(output)
    numerical = contract(inputs, config)
    # Validate the grid before source access, then retain the original projection.
    numerical_config(output, numerical)
    generation = original.pd.read_parquet(inputs['generation'])
    validation = original.pd.read_parquet(inputs['validation']) if config['phase'] == 'IN4.ic' else None
    result = calibrate(*original.matrix(generation, validation, config['phase'].split('.')[0]), numerical, output)
    result['card'] = config['phase']
    if result.get('status') != 'yielded':
        publication.write_json(output / 'RESULT.json', result)
    return result


def verify(output, inputs, config):
    output = Path(output)
    contract(inputs, config)
    saved = json.loads((output / 'RESULT.json').read_text('utf8'))
    bank = world_bank(output, complete=saved.get('status') == 'ok')
    result = execute(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return result | dict(verified=False)
    if result != saved or bank != world_bank(output / 'independent-replay', complete=result.get('status') == 'ok'):
        raise ValueError('IN complete summary or individual world replay differs')
    return dict(verified=True, all_worlds_and_cluster_draws_replayed=True,
                every_saved_world_independently_replayed=True)
