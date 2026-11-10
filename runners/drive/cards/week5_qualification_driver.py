"""One reviewed native qualification attempt, with evidence and budget refusal.

No automatic source creation, stage choice, continuation or human admission.
An owner-written admission binds the precise attempt, inputs, module, design,
component/source proofs and remaining original card/family CPU allowances.
"""
from pathlib import Path
import argparse
import json
from . import week5_runtime_v7 as runtime
from .batch_runtime import REPO, freeze, read, filehash
from .week5_runtime_v5_fixture import wait
from .week5_resume_v2 import output_manifest
from .week5_go3_collection_counted_fixture_v2 import all_bytes
from .. import week5_launch_v7 as launch
from runners.theory_days.launch import closure
from runners.stage9.process_identity import is_same_live_process

SPECS = {
    'IN3.ic': ('IN', 2500, 60000, 'runners.drive.cards.week5_in_sensitivity_fixture_v2'),
    'IN4.ic': ('IN', 5000, 60000, 'runners.drive.cards.week5_in_sensitivity_fixture_v2'),
    'SP3.ic': ('SP', 5000, 40000, 'runners.drive.cards.week5_sp3_ic_fixture_v2'),
    'MD3.s': ('MD', 1800, 34400, 'runners.drive.cards.week5_md3_followup_fixture_v2'),
    'MD3.m': ('MD', 1800, 34400, 'runners.drive.cards.week5_md3_followup_fixture_v2'),
    'MD3.p': ('MD', 1800, 34400, 'runners.drive.cards.week5_md3_followup_fixture_v2'),
}


def proof(path, digest):
    path = Path(path).resolve()
    if filehash(path) != digest:
        raise ValueError('Qualification evidence changed')
    value = read(path)
    if value.get('verified') is not True and value.get('passed') is not True:
        raise ValueError('Passing reviewed qualification evidence required')
    return path, value


def source_proof(receipt, item):
    path, value = proof(item['path'], item['sha256'])
    if receipt['card'].startswith('IN'):
        if (value.get('constructed_only') is not True or value.get('IN3_IN4_actual_execute_verify') is not True
                or value.get('calibration_worlds_per_effect') != 5 or value.get('draws') != 2000
                or value.get('reachable_sensitivity_failure') is not True):
            raise ValueError('Preserved IN source/branch qualification witness absent')
        source = REPO / 'runners/drive/cards/week5_in_followup.py'
        if value.get('module_sha256') != filehash(source):
            raise ValueError('Preserved IN source consumer pin differs')
        return [path]
    if path.name != 'VERIFIED.json' or value.get('complete_fixture_sources_independently_replayed') is not True or value.get('constructed_only') is not True:
        raise ValueError('Actual independently completed fixed source constructor required')
    root = path.parent
    done = read(root / 'COMPLETE.json')
    if done.get('status') != 'COMPLETE' or done.get('fresh_process_verified') is not True or any((root / name).exists() for name in ('FAILED.json', 'PAUSED.json')):
        raise ValueError('Constructed source native terminal is incomplete or ambiguous')
    source_plan = read(root / 'PLAN.json')
    if source_plan['module'] != 'runners.drive.cards.week5_qualification_sources' or source_plan['config'] != dict(phase='prepare', family=SPECS[receipt['card']][0]):
        raise ValueError('Constructed source has another producer')
    paths = [root / 'COMPLETE.json']
    for name, digest in source_plan['pins'].items():
        source = Path(name).resolve()
        if filehash(source) != digest:
            raise ValueError('Original constructed-source dependency changed')
        paths.append(source)
    for name, digest in done['outputs'].items():
        source = (root / name).resolve()
        source.relative_to(root.resolve())
        if filehash(source) != digest:
            raise ValueError('Complete fixed constructed source output changed')
        paths.append(source)
    for name in receipt['inputs'].values():
        relative = Path(name).resolve().relative_to(root.resolve()).as_posix()
        if relative not in done['outputs']:
            raise ValueError('Qualification input is not an output of its complete source proof')
    return paths


def check_admission(receipt):
    required = {'reviewed', 'attempt', 'card', 'operation', 'module', 'module_sha256', 'inputs', 'input_sha256',
                'config', 'design', 'design_sha256', 'design_commit', 'evidence', 'expected_terminal',
                'expected_operation', 'cpu_seconds', 'wall_seconds', 'ram_GiB', 'card_charged_cpu_seconds',
                'family_charged_cpu_seconds', 'cost_evidence', 'resume'}
    if set(receipt) != required or receipt['reviewed'] is not True or receipt['card'] not in SPECS:
        raise ValueError('Exact owner-reviewed qualification admission required')
    family, cap, family_cap, module = SPECS[receipt['card']]
    if receipt['operation'] not in ('sources', 'qualification'):
        raise ValueError('Only fixed constructed sources or qualification may run')
    if receipt['operation'] == 'sources':
        if family not in ('SP', 'MD'):
            raise ValueError('IN sources already have their preserved preparation proof')
        module = 'runners.drive.cards.week5_qualification_sources'
        if receipt['inputs'] or receipt['config'] != dict(phase='prepare', family=family):
            raise ValueError('Fixed source constructor configuration differs')
    if receipt['module'] != module:
        raise ValueError('Admission names an unregistered qualification module')
    module_path = REPO / (module.replace('.', '/') + '.py')
    if filehash(module_path) != receipt['module_sha256']:
        raise ValueError('Reviewed qualification module changed')
    design = Path(receipt['design']).resolve()
    design.relative_to(REPO)
    if filehash(design) != receipt['design_sha256'] or not receipt['design_commit']:
        raise ValueError('Exact reviewed committed design required')
    if set(receipt['inputs']) != set(receipt['input_sha256']):
        raise ValueError('Every constructed input requires an exact pin')
    for name, path in receipt['inputs'].items():
        if filehash(Path(path)) != receipt['input_sha256'][name]:
            raise ValueError('Constructed input pin changed')
    if not receipt['evidence']:
        raise ValueError('Component and source/runtime evidence are absent')
    if any(set(item) != {'role', 'path', 'sha256'} for item in receipt['evidence']):
        raise ValueError('Each qualification proof requires an explicit role')
    roles = [item['role'] for item in receipt['evidence']]
    required_roles = {'runtime'} if receipt['operation'] == 'sources' else {'component', 'source'}
    if not required_roles.issubset(roles) or len(roles) != len(set(roles)):
        raise ValueError('Required distinct runtime/component/source evidence roles are absent')
    evidence = []
    for item in receipt['evidence']:
        evidence.extend(source_proof(receipt, item) if item['role'] == 'source' else [proof(item['path'], item['sha256'])[0]])
    if not receipt['cost_evidence']:
        raise ValueError('Owner cost accounting evidence is absent')
    cost_paths = []
    for item in receipt['cost_evidence']:
        path = Path(item['path']).resolve()
        if filehash(path) != item['sha256']:
            raise ValueError('Owner cost accounting receipt changed')
        cost_paths.append(path)
    cpu, charged, family_charged = (float(receipt[key]) for key in ('cpu_seconds', 'card_charged_cpu_seconds', 'family_charged_cpu_seconds'))
    if any(not 0 <= value < float('inf') for value in (charged, family_charged)) or not 0 < cpu <= min(cap - charged, family_cap - family_charged):
        raise ValueError('Attempt exceeds original descendant or family remaining CPU ceiling')
    if receipt['operation'] == 'sources' and cpu > 60:
        raise ValueError('Constructed source preparation exceeds its bounded qualification envelope')
    if not 0 < float(receipt['wall_seconds']) <= 3600 or not 0 < float(receipt['ram_GiB']) <= 3:
        raise ValueError('Qualification wall/RAM envelope outside reviewed bounds')
    if receipt['expected_terminal'] not in ('PAUSED', 'COMPLETE') or receipt['expected_operation'] not in ('execute', 'verify', None):
        raise ValueError('Explicit expected native boundary required')
    if (receipt['expected_terminal'] == 'PAUSED') != (receipt['expected_operation'] in ('execute', 'verify')):
        raise ValueError('Expected terminal and operation boundary disagree')
    if receipt['operation'] == 'sources' and (receipt['resume'] is not None or receipt['expected_terminal'] != 'COMPLETE'):
        raise ValueError('Small fixed source preparation must complete as one bounded unit')
    name = receipt['attempt']
    if not name or any(character not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._' for character in name):
        raise ValueError('Invalid exact qualification attempt name')
    if receipt['operation'] == 'qualification':
        cfg, card = receipt['config'], receipt['card']
        if family == 'IN' and (set(cfg) != {'case', 'worlds', 'draws'} or cfg['worlds'] != 100 or cfg['draws'] != 2000 or cfg['case'] not in (card.split('.')[0], 'FAILURE')):
            raise ValueError('Full registered IN branch configuration required')
        if family == 'SP' and (set(cfg) - {'case', 'max_wall_seconds'} or cfg.get('case') not in ('exact', 'high-noise')):
            raise ValueError('Full registered SP sensitivity branch required')
        if family == 'MD' and (set(cfg) - {'phase', 'case', 'draws', 'max_wall_seconds', 'max_new_draws'} or cfg.get('phase') != card or cfg.get('draws') != 2000):
            raise ValueError('Full registered MD descendant branch required')
    return family, module, design, evidence, cost_paths


def predecessor_chain(root):
    result, seen = [], set()
    while root is not None:
        root = Path(root).resolve()
        root.relative_to(runtime.policy.ROOT.resolve())
        if root in seen:
            raise ValueError('Cyclic stopped qualification ancestry')
        seen.add(root)
        plan, paused = read(root / 'PLAN.json'), read(root / 'PAUSED.json')
        if paused['checkpoint_outputs'] != output_manifest(root / 'output'):
            raise ValueError('An ancestral stopped output manifest changed')
        result.append((root, paused))
        resume = plan.get('resume')
        if resume:
            parent = Path(resume['root'])
            if filehash(parent / 'PLAN.json') != resume['plan_sha256'] or filehash(parent / 'PAUSED.json') != resume['paused_sha256']:
                raise ValueError('Ancestral qualification identity changed')
            root = parent
        else:
            root = None
    return result


def main(admission_path):
    admission_path = Path(admission_path).resolve()
    receipt = read(admission_path)
    family, module, design, evidence, cost_paths = check_admission(receipt)
    root = runtime.policy.ROOT / receipt['attempt']
    if root.exists():
        raise ValueError('Qualification attempt already exists')
    paths = list(closure([module, *launch.MODULES, 'runners.drive.week5_launch_v7']))
    paths += [Path(__file__), admission_path, design, *evidence, *cost_paths, *map(Path, receipt['inputs'].values())]
    pins = {str(path.resolve()): filehash(path) for path in paths}
    previous = None
    previous_tree = None
    ancestors = []
    if receipt['resume'] is not None:
        resume = receipt['resume']
        if set(resume) != {'root', 'plan_sha256', 'paused_sha256'}:
            raise ValueError('Exact paused predecessor evidence required')
        previous = Path(resume['root']).resolve()
        previous.relative_to(runtime.policy.ROOT.resolve())
        if filehash(previous / 'PLAN.json') != resume['plan_sha256'] or filehash(previous / 'PAUSED.json') != resume['paused_sha256']:
            raise ValueError('Stopped predecessor identity changed')
        if any((previous / name).exists() for name in ('FAILED.json', 'COMPLETE.json')):
            raise ValueError('Only authentic unambiguous stopped predecessors may resume')
        old = read(previous / 'PLAN.json')
        for name, digest in old['pins'].items():
            if filehash(Path(name)) != digest or (name in pins and pins[name] != digest):
                raise ValueError('Original admitted source or branch pin changed')
            pins[name] = digest
        previous_tree = all_bytes(previous)
        ancestors = predecessor_chain(previous)
        charged = sum(float(terminal['cpu_seconds']) for _, terminal in ancestors)
        if charged > float(receipt['card_charged_cpu_seconds']) + 1e-8 or charged > float(receipt['family_charged_cpu_seconds']) + 1e-8:
            raise ValueError('Admission omitted known ancestral qualification CPU cost')
    validation_paths = [str(Path(item['path']).resolve()) for item in receipt['evidence']]
    plan = dict(campaign='S15-WEEK5', family=family, card=receipt['attempt'], module=module,
                inputs=receipt['inputs'], config=receipt['config'], design=str(design), reviewed_design_commit=receipt['design_commit'],
                pins=pins, fixture_passed=True, owner_reviewed=True, validation_receipts=validation_paths,
                paid=False, gpu=False, ollama=False, numerical_threads=2, max_cpu_seconds=receipt['cpu_seconds'],
                max_wall_seconds=receipt['wall_seconds'], projected_peak_ram_GiB=receipt['ram_GiB'],
                forecast_cpu_seconds=receipt['cpu_seconds'],
                premortem=dict(case_and_check='Only frozen constructed complete-grid qualification and native independent replay.',
                               smaller_route='Preserve exact source/output and failed costs; no reduced draw/world bank or gate change.'))
    if previous:
        plan['resume'] = receipt['resume']
    root.mkdir()
    freeze(root / 'PLAN.json', plan)
    freeze(root / 'QUALIFICATION_ADMISSION.json', receipt)
    launch_record = launch.launch(root)
    freeze(root / 'QUALIFICATION_LAUNCH.json', launch_record)
    name, terminal = wait(root)
    owner = read(root / 'OWNER.json')['native']
    if is_same_live_process(owner) or any(read(path).get('native') == owner for path in runtime.policy.lease_paths()):
        raise ValueError('Qualification owner/lease is still live')
    if previous and (all_bytes(previous) != previous_tree or read(root / 'RESUMED_FROM.json')['copied'] != read(previous / 'PAUSED.json')['checkpoint_outputs']):
        raise ValueError('Immutable predecessor or complete copied manifest differs')
    expected = name == receipt['expected_terminal']
    if name == 'PAUSED':
        if terminal['checkpoint_outputs'] != output_manifest(root / 'output'):
            raise ValueError('Incomplete qualification checkpoint manifest')
        expected &= terminal['paused_operation'] == receipt['expected_operation']
        output = root / 'output' if terminal['paused_operation'] == 'execute' else root / 'output/independent-replay'
        progress = output / 'QUALIFICATION_PROGRESS.json'
        pilot = read(progress).get('execute_pilot_complete') is True if progress.exists() else False
    elif name == 'COMPLETE':
        pilot = None
        for relative, digest in terminal['outputs'].items():
            if filehash(root / relative) != digest:
                raise ValueError('Complete qualification output changed')
        if read(root / 'VERIFIED.json').get('verified') is not True:
            raise ValueError('Explicit independent native verification absent')
    else:
        pilot = False
        expected = False
    full_chain = False
    if name == 'COMPLETE' and receipt['operation'] == 'qualification':
        witnessed = set()
        for prior_root, paused in ancestors:
            operation = paused['paused_operation']
            directory = prior_root / 'output' if operation == 'execute' else prior_root / 'output/independent-replay'
            progress = directory / 'QUALIFICATION_PROGRESS.json'
            if progress.exists() and read(progress).get('execute_pilot_complete') is True:
                witnessed.add(operation)
        full_chain = witnessed == {'execute', 'verify'}
        expected &= full_chain
    record = dict(attempt=str(root), terminal=name, expected_boundary=bool(expected), full_five_percent_pilot=pilot,
                  native=owner, cpu_seconds=terminal['cpu_seconds'], terminal_sha256=filehash(root / (name + '.json')),
                  admission_sha256=filehash(admission_path), all_prior_files_preserved=True,
                  only_this_attempt_ran=True, no_scientific_admission=True,
                  full_actual_execute_and_independent_verify_pilot_chain=full_chain)
    evidence_dir = REPO / '.agent-state/drive-20261107/qualification-attempts'
    evidence_dir.mkdir(parents=True, exist_ok=True)
    freeze(evidence_dir / (receipt['attempt'] + '.json'), record)
    print(json.dumps(record), flush=True)
    if not expected:
        raise ValueError('Unexpected native boundary retained; owner review required before any next attempt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('admission', type=Path)
    main(parser.parse_args().admission)
