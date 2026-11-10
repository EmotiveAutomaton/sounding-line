"""Bounded exact MD12 consumers; frozen source/statistic module is unchanged.

DESIGN CHECK: LESSONS 2?5, CONTROLS 6?7. Actual bootstrap draws and exact
per-person fits are checkpointed; no partial estimate can become a result.
A measured 100-of-2000 draw quantum forecasts the full execute/replay cost.
"""
from pathlib import Path
import hashlib,json,os,time
import numpy as np
from .week5_md import *
from .week5_md import _interval
from . import week5_md as original
from . import week5_md_analysis as analysis

class YieldRequested(Exception):
    def __init__(self,receipt): self.receipt=receipt

def clock_state(output,config):
    return dict(start=time.monotonic(),max_wall_seconds=float(config.get('max_wall_seconds',900)),
                max_new_draws=int(config.get('max_new_draws',2000)),yield_path=(Path(output).parent if Path(output).name=='independent-replay' else Path(output))/'YIELD_REQUEST.json')

def atomic_replace(source,target):
    for attempt in range(10):
        try:os.replace(source,target);return
        except PermissionError:
            if attempt==9:raise
            time.sleep(.02*(attempt+1))

def wants_yield(runtime):
    return runtime['yield_path'].exists() or time.monotonic()-runtime['start']>=runtime['max_wall_seconds']

def blocked_person_fit(plays,columns,penalty,*,output,runtime,**kwargs):
    output.mkdir(parents=True,exist_ok=True)
    fixed=kwargs.get('fixed_gamma')
    bind=hashlib.sha256(np.ascontiguousarray(plays).tobytes()+json.dumps({'columns':columns,'penalty':penalty,'kwargs':{k:v for k,v in kwargs.items() if k!='fixed_gamma'}},sort_keys=True).encode()+str(sha(Path(__file__))).encode()+(np.asarray(fixed).tobytes() if fixed is not None else b'')).hexdigest()
    collected=[]
    for start in range(0,len(plays),500):
        end=min(start+500,len(plays));path=output/f'block-{start:06}.npz'
        if path.exists():
            if sha(path)!=json.loads(path.with_suffix('.sha256.json').read_text('utf8'))['sha256']:raise ValueError('participant checkpoint seal mismatch')
            with np.load(path,allow_pickle=False) as saved:
                if str(saved['binding'])!=bind or int(saved['start'])!=start or int(saved['end'])!=end:raise ValueError('participant fit block mismatch')
                result={k:saved[k] for k in ['mse','beta','gamma','valid']}
        else:
            if wants_yield(runtime):raise YieldRequested({'status':'yielded','reason':'bounded MD per-person fit','completed':start,'total':len(plays)})
            local=dict(kwargs)
            if fixed is not None:local['fixed_gamma']=fixed[start:end]
            result=original.person_fit(plays[start:end],columns,penalty,**local)
            tmp=path.with_suffix('.tmp.npz');np.savez_compressed(tmp,binding=bind,start=start,end=end,**result);atomic_replace(tmp,path)
            save_json(path.with_suffix('.sha256.json'),{'sha256':sha(path)})
            save_json(output/'PROGRESS.json',{'completed':end,'total':len(plays)})
        collected.append(result)
    return {k:np.concatenate([r[k] for r in collected]) for k in ['mse','beta','gamma','valid']}

def pooled_bounded(plays: np.ndarray, out: Path, draws: int = 2000, seed: int = SEED, exploratory_n: int = 5000, runtime: dict | None = None) -> dict:
    """Primary MD1/2 fits. Actual participant bootstrap refits and reselects gamma."""
    out.mkdir(parents=True, exist_ok=True)
    runtime = runtime or clock_state(out, {})
    started_cpu = time.process_time()
    n_all = len(plays)
    rng = np.random.default_rng(seed)
    order = rng.permutation(n_all)
    n_explore = min(exploratory_n, max(0, n_all//3))
    main = plays[np.sort(order[n_explore:])]
    training_trial = np.array([np.flatnonzero(np.isfinite(p[:, 9]))[9] for p in main])
    mask = (np.arange(30)[None, :] <= training_trial[:, None]) & (main[:, :, 6] == 1)
    spreads = (main[:, :, 3] - main[:, :, 4])[mask]
    spread_mean, spread_sd = float(spreads.mean()), float(spreads.std(ddof=1))
    if spread_sd <= 0:
        raise ValueError("spread has no training variation")
    bank, objectives = [], []
    binding = hashlib.sha256(np.ascontiguousarray(plays).tobytes()).hexdigest()
    code_binding = sha(Path(__file__))
    for gamma in GAMMAS:
        x, y = rating_history(main, gamma, spread_mean, spread_sd)
        x, y, keep = center_training(x, y)
        s = stats(x, y); bank.append(s)
        objectives.append(fit_stats(s, [0, 1, 2, 3])[1])
    chosen = int(np.argmin(objectives)); gamma = float(GAMMAS[chosen]); s = bank[chosen]
    b0, _, mse0 = fit_stats(s, [0, 1, 2, 3])
    b1, _, mse1 = fit_stats(s, [0, 1, 2, 3, 4])
    b2, _, mse2 = fit_stats(s, [0, 1, 2, 3, 5, 6])
    x, y = rating_history(main, gamma, spread_mean, spread_sd); x, y, keep = center_training(x, y)
    # Residualize spread against the other MD2 regressors on training ratings only.
    nuisance = x[:, :10, [0, 1, 2, 3, 6]].reshape(-1, 5)
    spread_column = x[:, :10, 5].ravel()
    residual = spread_column - nuisance @ np.linalg.lstsq(nuisance, spread_column, rcond=1e-12)[0]
    residual_sd = float(residual.std(ddof=1))
    n = len(y); bootstrap = []
    checkpoint = out / "bootstrap.npz"
    if checkpoint.exists():
        if sha(checkpoint)!=json.loads(checkpoint.with_suffix(".sha256.json").read_text("utf8"))["sha256"]:raise ValueError("pooled checkpoint seal mismatch")
        old = np.load(checkpoint)
        if (int(old["seed"]) != seed or int(old["n"]) != n or int(old["draws"]) != draws
                or str(old["input_sha256"]) != binding or str(old["code_sha256"]) != code_binding):
            raise ValueError("bootstrap resume contract mismatch")
        bootstrap = old["values"].tolist()
        old.close()
    prior_draws = len(bootstrap)
    fit_cpu = time.process_time()
    for draw in range(len(bootstrap), draws):
        local = np.random.default_rng(np.random.SeedSequence([seed, draw, 12]))
        w = np.bincount(local.integers(0, n, n), minlength=n)
        fits = [fit_stats(sb, [0, 1, 2, 3], w) for sb in bank]
        index = int(np.argmin([f[1] for f in fits]))
        sb = bank[index]; base = fits[index]
        level = fit_stats(sb, [0, 1, 2, 3, 4], w)
        uncertainty = fit_stats(sb, [0, 1, 2, 3, 5, 6], w)
        # Residualized-unit scaling is frozen from the original training fit.
        bootstrap.append([(base[2]-level[2])/base[2], level[0][-1], uncertainty[0][4]*residual_sd])
        yielding = wants_yield(runtime) or draw+1-prior_draws >= runtime["max_new_draws"]
        if (draw+1) % 25 == 0 or draw+1 == draws or yielding:
            tmp = out / "bootstrap.tmp.npz"
            np.savez_compressed(tmp, values=np.array(bootstrap), seed=seed, n=n, draws=draws,
                                input_sha256=binding, code_sha256=code_binding)
            atomic_replace(tmp, checkpoint)
            save_json(checkpoint.with_suffix(".sha256.json"),{"sha256":sha(checkpoint)})
            save_json(out / "PROGRESS.json", {"phase": "participant_bootstrap", "completed": draw+1, "total": draws})
            save_json(out / "COST.json", {"new_draws": draw+1-prior_draws, "initialization_cpu_seconds": fit_cpu-started_cpu, "draw_cpu_seconds": time.process_time()-fit_cpu, "forecast_pooled_execute_plus_replay_cpu_seconds": 2*((fit_cpu-started_cpu)+(time.process_time()-fit_cpu)*draws/(draw+1-prior_draws)), "companions_not_included": True})
        if yielding and draw+1 < draws:
            raise YieldRequested({"status":"yielded", "reason":"bounded MD pooled checkpoint", "completed":draw+1,"total":draws})
    boot = np.asarray(bootstrap)
    residual0 = y[:, :10] - x[:, :10, :4] @ b0
    level_var = float(np.mean(np.var(x[:, :10, 4], axis=1)))
    plant_size = np.sqrt(.02 * float(np.var(residual0)) / level_var) if level_var > 0 else 0.
    controls = []
    for sign in [-1, 1]:
        yp = y + sign * plant_size * x[:, :, 4]
        ps = stats(x, yp)
        pb = fit_stats(ps, [0, 1, 2, 3]); pl = fit_stats(ps, [0, 1, 2, 3, 4])
        controls.append({"sign": sign, "added_weight": sign*plant_size, "gain": (pb[2]-pl[2])/pb[2],
                         "level_weight": float(pl[0][-1])})
    gain = (mse0-mse1)/mse0; weight_ci = _interval(boot[:, 1]); gain_ci = _interval(boot[:, 0])
    fitted_sign = 1 if b1[-1] >= 0 else -1
    sensitive = controls[(fitted_sign+1)//2]["gain"] >= .01
    outcome = "design cannot test" if not sensitive else (
        "against" if gain >= .01 and (weight_ci[0] > 0 or weight_ci[1] < 0) else
        "supports" if gain < .005 and weight_ci[0] <= 0 <= weight_ci[1] else "inconclusive")
    ev = (main[keep, :, 3]+main[keep, :, 4])/2
    rawspread = (main[keep, :, 3]-main[keep, :, 4]-spread_mean)/spread_sd
    effective_ev = b2[1]+b2[4]*rawspread+b2[5]*np.abs(ev)
    gamble = main[keep, :, 6] == 1
    mixed = gamble & (main[keep, :, 2] == 0)
    corr = float(np.corrcoef(rawspread[mixed], np.abs(ev[mixed]))[0, 1]) if mixed.sum() > 2 else None
    support = int(np.sum(mixed.sum(axis=1) >= 5))
    spread_ci = _interval(boot[:, 2])
    md2_outcome = "below floor, descriptive" if support < 10000 or corr is None or abs(corr) >= .9 else (
        "supports" if spread_ci[1] < -.01 else "against" if spread_ci[0] >= 0 else "inconclusive")
    result = {"phase": "pooled_primary_only", "first_plays": n_all, "exploratory_set_aside": n_explore,
              "main_participants": n, "zero_training_variance_excluded": int((~keep).sum()), "gamma": gamma,
              "draws": draws, "seed": seed, "MD1": {"gain": gain, "gain_interval": gain_ci,
                  "level_weight": float(b1[-1]), "weight_interval": weight_ci, "mse0": mse0, "mse1": mse1,
                  "outcome": outcome, "signed_level_plants": controls},
              "MD2": {"spread_weight_raw": float(b2[4]), "spread_weight_standardized": float(b2[4]*residual_sd),
                  "spread_interval": spread_ci, "residual_sd": residual_sd, "mse": mse2,
                  "mixed_supported_participants": support, "mixed_spread_abs_ev_correlation": corr,
                  "effective_ev_negative_share": float(np.mean(effective_ev[gamble] < 0)),
                  "certain_minus_ev": float(b2[0]-b2[1]), "outcome": md2_outcome},
              "complete_card": False, "remaining": ["per-participant ridge arm", "historical sign diagnostic", "independent replay"]}
    save_json(out / "POOLED.json", result)
    return result

def companions_bounded(plays: np.ndarray, out: Path, seed: int=SEED, exploratory_n: int=5000, runtime=None) -> dict:
    """Ridge companion and historical sign checks. This does not publish IDs."""
    order = np.random.default_rng(seed).permutation(len(plays))
    split = min(exploratory_n, max(0, len(plays) // 3))
    exploratory = plays[np.sort(order[:split])]
    main = plays[np.sort(order[split:])]
    penalties = [0.0, 0.01, 0.1, 1.0, 10.0, 100.0]
    tuning = []
    for penalty in penalties:
        model = blocked_person_fit(exploratory, [0, 1, 2, 3, 4], penalty, train=8, output=out / f'tuning-{penalty}', runtime=runtime)
        losses = []
        for gamma in np.unique(model['gamma'][model['valid']]):
            use = model['valid'] & np.isclose(model['gamma'], gamma)
            x, y = rating_history(exploratory[use], float(gamma))
            x, y, good = center_training(x, y, 8)
            pred = np.einsum('nti,ni->nt', x[:, 8:10, :5], model['beta'][use][good])
            losses.extend(np.mean((y[:, 8:10] - pred) ** 2, axis=1).tolist())
        tuning.append(float(np.mean(losses)))
    penalty = penalties[int(np.argmin(tuning))]
    base = blocked_person_fit(main, [0, 1, 2], penalty, output=out / 'arm-2', runtime=runtime)
    time_model = blocked_person_fit(main, [0, 1, 2, 3], penalty, output=out / 'arm-3', runtime=runtime)
    level = blocked_person_fit(main, [0, 1, 2, 3, 4], penalty, fixed_gamma=time_model['gamma'], output=out / 'arm-4', runtime=runtime)
    gamble = main[:, :, 6] == 1
    cutoff = np.array([np.flatnonzero(np.isfinite(p[:, 9]))[9] for p in main])
    train_trials = gamble & (np.arange(30)[None, :] <= cutoff[:, None])
    spreads = (main[:, :, 3] - main[:, :, 4])[train_trials]
    md2 = blocked_person_fit(main, [0, 1, 2, 3, 5, 6], penalty, fixed_gamma=time_model['gamma'], spread_mean=float(spreads.mean()), spread_sd=float(spreads.std(ddof=1)), output=out / 'arm-5', runtime=runtime)
    valid = base['valid'] & time_model['valid'] & level['valid']
    eligible = valid & (time_model['gamma'] <= 0.9)
    history = blocked_person_fit(plays[:18400], [0, 1, 2], 0.0, train=12, output=out / 'arm-6', runtime=runtime)
    groups = []
    for i in range(0, min(len(plays), 18400) - 199, 200):
        mask = history['valid'][i:i + 200]
        b = history['beta'][i:i + 200][mask]
        if len(b):
            groups.append(b.mean(axis=0))
    block = np.array(groups)
    record = {'ridge_penalty': penalty, 'ridge_grid': penalties, 'inner_validation_mse': tuning, 'exploratory_participants': split, 'per_person_valid': int(valid.sum()), 'gamma_above_point9_excluded': int((valid & ~eligible).sum()), 'per_person_median_level_weight': float(np.median(level['beta'][eligible, -1])), 'per_person_median_spread_weight': float(np.median(md2['beta'][eligible, 4])), 'time_gain': float(1 - np.mean(time_model['mse'][valid]) / np.mean(base['mse'][valid])), 'historical_sign_diagnostic': {'scope': 'current-source first plays; not exact deleted 2014 cohort', 'blocks': len(groups), 'positive_cr_ev_rpe_blocks': (block > 0).sum(axis=0).tolist(), 'ev_below_rpe_blocks': int((block[:, 1] < block[:, 2]).sum()), 'target_blocks': 92, 'target_positive_each': 92, 'target_ev_below_rpe': 91}, 'complete_card': False, 'remaining': ['independent replay', 'late-play level and observed-time companions']}
    save_json(out / 'COMPANIONS.json', record)
    return record


def execute(output:Path,inputs:dict,config:dict):
    output.mkdir(parents=True,exist_ok=True);runtime=clock_state(output,config);data=analysis.load_verified(inputs['task']);plays=data['first']
    if config.get('participants'):
        order=np.random.default_rng(SEED).permutation(len(plays));plays=plays[np.sort(order[:int(config['participants'])])]
    try:
        pooled=pooled_bounded(plays,output/'pooled',int(config.get('draws',2000)),runtime=runtime)
        companions=companions_bounded(plays,output/'companions',runtime=runtime)
        if wants_yield(runtime):raise YieldRequested({'status':'yielded','reason':'bounded MD before final companions'})
        extra=analysis.late_and_time(plays,pooled['gamma'])
        result={'cards':['MD1','MD2'],'pooled':pooled,'companions':companions,'late_and_time':extra,
                'complete_computation':True,'independent_replay_required':True,
                'scope':'descriptive first-play participants; sample-scoped' if len(plays)<len(data['first']) else 'descriptive first-play participants',
                'source_first_plays':len(data['first']),'analysed_first_plays':len(plays)}
        save_json(output/'RESULT.json',result);return result
    except YieldRequested as yielded:return yielded.receipt

def verify(output:Path,inputs:dict,config:dict):
    # Verification may also yield; no completion receipt is emitted until every
    # actual draw and fitted participant has independently been reconstructed.
    actual=execute(output/'independent-replay',inputs,config)
    if actual.get('status')=='yielded':return {**actual,'verified':False}
    expected=json.loads((output/'RESULT.json').read_text('utf8'))
    if actual!=expected:raise ValueError('bounded full MD result differs on independent replay')
    for original_path in sorted(output.rglob('*.npz')):
        relative=original_path.relative_to(output)
        if relative.parts[0]=='independent-replay':continue
        with np.load(original_path,allow_pickle=False) as left,np.load(output/'independent-replay'/relative,allow_pickle=False) as right:
            if set(left.files)!=set(right.files):raise ValueError('independent checkpoint keys differ')
            for key in left.files:
                equal=np.array_equal(left[key],right[key],equal_nan=True) if np.issubdtype(left[key].dtype,np.number) else np.array_equal(left[key],right[key])
                if not equal:raise ValueError('independent full checkpoint array differs')
    return {'verified':True,'all_statistics_and_draws_replayed':True}
