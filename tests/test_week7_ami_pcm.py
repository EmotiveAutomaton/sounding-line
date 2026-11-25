import hashlib
import struct
import wave

import pytest

from runners.drive.cards.week7_ami_pcm import read_headset


def write_recording(path, channels, samples):
    with wave.open(str(path), "wb") as recording:
        recording.setparams((channels, 2, 16000, 0, "NONE", "not compressed"))
        recording.writeframes(struct.pack("<" + "h" * len(samples), *samples))
    return {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


@pytest.mark.parametrize("channels", [1, 2])
def test_same_mono_stream(tmp_path, channels):
    path = tmp_path / "headset.wav"
    expected = [-32768, 17, 0, 32767]
    pin = write_recording(path, channels, [v for v in expected for _ in range(channels)])
    samples, rate = read_headset(path, pin)
    assert rate == 16000
    assert samples.tolist() == expected


def test_last_frame_differs(tmp_path):
    path = tmp_path / "headset.wav"
    pin = write_recording(path, 2, [1, 1, 2, 3])
    with pytest.raises(ValueError, match="Distinct stereo"):
        read_headset(path, pin)


@pytest.mark.parametrize("field,value", [("bytes", 3), ("sha256", "wrong")])
def test_pin_change(tmp_path, field, value):
    path = tmp_path / "headset.wav"
    pin = write_recording(path, 1, [9])
    with pytest.raises(ValueError, match="changed"):
        read_headset(path, {**pin, field: value})


def test_truncation_with_matching_digest(tmp_path):
    path = tmp_path / "headset.wav"
    write_recording(path, 2, [1, 1, 2, 2])
    raw = path.read_bytes()[:-2]
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="Truncated"):
        read_headset(path, {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})

