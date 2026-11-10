"""Counted constructed-only pause/replay qualification of frozen CH analyses.

No estimand or numerical function changes. Each deliberately issued request is
handled by the delivered adapter's actual request check, after real callbacks.
"""
from pathlib import Path
import time
from . import week5_ch_analysis_bounded as adapter
from . import week5_ch_analysis_bounded_fixture as reference_fixture
from .batch_runtime import REPO, read, freeze, filehash, now, check_files
from .timing_pmap_source import completed

MODULE = 'runners.drive.cards.week5_ch_analysis_qualification_adapter_v1'
INPUT_MANIFEST = REPO/'.agent-state/drive-20261107/ch-analysis-qualification-inputs-v1.json'
INPUT_SHA256 = '1dfaa2b723f7c961fbf58ad1fcd6906731470ec4a155516b128f4df49868d103'
CARDS = ('CH2', 'CH3', 'CH4', 'CH5', 'CH6')


def input_pins():
    if filehash(INPUT_MANIFEST) != INPUT_SHA256:
        raise ValueError('Original constructed-source inventory changed')
    receipt = read(INPUT_MANIFEST)
    if receipt.get('constructed') is not True or receipt.get('scientific_admission') is not False:
        raise ValueError('Constructed-only inventory required')
    pins = {str(INPUT_MANIFEST): INPUT_SHA256}
    for directory, files in receipt['source_trees'].items():
        root = Path(directory).resolve()
        root.relative_to((REPO/'.agent-state').resolve())
        actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        if actual != set(files):
            raise ValueError('Original constructed source/output tree changed')
        for name, digest in files.items():
            path = (root/name).resolve()
            path.relative_to(root)
            key = str(path)
            if key in pins and pins[key] != digest:
                raise ValueError('Conflicting original fixture pins')
            pins[key] = digest
    check_files(pins)
    return receipt, pins


def original_inputs(inputs, config):
    receipt, _ = input_pins()
    reference = config == dict(constructed_fixture=True, case='reference')
    expected = {'models_fixture', 'histories_fixture', 'frozen_inputs'}
    if not reference:
        expected.add('reference_completion')
        card = config.get('card')
        if config != dict(constructed_fixture=True, card=card, max_new_draws=1000000000) or card not in CARDS:
            raise ValueError('Exact constructed card configuration required')
    if set(inputs) != expected:
        raise ValueError('Exact original fixture inputs required')
    if inputs['frozen_inputs'] != dict(path=str(INPUT_MANIFEST), sha256=INPUT_SHA256):
        raise ValueError('Unreviewed original input inventory')
    fixed = receipt['fixture_inputs']
    if any(inputs[key] != value for key, value in fixed.items()):
        raise ValueError('Original native fixture receipt changed')
    if not reference:
        path = Path(inputs['reference_completion']).resolve()
        proof_path, plan_path = path.parent/'output/FIXTURE.json', path.parent/'PLAN.json'
        completed(path, proof_path)
        completed(path, plan_path)
        proof, plan = read(proof_path), read(plan_path)
        if (plan['module'] != MODULE or plan['config'] != dict(constructed_fixture=True, case='reference')
                or plan['inputs'] != {key: inputs[key] for key in expected - {'reference_completion'}}
                or proof.get('passed') is not True or proof.get('all_five_original_outputs_equal') is not True):
            raise ValueError('Complete counted all-five reference proof required')
    return fixed


def pause_phase(output, card):
    root = Path(output).resolve().parent
    plan = read(root/'PLAN.json')
    if plan['module'] != MODULE or plan['config'].get('card') != card:
        raise ValueError('Actual counted constructed card plan required')
    if 'resume' not in plan:
        if (root/'RESUMED_FROM.json').exists():
            raise ValueError('Unexpected copied checkpoint')
        return 'execute'
    prior = Path(plan['resume']['root']).resolve()
    copied = read(root/'RESUMED_FROM.json')
    if (Path(copied['predecessor']).resolve() != prior
            or copied['plan_sha256'] != filehash(prior/'PLAN.json')
            or copied['paused_sha256'] != filehash(prior/'PAUSED.json')
            or copied['copied'] != read(prior/'PAUSED.json')['checkpoint_outputs']):
        raise ValueError('Whole native-authenticated checkpoint required')
    phase = read(prior/'PAUSED.json')['paused_operation']
    if phase == 'execute':
        return 'verify'
    if phase == 'verify':
        return None
    raise ValueError('Unexpected predecessor phase')


def expected_case(inputs, config):
    fixed = original_inputs(inputs, config)
    cases = list(reference_fixture.cases(fixed))
    if {case[0] for case in cases} != set(CARDS):
        raise ValueError('Incomplete original numerical case bank')
    return next(case for case in cases if case[0] == config['card'])


def case_run(output, inputs, config, operation):
    started = time.monotonic()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    card, source, settings, expected = expected_case(inputs, config)
    stop_phase = pause_phase(output, card)
    original_progress = adapter.Progress
    pilot = []
    states = []

    class QualifyingProgress(original_progress):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.last_boundary = started
            self.max_boundary_wall_seconds = 0.
            self.first_callback_wall_seconds = None
            states.append(self)

        def begin(self, label, total):
            name = super().begin(label, total)
            if self.calls == 1:
                self.first_loop = name
            return name

        def value(self, name, index, compute):
            before = time.monotonic()
            self.max_boundary_wall_seconds = max(self.max_boundary_wall_seconds, before-self.last_boundary)
            if self.first_callback_wall_seconds is None:
                self.first_callback_wall_seconds = before-started
            result = super().value(name, index, compute)
            self.last_boundary = time.monotonic()
            self.max_boundary_wall_seconds = max(self.max_boundary_wall_seconds, self.last_boundary-before)
            if self.operation == stop_phase and name == self.first_loop and not pilot:
                series = self.series[name]
                done, total = len(series['values']), series['total']
                boundary = max(1, (total+19)//20)
                if done == boundary and done < total:
                    if self.restored != 0 or self.new_calls != done:
                        raise ValueError('Pilot must be actual new work from callback zero')
                    request_path = output/'YIELD_REQUEST.json'
                    if request_path.exists():
                        raise ValueError('Do not overwrite an external owner/resource request')
                    self.save()
                    request = dict(at=now(), reason='owner_cancel', constructed_fixture=True,
                                   qualification='CH analysis committed callback pilot')
                    adapter.write_json(request_path, request)
                    value = dict(card=card, operation=self.operation, series=name,
                                 source_units=done, source_total=total,
                                 observed_fraction=done/total, requested_fraction=.05,
                                 first_whole_callback_at_or_after_fraction=.05,
                                 exact_five_percent_claimed=(done*20 == total),
                                 constructed_fixture_only=True,
                                 source_or_verifier_completed=False,
                                 source_start_callback=0, restored_callbacks=self.restored,
                                 actual_new_callbacks=self.new_calls,
                                 request=request, request_sha256=filehash(request_path),
                                 checkpoint_sha256=filehash(self.path))
                    freeze(output/('QUALIFICATION_'+operation.upper()+'_PILOT.json'), value)
                    pilot.append(value)
            return result

    adapter.Progress = QualifyingProgress
    try:
        result = getattr(adapter, operation)(output, source, settings)
    finally:
        adapter.Progress = original_progress
    elapsed = time.monotonic()-started
    timing = dict(phase_wall_seconds=elapsed, constructed_scope_only=True,
                  maximum_observed_callback_or_gap_seconds=max(
                      [elapsed] if not states else
                      [max(state.max_boundary_wall_seconds, time.monotonic()-state.last_boundary)
                       for state in states]),
                  first_callback_wall_seconds=(states[0].first_callback_wall_seconds if states else None),
                  callback_coverage='setup, original callbacks, between-callback work and final summary; constructed scale only')
    if timing['maximum_observed_callback_or_gap_seconds'] > 60:
        raise ValueError('Constructed uninterruptible boundary exceeded native yield grace')
    if result.get('status') == 'yielded':
        if not pilot:
            return result
        if (result.get('phase') != operation or result.get('new_callbacks') != pilot[0]['source_units']
                or 'Owner requested' not in result.get('reason', '')):
            raise ValueError('Delivered adapter did not honor the actual pilot request')
        return dict(result, qualification_pilot=pilot[0], actual_adapter_request_honored=True,
                    cooperative_timing=timing)
    if operation == stop_phase:
        raise ValueError('Native fixture did not stop at the declared nonterminal callback boundary')
    if filehash(output/'SCIENCE.json') != filehash(expected):
        raise ValueError('Complete original scientific output differs')
    if operation == 'execute':
        if stop_phase == 'verify':
            previous = read(output/'QUALIFICATION_EXECUTE_PILOT.json')
            if result.get('reused_callbacks') != previous['source_units']:
                raise ValueError('Authenticated execution prefix was not reused exactly')
            freeze(output/'QUALIFICATION_EXECUTE_CONTINUATION.json', dict(
                card=card, result=result, original_science_sha256=filehash(expected),
                copied_callbacks_reused=previous['source_units']))
        elif result.get('sealed_output_reused') is not True:
            raise ValueError('Final attempt must preserve completed execution seal')
        return dict(result, constructed=True, frozen_original_science_sha256=filehash(expected),
                    cooperative_timing=timing)
    original_checkpoint = read(expected.parent/'CHECKPOINT.json')
    total_callbacks = sum(series['total'] for series in original_checkpoint['series'].values())
    if (result.get('verified') is not True or result.get('fresh_from_callback_zero') is not True
            or result.get('restored_verification_callbacks') != 0
            or result.get('recomputed_callbacks') != total_callbacks
            or filehash(output/'replay/SCIENCE.json') != filehash(expected)):
        raise ValueError('Every original callback must independently replay from zero')
    for phase in ('EXECUTE', 'VERIFY'):
        receipt = read(output/('QUALIFICATION_'+phase+'_PILOT.json'))
        if receipt['operation'] != phase.casefold() or receipt['card'] != card:
            raise ValueError('Both actual native pilot phases are required')
    proof = dict(verified=True, constructed=True, card=card,
                 full_fresh_verification=result, frozen_original_science_sha256=filehash(expected),
                 original_scientific_config=settings, every_original_callback_replayed=total_callbacks,
                 cooperative_timing=timing,
                 both_actual_native_pilots_required=True, scientific_admission=False)
    freeze(output/'QUALIFICATION_FINAL.json', proof)
    return proof


def execute(output, inputs, config):
    if config == dict(constructed_fixture=True, case='reference'):
        return reference_fixture.execute(output, original_inputs(inputs, config), dict(constructed_fixture=True))
    return case_run(output, inputs, config, 'execute')


def verify(output, inputs, config):
    if config == dict(constructed_fixture=True, case='reference'):
        return reference_fixture.verify(output, original_inputs(inputs, config), dict(constructed_fixture=True))
    return case_run(output, inputs, config, 'verify')
