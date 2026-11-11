"""Native IN parity with the production watcher pause envelope.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7. The original IN3/IN4 exact
constructed signed/null cases must pass and original high-noise case must fail.
All 500 worlds and 2,000 refits remain. Any source, summary or world difference
refuses qualification; both actual handlers retain their 25-world pilot.
"""
from pathlib import Path
import json
import numpy as np
from . import week5_in_sensitivity_fixture_v2 as baseline
from . import week5_in_ic_publication_v1 as candidate
from . import week5_qualification_io as publication


def compare(left, right, complete=False):
    a, b = baseline.world_bank(left, complete), candidate.world_bank(right, complete)
    common = min(len(a), len(b))
    if list(a)[:common] != list(b)[:common] or any(a[name] != b[name] for name in list(a)[:common]):
        raise ValueError('IN publication changed an individual world')
    if complete and json.loads((Path(left) / 'RESULT.json').read_text('utf8')) != json.loads((Path(right) / 'RESULT.json').read_text('utf8')):
        raise ValueError('IN publication changed the complete summary')
    return min(len(a), len(b))


def args(inputs, config):
    if set(config) != {'case', 'worlds', 'draws'} or config['worlds'] != 100 or config['draws'] != 2000:
        raise ValueError('Full constructed IN publication configuration required')
    baseline.validate(inputs, config)
    return {k: v for k, v in inputs.items() if k != 'fixture_manifest'}, dict(phase=config['case'] + '.ic', worlds=100, draws=2000)


def candidate_execute(output, inputs, config):
    data, cfg = args(inputs, config)
    if config['case'] != 'FAILURE':
        return candidate.execute(output, data, cfg)
    with np.load(data['noise'], allow_pickle=False) as source:
        result = candidate.calibrate(source['x'], source['y'], source['clusters'], source['contrast'], .1,
                                     dict(worlds=100, draws=2000), output)
    result['card'] = 'constructed-noise'
    if result.get('status') != 'yielded':
        publication.write_json(Path(output) / 'RESULT.json', result)
    return result


def execute(output, inputs, config):
    output = Path(output)
    args(inputs, config)
    left = baseline.execute(output / 'baseline', inputs, config)
    right = candidate_execute(output / 'candidate', inputs, config)
    yielded = any(r.get('status') == 'yielded' for r in (left, right))
    count = compare(output / 'baseline', output / 'candidate', complete=not yielded)
    publication.write_json(output / 'QUALIFICATION_PROGRESS.json', dict(completed=count, total=500, constructed_only=True))
    if yielded:
        return dict(status='yielded', complete_card=False, phase='IN_publication_execute', completed=count, total=500)
    if left != right or right['sensitivity_pass'] != (config['case'] != 'FAILURE'):
        raise ValueError('Original constructed IN sensitivity gate changed')
    result = dict(constructed_only=True, case=config['case'], exact_summary_and_all_worlds=True, worlds=500, draws_per_world=2000)
    publication.write_json(output / 'RESULT.json', result)
    return result


def verify(output, inputs, config):
    output = Path(output)
    data, cfg = args(inputs, config)
    left = baseline.verify(output / 'baseline', inputs, config)
    if config['case'] == 'FAILURE':
        right = candidate_execute(output / 'candidate/independent-replay', inputs, config)
        if right.get('status') != 'yielded':
            if right != json.loads((output / 'candidate/RESULT.json').read_text('utf8')):
                raise ValueError('High-noise replay summary differs')
            compare(output / 'candidate', output / 'candidate/independent-replay', True)
            right = dict(verified=True)
    else:
        right = candidate.verify(output / 'candidate', data, cfg)
    yielded = any(r.get('status') == 'yielded' for r in (left, right))
    count = compare(output / 'baseline/independent-replay', output / 'candidate/independent-replay', complete=not yielded)
    if yielded:
        return dict(status='yielded', verified=False, complete_card=False, phase='IN_publication_verify', completed=count, total=500)
    if left.get('verified') is not True or right.get('verified') is not True:
        raise ValueError('Both complete IN verification paths required')
    compare(output / 'baseline', output / 'candidate', True)
    expected = dict(constructed_only=True, case=config['case'], exact_summary_and_all_worlds=True, worlds=500, draws_per_world=2000)
    if json.loads((output / 'RESULT.json').read_text('utf8')) != expected:
        raise ValueError('IN publication qualification receipt changed')
    return dict(verified=True, actual_handlers_replayed=True, all_world_records_equal=True, constructed_only=True)
