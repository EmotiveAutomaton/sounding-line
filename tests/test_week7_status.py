from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week7_status_v1 as card

def sample():
    rng=np.random.default_rng(111)
    n=2400
    f=pd.DataFrame({'id':np.repeat(np.arange(60),40),'day':np.tile(np.repeat(np.arange(8),5),60),'beep':np.tile(np.arange(5),480),'interaction':rng.integers(1,3,n)})
    for k in sorted(set(card.columns('PSD1')+card.columns('PSD2')+card.columns('ISO1'))-set(f)):
        f[k]=rng.integers(1,7,n)
    return f

@pytest.mark.parametrize(('a','b','wanted'),[
    ([1,1,3,3],[1,3,1,3],1.),([1,3,1,3],[3,1,3,1],0.),([3,3,1,1],[3,3,1,1],2.)])
def test_cooccurrence(a,b,wanted):
    total,n=card.joint_terms(np.array(a),np.array(b),3)
    assert total/n==wanted

def test_undefined():
    assert card.joint_terms(np.array([1.,3.,np.nan]),np.array([1.,1.,3.]),3)==(0,0)

def test_chronology():
    frame=pd.DataFrame(dict(id=[1]*6,day=[1,1,1,2,2,2],beep=[1,1,2,1,3,4],interaction=[1]*6))
    f,dups=card.ordered(frame)
    assert dups==2
    assert f.adjacent.tolist()==[False,False,False,False,False,True]

@pytest.mark.parametrize('name',card.CARDS)
def test_replay(name):
    f=sample()
    left=card.prepare(name,f,False)
    right=card.prepare(name,f,True)
    w=np.tile([0,2],30)
    a=card.evaluate(left,w,lambda:None)
    b=card.evaluate(right,w,lambda:None,verify=True)
    assert a.keys()==b.keys() and all(v is not None for v in a.values())
    np.testing.assert_allclose(list(a.values()),list(b.values()),rtol=1e-7,atol=1e-9)
    if name=='ISO1':
        xx=np.eye(6)
        xy=np.array([.3,.1,-.1,0.,0.,0.])
        matrix=np.block([[xx,xy[:,None]],[xy[None,:],np.ones((1,1))]])
        left.panels['iso']=np.repeat(matrix[None,:,:],left.people,axis=0)
        assert card.evaluate(left,w,lambda:None)['ashamed_minus_others']==pytest.approx(.3)
        left.panels['iso'][:]=0
        assert card.evaluate(left,w,lambda:None)['ashamed_minus_others'] is None

def test_labels():
    f=sample()
    f.loc[0,'int_proud']=7
    with pytest.raises(ValueError,match='coding'):
        card.prepare('PSD2',f,False)

def test_preflight_operator():
    from zipfile import ZipFile
    from hashlib import sha256
    archive=Path('.agent-state/drive-20261115/lattice-20261120/intake/received-at-root/PREFLIGHT_2026-11-22.zip')
    if sha256(archive.read_bytes()).hexdigest()!='87bdb419bf581e68ca29045e217a57450e4e323df32874f11126dfde22115e1d':
        raise ValueError('Supplied fixture archive differs')
    with ZipFile(archive) as z:
        reference=z.read('PREFLIGHT_2026-11-22/pf35b/pf_dial.py')
    # Reviewed reference contains NumPy synthetic generators and a guarded main.
    import types
    ref=types.ModuleType('supplied_dial')
    exec(compile(reference,'supplied/pf_dial.py','exec'),ref.__dict__)
    ref.NP,ref.T=80,24
    rng=np.random.default_rng(138)
    adm,cri,p,s=ref.simulate('TWOc',rng)
    k,m=ref.person_stats(adm,cri,p,s)
    expected=ref.stats_from_sums(k,m.sum(axis=0))
    people=[]
    for i in range(ref.NP):
        g=pd.DataFrame(dict(proud=p[i]+1,ashamed=s[i]+1,status_admired=adm[i]+1,
            status_criticised=cri[i]+1,interaction=1,adjacent=np.arange(ref.T)>0))
        people.append(card.dial_terms(g,median_positive=True))
    actual=card.dial_values(np.sum(people,axis=0))
    for name,other in [('fall_proud','fall_proud'),('fall_ashamed','fall_shame')]:
        np.testing.assert_allclose(actual[name],expected[other],atol=1e-10)
    # Primary cut is checked on integer steps, like chk_dial.py.
    p=np.maximum(np.ceil(p/.5)-1,0); s=np.maximum(np.ceil(s/.5)-1,0)
    k,m=ref.person_stats(adm,cri,p,s)
    expected=ref.stats_from_sums(k,m.sum(axis=0))['cooc_within']
    terms=np.sum([card.joint_terms(1+(x>0)*2,1+(y>0)*2,3) for x,y in zip(p,s)],axis=0)
    np.testing.assert_allclose(terms[0]/terms[1],expected,atol=1e-12)
