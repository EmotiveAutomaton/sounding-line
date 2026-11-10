"""Counted constructed qualification of every declared GO3 scientific cell.

No human source is opened. Full positive/uninformative worlds, original whole
reference parity and independent repeat are required. Internal unit pilots are
exercised and retained; only the actual runtime may issue a native completion.
"""
from pathlib import Path
import time
from . import week5_go3_bank_analysis_fixture as fixture

bank = fixture.bank


def declaration():
    return dict(constructed_only=True, cells=bank.original.grid(), signals=[False, True],
                original_sha256=bank.core.sha(bank.original.__file__),
                analysis_sha256=bank.core.sha(bank.__file__), fixture_sha256=bank.core.sha(fixture.__file__),
                counted_fixture_sha256=bank.core.sha(__file__))


def cooperative_parity(output, signal, specification, stop):
    frame = fixture.world(signal)
    binding = bank.features.digest(dict(constructed=True, signal=signal, specification=specification,
                                       fixture_sha256=bank.core.sha(fixture.__file__)))
    result = bank.run_frame(output, frame, specification, binding, stop)
    if stop():
        raise bank.Paused('before independent original whole-case parity oracle')
    # The original oracle is deliberately not altered or partially replayed.
    # It is a bounded constructed case; its actual longest duration remains
    # an owner admission check, not an assumed sub-second validation step.
    expected = bank.original.classify(frame, specification)
    if specification['cell'] == 'GO3':
        expected['habit_companion'] = bank.original.habits(frame, 2000, 1000)
    expected.update(card='GO3', scope='comment-stated editing reason categories; retrospective and descriptive')
    if result != expected:
        raise ValueError('Complete original GO3 model, interval or habit reference parity differs')
    if signal and result.get('gain', 0) < .7:
        raise ValueError('Constructed strongly informative feature instrument failed')
    if not signal and result.get('outcome') == 'supports':
        raise ValueError('Uninformative fixed-design classifier world passed')
    if specification['cell'] == 'GO3' and (result['habit_companion']['passes'] or result['habit_companion']['difference_interval'] != [0., 0.]):
        raise ValueError('Exact context-only habit world passed or was not exact zero')
    return result


def execute(output, inputs, config):
    if inputs or set(config) - {'phase', 'max_wall_seconds'} or config.get('phase') != 'qualify-grid':
        raise ValueError('Exact constructed grid qualification contract required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    identity = declaration()
    path = output / 'DECLARATION.json'
    if path.exists() and bank.features.read(path) != identity:
        raise ValueError('Constructed full-grid binding changed')
    bank.core.write(path, identity)
    began = time.monotonic()
    maximum = float(config.get('max_wall_seconds', 900))
    if not 0 < maximum < float('inf'):
        raise ValueError('Positive finite constructed qualification quantum required')
    stop = lambda: bank.requested(output) or time.monotonic() - began >= maximum
    completed = []
    boundaries = []
    if (output / 'BOUNDARIES.json').exists():
        boundaries = bank.checked_read(output / 'BOUNDARIES.json', bank.features.digest(identity))['boundaries']
    for signal in identity['signals']:
        for specification in identity['cells']:
            case = ('informative-' if signal else 'uninformative-') + specification['cell']
            case_root = output / case
            proof = case_root / 'PARITY.json'
            if proof.exists():
                saved = bank.checked_read(proof, bank.features.digest(identity))
                if saved['result_sha256'] != bank.core.sha(case_root / 'RESULT.json'):
                    raise ValueError('Constructed case result changed')
                completed.append(case)
                continue
            while True:
                if stop():
                    return dict(status='yielded', phase='constructed_grid_qualification', completed=len(completed), total=16,
                                constructed_only=True, complete_qualification=False)
                try:
                    cooperative_parity(case_root, signal, specification, stop)
                    break
                except bank.Paused as pause:
                    if not str(pause).startswith('first five percent'):
                        return dict(status='yielded', phase='constructed_grid_qualification', completed=len(completed), total=16,
                                    constructed_only=True, complete_qualification=False, reason=str(pause))
                    marker = dict(case=case, reason=str(pause), completed_units=bank.progress_counts(case_root, specification)[0])
                    if marker in boundaries:
                        raise ValueError('Constructed internal pilot repeated without progress')
                    boundaries.append(marker)
                    bank.checked_write(output / 'BOUNDARIES.json', dict(binding=bank.features.digest(identity), boundaries=boundaries))
            bank.checked_write(proof, dict(binding=bank.features.digest(identity), passed=True,
                               result_sha256=bank.core.sha(case_root / 'RESULT.json')))
            completed.append(case)
            bank.core.write(output / 'PROGRESS.json', dict(phase='constructed_grid_qualification', completed=len(completed), total=16))
    # Two complete primary worlds have classifier and habit pilots; fourteen
    # texture worlds each have a classifier pilot. All are real handler paths.
    if len(boundaries) != 18:
        raise ValueError('Every expected whole-handler pilot boundary must be exercised')
    result = dict(verified=True, constructed_only=True, cases=completed, total_cases=16,
                  primary_draws=2000, texture_draws=200, conditional_references=1000,
                  paired_habit_draws=2000, internal_complete_unit_pilots=18,
                  fixed_signal_and_uninformative_worlds=True, exact_context_only_habit_null=True,
                  original_complete_estimator_and_reference_parity=True)
    bank.core.write(output / 'FIXTURE.json', result)
    return result


def verify(output, inputs, config):
    output = Path(output)
    result = execute(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return result | dict(verified=False)
    if result != bank.features.read(output / 'FIXTURE.json'):
        raise ValueError('Complete constructed grid qualification did not replay')
    # Complete row/model/reference replay is required, not only verdict parity.
    for case in result['cases']:
        left, right = output / case, output / 'independent-replay' / case
        for area in ('classifier', 'habits'):
            a, b = left / area, right / area
            names = sorted(p.relative_to(a).as_posix() for p in a.rglob('*') if p.is_file() and not p.name.endswith('.seal.json') and p.name != 'PROGRESS.json')
            others = sorted(p.relative_to(b).as_posix() for p in b.rglob('*') if p.is_file() and not p.name.endswith('.seal.json') and p.name != 'PROGRESS.json')
            if names != others:
                raise ValueError('Constructed full-grid saved bank differs')
            for name in names:
                if name.endswith('.npz'):
                    x, y = bank.features.load_arrays(a / name), bank.features.load_arrays(b / name)
                    if set(x) != set(y) or any(not bank.np.array_equal(x[key], y[key]) for key in x):
                        raise ValueError('Constructed full-grid models/predictions differ')
                elif bank.features.read(a / name) != bank.features.read(b / name):
                    raise ValueError('Constructed full-grid complete draw bank differs')
    return dict(verified=True, complete_constructed_grid_replayed=True,
                every_model_prediction_and_reference_draw_replayed=True, constructed_only=True)
