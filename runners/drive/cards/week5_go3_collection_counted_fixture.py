"""Owner-reviewed, one-stage-at-a-time counted GO3 collection qualification.

DESIGN CHECK: constructed source envelopes only; full source-byte pins and
native identity, authentic immutable pause/copy, independent verifier pause
and final all-output authentication. No automatic continuation or human fit.
"""
from pathlib import Path
import argparse
import json
from . import week5_go3_collection_fixture as fixture
from . import week5_runtime_v7 as runtime
from .batch_runtime import REPO, freeze, read, filehash
from .week5_runtime_v5_fixture import wait
from .week5_resume_v2 import output_manifest
from .. import week5_launch_v7 as launch
from runners.theory_days.launch import closure
from runners.stage9.process_identity import is_same_live_process

PRIVATE = REPO / '.agent-state/drive-20261107'
INPUTS = PRIVATE / 'go3-collection-fixture-inputs'
STAGES = ('source-pilot', 'verify-pilot', 'complete')


def execute(output, inputs, config):
    return fixture.execute(Path(output), inputs, config)


def verify(output, inputs, config):
    return fixture.verify(Path(output), inputs, config)


def prepare():
    fixture.prepare(INPUTS)
    files = {str(path.relative_to(INPUTS)): filehash(path) for path in INPUTS.rglob('*') if path.is_file()}
    freeze(PRIVATE / 'go3-collection-fixture-input-tree.json', dict(constructed_only=True, files=files,
        source_envelopes_are_not_native_results=True,
        producer_sha256=filehash(fixture.collection.producer.__file__),
        archive_bindings=fixture.collection.source.ARCHIVES,
        license_sha256=fixture.collection.source.LICENSE_SHA,
        constructed_salt_sha256=fixture.key('shared-salt')))


def all_bytes(root):
    return {path.relative_to(root).as_posix(): filehash(path) for path in root.rglob('*') if path.is_file()}


def attempt_name(case, stage):
    return 'GO3-collection-fixture-' + case + '-' + stage


def main(case, commit, stage, component_proof):
    component_proof = Path(component_proof).resolve()
    component = read(component_proof)
    if component.get('passed') is not True and component.get('verified') is not True:
        raise ValueError('Passing targeted component/refusal proof required')
    expected = read(PRIVATE / 'go3-collection-fixture-input-tree.json')
    if expected.get('constructed_only') is not True or all_bytes(INPUTS) != expected['files']:
        raise ValueError('Complete constructed source input tree changed')
    evidence = PRIVATE / ('go3-collection-counted-' + case)
    evidence.mkdir(parents=True, exist_ok=stage != STAGES[0])
    inputs = dict(roster=str(INPUTS / (case + '-roster.json')),
                  fixture_manifest=str(INPUTS / (case + '-fixture.json')))
    design = REPO / 'docs/design/stage-15/week5/GO3_COLLECTION.md'
    source_proof = PRIVATE / 'go3-counted-native/FIXTURE.json'
    module = 'runners.drive.cards.week5_go3_collection_counted_fixture'
    paths = list(closure([module, *launch.MODULES, 'runners.drive.week5_launch_v7']))
    paths += [design, source_proof, component_proof,
              REPO / 'docs/design/stage-15/week5/GO3_COLLECTION_COUNTED.md',
              REPO / 'tests/test_week5_go3_collection.py',
              REPO / 'tests/test_week5_go3_collection_refusals.py',
              PRIVATE / 'go3-collection-fixture-input-tree.json']
    paths += [path for path in INPUTS.rglob('*') if path.is_file()]
    plan = dict(campaign='S15-WEEK5', family='GO', module=module, inputs=inputs,
                config=dict(phase='collect', case=case, max_wall_seconds=300),
                design=str(design), reviewed_design_commit=commit,
                pins={str(path.resolve()): filehash(path) for path in paths},
                fixture_passed=True, owner_reviewed=True,
                validation_receipts=[str(source_proof), str(component_proof)],
                paid=False, gpu=False, ollama=False, numerical_threads=2,
                max_cpu_seconds=120, max_wall_seconds=600,
                forecast_cpu_seconds=30, projected_peak_ram_GiB=1,
                premortem=dict(case_and_check='Constructed five-site source collection; exact support routing and complete native pause/copy/replay.',
                               smaller_route='Stop and retain evidence; no smaller site roster, missing category or failed draw is selected away.'))
    previous = None
    prior_tree = None
    if stage != STAGES[0]:
        previous = runtime.policy.ROOT / attempt_name(case, STAGES[STAGES.index(stage) - 1])
        prior_tree = all_bytes(previous)
        prior_plan = read(previous / 'PLAN.json')
        if any(plan['pins'].get(name) != digest for name, digest in prior_plan['pins'].items()):
            raise ValueError('Original source/runtime/refusal proof pins changed')
        plan['resume'] = dict(root=str(previous), plan_sha256=filehash(previous / 'PLAN.json'),
                              paused_sha256=filehash(previous / 'PAUSED.json'))
    root = runtime.policy.ROOT / attempt_name(case, stage)
    root.mkdir()
    plan['card'] = root.name
    freeze(root / 'PLAN.json', plan)
    freeze(evidence / (stage + '-launch.json'), launch.launch(root))
    terminal_name, terminal = wait(root)
    expected_terminal = 'COMPLETE' if stage == STAGES[-1] else 'PAUSED'
    if terminal_name != expected_terminal:
        raise ValueError('Unexpected counted collection terminal: ' + terminal_name)
    if previous:
        if all_bytes(previous) != prior_tree:
            raise ValueError('Stopped predecessor bytes changed')
        if read(root / 'RESUMED_FROM.json')['copied'] != read(previous / 'PAUSED.json')['checkpoint_outputs']:
            raise ValueError('Complete stopped collection manifest was not copied')
    owner = read(root / 'OWNER.json')['native']
    if is_same_live_process(owner) or any(read(path).get('native') == owner for path in runtime.policy.lease_paths()):
        raise ValueError('Counted owner or lease remains active')
    if terminal_name == 'PAUSED':
        if terminal['checkpoint_outputs'] != output_manifest(root / 'output'):
            raise ValueError('Stopped collection manifest is incomplete')
        if terminal['paused_operation'] != ('execute' if stage == 'source-pilot' else 'verify'):
            raise ValueError('Wrong independently counted pilot boundary')
    record = dict(root=str(root), terminal=terminal_name, cpu_seconds=terminal['cpu_seconds'],
                  terminal_sha256=filehash(root / (terminal_name + '.json')), native=owner,
                  plan_sha256=filehash(root / 'PLAN.json'))
    freeze(evidence / (stage + '-terminal.json'), record)
    print(json.dumps(record), flush=True)
    if stage != STAGES[-1]:
        return
    for name, digest in terminal['outputs'].items():
        if filehash(root / name) != digest:
            raise ValueError('Complete counted collection output changed')
    if read(root / 'VERIFIED.json').get('verified') is not True:
        raise ValueError('Full independent collection verification absent')
    records = [read(evidence / (name + '-terminal.json')) for name in STAGES]
    freeze(evidence / 'FIXTURE.json', dict(verified=True, constructed_only=True, case=case,
        actual_counted_execution_and_verification_pilots=True, immutable_complete_manifest_copy=True,
        complete_five_site_source_support_replay=True, no_scientific_fitting=True,
        every_complete_output_hash_verified=True, all_native_owners_exited_and_leases_released=True,
        measured_cpu_seconds=sum(value['cpu_seconds'] for value in records), attempts=records,
        source_pins=plan['pins']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'run'))
    parser.add_argument('--case', choices=('supported', 'missing-category'))
    parser.add_argument('--stage', choices=STAGES, default=STAGES[0])
    parser.add_argument('--commit')
    parser.add_argument('--component-proof')
    args = parser.parse_args()
    if args.mode == 'prepare':
        prepare()
    else:
        main(args.case, args.commit, args.stage, args.component_proof)
