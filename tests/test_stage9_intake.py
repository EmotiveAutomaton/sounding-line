"""Adversarial intake fixtures exercise reachable failures, without any network."""
import io
import stat
import urllib.request
import zipfile

import pytest

from runners.stage9.common import Units, distribution, read
from runners.stage9.intake import Refused, RedirectPolicy, bounded_copy, inspect_zip, member_path


def test_budget_has_one_writer_and_survives_new_intake_instance(tmp_path):
    from runners.stage9.intake import Intake
    first, second = Intake(tmp_path), Intake(tmp_path)
    with first.writer():
        first.charge('downloaded', 19)
        with pytest.raises(Refused, match='another intake writer'):
            with second.writer():
                pass
    with second.writer():
        assert second.ledger['downloaded'] == 19


def test_failed_open_closes_temporary_file(tmp_path, monkeypatch):
    from runners.stage9.intake import Intake
    intake = Intake(tmp_path, ['allowed.example'])
    monkeypatch.setattr(intake, 'before', lambda url: None)
    def fail(*args, **kwargs):
        raise OSError('fixture failure')
    monkeypatch.setattr(intake.opener, 'open', fail)
    with pytest.raises(OSError, match='fixture failure'):
        intake.fetch('https://allowed.example/data', {'reviewed': True, 'basis': 'fixture', 'source': 'fixture'})
    assert list(tmp_path.glob('*.partial')) == []


def test_zip_resume_checks_hash_and_does_not_charge_twice(tmp_path):
    from runners.stage9.intake import Intake
    from runners.stage9.common import file_hash
    intake = Intake(tmp_path)
    source = tmp_path / 'release.zip'
    with zipfile.ZipFile(source, 'w') as archive:
        archive.writestr('release/data.csv', 'a,b\n1,2\n')
    sha = file_hash(source)
    (tmp_path / 'objects').mkdir()
    source.rename(tmp_path / 'objects' / sha)
    first = intake.extract_zip(sha, ['release/data.csv'])
    charged = intake.ledger['extracted']
    assert intake.extract_zip(sha, ['release/data.csv']) == first
    assert intake.ledger['extracted'] == charged
    (tmp_path / 'materialized' / sha / 'release/data.csv').write_text('changed')
    with pytest.raises(Refused, match='hash mismatch'):
        intake.extract_zip(sha, ['release/data.csv'])


def test_robots_redirect_does_not_recursively_fetch_robots(tmp_path, monkeypatch):
    from runners.stage9.intake import Intake
    intake = Intake(tmp_path, ['allowed.example'])
    intake.resolving_robots = True
    calls = []
    monkeypatch.setattr(intake.opener, 'open', calls.append)
    intake.before('https://allowed.example/moved-robots')
    assert calls == []


def test_expanded_member_limit_is_separate_from_download_limit(tmp_path, monkeypatch):
    import runners.stage9.intake as intake_module
    from runners.stage9.common import file_hash
    intake = intake_module.Intake(tmp_path)
    source = tmp_path / 'release.zip'
    with zipfile.ZipFile(source, 'w') as archive:
        archive.writestr('data.csv', 'header\n' + 'x\n' * 20)
    sha = file_hash(source)
    (tmp_path / 'objects').mkdir()
    source.rename(tmp_path / 'objects' / sha)
    monkeypatch.setattr(intake_module, 'ASSET_LIMIT', 10)
    receipt = intake.extract_zip(sha, ['data.csv'])
    assert receipt['materialized']['data.csv']['bytes'] == 47


def test_redirect_refuses_before_callback_or_request():
    requests = []
    policy = RedirectPolicy({"allowed.example"}, requests.append)
    request = urllib.request.Request("https://allowed.example/source")
    with pytest.raises(Refused):
        policy.redirect_request(request, None, 302, "Found", {}, "https://forbidden.example/truth")
    assert requests == []
    redirected = policy.redirect_request(request, None, 302, "Found", {}, "https://allowed.example/release")
    assert redirected.full_url == "https://allowed.example/release"
    assert requests == [redirected.full_url]


def test_complete_eof_and_decompression_cap():
    import gzip
    out = io.BytesIO()
    assert bounded_copy(io.BytesIO(b"abc"), out, 3) == 3
    assert out.getvalue() == b"abc"
    with pytest.raises(Refused):
        bounded_copy(io.BytesIO(b"abcd"), io.BytesIO(), 3)
    bomb = gzip.compress(b"x" * 1000000)
    with gzip.GzipFile(fileobj=io.BytesIO(bomb)) as stream:
        with pytest.raises(Refused):
            bounded_copy(stream, io.BytesIO(), 1024)


@pytest.mark.parametrize("name", ["../escape", "/escape", "C:/escape", "a\\escape", "a/../../b", "a/NUL.txt", "a/x."])
def test_path_traversal_and_windows_aliases(name):
    with pytest.raises(Refused):
        member_path(name)


def test_archive_links_and_collisions_are_rejected_before_extraction(tmp_path):
    source = tmp_path / "links.zip"
    with zipfile.ZipFile(source, "w") as archive:
        link = zipfile.ZipInfo("release/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link, "../../truth")
    with pytest.raises(Refused):
        inspect_zip(source)
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("release/Data.csv", "a,b\n")
        archive.writestr("release/data.csv", "c,d\n")
    with pytest.raises(Refused):
        inspect_zip(source)


def test_resume_preserves_exact_unit_and_rejects_new_identity(tmp_path):
    store = Units(tmp_path, {"source": "frozen", "split": "pilot"})
    key = {"world": 1, "condition": "altered", "reader": "qwen"}
    store.put(key, {"score": -1.0})
    resumed = Units(tmp_path, {"source": "frozen", "split": "pilot"})
    assert resumed.get(key) == {"score": -1.0}
    assert resumed.get(dict(key, condition="genuine")) is None
    with pytest.raises(ValueError):
        Units(tmp_path, {"source": "changed", "split": "pilot"})
    with pytest.raises(ValueError):
        resumed.put(key, {"score": 0.0})
    assert len(resumed.all()) == 1


@pytest.mark.parametrize("values", [{}, {"a": float("nan")}, {"a": 4.0}, {"a": 0.0}, {"a": -1.0, "b": 2.0}])
def test_invalid_probabilities_never_become_uniform(values):
    with pytest.raises(ValueError):
        distribution(values)
