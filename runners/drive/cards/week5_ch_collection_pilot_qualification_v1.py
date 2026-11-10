"""Unrun, nonlaunching preparation/inspection of the real CH roster-pilot path.

Requires a completed counted original-parity collector fixture, then prepares
three separate candidate requests for the unchanged production pilot adapter.
Each native stage is launched only by the owner after review. No driver loop,
fake native receipt, model call or source scan is present here.
"""
from pathlib import Path
import json

from . import week5_ch_collection_pilot_v1 as adapter
from . import week5_ch_collection_bounded_v1 as collection
from .timing_pmap_source import completed
from .week5_ch_source import digest, write_json
from . import week5_policy_v2 as policy
from runners.stage9.process_identity import is_same_live_process


STAGES = ('execute_pilot', 'verify_pilot', 'final')
FIXTURE_MODULE = 'runners.drive.cards.week5_ch_collection_bounded_fixture_v1'


def read(path):
    return collection.read_json(path)


def reference(complete):
    complete = Path(complete).resolve()
    root = complete.parent
    proof_path = root/'output/constructed_execution/FIXTURE.json'
    plan_path = root/'PLAN.json'
    completed(complete, proof_path)
    completed(complete, plan_path)
    plan, proof = read(plan_path), read(proof_path)
    if (plan.get('module') != FIXTURE_MODULE or plan.get('inputs') != {}
            or plan.get('config') != {'constructed_fixture':True}
            or proof.get('constructed') is not True or proof.get('positions') != 180
            or proof.get('original_all_three_files_byte_equal') is not True
            or proof.get('complete_fresh_source_replay') is not True
            or proof.get('optimizer_and_gzip_actual_owner_yield') is not True
            or proof.get('exact_final_gzip_quantum') is not True):
        raise ValueError('Complete exact constructed collector fixture required')
    private = root/'output/constructed_execution'
    inputs = {}
    for key, name in (('positions','positions.gz'), ('batches','BATCHES.json')):
        path = private/'inputs'/name
        completed(complete, path)
        inputs[key] = dict(path=str(path), sha256=digest(path))
    # Batch metadata names every score; the original counted completion must
    # bind all of them. No score payload or participant value is inspected.
    manifest = read(inputs['batches']['path'])
    for batch in manifest['batches']:
        for name in ('verify', 'report', 'score_bindings'):
            path = Path(batch[name]['path'])
            completed(complete, path)
            if digest(path) != batch[name]['sha256']:
                raise ValueError('Constructed batch metadata changed')
        for name, sha in read(batch['score_bindings']['path']).items():
            path = Path(batch['path'])/name
            completed(complete, path)
            if digest(path) != sha:
                raise ValueError('Constructed score bytes changed')
    expected = {}
    for name in collection.FILES:
        path = private/'original'/name
        completed(complete, path)
        expected[name] = dict(path=str(path), sha256=digest(path))
    return inputs, dict(constructed_fixture=True, expected_positions=180, nodes=1000000), expected


def prepare(complete, destination):
    inputs, config, expected = reference(complete)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for index, stage in enumerate(STAGES):
        write_json(destination/(stage+'.CANDIDATE.json'), dict(
            status='candidate_not_admitted', stage=stage, module=adapter.MODULE,
            inputs=inputs, config=config, expected_roster_boundary=9,
            expected_roster_fraction=.05, expected_score_rows_at_pilot=0,
            expected_complete_fit_units_at_pilot=0,
            source_scope='constructed fixture only; original 180-row roster',
            reference_completion=dict(path=str(Path(complete).resolve()), sha256=digest(complete)),
            original_reference_outputs=expected,
            requires_prior_stage=None if index==0 else STAGES[index-1],
            resume=None, owner_reviewed=False, fixture_passed=False,
            reviewed_design_commit=None, pins=None, attempt_root=None,
            max_cpu_seconds=None, max_wall_seconds=None,
            projected_peak_ram_GiB=None, measured_cost=None,
            scientific_admission=False, launcher=None))
    write_json(destination/'QUALIFICATION_REQUIREMENTS.json', dict(
        all_three_separate_counted_stages_required=True, stages=list(STAGES),
        actual_native_copies_and_exits=True, exact_original_outputs_required=True,
        first_roster_rows_only=True, first_five_percent_total_cpu_claim=False,
        every_attempt_and_replay_charged_to_CH=True,
        source_or_scientific_admission=False, no_launcher=True))


def inspect(root, stage, complete):
    """Read-only acceptance checks; cannot launch or advance another stage."""
    if stage not in STAGES:
        raise ValueError('Unknown qualification stage')
    root = Path(root).resolve()
    inputs, config, expected = reference(complete)
    plan = read(root/'PLAN.json')
    if plan.get('module') != adapter.MODULE or plan.get('inputs') != inputs or plan.get('config') != config:
        raise ValueError('Native attempt differs from the exact constructed plan')
    output = root/'output'
    adapter.context(output, inputs, config)
    owner = read(root/'OWNER.json')
    if is_same_live_process(owner['native']):
        raise ValueError('Native owner still active')
    operations = ('execute',) if stage=='execute_pilot' else ('execute','verify')
    measured = 0.0
    for operation in operations:
        native = read(root/(operation.upper()+'_NATIVE.json'))['native']
        if is_same_live_process(native):
            raise ValueError('Native child still active')
        # Job usage, not a child+Job double count. Earlier attempts and runtime
        # overhead remain required in separate family/campaign accounting.
        measured += policy.finite(read(root/(operation.upper()+'_JOB_USAGE.json'))['cpu_seconds'])
        read(root/(operation.upper()+'_USAGE.json'))
    for path in policy.lease_paths():
        lease = read(path)
        if Path(lease.get('attempt_root','')).resolve()==root:
            raise ValueError('Native lease not released')
    terminals = [name for name in ('COMPLETE.json','PAUSED.json','FAILED.json') if (root/name).exists()]
    expected_terminal = 'COMPLETE.json' if stage=='final' else 'PAUSED.json'
    if terminals != [expected_terminal]:
        raise ValueError('Ambiguous or wrong native terminal')
    result = read(root/('RESULT.json' if stage=='execute_pilot' else 'VERIFIED.json'))
    if stage != 'final':
        operation = 'execute' if stage=='execute_pilot' else 'verify'
        paused = read(root/'PAUSED.json')
        pilot = read(output/adapter.PILOTS[operation])
        if (paused.get('status') != 'PAUSED' or paused.get('paused_operation') != operation
                or result.get('status') != 'yielded'
                or pilot.get('binding') != adapter.contract(inputs,config)
                or pilot.get('operation') != operation
                or pilot.get('completed_roster_rows') != 9
                or pilot.get('source_roster_rows') != 180
                or pilot.get('score_rows') != 0 or pilot.get('complete_fit_units') != 0
                or pilot.get('cpu_fraction_claimed') is not False
                or pilot.get('full_collection_fraction_claimed') is not False
                or pilot.get('population_complete') is not False
                or paused['checkpoint_outputs'].get(adapter.PILOTS[operation]) != digest(output/adapter.PILOTS[operation])):
            raise ValueError('Actual first-nine-row native pilot missing')
        db = output/pilot['checkpoint_relative_path']
        _, counts = adapter.checkpoint(db, inputs, config)
        if digest(db) != pilot['checkpoint_sha256'] or counts['roster'] != 9:
            raise ValueError('Pilot checkpoint changed')
    else:
        if result.get('verified') is not True or result.get('complete_recalculation') is not True:
            raise ValueError('Complete independent collection replay missing')
        for operation in ('execute','verify'):
            if not adapter.copied_pilot(output, operation, inputs, config):
                raise ValueError('Both genuine prior native pilots are required')
        for name in collection.FILES:
            completed(root/'COMPLETE.json', output/name)
    if stage != 'execute_pilot':
        for name, spec in expected.items():
            if digest(output/name) != spec['sha256']:
                raise ValueError('Unchanged original collection output differs')
    return dict(stage=stage, accepted=True, constructed=True,
                current_attempt_native_job_cpu_seconds=measured,
                prior_and_runtime_costs_still_required=True,
                native_exits_and_lease_release=True,
                scientific_admission=False,
                watcher_delivery_requires_owner_confirmation=True,
                first_roster_row_fraction_only=True)


def arithmetic_fixture():
    """Prepared source-free assertions; deliberately not invoked at import."""
    for count, expected in ((1,1),(19,1),(20,1),(21,2),(40,2),(41,3),(180,9),(400000,20000)):
        actual = adapter.boundary(count)
        assert actual == expected and actual*20 >= count and (actual-1)*20 < count
    for invalid in (0,-1,400001,True,20.0,None):
        try:
            adapter.boundary(invalid)
        except ValueError:
            continue
        raise AssertionError('Invalid denominator accepted')
    return dict(arithmetic=True, no_runtime_or_collection_execution=True,
                rounding_is_declared=True, scientific_admission=False)
