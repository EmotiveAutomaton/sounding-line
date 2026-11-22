import sys
from pathlib import Path
from types import ModuleType
from hashlib import sha256
from zipfile import ZipFile
import numpy as np
import pytest
from runners.drive.cards import week7_phase1_operators as ops


def reference(name,monkeypatch):
    archive=Path('.agent-state/drive-20261115/lattice-20261120/intake/received-at-root/PREFLIGHT_2026-11-22.zip')
    assert sha256(archive.read_bytes()).hexdigest()=='87bdb419bf581e68ca29045e217a57450e4e323df32874f11126dfde22115e1d'
    monkeypatch.setattr(sys,'argv',['constructed'])
    with ZipFile(archive) as z:
        for k in (('pf_slopes',name) if name=='pf_rebound' else (name,)):
            path,=[e for e in z.namelist() if e.endswith('/'+k+'.py')]
            mod=ModuleType(k);mod.__file__=path;monkeypatch.setitem(sys.modules,k,mod)
            exec(compile(z.read(path),path,'exec'),mod.__dict__)
    return mod


def test_rebound(monkeypatch):
    ref=reference('pf_rebound',monkeypatch);ref.NBOOT=10
    args=(40,6,10,.15,False)
    expected=ref.one_rep(np.random.default_rng(4),*args)
    stress,play=ref.generate(np.random.default_rng(4),*args)
    now=stress[:,:,1:]
    result=ops.rebound(np.broadcast_to(np.arange(40)[:,None,None],now.shape).ravel(),now.ravel(),stress[:,:,:-1].ravel(),play[:,:,1:].ravel())
    assert result[1]==pytest.approx(expected['fall'],abs=1e-10)
    assert ops.rebound([0,0],[1,1],[1,1],[1,1]) is None


def test_price(monkeypatch):
    ref=reference('pf_price',monkeypatch)
    answers=ref.simulate('RULE',np.random.default_rng(42))
    excess,dip,_=ref.stats(np.ones((1,len(answers))),answers)
    row=[ops.refusal(np.bincount(col,minlength=8)) for col in answers.T]
    assert np.mean([x[1] for x in row])==pytest.approx(excess[0],abs=2e-6)
    assert np.mean([x[2] for x in row])==pytest.approx(dip[0])
    assert ops.refusal([0,0,0,12]) is None


def test_gate(monkeypatch):
    ref=reference('pf_gate',monkeypatch)
    ref.NR=80;ref.NB=2
    expected=ref.one_rep(1,'GATE',5)[6]
    args=ref.simulate('GATE',np.random.default_rng([35,ref.SCRIPT,1,5]))
    assert ops.choice_product(*args)==pytest.approx(expected,abs=1e-6)


@pytest.mark.parametrize('separation',[.3,5])
def test_cluster(monkeypatch,separation):
    ref=reference('pf_cluster',monkeypatch);rng=np.random.default_rng(64)
    x=np.vstack([rng.normal(size=(200,2)),rng.normal(size=(210,2))+separation])
    mixture=ref.gmm(x,3,6)
    left,n=ref.merge(mixture);right,m=ops.merge_components(mixture)
    assert n==m
    np.testing.assert_array_equal(left[:,None]==left,right[:,None]==right)
