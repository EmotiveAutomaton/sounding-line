"""V1 producer rename races and unchanged fail-closed resource accounting."""
import errno
import os
from pathlib import Path
import pytest
from runners.drive.cards import week5_output_size as old
from runners.drive.cards import week5_output_size_v2 as size
from runners.drive.cards import week5_go as producer


@pytest.mark.parametrize('prefix', ['', 'independent-replay/'])
@pytest.mark.parametrize('target', ['fits/055-0103.json', 'fits/055-0103.seal.json',
                                  'bank-055.json', 'BINDINGS.json', 'PCA.json', 'RESULT.json'])
def test_actual_producer_rename_between_enumeration_and_stat(tmp_path, monkeypatch, prefix, target):
    destination = tmp_path / (prefix + target)
    destination.parent.mkdir(parents=True, exist_ok=True)
    real_replace = os.replace
    # The producer supplies the exact PID naming convention and complete bytes;
    # defer just its rename to the precise accounting race boundary.
    replacements = []
    monkeypatch.setattr(producer.os, 'replace', lambda src, dst: replacements.append((Path(src), Path(dst))))
    producer.write(destination, {'constructed': True})
    assert len(replacements) == 1
    temporary, recorded_destination = replacements[0]
    assert recorded_destination == destination and temporary.exists()
    real_stat = Path.lstat
    renamed = []
    def racing_stat(path, *args, **kwargs):
        if path == temporary and not renamed:
            real_replace(temporary, destination)
            renamed.append(True)
        return real_stat(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'lstat', racing_stat)
    assert size.output_bytes(tmp_path) == 0  # Destination was not in this enumeration.
    assert renamed and destination.exists() and not temporary.exists()
    assert size.output_bytes(tmp_path) == destination.stat().st_size


@pytest.mark.parametrize('relative', ['fits/055-0103.seal.json.271160.tmp',
                                    'independent-replay/fits/055-0103.json.12.tmp'])
def test_present_pid_temporary_counts_in_full(tmp_path, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(b'present temporary')
    assert size.output_bytes(tmp_path) == 17


@pytest.mark.parametrize('relative', ['fits/055-0103.json', 'fits/055-0103.seal.json',
    'fits/055-0103.json.0.tmp', 'fits/55-0103.json.1.tmp', 'fits/055-103.json.1.tmp',
    'other/055-0103.json.1.tmp', 'nested/fits/055-0103.json.1.tmp', 'OTHER.json.1.tmp'])
def test_unapproved_missing_paths_fail(tmp_path, relative):
    path = tmp_path / relative
    with pytest.raises(FileNotFoundError):
        if not size.vanished_transient(path, tmp_path):
            raise FileNotFoundError(path)


def test_vanished_temp_requires_regular_committed_companion(tmp_path):
    path = tmp_path / 'fits/055-0103.json.1.tmp'
    path.parent.mkdir()
    with pytest.raises(FileNotFoundError):
        size.vanished_transient(path, tmp_path)
    path.with_name('055-0103.json').mkdir()
    with pytest.raises(ValueError, match='regular output'):
        size.vanished_transient(path, tmp_path)


@pytest.mark.parametrize('error', [PermissionError(errno.EACCES, 'denied'), OSError(errno.EIO, 'I/O')])
def test_companion_io_errors_fail(tmp_path, monkeypatch, error):
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(Path, 'lstat', fail)
    with pytest.raises(type(error)):
        size.vanished_transient(tmp_path / 'fits/055-0103.json.1.tmp', tmp_path)


def test_prior_helper_does_not_accept_observed_failure(tmp_path):
    path = tmp_path / 'fits/055-0103.seal.json.271160.tmp'
    assert old.vanished_transient(path, tmp_path) is False


def test_exact_runtime_and_launcher_diff():
    root = Path(__file__).resolve().parents[1]
    prior = (root / 'runners/drive/cards/week5_runtime_v7.py').read_text('utf8')
    expected = prior.replace('Week 5 v7 successor', 'Week 5 v8 successor', 1).replace(
        'from .week5_output_size import', 'from .week5_output_size_v2 import', 1)
    assert expected == (root / 'runners/drive/cards/week5_runtime_v8.py').read_text('utf8')
    prior = (root / 'runners/drive/week5_launch_v7.py').read_text('utf8')
    assert prior.replace('week5_runtime_v7', 'week5_runtime_v8') == (root / 'runners/drive/week5_launch_v8.py').read_text('utf8')
