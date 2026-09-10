import pytest
from runners.stage9.common import closure,digest,write
from runners.stage9.model_pilot import completed,queue_identity


def test_calibration_completion_rejects_other_cell_and_changed_output(tmp_path):
    evidence=tmp_path/'prediction.json';write(evidence,{'prediction':'original'})
    plan={'cell_identity':'a'*64}
    receipt={'cell_identity':'a'*64,'plan_sha256':digest(plan),'outputs':closure([evidence])}
    write(tmp_path/'COMPLETE.json',receipt)
    assert completed(tmp_path,plan)==receipt
    with pytest.raises(ValueError,match='identity'):
        completed(tmp_path,{'cell_identity':'b'*64})
    write(evidence,{'prediction':'changed'})
    with pytest.raises(ValueError,match='closure'):
        completed(tmp_path,plan)


def test_calibration_retains_the_actual_queue_identity(monkeypatch):
    monkeypatch.setenv('S9_CELL_IDENTITY','f'*64)
    assert queue_identity()=='f'*64
    monkeypatch.setenv('S9_CELL_IDENTITY','')
    with pytest.raises(ValueError,match='identity'):queue_identity()
