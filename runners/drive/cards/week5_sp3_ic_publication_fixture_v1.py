"""Native parity of the actual SP3 sensitivity publication entry points.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7. Existing exact and high-noise
constructed sources retain all five signed/null doses, 100 worlds and 2,000
draws. Exact must pass; high noise must fail the unchanged sensitivity gate.
Both actual handlers retain first-25-world execution and verification pauses.
Any array, summary, source or complete-bank mismatch refuses qualification.
"""
from pathlib import Path
import json
import numpy as np
from . import week5_sp3_ic_fixture_v2 as baseline
from . import week5_sp3_ic_publication_v1 as candidate
from . import week5_qualification_io as publication


def compare(left, right, complete=False):
    left, right = Path(left), Path(right)
    a, b = baseline.world_bank(left, complete), baseline.world_bank(right, complete)
    common = min(len(a), len(b))
    if a[:common] != b[:common]:
        raise ValueError('Publication changed the SP3 world roster')
    for name in a[:common]:
        with np.load(left / 'worlds' / name, allow_pickle=False) as x, np.load(right / 'worlds' / name, allow_pickle=False) as y:
            if set(x.files) != set(y.files) or any(not np.array_equal(x[key], y[key]) for key in x.files):
                raise ValueError('Publication changed a complete SP3 numerical array')
    if complete and json.loads((left / 'RESULT.json').read_text('utf8')) != json.loads((right / 'RESULT.json').read_text('utf8')):
        raise ValueError('Publication changed the complete SP3 result')
    return len(a), len(b)


def args(inputs, config):
    if set(inputs) != {'data', 'fixture_manifest'} or set(config) - {'case', 'max_wall_seconds'}:
        raise ValueError('Exact constructed publication contract required')
    baseline.original.check_inputs(inputs, config)
    return {'data': inputs['data']}, dict(phase='SP3.ic', draws=2000, worlds=100,
                                         max_wall_seconds=config.get('max_wall_seconds', 900))


def progress(output, counts, phase):
    publication.write_json(Path(output) / 'QUALIFICATION_PROGRESS.json', dict(
        phase=phase, baseline_worlds=counts[0], candidate_worlds=counts[1],
        completed=min(counts), total=500, execute_pilot_complete=min(counts) >= 25,
        constructed_only=True))


def execute(output, inputs, config):
    output = Path(output)
    data, cfg = args(inputs, config)
    left = baseline.execute(output / 'baseline', inputs, config)
    right = candidate.execute(output / 'candidate', data, cfg)
    yielded = any(result.get('status') == 'yielded' for result in (left, right))
    counts = compare(output / 'baseline', output / 'candidate', complete=not yielded)
    progress(output, counts, 'SP3_publication_execute')
    if yielded:
        return dict(status='yielded', complete_card=False, phase='publication_execute', completed=min(counts), total=500)
    if left != right or right['sensitivity_pass'] != (config['case'] == 'exact'):
        raise ValueError('Original constructed sensitivity gate changed')
    result = dict(constructed_only=True, case=config['case'], exact_summary_and_all_arrays=True,
                  worlds=500, draws_per_world=2000, source_sha256=publication.sha(inputs['data']))
    publication.write_json(output / 'RESULT.json', result)
    return result


def verify(output, inputs, config):
    output = Path(output)
    data, cfg = args(inputs, config)
    left = baseline.verify(output / 'baseline', inputs, config)
    right = candidate.verify(output / 'candidate', data, cfg)
    yielded = any(result.get('status') == 'yielded' for result in (left, right))
    counts = compare(output / 'baseline/independent-replay', output / 'candidate/independent-replay', complete=not yielded)
    progress(output / 'independent-replay', counts, 'SP3_publication_verify')
    if yielded:
        return dict(status='yielded', verified=False, complete_card=False, phase='publication_verify', completed=min(counts), total=500)
    if left.get('verified') is not True or right.get('verified') is not True:
        raise ValueError('Both actual independent verification handlers must pass')
    compare(output / 'baseline', output / 'candidate', complete=True)
    expected = dict(constructed_only=True, case=config['case'], exact_summary_and_all_arrays=True,
                    worlds=500, draws_per_world=2000, source_sha256=publication.sha(inputs['data']))
    if json.loads((output / 'RESULT.json').read_text('utf8')) != expected:
        raise ValueError('Publication qualification receipt changed')
    return dict(verified=True, actual_handlers_replayed=True, original_arithmetic_replayed=True,
                complete_baseline_candidate_array_parity=True, constructed_only=True)
