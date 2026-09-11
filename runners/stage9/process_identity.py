"""Read-only native process identity. A PID alone is never an ownership identity.

DESIGN CHECK: X12; LESSONS 3-5 read 2026-09-11. NULL: an inaccessible but
enumerated process, incomplete enumeration or API failure remains unknown.
ALTERNATIVE: independent complete native enumeration can establish PID absence.
PID reuse still requires creation-time identity. No process is stopped here.
Native cleanup still requires inspection of its command.
"""
import os


def _enumerated_process_ids(kernel):
    """Complete native snapshot; a full buffer never establishes absence.

    Microsoft EnumProcesses requires a larger buffer when returned bytes equal
    its capacity. K32EnumProcesses is the Windows 7+ kernel32 export.
    """
    import ctypes
    from ctypes import wintypes
    enumerate_ids = kernel.K32EnumProcesses
    enumerate_ids.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD,
                             ctypes.POINTER(wintypes.DWORD)]
    enumerate_ids.restype = wintypes.BOOL
    capacity = 1024
    while capacity <= 1048576:
        ids = (wintypes.DWORD * capacity)()
        used = wintypes.DWORD()
        size = ctypes.sizeof(ids)
        if not enumerate_ids(ids, size, ctypes.byref(used)):
            raise OSError(ctypes.get_last_error(), 'native process enumeration failed')
        if not used.value or used.value > size or used.value % ctypes.sizeof(wintypes.DWORD):
            raise OSError('invalid native process enumeration size')
        if used.value == size:
            capacity *= 2
            continue
        result = set(ids[:used.value // ctypes.sizeof(wintypes.DWORD)])
        if os.getpid() not in result:
            raise OSError('native process enumeration omitted its own caller')
        return result
    raise OSError('native process enumeration remained incomplete')


def native_identity(pid=None):
    pid = os.getpid() if pid is None else int(pid)
    if os.name != 'nt':
        raise RuntimeError('this queue requires the reviewed Windows identity implementation')
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)]*4
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error in (87, 1168):
            return None
        # A retained terminated process object may deny query access. Only an
        # independently signalled handle or complete OS process-list absence
        # establishes termination; access denial alone never establishes exit.
        sync = kernel.OpenProcess(0x100000, False, pid)
        if sync:
            try:
                if kernel.WaitForSingleObject(sync, 0) == 0:
                    return None
            finally:
                kernel.CloseHandle(sync)
        if pid not in _enumerated_process_ids(kernel):
            return None
        raise OSError(error, 'cannot inspect native process identity')
    try:
        created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user)):
            raise OSError(ctypes.get_last_error(), 'GetProcessTimes failed')
        if exited.dwHighDateTime or exited.dwLowDateTime:
            return None
        size, name = wintypes.DWORD(32768), ctypes.create_unicode_buffer(32768)
        if not kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)):
            error = ctypes.get_last_error()
            # The process can exit between the first time query and the image
            # query. Recheck the same handle, which cannot refer to a reused PID.
            if (kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user))
                    and (exited.dwHighDateTime or exited.dwLowDateTime)):
                return None
            raise OSError(error, 'QueryFullProcessImageNameW failed')
        return {'pid': pid, 'created_ticks': (created.dwHighDateTime << 32) | created.dwLowDateTime,
                'executable': name.value}
    finally:
        kernel.CloseHandle(handle)


def is_same_live_process(record):
    current = native_identity(record['pid'])
    return current is not None and current == record
