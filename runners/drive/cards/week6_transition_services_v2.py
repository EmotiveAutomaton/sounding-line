"""Fail-closed R18 ledger transition; no stop, resume, launch or registry write.

DESIGN CHECK: LESSONS 3-5. Live, inaccessible, unexplained or changed legacy
readers refuse before any new-family ledger member exists. A reviewed exact
clock-only calendar is compatible. Numerical outcomes never affect this gate.
"""
from datetime import datetime, timezone
from pathlib import Path
import os
import stat
import psutil
from .batch_runtime import REPO, read, filehash, check_files
from runners.stage9.process_identity import native_identity

EPOCH = 'week6-extension-v2'
CALENDAR = REPO/'runners/drive/calendar_20261115_week6.py'
CALENDAR_SHA256 = '24f88b9ec7dfef045e6f04f1d7e754ea6af73b997e10296e73af9c7ba72211fa'
LEGACY_READERS = (
    'week6_runtime_v1', 'week6_runtime_v2', 'week6_launch_v1', 'week6_launch_v2',
    'week6_policy_v1', 'week6_policy_v2', 'tr2_b2_archive_runtime_v1',
)
NEW_READERS = ('week6_runtime_extension_v2', 'week6_launch_extension_v2',
               'tr2_b2_archive_runtime_extension_v2')
REQUIRED_SOURCES = tuple(REPO/name for name in (
    'runners/drive/cards/week6_policy_v1.py', 'runners/drive/cards/week6_policy_v2.py',
    'runners/drive/cards/week6_limits_v1.py', 'runners/drive/cards/week6_limits_v2.py',
    'runners/drive/cards/week6_runtime_v1.py', 'runners/drive/cards/week6_runtime_v2.py',
    'runners/drive/cards/tr2_b2_archive_runtime_v1.py',
    'runners/drive/cards/week6_child_v1.py', 'runners/drive/cards/week6_resume_v1.py',
    'runners/drive/cards/week6_policy_extension_v2.py',
    'runners/drive/cards/week6_limits_extension_v2.py',
    'runners/drive/cards/week6_runtime_extension_v2.py',
    'runners/drive/cards/tr2_b2_archive_runtime_extension_v2.py',
    'runners/drive/cards/week6_transition_extension_v2.py',
    'runners/drive/week6_launch_v1.py', 'runners/drive/week6_launch_v2.py',
    'runners/drive/week6_launch_extension_v2.py', 'runners/drive/calendar_20261115_week6.py',
    'docs/design/stage-15/week6/PACKET_EXTENSION_2026-11-15.md',
    'docs/design/stage-15/week6/EXECUTION_ADDENDUM.md'))
REQUIRED_SOURCES += tuple(REPO/name for name in (
    'runners/drive/cards/week6_transition_services_v1.py',
    'runners/drive/cards/week6_process_services_v1.py',
    'runners/drive/cards/week6_policy_services_v1.py',
    'runners/drive/cards/week6_runtime_services_v1.py',
    'runners/drive/cards/tr2_b2_archive_runtime_services_v1.py',
    'runners/drive/week6_launch_services_v1.py',
))
METADATA_SUFFIXES = ('_NATIVE.json', '_CHILD.json', '_OWNED.json', '_READY.json',
                     '_MEMBER.json', '_LAUNCH_MEMBER.json', '_CLOSED.json',
                     '_EXIT.json', '_JOB_USAGE.json', '_JOB_EMPTY.json')


def need(value, message):
    if not value:
        raise ValueError(message)


def regular(path):
    path = Path(path); info = path.lstat()
    need(not (stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0)&0x400), 'Linked transition evidence')
    need(stat.S_ISREG(info.st_mode), 'Nonregular transition evidence')
    return path


def directories(root):
    info = Path(root).lstat()
    need(stat.S_ISDIR(info.st_mode) and not (stat.S_ISLNK(info.st_mode) or
         getattr(info, 'st_file_attributes', 0)&0x400), 'Linked or non-directory campaign root')
    for path in Path(root).iterdir():
        info = path.lstat()
        need(not (stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0)&0x400), 'Linked campaign member')
        if stat.S_ISDIR(info.st_mode):
            yield path


def has(path):
    try:
        regular(path); return True
    except FileNotFoundError:
        return False


def native_records(value):
    """Collect exact identities from bounded operational metadata, never outputs."""
    if isinstance(value, dict):
        if {'pid', 'created_ticks', 'executable'} <= set(value):
            yield {key:value[key] for key in ('pid', 'created_ticks', 'executable')}
        else:
            for item in value.values():
                yield from native_records(item)
    elif isinstance(value, list):
        for item in value:
            yield from native_records(item)


def require_exited(record):
    current = native_identity(record['pid'])
    # Native identity errors propagate; PID reuse is distinct from an exit guess.
    need(current is None or current != record, 'Legacy accounting reader remains live')


def legacy_inventory(root):
    result = {}
    for directory in directories(root):
        path = directory/'PLAN.json'
        if not has(path):
            continue
        plan = read(path)
        if plan.get('campaign') != 'S15-WEEK6' or plan.get('accounting_runtime') == EPOCH:
            continue
        pins = {'PLAN.json':filehash(path)}; natives = {}
        claimed = has(directory/'ATTEMPT.claim'); owned = has(directory/'OWNER.json')
        if claimed or owned:
            need(owned, 'Legacy attempt has no native owner')
            owner = read(directory/'OWNER.json')
            need(owner.get('plan_sha256') == pins['PLAN.json'], 'Legacy owner/plan binding differs')
            terminals = [name for name in ('COMPLETE.json', 'FAILED.json', 'PAUSED.json') if has(directory/name)]
            need(len(terminals) == 1, 'Legacy reader requires one authenticated terminal')
            terminal = read(directory/terminals[0])
            need(terminal.get('status') == terminals[0][:-5], 'Legacy terminal status differs')
            from .week6_policy_v2 import finite
            finite(terminal['cpu_seconds'])
            pins.update({name:filehash(directory/name) for name in ('OWNER.json', terminals[0])})
            if claimed:
                pins['ATTEMPT.claim'] = filehash(directory/'ATTEMPT.claim')
            locations = [directory]
            phases = directory/'phases'
            if phases.exists():
                locations.extend(directories(phases))
            for location in locations:
                for metadata in location.iterdir():
                    if not metadata.name.endswith(METADATA_SUFFIXES):
                        continue
                    regular(metadata); value = read(metadata)
                    pins[metadata.relative_to(directory).as_posix()] = filehash(metadata)
                    for identity in native_records(value):
                        natives[str(identity['pid'])+':'+str(identity['created_ticks'])] = identity
            identity = owner['native']; natives[str(identity['pid'])+':'+str(identity['created_ticks'])] = identity
            for identity in natives.values():
                require_exited(identity)
        result[directory.name] = {'pins':pins, 'native_identities':natives, 'claimed':claimed, 'owned':owned}
    return result


def calendar_compatibility(record):
    """One exact reviewed clock-only implementation; no general import exemption."""
    root = Path(record['root']).resolve(); root.relative_to(REPO)
    regular(root/'PLAN.json'); regular(root/'OWNER.json')
    need(filehash(CALENDAR) == CALENDAR_SHA256, 'Unreviewed calendar source')
    need(filehash(root/'PLAN.json') == record['plan_sha256'], 'Calendar plan differs')
    need(filehash(root/'OWNER.json') == record['owner_sha256'], 'Calendar owner differs')
    plan = read(root/'PLAN.json'); owner = read(root/'OWNER.json')
    need(plan.get('calendar_only') is True and plan.get('research_dispatch') is False,
         'Calendar can dispatch or is not clock-only')
    need(plan.get('campaign') == 'S15-WEEK6-calendar', 'Calendar campaign differs')
    need(owner.get('plan_sha256') == record['plan_sha256'] and owner['native'] == record['native'],
         'Calendar native binding differs')
    need(plan['pins'].get(str(CALENDAR)) == CALENDAR_SHA256, 'Calendar exact source is not pinned')
    check_files(plan['pins'])
    return owner['native']


def classify_process(command, cwd, repo=REPO):
    """Unknown workspace Python helpers cannot receive a policy exemption."""
    text = ' '.join(command).lower().replace('\\', '/')
    in_repo = str(repo).lower().replace('\\', '/') in text
    try:
        in_repo = in_repo or Path(cwd).resolve().is_relative_to(Path(repo).resolve())
    except (TypeError, ValueError):
        pass
    if any(name.lower() in text for name in LEGACY_READERS):
        return 'legacy'
    module = command[command.index('-m')+1] if '-m' in command and command.index('-m')+1<len(command) else None
    if module and module.rsplit('.', 1)[-1] in NEW_READERS:
        return 'extension'
    return 'unknown_workspace' if in_repo else 'outside_workspace'


def check_process_census(compatible, root, *, services, images, companions):
    from . import week6_process_services_v1 as service
    from . import week6_companion_proof_v1 as companion
    proofs=[companion.reader_compatibility(row) for row in companions]
    allowed = list(compatible)+[native for group in proofs for native in group]
    for row in services:
        value=service.watcher_compatibility(row)
        if value is not None:allowed.append(value)
    for directory in directories(root):
        if not has(directory/'PLAN.json'):continue
        plan=read(directory/'PLAN.json')
        if plan.get('campaign')!='S15-WEEK6' or plan.get('accounting_runtime')!=EPOCH:continue
        metadata=('OWNER.json','EXECUTE_NATIVE.json','VERIFY_NATIVE.json','EXECUTE_CHILD.json','VERIFY_CHILD.json')
        if any(has(directory/name) for name in metadata):
            need(has(directory/'OWNER.json'),'Extension native proof lacks owner binding')
        if has(directory/'OWNER.json'):
            need(read(directory/'OWNER.json').get('plan_sha256')==filehash(directory/'PLAN.json'),
                 'Extension owner/plan binding differs')
        for name in metadata:
            if has(directory/name):allowed.extend(native_records(read(directory/name)))
    # There is deliberately no command-only pre-OWNER exemption. This runtime
    # publishes OWNER before claim; another unowned reader causes a safe refusal.
    service.check_census(allowed, classify_process, images)
    for row in services:service.watcher_compatibility(row)
    need(proofs==[companion.reader_compatibility(row) for row in companions],
         "Companion ownership changed during census")


def require_transition(review_path, review_sha256, root, *, at=None):
    path = regular(Path(review_path).resolve())
    need(filehash(path) == review_sha256, 'Migration review changed')
    review = read(path); root = Path(root).resolve()
    need(review.get('schema') == 'WEEK6_R18_COMPANION_TRANSITION_REVIEW_V1' and review.get('epoch') == EPOCH,
         'Wrong authenticated migration')
    need(review.get('owner_reviewed') is True and review.get('full_write_through') is True,
         'Owner review and full legacy filing required')
    need(Path(review['campaign_root']).resolve() == root, 'Different migration campaign')
    at = at or datetime.now(timezone.utc); stamp = datetime.fromisoformat(review['at'])
    need(at.tzinfo is not None and stamp.tzinfo is not None and stamp <= at, 'Invalid migration clock')
    need(review.get('legacy_launchers_retired_from_owner_workflow') is True,
         'Legacy launchers and budget writers have not been retired')
    need(review.get('source_pins'), 'Migration source closure missing')
    need(isinstance(review.get('pending_preparation'), dict), 'Explicit pending preparation inventory required')
    for pending in review['pending_preparation'].values():
        need(pending.get('evidence_pins'), 'Pending preparation cost evidence missing')
        check_files(pending['evidence_pins'])
    need(all(review['source_pins'].get(str(p.resolve())) == filehash(p) for p in REQUIRED_SOURCES),
         'Migration omitted or changed required reader/runtime/authority pins')
    check_files(review['source_pins'])
    actual = legacy_inventory(root)
    need(review['legacy_inventory'] == actual, 'Legacy reader inventory changed or incomplete')
    for name, item in actual.items():
        if not (item['claimed'] or item['owned']):
            continue
        receipt = review['filing_receipts'][name]; receipt_path = regular(receipt['path'])
        need(filehash(receipt_path) == receipt['sha256'], 'Legacy filing receipt changed')
        filed = read(receipt_path)
        need(filed.get('full_write_through') is True and filed.get('accounting_reconciled') is True,
             'Legacy failed/native costs are not fully reconciled')
        need(Path(filed['attempt_root']).resolve() == root/name and filed['terminal_pins'] == item['pins'],
             'Legacy filing does not bind exact terminal/native evidence')
    for name, pin in review['baseline_budget_pins'].items():
        candidate = regular(root/'_budgets'/name)
        need(filehash(candidate) == pin, 'Original immutable budget ancestry changed')
    calendars = [calendar_compatibility(row) for row in review['compatible_calendars']]
    check_process_census(calendars, root, services=review['compatible_services'],
                         images=review['python_forwarder_images'], companions=review['compatible_companions'])
    return review

REQUIRED_SOURCES += tuple(REPO/name for name in ('runners/drive/cards/week6_policy_services_v2.py', 'runners/drive/cards/week6_runtime_services_v2.py', 'runners/drive/cards/week6_transition_services_v2.py', 'runners/drive/week6_launch_services_v2.py', 'runners/drive/cards/week6_companion_proof_v1.py'))
