"""Observed PID-temp race and unchanged byte-cap refusal, no human data."""
from pathlib import Path
from unittest.mock import patch
import pytest
from runners.drive.cards.batch_runtime_v8 import output_bytes
from runners.drive.cards.batch_runtime_v7 import output_bytes as previous
from runners.drive.cards.timing_p6 import progress
from runners.stage14.common import atomic


def scan_one(path, scanner=output_bytes):
    with patch.object(Path, 'rglob', return_value=iter([path])):
        return scanner(path.parent)


@pytest.mark.parametrize('writer', [progress, atomic])
def test_actual_writer_temporary_disappears(tmp_path, writer):
    import os
    original_replace = os.replace
    observed = []
    def capture(source, destination):
        observed.append(Path(source))
        return original_replace(source, destination)
    with patch.object(os, 'replace', capture):
        writer(tmp_path/'PROGRESS.json', {'done': 1})
    assert len(observed) == 1 and not observed[0].exists()
    assert scan_one(observed[0]) == 0
    if writer is progress:
        with pytest.raises(FileNotFoundError):
            scan_one(observed[0], previous)


@pytest.mark.parametrize('name', ['PROGRESS.json.175224.tmp', 'RESULT.json.'+'a'*32+'.tmp'])
def test_disappears_between_enumeration_and_stat(tmp_path, name):
    path = tmp_path/name
    path.write_bytes(b'partial')
    stat = Path.stat
    def disappear(self, *args, **kwargs):
        if self == path:
            self.unlink()
        return stat(self, *args, **kwargs)
    with patch.object(Path, 'stat', disappear):
        assert scan_one(path) == 0


@pytest.mark.parametrize('name', ['RESULT.json', 'RESULT.json.123.tmp',
    'PROGRESS.json.tmp', 'PROGRESS.json.0.tmp', 'PROGRESS.json.-1.tmp',
    'PROGRESS.json.1.2.tmp', 'PROGRESS.json.01.tmp', 'progress.json.123.tmp',
    'PROGRESS.json.'+'a'*31+'.tmp'])
def test_missing_other_names_fail(tmp_path, name):
    with pytest.raises(FileNotFoundError):
        scan_one(tmp_path/name)


@pytest.mark.parametrize('error', [PermissionError('denied'), OSError('I/O error')])
def test_other_io_errors_fail(tmp_path, error):
    with patch.object(Path, 'stat', side_effect=error):
        with pytest.raises(type(error)):
            scan_one(tmp_path/'PROGRESS.json.123.tmp')


def test_every_present_byte_counts_including_abandoned_temps(tmp_path):
    (tmp_path/'nested').mkdir()
    (tmp_path/'nested/RESULT.json').write_bytes(b'12345')
    (tmp_path/'PROGRESS.json.123.tmp').write_bytes(b'1234567')
    (tmp_path/('PROGRESS.json.'+'b'*32+'.tmp')).write_bytes(b'123')
    assert output_bytes(tmp_path) == 15
    assert output_bytes(tmp_path) > 14


def test_each_path_has_one_stat(tmp_path):
    path=tmp_path/'RESULT.json';path.write_bytes(b'123')
    original=Path.stat;calls=[]
    def counted(self,*args,**kwargs):
        calls.append(self)
        return original(self,*args,**kwargs)
    with patch.object(Path,'stat',counted):
        assert scan_one(path)==3
    assert calls==[path]
