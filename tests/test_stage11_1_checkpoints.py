from datetime import datetime,timezone
import pytest
from runners.stage11_1.checkpoints import schedule,due


def test_only_commissioned_checkpoints_and_timezone_boundary():
    contract=dict(commissioned_at='2026-09-18T16:18:24+00:00',checkpoints_elapsed_hours=[4,12,24,36],
                  reporting_starts='2026-09-20T13:00:00+00:00',checkpoint='2026-09-20T15:00:00+00:00')
    rows=schedule(contract)
    assert len(rows)==6 and rows[0]['at']=='2026-09-18T20:18:24+00:00'
    assert due(rows,datetime(2026,9,18,20,18,23,tzinfo=timezone.utc))==[]
    assert due(rows,datetime(2026,9,18,20,18,24,tzinfo=timezone.utc))==rows[:1]
    assert len(due(rows,datetime(2026,9,21,tzinfo=timezone.utc)))==6
    with pytest.raises(ValueError):due(rows,datetime(2026,9,18))
