"""Known-answer checks for the local November 21 rows and budget identities."""
import numpy as np
import pandas as pd
import pytest

from runners.drive.cards import week6_person_small_v1 as engine
from runners.drive.cards import week6_person_policy_v1 as policy


def fixture(card, member):
    rng=np.random.default_rng(34)
    n=2400
    keys=engine.source_columns(card,member)
    values={k:rng.integers(1,6,n) for k in keys}
    values['id']=np.repeat(np.arange(80).astype(str),30)
    if 'interaction' in keys:
        values['interaction']=rng.integers(1,3,n)
    if 'anxious_schoolwork' in keys:
        values['anxious_schoolwork']=(values['afraid']+values['sad']+rng.normal(size=n)>6).astype(int)
    return pd.DataFrame(values)


@pytest.mark.parametrize('card,member',sorted(set(engine.LINEAR)|engine.PAIRS))
def test_two_implementations(card,member):
    data=engine.prepare(card,member,fixture(card,member))
    mass=np.random.default_rng(31).multinomial(data.people,np.full(data.people,1/data.people))
    original=engine.evaluate(data,mass,lambda:None)
    replay=engine.evaluate(data,mass,lambda:None,verify=True)
    assert set(original)==set(replay)==set(data.specs)
    for key in original:
        assert original[key] is not None
        assert original[key]==pytest.approx(replay[key],abs=1e-7)
    if card=='ANX1': assert original['explained']+original['residual']==pytest.approx(1)
    if member=='0060': assert original['L/anxious_schoolwork/afraid']>.3
    if card=='PRD1': assert 'a/contrast' in original


def test_null_and_person_offsets():
    f=fixture('ANX1','0072')
    f['parent_worried']=f.parent_afraid
    d=engine.prepare('ANX1','0072',f)
    fit=engine.evaluate(d,None,lambda:None)
    assert fit['L/parent_worried/parent_afraid']==pytest.approx(1)
    assert fit['L/parent_worried/parent_sad']==pytest.approx(0,abs=1e-9)
    f['parent_worried']+=f.id.astype(int)%2
    moved=engine.evaluate(engine.prepare('ANX1','0072',f),None,lambda:None)
    assert moved==pytest.approx(fit)


def test_singular_preserves_missing():
    f=fixture('PBK1','0072')
    f['parent_sad']=f.parent_afraid
    result=engine.evaluate(engine.prepare('PBK1','0072',f),None,lambda:None)
    assert all(v is None for v in result.values())


def test_pair_uses_identical_reports():
    f=fixture('PRD1','0057')
    mask=(f.interaction==1)&(f.int_proud==1)
    f.loc[mask,'int_enthusiastic']=np.nan
    d=engine.prepare('PRD1','0057',f)
    assert d.metadata['panels']['a']['rows']==int(((f.interaction==1)&~mask).sum())


def test_binding_and_codes_fail_closed(tmp_path):
    f=fixture('ANX1','0060');f.loc[0,'anxious_schoolwork']=2
    with pytest.raises(ValueError): engine.prepare('ANX1','0060',f)
    with pytest.raises(ValueError): engine.source_columns('ANX1','0064')
    with pytest.raises(ValueError): engine.binding('ANX1','0060',tmp_path)
    with pytest.raises(KeyError): engine.prepare('PBK1','0072',fixture('PBK1','0072').drop(columns='parent_sad'))


def test_changed_manifest_is_rejected(tmp_path,monkeypatch):
    root=tmp_path/engine.ROOT_NAME; root.mkdir()
    (root/'DRT1_MANIFEST.json').write_bytes(b'{}')
    monkeypatch.setenv('SystemDrive',root.drive)
    with pytest.raises(ValueError,match='manifest'): engine.binding('ANX1','0060',root)


def test_scoped_allowances():
    for card in ('ANX1','PRD1','PBK1'):
        assert policy.card_identity(card)==('ES','ES-'+card,20000)
    with pytest.raises(ValueError): policy.card_identity('LD1')
    with pytest.raises(ValueError): policy.review_budget_scope(dict(key='ES-ANX1',family='ES',ceiling_cpu_seconds=20001))

