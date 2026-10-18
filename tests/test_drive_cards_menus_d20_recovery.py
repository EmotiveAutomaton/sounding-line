import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from runners.drive.cards import menus_d20 as original
from runners.drive.cards import menus_d20_recovery as repair
from runners.drive.cards.menus_io import read,write,sha256,input_hashes,assert_equal
from tests.test_drive_cards_menus_d20 import fixture


def failed_fixture(root,shared=False):
    """Serialized known world plus an explicitly constructed capacity-failure receipt."""
    inputs,config=fixture(root,shared=shared);prior=root/'prior';prior.mkdir()
    result=original.execute(prior/'output',inputs,config)
    pins={str(value):sha256(value) for value in inputs.values()}
    for module in (original,original.source):
        path=str(Path(module.__file__).resolve());pins[path]=sha256(path)
    write(prior/'PLAN.json',dict(card='D20',module='runners.drive.cards.menus_d20',inputs=inputs,config=config,
        pins=pins,at='2026-10-18T00:00:00+00:00',max_wall_seconds=360,max_output_bytes=512*1024**2))
    write(prior/'FAILED.json',dict(status='FAILED',error="RuntimeError('Frozen output byte cap exceeded')",
        engineering_retry_available=True,at='2026-10-18T00:00:01+00:00',synthetic_fixture_only=True))
    inventory=dict(original_plan_sha256=sha256(prior/'PLAN.json'),original_failure_sha256=sha256(prior/'FAILED.json'),sessions={})
    for path in (prior/'output/sessions').glob('*.json'):
        if path.name.endswith('.seal.json'):continue
        inventory['sessions'][path.stem]=dict(sha256=sha256(path),seal_sha256=sha256(path.with_suffix('.seal.json')),bytes=path.stat().st_size)
    write(root/'INVENTORY.json',inventory)
    return inputs|dict(original_plan=str(prior/'PLAN.json'),original_failure=str(prior/'FAILED.json'),
        original_inventory=str(root/'INVENTORY.json')),config,result


def scientific_report(report):
    return {k:v for k,v in report.items() if k not in ('session_hashes','comparisons_hash','recovery','comparison_storage')}


def test_positive_exact_byte_parity_resume_reentry_fresh_process(tmp_path):
    inputs,config,expected=failed_fixture(tmp_path);output=tmp_path/'recovery';output.mkdir()
    write(output/'YIELD_REQUEST.json',{})
    assert repair.execute(output,inputs,config)['status']=='yielded'
    (output/'YIELD_REQUEST.json').unlink();actual=repair.execute(output,inputs,config)
    assert_equal(scientific_report(actual),scientific_report(expected))
    assert actual['primary']['state']=='positive' and actual['recovery']['reused_sessions']==16
    for path in (output/'sessions').glob('*.gz'):
        assert gzip.decompress(path.read_bytes())==(tmp_path/'prior/output/sessions'/path.stem).read_bytes()
    assert gzip.decompress((output/'COMPARISONS.json.gz').read_bytes())==(tmp_path/'prior/output/COMPARISONS.json').read_bytes()
    before={str(p):sha256(p) for p in output.rglob('*') if p.is_file()}
    assert repair.execute(output,inputs,config)==actual
    assert before=={str(p):sha256(p) for p in output.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(output),inputs=inputs,config=config))
    code='import json,sys;from runners.drive.cards.menus_d20_recovery import verify;assert verify(**json.load(open(sys.argv[1]))) ["original_json_bytes_preserved"]'
    subprocess.run([sys.executable,'-B','-c',code,str(request)],check=True,timeout=60,env=os.environ|dict(PYTHONHASHSEED='721'))
    path=next((output/'sessions').glob('*.gz'));path.write_bytes(path.read_bytes()+b'bad')
    with pytest.raises(ValueError,match='changed'):repair.verify(output,inputs,config)


def test_null_parity_and_original_checkpoint_damage_refused(tmp_path):
    inputs,config,expected=failed_fixture(tmp_path,shared=True);output=tmp_path/'recovery'
    actual=repair.execute(output,inputs,config)
    assert_equal(scientific_report(actual),scientific_report(expected))
    assert actual['primary']['state']=='null' and repair.verify(output,inputs,config)['verified']
    path=next(p for p in (tmp_path/'prior/output/sessions').glob('*.json') if not p.name.endswith('.seal.json'))
    path.write_bytes(path.read_bytes()+b' ')
    # Even rewriting the original seal cannot evade the externally pinned inventory.
    path.with_suffix('.seal.json').write_text(json.dumps(dict(sha256=sha256(path))),encoding='utf8')
    with pytest.raises(ValueError):repair.verify(output,inputs,config)


def test_capacity_charge_source_config_and_inventory_refusals(tmp_path):
    inputs,config,_=failed_fixture(tmp_path);output=tmp_path/'retry/output';output.parent.mkdir()
    write(output.parent/'PLAN.json',dict(module=repair.__name__,max_wall_seconds=360,max_output_bytes=512*1024**2))
    with pytest.raises(ValueError,match='charge'):repair.context(output,inputs,config)
    (output.parent/'PLAN.json').write_text(json.dumps(dict(module=repair.__name__,max_wall_seconds=359,max_output_bytes=512*1024**2)),encoding='utf8')
    assert repair.context(output,inputs,config)[3]['prior_elapsed_charged_seconds']==1
    with pytest.raises(ValueError):repair.context(output,inputs,config|dict(seed=config['seed']+1))
    changed=read(inputs['original_inventory']);changed['sessions'].pop(next(iter(changed['sessions'])))
    Path(inputs['original_inventory']).write_text(json.dumps(changed),encoding='utf8')
    with pytest.raises(ValueError,match='roster'):repair.context(output,inputs,config)


def test_deterministic_gzip_all_json_float_bytes(tmp_path):
    raw=b'{"f":[-0.0,1.2345678901234567,1e-300],"text":"\\u2019"}\n'
    a=repair.compressed(tmp_path/'a.gz',raw);b=repair.compressed(tmp_path/'b.gz',raw)
    assert a==b and (tmp_path/'a.gz').read_bytes()==(tmp_path/'b.gz').read_bytes()
    assert gzip.decompress((tmp_path/'a.gz').read_bytes())==raw
