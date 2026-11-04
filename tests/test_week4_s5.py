import numpy as np
import pytest
from runners.drive.cards import week4_s5 as s
from threadpoolctl import threadpool_limits

@pytest.mark.parametrize('effect',[0.,.7,-.7])
def test_null_signal_and_reversal_known_answers(effect):
    with threadpool_limits(limits=1):
        result=s.fit_arrays(*s.known_arrays(effect),bootstrap=25,permutations=20)
    assert result['estimate']==pytest.approx(effect,abs=1e-8)
    assert np.allclose(result['bootstrap'],effect,atol=1e-8)

def test_dense_gls_identity_with_nested_author_project_covariance():
    x,y,a,p=s.known_arrays()
    x=s.center_by_author(x,a);xx=np.column_stack([np.ones(len(x)),x])
    za=np.equal.outer(a,a).astype(float);zp=np.equal.outer(p,p).astype(float)
    with threadpool_limits(limits=1):
        for va,vp in [(0,0),(.2,2),(5,.01)]:
            v=np.eye(len(x))+va*za+vp*zp
            beta=np.linalg.solve(xx.T@np.linalg.solve(v,xx),xx.T@np.linalg.solve(v,y))
            assert beta[1]==pytest.approx(.7,abs=1e-10)

def row(timestamp,category,label):
    return dict(project='p',author='a',timestamp=timestamp,**{'high-level':category,'label':label,'before text':'a','after text':'ab'})

def test_high_level_not_fine_label_runs_and_break_census():
    rows=[row(0,'IMPLEMENTATION','Text Production'),row(1000,'PLANNING','Idea Generation'),
          row(2000,'PLANNING','Section Planning'),row(3000,'IMPLEMENTATION','Text Production'),
          row(1900000,'PLANNING','Idea Generation')]
    records,audit=s.extract(rows)
    assert records[0]['high_start'] and records[1]['fine_start'] and not records[1]['high_start']
    assert records[2]['high_start'] and records[3]['break_gap']
    assert audit['long_gaps']==1 and audit['missing: first released row']==1
    result,_=s.summarize(records,audit,s.CONFIG)
    assert result['state']=='design cannot test' and 'primary' not in result

def test_ambiguous_timestamp_edges_are_not_timing():
    rows=[row(0,'PLANNING','Idea Generation'),row(1000,'PLANNING','Idea Generation'),
          row(1000,'PLANNING','Idea Generation'),row(2000,'IMPLEMENTATION','Text Production')]
    records,audit=s.extract(rows)
    assert not records and audit['missing: ambiguous timestamp block']==3

def test_primary_collinearity_refuses():
    with pytest.raises(ValueError,match='not identifiable'):
        s.solve(np.ones((2,2)),np.ones(2))

def test_supported_summary_includes_mixtures_and_label_distributions():
    x,y,a,p=s.known_arrays();rows=[]
    category=np.tile(np.repeat(np.arange(3),12),8)
    for i in range(len(y)):
        rows.append(dict(author=str(a[i]),project=str(p[i]),category=['PLANNING','IMPLEMENTATION','REVISION'][category[i]],
            label=['Idea Generation','Text Production','Clarity'][category[i]],break_gap=False,high_start=True,fine_start=True,
            log_relative_gap=float(y[i]),gap_seconds=float(np.exp(y[i])),log_edit_size=float(x[i,2]+10),log_session_elapsed=float(x[i,3]+10)))
    cfg=dict(s.CONFIG,planning_starts_per_author=10,bootstrap=25,permutations=20)
    with threadpool_limits(limits=1):result,private=s.summarize(rows,{},cfg)
    assert result['primary']['estimate']==pytest.approx(.7,abs=1e-8)
    assert result['state']=='positive' and len(result['label_gap_distributions'])==3
    assert len(private['descriptive_author_mixtures'])==8
