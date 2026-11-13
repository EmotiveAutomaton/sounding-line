"""Constructed exact-format retirement evidence; never reads real attempt records.

The eleven old control-flow source files are copied as inert bytes. No copied
runtime is imported or launched. These invented identities prove no real exit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from . import week5_reader_retirement_v1 as checker
from . import week5_reader_retirement_profiles_v1 as profile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def repin(case):
    """Fixture-only reauthorization permits testing semantic, not only hash, gates."""
    root, authority_path = case['root'], case['authority_path']
    authority = read(authority_path)
    authority['metadata_sha256'] = {p.name: sha(p) for p in root.iterdir()
                                  if p.is_file() and (p.suffix == '.json' or p.name == 'ATTEMPT.claim')}
    authority['launch_evidence']['sha256'] = sha(case['launch_path'])
    write(authority_path, authority)
    case['authority_sha256'] = sha(authority_path)


def make_case(directory, status='COMPLETE', paused_operation='execute'):
    base = Path(directory).absolute()
    if base.exists():
        raise ValueError('Fresh constructed root required')
    repo = base / 'constructed-repository'
    root = repo / checker.CAMPAIGN / 'constructed-old-reader'
    root.mkdir(parents=True)
    for bank in checker.BANKS:
        (repo / bank).mkdir(parents=True)
    for rel, expected in profile.SOURCES.items():
        original = Path(__file__).resolve().parents[3] / rel
        if sha(original) != expected:
            raise ValueError('Original profile changed')
        destination = root / 'source_capsule' / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, destination)
    exe = str(repo / '.venv/Scripts/python.exe')
    owner = dict(pid=1001, created_ticks=100_000_001, executable=exe)
    operations = ['execute', 'verify'] if status == 'COMPLETE' or paused_operation == 'verify' else ['execute']
    plan = dict(campaign='S15-WEEK5', family='CH', card='constructed-retirement',
                module='constructed.no_human_handler', max_cpu_seconds=100,
                pins={str(repo / rel): expected for rel, expected in profile.SOURCES.items()})
    write(root / 'PLAN.json', plan)
    (root / 'ATTEMPT.claim').write_text('2026-11-13T10:00:00+00:00', encoding='utf-8')
    write(root / 'OWNER.json', dict(at='2026-11-13T10:00:00+00:00', native=owner, plan_sha256=sha(root / 'PLAN.json')))
    write(root / 'MONITOR_READY.json', dict(at='2026-11-13T10:00:01+00:00', owner_sha256=sha(root / 'OWNER.json'), watch_config_sha256='a'*64))
    lease = repo / checker.BANKS[1] / 'slot-4.json'
    write(root / 'ADMISSION.json', dict(lease=str(lease), threads=2, remaining_cpu_seconds=100))
    children = []
    for index, operation in enumerate(operations):
        upper = operation.upper()
        child = dict(pid=1010+index*2, created_ticks=100_000_010+index*2, executable=exe)
        worker = dict(pid=1011+index*2, created_ticks=100_000_011+index*2, executable=exe)
        children.extend((child, worker))
        at = '2026-11-13T10:00:02+00:00'
        write(root / (upper+'_CHILD.json'), dict(at=at, native=child))
        write(root / (upper+'_NATIVE.json'), dict(at=at, native=worker))
        write(root / (upper+'_ENVIRONMENT.json'), dict(pools=[], threads=2, cuda_visible=''))
        write(root / (upper+'_USAGE.json'), dict(at=at, cpu_seconds=.5, wall_seconds=1))
        cpu = float(index+1)
        write(root / (upper+'_JOB_USAGE.json'), dict(at=at, cpu_seconds=cpu, measured_cpu_seconds=cpu,
              termination_margin_cpu_seconds=0., includes_all_descendants_and_exited_processes=True,
              exit_code=1 if status == 'FAILED' and operation == operations[-1] else 0))
        if status != 'FAILED' or operation != operations[-1]:
            result = dict(verified=True) if operation == 'verify' else dict(status='complete')
            if status == 'PAUSED' and operation == operations[-1]:
                result = dict(status='yielded', checkpoint='constructed-only')
            write(root / ('RESULT.json' if operation == 'execute' else 'VERIFIED.json'), result)
    terminal = dict(at='2026-11-13T10:00:05+00:00', status=status, card=plan['card'],
                    cpu_seconds=sum(range(1,len(operations)+1)), scientific_admission=False)
    if status == 'COMPLETE':
        terminal.update(fresh_process_verified=True, outputs={p.name:sha(p) for p in root.iterdir()
                        if p.is_file() and p.name != 'MONITOR_READY.json'})
    elif status == 'PAUSED':
        terminal.update(paused_operation=operations[-1], checkpoint_validation_required=True,
                        checkpoint_outputs={'constructed-state.json':'b'*64})
    elif status == 'FAILED':
        terminal.update(error="RuntimeError('constructed failure')", failure_class='engineering',
                        accounting_reconciliation_required=False)
    else:
        raise ValueError('Unknown constructed terminal')
    write(root / (status+'.json'), terminal)
    review = repo / 'private-review'
    launch_path = review / 'recorded-launch.json'
    write(launch_path, dict(schema='week5-recorded-launch-provenance-v1', basis='recorded_at_launch',
          at='2026-11-13T10:00:01+00:00', attempt_root=str(root), native=owner,
          plan_sha256=sha(root/'PLAN.json'), runtime_module=profile.RUNTIME_MODULE,
          launcher_sha256=profile.LAUNCHER_SHA256,
          argv=[exe,'-X','utf8','-B','-m',profile.RUNTIME_MODULE,str(root)]))
    authority_path = review / 'owner-review-authority.json'
    write(authority_path, dict(schema='week5-reader-review-authority-v1', profile=profile.PROFILE_ID,
          constructed=True, repository=str(repo), attempt_root=str(root), metadata_sha256={},
          launch_evidence=dict(path=str(launch_path),sha256=sha(launch_path)),
          started_operations=operations,other_lease_sha256={}))
    case = dict(repository=repo, root=root, authority_path=authority_path,
                launch_path=launch_path, native=owner, children=children,
                terminal_name=status+'.json',lease_path=lease)
    repin(case)
    return case


def inspect(case, **extra):
    return checker.inspect_post_reader(case['root'], repository=case['repository'],
            authority_path=case['authority_path'], authority_sha256=case['authority_sha256'],
            constructed=True, **extra)


def snapshot(directory):
    return {p.relative_to(directory).as_posix():sha(p) for p in Path(directory).rglob('*') if p.is_file()}


def native_exit_record(case):
    path = case['authority_path'].parent / 'recorded-exit.json'
    write(path, dict(schema='week5-recorded-native-exit-v1', basis='retained_exact_native_handles',
          at='2026-11-13T10:00:06+00:00',attempt_root=str(case['root']),
          owner_sha256=sha(case['root']/'OWNER.json'),
          terminal_sha256=sha(case['root']/case['terminal_name']),
          identities=[dict(native=x,signalled_exit=True) for x in [case['native'],*case['children']]],
          contained_descendants_closed=True))
    return path


def execute(output, inputs, config):
    """Future constructed native fixture only; not admitted or run in this build."""
    if inputs or config != {'constructed_only': True}:
        raise ValueError('Only the frozen empty-input constructed fixture is supported')
    output = Path(output)
    case = make_case(output/'constructed-evidence')
    before = snapshot(case['repository'])
    result = inspect(case)
    if before != snapshot(case['repository']):
        raise ValueError('Checker modified constructed evidence')
    summary = dict(status='complete', reader_retired=result['accounting_reader_retired'],
                   native_owner_exit_verified=result['native_owner_exit_verified'],
                   retained_cpu_seconds=result['retained_cpu_seconds'], evidence_unchanged=True,
                   constructed_evidence=True, record_kind='run',theory_tags=[],by_construction=False,activation=[])
    write(output/'FIXTURE.json',summary)
    return summary


def verify(output, inputs, config):
    if inputs or config != {'constructed_only': True}:
        raise ValueError('Only the frozen empty-input constructed fixture is supported')
    output=Path(output)
    replay=execute(output/'independent-replay',inputs,config)
    if replay != read(output/'FIXTURE.json'):
        raise ValueError('Constructed independent replay differs')
    return dict(verified=True,constructed_evidence=True,record_kind='run',theory_tags=[],by_construction=False,activation=[])
