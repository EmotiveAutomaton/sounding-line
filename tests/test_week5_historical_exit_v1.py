from datetime import datetime,timezone
import pytest
from runners.drive.cards import week5_historical_exit_v1 as h

BOOT=1794769066.0
def stamp(epoch):return datetime.fromtimestamp(epoch,timezone.utc).isoformat()
def identity(epoch):return dict(pid=12452,created_ticks=int((epoch+h.EPOCH)*10_000_000),executable='python.exe')

def test_corroborated_preboot_identity():
    p=h.preboot(identity(BOOT-1000),stamp(BOOT-500),int((BOOT+h.EPOCH)*10_000_000),BOOT,BOOT+200)
    assert p['native']['pid']==12452

@pytest.mark.parametrize('defect',['disagreement','creation','terminal','order','naive','future','identity'])
def test_unknown_exit_refuses(defect):
    n=identity(BOOT-1000);terminal=stamp(BOOT-500);os_boot=int((BOOT+h.EPOCH)*10_000_000);kernel=BOOT;now=BOOT+200
    if defect=='disagreement':kernel+=20
    if defect=='creation':n=identity(BOOT+5)
    if defect=='terminal':terminal=stamp(BOOT+5)
    if defect=='order':terminal=stamp(BOOT-2000)
    if defect=='naive':terminal='2026-11-15T01:00:00'
    if defect=='future':now=BOOT-1
    if defect=='identity':n['created_ticks']='unknown'
    with pytest.raises(ValueError):h.preboot(n,terminal,os_boot,kernel,now)

def test_live_native_is_never_overridden(monkeypatch):
    monkeypatch.setattr(h,'is_same_live_process',lambda _:True)
    assert h.stopped(identity(BOOT-1000),stamp(BOOT-500)) is False

def test_only_access_denial_uses_boot_evidence(monkeypatch):
    def failed(_):raise OSError(87,'unknown')
    monkeypatch.setattr(h,'is_same_live_process',failed)
    with pytest.raises(OSError):h.stopped(identity(BOOT-1000),stamp(BOOT-500))
