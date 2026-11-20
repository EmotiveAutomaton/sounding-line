import numpy as np
import pytest
from scipy.special import expit
from runners.drive.cards import week6_lattice_bindings_v1 as b
from runners.drive.cards.week6_lattice_diary_v1 import InvalidFit, within

def base():
    r=np.random.default_rng(735)
    ids=np.repeat(np.arange(90),25)
    means=r.normal(size=(90,8))
    x=r.normal(size=(len(ids),8))+means[ids]
    return r,ids,x

def test_ld3_joint_fit_recovers_declared_full_table():
    r,ids,x=base();zw,_,_=within(x,ids)
    feelings={name:zw[:,j]+.5*zw[:,(j+1)%8] for j,name in enumerate(
        ('enthusiastic','relaxed','anxious','angry','sad','ashamed','insecure','proud'))}
    out=b.ld3(ids,dict(zip(b.ACTIVITY,x.T)),feelings)
    assert set(out['table'])==set(feelings)
    for j,name in enumerate(feelings):
        # Independently standardise the known linear signal, without fitted residuals.
        truth=np.zeros(8);truth[j]=1;truth[(j+1)%8]=.5
        truth/=np.sqrt(np.mean(feelings[name]**2))
        np.testing.assert_allclose(out['table'][name],truth,atol=1e-12)

def test_ld3_whole_person_weights_equal_literal_resampling():
    r,ids,x=base();y=r.normal(size=(len(ids),4))
    feelings=dict(zip(('enthusiastic','relaxed','anxious','angry'),y.T))
    counts=r.integers(0,4,90);w=counts[ids];ix=np.repeat(np.arange(len(ids)),w)
    first=b.ld3(ids,dict(zip(b.ACTIVITY,x.T)),feelings,w)
    second=b.ld3(ids[ix],dict(zip(b.ACTIVITY,x[ix].T)),{k:v[ix] for k,v in feelings.items()})
    for k in feelings:np.testing.assert_allclose(first['table'][k],second['table'][k],atol=1e-12)

def test_ld3_rejects_dropped_covariate():
    r,ids,x=base()
    with pytest.raises(InvalidFit,match='entire'):b.ld3(ids,dict(zip(b.ACTIVITY[:-1],x.T)),{})

def test_ld1_context_contrast_matches_independent_fits():
    import statsmodels.api as sm
    r,ids,x=base();ctx=r.integers(0,2,len(ids));f=x[:,0]
    fw,fm,_=within(f,ids);X=np.column_stack((np.ones(len(ids)),ctx,fw[:,0],ctx*fw[:,0],fm[:,0]))
    outcomes={name:1+r.binomial(1,expit(X@np.array([-.3,.1,.2,product,.15])))
              for name,product in (('ashamed',.35),('sad',.05))}
    out=b.ld1(ids,ctx,f,outcomes)
    reference={k:sm.Logit(y>1,X).fit(disp=0).params for k,y in outcomes.items()}
    assert out['primary']==pytest.approx(reference['ashamed'][3]-reference['sad'][3],abs=1e-7)

def test_ld1_requires_both_contexts():
    with pytest.raises(InvalidFit,match='Both contexts'):b.ld1([0,0],[1,1],[1,2],{})

def test_ld2_product_keeps_every_event_and_all_fear_items():
    import statsmodels.api as sm
    r,ids,x=base();z,means,_=within(x[:,:7],ids)
    X=np.column_stack((np.ones(len(ids)),z,z[:,1]*z[:,6],means))
    outcomes={}
    for name,tilt in (('angry',.4),('anxious',.1),('ashamed',.1),('insecure',.1)):
        coefficients=np.full(X.shape[1],.03);coefficients[0]=-.5;coefficients[8]=tilt
        outcomes[name]=1+r.binomial(1,expit(X@coefficients))
    out=b.ld2_product(ids,dict(zip(b.STATUS,x[:,:6].T)),x[:,6],outcomes)
    reference={k:sm.Logit(y>1,X).fit(disp=0).params for k,y in outcomes.items()}
    expected=reference['angry'][8]-np.mean([reference[k][8] for k in b.FEAR_LIKE])
    assert out['primary']==pytest.approx(expected,abs=1e-7)
    assert out['coefficients']['angry'].shape==(16,)

def test_role_support_does_not_count_repeated_rows_as_people():
    ids=np.r_[np.repeat(np.arange(39),3),np.repeat(np.arange(40,80),3)]
    role=np.r_[np.repeat(2,117),np.repeat(1,120)]
    out=b.role_support(ids,np.ones(len(ids)),role,np.repeat(2,len(ids)),np.where(role==2,5,2))
    assert out['strata']['below']==dict(criticised_prompts=117,people=39)
    assert not out['support_passes'] and not out['inferentially_eligible']

def test_role_floor_and_coding_both_gate():
    ids=np.tile(np.repeat(np.arange(40),2),2);role=np.repeat([2,1],80)
    out=b.role_support(ids,np.ones(160),role,np.full(160,2),np.where(role==2,2,5))
    assert out['support_passes'] and not out['coding_passes']
    out=b.role_support(ids,np.ones(160),role,np.ones(160),np.where(role==2,5,2))
    assert not out['support_passes']

def test_nan_refused_before_model():
    with pytest.raises(InvalidFit,match='finite'):b.form_l([1,1],[1,float('nan')],{})

def test_prospective_register_and_canonical_event_binding():
    import json
    from pathlib import Path
    from runners.drive.cards.es_core_v1 import EVENTS
    from runners.drive.cards.week6_lattice_v1 import validate_register
    rows=json.loads((Path(__file__).resolve().parents[1]/'docs/design/stage-15/week6/LATTICE_PREDICTIONS_20261119.json').read_text())
    validate_register(rows)
    assert len({r['source_group'] for r in rows})==14
    assert rows[36]['direction']==rows[40]['direction']==1
    assert rows[42]['direction']==-1
    assert b.STATUS==EVENTS
