"""Counted RF1 first-cost/first-five-percent prefix; no incomplete inference.

Uses exact global draws from the complete consumer, then freshly replays them.
Runtime accounting supplies actual costs. This wrapper invents no forecast and
does not qualify the source or release the remaining full run by itself.
"""
from pathlib import Path
from . import week5_rf_analysis_v3 as analysis
from . import week5_rf_cp_source_v1 as source


def run(output, inputs, config, reference=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    requested = config['prefix_draws']
    if type(requested) is not int or requested not in (4, 100):
        raise ValueError('RF1 prefix must be four draws or the first100 of2000')
    target = output/'analysis'
    blocks = sorted(p for p in target.glob('draw-*.json') if '.seal.' not in p.name)
    expected = [f'draw-{i:04d}.json' for i in range(0, requested, analysis.DRAW_BLOCK)]
    if [p.name for p in blocks] != expected[:len(blocks)] or len(blocks) > len(expected):
        raise ValueError('Prefix checkpoint exceeds or differs from its exact global scope')
    consumer_config = {k: v for k, v in config.items() if k != 'prefix_draws'}
    consumer_config['max_new_draw_blocks'] = len(expected)-len(blocks)
    result = analysis.produce(target, inputs, consumer_config, reference=reference)
    names = sorted(p.name for p in target.glob('draw-*.json') if '.seal.' not in p.name)
    absent_case = result['status'] == 'complete' and not names
    if names != expected and not absent_case:
        return {'status': 'yielded', 'reason': 'RF1 measured prefix checkpoint', 'scientific_admission': False}
    files = ['BINDING.json', 'ELECTION_SUPPORT.json', 'POINT.json', *names]
    receipt = {'schema': 'RF1-COUNTED-PREFIX-1', 'prefix_module_sha256': source.sha(__file__),
        'consumer_sha256': source.sha(analysis.__file__), 'requested_global_draws': requested,
        'completed_global_draws': len(names)*analysis.DRAW_BLOCK,
        'five_percent_of_registered_uncertainty': requested == 100 and len(names)*analysis.DRAW_BLOCK == 100,
        'forecast_eligible': not absent_case, 'no_case_or_below_floor_route': absent_case,
        'cost_measurement': 'external native accounting, including source load and fresh verifier',
        'files': {name: source.sha(target/name) for name in files}, 'scientific_admission': False}
    source.write_equal(output/'PREFIX.json', receipt)
    return {'status': 'complete', 'prefix_sha256': source.sha(output/'PREFIX.json'), 'scientific_admission': False}


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output)
    if not (output/'PREFIX.json').exists():
        raise ValueError('Unfinished RF1 cost prefix cannot verify')
    replay = output/'fresh-prefix-replay'
    result = run(replay, inputs, config, reference=True)
    if result['status'] == 'yielded':
        return dict(result, verified=False)
    original = analysis.read(output/'PREFIX.json')
    if (output/'PREFIX.json').read_bytes() != (replay/'PREFIX.json').read_bytes():
        raise ValueError('Fresh prefix receipt differs')
    for name, pin in original['files'].items():
        if source.sha(output/'analysis'/name) != pin or source.sha(replay/'analysis'/name) != pin:
            raise ValueError('Fresh original-global-draw prefix differs')
    return {'verified': True, 'complete_requested_prefix_replayed': True,
        'full_uncertainty_complete': False, 'scientific_admission': False}
