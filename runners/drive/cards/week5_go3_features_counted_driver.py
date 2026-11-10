"""Explicit one-attempt launcher for reviewed GO3 feature qualification only.

This file does not dispatch on import or choose continuations automatically.
Both the complete counted collection proof and component proof are required.
The owner must review/commit the design and authorize each attempted boundary.
"""
from pathlib import Path
import argparse
import json
from . import week5_runtime_v7 as runtime
from .batch_runtime import REPO, freeze, read, filehash
from .week5_runtime_v5_fixture import wait
from .week5_resume_v2 import output_manifest
from .week5_go3_collection_counted_fixture_v2 import all_bytes
from . import week5_go3_features_collected_fixture as fixture
from .. import week5_launch_v7 as launch
from runners.theory_days.launch import closure
from runners.stage9.process_identity import is_same_live_process

PRIVATE = REPO / '.agent-state/drive-20261107'
STAGES = ('source-pilot', 'verify-pilot', 'complete')


def attempt_name(case, stage):
    return 'GO3-feature-fixture-' + case + '-' + stage


def main(case, stage, commit, component_proof, training):
    if case not in ('supported', 'missing-category') or stage not in STAGES:
        raise ValueError('Only the two constructed complete collection cases are allowed')
    training, component_proof = Path(training).resolve(), Path(component_proof).resolve()
    source_root = runtime.policy.ROOT / ('GO3-collection-fixture-' + case + '-complete')
    source_proof = PRIVATE / ('go3-collection-counted-' + case) / 'FIXTURE.json'
    proof = read(source_proof)
    if proof.get('verified') is not True or proof.get('constructed_only') is not True:
        raise ValueError('Complete counted constructed collection proof required')
    final = proof['attempts'][-1]
    if Path(final['root']).resolve() != source_root.resolve() or filehash(source_root / 'COMPLETE.json') != final['terminal_sha256']:
        raise ValueError('Counted collection proof names another completed source')
    component = read(component_proof)
    if component.get('passed') is not True and component.get('verified') is not True:
        raise ValueError('Passing feature component/refusal proof required')
    if filehash(training) != fixture.features.analysis.ITERATER_SHA:
        raise ValueError('Original published intent training partition required')
    source_tree = all_bytes(source_root)
    source_done = read(source_root / 'COMPLETE.json')
    for name, digest in source_done['outputs'].items():
        if filehash(source_root / name) != digest:
            raise ValueError('Counted collection dependency changed')
    module = 'runners.drive.cards.week5_go3_features_collected_fixture'
    design = REPO / 'docs/design/stage-15/week5/GO3_COLLECTED_FEATURES.md'
    paths = list(closure([module, *launch.MODULES, 'runners.drive.week5_launch_v7']))
    paths += [Path(__file__), design, source_proof, component_proof, training,
              REPO / 'tests/test_week5_go3_features_collected.py']
    paths += [source_root / name for name in source_tree]
    pins = {str(path.resolve()): filehash(path) for path in paths}
    # Carry the exact original producer/archive/licence/salt/source-fixture pins.
    # A same-content alias does not replace a changed or absent admitted path.
    for name, digest in read(source_root / 'PLAN.json')['pins'].items():
        if filehash(Path(name)) != digest or (name in pins and pins[name] != digest):
            raise ValueError('Original collection source or native-runtime pin changed')
        pins[name] = digest
    inputs = dict(collection_run=str(source_root), iterater_train=str(training))
    fixture.validate(inputs)
    plan = dict(campaign='S15-WEEK5', family='GO', module=module, inputs=inputs,
                config=dict(phase='features', max_wall_seconds=900), design=str(design), reviewed_design_commit=commit,
                pins=pins, fixture_passed=True, owner_reviewed=True,
                validation_receipts=[str(source_proof), str(component_proof)], paid=False, gpu=False, ollama=False,
                numerical_threads=2, max_cpu_seconds=600, max_wall_seconds=1800,
                forecast_cpu_seconds=60, projected_peak_ram_GiB=3,
                premortem=dict(case_and_check='Actual counted constructed five-site collection -> original pinned external model -> all-row features -> independent original/numerical replay.',
                               smaller_route='Retain complete stopped output for owner cost review; no partial site/model/training or row sample is substituted.'))
    previous, previous_tree = None, None
    if stage != STAGES[0]:
        previous = runtime.policy.ROOT / attempt_name(case, STAGES[STAGES.index(stage) - 1])
        previous_tree = all_bytes(previous)
        prior_plan = read(previous / 'PLAN.json')
        if any(plan['pins'].get(name) != value for name, value in prior_plan['pins'].items()):
            raise ValueError('Feature qualifier continuation changed an original pin')
        plan['resume'] = dict(root=str(previous), plan_sha256=filehash(previous / 'PLAN.json'), paused_sha256=filehash(previous / 'PAUSED.json'))
    root = runtime.policy.ROOT / attempt_name(case, stage)
    root.mkdir()
    evidence = PRIVATE / ('go3-feature-counted-' + case)
    evidence.mkdir(parents=True, exist_ok=stage != STAGES[0])
    plan['card'] = root.name
    freeze(root / 'PLAN.json', plan)
    freeze(evidence / (stage + '-launch.json'), launch.launch(root))
    name, terminal = wait(root)
    if name != ('COMPLETE' if stage == STAGES[-1] else 'PAUSED'):
        raise ValueError('Unexpected counted feature qualifier terminal: ' + name)
    if all_bytes(source_root) != source_tree:
        raise ValueError('Complete counted collection predecessor was modified')
    if previous:
        if all_bytes(previous) != previous_tree or read(root / 'RESUMED_FROM.json')['copied'] != read(previous / 'PAUSED.json')['checkpoint_outputs']:
            raise ValueError('Authentic immutable feature checkpoint copy failed')
    owner = read(root / 'OWNER.json')['native']
    if is_same_live_process(owner) or any(read(path).get('native') == owner for path in runtime.policy.lease_paths()):
        raise ValueError('Feature qualifier owner or lease is still live')
    if name == 'PAUSED':
        if terminal['checkpoint_outputs'] != output_manifest(root / 'output'):
            raise ValueError('Feature checkpoint manifest is incomplete')
        if terminal['paused_operation'] != ('execute' if stage == STAGES[0] else 'verify'):
            raise ValueError('Wrong independent feature pilot boundary')
    else:
        for relative, digest in terminal['outputs'].items():
            if filehash(root / relative) != digest:
                raise ValueError('Complete feature qualifier output changed')
        if read(root / 'VERIFIED.json').get('original_external_model_and_complete_feature_parity') is not True:
            raise ValueError('Complete original-model feature parity absent')
    record = dict(root=str(root), terminal=name, cpu_seconds=terminal['cpu_seconds'], native=owner,
                  terminal_sha256=filehash(root / (name + '.json')), plan_sha256=filehash(root / 'PLAN.json'))
    freeze(evidence / (stage + '-terminal.json'), record)
    print(json.dumps(record), flush=True)
    if stage == STAGES[-1]:
        records = [read(evidence / (value + '-terminal.json')) for value in STAGES]
        freeze(evidence / 'FIXTURE.json', dict(verified=True, constructed_only=True, case=case, attempts=records,
            actual_complete_collection_dependency=True, original_external_model_and_complete_feature_parity=True,
            immutable_native_execution_and_independent_verification_pilots=True,
            all_native_owners_exited_and_leases_released=True, measured_cpu_seconds=sum(value['cpu_seconds'] for value in records),
            source_pins=plan['pins']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', required=True, choices=('supported', 'missing-category'))
    parser.add_argument('--stage', required=True, choices=STAGES)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--component-proof', required=True)
    parser.add_argument('--training', required=True)
    args = parser.parse_args()
    main(args.case, args.stage, args.commit, args.component_proof, args.training)
