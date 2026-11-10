"""Qualification-only successor: exact source contracts and every world replay.

The preserved IN calibrator performs all 100 worlds at each of five fixed
doses, each with its unchanged 2,000 cluster refits. Only publication and
qualification checks differ. Original code, estimands and failed fits stay.
"""
from pathlib import Path
from . import week5_in_sensitivity_counted_fixture as original
from . import week5_qualification_io as publication

DOSES = (-2, -1, 0, 1, 2)
NAMES = tuple(f'{dose}-{world:03d}.json' for dose in DOSES for world in range(100))


def validate(inputs, config):
    case = config['case']
    keys = {'fixture_manifest', 'generation'} if case == 'IN3' else {'fixture_manifest', 'generation', 'validation'} if case == 'IN4' else {'fixture_manifest', 'noise'} if case == 'FAILURE' else set()
    if not keys or set(inputs) != keys:
        raise ValueError('Exact constructed branch source roster required')
    manifest = original.read(inputs['fixture_manifest'])
    if set(manifest['sha256']) != keys - {'fixture_manifest'}:
        raise ValueError('Every constructed input must have a branch pin')
    if manifest.get('constructed_only') is not True or manifest['case'] != case:
        raise ValueError('Constructed IN branch identity differs')
    for name, expected in manifest['sha256'].items():
        if publication.sha(inputs[name]) != expected:
            raise ValueError('Constructed IN source changed')


def world_bank(output, complete=False):
    root = Path(output) / 'worlds'
    actual = {path.name for path in root.glob('*.json')}
    worlds = [name for name in NAMES if name in actual]
    if worlds != list(NAMES[:len(worlds)]):
        raise ValueError('IN world bank is not a complete ordered prefix')
    expected = set(worlds) | {Path(name).with_suffix('.seal.json').name for name in worlds}
    if actual != expected or (complete and len(worlds) != 500):
        raise ValueError('IN world bank has missing, orphaned or extra records')
    records = {}
    for name in worlds:
        path = root / name
        if publication.sha(path) != original.read(path.with_suffix('.seal.json'))['sha256']:
            raise ValueError('IN world checkpoint changed')
        record = original.read(path)
        if record['fit'].get('status') != 'ok' or record['fit'].get('draws') != 2000:
            raise ValueError('A counted fixture world lacks all 2,000 successful refits')
        records[name] = record
    return records


def execute(output, inputs, config):
    output = Path(output)
    validate(inputs, config)
    world_bank(output)
    with publication.publication([(original.follow.core, 'write_json')]):
        result = original.perform(output, inputs, config)
        bank = world_bank(output, result.get('status') != 'yielded')
        publication.write_json(output / 'QUALIFICATION_PROGRESS.json', dict(phase='IN_full_sensitivity', completed=len(bank), total=500,
            worlds_per_dose=100, refits_per_world=2000, execute_pilot_complete=len(bank) >= 25,
            original_wrapper_sha256=publication.sha(original.__file__), publication_adapter_sha256=publication.sha(publication.__file__)))
    return result


def verify(output, inputs, config):
    output = Path(output)
    result = execute(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return result | dict(verified=False)
    if result != original.read(output / 'RESULT.json'):
        raise ValueError('Full sensitivity summary differs')
    if world_bank(output, True) != world_bank(output / 'independent-replay', True):
        raise ValueError('Every fixed world fit and interval must independently replay')
    return dict(verified=True, constructed_only=True, full_100_worlds_per_effect_and_2000_draws=True,
                all_500_world_records_independently_replayed=True)
