import json
import pytest
from runners.drive.cards import week3_tr4_model_checks as m


def test_actual_handler_reentry_and_changed_output_refusal(tmp_path):
    first=m.execute(tmp_path,{},m.CONFIG)
    assert all(first['gates'].values())
    before=(tmp_path/'CHECKS.json').read_bytes()
    assert m.execute(tmp_path,{},m.CONFIG)==first
    assert (tmp_path/'CHECKS.json').read_bytes()==before
    assert m.verify(tmp_path,{},m.CONFIG)['complete_input_replay']
    value=json.loads(before);value['gates']['rising_tracked']=False
    (tmp_path/'CHECKS.json').write_text(json.dumps(value),encoding='utf8')
    with pytest.raises(ValueError):m.verify(tmp_path,{},m.CONFIG)


def test_corpus_input_and_changed_configuration_refused(tmp_path):
    with pytest.raises(ValueError):m.execute(tmp_path,{'human':'not-consumed'},m.CONFIG)
    with pytest.raises(ValueError):m.execute(tmp_path,{},dict(m.CONFIG,sessions=12))
