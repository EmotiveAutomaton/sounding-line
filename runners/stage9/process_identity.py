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
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)]*4
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        if ctypes.get_last_error() in (87, 1168):
            return None
        raise OSError(ctypes.get_last_error(), 'cannot inspect native process identity')
    try:
        created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user)):
            raise OSError(ctypes.get_last_error(), 'GetProcessTimes failed')
        size, name = wintypes.DWORD(32768), ctypes.create_unicode_buffer(32768)
        if not kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)):
            raise OSError(ctypes.get_last_error(), 'QueryFullProcessImageNameW failed')
        return {'pid': pid, 'created_ticks': (created.dwHighDateTime << 32) | created.dwLowDateTime,
                'executable': name.value}
    finally:
        kernel.CloseHandle(handle)


def is_same_live_process(record):
    current = native_identity(record['pid'])
    return current is not None and current == record
