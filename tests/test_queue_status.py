import errno
import json

import pytest

from runners import queue_status


def test_transient_replace_preserves_old_status_until_success(tmp_path, monkeypatch):
    path = tmp_path / 'status.json'
    path.write_text('{"old": true}')
    replace = queue_status.os.replace
    calls = []
    def busy_then_replace(src, dst):
        calls.append(src)
        assert json.loads(path.read_text()) == {'old': True}
        if len(calls) < 3:
            raise OSError(errno.EINVAL, 'simulated Windows shared target')
        replace(src, dst)
    monkeypatch.setattr(queue_status.os, 'replace', busy_then_replace)
    monkeypatch.setattr(queue_status.time, 'sleep', lambda _: None)
    queue_status.save_status(path, {'stages': ['complete']})
    assert json.loads(path.read_text()) == {'stages': ['complete']}
    assert len(calls) == 3
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize('error,attempts', [(errno.EACCES, 20), (errno.ENOSPC, 1)])
def test_failed_replace_keeps_readable_previous_status(tmp_path, monkeypatch, error, attempts):
    path = tmp_path / 'status.json'
    path.write_text('{"old": true}')
    calls = []
    def fail(*args):
        calls.append(args)
        raise OSError(error, 'fixture')
    monkeypatch.setattr(queue_status.os, 'replace', fail)
    monkeypatch.setattr(queue_status.time, 'sleep', lambda _: None)
    with pytest.raises(OSError):
        queue_status.save_status(path, {'new': True})
    assert json.loads(path.read_text()) == {'old': True}
    assert len(calls) == attempts
    assert list(tmp_path.iterdir()) == [path]
