from pathlib import Path
import pytest
from runners.drive.cards import engine_signatures as base,engine_signatures_guarded as card
from tests.test_drive_engine_signatures import fixture,save


@pytest.mark.parametrize('marker',['STOP','output/YIELD_REQUEST.json'])
def test_stop_before_input_loading(tmp_path,monkeypatch,marker):
    p=tmp_path/marker;p.parent.mkdir(parents=True,exist_ok=True);save(p,dict(reason='fixture-stop'))
    monkeypatch.setattr(card,'load',lambda *a:pytest.fail('must stop before source loading'))
    with pytest.raises(RuntimeError):card.execute(tmp_path/'output',{},card.CONSTRUCTED)


def test_mid_comparison_yield_and_unchanged_full_replay(tmp_path,monkeypatch):
    inputs=dict(fixture=save(tmp_path/'fixture.json',fixture()))
    output=tmp_path/'output';analyze=card.analyze
    def interrupted(rows,config,progress):
        save(output/'YIELD_REQUEST.json',dict(reason='fixture-resource-floor'))
        progress(dict(phase='boundary'))
        pytest.fail('must stop at progress boundary')
    monkeypatch.setattr(card,'analyze',interrupted)
    with pytest.raises(RuntimeError):card.execute(output,inputs,card.CONSTRUCTED)
    assert not (output/'SUMMARY.json').exists()
    (output/'YIELD_REQUEST.json').unlink();monkeypatch.setattr(card,'analyze',analyze)
    result=card.execute(output,inputs,card.CONSTRUCTED)
    assert card.verify(output,inputs,card.CONSTRUCTED)['summary']==result
    assert result==base.execute(tmp_path/'original',inputs,base.CONSTRUCTED)
