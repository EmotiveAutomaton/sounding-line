"""Real cost-handler replay and producer-boundary refusal fixtures."""
from pathlib import Path
import pytest
from runners.drive.cards import week3_d7_cost as c
from runners.drive.cards import week3_d7_models as m
from runners.stage14.common import freeze,filehash,read
from tests.test_week3_d7_models import check_core


def execute(output,inputs,config):
    result=c.run(output,inputs,config,loader=lambda _:m.world(writers=3))
    freeze(Path(output)/'KNOWN_ANSWERS.json',check_core())
    return result
def verify(output,inputs,config):
    if read(Path(output)/'KNOWN_ANSWERS.json')!=check_core():raise ValueError('Known-answer replay differs')
    return c.run(output,inputs,config,True,loader=lambda _:m.world(writers=3))


def test_actual_handler(tmp_path):
    execute(tmp_path,{},c.CONFIG);saved=filehash(tmp_path/'PRIVATE_FITS.json')
    assert verify(tmp_path,{},c.CONFIG)['full_fresh_fit_replay']
    assert filehash(tmp_path/'PRIVATE_FITS.json')==saved
    f=read(tmp_path/'FORECAST.json');assert f['full_cpu_seconds']==f['human_cpu_seconds']+f['calibration_cpu_seconds'] and f['reference_arms']==401
    (tmp_path/'PRIVATE_FITS.json').write_text('{}')
    with pytest.raises(ValueError):verify(tmp_path,{},c.CONFIG)


def test_yield_and_config(tmp_path):
    (tmp_path/'YIELD_REQUEST.json').write_text('{}')
    with pytest.raises(InterruptedError):execute(tmp_path,{},c.CONFIG)
    with pytest.raises(ValueError):execute(tmp_path,{},dict(c.CONFIG,arms=2))


def test_source_binding(tmp_path):
    # Exact declared row count and 61 distinct writers, exercising the real
    # producer-reader path without evaluating human outcomes.
    rows=[dict(writer=str(i%61)) for i in range(16855)]
    freeze(tmp_path/'ROWS.json',rows);freeze(tmp_path/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={'ROWS.json':filehash(tmp_path/'ROWS.json')}))
    freeze(tmp_path/'LANDED.json',dict(full_write_through=True,completion_sha256=filehash(tmp_path/'COMPLETE.json')))
    inputs=dict(source_complete=str(tmp_path/'COMPLETE.json'),source_rows=str(tmp_path/'ROWS.json'),source_landing=str(tmp_path/'LANDED.json'))
    # This check reaches grouping, so give the synthetic records chronology.
    for i,r in enumerate(rows):r.update(open_at=i,key=str(i))
    (tmp_path/'ROWS.json').write_text(__import__('json').dumps(rows))
    complete=read(tmp_path/'COMPLETE.json');complete['outputs']['ROWS.json']=filehash(tmp_path/'ROWS.json')
    (tmp_path/'COMPLETE.json').write_text(__import__('json').dumps(complete))
    (tmp_path/'LANDED.json').write_text(__import__('json').dumps(dict(full_write_through=True,completion_sha256=filehash(tmp_path/'COMPLETE.json'))))
    assert c.source(inputs)==rows
    (tmp_path/'ROWS.json').write_text('[]')
    with pytest.raises(ValueError):c.source(inputs)
