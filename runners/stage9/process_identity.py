"""Read-only native process identity. A PID alone is never an ownership identity.

DESIGN CHECK: X12. PID reuse must not turn a stale owner record into a live owner.
No process is stopped here. Native cleanup still requires inspection of its command.
"""
import os


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
        # independently signalled process handle establishes termination; an
        # access error by itself is never evidence that an owner is dead.
        sync = kernel.OpenProcess(0x100000, False, pid)
        if sync:
            try:
                if kernel.WaitForSingleObject(sync, 0) == 0:
                    return None
            finally:
                kernel.CloseHandle(sync)
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
