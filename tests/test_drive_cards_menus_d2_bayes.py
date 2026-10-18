import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from scipy.optimize import check_grad
from scipy.integrate import quad
from scipy.special import expit, logsumexp

from runners.drive.cards import menus_d2_bayes as d
from runners.drive.cards import menus_d2_bayes_stats as s
from runners.drive.cards.menus_io import read,write,sha256,input_hashes
from tests.test_drive_cards_menus_d2 import fixture as original_fixture


def binary(writers=4,menus=40,opposed=False):
    matrices=[];truths=[];names=[]
    for w in range(writers):
        for i in range(menus):
            matrices.append(np.array([[-.5],[.5]]));names.append(str(w))
            truths.append((w%2 if i%10 else 1-w%2) if opposed else i%2)
    return s.pack(matrices,truths,names,[0])


def evidence_grid(data,config):
    return [[s.laplace(data,float(tau),config) for tau in np.r_[0,s.quadrature(config,n)[0]]]
            for n in (config['quadrature_coarse'],config['quadrature_fine'])]


def test_gradient_hessian_and_exact_gaussian_prior_integral():
    data=binary(3,8);theta=np.array([.2,-.1,.3,.7]);tau=.7
    assert check_grad(lambda v:s.objective(v,data,tau,2.)[0],lambda v:s.objective(v,data,tau,2.)[1],theta)<1e-6
    a,bs,cs=s.blocks(theta,data,tau,2.);hessian=np.zeros((4,4));hessian[:1,:1]=a
    for w,(b,c) in enumerate(zip(bs,cs)):
        hessian[1+w:2+w,1+w:2+w]=b;hessian[:1,1+w:2+w]=c;hessian[1+w:2+w,:1]=c.T
    for j in range(4):
        step=np.eye(4)[j]*1e-5
        derivative=(s.objective(theta+step,data,tau,2.)[1]-s.objective(theta-step,data,tau,2.)[1])/2e-5
        assert np.allclose(derivative,hessian[:,j],atol=1e-8)
    assert s.schur(a,bs,cs)[2]==pytest.approx(np.linalg.slogdet(hessian)[1])
    zero=binary();zero['x'][:]=0;zero['z'][:]=0
    config=d.CONFIG|dict(quadrature_coarse=12,quadrature_fine=24)
    grids=evidence_grid(zero,config);result=s.grid_summary(*grids,config)
    assert result['valid'] and result['primary']['spike_posterior']==pytest.approx(.5,abs=1e-10)
    assert result['primary']['ci95'][0]==0
    for grid in grids:
        assert np.allclose([r['log_evidence'] for r in grid],-160*math.log(2),atol=1e-12)


def exact_evidence(tau,counts,nodes=80):
    """Independent deterministic Gaussian quadrature, no fitted modes/Hessian."""
    grid,weights=np.polynomial.hermite.hermgauss(nodes)
    weights=weights/math.sqrt(math.pi)
    def integrand(mu):
        total=math.exp(-mu*mu/8)/math.sqrt(8*math.pi)
        for yes,no in counts:
            coefficients=mu+math.sqrt(2)*tau*grid
            total*=float((expit(coefficients)**yes*expit(-coefficients)**no)@weights)
        return total
    integral,error=quad(integrand,-20,20,epsabs=1e-22,epsrel=1e-10,limit=200)
    assert error<1e-8*integral
    return float(math.log(integral))


def test_laplace_matches_independent_low_dimensional_quadrature():
    # Modest information and two writers: quadrature covers the population
    # coefficient and each writer deviation independently, unlike Laplace.
    counts=[(9,11),(12,8)];matrices=[];truths=[];names=[]
    for w,(yes,no) in enumerate(counts):
        matrices += [np.array([[-.5],[.5]])]*(yes+no)
        truths += [1]*yes+[0]*no;names += [str(w)]*(yes+no)
    data=s.pack(matrices,truths,names,[0])
    exact=[];approx=[]
    for tau in (0.,.3,.7,1.2):
        value=s.laplace(data,tau,d.CONFIG)['log_evidence'];reference=exact_evidence(tau,counts)
        assert abs(reference-exact_evidence(tau,counts,120))<1e-6
        assert abs(value-reference)<.06
        exact.append(reference);approx.append(value)
    # Bayes factors, which drive spike odds, agree more tightly than absolute evidence.
    assert np.max(np.abs((np.array(exact)-exact[0])-(np.array(approx)-approx[0])))<.04


def test_known_null_and_opposed_writers_and_grid_tail_failures():
    config=d.CONFIG|dict(quadrature_coarse=16,quadrature_fine=32)
    null=s.grid_summary(*evidence_grid(binary(8,40),config),config)
    plant=s.grid_summary(*evidence_grid(binary(8,40,True),config),config)
    assert null['primary']['ci95'][0]==0 and null['valid']
    assert plant['primary']['ci95'][0]>0 and plant['valid']
    tail=s.grid_summary(*evidence_grid(binary(8,40,True),config),config|dict(tail_start=.01,maximum_tail_mass=.005))
    assert not tail['valid'] and not tail['stability']['tail_ok']
    bad=d.CONFIG|dict(maxiter=1,gradient_tolerance=1e-30)
    with pytest.raises(ValueError,match='uncertified'):s.laplace(binary(3,9,True),1.,bad)


def test_twenty_world_band_is_derived_and_power_gate_can_fail():
    quiet=dict(valid=True,primary=dict(ci95=[0.,.4]));positive=dict(valid=True,primary=dict(ci95=[.3,1.]))
    gate=s.calibration([positive]*3+[quiet]*17,[positive]*4+[quiet],d.CONFIG)
    assert gate['null_reject_at']==4 and gate['null_band_tail_probability']==pytest.approx(.015901526,rel=1e-6)
    assert gate['valid']
    assert not s.calibration([positive]*4+[quiet]*16,[positive]*5,d.CONFIG)['valid']
    assert not s.calibration([quiet]*20,[positive]*3+[quiet]*2,d.CONFIG)['valid']
    assert gate['null_rate_ci95'][1]>.3


def fixture(tmp_path):
    inputs,_=original_fixture(tmp_path);root=Path(inputs['sessions']).parent
    write(root/'D2_SUMMARY.json',dict(state='marginal',primary=dict(effect=.1,ci95=[-.1,.2]),
        uniform_control=dict(state='positive'),input_hashes=input_hashes(inputs)))
    write(root/'D2_COMPLETE.json',dict(status='COMPLETE',outputs={'D2_SUMMARY.json':sha256(root/'D2_SUMMARY.json')}))
    write(root/'V4_SUMMARY.json',dict(labels={'taste':'blind','habit':'blind'}))
    write(root/'V4_COMPLETE.json',dict(status='COMPLETE',outputs={'V4_SUMMARY.json':sha256(root/'V4_SUMMARY.json')}))
    inputs.update({k:str(root/v) for k,v in dict(d2_summary='D2_SUMMARY.json',d2_complete='D2_COMPLETE.json',
                  v4_summary='V4_SUMMARY.json',v4_complete='V4_COMPLETE.json').items()})
    config=d.CONFIG|dict(quadrature_coarse=6,quadrature_fine=12,null_worlds=2,planted_worlds=1)
    return inputs,config


def test_actual_end_to_end_resume_fresh_primary_and_bindings(tmp_path):
    inputs,config=fixture(tmp_path);out=tmp_path/'output';out.mkdir()
    write(out/'YIELD_REQUEST.json',dict(reason='fixture'))
    assert d.execute(out,inputs,config)['status']=='yielded' and not (out/'SUMMARY.json').exists()
    (out/'YIELD_REQUEST.json').unlink()
    result=d.execute(out,inputs,config)
    assert result['context']['uniform_control']['state']=='positive'
    assert result['observed_computed']==result['calibration']['valid']
    before={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    assert d.execute(out,inputs,config)==result
    assert before=={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(out),inputs=inputs,config=config))
    code='import json,sys;from runners.drive.cards.menus_d2_bayes import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["source_design_replayed"]'
    env=os.environ.copy();env['PYTHONHASHSEED']='813'
    subprocess.run([sys.executable,'-B','-c',code,str(request)],check=True,timeout=30,env=env)
    path=next((out/'fits').rglob('*.json'));path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):d.verify(out,inputs,config)


def test_wrong_parent_gate_and_source_refusal(tmp_path):
    inputs,config=fixture(tmp_path);path=Path(inputs['d2_summary']);value=read(path);value['state']='null'
    path.write_text(json.dumps(value),encoding='utf8')
    complete=Path(inputs['d2_complete']);receipt=read(complete);receipt['outputs']['D2_SUMMARY.json']=sha256(path)
    complete.write_text(json.dumps(receipt),encoding='utf8')
    with pytest.raises(ValueError,match='gate closed'):d.authenticate(inputs)
