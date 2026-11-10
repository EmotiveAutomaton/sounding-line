"""Bounded metadata-driver qualification, with a real prior native receipt.

DESIGN CHECK: LESSONS 3-5. Actual native provenance is authenticated without
model loading. Explicit constructed metadata probes refusal boundaries only;
they are never measured human-model costs or forecasts. No admission or launch.
"""
from pathlib import Path
import importlib.util
import pytest
from . import week5_at_admission_prepare as driver
from .timing_census import read,filehash
from .timing_p6 import write_equal


def run(output,inputs,config,verifying=False):
    if set(inputs)!={'completed_constructed_root'} or config:
        raise ValueError('One prior completed constructed native receipt required')
    prior,plan,done=driver.complete(inputs['completed_constructed_root'],
                                   'runners.drive.cards.week5_at_collect_v4_fixture')
    if read(prior/'output/FIXTURE.json').get('fixture_only') is not True:
        raise ValueError('Human collection cannot substitute for the constructed native proof')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    testfile=driver.REPO/'tests/test_week5_at_admission_prepare.py'
    spec=importlib.util.spec_from_file_location('constructed_AT_admission_tests',testfile)
    tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
    phase=root/('verify-controls' if verifying else 'execute-controls')
    names=['test_completed_native_schema_requires_both_actual_phase_counts',
           'test_complete_label_cannot_replace_verified_or_descendant_accounting',
           'test_failed_evidence_and_changed_pin_never_disappear',
           'test_guard_measurement_uses_only_sealed_actual_phases',
           'test_full_pilot_requires_exact_coverage_and_no_duplicate_charge']
    for name in names:
        if (root/'YIELD_REQUEST.json').exists():
            return dict(status='yielded',reason='between bounded admission metadata controls')
        location=phase/name;location.mkdir(parents=True,exist_ok=True)
        with pytest.MonkeyPatch.context() as patch:
            call=getattr(tests,name)
            if name=='test_guard_measurement_uses_only_sealed_actual_phases':call(location)
            elif name=='test_full_pilot_requires_exact_coverage_and_no_duplicate_charge':call(patch)
            else:call(location,patch)
    for value in [None,True,-1,float('nan'),float('inf')]:
        tests.test_unmeasured_or_invalid_value_is_not_a_zero_cost(value)
    tests.test_unknown_stage_and_missing_owner_review_refuse_before_git()
    result=dict(fixture_only=True,no_model_import_or_load=True,no_launch_or_admission=True,
                actual_prior_native_complete_authenticated=True,
                prior_complete_sha256=filehash(prior/'COMPLETE.json'),
                prior_module=plan['module'],test_source_sha256=filehash(testfile),
                both_phase_accounting_and_verified_true_required=True,
                failures_changed_pins_missing_measurements_refused=True,
                only_sealed_guard_peaks_accepted=True,
                incomplete_duplicate_pilot_work_and_charge_refused=True,
                constructed_metadata_predicates_only=True,
                actual_full_stage_preparation_and_future_policy_admission_unclaimed=True)
    if verifying:
        if read(root/'FIXTURE.json')!=result:raise ValueError('Admission predicate proof differs')
        return dict(verified=True,complete_metadata_refusal_replay=True)
    write_equal(root/'FIXTURE.json',result)
    return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
