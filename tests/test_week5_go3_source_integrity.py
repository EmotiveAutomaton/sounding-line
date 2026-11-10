from pathlib import Path
import py7zr
import pytest
from runners.drive.cards import week5_go3_source_integrity as safe


def tiny_archive(tmp):
    archive=tmp/'tiny.7z'
    for name in safe.TARGETS:(tmp/name).write_bytes(b'<root/>')
    with py7zr.SevenZipFile(archive,'w') as z:
        for name in safe.TARGETS:z.write(tmp/name,arcname=name)
    return archive


def test_fresh_decode_and_exact_reentry(tmp_path):
    archive=tiny_archive(tmp_path);out=tmp_path/'decode'
    expected=safe.extract(archive,out)
    assert safe.extract(archive,out)==expected
    assert set(expected)==set(safe.TARGETS)
    assert all(safe.member_crc(out/name)==safe.member_crc(tmp_path/name) for name in safe.TARGETS)


def test_partial_both_names_refuse_before_parsing(tmp_path):
    archive=tiny_archive(tmp_path);out=tmp_path/'decode';out.mkdir()
    for name in safe.TARGETS:(out/name).write_bytes(b'<')
    with pytest.raises(ValueError,match='Unsealed'):safe.extract(archive,out)
    assert all((out/name).read_bytes()==b'<' for name in safe.TARGETS)


def test_same_size_mutation_refuses(tmp_path):
    archive=tiny_archive(tmp_path);out=tmp_path/'decode';safe.extract(archive,out)
    target=out/'Posts.xml';target.write_bytes(b'<evil/>')
    with pytest.raises(ValueError,match='bytes changed'):safe.extract(archive,out)
