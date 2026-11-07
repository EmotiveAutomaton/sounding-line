import json
import numpy as np
import pytest
from runners.theory_days import moral_texture_cached as c
from runners.theory_days.moral_expectation import load
from runners.theory_days.moral_texture import family


def test_exact_cache_and_immutable_reentry(tmp_path):
    source=c.fixture_source(tmp_path/'fixture');out=tmp_path/'cache'
    c.save_cache(out,source);before={p.name:p.read_bytes() for p in out.iterdir()}
    cached=c.get_cache(out,c.filehash(source));original=load(source)
    assert all(np.array_equal(a,b) for a,b in zip(cached,original))
    assert family(cached[0],0,[-.1,.1],32,False)==family(original[0],0,[-.1,.1],32,False)
    c.save_cache(out,source);assert before=={p.name:p.read_bytes() for p in out.iterdir()}


def test_corrupt_source_and_array_refuse(tmp_path):
    source=c.fixture_source(tmp_path/'fixture');out=tmp_path/'cache';c.save_cache(out,source)
    with pytest.raises(ValueError):c.get_cache(out,'0'*64)
    p=out/'counts.npy';p.write_bytes(p.read_bytes()+b'changed')
    with pytest.raises(ValueError):c.get_cache(out,c.filehash(source))


def test_complete_native_handler_replays(tmp_path):
    config=dict(cache_build=True,constructed=True)
    c.execute(tmp_path,{},config)
    assert c.verify(tmp_path,{},config)['complete_recalculation']
