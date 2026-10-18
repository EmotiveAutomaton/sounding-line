"""Separate source-only recovery: immutable original, full scientific fixtures."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from runners.drive.cards import timing_pmap as original
from runners.drive.cards import timing_pmap_recovery as card
from runners.drive.cards import timing_pmap_source as old_source
from runners.drive.cards import timing_pmap_source_recovery as source
from runners.drive.cards.timing_census import read, write, filehash


def replace(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True),encoding='utf8')


def fixture(root,mode='positive'):
    root=Path(root).resolve()
    spec=importlib.util.spec_from_file_location('original_pmap_fixture',Path(__file__).with_name('test_drive_cards_timing_pmap.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    inputs=module.fixture(root/'sources',mode)
    rows=read(inputs['raw_roster'])
    rows.append(dict(session='upstream-only',path='upstream-only-unread.jsonl',source_sha256='unread'))
    replace(inputs['raw_roster'],rows);repin_roster(inputs)
    # The original failure is reproduced before constructing the recovery proof.
    try:old_source.Sources(inputs)
    except ValueError as exc:
        assert str(exc)=='source session populations differ'
    else:raise AssertionError('original did not reproduce broader-roster failure')
    failed=root/'failed';plan=failed/'PLAN.json'
    pins={str(Path(original.__file__).resolve()):filehash(original.__file__),
          str(Path(old_source.__file__).resolve()):filehash(old_source.__file__)}
    write(plan,dict(module='runners.drive.cards.timing_pmap',inputs=inputs,config=card.CONFIG,
        pins=pins,max_wall_seconds=5400,forecast_cpu_seconds=1800))
    write(failed/'FAILED.json',dict(status='FAILED',engineering_retry_available=True,at='2026-10-18T00:00:02+00:00'))
    write(failed/'OWNER.json',dict(plan_sha256=filehash(plan),at='2026-10-18T00:00:00+00:00'))
    (failed/'execute.stderr.log').write_text('ValueError: source session populations differ\n',encoding='utf8')
    write(failed/'output/INPUT_BINDING.json',original.input_binding(inputs,card.CONFIG))
    start=time.monotonic();preflight=source.Sources(inputs).preflight()
    preflight.update(status='PASSED',elapsed_seconds=time.monotonic()-start,input_binding=original.input_binding(inputs,card.CONFIG),
        failed_plan_sha256=filehash(plan),failed_record_sha256=filehash(failed/'FAILED.json'),source_sha256=filehash(source.__file__))
    write(root/'PREFLIGHT.json',preflight)
    result={**inputs,'failed_plan':str(plan),'failed_record':str(failed/'FAILED.json'),'source_preflight':str(root/'PREFLIGHT.json')}
    write(root/'RECOVERY_INPUTS.json',result)
    return result


def repin_roster(inputs):
    plan=read(inputs['foundation_plan']);root=Path(inputs['repo_root'])
    plan['pins'][Path(inputs['raw_roster']).relative_to(root).as_posix()]=filehash(inputs['raw_roster'])
    replace(inputs['foundation_plan'],plan)
    complete=read(inputs['foundation_complete']);complete['plan_sha256']=filehash(inputs['foundation_plan'])
    replace(inputs['foundation_complete'],complete)


@pytest.mark.parametrize('mode,state',[('positive','positive'),('null','null'),('negative','negative')])
def test_signed_null_reverse_broader_roster_fresh_process(tmp_path,mode,state):
    inputs=fixture(tmp_path/'fixture',mode);output=tmp_path/'output';start=time.monotonic()
    result=card.execute(output,inputs,card.CONFIG)
    assert result['primary']['state']==state and result['permutations']==200
    population=read(output/'RECOVERY_SOURCE.json')['population']
    assert population['primary_sessions']==24 and population['raw_roster_sessions']==25
    assert population['upstream_only_sessions']==['upstream-only']
    assert read(output/'ACTIVE_TIME.json')['seconds']>=2
    code='import sys,json;from pathlib import Path;from runners.drive.cards.timing_pmap_recovery import verify,CONFIG;print(verify(Path(sys.argv[1]),json.load(open(sys.argv[2])),CONFIG))'
    child=subprocess.run([sys.executable,'-c',code,str(output),str(tmp_path/'fixture/RECOVERY_INPUTS.json')],capture_output=True,text=True,
        env={**os.environ,'PYTHONHASHSEED':'919','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},timeout=90)
    assert child.returncode==0,child.stdout+child.stderr
    write(tmp_path/'FIXTURE_RECEIPT.json',dict(mode=mode,elapsed_seconds=time.monotonic()-start,
        output_bytes=sum(p.stat().st_size for p in output.rglob('*') if p.is_file()),fresh_exit=child.returncode))


@pytest.mark.parametrize('defect',['missing','duplicate'])
def test_primary_coverage_and_duplicate_refusal(tmp_path,defect):
    inputs=fixture(tmp_path/'fixture');base={k:inputs[k] for k in old_source.INPUTS};rows=read(inputs['raw_roster'])
    rows=rows[1:] if defect=='missing' else rows+[rows[0]]
    replace(inputs['raw_roster'],rows);repin_roster(inputs)
    with pytest.raises(ValueError,match='primary|duplicate'):source.Sources(base)


@pytest.mark.parametrize('defect',['canonical','identity','vector'])
def test_all_metadata_preflight_refuses_changed_join(tmp_path,defect):
    inputs=fixture(tmp_path/'fixture');s=source.Sources({k:inputs[k] for k in old_source.INPUTS})
    first=sorted(s.p2)[0];m=s.meta[first]['rows'][0]
    if defect=='canonical':s.audit[m['key']]['canonical_positions']=[1]
    elif defect=='identity':s.content[m['key']]['writer']='forged'
    else:s.content[m['key']]['options'][0]=-1
    with pytest.raises(ValueError,match='source reconstruction|identity|vector index'):s.preflight()


def test_wrong_failure_old_output_or_preflight_refused(tmp_path):
    inputs=fixture(tmp_path/'fixture');failed=Path(inputs['failed_plan']).parent
    stderr=failed/'execute.stderr.log';saved=stderr.read_bytes();stderr.write_text('different error',encoding='utf8')
    with pytest.raises(ValueError,match='population preflight'):card.recovery(inputs,card.CONFIG)
    stderr.write_bytes(saved)
    write(failed/'output/PROGRESS.json',dict(done=1))
    with pytest.raises(ValueError,match='passed source'):card.recovery(inputs,card.CONFIG)
    (failed/'output/PROGRESS.json').unlink()
    preflight=read(inputs['source_preflight']);preflight['input_binding']['inputs']['raw_roster']='forged'
    replace(inputs['source_preflight'],preflight)
    with pytest.raises(ValueError,match='preflight authentication'):card.recovery(inputs,card.CONFIG)


def test_real_yield_path_resume_cost_and_fixed_config(tmp_path):
    inputs=fixture(tmp_path/'fixture');output=tmp_path/'run/output'
    write(output/'YIELD_REQUEST.json',dict(reason='fixture'))
    result=card.execute(output,inputs,card.CONFIG)
    assert result['status']=='yielded' and result['completed']==1 and result['active_seconds']>=2
    first=next((output/'sessions').glob('*.json.gz'));saved=first.read_bytes()
    (output/'YIELD_REQUEST.json').unlink()
    assert card.execute(output,inputs,card.CONFIG)['primary']['state']=='positive'
    assert first.read_bytes()==saved
    with pytest.raises(ValueError,match='configuration'):card.execute(output,inputs,{**card.CONFIG,'permutations':25})
