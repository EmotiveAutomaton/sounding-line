"""Separate complete-record policy, actual partial-row validation and refusal."""
from pathlib import Path
import importlib.util
import json
import os
import struct
import subprocess
import sys
import time
import zipfile
import numpy as np
import pytest

from runners.drive.cards import timing_jester_complete_records as card
from runners.drive.cards import timing_jester_ratings as old
from runners.drive.cards.timing_census import read,write,filehash

REPO=Path(__file__).resolve().parents[1]


def fixture(root):
    spec=importlib.util.spec_from_file_location('jester_old_fixture',REPO/'tests/test_drive_cards_timing_jester_ratings.py')
    helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
    root=Path(root).resolve();base,_,_=helpers.make_fixture(root/'source')
    rows=helpers.fixture_rows();records=rows*210+rows[:2];partial=rows[0][:123]+[None]*28;records.append(partial)
    def rec(kind,data):return struct.pack('<HH',kind,len(data))+data
    def bof(kind):return rec(0x0809,struct.pack('<HHHHII',0x600,kind,0xDBB,0x7CC,0,6))
    end=rec(0xA,b'');name='constructed';head=bof(5)+rec(0x42,struct.pack('<H',1200))+rec(0xE0,b'\0'*20)
    offset=len(head)+4+8+len(name)+len(end)
    head+=rec(0x85,struct.pack('<IBBBB',offset,0,0,len(name),0)+name.encode())+end
    cells=[bof(0x10),rec(0x200,struct.pack('<IIHHH',0,len(records),0,151,0))]
    for i,row in enumerate(records):
        for j,value in enumerate(row):
            if value is not None:cells.append(rec(0x203,struct.pack('<HHHd',i,j,0,float(value))))
    raw=head+b''.join(cells)+end
    with zipfile.ZipFile(base['ratings_archive'],'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('constructed.xls',raw)
    manifest=read(base['source_manifest']);manifest.update(workbook_sha256=old.sha_bytes(raw),sheets=[dict(name=name,rows=len(records),columns=151)],advertised_raters=len(records))
    manifest['input_sha256']['ratings_archive']=filehash(base['ratings_archive'])
    Path(base['source_manifest']).write_text(json.dumps(manifest),encoding='utf8')
    failed=root/'original';output=failed/'output'
    with pytest.raises(ValueError):old.execute(output,base,old.CONFIG)
    assert read(output/'PROGRESS.json')['complete_raters']==1024
    write(failed/'PLAN.json',dict(module='runners.drive.cards.timing_jester_ratings',config=old.CONFIG,inputs=base,
        pins={str(Path(old.__file__).resolve()):filehash(old.__file__)}))
    write(failed/'FAILED.json',dict(status='FAILED',error='Constructed final partial source record'))
    decision=root/'DECISION.json';write(decision,read(REPO/'docs/design/stage-15/drive/JESTER_COMPLETE_RECORDS_DECISION_20261018.json'))
    return dict(base,failed_plan=str(failed/'PLAN.json'),failed_record=str(failed/'FAILED.json'),decision=str(decision))


def test_constructed_signed_records_byte_reuse_and_fresh_process(tmp_path):
    start=time.perf_counter();inputs=fixture(tmp_path/'inputs');output=tmp_path/'output'
    result=card.execute(output,inputs,card.CONFIG)
    assert result['raters']==1052 and result['quarantined_records']==1
    original=Path(inputs['failed_plan']).parent/'output/chunks'
    for suffix in ('npy','json'):assert (output/'chunks'/('0000.'+suffix)).read_bytes()==(original/('0000.'+suffix)).read_bytes()
    first=np.load(output/'chunks/0000.npy');assert first[0,:4].tolist()==[-10.,0.,10.,3.125]
    assert read(output/'ACTIVE_TIME.json')['seconds']>=10.295497
    call=tmp_path/'CALL.json';write(call,dict(output=str(output),inputs=inputs,config=card.CONFIG))
    code="import json,sys;from pathlib import Path;from runners.drive.cards import timing_jester_complete_records as c;v=json.load(open(sys.argv[1],encoding='utf8'));assert c.verify(Path(v['output']),v['inputs'],v['config'])['verified']"
    child=subprocess.run([sys.executable,'-c',code,str(call)],cwd=REPO,capture_output=True,text=True,timeout=60,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=='nt' else 0)
    assert child.returncode==0,child.stderr
    write(tmp_path/'SMOKE.json',dict(seconds=time.perf_counter()-start,fresh_exit=child.returncode,
        bytes=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())))


def test_actual_authenticated_partial_record_and_wrong_row_refusal(tmp_path):
    # Owner-authorized source-only check. No ratings aggregate or outcome model.
    inputs=read(REPO/'.agent-state/drive-20261017/builder2/JESTER2PLUS_INPUTS_20261018.json')
    failed=REPO/'results/phase_2_4_stage_15/raw/drive-wave-20261017-w1/Jester2plus-intake'
    recovery=dict(inputs,failed_plan=str(failed/'PLAN.json'),failed_record=str(failed/'FAILED.json'),
        decision=str(REPO/'docs/design/stage-15/drive/JESTER_COMPLETE_RECORDS_DECISION_20261018.json'))
    _,manifest,_,_,sealed=card.validate(recovery,card.CONFIG)
    assert sealed==49
    book,_=old.open_source(inputs,manifest)
    try:
        sheet=book.sheet_by_index(0);values=sheet.row_values(50691);types=sheet.row_types(50691)
        q=card.partial_record(values,types,50691,manifest['sheets'][0],manifest)
        assert q['numeric_cells']==123 and q['blank_cells']==28
        with pytest.raises(ValueError,match='final source row'):card.partial_record(values,types,50690,manifest['sheets'][0],manifest)
        write(tmp_path/'ACTUAL_PARTIAL_PROOF.json',dict(workbook_sha256=manifest['workbook_sha256'],row=50691,
            numeric_cells=123,blank_cells=28,blank_columns_zero_based=q['blank_columns_zero_based'],source_values_disclosed=False))
    finally:book.release_resources()


def test_multiple_partial_rows_and_wrong_occupancy_refuse():
    full=[0.]+[99.]*150;partial=[0.]+[99.]*122+['']*28;types=[2]*123+[0]*28
    spec=dict(name='s',rows=3,columns=151);manifest=dict(source_kind='constructed_fixture',workbook_sha256='known',sheets=[spec])
    q=card.partial_record(partial,types,2,spec,manifest)
    with pytest.raises(ValueError,match='occupancy'):card.partial_record(full,[2]*151,2,spec,manifest)
    class Sheet:
        nrows=3;ncols=151
        def row_values(self,i):return full if i==0 else partial
        def row_types(self,i):return [2]*151 if i==0 else types
    class Book:
        def sheet_by_index(self,i):return Sheet()
        def unload_sheet(self,i):pass
    with pytest.raises(ValueError):list(card.checked_chunks(Book(),manifest,q))


def test_source_policy_configuration_and_quarantine_tamper_refuse(tmp_path):
    inputs=fixture(tmp_path/'inputs');output=tmp_path/'output'
    with pytest.raises(ValueError,match='exact Jester'):card.execute(output,inputs,dict(card.CONFIG,rows_per_chunk=25))
    card.execute(output,inputs,card.CONFIG)
    q=read(output/'QUARANTINE.json');q['original_cell_values'][0]=149
    (output/'QUARANTINE.json').write_text(json.dumps(q),encoding='utf8')
    binding=read(output/'TIMING_BINDINGS.json');binding['outputs']['QUARANTINE.json']=filehash(output/'QUARANTINE.json')
    (output/'TIMING_BINDINGS.json').write_text(json.dumps(binding),encoding='utf8')
    with pytest.raises(ValueError,match='quarantine differs'):card.verify(output,inputs,card.CONFIG)


def test_actual_yield_resume_preserves_original_chunk_and_cumulative_charge(tmp_path):
    inputs=fixture(tmp_path/'inputs');output=tmp_path/'output';write(output/'YIELD_REQUEST.json',dict(reason='fixture'))
    result=card.execute(output,inputs,card.CONFIG);assert result['status']=='yielded' and result['complete_raters']==1024
    path=output/'chunks/0000.npy';before=(path.read_bytes(),path.stat().st_mtime_ns);charged=read(output/'ACTIVE_TIME.json')['seconds']
    (output/'YIELD_REQUEST.json').unlink();result=card.execute(output,inputs,card.CONFIG)
    assert result['raters']==1052 and (path.read_bytes(),path.stat().st_mtime_ns)==before
    assert card.verify(output,inputs,card.CONFIG)['verified'] and read(output/'ACTIVE_TIME.json')['seconds']>=charged
