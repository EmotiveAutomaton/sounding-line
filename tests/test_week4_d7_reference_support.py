import pytest
from runners.drive.cards import week4_d7_reference_support as m


def test_all_constructed_assignments_and_fresh_replay(tmp_path,monkeypatch):
    monkeypatch.setattr(m.calibration,'fits',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('no fit allowed')))
    cfg=m.configuration('constructed');r=m.execute(tmp_path,{},cfg)
    assert r['attempted']==200 and r['invalid']==0 and r['supported_writers']==6
    assert m.verify(tmp_path,{},cfg)['no_fits']


def test_invalid_bank_stays_recorded_without_redraw(tmp_path,monkeypatch):
    original=m.calibration.audit_bank
    def altered(*args,**kwargs):
        a=original(*args,**kwargs);a['draws'][0]['same_supported_writers']=False;a['valid']=False;return a
    monkeypatch.setattr(m.calibration,'audit_bank',altered)
    r=m.execute(tmp_path,{},m.configuration('constructed'))
    assert r['attempted']==200 and r['invalid']==1 and not r['support_invariant']


def test_changed_private_output_refused(tmp_path):
    cfg=m.configuration('constructed');m.execute(tmp_path,{},cfg)
    (tmp_path/'PRIVATE_REFERENCE_SUPPORT.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError,match='support replay differs'):m.verify(tmp_path,{},cfg)


def test_input_or_configuration_change_refused(tmp_path):
    with pytest.raises(ValueError,match='No human'):
        m.execute(tmp_path,{'human':'forbidden'},m.configuration('constructed'))
    with pytest.raises(ValueError,match='Frozen'):
        m.execute(tmp_path,{},dict(m.configuration('constructed'),assignments=1))
