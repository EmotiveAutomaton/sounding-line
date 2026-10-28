import ctypes
import errno
import json
import os
import threading
import time
from pathlib import Path
import pytest
from runners.drive.cards import week3_tr4_sensitivity as original
from runners.drive.cards import week3_tr4_sensitivity_recovery as recovery


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf8')


def make_source(tmp_path,monkeypatch,two_worlds=False):
    config=dict(original.CONFIGS['constructed'])
    if two_worlds:
        config['worlds']=[[.15,202610298],[.30,202610297]]
        monkeypatch.setitem(original.CONFIGS,'constructed',config)
    parent=tmp_path/'parent.json';write(parent,dict(full_write_through=True,id='S15-TR4-20261027'))
    base={'parent_landing':str(parent)};root=tmp_path/'source'
    original.execute(root/'output',base,config)
    write(root/'PLAN.json',dict(config=config,inputs=base,pins={str(parent):original.filehash(parent)}))
    write(root/'COMPLETE.json',dict(test_source=True))
    m=dict(source_root=str(root),plan_sha256=original.filehash(root/'PLAN.json'),terminal_name='COMPLETE.json',terminal_sha256=original.filehash(root/'COMPLETE.json'),files={'00.json':original.filehash(root/'output/cells/00.json')})
    manifest=tmp_path/'resume.json';write(manifest,m)
    return root,config,dict(**base,resume_manifest=str(manifest))


def test_partial_resume_matches_original_and_replays_retained_cell(tmp_path,monkeypatch):
    source,config,inputs=make_source(tmp_path,monkeypatch,True)
    old=recovery.original.parent.run_analysis;calls=[]
    def counted(*a,**k):calls.append(1);return old(*a,**k)
    monkeypatch.setattr(recovery.original.parent,'run_analysis',counted)
    output=tmp_path/'recovery';recovery.execute(output,inputs,config)
    assert len(calls)==1
    assert recovery.verify(output,inputs,config)['retained_cells_freshly_replayed']==1 and len(calls)==3
    for name in ['cells/00.json','cells/01.json','SUMMARY.json','BINDING.json']:
        assert (output/name).read_bytes()==(source/'output'/name).read_bytes()


def test_full_prefix_executes_no_new_world_but_verification_reconstructs(tmp_path,monkeypatch):
    source,config,inputs=make_source(tmp_path,monkeypatch)
    old=recovery.original.parent.run_analysis
    def refuse(*a,**k):raise AssertionError('retained execution recomputed')
    monkeypatch.setattr(recovery.original.parent,'run_analysis',refuse)
    output=tmp_path/'recovery';recovery.execute(output,inputs,config)
    monkeypatch.setattr(recovery.original.parent,'run_analysis',old)
    assert recovery.verify(output,inputs,config)['complete_input_replay']
    cell=json.loads((output/'cells/00.json').read_text());cell['result']['primary']['status']='tampered';write(output/'cells/00.json',cell)
    with pytest.raises(ValueError,match='cell replay'):recovery.verify(output,inputs,config)


def test_source_tamper_and_nonprefix_are_refused_before_compute(tmp_path,monkeypatch):
    source,config,inputs=make_source(tmp_path,monkeypatch)
    cell=source/'output/cells/00.json';cell.write_bytes(cell.read_bytes()+b' ')
    with pytest.raises(ValueError,match='bytes differ'):recovery.execute(tmp_path/'out',inputs,config)
    manifest=Path(inputs['resume_manifest']);m=json.loads(manifest.read_text());m['files']={'01.json':'x'};write(manifest,m)
    with pytest.raises(ValueError,match='prefix'):recovery.execute(tmp_path/'out',inputs,config)


def test_permanent_sharing_refusal_is_bounded_and_keeps_last_status(tmp_path,monkeypatch):
    path=tmp_path/'PROGRESS.json';path.write_text('old');calls=[]
    def refuse(*a):calls.append(1);raise PermissionError(errno.EACCES,'test sharing refusal')
    monkeypatch.setattr(recovery.os,'replace',refuse)
    with pytest.raises(PermissionError):recovery.progress(path,{'fresh':True},attempts=3,delay=0)
    assert len(calls)==3 and path.read_text()=='old'


def test_unrelated_io_error_is_not_retried(tmp_path,monkeypatch):
    calls=[]
    def refuse(*a):calls.append(1);raise OSError(errno.ENOSPC,'test disk refusal')
    monkeypatch.setattr(recovery.os,'replace',refuse)
    with pytest.raises(OSError):recovery.progress(tmp_path/'p.json',{},attempts=3,delay=0)
    assert len(calls)==1


@pytest.mark.skipif(os.name!='nt',reason='native Windows sharing behavior')
def test_actual_windows_read_handle_releases_before_bounded_replace(tmp_path):
    path=tmp_path/'PROGRESS.json';path.write_text('old')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
    kernel.CreateFileW.restype=ctypes.c_void_p;kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.CreateFileW(str(path),0x80000000,1,None,3,0,None)
    assert handle not in (None,ctypes.c_void_p(-1).value)
    released=threading.Event()
    def release():
        time.sleep(.15);kernel.CloseHandle(handle);released.set()
    worker=threading.Thread(target=release);worker.start()
    try:recovery.progress(path,{'fresh':True})
    finally:worker.join()
    assert released.is_set() and json.loads(path.read_text())=={'fresh':True}
