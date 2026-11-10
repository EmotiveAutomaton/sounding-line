"""Qualification-only MD3 publication adapter and explicit full-bank census.

No likelihood, optimizer, reference, source, dose, seed or gate is changed.
The existing fixture remains immutable and must pass its original decisions.
"""
from pathlib import Path
from . import week5_md3_followup_fixture as original
from . import week5_qualification_io as publication


def bank_census(output, card, complete=False):
    output = Path(output)
    gammas = original.study.GAMMAS if card == 'MD3.s' else (.65,)
    result = []
    for gamma in gammas:
        root = output / f'gamma-{gamma:.2f}'
        draws = sorted(p.name for p in root.glob('draw-*.json') if not p.name.endswith('.sha256.json'))
        nulls = sorted(p.name for p in root.glob('null-*.json') if not p.name.endswith('.sha256.json'))
        if draws != [f'draw-{i:04d}.json' for i in range(len(draws))] or len(draws) > 2000:
            raise ValueError('MD3 participant draw bank is not a complete ordered prefix')
        if nulls != [f'null-{i:02d}.json' for i in range(len(nulls))] or len(nulls) > 20:
            raise ValueError('MD3 dynamic-null bank is not a complete ordered prefix')
        if complete and (len(draws) != 2000 or len(nulls) != 20):
            raise ValueError('MD3 fixture lacks its entire declared banks')
        for name in draws + nulls:
            path = root / name
            if publication.sha(path) != original.study.read(path.with_suffix('.sha256.json'))['sha256']:
                raise ValueError('MD3 fixture draw/null checkpoint changed')
        for name in ('POINT.npz', 'NULL_FIT.npz'):
            path = root / name
            if path.exists() and publication.sha(path) != original.study.read(path.with_suffix('.sha256.json'))['sha256']:
                raise ValueError('MD3 fitted checkpoint changed or is unsealed')
        result.append(dict(gamma=gamma, draws=len(draws), nulls=len(nulls)))
    return result


def execute(output, inputs, config):
    output = Path(output)
    if config.get('draws', 2000) != 2000:
        raise ValueError('Full MD3 draw count required')
    manifest = original.study.read(inputs['manifest'])
    if manifest.get('participants') != 96 or manifest.get('parent_primary', {}).get('gamma') != .65:
        raise ValueError('Frozen constructed MD3 population/parent reference differs')
    bank_census(output, config['phase'])
    with publication.publication([(original.study.core, 'save_json')], [(original.study, 'save_fit')]):
        result = original.execute(output, inputs, config)
        counts = bank_census(output, config['phase'], result.get('status') != 'yielded')
        publication.write_json(output / 'QUALIFICATION_PROGRESS.json', dict(phase='MD3_complete_fixture',
            completed=sum(row['draws'] for row in counts), total=2000 * len(counts), cells=counts,
            execute_pilot_complete=all(row['draws'] >= 100 and row['nulls'] == 20 for row in counts),
            original_wrapper_sha256=publication.sha(original.__file__), publication_adapter_sha256=publication.sha(publication.__file__)))
    return result


def verify(output, inputs, config):
    output = Path(output)
    value = execute(output / 'independent-replay', inputs, config)
    if value.get('status') == 'yielded':
        return value | dict(verified=False)
    original.study.compare_complete(output)
    if original.study.read(output / 'ARITHMETIC.json') != original.study.read(output / 'independent-replay/ARITHMETIC.json'):
        raise ValueError('MD3 independent arithmetic witness differs')
    bank_census(output, config['phase'], True)
    bank_census(output / 'independent-replay', config['phase'], True)
    return dict(verified=True, full_signed_or_null_case=True, all_2000_draws_and_20_nulls_independently_replayed=True,
                publication_adapter_only=True)
