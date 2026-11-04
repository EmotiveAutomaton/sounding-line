import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from runners.drive.cards import week4_pp1_ic as ic


def test_world_truth_support_and_shared_draws():
    zero,t0=ic.world(ic.SEEDS[0],0.)
    high,t1=ic.world(ic.SEEDS[0],.3)
    assert zero==ic.world(ic.SEEDS[0],0.)[0]
    assert len(zero)==80 and len({r['writer'] for r in zero})==20
    assert sum(len(r['intervals']) for r in zero)==3200
    for a,b in zip(zero,high):
        for x,y in zip(a['intervals'],b['intervals']):
            if x['location']!='before_sentence':assert x==y
    assert abs(t0['realized_middle_contrast'])<.08
    assert .22<t1['realized_middle_contrast']<.38


def test_known_null_and_boundary_signal():
    for seed in ic.SEEDS:
        null,_=ic.world(seed,0.);planted,_=ic.world(seed,.3)
        assert abs(ic.model.model(null)['contrasts']['sentence_minus_word'])<.12
        assert ic.model.model(planted)['contrasts']['sentence_minus_word']>.15


def test_full_counts_and_exhaustive_bands():
    for lo,hi,expected in [(-.1,.1,'not_detected'),(0.,.1,'not_detected'),(-.1,0.,'not_detected'),(.01,.1,'positive'),(-.2,-.1,'negative')]:
        assert ic.classify(lo,hi)==expected
    with pytest.raises(ValueError):ic.configuration(dict(ic.CONFIG,bootstrap_draws=1999))
    with pytest.raises(ValueError):ic.configuration(dict(ic.CONFIG,seed=7))
    with pytest.raises(ValueError):ic.world(4,0.)


def test_fresh_complete_reconstruction_and_corruption(tmp_path):
    config=dict(ic.CONFIG,mode='validation',bootstrap_draws=2)
    result=ic.execute(tmp_path,{},config)
    assert len(result['worlds'])==6 and not result['full_calibration']
    env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONHASHSEED='42')
    script='from runners.drive.cards import week4_pp1_ic as c; c.verify('+repr(str(tmp_path))+',{},'+repr(config)+')'
    subprocess.run([sys.executable,'-B','-c',script],check=True,env=env,capture_output=True)
    p=tmp_path/'RESULT.json';d=json.loads(p.read_text());d['worlds'][0]['effect']+=.1;p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='reconstruction'):ic.verify(tmp_path,{},config)


def test_cost_only_and_no_external_inputs(tmp_path):
    with pytest.raises(ValueError):ic.execute(tmp_path,{'human':'forbidden'},dict(ic.CONFIG,mode='cost',bootstrap_draws=5))
    result=ic.execute(tmp_path,{},dict(ic.CONFIG,mode='cost',bootstrap_draws=5))
    assert 'worlds' not in result and result['projected_execute_and_replay_cpu_seconds']>0
    assert not (tmp_path/'BOOTSTRAPS.json.gz').exists()
