from pathlib import Path
import contextlib
import json
import pytest
from runners.drive.cards import week5_runtime_v6 as runtime


def banks(tmp_path, monkeypatch, occupied=()):
    old, new = tmp_path/'original', tmp_path/'additional'
    old.mkdir(); new.mkdir()
    monkeypatch.setattr(runtime.policy, 'OLD_SLOTS', old)
    monkeypatch.setattr(runtime.policy, 'NEW_SLOTS', new)
    calls=[]
    @contextlib.contextmanager
    def mutex(path):
        assert path==old
        calls.append('lock')
        yield
        calls.append('unlock')
    monkeypatch.setattr(runtime.kernel, 'admission_lock', mutex)
    def admission(plan):
        assert calls==['lock']
        calls.append('admission')
        return {'admitted':True}
    monkeypatch.setattr(runtime.policy, 'admission', admission)
    monkeypatch.setattr(runtime, 'native_identity', lambda: {'pid':1234})
    for index in occupied:
        ((new if index>=4 else old)/f'slot-{index}.json').write_text('retained lease',encoding='utf8')
    return old,new,calls


@pytest.mark.parametrize('family,occupied,expected',[
    ('BK',(),0),('BK',(0,),1),('BK',(0,1,2),3),
    ('GO',(),4),('MD',(4,5,6,7),0),('CH',(4,5,6,7,0,1,2),3),
])
def test_family_banks(tmp_path,monkeypatch,family,occupied,expected):
    old,new,calls=banks(tmp_path,monkeypatch,occupied)
    before={p:p.read_bytes() for b in (old,new) for p in b.glob('slot-*.json')}
    lease,resources=runtime.claim(tmp_path/'attempt',dict(card='constructed',family=family,projected_peak_ram_GiB=1))
    assert lease[0]==(new if expected>=4 else old)/f'slot-{expected}.json'
    assert json.loads(lease[0].read_text())==lease[1]
    assert lease[1]['family']==family and lease[1]['native']=={'pid':1234}
    assert resources=={'admitted':True}
    assert calls==['lock','admission','unlock']
    assert all(p.read_bytes()==raw for p,raw in before.items())


def test_bk_refuses_additional_even_when_idle(tmp_path,monkeypatch):
    old,new,_=banks(tmp_path,monkeypatch,range(4))
    with pytest.raises(RuntimeError,match='No free counted slot'):
        runtime.claim(tmp_path/'attempt',dict(card='constructed',family='BK',projected_peak_ram_GiB=1))
    assert not list(new.iterdir())
    assert all(p.read_text()=='retained lease' for p in old.iterdir())


def test_resource_admission_remains_first(tmp_path,monkeypatch):
    old,new,_=banks(tmp_path,monkeypatch)
    def refused(plan):raise RuntimeError('fixture policy refusal')
    monkeypatch.setattr(runtime.policy,'admission',refused)
    with pytest.raises(RuntimeError,match='fixture policy refusal'):
        runtime.claim(tmp_path/'attempt',dict(card='constructed',family='BK',projected_peak_ram_GiB=1))
    assert not list(old.iterdir()) and not list(new.iterdir())


def test_only_claim_bank_and_launcher_import_change():
    root=Path(__file__).resolve().parents[1]
    old=(root/'runners/drive/cards/week5_runtime_v5.py').read_text(encoding='utf8')
    new=(root/'runners/drive/cards/week5_runtime_v6.py').read_text(encoding='utf8')
    old=old.replace('Week 5 v5 successor','Week 5 v6 successor',1)
    start=old.index('        # Prefer the new bank.')
    end=old.index("            path=(policy.NEW_SLOTS",start)
    newstart=new.index('        # Packet section 3 reserves BK')
    newend=new.index("            path=(policy.NEW_SLOTS",newstart)
    assert old[:start]==new[:newstart] and old[end:]==new[newend:]
    launch=(root/'runners/drive/week5_launch_v5.py').read_text(encoding='utf8')
    assert launch.replace('week5_runtime_v5','week5_runtime_v6')==(root/'runners/drive/week5_launch_v6.py').read_text(encoding='utf8')
