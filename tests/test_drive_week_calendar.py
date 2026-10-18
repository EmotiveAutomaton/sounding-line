from datetime import datetime
import pytest
from runners.drive.calendar_20261018_week import tick,due_names,MILESTONES
from runners.stage14.common import atomic,read


def test_week_deadlines_are_exact_and_nonrepeating(tmp_path):
    config=tmp_path/'watch.json';atomic(config,dict(transition_only=False,health_interval_seconds=21600))
    assert due_names(datetime.fromisoformat('2026-10-19T18:59:59+00:00'),set())==[]
    at=datetime.fromisoformat('2026-10-19T19:00:00+00:00')
    assert tick(tmp_path,config,at)==['ENGINE_EXPORT_DUE']
    assert tick(tmp_path,config,at)==[]
    assert not read(config)['transition_only']
    with pytest.raises(ValueError):due_names(datetime(2026,10,19),set())


def test_reopen_then_final_drain_retains_other_watcher_state(tmp_path):
    config=tmp_path/'watch.json';original=dict(transition_only=True,owner='same',health_interval_seconds=21600,paths=['keep'])
    atomic(config,original)
    tick(tmp_path,config,datetime.fromisoformat('2026-10-22T14:00:00+00:00'))
    assert read(config)==dict(original,transition_only=False)
    tick(tmp_path,config,datetime.fromisoformat('2026-10-26T03:00:00+00:00'))
    assert not read(config)['transition_only']
    assert not (tmp_path/'FINAL_DRAIN_RECONCILIATION.json').exists()
    tick(tmp_path,config,datetime.fromisoformat('2026-10-26T05:00:00+00:00'))
    assert read(config)==original


def test_late_catchup_never_leaves_ended_week_open(tmp_path):
    config=tmp_path/'watch.json';atomic(config,dict(transition_only=True))
    assert tick(tmp_path,config,datetime.fromisoformat('2026-10-27T00:00:00+00:00'))==[n for n,_ in MILESTONES]
    assert read(config)['transition_only']
    assert all(not read(tmp_path/(name+'.json'))['publication_performed'] for name,_ in MILESTONES)
