import json
import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week5_sp3_ic as s


def table():
    return pd.DataFrame([dict(building=f'fixture-{i:03d}',cooling=s.parent.AC if i<24 else s.parent.NV,
                              weather=10+i%24,slope=.4+.03*(i%7)) for i in range(48)])


def test_all_frame_operator_matches_expanded_rows():
    data,at,x,y=s.design(table());matrix,failed=s.operators(data,32)
    assert not failed
    eligible=np.zeros(len(data),bool);eligible[at]=True;center=np.zeros(len(data));center[at]=x[:,1]
    rng=np.random.default_rng(s.SEED)
    for draw in range(32):
        sampled=rng.integers(0,len(data),len(data));chosen=sampled[eligible[sampled]]
        fit=np.linalg.lstsq(np.column_stack([np.ones(len(chosen)),center[chosen]]),y[chosen],rcond=None)[0][1]
        assert matrix[draw]@y==pytest.approx(fit,abs=1e-12)


def test_unsupported_draws_are_retained():
    data=table();data['cooling']=s.parent.AC;data.loc[[24,47],'cooling']=s.parent.NV
    matrix,failures=s.operators(data,32)
    assert failures and matrix.shape==(32,48)
    assert all(np.all(matrix[i]==0) for i in failures)


def test_duplicate_building_refuses():
    data=table();data.loc[1,'building']=data.loc[0,'building']
    with pytest.raises(ValueError,match='One summary'):s.design(data)


def test_complete_draw_count_required(tmp_path):
    with pytest.raises(ValueError,match='Full fixed'):s.calibrate(table(),tmp_path,{'draws':1999},'constructed')


def test_small_analytic_case_is_descriptive(tmp_path):
    data=table();data.loc[30:,'cooling']=s.parent.AC
    result=s.calibrate(data,tmp_path,{},'constructed')
    assert result['status']=='below floor, descriptive'
    assert result['analytic_buildings']==6 and 'sensitivity_pass' not in result


def test_modified_checkpoint_refuses(tmp_path):
    directory=tmp_path/'worlds';directory.mkdir();path=directory/'-2-000.npz'
    np.savez(path,values=np.zeros(2000),point=0.)
    ordered,_,_,_=s.design(table())
    path.with_suffix('.sha256.json').write_text(json.dumps({'binding':s.binding_for(ordered,'constructed',2000,100),'sha256':'wrong'}))
    with pytest.raises(ValueError,match='checkpoint changed'):s.calibrate(table(),tmp_path,{},'constructed')
