"""Focused native ownership regression: live, reused, exited and denied are distinct."""
import ctypes
import os
import subprocess
import sys
from unittest.mock import Mock
import pytest
from runners.stage9.process_identity import native_identity, is_same_live_process
from runners.stage9 import process_identity

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows process identities')


def test_live_and_reused_identity():
    current = native_identity()
    assert is_same_live_process(current)
    assert not is_same_live_process(dict(current, created_ticks=current['created_ticks'] + 1))


def test_retained_exited_native_handle():
    child = subprocess.Popen([sys.executable, '-c', 'pass'], creationflags=subprocess.CREATE_NO_WINDOW)
    child.wait(timeout=20)
    assert child._handle is not None
    assert native_identity(child.pid) is None


@pytest.mark.parametrize('wait_result,expected_dead', [(0, True), (258, False), (0xffffffff, False)])
def test_query_denial_needs_independent_termination(monkeypatch, wait_result, expected_dead):
    kernel = Mock()
    kernel.OpenProcess.side_effect = [0, 123]
    kernel.WaitForSingleObject.return_value = wait_result
    monkeypatch.setattr(ctypes, 'WinDLL', lambda *a, **k: kernel)
    monkeypatch.setattr(ctypes, 'get_last_error', lambda: 5)
    monkeypatch.setattr(process_identity, '_enumerated_process_ids', lambda k: {12345, os.getpid()})
    if expected_dead:
        assert native_identity(12345) is None
    else:
        with pytest.raises(OSError):
            native_identity(12345)
    kernel.CloseHandle.assert_called_once_with(123)


def test_all_access_denied_stays_unknown(monkeypatch):
    kernel = Mock(); kernel.OpenProcess.return_value = 0
    monkeypatch.setattr(ctypes, 'WinDLL', lambda *a, **k: kernel)
    monkeypatch.setattr(ctypes, 'get_last_error', lambda: 5)
    monkeypatch.setattr(process_identity, '_enumerated_process_ids', lambda k: {12345, os.getpid()})
    with pytest.raises(OSError):
        native_identity(12345)
    kernel.WaitForSingleObject.assert_not_called()


def test_denied_handles_with_independent_absence(monkeypatch):
    kernel = Mock(); kernel.OpenProcess.return_value = 0
    monkeypatch.setattr(ctypes, 'WinDLL', lambda *a, **k: kernel)
    monkeypatch.setattr(ctypes, 'get_last_error', lambda: 5)
    monkeypatch.setattr(process_identity, '_enumerated_process_ids', lambda k: {os.getpid()})
    assert native_identity(12345) is None


def test_failed_enumeration_never_proves_exit(monkeypatch):
    kernel = Mock(); kernel.OpenProcess.return_value = 0
    monkeypatch.setattr(ctypes, 'WinDLL', lambda *a, **k: kernel)
    monkeypatch.setattr(ctypes, 'get_last_error', lambda: 5)
    def failed(k):
        raise OSError('enumeration denied')
    monkeypatch.setattr(process_identity, '_enumerated_process_ids', failed)
    with pytest.raises(OSError, match='enumeration denied'):
        native_identity(12345)


def test_full_buffer_must_grow_before_declaring_absence():
    kernel = Mock(); calls = []
    def enumerate_ids(ids, size, used):
        calls.append(size)
        if len(calls) == 1:
            # The missing target is outside this truncated first buffer.
            for i in range(len(ids)): ids[i] = 1000000 + i
            used._obj.value = size
        else:
            ids[0], ids[1] = os.getpid(), 12345
            used._obj.value = 2 * ctypes.sizeof(ctypes.c_ulong)
        return 1
    kernel.K32EnumProcesses.side_effect = enumerate_ids
    assert process_identity._enumerated_process_ids(kernel) == {os.getpid(), 12345}
    assert calls[1] == 2 * calls[0]


@pytest.mark.parametrize('response', ['failure', 'empty', 'misaligned', 'oversize', 'missing_self', 'always_full'])
def test_invalid_or_incomplete_native_snapshot_refuses(response):
    kernel = Mock()
    def enumerate_ids(ids, size, used):
        if response == 'failure': return 0
        used._obj.value = {'empty': 0, 'misaligned': 3, 'oversize': size + 4,
                          'missing_self': 4, 'always_full': size}[response]
        ids[0] = 12345 if os.getpid() != 12345 else 12346
        return 1
    kernel.K32EnumProcesses.side_effect = enumerate_ids
    with pytest.raises(OSError):
        process_identity._enumerated_process_ids(kernel)


def test_real_native_snapshot_includes_caller():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    assert os.getpid() in process_identity._enumerated_process_ids(kernel)
