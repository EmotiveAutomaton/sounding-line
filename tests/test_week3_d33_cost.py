from pathlib import Path
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week3_d33_cost as card
from runners.drive.cards.timing_p6 import write_equal
from runners.drive.cards.timing_census import read
from tests.test_drive_d33_calibrated import fixture_prepared


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return card.one_pass(output,inputs,config,prepare=fixture_prepared)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return card.one_pass(output,inputs,config,True,fixture_prepared)


def test_actual_handlers_complete_first_block_fresh_replay_and_tamper(tmp_path):
    source=tmp_path/'FIXTURE.json';write_equal(source,dict(constructed=True))
    inputs=dict(prior_completion=str(source),prior_receipt=str(source));output=tmp_path/'out'
    assert execute(output,inputs,card.CONFIG)['timing_only']
    assert verify(output,inputs,card.CONFIG)['complete_first_block_replay']
    assert read(output/'PROBE.json')['coverage']['retained_writers']==5
    assert read(output/'FORECAST.json')['full_cpu_seconds']>0
    assert not (output/'PRIMARY.json').exists()
    assert len(list((output/'inference').glob('block-??.json')))==1
    saved=read(output/'PROBE.json');saved['complete_blocks']=2
    (output/'PROBE.json').write_text(__import__('json').dumps(saved),encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):verify(output,inputs,card.CONFIG)


def test_bad_configuration_refuses_before_source_access(tmp_path):
    with pytest.raises(ValueError,match='Frozen'):execute(tmp_path,{},dict(card.CONFIG,schema=2))
