"""Durable record reads survive temporary Windows sharing, never bad evidence."""
import errno
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from runners.stage9 import live_status as common


@pytest.fixture
def record(tmp_path):
    path = tmp_path / 'STATUS.json'
    path.write_text('{"jobs":{"one":"COMPLETE"}}', encoding='utf-8')
    return path


def test_normal_record_read_never_waits(record, monkeypatch):
    monkeypatch.setattr(common.time, 'sleep', lambda _: pytest.fail('unexpected retry'))
    assert common.read(record) == {'jobs': {'one': 'COMPLETE'}}


@pytest.mark.parametrize('error_number,windows_code', [(errno.EACCES, None), (None, 5), (None, 32), (None, 33)])
def test_transient_windows_access_reopens_only_original_path(record, monkeypatch, error_number, windows_code):
    monkeypatch.setattr(common, 'os', SimpleNamespace(name='nt'))
    original = Path.open
    seen = []
    waits = []
    error = OSError(error_number, 'transient access')
    if windows_code is not None:
        error.winerror = windows_code
    def opening(path, *args, **kwargs):
        seen.append(path)
        if len(seen) <= 2:
            raise error
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', opening)
    monkeypatch.setattr(common.time, 'sleep', waits.append)
    assert common.read(record) == {'jobs': {'one': 'COMPLETE'}}
    assert seen == [record] * 3 and waits == [0.025, 0.05]


def test_persistent_windows_denial_remains_bounded_and_raises_original(record, monkeypatch):
    monkeypatch.setattr(common, 'os', SimpleNamespace(name='nt'))
    error = PermissionError(errno.EACCES, 'persistent denial', str(record))
    attempts = []
    waits = []
    def opening(path, *args, **kwargs):
        attempts.append(path)
        raise error
    monkeypatch.setattr(Path, 'open', opening)
    monkeypatch.setattr(common.time, 'sleep', waits.append)
    with pytest.raises(PermissionError) as caught:
        common.read(record)
    assert caught.value is error and attempts == [record] * 8
    assert waits == pytest.approx([0.025, 0.05, 0.075, 0.1, 0.1, 0.1, 0.1])


def test_malformed_json_is_not_retried(record, monkeypatch):
    record.write_text('{"jobs":', encoding='utf-8')
    monkeypatch.setattr(common.time, 'sleep', lambda _: pytest.fail('malformed record retried'))
    with pytest.raises(json.JSONDecodeError):
        common.read(record)


@pytest.mark.parametrize('error_number', [errno.ENOENT, errno.EINVAL, errno.EIO])
def test_other_io_errors_are_not_retried(record, monkeypatch, error_number):
    monkeypatch.setattr(common, 'os', SimpleNamespace(name='nt'))
    error = OSError(error_number, 'not transient access')
    def opening(*args, **kwargs):
        raise error
    monkeypatch.setattr(Path, 'open', opening)
    monkeypatch.setattr(common.time, 'sleep', lambda _: pytest.fail('other error retried'))
    with pytest.raises(OSError) as caught:
        common.read(record)
    assert caught.value is error


def test_non_windows_denial_is_not_retried(record, monkeypatch):
    monkeypatch.setattr(common, 'os', SimpleNamespace(name='posix'))
    def opening(*args, **kwargs):
        raise PermissionError(errno.EACCES, 'denied')
    monkeypatch.setattr(Path, 'open', opening)
    monkeypatch.setattr(common.time, 'sleep', lambda _: pytest.fail('non-Windows denial retried'))
    with pytest.raises(PermissionError):
        common.read(record)


@pytest.mark.skipif(os.name != 'nt', reason='actual Windows sharing semantics')
def test_actual_windows_exclusive_handle_then_same_record_read(record, monkeypatch):
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateFileW(str(record), 0x80000000, 0, None, 3, 0, None)
    assert handle != ctypes.c_void_p(-1).value, ctypes.get_last_error()
    waits = []
    def release(delay):
        nonlocal handle
        waits.append(delay)
        assert kernel.CloseHandle(handle)
        handle = None
    try:
        # Establish that the OS, not a substituted Path.open, denies this read.
        with pytest.raises(PermissionError):
            with record.open(encoding='utf-8'):
                pass
        monkeypatch.setattr(common.time, 'sleep', release)
        assert common.read(record) == {'jobs': {'one': 'COMPLETE'}}
        assert waits == [0.025]
    finally:
        if handle is not None:
            kernel.CloseHandle(handle)
