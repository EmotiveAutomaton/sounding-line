"""Regression for the observed atomic progress/stat race; no scientific data."""
from pathlib import Path
from unittest.mock import patch
import pytest
from runners.drive.cards.batch_runtime_v6 import output_bytes


def scan_one(path):
    with patch.object(Path, 'rglob', return_value=iter([path])):
        return output_bytes(path.parent)


def test_vanished_exact_atomic_temp(tmp_path):
    path = tmp_path / ('PROGRESS.json.' + 'a'*32 + '.tmp')
    path.write_bytes(b'partial')
    stat = Path.stat
    def disappear(self, *args, **kwargs):
        if self == path:
            self.unlink()
        return stat(self, *args, **kwargs)
    with patch.object(Path, 'stat', disappear):
        assert scan_one(path) == 0


@pytest.mark.parametrize('name', ['RESULT.json', 'PROGRESS.json.tmp',
                                'PROGRESS.json.'+'a'*31+'.tmp'])
def test_missing_non_atomic_fails(tmp_path, name):
    with pytest.raises(FileNotFoundError):
        scan_one(tmp_path/name)


def test_permission_failure_is_not_ignored(tmp_path):
    path = tmp_path / ('PROGRESS.json.'+'a'*32+'.tmp')
    with patch.object(Path, 'stat', side_effect=PermissionError('denied')):
        with pytest.raises(PermissionError):
            scan_one(path)


def test_all_existing_bytes_count_including_temps(tmp_path):
    (tmp_path/'nested').mkdir()
    (tmp_path/'nested/RESULT.json').write_bytes(b'12345')
    (tmp_path/('PROGRESS.json.'+'b'*32+'.tmp')).write_bytes(b'1234567')
    assert output_bytes(tmp_path) == 12
    assert output_bytes(tmp_path) > 11  # unchanged cap predicate


def test_each_path_stat_once(tmp_path):
    path = tmp_path/'RESULT.json'
    path.write_bytes(b'123')
    original = Path.stat
    calls = []
    def counted(self, *args, **kwargs):
        calls.append(self)
        return original(self, *args, **kwargs)
    with patch.object(Path, 'stat', counted):
        assert scan_one(path) == 3
    assert calls == [path]
