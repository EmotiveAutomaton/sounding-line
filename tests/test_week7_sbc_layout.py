import copy
import hashlib
import wave
import zipfile
import zlib

import pytest

from runners.drive.sealed.week7_sbc_layout import verify_layout


@pytest.fixture
def fixture_map(tmp_path):
    rows = []
    archive = tmp_path / "text.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for idx in [1,2]:
            member = f"mock{idx}.cha"
            text = b"@Begin\n@End\n"
            bundle.writestr(member,text)
            path = tmp_path / f"mock{idx}.wav"
            with wave.open(str(path),"wb") as stream:
                stream.setparams((1,2,16000,0,"NONE","not compressed"))
                stream.writeframes(bytes(64))
            rows.append(dict(recording_id=str(idx), recording=path.name, bytes=path.stat().st_size,
                recording_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), transcript_member=member,
                transcript_bytes=len(text), transcript_zip_crc32=f"{zlib.crc32(text):08x}"))
    return dict(transcript_archive=archive.name,transcript_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),items=rows)


def test_matched_and_incomplete(tmp_path,fixture_map):
    assert verify_layout(tmp_path,fixture_map,expected_count=2)==2
    with pytest.raises(ValueError,match="Incomplete"):
        verify_layout(tmp_path,fixture_map)


@pytest.mark.parametrize("field,value", [
    ("recording","../outside.wav"), ("recording","mock1.wav"), ("recording_sha256","0"*64),
    ("transcript_member","unknown.cha"), ("transcript_zip_crc32","deadbeef"), ("bytes",5)])
def test_reject_unbound(tmp_path,fixture_map,field,value):
    bad=copy.deepcopy(fixture_map)
    bad["items"][1][field]=value
    with pytest.raises(ValueError):
        verify_layout(tmp_path,bad,expected_count=2)

