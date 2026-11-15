"""Exact Job membership and two-role exit evidence for the AT queue.

DESIGN CHECK: LESSONS 3-5. Null/alternative share the same native proof. A
redirector is not its scorer. Unknown, nonmember, reused, live or nonempty
identities refuse. All operations address only the owned exact Job or handles.
This candidate has no scientific calculation and has not been tested.
"""
import ctypes
from ctypes import wintypes as W
from pathlib import Path
import time
from .batch_runtime import read, filehash
from .batch_runtime_v8 import JobAccounting
from runners.stage9.process_identity import native_identity


def need(value, message):
    if not value: raise ValueError(message)


def sample_job(worker):
    query = worker.kernel.QueryInformationJobObject
    query.argtypes = [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD, W.LPVOID]
    query.restype = W.BOOL
    info = JobAccounting()
    if not query(worker.job, 1, ctypes.byref(info), ctypes.sizeof(info), None):
        raise ctypes.WinError(ctypes.get_last_error())
    class Members(ctypes.Structure):
        _fields_ = [('assigned', W.DWORD), ('count', W.DWORD), ('ids', ctypes.c_size_t * 256)]
    members = Members()
    if not query(worker.job, 3, ctypes.byref(members), ctypes.sizeof(members), None):
        raise ctypes.WinError(ctypes.get_last_error())
    need(members.count <= 256 and members.assigned <= 256 and members.count <= members.assigned,
         'Incomplete owned Job membership enumeration')
    identities = []
    for pid in members.ids[:members.count]:
        identity = native_identity(pid)
        # A race to known exit is allowed; inaccessible/unknown raises.
        if identity is not None: identities.append(identity)
    return dict(cpu_seconds=(info.user + info.kernel) / 10000000,
                active_processes=info.active, assigned_processes=members.assigned,
                listed_process_ids=list(members.ids[:members.count]), identities=identities,
                total_processes=info.total, terminated_processes=info.terminated)


def prove_member(worker, expected):
    """Bind identity and Job membership on the same open native process handle."""
    kernel = worker.kernel
    for name, args, result in [
        ('OpenProcess', [W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
        ('GetProcessTimes', [W.HANDLE] + [ctypes.POINTER(W.FILETIME)] * 4, W.BOOL),
        ('QueryFullProcessImageNameW', [W.HANDLE, W.DWORD, W.LPWSTR, ctypes.POINTER(W.DWORD)], W.BOOL),
        ('IsProcessInJob', [W.HANDLE, W.HANDLE, ctypes.POINTER(W.BOOL)], W.BOOL),
        ('WaitForSingleObject', [W.HANDLE, W.DWORD], W.DWORD),
        ('CloseHandle', [W.HANDLE], W.BOOL)]:
        fn = getattr(kernel, name); fn.argtypes = args; fn.restype = result
    handle = kernel.OpenProcess(0x1000 | 0x100000, False, int(expected['pid']))
    if not handle: raise ctypes.WinError(ctypes.get_last_error())
    try:
        created, exited, system, user = (W.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user)):
            raise ctypes.WinError(ctypes.get_last_error())
        ticks = (created.dwHighDateTime << 32) | created.dwLowDateTime
        need(ticks == expected['created_ticks'] and not (exited.dwHighDateTime or exited.dwLowDateTime),
             'Job membership identity changed or exited')
        size = W.DWORD(32768); name = ctypes.create_unicode_buffer(32768)
        if not kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        need(Path(name.value).resolve() == Path(expected['executable']).resolve(),
             'Job membership executable changed')
        member = W.BOOL()
        if not kernel.IsProcessInJob(handle, worker.job, ctypes.byref(member)):
            raise ctypes.WinError(ctypes.get_last_error())
        need(bool(member.value), 'Native identity is not a member of owned Job')
        need(kernel.WaitForSingleObject(handle, 0) == 258, 'Member exited before authentication')
        return dict(native=expected, member_of_exact_owned_job=True,
                    identity_checked_on_membership_handle=True, known_live_when_authenticated=True)
    finally:
        kernel.CloseHandle(handle)


def empty(snapshot):
    return (snapshot['active_processes'] == 0 and snapshot['assigned_processes'] == 0 and
            snapshot['listed_process_ids'] == [] and snapshot['identities'] == [])


def terminate_and_drain(worker, remember):
    """Stop only this owned Job; retain accounting handle until verified empty."""
    terminate = worker.kernel.TerminateJobObject
    terminate.argtypes = [W.HANDLE, W.UINT]; terminate.restype = W.BOOL
    if not terminate(worker.job, 1): raise ctypes.WinError(ctypes.get_last_error())
    deadline = time.monotonic() + 10
    while True:
        snapshot = sample_job(worker); remember(snapshot)
        if empty(snapshot) and worker.poll() is not None: return snapshot
        if time.monotonic() >= deadline: raise RuntimeError('Owned native Job failed to drain')
        time.sleep(.05)


def exited_identities(identities):
    checks = []
    for expected in identities:
        current = native_identity(expected['pid'])
        need(current != expected, 'Owned native identity remains live after Job close')
        checks.append(dict(expected=expected, current=current, exited=True, query_completed=True))
    need(bool(checks), 'No owned identities recorded')
    return checks


def require_phase_proof(root, phase, actual=None, allow_forced=False):
    root = Path(root)
    launch = read(root / (phase + '_OWNED.json'))['native']
    ready = read(root / (phase + '_READY.json'))
    if actual is None: actual = ready['native']
    need(ready['native'] == actual and ready['phase'] == phase.lower() and
         ready['plan_sha256'] == filehash(root/'PLAN.json'), 'Actual scorer handshake differs')
    for suffix, identity in [('_LAUNCH_MEMBER.json', launch), ('_MEMBER.json', actual)]:
        proof = read(root / (phase + suffix))
        need(proof['native'] == identity and proof['member_of_exact_owned_job'] is True and
             proof['identity_checked_on_membership_handle'] is True and
             proof['known_live_when_authenticated'] is True, 'Exact owned Job membership proof missing')
    member = read(root / (phase + '_MEMBER.json'))
    need(member['launch_native'] == launch and member['ready_sha256'] == filehash(root/(phase+'_READY.json')),
         'Scorer membership has wrong launcher or handshake')
    closure = read(root/(phase+'_CLOSED.json')); exit_record = read(root/(phase+'_EXIT.json'))
    snapshot = read(root/(phase+'_JOB_EMPTY.json'))
    need(empty(snapshot) and closure['job_empty_before_close'] is True and closure['job_closed'] is True,
         'Owned Job emptiness or close proof missing')
    need(closure['native'] == actual and closure['launch_native'] == launch and
         exit_record['native'] == actual and exit_record['launch_native'] == launch,
         'Launcher/scorer exit roles differ')
    need(closure['known_not_same_live'] is True and closure['native_inspection_completed'] is True,
         'Exact native closure proof missing')
    checks = closure['identity_checks']
    for identity in (launch, actual):
        need(any(c['expected'] == identity and c['exited'] is True and c['query_completed'] is True and
                 c['current'] != identity for c in checks), 'Launcher or scorer exit proof missing')
    need(all(c['exited'] is True and c['query_completed'] is True and c['current'] != c['expected'] for c in checks),
         'Observed Job member exit is unknown')
    if closure['forced']:
        need(allow_forced, 'Forced phase cannot authenticate a completed chunk')
        forced = read(root/(phase+'_FORCED_STOP.json'))
        need(forced['native'] == actual and forced['launch_native'] == launch,
             'Forced stop native roles differ')
    else: need(exit_record['exit_code'] == 0, 'Native phase exit mismatch')
    return dict(launch_native=launch, native=actual, forced=closure['forced'],
                native_roles_distinct=launch != actual)
