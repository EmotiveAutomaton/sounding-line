import numpy as np
import pytest
from runners.theory_days import chess_model as model,chess_sensitivity as s

def test_full_dose_recomputation_parity():
    assert all(r['full_recomputation_parity'] for r in s.validate()['exact_shift_parity'])

def test_finite_count_uncertainty_and_rejection():
    assert s.wilson(0,100)['interval'][1]>0
    assert s.wilson(100,100)['interval'][0]<1
    assert s.wilson(50,100)['interval'][0]<.5<s.wilson(50,100)['interval'][1]
    with pytest.raises(ValueError):s.wilson(2,1)

def test_real_handler_native_replay(tmp_path):
    out=tmp_path/'absent';s.execute(out,{},dict(constructed=True))
    assert s.verify(out,{},dict(constructed=True))['complete_recalculation']

def test_one_sign_per_whole_game():
    baseline=np.array([10.,20.,30.,40.]);residual=np.array([1.,2.,3.,4.])
    inverse=np.array([0,0,1,1]);signs=np.array([-1.,1.])
    assert np.array_equal(s.wild_outcome(baseline,residual,inverse,signs),[9,18,33,44])
    with pytest.raises(ValueError):s.wild_outcome(baseline,residual,inverse,np.array([0.,1.]))

def test_grid_counts_and_invalid_world_refusal():
    values,groups=model.constructed(0)
    result=s.calculate(values,groups,worlds=3,draws=32)
    assert result['status']=='complete' and len(result['records'])==3 and len(result['rows'])==5
    for row in result['rows']:
        assert sum(row['counts']['verdict_'+v]['successes'] for v in ('supports','against','inconclusive'))==3
        assert row['counts']['coverage']['total']==3
    values[:,3]=0
    failed=s.calculate(values,groups,worlds=2,draws=32)
    assert failed['status']=='invalid calibration' and failed['invalid_worlds']==2 and len(failed['records'])==2
