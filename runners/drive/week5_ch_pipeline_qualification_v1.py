"""Owner-driven, one-counted-stage-at-a-time CH pipeline qualification.

No command chains native jobs or polls for completion. `launch` starts exactly
one reviewed stage and returns; `inspect` is run after its durable terminal wake.
No automatic retry, source repair, acknowledgement or scientific launch exists.
"""
from pathlib import Path
import argparse
import json
import re
import subprocess
import sys
import time
import uuid
from runners.drive.cards.batch_runtime import REPO, freeze, filehash, now, check_files
from runners.drive.cards import week5_policy_v2 as policy
from runners.drive import week5_launch_v7 as launcher
from runners.drive.cards.week5_resume_v2 import output_manifest
from runners.stage9.process_identity import is_same_live_process
from runners.theory_days.launch import closure

read = policy.read
WRAPPER = 'runners.drive.cards.week5_ch_pipeline_qualification_adapter_v1'
FIXTURE = 'runners.drive.cards.week5_ch_pipeline_bounded_fixture'
DESIGN = REPO/'docs/design/stage-15/week5/CH_PIPELINE_QUALIFICATION.md'
DELIVERED = REPO/'.agent-state/drive-20261107/ch-second-gear-admission-v1/PIPELINE_SUCCESSORS_PENDING.json'
STAGES = ('reference', 'merge-execute-pilot', 'merge-verify-pilot', 'merge-complete',
          'sample-execute-pilot', 'sample-verify-pilot', 'sample-complete',
          'history-execute-pilot', 'history-verify-pilot', 'history-complete')


def manifest(root):
    return {p.relative_to(root).as_posix():filehash(p) for p in sorted(root.rglob('*')) if p.is_file()}


def checked_controller(root):
    root = Path(root).resolve()
    root.relative_to((REPO/'.agent-state').resolve())
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,70}', root.name):
        raise ValueError('Use a bounded lowercase qualification name')
    return root


def stage_root(controller, stage):
    if stage not in STAGES:
        raise ValueError('Unknown qualification stage')
    return policy.ROOT/(controller.name+'-'+stage)


def snapshot_path(controller, stage):
    return controller/(stage+'-IMMUTABLE.json')


def checked_setup(controller):
    setup = read(controller/'SETUP.json')
    check_files(setup['pins'])
    if setup['constructed_only'] is not True or setup['stage_order'] != list(STAGES):
        raise ValueError('Changed qualification scope')
    expected = dict(reference_cpu_cap=600, successor_attempt_cpu_cap=300,
                    maximum_ten_attempt_cpu_envelope=3300,
                    owner_supervisor_allowance_per_attempt=30,
                    native_launch_shell_allowance_per_attempt=5,
                    controller_command_allowance_seconds=1)
    if any(setup.get(key) != value for key,value in expected.items()):
        raise ValueError('Changed qualification ceilings or accounting allowances')
    return setup


def prior_stage(controller, stage):
    index = STAGES.index(stage)
    if index:
        prior = STAGES[index-1]
        proof = read(controller/(prior+'-INSPECTED.json'))
        if proof.get('passed') is not True:
            raise ValueError('Prior qualification stage is not independently inspected')
        assert_old(controller, prior)


def assert_old(controller, stage):
    old = read(snapshot_path(controller, stage))
    if manifest(stage_root(controller, stage)) != old['files']:
        raise ValueError('Prior terminal attempt changed after native exit')


def initialize(controller, commit, validations):
    controller = checked_controller(controller)
    if controller.exists():
        raise ValueError('Qualification initialization is immutable')
    delivered = read(DELIVERED)
    pins = {str((REPO/name).resolve()):digest for name,digest in delivered['files'].items()}
    check_files(pins)
    paths = closure([WRAPPER, FIXTURE, *launcher.MODULES,
                     'runners.drive.week5_launch_v7', 'runners.drive.week5_ch_pipeline_qualification_v1'])
    paths |= {DESIGN, DELIVERED, Path(__file__).resolve()}
    validations = [str(Path(p).resolve()) for p in validations]
    if not validations or len(set(validations)) != len(validations):
        raise ValueError('Existing owner-reviewed native foundation receipts are required')
    for path in validations:
        read(path)
        paths.add(Path(path))
    for path in paths:
        pins[str(path.resolve())] = filehash(path)
    # Both the delivered design and this qualification procedure must be in the
    # actual reviewed commit. Reading git objects is not publishing anything.
    for design in (DESIGN, REPO/'docs/design/stage-15/week5/CH_PIPELINE_BOUNDED.md'):
        rel = design.relative_to(REPO).as_posix()
        frozen = subprocess.run(['git', 'show', commit+':'+rel], cwd=REPO,
                                capture_output=True, check=True).stdout
        if frozen != design.read_bytes():
            raise ValueError('Qualification design differs from reviewed commit')
    controller.mkdir(parents=True, exist_ok=False)
    setup = dict(at=now(), constructed_only=True, stage_order=list(STAGES),
                 reviewed_design_commit=commit, design=str(DESIGN),
                 validation_receipts=validations, pins=pins,
                 reference_cpu_cap=600, successor_attempt_cpu_cap=300,
                 maximum_ten_attempt_cpu_envelope=3300,
                 owner_supervisor_allowance_per_attempt=30,
                 native_launch_shell_allowance_per_attempt=5,
                 controller_command_allowance_seconds=1,
                 scientific_admission=False, automatic_next_stage=False)
    freeze(controller/'SETUP.json', setup)
    return dict(status='prepared', root=str(controller), next_command='launch reference', native_started=False)


def launch_one(controller, stage):
    setup = checked_setup(controller)
    prior_stage(controller, stage)
    root = stage_root(controller, stage)
    if root.exists() or (controller/(stage+'-LAUNCH.json')).exists():
        raise ValueError('Existing stage is inspection-only; no automatic retry')
    reference = stage_root(controller, 'reference')/'COMPLETE.json'
    pins = dict(setup['pins'])
    if stage == 'reference':
        module, inputs, config = FIXTURE, {}, dict(constructed_fixture=True)
        cap = setup['reference_cpu_cap']
    else:
        if read(controller/'reference-INSPECTED.json').get('passed') is not True:
            raise ValueError('Counted complete reference fixture required')
        assert_old(controller, 'reference')
        module, inputs = WRAPPER, dict(fixture_completion=str(reference))
        config = dict(constructed_fixture=True, component=stage.split('-')[0], max_new_draws=1000000000)
        cap = setup['successor_attempt_cpu_cap']
        pins[str(reference)] = filehash(reference)
        for name,digest in read(reference)['outputs'].items():
            # The entire immutable reference is the qualification input, not
            # merely its top-level completion marker or a claimed source count.
            pins[str(reference.parent/name)] = digest
    plan = dict(campaign='S15-WEEK5', card=root.name, family='CH', module=module,
                inputs=inputs, config=config, design=setup['design'],
                reviewed_design_commit=setup['reviewed_design_commit'], pins=pins,
                owner_reviewed=True, fixture_passed=True,
                validation_receipts=setup['validation_receipts'],
                paid=False, gpu=False, ollama=False, numerical_threads=2,
                max_cpu_seconds=cap, max_wall_seconds=1800 if stage == 'reference' else 1200,
                projected_peak_ram_GiB=2, max_output_bytes=2*1024**3,
                premortem=dict(case_and_check='Constructed exact original-output parity, native transactional pilot pauses and complete fresh source-zero replay.',
                              smaller_route='Retain failure/interruption and all costs; stop this qualification sequence for owner review.'))
    if stage.endswith('-verify-pilot') or stage.endswith('-complete'):
        predecessor = STAGES[STAGES.index(stage)-1]
        old = stage_root(controller, predecessor)
        assert_old(controller, predecessor)
        plan['resume'] = dict(root=str(old), plan_sha256=filehash(old/'PLAN.json'),
                              paused_sha256=filehash(old/'PAUSED.json'))
    # Admission is rechecked by launch and again under the native slot mutex.
    # A refusal leaves evidence and never schedules an unattended later start.
    launcher.review(plan)
    policy.admission(plan)
    root.mkdir(parents=True, exist_ok=False)
    freeze(root/'PLAN.json', plan)
    try:
        receipt = launcher.launch(root)
    except BaseException as error:
        freeze(controller/(stage+'-LAUNCH_REFUSED.json'), dict(at=now(), error=repr(error),
                                                              root=str(root), automatic_retry=False))
        raise
    freeze(controller/(stage+'-LAUNCH.json'), receipt)
    return dict(status='launched_one_stage', stage=stage, **receipt,
                next_action='Wait for durable terminal delivery, then inspect this same stage. No next stage launched.')


def inspect_one(controller, stage):
    checked_setup(controller)
    prior_inspection = controller/(stage+'-INSPECTED.json')
    if prior_inspection.exists():
        assert_old(controller, stage)
        return read(prior_inspection)
    root = stage_root(controller, stage)
    terminals = [(name, root/(name+'.json')) for name in ('COMPLETE', 'PAUSED', 'FAILED', 'MONITOR_FAILED')
                 if (root/(name+'.json')).exists()]
    if not terminals:
        return dict(status='no_terminal_yet', stage=stage, native_started=False)
    if len(terminals) != 1:
        raise ValueError('Ambiguous terminal records; retain all evidence for owner review')
    terminal, terminal_path = terminals[0]
    receipt = read(terminal_path)
    owner = read(root/'OWNER.json')['native']
    identities = {'owner':owner}
    for phase in ('EXECUTE', 'VERIFY'):
        for suffix in ('CHILD', 'NATIVE'):
            path = root/(phase+'_'+suffix+'.json')
            if path.exists():
                identities[phase+'_'+suffix] = read(path)['native']
    live = [name for name,native in identities.items() if is_same_live_process(native)]
    if live:
        return dict(status='terminal_written_native_exit_pending', stage=stage, live_roles=live)
    leases = [str(p) for p in policy.lease_paths()
              if read(p).get('native') == owner or read(p).get('attempt_root') == str(root)]
    if leases:
        return dict(status='native_exited_lease_release_pending', stage=stage, leases=leases)
    expected = 'PAUSED' if stage.endswith('-pilot') else 'COMPLETE'
    passed = terminal == expected
    reasons = []
    if not passed:
        reasons.append('Unexpected terminal '+terminal+'; no automatic healing or advance')
    if read(root/'OWNER.json')['plan_sha256'] != filehash(root/'PLAN.json'):
        raise ValueError('Native owner is not bound to this plan')
    usages = {}
    for phase in ('EXECUTE', 'VERIFY'):
        if (root/(phase+'_CHILD.json')).exists():
            path = root/(phase+'_JOB_USAGE.json')
            if not path.exists():
                passed = False
                reasons.append('Missing '+phase+' descendant accounting')
                continue
            value = read(path)
            cost = policy.finite(value['cpu_seconds'])
            if value.get('exit_code') != 0 or value.get('includes_all_descendants_and_exited_processes') is not True:
                passed = False
                reasons.append('Native child exit/accounting failure in '+phase)
            usages[phase] = dict(cpu_seconds=cost, receipt_sha256=filehash(path), exit_code=value.get('exit_code'))
            environment = read(root/(phase+'_ENVIRONMENT.json'))
            if (environment.get('threads') != 2 or environment.get('cuda_visible') != ''
                    or any(pool['num_threads'] > 2 for pool in environment.get('pools', []))):
                passed = False
                reasons.append('Actual numerical environment differs in '+phase)
    if not usages or abs(sum(x['cpu_seconds'] for x in usages.values())-policy.finite(receipt.get('cpu_seconds',0))) > 1e-8:
        passed = False
        reasons.append('Terminal cost is not reconciled with descendant receipts')
    sys.path.insert(0, str(REPO/'tools'))
    from tools.codex_watch import valid_json
    watch_config = read(REPO/'.agent-state/watch.json')
    watches = watch_config['process_watches']
    expected_paths = {(root/(name+'.json')).relative_to(REPO).as_posix()
                      for name in ('COMPLETE', 'FAILED', 'PAUSED', 'MONITOR_FAILED')}
    terminal_paths = expected_paths - {(root/'MONITOR_FAILED.json').relative_to(REPO).as_posix()}
    watcher = (any(w['native'] == owner and set(w.get('terminal_paths', [])) == terminal_paths
                   and w.get('failure_output') == (root/'MONITOR_FAILED.json').relative_to(REPO).as_posix()
                   for w in watches)
               and expected_paths <= set(watch_config['paths'])
               and expected_paths <= set(watch_config['urgent_paths'])
               and read(root/'MONITOR_READY.json')['owner_sha256'] == filehash(root/'OWNER.json'))
    if not watcher or not valid_json(terminal_path):
        passed = False
        reasons.append('Watcher identity registration or actual terminal schema failed')
    plan = read(root/'PLAN.json')
    if 'resume' in plan:
        old = Path(plan['resume']['root'])
        old_stage = STAGES[STAGES.index(stage)-1]
        assert_old(controller, old_stage)
        copied = read(root/'RESUMED_FROM.json')
        if copied['copied'] != output_manifest(old/'output') or copied['copied'] != read(old/'PAUSED.json')['checkpoint_outputs']:
            raise ValueError('Whole immutable output checkpoint was not copied')
    pilot = None
    if passed and expected == 'PAUSED':
        phase = 'execute' if stage.endswith('-execute-pilot') else 'verify'
        result = read(root/('RESULT.json' if phase == 'execute' else 'VERIFIED.json'))
        pilot = result.get('qualification_pilot')
        if (receipt.get('paused_operation') != phase or not pilot
                or pilot['operation'] != phase or pilot['source_units'] >= pilot['source_total']
                or pilot['source_units'] <= 0 or pilot.get('constructed_fixture_only') is not True):
            passed = False
            reasons.append('Required actual nonterminal pilot phase was not exercised')
        if receipt.get('checkpoint_outputs') != output_manifest(root/'output'):
            raise ValueError('Paused checkpoint is not complete and immutable')
    if passed and expected == 'COMPLETE':
        verify = read(root/'VERIFIED.json')
        if verify.get('verified') is not True or receipt.get('fresh_process_verified') is not True:
            raise ValueError('Fresh native verification is missing')
        for name,digest in receipt['outputs'].items():
            if filehash(root/name) != digest:
                raise ValueError('Completed artifact binding differs')
        if stage != 'reference':
            proof = read(root/'output/QUALIFICATION_FINAL.json')
            if proof != verify or proof.get('scientific_admission') is not False:
                raise ValueError('Final original-parity qualification proof missing')
    snapshot = dict(at=now(), root=str(root), files=manifest(root))
    inspection = dict(at=now(), stage=stage, root=str(root), passed=passed, reasons=reasons,
                      terminal=terminal, terminal_sha256=filehash(terminal_path),
                      native_identities=identities, all_native_exited=True, leases_released=True,
                      watcher_registered=watcher, terminal_schema=bool(valid_json(terminal_path)),
                      job_usages=usages, terminal_cpu_seconds=receipt.get('cpu_seconds'),
                      pilot=pilot, predecessor_immutable='resume' in plan,
                      scientific_admission=False, automatic_next_stage=False)
    freeze(snapshot_path(controller, stage), snapshot)
    freeze(controller/(stage+'-INSPECTED.json'), inspection)
    return inspection


def finalize(controller):
    setup = checked_setup(controller)
    inspections = []
    for stage in STAGES:
        value = read(controller/(stage+'-INSPECTED.json'))
        if value.get('passed') is not True:
            raise ValueError('Incomplete or failed qualification chain')
        assert_old(controller, stage)
        inspections.append(value)
    commands = [read(p) for p in sorted((controller/'commands').glob('*.json'))]
    measured = sum(float(v['terminal_cpu_seconds']) for v in inspections)
    driver = sum(float(v['controller_cpu_seconds']) for v in commands)
    result = dict(at=now(), passed=True, constructed=True, scientific_admission=False,
                  one_stage_at_a_time=True, automatic_launch_or_retry=False,
                  original_files_unchanged=True, full_checkpoint_copies_verified=True,
                  all_native_exits_and_leases_verified=True,
                  all_three_execute_and_fresh_verify_pilots=True,
                  exact_frozen_original_parity=True,
                  actual_pilot_fractions={v['stage']:v['pilot']['observed_fraction'] for v in inspections if v['pilot']},
                  measured_descendant_cpu_seconds=measured, measured_controller_cpu_seconds=driver,
                  conservative_supervisor_allowance_seconds=10*setup['owner_supervisor_allowance_per_attempt'],
                  conservative_launch_shell_allowance_seconds=10*setup['native_launch_shell_allowance_per_attempt'],
                  controller_tail_allowance_seconds=(len(commands)+1)*setup['controller_command_allowance_seconds'],
                  finalization_process_cpu_so_far_seconds=time.process_time(),
                  attempts=[dict(stage=v['stage'], root=v['root'], terminal=v['terminal'],
                                 cpu_seconds=v['terminal_cpu_seconds'], inspection_sha256=filehash(controller/(v['stage']+'-INSPECTED.json')))
                            for v in inspections],
                  design_commit=setup['reviewed_design_commit'], pins=setup['pins'])
    freeze(controller/'QUALIFICATION.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('init', 'launch', 'inspect', 'finalize'))
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--stage', choices=STAGES)
    parser.add_argument('--commit')
    parser.add_argument('--validation', action='append', default=[])
    args = parser.parse_args()
    root = checked_controller(args.root)
    try:
        if args.command == 'init':
            if not args.commit:raise ValueError('Reviewed committed design required')
            result = initialize(root, args.commit, args.validation)
        elif args.command == 'launch':
            if args.stage is None:raise ValueError('Explicit single stage required')
            result = launch_one(root, args.stage)
        elif args.command == 'inspect':
            if args.stage is None:raise ValueError('Explicit stage required')
            result = inspect_one(root, args.stage)
        else:
            result = finalize(root)
        print(json.dumps(result, sort_keys=True))
    finally:
        if (root/'SETUP.json').exists():
            commands = root/'commands'
            commands.mkdir(exist_ok=True)
            freeze(commands/(uuid.uuid4().hex+'.json'), dict(at=now(), command=args.command,
                   stage=args.stage, controller_cpu_seconds=time.process_time(),
                   process_accounting='whole current controller process before receipt write',
                   scientific_execution_in_controller=False))


if __name__ == '__main__':main()
