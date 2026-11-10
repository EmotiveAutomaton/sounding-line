"""Complete native parity of original comfort-grid and publication successor.

DESIGN CHECK: LESSONS 3-5. Every known signed/null and declared-grid result
must equal the existing qualified handler result; full fresh replay must
reproduce every record. No population, numerical gate or draw count changes.
"""
from pathlib import Path
import json
from . import week5_sp_grid_counted_fixture_v1 as baseline
from . import week5_sp_publication_v1 as successor
from . import week5_qualification_io as publication


def execute(output, inputs, config):
    if inputs or config != {'constructed_fixture': True}:
        raise ValueError('Complete constructed grid required')
    output = Path(output)
    reference = output / 'reference'
    original = baseline.execute(reference, inputs, config)
    cases = []
    for card in ('SP1', 'SP2', 'SP3'):
        for sign in (-1, 0, 1):
            name = f'{card}-{sign}'
            cases.append((name, reference / 'known' / name / 'constructed.parquet',
                          {'phase': card, 'draws': 2000}, reference / 'known' / name / 'run'))
    for cfg in baseline.core.grid():
        cases.append((cfg['cell'], reference / 'grid' / 'comfort.parquet', cfg,
                      reference / 'grid' / cfg['cell']))
    checks = []
    for name, source, cfg, expected in cases:
        root = output / 'adapted' / name
        result = successor.execute(root, {'data': str(source)}, cfg)
        if result != json.loads((expected / 'RESULT.json').read_text('utf8')):
            raise ValueError('Publication successor changed numerical result: ' + name)
        if not successor.verify(root, {'data': str(source)}, cfg)['verified']:
            raise ValueError('Complete adapted replay failed: ' + name)
        checks.append(name)
    result = dict(passed=True, constructed_only=True, baseline=original,
                  complete_equal_cases=checks, scientific_admission=False)
    publication.write_json(output / 'FIXTURE.json', result)
    return result


def verify(output, inputs, config):
    output = Path(output)
    replay = output / 'independent-replay'
    if execute(replay, inputs, config) != json.loads((output / 'FIXTURE.json').read_text('utf8')):
        raise ValueError('Complete publication qualification receipt differs')
    for name in ('reference', 'adapted'):
        if baseline.records(output / name) != baseline.records(replay / name):
            raise ValueError('Complete result-bank replay differs')
    return dict(verified=True, constructed_only=True, complete_grid_and_known_answer_parity=True,
                every_result_independently_replayed=True, scientific_admission=False)
