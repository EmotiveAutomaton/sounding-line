"""Own one suspended Windows child and all descendants in a kill-on-close job.

DESIGN CHECK (2026-10-18)
Lessons read: LESSONS sections 3-5.
Under both the null and alternative, a child may run only after containment.
Failure direction: failed assignment, timeout or lost supervision closes the
job and terminates only its assigned descendants. No process-name cleanup.
Operational bands are exhaustive: running, exited, or refused before resume.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as W
import os
import subprocess


class BasicLimits(ctypes.Structure):
    _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
        ('flags', W.DWORD), ('min_working_set', ctypes.c_size_t),
        ('max_working_set', ctypes.c_size_t), ('active_limit', W.DWORD),
        ('affinity', ctypes.c_size_t), ('priority', W.DWORD), ('scheduling', W.DWORD)]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic', BasicLimits), ('io', ctypes.c_uint64 * 6),
        ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
        ('peak_process_memory', ctypes.c_size_t), ('peak_job_memory', ctypes.c_size_t)]


class ContainedProcess:
    """Logs stay open until close; the job handle is never inherited by children."""
    def __init__(self, command, cwd, stdout, stderr, env=None):
        if os.name != 'nt':
            raise OSError('Windows counted exporter requires native job containment')
        import _winapi
        import msvcrt
        self.api = _winapi
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        for name, args, result in [
            ('CreateJobObjectW', [W.LPVOID, W.LPCWSTR], W.HANDLE),
            ('SetInformationJobObject', [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD], W.BOOL),
            ('AssignProcessToJobObject', [W.HANDLE, W.HANDLE], W.BOOL),
            ('ResumeThread', [W.HANDLE], W.DWORD),
            ('CloseHandle', [W.HANDLE], W.BOOL)]:
            fn = getattr(self.kernel, name); fn.argtypes = args; fn.restype = result
        self.process = self.thread = self.job = None
        self.streams = []
        try:
            self.job = self.kernel.CreateJobObjectW(None, None)
            if not self.job: raise ctypes.WinError(ctypes.get_last_error())
            limits = ExtendedLimits(); limits.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE
            if not self.kernel.SetInformationJobObject(self.job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.streams = [open(os.devnull, 'rb'), open(stdout, 'wb'), open(stderr, 'wb')]
            handles = [msvcrt.get_osfhandle(s.fileno()) for s in self.streams]
            for handle in handles: os.set_handle_inheritable(handle, True)
            si = subprocess.STARTUPINFO(); si.dwFlags = _winapi.STARTF_USESTDHANDLES
            si.hStdInput, si.hStdOutput, si.hStdError = handles
            si.lpAttributeList = {'handle_list': handles}
            try:
                self.process, self.thread, self.pid, _ = _winapi.CreateProcess(
                    str(command[0]), subprocess.list2cmdline([str(x) for x in command]),
                    None, None, True, 0x00000004 | 0x08000000 | 0x4000,
                    env, str(cwd), si)
            finally:
                for handle in handles: os.set_handle_inheritable(handle, False)
            if not self.kernel.AssignProcessToJobObject(self.job, self.process):
                # Still suspended: no descendant can escape before assignment.
                _winapi.TerminateProcess(self.process, 1)
                raise ctypes.WinError(ctypes.get_last_error())
            if self.kernel.ResumeThread(self.thread) == 0xffffffff:
                raise ctypes.WinError(ctypes.get_last_error())
            _winapi.CloseHandle(self.thread); self.thread = None
        except BaseException:
            self.close()
            raise

    def poll(self):
        if self.api.WaitForSingleObject(self.process, 0) == self.api.WAIT_TIMEOUT:
            return None
        return self.api.GetExitCodeProcess(self.process)

    def close(self):
        if self.job:
            self.kernel.CloseHandle(self.job); self.job = None
        if self.process:
            self.api.WaitForSingleObject(self.process, 10000)
            self.api.CloseHandle(self.process); self.process = None
        if self.thread:
            self.api.CloseHandle(self.thread); self.thread = None
        for stream in self.streams: stream.close()
        self.streams = []

    def __enter__(self): return self
    def __exit__(self, *args): self.close()
