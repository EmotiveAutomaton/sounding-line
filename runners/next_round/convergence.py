"""T0b numerical successor; saved data only, no provider or GPU calls.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-3 read 2026-10-15.
NULL: constant evidence cannot identify a prior; unchanged solutions agree.
ALTERNATIVE: known interior/boundary optima pass the independent gap certificate.
Invalid inputs, changed pins, replay disagreement or failed certificates refuse.
Full successor contrasts preserve old folds, estimands and invalid penalties.
"""
import os
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'
import argparse
import sys
import threading
import time
import traceback
import numpy as np
from scipy.optimize import minimize
from runners.stage14.common import REPO, read, freeze, atomic, pins, check_pins, filehash, limits, now
from runners.stage9.process_identity import native_identity
from .queue import require_resources, resource_snapshot
from .statistics import simplex, em_shift, fit_calibrator, calibrate, stack_weight, losses

ROOT = REPO / 'results/phase_2_4_stage_15/raw/t0b-convergence-v1'
OLD = REPO / 'results/phase_2_4_stage_15/raw/phase0-v1/T0b'
TOL = 1e-7


def shift_terms(p, source):
    p = simplex(p)
    source = np.asarray(source, float)
    if not len(p) or source.shape != (4,) or not np.isfinite(source).all() or (source <= 0).any() or not np.isclose(source.sum(), 1):
        raise ValueError('invalid shift support/source')
    return p / source


def certificate(ratio, prior):
    prior = np.asarray(prior, float)
    if prior.shape != (4,) or not np.isfinite(prior).all() or (prior < -1e-12).any() or abs(prior.sum()-1) > 1e-10:
        raise ValueError('invalid optimized prior')
    den = ratio @ prior
    if (den <= 0).any():
        raise ValueError('nonpositive mixture')
    q = ratio * prior / den[:, None]
    gradient = (ratio / den[:, None]).mean(0)
    return q, dict(objective=float(-np.log(den).mean()),
        gap=float(max(0., gradient.max()-gradient @ prior)),
        fixed_point_residual=float(np.max(abs(q.mean(0)-prior))),
        prior=prior.tolist(), gradient=gradient.tolist(),
        ratio_rank=int(np.linalg.matrix_rank(ratio)))


def optimized_shift(p, source, old_prior=None):
    ratio = shift_terms(p, source)
    def obj(x):
        den = ratio @ x
        if (den <= 0).any():
            return 1e100, np.zeros(4)
        return -np.log(den).mean(), -(ratio/den[:, None]).mean(0)
    starts = [np.asarray(source, float), np.full(4, .25), *np.eye(4)]
    attempts = []
    best = None
    for start in starts:
        result = minimize(obj, start, jac=True, method='SLSQP', bounds=[(0.,1.)]*4,
            constraints=[dict(type='eq', fun=lambda x: x.sum()-1., jac=lambda x: np.ones(4))],
            options=dict(maxiter=2000, ftol=1e-13))
        x = np.maximum(result.x, 0.); x /= x.sum()
        q, cert = certificate(ratio, x)
        attempts.append(dict(success=bool(result.success), status=int(result.status),
                             message=str(result.message), iterations=int(result.nit), **cert))
        if best is None or cert['objective'] < best[1]['objective']:
            best = q, cert
        if cert['gap'] <= TOL and cert['fixed_point_residual'] <= TOL:
            break
    q, cert = best
    old = certificate(ratio, old_prior)[1] if old_prior is not None else None
    ok = cert['gap'] <= TOL and cert['fixed_point_residual'] <= TOL
    ok = ok and (old is None or cert['objective'] <= old['objective'] + 1e-10)
    cert.update(attempts=attempts, old=old, certified=bool(ok))
    if not ok:
        raise ValueError('independent shift certificate failed: '+repr(cert))
    return q, cert


def close(a, b, name, atol=1e-10):
    if not np.allclose(a, b, rtol=1e-10, atol=atol):
        raise ValueError('original replay mismatch: '+name)


def solve_fold(p, base, y, groups, valid, original):
    heldout = original['heldout_writer']; test = groups == heldout; train = ~test
    old_inner = base.copy(); new_inner = base.copy(); records = []
    if original['outer_fit_writers'] != sorted(set(groups[train])):
        raise ValueError('outer roster changed')
    def solve(fitmask, target, receipt):
        fit = fit_calibrator(p[fitmask], y[fitmask], groups[fitmask], False)
        close([fit['scale'], *fit['bias']], [receipt['calibrator']['scale'], *receipt['calibrator']['bias']], 'temperature')
        source = simplex(p[fitmask]).mean(0)
        oq, old_em = em_shift(p[target], source)
        close(old_em['prior'], receipt['em']['prior'], 'old EM prior')
        if any(old_em[k] != receipt['em'][k] for k in ('iterations','converged')):
            raise ValueError('old EM termination changed')
        nq, cert = optimized_shift(p[target], source, old_em['prior'])
        return calibrate(oq, fit), calibrate(nq, fit), dict(source_prior=source.tolist(),
            calibrator=fit, old_em=old_em, certificate=cert,
            max_adjusted_probability_change=float(np.max(abs(oq-nq))))
    expected = sorted(set(groups[train]))
    if [r['validation_writer'] for r in original['audit']] != expected:
        raise ValueError('inner roster changed')
    for receipt in original['audit']:
        g = receipt['validation_writer']; validation = train & (groups == g)
        fitmask = train & (groups != g) & valid
        if receipt['fit_writers'] != sorted(set(groups[fitmask])):
            raise ValueError('inner fit roster changed')
        old_inner[validation], new_inner[validation], cert = solve(fitmask, validation, receipt)
        old_inner[validation & ~valid] = base[validation & ~valid]
        new_inner[validation & ~valid] = base[validation & ~valid]
        records.append(dict(validation_writer=g, fit_writers=receipt['fit_writers'], **cert))
    ow = stack_weight(base[train], old_inner[train], y[train], groups[train])
    nw = stack_weight(base[train], new_inner[train], y[train], groups[train])
    close(ow, original['weight'], 'original stack weight')
    oc, nc, final = solve(train & valid, test, original['final'])
    old_candidate = oc.copy(); new_candidate = nc.copy()
    old_candidate[~valid[test]] = base[test][~valid[test]]
    new_candidate[~valid[test]] = base[test][~valid[test]]
    return dict(old_corrected=oc, corrected=nc, old_stacked=(1-ow)*base[test]+ow*old_candidate,
        stacked=(1-nw)*base[test]+nw*new_candidate, old_weight=ow, weight=nw, audit=records, final=final,
        heldout_writer=heldout, outer_fit_writers=original['outer_fit_writers'])


def comparisons(rows, saved_p, base, corrected, stacked, y, valid):
    from runners.stage14_midweek.analyze_modal import paired
    cb, cl = losses(corrected, y, valid); sb, sl = losses(stacked, y); bb, bl = losses(base, y)
    out = dict(stack_minus_mix_gain=paired(rows,bb-sb), corrected_minus_mix_gain=paired(rows,bb-cb),
        stack_log_loss_gain=paired(rows,bl-sl), corrected_system_log_loss_gain=paired(rows,bl-cl))
    for baseline in ('B-pop','B-writer','B-last','P04-effort-features','P04-E','P04-E-shuffle'):
        b = np.array([saved_p[r['key']][baseline]['scores']['half_brier'] for r in rows])
        out['stack_gain_over_'+baseline] = paired(rows,b-sb)
    c = out['stack_minus_mix_gain']
    out.update(delta_screen=bool(c['interval'][0]>.01 and c['crossed_interval'][0]>.01), invalid_retained=int((~valid).sum()))
    preds = [dict(key=r['key'], writer=r['writer'], prompt=r['prompt'], raw_valid=bool(valid[i]),
        corrected=corrected[i].tolist(), stacked=stacked[i].tolist(), corrected_half_brier=float(cb[i]),
        stacked_half_brier=float(sb[i]), corrected_system_log_loss=float(cl[i]), stacked_log_loss=float(sl[i]))
        for i,r in enumerate(rows)]
    return preds, out


def analyze(folder, guard):
    from .phase0 import saved, verify_manifest
    from runners.stage14_midweek.analyze_modal import paired
    verify_manifest(OLD)
    original_fits=read(OLD/'FITS.json'); original_p=read(OLD/'PREDICTIONS.json')
    original_s=read(OLD/'SUMMARY.json')
    rows,saved_p,y=saved(); groups=np.array([r['writer'] for r in rows])
    base=np.array([saved_p[r['key']]['B-mixlogit']['probabilities'] for r in rows])
    all_p={}; all_f={}; all_s={}; numerical={}
    for arm in ('R27.H0','R27.H1','R27.H2','R27.H3'):
        name=arm+'.EM_TS'; prior=original_p[name]
        if [r['key'] for r in prior] != [r['key'] for r in rows]: raise ValueError('target order changed')
        valid=np.array([saved_p[r['key']][arm]['valid'] for r in rows])
        p=simplex([saved_p[r['key']][arm]['probabilities'] if ok else [.25]*4 for r,ok in zip(rows,valid)])
        corrected=np.zeros_like(base); stacked=np.zeros_like(base); audits=[]
        for index,old in enumerate(original_fits[name]):
            guard(dict(arm=arm,outer_fold=index,total=31))
            fold=solve_fold(p,simplex(base),y,groups,valid,old); m=groups==old['heldout_writer']
            close(fold.pop('old_corrected'), [r['corrected'] for r in prior if r['writer']==old['heldout_writer']], 'corrected')
            close(fold.pop('old_stacked'), [r['stacked'] for r in prior if r['writer']==old['heldout_writer']], 'stacked')
            corrected[m]=fold.pop('corrected'); stacked[m]=fold.pop('stacked'); audits.append(fold)
        all_p[name],all_s[name]=comparisons(rows,saved_p,base,corrected,stacked,y,valid)
        all_f[name]=audits
        certs=[r for f in audits for r in [*f['audit'],f['final']]]
        numerical[name]=dict(fits=len(certs),old_capped=sum(not c['old_em']['converged'] for c in certs),
            maximum_gap=max(c['certificate']['gap'] for c in certs),
            maximum_fixed_point_residual=max(c['certificate']['fixed_point_residual'] for c in certs),
            max_corrected_probability_change=float(np.max(abs(corrected-np.array([r['corrected'] for r in prior])))),
            max_stacked_probability_change=float(np.max(abs(stacked-np.array([r['stacked'] for r in prior])))))
        numerical[name]['material_probability_change']=numerical[name]['max_corrected_probability_change']>1e-6 or numerical[name]['max_stacked_probability_change']>1e-6
        bcts=arm+'.BCTS'; all_p[bcts]=original_p[bcts]; all_f[bcts]=original_fits[bcts]
        all_s[bcts]=original_s['comparisons'][bcts]
    for mode in ('EM_TS','BCTS'):
        own=np.array([r['stacked_half_brier'] for r in all_p['R27.H2.'+mode]])
        donor=np.array([r['stacked_half_brier'] for r in all_p['R27.H3.'+mode]])
        all_s['own_over_donor_'+mode]=paired(rows,donor-own)
    freeze(folder/'PREDICTIONS.json',all_p); freeze(folder/'FITS.json',all_f)
    freeze(folder/'NUMERICAL.json',numerical)
    freeze(folder/'SUMMARY.json',dict(comparisons=all_s,numerical=numerical,
        engine_admission=False,limits=original_s['limits'],original_summary_sha256=filehash(OLD/'SUMMARY.json'),
        original_replay_verified=True,provider_calls=0))


def prepare():
    from .phase0 import BASE, verify_manifest
    limits(); require_resources(resource_snapshot())
    for path in (OLD,BASE/'modal-analysis-v2',BASE/'baselines-v1'): verify_manifest(path)
    if (ROOT/'PLAN.json').exists(): raise ValueError('already prepared')
    paths=[REPO/p for p in ('runners/next_round/convergence.py','runners/next_round/statistics.py',
        'runners/next_round/phase0.py','runners/next_round/queue.py','runners/stage14/common.py',
        'runners/stage9/process_identity.py','runners/stage14_midweek/analyze_modal.py',
        'runners/stage14_midweek/data.py','runners/stage14_midweek/baselines.py','runners/stage14_midweek/protocol.py',
        'docs/design/stage-15/T0B_CONVERGENCE.md','tests/test_next_round_convergence.py')]
    for folder in (OLD,BASE/'modal-analysis-v2',BASE/'baselines-v1',BASE/'data-v2'):
        paths.extend(p for p in folder.glob('*.json') if p.name!='PROGRESS.json')
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(paths),max_wall_seconds=7200,provider_calls=0,
        engine_admission=False,protocol='T0B_CONVERGENCE.md',versions=dict(numpy=np.__version__,
            scipy=__import__('scipy').__version__)))
    print('Convergence plan frozen; no forecasts scored.')


def run():
    limits(); plan=read(ROOT/'PLAN.json'); check_pins(plan['pins']); require_resources(resource_snapshot())
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f: f.write(now()+'\n')
    owner=dict(at=now(),native=native_identity(),argv=sys.argv,plan_sha256=filehash(ROOT/'PLAN.json'))
    freeze(ROOT/'OWNER.json',owner)
    # Launch handoff must register this exact native identity before computation.
    start=time.time(); stop=threading.Event()
    def hard_limit():
        if stop.wait(plan['max_wall_seconds']): return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='hard finite CPU deadline'))
        os._exit(124)
    threading.Thread(target=hard_limit,daemon=True).start()
    def guard(progress):
        snap=resource_snapshot(); require_resources(snap)
        atomic(ROOT/'PROGRESS.json',dict(at=now(),progress=progress,resources=snap))
    try:
        # Bounded launch synchronization, never an agent polling loop.
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-start>60: raise TimeoutError('native monitor was not registered')
            time.sleep(.25)
        ready=read(ROOT/'MONITOR_READY.json')
        if ready['owner_sha256']!=filehash(ROOT/'OWNER.json'): raise ValueError('monitor owner mismatch')
        analyze(ROOT,guard); check_pins(plan['pins'])
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),wall_seconds=time.time()-start,
            outputs={n:filehash(ROOT/n) for n in ('PREDICTIONS.json','FITS.json','NUMERICAL.json','SUMMARY.json')},
            plan_sha256=filehash(ROOT/'PLAN.json'),engine_admission=False,provider_calls=0,write_through_required=True))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),type=type(exc).__name__,error=str(exc),
            traceback=traceback.format_exc(),plan_sha256=filehash(ROOT/'PLAN.json')))
        raise
    finally: stop.set()


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['prepare','run'])
    args=parser.parse_args(); prepare() if args.action=='prepare' else run()
