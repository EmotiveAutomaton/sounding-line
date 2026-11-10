"""Week 5 MD1–MD3: Rutledge task source projection and numerical consumers.

DESIGN CHECK: LESSONS 2–5; CONTROLS 6–7. The initial rating precedes trial 1;
no held-out rating enters a training mean, scale, ridge choice or forgetting factor.
Null and both signed level plants exercise the actual pooled prediction function.
Missing first plays, zero training variance and failed finite/rank checks are
counted, never converted into null effects. Human outcomes require owner admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

for _key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "2"

import numpy as np
from scipy.io import loadmat
from scipy.special import expit

SEED = 20261107
GAMMAS = np.round(np.arange(.05, .901, .05), 2)
MAT_SHA = "b653513277ea27e89daee94806cae012ea7cfcb34de2383b1b80c7b01476ac4e"
ZIP_SHA = "456859176aece7ac40dc2303aec210490a90bb5d395f713ddf75ffb91fb82168"
HEADER = ["nTrial", "riskySide", "certainValue", "winValue", "loseValue", "empty", "choseRisky", "outcome", "choiceRT", "happiness", "startValue", "happinessRT", "empty", "spinDuration", "spinAngle"]


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for attempt in range(10):
        try:
            os.replace(tmp, path)
            break
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(.02*(attempt+1))


def project_subject(subject: dict) -> tuple[list[np.ndarray], np.ndarray, np.ndarray]:
    """Read only task fields, never demographic or clinical data."""
    if list(subject["dataHdr"]) != HEADER:
        raise ValueError("task column schema differs from published guide")
    plays = subject["data"]
    if isinstance(plays, np.ndarray) and plays.shape == (30, 15):
        plays = [plays]
    else:
        plays = list(plays)
    counters = np.atleast_1d(subject["timesPlayed"]).astype(int)
    days = np.atleast_1d(subject["dayNumber"]).astype(float)
    tod = np.atleast_1d(subject["timeOfDay"]).astype(float)
    if not (len(plays) == len(counters) == len(days) == len(tod) == int(subject["nPlays"])):
        raise ValueError("play metadata cardinality mismatch")
    if len(set(counters.tolist())) != len(counters) or np.any(counters < 1):
        raise ValueError("invalid play counters")
    for data in plays:
        validate_play(np.asarray(data, dtype=float))
    # Counter order identifies attempted play number; calendar coordinates break no ties.
    order = np.argsort(counters, kind="stable")
    return [np.asarray(plays[i], dtype=float) for i in order], counters[order], (days + tod)[order]


def validate_play(data: np.ndarray) -> None:
    if data.shape != (30, 15) or not np.array_equal(data[:, 0], np.arange(1, 31)):
        raise ValueError("expected thirty ordered trials")
    if not np.all(np.isfinite(data[:, [2, 3, 4, 6, 7]])) or not np.isin(data[:, 6], [0, 1]).all():
        raise ValueError("invalid task quantities")
    ratings = np.flatnonzero(np.isfinite(data[:, 9]))
    if len(ratings) != 12 or ratings[0] != 0 or ratings[-1] != 29:
        raise ValueError("rating support differs from twelve-rating published task")
    if np.any((data[ratings, 9] < 0) | (data[ratings, 9] > 100)):
        raise ValueError("rating outside scale")
    safe = data[:, 6] == 0
    if not np.allclose(data[safe, 7], data[safe, 2]):
        raise ValueError("safe outcome disagrees with certain option")
    if not np.all((data[~safe, 7] == data[~safe, 3]) | (data[~safe, 7] == data[~safe, 4])):
        raise ValueError("gamble outcome is not an offered endpoint")


def prepare(source: Path, out: Path) -> dict:
    archive = source / "Rutledge_risk_and_happiness_task_2023.zip"
    if sha(archive) != ZIP_SHA:
        raise ValueError("Rutledge archive pin mismatch")
    mat = source / "Rutledge_GBE_risk_data_TOD.mat"
    if sha(mat) != MAT_SHA:
        raise ValueError("Rutledge extracted member pin mismatch")
    subjects = loadmat(mat, variable_names=["subjData"], simplify_cells=True)["subjData"]
    first, all_plays, person, counter, day, missing = [], [], [], [], [], 0
    first_person = []
    for ordinal, subject in enumerate(subjects):
        plays, counters, days = project_subject(subject)
        for play, c, d in zip(plays, counters, days):
            all_plays.append(play); person.append(ordinal); counter.append(c); day.append(d)
            if c == 1:
                first.append(play); first_person.append(ordinal)
        missing += int(1 not in counters)
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "task.npz", first=np.asarray(first), first_person=np.array(first_person),
                        plays=np.asarray(all_plays), person=np.array(person), counter=np.array(counter), day=np.array(day))
    record = {"kind": "source_projection", "participants": len(subjects), "plays": len(all_plays),
              "first_plays": len(first), "missing_actual_first_play": missing,
              "archive_sha256": ZIP_SHA, "mat_sha256": sha(mat), "task_sha256": sha(out / "task.npz"),
              "identifier_policy": "No source id, demographic or clinical field retained; private ordinal cluster only.",
              "time_policy": "Trial index primary; elapsed components are not complete wall-clock task time.",
              "scientific_result": False}
    save_json(out / "SOURCE.json", record)
    return record


def verify_projection(source: Path, out: Path) -> dict:
    """Independent direct projection comparison against every retained task value."""
    if sha(source / "Rutledge_risk_and_happiness_task_2023.zip") != ZIP_SHA:
        raise ValueError("archive mismatch in independent verification")
    mat = source / "Rutledge_GBE_risk_data_TOD.mat"
    if sha(mat) != MAT_SHA:
        raise ValueError("MAT member mismatch in independent verification")
    record = json.loads((out / "SOURCE.json").read_text("utf8"))
    if sha(out / "task.npz") != record["task_sha256"]:
        raise ValueError("projection byte binding mismatch")
    subjects = loadmat(mat, variable_names=["subjData"], struct_as_record=False, squeeze_me=True)["subjData"]
    checked = 0; first_checked = 0
    with np.load(out / "task.npz", allow_pickle=False) as bundle:
        saved = {key: bundle[key] for key in bundle.files}
        for ordinal, subject in enumerate(subjects):
            raw = subject.data
            plays = [raw] if getattr(raw, "shape", None) == (30, 15) else list(raw)
            counters = np.atleast_1d(subject.timesPlayed)
            days = np.atleast_1d(subject.dayNumber) + np.atleast_1d(subject.timeOfDay)
            for index in sorted(range(len(counters)), key=lambda i: counters[i]):
                # This verifier deliberately bypasses project_subject/rating_history.
                if not np.array_equal(saved["plays"][checked], plays[index], equal_nan=True):
                    raise ValueError("task projection numerical mismatch")
                if (saved["person"][checked] != ordinal or saved["counter"][checked] != counters[index]
                        or saved["day"][checked] != days[index]):
                    raise ValueError("play metadata projection mismatch")
                if counters[index] == 1:
                    if (saved["first_person"][first_checked] != ordinal or
                            not np.array_equal(saved["first"][first_checked], plays[index], equal_nan=True)):
                        raise ValueError("actual first-play projection mismatch")
                    first_checked += 1
                checked += 1
        if checked != len(saved["plays"]) or first_checked != len(saved["first"]):
            raise ValueError("extra rows in saved projection")
    result = {"verified": True, "plays_checked": checked, "first_plays_checked": first_checked,
              "task_sha256": record["task_sha256"], "all_numeric_values": True}
    save_json(out / "VERIFIED.json", result)
    return result


def execute(output: Path, inputs: dict, config: dict) -> dict:
    phase = config.get("phase", "prepare")
    if phase == "fixture":
        result = fixture(); save_json(output / "FIXTURE.json", result); return result
    if phase == "prepare":
        return prepare(Path(inputs.get("source", "corpora/store/external/rutledge_gbe")), output)
    raise ValueError("phase not yet admitted as a whole scientific card")


def verify(output: Path, inputs: dict, config: dict) -> dict:
    if config.get("phase", "prepare") == "prepare":
        return verify_projection(Path(inputs.get("source", "corpora/store/external/rutledge_gbe")), output)
    if config.get("phase") == "fixture":
        expected = json.loads((output / "FIXTURE.json").read_text("utf8"))
        if fixture() != expected:
            raise ValueError("fixture replay mismatch")
        return {"verified": True, "fixture_replayed": True}
    raise ValueError("unknown verification phase")


def rating_history(plays: np.ndarray, gamma: float, spread_mean: float = 0., spread_sd: float = 1.) -> tuple[np.ndarray, np.ndarray]:
    """Return N×12×7 features [CR,EV,RPE,trial,level,EVspread,EVabs]."""
    n = len(plays)
    gamble = plays[:, :, 6]
    ev = (plays[:, :, 3] + plays[:, :, 4]) / 2
    spread = (plays[:, :, 3] - plays[:, :, 4] - spread_mean) / spread_sd
    signals = np.stack([plays[:, :, 2] * (1-gamble), ev * gamble,
                        (plays[:, :, 7] - ev) * gamble, ev * spread * gamble,
                        ev * np.abs(ev) * gamble], axis=-1)
    states = np.zeros((n, 31, 5))
    for t in range(30):
        states[:, t+1] = gamma * states[:, t] + signals[:, t]
    level = np.concatenate([np.zeros((n, 1)), np.cumsum(plays[:, :, 7], axis=1)], axis=1)
    indices = np.stack([np.flatnonzero(np.isfinite(p[:, 9])) for p in plays])
    # The first rating, stored in trial 1, is pre-task. Others follow that row.
    observed = indices + 1
    observed[:, 0] = 0
    selected = states[np.arange(n)[:, None], observed]
    x = np.concatenate([selected[:, :, :3], observed[:, :, None],
                        level[np.arange(n)[:, None], observed][:, :, None], selected[:, :, 3:]], axis=2)
    y = plays[np.arange(n)[:, None], indices, 9]
    return x, y


def center_training(x: np.ndarray, y: np.ndarray, train: int = 10) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    scale = y[:, :train].std(axis=1, ddof=1)
    keep = np.isfinite(scale) & (scale > 1e-12)
    y = (y[keep] - y[keep, :train].mean(axis=1)[:, None]) / scale[keep, None]
    x = x[keep] - x[keep, :train].mean(axis=1)[:, None, :]
    return x, y, keep


def stats(x: np.ndarray, y: np.ndarray, train: int = 10) -> dict:
    return {"xx": np.einsum("nti,ntj->nij", x[:, :train], x[:, :train]),
            "xy": np.einsum("nti,nt->ni", x[:, :train], y[:, :train]),
            "yy": np.einsum("nt,nt->n", y[:, :train], y[:, :train]),
            "txx": np.einsum("nti,ntj->nij", x[:, train:], x[:, train:]),
            "txy": np.einsum("nti,nt->ni", x[:, train:], y[:, train:]),
            "tyy": np.einsum("nt,nt->n", y[:, train:], y[:, train:])}


def fit_stats(s: dict, columns: list[int], weights: np.ndarray | None = None) -> tuple[np.ndarray, float, float]:
    if weights is None:
        weights = np.ones(len(s["yy"]))
    xx = np.einsum("n,nij->ij", weights, s["xx"])[np.ix_(columns, columns)]
    xy = np.einsum("n,ni->i", weights, s["xy"])[columns]
    # Column scaling prevents raw point^2 curvature terms from wrecking conditioning.
    scale = np.sqrt(np.diag(xx)).clip(1e-15)
    beta = np.linalg.lstsq(xx / scale[:, None] / scale[None, :], xy / scale, rcond=1e-12)[0] / scale
    train_sse = weights @ s["yy"] - 2*beta @ xy + beta @ xx @ beta
    txx = np.einsum("n,nij->ij", weights, s["txx"])[np.ix_(columns, columns)]
    txy = np.einsum("n,ni->i", weights, s["txy"])[columns]
    test_sse = weights @ s["tyy"] - 2*beta @ txy + beta @ txx @ beta
    return beta, float(train_sse), float(test_sse / (2 * weights.sum()))


def _interval(draws: list[float] | np.ndarray) -> list[float]:
    return np.quantile(draws, [.025, .975]).tolist()


def pooled(plays: np.ndarray, out: Path, draws: int = 2000, seed: int = SEED, exploratory_n: int = 5000) -> dict:
    """Primary MD1/2 fits. Actual participant bootstrap refits and reselects gamma."""
    out.mkdir(parents=True, exist_ok=True)
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
        old = np.load(checkpoint)
        if (int(old["seed"]) != seed or int(old["n"]) != n or int(old["draws"]) != draws
                or str(old["input_sha256"]) != binding or str(old["code_sha256"]) != code_binding):
            raise ValueError("bootstrap resume contract mismatch")
        bootstrap = old["values"].tolist()
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
        if (draw+1) % 25 == 0 or draw+1 == draws:
            tmp = out / "bootstrap.tmp.npz"
            np.savez_compressed(tmp, values=np.array(bootstrap), seed=seed, n=n, draws=draws,
                                input_sha256=binding, code_sha256=code_binding)
            os.replace(tmp, checkpoint)
            save_json(out / "PROGRESS.json", {"phase": "participant_bootstrap", "completed": draw+1, "total": draws})
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


def person_fit(plays: np.ndarray, columns: list[int], penalty: float, train: int = 10,
               fixed_gamma: np.ndarray | None = None, spread_mean: float = 0., spread_sd: float = 1.) -> dict:
    """Independent ridge fits with training-only scaling and gamma selection."""
    n = len(plays); best = np.full(n, np.inf); mse = np.full(n, np.nan)
    coefficient = np.zeros((n, len(columns))); selected = np.zeros(n)
    valid_all = np.zeros(n, dtype=bool)
    for gamma in np.r_[GAMMAS, .95, 1.]:
        xx, yy = rating_history(plays, float(gamma), spread_mean, spread_sd)
        x, y, valid = center_training(xx, yy, train)
        selected_rows = np.flatnonzero(valid)
        if fixed_gamma is not None:
            subset = np.isclose(fixed_gamma[valid], gamma)
            selected_rows = selected_rows[subset]; x=x[subset]; y=y[subset]
        if not len(x):
            continue
        x = x[:, :, columns]
        scale = np.sqrt(np.mean(x[:, :train]**2, axis=1)).clip(1e-12)
        z = x/scale[:, None, :]
        gram = np.einsum("nti,ntj->nij", z[:, :train], z[:, :train])
        rhs = np.einsum("nti,nt->ni", z[:, :train], y[:, :train])
        regular = gram + penalty*np.eye(len(columns))[None, :, :]
        b = np.einsum("nij,nj->ni", np.linalg.pinv(regular, rcond=1e-12), rhs)
        predicted = np.einsum("nti,ni->nt", z, b)
        objective = ((y[:, :train]-predicted[:, :train])**2).sum(axis=1) + penalty*(b*b).sum(axis=1)
        improvement = objective < best[selected_rows]
        rows = selected_rows[improvement]
        best[rows] = objective[improvement]
        mse[rows] = ((y[:, train:]-predicted[:, train:])**2).mean(axis=1)[improvement]
        coefficient[rows] = (b/scale)[improvement]
        selected[rows] = gamma
        valid_all[rows] = True
    return {"mse": mse, "beta": coefficient, "gamma": selected, "valid": valid_all}


def companions(plays: np.ndarray, out: Path, seed: int = SEED, exploratory_n: int = 5000) -> dict:
    """Ridge companion and historical sign checks. This does not publish IDs."""
    order = np.random.default_rng(seed).permutation(len(plays))
    split = min(exploratory_n, max(0, len(plays)//3))
    exploratory = plays[np.sort(order[:split])]
    main = plays[np.sort(order[split:])]
    penalties = [0., .01, .1, 1., 10., 100.]
    tuning = []
    # Inner validation is ratings 9–10; final 2 ratings are never tuning targets.
    for penalty in penalties:
        model = person_fit(exploratory, [0, 1, 2, 3, 4], penalty, train=8)
        # person_fit predicts all remaining ratings; recompute only 9–10 here.
        losses = []
        for gamma in np.unique(model["gamma"][model["valid"]]):
            use = model["valid"] & np.isclose(model["gamma"], gamma)
            x, y = rating_history(exploratory[use], float(gamma))
            x, y, good = center_training(x, y, 8)
            pred = np.einsum("nti,ni->nt", x[:, 8:10, :5], model["beta"][use][good])
            losses.extend(np.mean((y[:, 8:10]-pred)**2, axis=1).tolist())
        tuning.append(float(np.mean(losses)))
    penalty = penalties[int(np.argmin(tuning))]
    base = person_fit(main, [0, 1, 2], penalty)
    time_model = person_fit(main, [0, 1, 2, 3], penalty)
    level = person_fit(main, [0, 1, 2, 3, 4], penalty, fixed_gamma=time_model["gamma"])
    gamble = main[:, :, 6] == 1
    cutoff = np.array([np.flatnonzero(np.isfinite(p[:, 9]))[9] for p in main])
    train_trials = gamble & (np.arange(30)[None, :] <= cutoff[:, None])
    spreads = (main[:, :, 3]-main[:, :, 4])[train_trials]
    md2 = person_fit(main, [0, 1, 2, 3, 5, 6], penalty, fixed_gamma=time_model["gamma"],
                     spread_mean=float(spreads.mean()), spread_sd=float(spreads.std(ddof=1)))
    valid = base["valid"] & time_model["valid"] & level["valid"]
    eligible = valid & (time_model["gamma"] <= .9)
    # Original-style sign diagnostic uses the current first-play roster, all 12
    # ratings, no time or level, and 92 consecutive blocks of 200 if available.
    history = person_fit(plays[:18400], [0, 1, 2], 0., train=12)
    groups = []
    for i in range(0, min(len(plays), 18400)-199, 200):
        mask = history["valid"][i:i+200]
        b = history["beta"][i:i+200][mask]
        if len(b):
            groups.append(b.mean(axis=0))
    block = np.array(groups)
    record = {"ridge_penalty": penalty, "ridge_grid": penalties, "inner_validation_mse": tuning,
              "exploratory_participants": split, "per_person_valid": int(valid.sum()),
              "gamma_above_point9_excluded": int((valid & ~eligible).sum()),
              "per_person_median_level_weight": float(np.median(level["beta"][eligible, -1])),
              "per_person_median_spread_weight": float(np.median(md2["beta"][eligible, 4])),
              "time_gain": float(1-np.mean(time_model["mse"][valid])/np.mean(base["mse"][valid])),
              "historical_sign_diagnostic": {"scope": "current-source first plays; not exact deleted 2014 cohort",
                  "blocks": len(groups), "positive_cr_ev_rpe_blocks": (block > 0).sum(axis=0).tolist(),
                  "ev_below_rpe_blocks": int((block[:, 1] < block[:, 2]).sum()),
                  "target_blocks": 92, "target_positive_each": 92, "target_ev_below_rpe": 91},
              "complete_card": False, "remaining": ["independent replay", "late-play level and observed-time companions"]}
    save_json(out / "COMPANIONS.json", record)
    return record


def fixture() -> dict:
    p = np.zeros((80, 30, 15), dtype=float)
    p[:, :, 0] = np.arange(1, 31)
    rng = np.random.default_rng(SEED)
    p[:, :, 2] = rng.choice([-20., 0., 20.], (80, 30))
    p[:, :, 3] = rng.choice([40., 60., 80.], (80, 30))
    p[:, :, 4] = -rng.choice([20., 40., 60.], (80, 30))
    p[:, :, 6] = rng.integers(0, 2, (80, 30))
    wins = rng.integers(0, 2, (80, 30))
    p[:, :, 7] = np.where(p[:, :, 6], np.where(wins, p[:, :, 3], p[:, :, 4]), p[:, :, 2])
    p[:, :, 9] = np.nan
    rows = np.array([0, 3, 5, 8, 11, 13, 16, 18, 21, 24, 26, 29])
    p[:, rows, 9] = 50.
    x, _ = rating_history(p, .5)
    assert np.array_equal(x[:, 0], np.zeros((80, 7)))
    assert np.allclose(x[:, 1, 4], p[:, :4, 7].sum(axis=1))
    manual = np.zeros(5)
    pp = p[0]
    for t in range(4):
        g = pp[t, 6]; ev = (pp[t, 3]+pp[t, 4])/2; spread = pp[t, 3]-pp[t, 4]
        manual = .5*manual + [pp[t, 2]*(1-g), ev*g, (pp[t, 7]-ev)*g, ev*spread*g, ev*abs(ev)*g]
    assert np.allclose(x[0, 1, [0, 1, 2, 5, 6]], manual)
    signed = []
    for sign in [-1, 0, 1]:
        y = x[:, :, :4] @ np.array([.01, .01, .02, -.02]) + sign*.02*x[:, :, 4]
        xc = x-x[:, :10].mean(axis=1)[:, None, :]
        yc = y-y[:, :10].mean(axis=1)[:, None]
        beta = fit_stats(stats(xc, yc), [0, 1, 2, 3, 4])[0]
        assert abs(beta[-1]-sign*.02) < 1e-10
        signed.append(float(beta[-1]))
    # Held-out happiness cannot affect centering or coefficient fitting.
    a, y, _ = center_training(x, 50+x[:, :, 4]*.01+rng.normal(size=(80, 12)))
    y2 = y.copy(); y2[:, 10:] += 1000
    assert np.allclose(fit_stats(stats(a, y), [0, 1, 2, 3, 4])[0], fit_stats(stats(a, y2), [0, 1, 2, 3, 4])[0])
    return {"passed": True, "rating_clock": True, "manual_discount_replay": True,
            "signed_level_weights": signed, "heldout_training_isolation": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["fixture", "prepare", "pooled"])
    parser.add_argument("--source", type=Path, default=Path("corpora/store/external/rutledge_gbe"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--draws", type=int, default=2000)
    args = parser.parse_args(); start = time.process_time()
    if args.mode == "fixture":
        result = fixture(); save_json(args.out / "FIXTURE.json", result)
    elif args.mode == "prepare":
        result = prepare(args.source, args.out)
    else:
        source = args.input or args.source / "task.npz"
        with np.load(source) as data:
            result = pooled(data["first"], args.out, args.draws)
    save_json(args.out / "EXECUTION.json", {"mode": args.mode, "cpu_seconds": time.process_time()-start,
                                           "scientific_complete": False})


if __name__ == "__main__":
    main()
