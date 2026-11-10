"""Counted qualification of the complete already-declared IN texture grid.

DESIGN CHECK: LESSONS 3-5. Original signed/null and rank controls must pass;
every declared variant must run and reproduce every result in a fresh process.
No human data, numerical change, cell selection or reduced refit bank.
"""
from pathlib import Path
import json
from . import week5_in as core
from . import week5_in_fixture_v2 as primary
from . import week5_in4_fixture as agreement
from . import week5_in_sp_grid_fixture as grid
from . import week5_qualification_io as publication


def validate(inputs, config):
    if inputs or config != {'constructed_fixture': True}:
        raise ValueError('Exact complete constructed qualification required')


def execute(output, inputs, config):
    validate(inputs, config)
    output = Path(output)
    with publication.publication([(core, 'write_json')]):
        p = primary.run(output / 'primary', draws=2000)
        a = agreement.run(output / 'agreement', draws=2000)
        g = grid.in_grid(output / 'grid')
        expected = [cell['cell'] for cell in core.grid()]
        if not p['passed'] or not a['passed'] or not g['passed']:
            raise ValueError('Known-answer qualification failed')
        if [cell['cell'] for cell in g['declared_grid']] != expected:
            raise ValueError('Complete declared grid was not exercised')
        result = dict(passed=True, constructed_only=True, primary=p,
                      agreement=a, grid=g, scientific_admission=False)
        publication.write_json(output / 'FIXTURE.json', result)
    return result


def records(root):
    return {p.relative_to(root).as_posix(): json.loads(p.read_text('utf8'))
            for p in root.rglob('RESULT.json')}


def verify(output, inputs, config):
    output = Path(output)
    replay = output / 'independent-replay'
    expected = {}
    for name in ('primary', 'agreement', 'grid'):
        expected[name] = records(output / name)
    result = execute(replay, inputs, config)
    if result != json.loads((output / 'FIXTURE.json').read_text('utf8')):
        raise ValueError('Complete qualification receipt differs')
    for name in expected:
        if not expected[name] or expected[name] != records(replay / name):
            raise ValueError('Complete constructed result bank differs: ' + name)
    return dict(verified=True, constructed_only=True,
                complete_original_grid=True, all_result_records_replayed=True,
                signed_null_and_rank_controls=True, scientific_admission=False)
