from datetime import timedelta
from runners.theory_days.calendar import tick,FREEZE,DRAIN
from runners.stage14.common import freeze,read

def test_deadlines_and_idempotent_late_recovery(tmp_path):
    config=tmp_path/'watch.json';freeze(config,dict(transition_only=False,keep='owner'))
    root=tmp_path/'markers';root.mkdir()
    assert tick(root,config,FREEZE-timedelta(seconds=1))==[]
    assert tick(root,config,FREEZE)==['FINAL_DIGEST_AND_START_FREEZE']
    assert not read(config)['transition_only']
    assert tick(root,config,DRAIN)==['FINAL_DRAIN_RECONCILIATION']
    assert read(config)==dict(transition_only=True,keep='owner')
    assert tick(root,config,DRAIN+timedelta(days=1))==[]
