from pathlib import Path
from types import SimpleNamespace
import errno
import stat
import sqlite3
import pytest
from runners.drive.cards import week5_output_size as size


def disappear(monkeypatch, vanished, exception=None):
    original = Path.lstat
    def lstat(path, *args, **kwargs):
        if path == vanished:
            raise exception or FileNotFoundError(errno.ENOENT, 'constructed enumeration/stat race', str(path))
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'lstat', lstat)


@pytest.mark.parametrize('relative', sorted(size.GO3_JOURNALS))
def test_exact_vanished_go3_journal(tmp_path, monkeypatch, relative):
    journal = tmp_path / relative
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.with_name('projection.sqlite').write_bytes(b'database')
    journal.write_bytes(b'ephemeral')
    (tmp_path / 'stable.bin').write_bytes(b'stable')
    disappear(monkeypatch, journal)
    assert size.output_bytes(tmp_path) == len(b'database') + len(b'stable')


@pytest.mark.parametrize('relative', sorted(size.GO3_JOURNALS))
def test_present_journal_is_counted(tmp_path, relative):
    journal = tmp_path / relative
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.with_name('projection.sqlite').write_bytes(b'database')
    journal.write_bytes(b'journal bytes')
    assert size.output_bytes(tmp_path) == len(b'databasejournal bytes')


@pytest.mark.parametrize('relative', ['other.sqlite-journal', 'nested/projection.sqlite-journal',
                                   'projection.sqlite-wal', 'projection.sqlite-shm',
                                   'projection.sqlite', 'stable.bin', 'SNAPSHOT.json',
                                   'PROGRESS.json.0.tmp', 'projection.sqlite-journal.tmp'])
def test_other_missing_paths_fail(tmp_path, monkeypatch, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'retained')
    disappear(monkeypatch, path)
    with pytest.raises(FileNotFoundError):
        size.output_bytes(tmp_path)


@pytest.mark.parametrize('name', ['PROGRESS.json.1.tmp', 'PROGRESS.json.987.tmp',
                               'COST.json.0123456789abcdef0123456789abcdef.tmp'])
def test_prior_atomic_temp_exception_preserved(tmp_path, monkeypatch, name):
    path = tmp_path / name
    path.write_bytes(b'temporary')
    disappear(monkeypatch, path)
    assert size.output_bytes(tmp_path) == 0


def test_present_atomic_temp_counts(tmp_path):
    (tmp_path / 'PROGRESS.json.1.tmp').write_bytes(b'temporary')
    assert size.output_bytes(tmp_path) == 9


def test_missing_companion_is_not_ignored(tmp_path, monkeypatch):
    journal = tmp_path / 'projection.sqlite-journal'
    journal.write_bytes(b'journal')
    disappear(monkeypatch, journal)
    with pytest.raises(FileNotFoundError):
        size.output_bytes(tmp_path)


def test_nonfile_companion_refuses(tmp_path, monkeypatch):
    (tmp_path / 'projection.sqlite').mkdir()
    journal = tmp_path / 'projection.sqlite-journal'
    journal.write_bytes(b'journal')
    disappear(monkeypatch, journal)
    with pytest.raises(ValueError, match='regular database'):
        size.output_bytes(tmp_path)


@pytest.mark.parametrize('error', [PermissionError(errno.EACCES, 'constructed denied'),
                                  OSError(errno.EIO, 'constructed I/O fault')])
def test_real_stat_errors_propagate(tmp_path, monkeypatch, error):
    path = tmp_path / 'projection.sqlite-journal'
    path.write_bytes(b'journal')
    disappear(monkeypatch, path, error)
    with pytest.raises(type(error)):
        size.output_bytes(tmp_path)


def test_directory_scan_error_propagates(tmp_path, monkeypatch):
    def refused(path):
        raise PermissionError(errno.EACCES, 'constructed scan refusal')
    monkeypatch.setattr(size.os, 'scandir', refused)
    with pytest.raises(PermissionError):
        size.output_bytes(tmp_path)


@pytest.mark.parametrize('mode,attributes', [(stat.S_IFLNK, 0), (stat.S_IFDIR, stat.FILE_ATTRIBUTE_REPARSE_POINT),
                                           (stat.S_IFREG, stat.FILE_ATTRIBUTE_REPARSE_POINT)])
def test_link_and_reparse_entries_refuse(mode, attributes):
    with pytest.raises(ValueError, match='symlinks and reparse'):
        size.reject_link(SimpleNamespace(st_mode=mode, st_file_attributes=attributes))


def test_initial_absent_output_is_zero(tmp_path):
    assert size.output_bytes(tmp_path / 'not-yet-created') == 0


def test_stable_nested_bytes_are_all_counted(tmp_path):
    (tmp_path / 'inner').mkdir()
    (tmp_path / 'one').write_bytes(b'1234')
    (tmp_path / 'inner' / 'two').write_bytes(b'123456')
    assert size.output_bytes(tmp_path) == 10


def test_real_sqlite_commit_between_enumeration_and_stat(tmp_path, monkeypatch):
    database = tmp_path / 'projection.sqlite'
    journal = tmp_path / 'projection.sqlite-journal'
    with sqlite3.connect(database) as connection:
        connection.execute('PRAGMA journal_mode=DELETE')
        connection.execute('CREATE TABLE fixture(value INTEGER)')
        connection.execute('INSERT INTO fixture VALUES(1)')
        connection.commit()
        connection.execute('UPDATE fixture SET value=2')
        assert journal.exists()
        original = Path.lstat
        committed = []
        def lstat(path, *args, **kwargs):
            if path == journal and not committed:
                connection.commit()
                committed.append(True)
            return original(path, *args, **kwargs)
        monkeypatch.setattr(Path, 'lstat', lstat)
        assert size.output_bytes(tmp_path) == database.stat().st_size
        assert committed and not journal.exists()
        assert connection.execute('SELECT value FROM fixture').fetchone() == (2,)


def test_only_version_and_measure_import_change():
    root = Path(__file__).resolve().parents[1]
    previous = (root / 'runners/drive/cards/week5_runtime_v6.py').read_text('utf8')
    expected = previous.replace('Week 5 v6 successor', 'Week 5 v7 successor', 1)
    expected = expected.replace('from .batch_runtime_v8 import measured_child, job_cpu, output_bytes',
                                'from .batch_runtime_v8 import measured_child, job_cpu\nfrom .week5_output_size import output_bytes', 1)
    assert expected == (root / 'runners/drive/cards/week5_runtime_v7.py').read_text('utf8')
    previous = (root / 'runners/drive/week5_launch_v6.py').read_text('utf8')
    assert previous.replace('week5_runtime_v6', 'week5_runtime_v7') == (root / 'runners/drive/week5_launch_v7.py').read_text('utf8')
