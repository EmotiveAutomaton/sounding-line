"""Counted complete-grid qualification of the frozen thermal-comfort pipeline.

DESIGN CHECK: LESSONS 3-5. Exact signed and null buildings must recover
their known contrasts; every original grid cell must independently replay.
No human data, substituted units, reduced draw bank or numerical repair.
"""
from pathlib import Path
import json
from . import week5_sp as core
from . import week5_sp_analysis_h1 as analysis
from . import week5_sp1_h2 as location
from . import week5_sp_fixture_v2 as worlds
from . import week5_in_sp_grid_fixture as grid
from . import week5_qualification_io as publication


def execute(output, inputs, config):
    if inputs or config != {'constructed_fixture': True}:
        raise ValueError('Exact complete constructed qualification required')
    output = Path(output)
    checks = []
    with publication.publication([(core, 'write'), (location, 'write')]):
        for card, size in [('SP1', .3), ('SP2', .2), ('SP3', .02)]:
            module = location if card == 'SP1' else analysis
            for sign in (-1, 0, 1):
                folder = output / 'known' / f'{card}-{sign}'
                folder.mkdir(parents=True, exist_ok=True)
                source = folder / 'constructed.parquet'
                worlds.world(card, sign).to_parquet(source, index=False)
                args = {'data': str(source)}
                cfg = {'phase': card, 'draws': 2000}
                result = module.execute(folder / 'run', args, cfg)
                if result['status'] != 'ok' or abs(result['estimate'] - sign * size) > 1e-10:
                    raise ValueError('Exact signed/null comfort contrast failed')
                if not module.verify(folder / 'run', args, cfg)['verified']:
                    raise ValueError('Known-answer complete replay failed')
                checks.append({'card': card, 'sign': sign, 'passed': True})
        bank = grid.sp_grid(output / 'grid')
        if [c['cell'] for c in bank['declared_grid']] != [c['cell'] for c in core.grid()]:
            raise ValueError('Original declared grid is incomplete')
        result = dict(passed=True, constructed_only=True, known_answers=checks,
                      grid=bank, scientific_admission=False)
        publication.write_json(output / 'FIXTURE.json', result)
    return result


def records(root):
    return {p.relative_to(root).as_posix(): json.loads(p.read_text('utf8'))
            for p in root.rglob('RESULT.json')}


def verify(output, inputs, config):
    output = Path(output)
    expected = {name: records(output / name) for name in ('known', 'grid')}
    replay = output / 'independent-replay'
    if execute(replay, inputs, config) != json.loads((output / 'FIXTURE.json').read_text('utf8')):
        raise ValueError('Full qualification receipt differs')
    for name, original in expected.items():
        if not original or original != records(replay / name):
            raise ValueError('Every comfort result must independently replay')
    return dict(verified=True, constructed_only=True, complete_original_grid=True,
                signed_null_controls=True, all_result_records_replayed=True,
                scientific_admission=False)
