"""Read the pinned AMI PCM stream, accepting stereo only when every sample is duplicated."""
import hashlib
import wave

import numpy as np


def read_headset(path, expected):
    if path.stat().st_size != expected["bytes"]:
        raise ValueError("Recording length changed")
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != expected["sha256"]:
            raise ValueError("Recording digest changed")
        stream.seek(0)
        with wave.open(stream) as recording:
            channels = recording.getnchannels()
            rate = recording.getframerate()
            frames = recording.getnframes()
            if (channels not in (1, 2) or recording.getsampwidth() != 2
                    or recording.getcomptype() != "NONE" or not 8000 <= rate <= 96000):
                raise ValueError("Unsupported headset recording")
            data = recording.readframes(frames)
    if len(data) != frames * channels * 2:
        raise ValueError("Truncated headset recording")
    samples = np.frombuffer(data, dtype="<i2")
    if channels == 2:
        pair = samples.reshape(frames, 2)
        if not np.array_equal(pair[:, 0], pair[:, 1]):
            raise ValueError("Distinct stereo signals on assigned headset")
        samples = pair[:, 0].copy()
    return samples, rate

