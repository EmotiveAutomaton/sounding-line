"""Constructed writer retries are bounded; no scientific source is modified."""
from unittest.mock import patch
import pytest
from runners.drive.cards import week4_runtime_fixture_v8_h1 as fixture


def test_transient_permission_retry_preserves_value(tmp_path):
    original=fixture.progress;attempts=[];target=tmp_path/'PROGRESS.json'
    def writer(path,value):
        attempts.append((path,value))
        if len(attempts)<3:raise PermissionError('sharing')
        original(path,value)
    with patch.object(fixture,'progress',writer),patch.object(fixture.time,'sleep'):
        assert fixture.pid_write(target,{'done':7})==2
    assert attempts==[(target,{'done':7})]*3
    assert fixture.read(target)=={'done':7}


def test_permanent_denial_is_bounded(tmp_path):
    with patch.object(fixture,'progress',side_effect=PermissionError('denied')) as writer,patch.object(fixture.time,'sleep') as sleep:
        with pytest.raises(PermissionError):fixture.pid_write(tmp_path/'PROGRESS.json',{})
    assert writer.call_count==50 and sleep.call_count==49


def test_other_io_error_immediately_fails(tmp_path):
    with patch.object(fixture,'progress',side_effect=OSError('disk')) as writer,patch.object(fixture.time,'sleep') as sleep:
        with pytest.raises(OSError):fixture.pid_write(tmp_path/'PROGRESS.json',{})
    assert writer.call_count==1 and sleep.call_count==0
