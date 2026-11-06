import copy
import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week4_conflict_stats as m


def test_exact_known_worlds_and_dense_gls():
    with threadpool_limits(limits=1):
        assert len(m.known_answers()) == 6


def test_sign_reexpression_preserves_primary():
    rows,_=m.world('own_and_conflict');x,y,w=m.design(rows)
    with threadpool_limits(limits=1):
        first=m.adjusted_fit(m.sufficient(x,y,w))
        x[:,-1]*=-1
        other=m.adjusted_fit(m.sufficient(x,y,w))
    assert first['own']==pytest.approx(other['own'],abs=1e-9)
    assert first['coefficients']['negative_margin']==pytest.approx(-other['coefficients']['negative_margin'],abs=1e-9)


def test_collinear_conflict_refuses():
    rows,_=m.world('own');x,y,w=m.design(rows);x[:,-1]=x[:,-2]
    with pytest.raises(ValueError,match='Conflict'):
        m.adjusted_fit(m.sufficient(x,y,w))


def test_original_baseline_is_unchanged():
    rows,_=m.world('own');x,y,w=m.design(rows)
    with threadpool_limits(limits=1):
        fit=m.paired_fit(m.sufficient(x,y,w),m.sufficient(x[:,:10],y,w))
        old=m.original.fit(m.sufficient(*m.original.design(rows)))
    assert fit['original']==old


def test_complete_cost_block_and_reproducibility():
    rows,_=m.world('own');seen=[]
    with threadpool_limits(limits=1):
        result=m.run(rows,blocks=1,progress=seen.append)
        second=m.run(list(reversed(rows)),blocks=1)
    assert result['state']=='cost_only' and result['bootstrap_draws']==200
    assert result['permutation_draws']==20 and not result['complete_banks']
    assert seen==[dict(blocks=1,total_blocks=1,bootstraps=200,permutations=20)]
    # Floating aggregation order can differ; complete same-order native replay
    # is exact, while row reversal must preserve the estimand numerically.
    assert result['point']['adjusted_own']==pytest.approx(second['point']['adjusted_own'],abs=1e-8)


def test_missing_writer_or_nonfinite_refuses():
    rows,_=m.world('null')
    with pytest.raises(ValueError,match='twenty'):
        m.run([r for r in rows if r['writer']!='w00'],blocks=1)
    rows[0]['entropy']=np.nan
    with pytest.raises(ValueError,match='Nonfinite'):
        m.design(rows)


def test_actual_constructed_handler_and_changed_output(tmp_path):
    from runners.drive.cards import week4_conflict_inference as runner
    config=runner.configuration('constructed')
    runner.execute(tmp_path,{},config)
    assert runner.verify(tmp_path,{},config)['full_fresh_replay']
    runner.atomic(tmp_path/'SUMMARY.json',{'native_known_answers':True})
    with pytest.raises(ValueError,match='summary differs'):
        runner.verify(tmp_path,{},config)


def test_incomplete_calibration_rejected():
    from runners.drive.cards.week4_conflict_inference import calibration_check
    with pytest.raises(ValueError,match='Incomplete'):
        calibration_check(dict(state='cost_only'),{})
