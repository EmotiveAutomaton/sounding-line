import json,os,subprocess,sys
import numpy as np
import pytest
from runners.drive.cards import week4_pp1_ic_h1 as h


def test_every_world_and_repeated_writer_parity():
    for seed in h.original.SEEDS:
        for dose in h.original.DOSES:
            rows,_=h.original.world(seed,dose);prepared=h.prepare(rows)
            assert h.contrasts(prepared[0])==h.model.model(rows)['contrasts']
            selected=np.random.default_rng(seed).integers(0,20,20)
            expected=h.model.arrays(h.model.writer_resample(rows,selected));actual=h.gather(prepared,selected)
            for k in actual:
                if isinstance(actual[k],np.ndarray):assert np.array_equal(actual[k],expected[k]),k
                else:assert actual[k]==expected[k],k
            assert h.contrasts(actual)==h.model.model(h.model.writer_resample(rows,selected))['contrasts']


def test_native_replay_and_corruption(tmp_path):
    config=dict(h.original.CONFIG,mode='validation',bootstrap_draws=2)
    result=h.execute(tmp_path,{},config)
    env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONHASHSEED='271')
    subprocess.run([sys.executable,'-B','-c','from runners.drive.cards import week4_pp1_ic_h1 as h; h.verify('+repr(str(tmp_path))+',{},'+repr(config)+')'],check=True,env=env,capture_output=True)
    assert len(result['worlds'])==6
    p=tmp_path/'RESULT.json';d=json.loads(p.read_text());d['worlds'][0]['effect']+=.1;p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='reconstruction'):h.verify(tmp_path,{},config)
