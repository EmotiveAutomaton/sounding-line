"""The whole-design timing pass cannot expose intermediate power scores."""
import json

import pytest

from runners.drive.cards import week3_adapter_timing as card
from runners.drive.cards.timing_census import read
from tests.test_week3_adapter_audit import fixture


def test_full_fixture_work_and_fresh_replay_record_only_cost(tmp_path):
    path=tmp_path/'fixture.json';path.write_text(json.dumps(fixture()),encoding='utf8')
    output=tmp_path/'output';inputs=dict(fixture=str(path))
    assert card.execute(output,inputs,card.CONSTRUCTED)['cost_only']
    assert card.verify(output,inputs,card.CONSTRUCTED)['verified']
    work=read(output/'WORK.json');forecast=read(output/'FORECAST.json')
    assert work['work_counts']['cells']==2 and work['work_counts']['worlds']==8
    assert not work['scientific_admission'] and not (output/'SUMMARY.json').exists()
    assert forecast['projected_execute_plus_verify']['cpu_seconds']>=forecast['pilot_charged_cpu_seconds']
    path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='differs'):card.verify(output,inputs,card.CONSTRUCTED)
