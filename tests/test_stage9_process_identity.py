"""Focused native ownership regression: live, reused, exited and denied are distinct."""
import ctypes
import os
import subprocess
import sys
from unittest.mock import Mock
import pytest
from runners.stage9.process_identity import native_identity, is_same_live_process

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
    with pytest.raises(OSError):
        native_identity(12345)
    kernel.WaitForSingleObject.assert_not_called()
