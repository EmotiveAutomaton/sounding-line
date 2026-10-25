import numpy as np
import pytest

from runners.drive.cards import week3_alignment_encoder_smoke as smoke


def vectors():
    x=np.eye(384,dtype=np.float32)[:len(smoke.TEXTS)].copy();x[1]=x[0];return x


def test_known_shape_norm_duplicate_and_constant_failures():
    smoke.validate(vectors())
    for values in (np.ones((len(smoke.TEXTS),384),dtype=np.float32),vectors().astype(np.float64),vectors()[:2]):
        with pytest.raises(ValueError):smoke.validate(values)
    bad=vectors();bad[1]=bad[2]
    with pytest.raises(ValueError,match='identical'):smoke.validate(bad)
    bad=vectors();bad[2,2]=np.nan
    with pytest.raises(ValueError,match='finiteness'):smoke.validate(bad)
    bad=np.zeros_like(vectors());bad[:,0]=1
    with pytest.raises(ValueError,match='constant'):smoke.validate(bad)


def test_handler_always_uses_actual_encoder_mode_and_repeats(tmp_path,monkeypatch):
    inputs={k:str(tmp_path/k) for k in ('model_summary','model_complete')}
    for p in inputs.values():__import__('pathlib').Path(p).write_text('{}')
    calls=[]
    def encoder(given,config):
        assert given==inputs and config=={}
        def encode(texts):assert tuple(texts)==smoke.TEXTS;calls.append('encode');return vectors()
        return encode
    monkeypatch.setattr(smoke.features,'encoder',encoder)
    monkeypatch.setattr(smoke,'environment',lambda:dict(constructed_test_stub=True))
    out=tmp_path/'out';summary=smoke.execute(out,inputs,{})
    assert summary['constructed_strings']==8 and not summary['scientific_admission']
    assert smoke.verify(out,inputs,{})['verified'] and calls==['encode']*4


def test_missing_or_different_dependency_does_not_fallback(monkeypatch):
    monkeypatch.setattr(smoke.importlib.metadata,'version',lambda name:'6.1.0')
    with pytest.raises(ValueError,match='pin'):smoke.environment()
