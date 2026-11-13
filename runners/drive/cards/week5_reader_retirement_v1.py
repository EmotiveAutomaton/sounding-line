"""Read-only, prospective exact-v8 accounting-reader retirement checker.

DESIGN CHECK: a terminal name, compatibility label, or inaccessible PID is not
retirement evidence. This module never queries processes or writes certificates.
Its caller supplies a separately reviewed authority file and expected digest.
Passing this checker is neither a transition admission nor checkpoint-copy consent.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import stat
from datetime import datetime

from . import week5_reader_retirement_profiles_v1 as profile

CAMPAIGN = 'results/phase_2_4_stage_15/raw/drive-week5-20261107'
BANKS = ('results/.cpu-slots-20261017', 'results/.cpu-slots-20261107')
TERMINALS = ('COMPLETE.json', 'PAUSED.json', 'FAILED.json')
OPERATIONS = ('execute', 'verify')
MAX_FILE_BYTES = 2 * 1024**2
MAX_TOTAL_BYTES = 64 * 1024**2
MAX_READS = 256


class RetirementRefusal(ValueError):
    """Evidence is unavailable, ambiguous, changed, or outside the reviewed profile."""


def need(condition, reason):
    if not condition:
        raise RetirementRefusal(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def valid_hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def number(value):
    need(type(value) in (int, float), 'Invalid accounting number')
    try:
        result = float(value)
    except OverflowError as exc:
        raise RetirementRefusal('Invalid accounting number') from exc
    need(math.isfinite(result) and result >= 0, 'Invalid accounting number')
    return result


def instant(value):
    try:
        result = datetime.fromisoformat(value)
        need(result.tzinfo is not None, 'Naive evidence time')
        return result
    except (TypeError, ValueError) as exc:
        raise RetirementRefusal('Invalid evidence time') from exc


def identity(value):
    need(isinstance(value, dict) and set(value) == {'pid', 'created_ticks', 'executable'}, 'Incomplete native identity')
    need(type(value['pid']) is int and value['pid'] > 0, 'Invalid native PID')
    need(type(value['created_ticks']) is int and value['created_ticks'] > 0, 'Invalid native birth identity')
    need(isinstance(value['executable'], str) and Path(value['executable']).is_absolute(), 'Invalid native executable')
    return value


def same_birth(left, right):
    return (left['pid'], left['created_ticks']) == (right['pid'], right['created_ticks'])


def relative(value):
    need(isinstance(value, str) and '\\' not in value and bool(value), 'Noncanonical relative evidence path')
    path = PurePosixPath(value)
    need(not path.is_absolute() and all(p not in ('.', '..') for p in path.parts)
         and path.as_posix() == value and ':' not in value, 'Unsafe relative evidence path')
    return value


def no_links(path):
    path = Path(path).absolute()
    for part in (*reversed(path.parents), path):
        info = part.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not (getattr(info, 'st_file_attributes', 0) & 0x400),
             'Reparse or symbolic evidence path')
    return path


def directory_inventory(path):
    no_links(path)
    # scandir/stat exceptions propagate as refusal, never a silently empty glob.
    entries = []
    with os.scandir(path) as scan:
        for entry in scan:
            info = entry.stat(follow_symlinks=False)
            need(not stat.S_ISLNK(info.st_mode) and not (getattr(info, 'st_file_attributes', 0) & 0x400), 'Reparse directory member')
            entries.append((entry.name, stat.S_IFMT(info.st_mode), info.st_size, info.st_mtime_ns))
            need(len(entries) <= 2048, 'Evidence inventory exceeds reviewed bound')
    return tuple(sorted(entries))


def json_object(data):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def constant(_):
        raise RetirementRefusal('Nonfinite JSON constant')
    value = json.loads(data.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    need(isinstance(value, dict), 'Evidence object required')
    return value


class Reader:
    def __init__(self):
        self.pins = {}
        self.bytes = 0
        self.reads = 0

    def bytes_at(self, path, expected):
        need(valid_hash(expected), 'Expected authenticated SHA-256 required')
        path = no_links(path)
        with path.open('rb') as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        self.reads += 1
        self.bytes += len(data)
        need(len(data) <= MAX_FILE_BYTES and self.bytes <= MAX_TOTAL_BYTES and self.reads <= MAX_READS,
             'Evidence read exceeds reviewed bound')
        need(digest(data) == expected, 'Changed or unauthenticated evidence: ' + path.name)
        previous = self.pins.setdefault(str(path), expected)
        need(previous == expected, 'Conflicting evidence aliases')
        return data

    def object_at(self, path, expected):
        return json_object(self.bytes_at(path, expected))

    def stable(self):
        for path, expected in tuple(self.pins.items()):
            self.bytes_at(path, expected)


def _review(attempt, repository, authority_path, authority_sha256, native_exit, constructed):
    reader = Reader()
    repo = no_links(repository)
    root = no_links(attempt)
    need(root.parent == repo / CAMPAIGN, 'Attempt is outside the exact campaign root')
    before = directory_inventory(root)
    names = {x[0] for x in before}
    need('ATTEMPT.claim' in names and 'OWNER.json' in names, 'Unclaimed or starting attempt')
    terminals = [x for x in TERMINALS if x in names]
    need(len(terminals) == 1, 'Unique terminal reconciliation required')
    terminal_name = terminals[0]
    authority = reader.object_at(authority_path, authority_sha256)
    need(authority.get('schema') == 'week5-reader-review-authority-v1', 'Unknown review authority')
    need(type(constructed) is bool and authority.get('constructed') is constructed, 'Constructed evidence requires explicit isolated-fixture mode')
    need(authority.get('profile') == profile.PROFILE_ID and authority.get('attempt_root') == str(root)
         and authority.get('repository') == str(repo), 'Authority scope/profile mismatch')
    pins = authority.get('metadata_sha256')
    need(isinstance(pins, dict), 'Missing authenticated metadata inventory')
    for name, value in pins.items():
        relative(name)
        need('/' not in name and valid_hash(value), 'Metadata must be bounded root-level records')
    def record(name):
        need(name in pins, 'Unpinned operational receipt: ' + name)
        return reader.object_at(root / name, pins[name])
    need('ATTEMPT.claim' in pins, 'Unpinned exclusive attempt claim')
    instant(reader.bytes_at(root / 'ATTEMPT.claim', pins['ATTEMPT.claim']).decode('utf-8').strip())
    plan, owner = record('PLAN.json'), record('OWNER.json')
    need(plan.get('campaign') == 'S15-WEEK5' and plan.get('family') in {'AT','CH','IN','SP','GO','MD','LA','ID','BK','EX'}, 'Unknown legacy family/campaign')
    need(plan.get('accounting_runtime') in (None, ''), 'Compatibility-label/profile spoof')
    native = identity(owner.get('native'))
    need(owner.get('plan_sha256') == pins['PLAN.json'], 'Owner/PLAN binding mismatch')
    monitor, admission, terminal = record('MONITOR_READY.json'), record('ADMISSION.json'), record(terminal_name)
    need(monitor.get('owner_sha256') == pins['OWNER.json'], 'Monitor/owner binding mismatch')
    need(valid_hash(monitor.get('watch_config_sha256')), 'Missing monitor provenance')
    need(terminal.get('status') + '.json' == terminal_name and terminal.get('card') == plan.get('card'), 'Terminal type/card mismatch')
    need(terminal.get('scientific_admission') is False, 'Unexpected legacy terminal schema')
    need(instant(owner['at']) <= instant(monitor['at']) <= instant(terminal['at']), 'Terminal chronology mismatch')

    launch_pin = authority.get('launch_evidence', {})
    launch = reader.object_at(launch_pin['path'], launch_pin['sha256'])
    need(launch.get('schema') == 'week5-recorded-launch-provenance-v1' and launch.get('basis') == 'recorded_at_launch', 'Actual launch provenance required; PLAN/capsule alone is insufficient')
    need(launch.get('attempt_root') == str(root) and launch.get('native') == native
         and launch.get('plan_sha256') == pins['PLAN.json'], 'Launch identity binding mismatch')
    need(launch.get('runtime_module') == profile.RUNTIME_MODULE and launch.get('launcher_sha256') == profile.LAUNCHER_SHA256,
         'Unreviewed actual entrypoint')
    expected_argv = [str(repo / '.venv/Scripts/python.exe'), '-X', 'utf8', '-B', '-m', profile.RUNTIME_MODULE, str(root)]
    need(launch.get('argv') == expected_argv, 'Actual launch command differs from reviewed entrypoint')
    need(instant(owner['at']) <= instant(launch['at']) <= instant(terminal['at']), 'Launch evidence chronology mismatch')
    plan_pins = plan.get('pins', {})
    need(isinstance(plan_pins, dict), 'Missing original source pin map')
    for rel, expected in profile.SOURCES.items():
        aliases = [value for key, value in plan_pins.items() if Path(key).is_absolute() and Path(key).absolute() == repo / rel]
        need(aliases and set(aliases) == {expected}, 'Missing/changed exact control-flow source pin: ' + rel)
        reader.bytes_at(root / 'source_capsule' / rel, expected)

    operations = authority.get('started_operations')
    need(operations in (['execute'], ['execute', 'verify']), 'Pre-child or ambiguous started-operation history is not covered by v1')
    if terminal_name == 'COMPLETE.json':
        need(operations == ['execute', 'verify'] and terminal.get('fresh_process_verified') is True, 'Incomplete complete-operation history')
    if terminal_name == 'PAUSED.json':
        need(terminal.get('paused_operation') == operations[-1] and terminal.get('checkpoint_validation_required') is True, 'Unbound paused operation')
        checkpoint = terminal.get('checkpoint_outputs')
        need(isinstance(checkpoint, dict), 'Missing pause manifest')
        for path, value in checkpoint.items():
            relative(path)
            need(valid_hash(value), 'Malformed checkpoint digest')
    if terminal_name == 'FAILED.json':
        need(terminal.get('accounting_reconciliation_required') is False and isinstance(terminal.get('error'), str)
             and terminal.get('failure_class') in {'engineering', 'environment', 'cost'}, 'Failed accounting remains unresolved')

    total = 0.0
    child_identities = []
    for operation in OPERATIONS:
        upper = operation.upper()
        receipt_names = [upper + suffix for suffix in ('_CHILD.json','_NATIVE.json','_JOB_USAGE.json','_USAGE.json','_ENVIRONMENT.json')]
        result_name = 'RESULT.json' if operation == 'execute' else 'VERIFIED.json'
        if operation not in operations:
            need(not any(name in names for name in (*receipt_names, result_name)), 'Unexpected later-operation evidence')
            continue
        child, worker, usage, local, environment = [record(name) for name in receipt_names]
        for value in (child, worker):
            ident = identity(value.get('native'))
            need(not same_birth(ident, native) and instant(owner['at']) <= instant(value['at']) <= instant(terminal['at']), 'Child identity/chronology mismatch')
            if ident not in child_identities:
                child_identities.append(ident)
        need(usage.get('includes_all_descendants_and_exited_processes') is True and type(usage.get('exit_code')) is int,
             'Unknown/forced child shutdown')
        need(number(usage.get('termination_margin_cpu_seconds')) == 0, 'Forced-child closure needs separate reconciliation')
        measured = number(usage.get('measured_cpu_seconds'))
        need(math.isclose(number(usage.get('cpu_seconds')), measured, rel_tol=0, abs_tol=1e-8), 'Job cost mismatch')
        total += measured
        need(number(local.get('cpu_seconds')) <= measured + 1e-8, 'Native child exceeds complete Job accounting')
        need(environment.get('threads') == 2 and environment.get('cuda_visible') == '', 'Unexpected child execution boundary')
        for item in (usage, local):
            need(instant(owner['at']) <= instant(item['at']) <= instant(terminal['at']), 'Accounting chronology mismatch')
        if terminal_name != 'FAILED.json' or result_name in names:
            result = record(result_name)
            if terminal_name == 'PAUSED.json' and operation == operations[-1]:
                need(result.get('status') == 'yielded', 'Paused child did not yield')
            elif operation == 'verify':
                need(result.get('verified') is True, 'Verification closure missing')
            need(usage['exit_code'] == 0, 'Result receipt with nonzero native exit')
    retained_cpu = number(terminal.get('cpu_seconds'))
    need(retained_cpu + 1e-8 >= total, 'Terminal undercounts child Job CPU')
    if terminal_name != 'FAILED.json':
        need(math.isclose(retained_cpu, total, rel_tol=0, abs_tol=1e-8), 'Terminal/Job CPU mismatch')
    if terminal_name == 'COMPLETE.json':
        outputs = terminal.get('outputs', {})
        need(isinstance(outputs, dict), 'Missing terminal operational manifest')
        for name, expected in pins.items():
            if name not in (terminal_name, 'MONITOR_READY.json'):
                need(outputs.get(name) == expected, 'Terminal operational manifest binding missing: ' + name)

    bank_snapshots = {}
    authenticated_leases = authority.get('other_lease_sha256', {})
    need(isinstance(authenticated_leases, dict), 'Missing lease review map')
    own_lease = Path(admission.get('lease', '')).absolute()
    expected_slots = {repo / bank / ('slot-' + str(i) + '.json') for bank, indices in zip(BANKS, (range(4), range(4,8))) for i in indices}
    need(own_lease in expected_slots and admission.get('threads') == 2, 'Admission lease is outside exact reviewed banks')
    for bank in BANKS:
        path = repo / bank
        bank_snapshots[str(path)] = directory_inventory(path)
        for name, mode, _, _ in bank_snapshots[str(path)]:
            if not name.startswith('slot-'):
                continue
            lease_path = path / name
            need(lease_path in expected_slots and mode == stat.S_IFREG, 'Unknown slot member')
            key = lease_path.relative_to(repo).as_posix()
            need(key in authenticated_leases, 'Unreviewed occupied/successor lease')
            lease = reader.object_at(lease_path, authenticated_leases[key])
            need(not same_birth(identity(lease.get('native')), native)
                 and Path(lease.get('attempt_root', '')).absolute() != root, 'Attempt-owned lease remains')
            need(isinstance(lease.get('attempt_root'), str) and bool(lease['attempt_root'])
                 and isinstance(lease.get('card'), str) and bool(lease['card']), 'Unbound successor lease')

    exit_verified = False
    if native_exit is not None:
        proof = reader.object_at(native_exit['path'], native_exit['sha256'])
        need(proof.get('schema') == 'week5-recorded-native-exit-v1' and proof.get('basis') == 'retained_exact_native_handles', 'Independent native-exit evidence required')
        need(proof.get('attempt_root') == str(root) and proof.get('owner_sha256') == pins['OWNER.json']
             and proof.get('terminal_sha256') == pins[terminal_name], 'Native-exit evidence binding mismatch')
        need(instant(proof['at']) >= instant(terminal['at']), 'Native exit precedes terminal')
        expected = [native, *child_identities]
        observed = proof.get('identities', [])
        need(isinstance(observed, list) and all(isinstance(x, dict) for x in observed), 'Malformed native-exit observations')
        need(len(observed) == len(expected) and all(any(x.get('native') == ident and x.get('signalled_exit') is True for x in observed) for ident in expected), 'Incomplete exact native-exit observations')
        need(proof.get('contained_descendants_closed') is True, 'Missing contained descendant closure')
        exit_verified = True
    reader.stable()
    need(directory_inventory(root) == before, 'Attempt inventory changed during review')
    for path, snapshot in bank_snapshots.items():
        need(directory_inventory(path) == snapshot, 'Lease inventory changed during review')
    return dict(schema='week5-reader-retirement-review-v1', profile=profile.PROFILE_ID,
                attempt_root=str(root), scope='campaign_accounting_reader_retired',
                evidence_route='observed_native_exit' if exit_verified else 'audited_post_reader_terminal',
                accounting_reader_retired=True, native_owner_exit_verified=exit_verified,
                scientific_validity_checked=False, checkpoint_copy_authorized=False,
                campaign_transition_admitted=False, terminal=terminal_name,
                constructed_evidence=constructed,
                retained_cpu_seconds=retained_cpu, child_job_cpu_seconds=total,
                existing_accounting_supervisor_charge_seconds=30.0,
                metadata_pins=dict(reader.pins), reads=reader.reads, bytes_read=reader.bytes,
                record_kind='run', theory_tags=[], by_construction=False, activation=[])


def inspect_post_reader(attempt, *, repository, authority_path, authority_sha256, constructed=False):
    """Read evidence only. Caller must hold the campaign admission lock in use."""
    try:
        return _review(attempt, repository, authority_path, authority_sha256, None, constructed)
    except (OSError, KeyError, TypeError, json.JSONDecodeError, UnicodeError) as exc:
        raise RetirementRefusal('Retirement evidence unavailable or malformed') from exc


def inspect_observed_exit(attempt, *, repository, authority_path, authority_sha256, exit_path, exit_sha256, constructed=False):
    """Separate stronger route: never infer OS exit from reader retirement."""
    try:
        return _review(attempt, repository, authority_path, authority_sha256,
                       dict(path=exit_path, sha256=exit_sha256), constructed)
    except (OSError, KeyError, TypeError, json.JSONDecodeError, UnicodeError) as exc:
        raise RetirementRefusal('Native-exit evidence unavailable or malformed') from exc
