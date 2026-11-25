"""Constructed checks for the Santa Barbara room-audio binding."""
import io
import wave

import numpy as np
import pytest

from runners.drive.sealed.week7_sbc_units import (
    five_measures, parse, reference_pitches, room_samples, select,
)


def tier(actor, content, start, end):
    return f"*{actor}:\t{content} \x15{start}_{end}\x15"


def test_laughter_and_clean_speech_have_separate_rules():
    lines = [
        tier("A", "&=laughs .", 100, 200),
        tier("A", "hello &=laughing .", 300, 400),
        tier("A", "hiἩthere .", 400, 500),
        tier("A", "plain words .", 500, 700),
        tier("A", "&=laughs .", 720, 900),
        tier("UNKNOWN", "voice .", 810, 850),
        tier("A", "⌈ &=laughs ⌉ .", 900, 1000),
        tier("A", "☺ speech .", 1100, 1200),
    ]
    marks, eligible, _, references, counts = select(parse("\n".join(lines)), {"A": "p"}, 2)
    assert len(marks) == 3
    assert eligible == [True, False, False]
    assert references == {"p": [(0.5, 0.7)]}
    assert counts["p"]["marked_units"] == 5
    assert counts["p"]["mixed"] == 2


def test_untimed_unknown_voice_closes_isolation():
    text = tier("A", "&=laughs .", 0, 100) + "\n*B:\tvoice ."
    _, eligible, _, references, _ = select(parse(text), {"A": "known"}, 1)
    assert eligible == [False] and not references


def test_room_reference_uses_only_included_intervals_and_five_measures():
    rate = 8000
    t = np.arange(rate) / rate
    pcm = np.concatenate([np.sin(2*np.pi*150*t), np.sin(2*np.pi*300*t)])
    stereo = np.column_stack([pcm * 12000, pcm * 6000]).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as src:
        src.setparams((2, 2, rate, 0, "NONE", ""))
        src.writeframes(stereo.tobytes())
    buf.seek(0)
    with wave.open(buf, "rb") as src:
        refs = reference_pitches(src, {"person": [(0, 1)]})
        clip = room_samples(src, (1, 2))
        np.testing.assert_allclose(clip, stereo[rate:].mean(axis=1)/32768.)
        assert refs["person"] == pytest.approx(150, abs=2)
        duration, bursts, fraction, relative, spread = five_measures(clip, rate, 1, refs["person"])
        assert (duration, bursts, fraction) == (1, 1, 1)
        assert relative == pytest.approx(12, abs=.2) and spread < .15
        assert np.isnan(five_measures(clip, rate, 1, None)[3])
        with pytest.raises(ValueError):
            room_samples(src, (1, 3))

