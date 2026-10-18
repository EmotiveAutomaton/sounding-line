"""Corrected V4.c half-specific readers and simulated boundary reference.

DESIGN CHECK: LESSONS 3-5 and October18 errata read. Directions, scaling,
kernel choice and session-start population frequencies for A cannot depend on
B outcomes. The tested variance is constrained nonnegative, retaining exact
zero. The reference uses correlated score components inside each half, and
independent Gaussian draws between halves: that last step is an approximation
because swapped fitted directions share a world. The required saved null
worlds, not a claim of exact asymptotics, determine calibration. Singular null
information is an invalid test, never a zero statistic or a repaired ridge.
"""
from __future__ import annotations

import copy
import heapq
import itertools
from collections import defaultdict

import numpy as np

from .menus_v4_stats import variance_reader, predict, taste_directions
from .menus_v4_saved_diagnostics import ACTIONS
from runners.drive.statistics import half_brier

READERS = ("R-taste", "R-kernel", "R-both")


def alternating_halves(rows):
    groups = defaultdict(list)
    for index, row in enumerate(rows):
        groups[row["session"]].append(index)
    halves = np.zeros(len(rows), int)
    for ids in groups.values():
        ordered = sorted(ids, key=lambda i: (rows[i]["open_at"], rows[i]["key"]))
        halves[ordered] = np.arange(len(ordered)) % 2
    return halves


def separate_history(rows, halves):
    result = copy.deepcopy(rows)
    for half in (0, 1):
        history, pending = {}, []
        for i in sorted(np.flatnonzero(halves == half), key=lambda i: (rows[i]["open_at"], rows[i]["key"])):
            row = result[i]
            while pending and pending[0][0] <= row["open_at"]:
                _, key, writer, opened, action = heapq.heappop(pending)
                candidate = (opened, key, action)
                if writer not in history or candidate[:2] > history[writer][:2]:
                    history[writer] = candidate
            row["previous_handling"] = history.get(row["writer"], (None, None, None))[2]
            heapq.heappush(pending, (row["resolved_at"], row["key"], row["writer"], row["open_at"], row["handling"]))
    return result


def population(rows, sessions, halves, learning_half):
    """Exact B-pop pseudocount, restricted to earlier completed A sessions."""
    row_by_session = defaultdict(list)
    for i, row in enumerate(rows):
        row_by_session[row["session"]].append(i)
    pending = []
    for session in sessions:
        ids = [i for i in row_by_session[session["session"]] if halves[i] == learning_half]
        counts = np.bincount([ACTIONS.index(rows[i]["handling"]) for i in ids], minlength=4)
        pending.append((session["end_at"], session["session"], counts))
    pending.sort(key=lambda item: (item[0], item[1]))
    accumulated = np.zeros(4, int); cursor = 0; values = np.zeros((len(rows), 4)); audit = []
    for session in sorted(sessions, key=lambda s: (s["timestamp"], s["session"])):
        while cursor < len(pending) and pending[cursor][0] < session["timestamp"]:
            accumulated += pending[cursor][2]; cursor += 1
        p = (accumulated + 1.) / (accumulated.sum() + 4.)
        values[row_by_session[session["session"]]] = p
        audit.append(dict(session=session["session"], learning_half=learning_half,
                          prior_decisions=int(accumulated.sum()), probabilities=p.tolist()))
    if not np.allclose(values.sum(1), 1.):
        raise ValueError("half-specific B-pop lacks source coverage")
    return values, audit


def half_kernels(rows, halves, base, decay):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["writer"]].append(base[row["key"]])
    centers = {name: np.asarray(values).mean(0) for name, values in grouped.items()}
    values = np.zeros((len(rows), 1))
    for half in (0, 1):
        current = {name: value.copy() for name, value in centers.items()}; pending = []
        for i in sorted(np.flatnonzero(halves == half), key=lambda i: (rows[i]["open_at"], rows[i]["key"])):
            row = rows[i]
            while pending and pending[0][0] <= row["open_at"]:
                _, key, writer, outcome = heapq.heappop(pending)
                current[writer] = decay*current[writer] + (1-decay)*np.eye(4)[outcome]
            values[i,0] = current[row["writer"]][0] - centers[row["writer"]][0]
            heapq.heappush(pending, (row["resolved_at"], row["key"], row["writer"], ACTIONS.index(row["handling"])))
    return values


def select_half(rows, sessions, saved, geometry, base, learning_half, maxiter=100):
    halves = alternating_halves(rows)
    rows = separate_history(rows, halves)
    writer = np.asarray([r["writer"] for r in rows]); keys = [r["key"] for r in rows]
    y = np.asarray([ACTIONS.index(r["handling"]) for r in rows]); accept = (y == 0).astype(float)
    p, population_audit = population(rows, sessions, halves, learning_half)
    train = np.isin(keys, saved["train_keys"]) & (halves == learning_half)
    cal = np.isin(keys, saved["calibration_keys"]) & (halves == learning_half)
    eligible = np.isin(keys, saved["train_keys"] + saved["calibration_keys"] + saved["keys"])
    test = eligible & (halves != learning_half)
    if not train.any() or not cal.any() or not test.any():
        raise ValueError("empty split-test learning/calibration/testing support")
    index = {key: i for i, key in enumerate(geometry["keys"])}
    raw = np.asarray([geometry["menu_mini"][index[key]] for key in keys])
    mean, sd = raw[train].mean(0), raw[train].std(0); sd[sd < 1e-10] = 1.
    x = (raw - mean) / sd
    directions = {}; candidates = {}; designs = {}

    def select(named):
        scores = []
        for name, design in sorted(named.items()):
            fit = variance_reader(design[train], accept[train], p[train, 0], writer[train], maxiter)
            prediction = predict(fit, design[cal], p[cal], writer[cal])
            score = float(half_brier(prediction, y[cal]).mean())
            candidates[name] = dict(fit=fit, calibration_half_brier=score)
            scores.append((score, name))
        chosen = min(scores)[1]
        return chosen, named[chosen]

    taste = {}
    for k in (2, 4):
        direction = taste_directions(x, accept, p[:, 0], writer, train, k)
        directions[str(k)] = direction.tolist(); taste["taste_" + str(k)] = x @ direction
    taste_name, taste_x = select(taste)
    kernels = {}
    for decay in (.5, .8, .95):
        # Original whole-writer frozen baseline center, with distinct half-only
        # update streams. No re-centering on either half's observed outcomes.
        kernels["kernel_" + str(decay)] = half_kernels(rows, halves, base, decay)
    kernel_name, kernel_x = select(kernels)
    designs.update({"R-taste": taste_x, "R-kernel": kernel_x, "R-both": np.c_[taste_x, kernel_x]})
    audit = dict(learning_half=learning_half, tested_half=1-learning_half,
        train_keys=[k for k,m in zip(keys,train) if m], calibration_keys=[k for k,m in zip(keys,cal) if m],
        test_keys=[k for k,m in zip(keys,test) if m], selected_taste=taste_name, selected_kernel=kernel_name,
        directions=directions, mean=mean.tolist(), scale=sd.tolist(), candidates=candidates,
        population=population_audit, test_population_accept=p[test,0].tolist(),
        test_truth=accept[test].tolist(), test_writers=writer[test].tolist(),
        kernel_history="separate causal outcome stream in each alternating half")
    return designs, audit, dict(test=test, accept=accept, population=p, writers=writer)


def score_information(x, p, writers):
    """Exact covariance of the zero-variance score for fixed independent rows.

    S_j=.5*((sum_i x_ij*(Y_i-p_i))**2-sum_i x_ij**2*v_i), summed by writer.
    Cov(S_j,S_k)=.5*sum_w(sum_i v_i*x_ij*x_ik)**2
                  +.25*sum_i v_i*(1-6*v_i)*x_ij**2*x_ik**2.
    This fixed-design information is an approximation for causal random designs.
    """
    x, p, writers = np.asarray(x,float), np.asarray(p,float), np.asarray(writers)
    if x.ndim != 2 or p.shape != (len(x),) or writers.shape != p.shape or not np.isfinite(x).all() or not np.all((p > 0) & (p < 1)):
        raise ValueError("invalid variance-score information support")
    v = p*(1-p); information = np.zeros((x.shape[1],x.shape[1]))
    for writer in sorted(set(writers)):
        a = x[writers == writer]; variance = v[writers == writer]
        covariance = a.T @ (variance[:,None] * a)
        square = a*a
        information += .5*covariance*covariance + .25*(square.T @ ((variance*(1-6*variance))[:,None] * square))
    return (information + information.T)/2


def cone_statistics(information, normals):
    """Maximize 2*s'v-v'Iv over nonnegative v by exact active-set enumeration."""
    information, normals = np.asarray(information,float), np.asarray(normals,float)
    k = len(information)
    if information.shape != (k,k) or normals.ndim != 2 or normals.shape[1] != k or not np.isfinite(information).all() or not np.isfinite(normals).all():
        raise ValueError("invalid chi-bar reference arrays")
    scale = np.sqrt(np.diag(information))
    if np.any(scale <= 0):
        raise ValueError("unidentified null variance information")
    correlation = information / np.outer(scale,scale)
    eigen = np.linalg.eigvalsh(correlation)
    if eigen[0] <= 1e-10:
        raise ValueError("singular null variance information; no ridge repair")
    scores = normals @ np.linalg.cholesky(correlation).T
    values = np.zeros(len(normals))
    for size in range(1,k+1):
        for ids in itertools.combinations(range(k),size):
            ids = list(ids); block = correlation[np.ix_(ids,ids)]
            coefficients = np.linalg.solve(block,scores[:,ids].T).T
            valid = np.all(coefficients >= 0,axis=1)
            value = np.sum(coefficients*scores[:,ids],axis=1)
            values = np.maximum(values,np.where(valid,value,0.))
    return values, dict(information=information.tolist(), score_correlation=correlation.tolist(),
        minimum_eigenvalue=float(eigen[0]), dimensions=k, approximation="fixed-design Gaussian variance-score cone")


def reference(information_a, information_b, observed, seed, draws=20000):
    rng=np.random.default_rng(seed)
    a, aa=cone_statistics(information_a,rng.normal(size=(draws,len(information_a))))
    b, bb=cone_statistics(information_b,rng.normal(size=(draws,len(information_b))))
    values=(a+b)/2
    return dict(p_value=float((1+np.sum(values>=observed))/(draws+1)),
        threshold95=float(np.quantile(values,.95)), mean=float(values.mean()),
        standard_deviation=float(values.std(ddof=1)), quantiles95=np.quantile(values,[.025,.975]).tolist(),
        seed=seed,draws=draws,half_information=[aa,bb],
        independent_between_half_draws_approximation=True,
        dependence_warning="Swapped learned directions share the original world; independent half Gaussian draws are not an exact joint reference. Full saved null-world calibration is decisive.")


def split_world(rows,sessions,saved,geometry,base,seed,maxiter=100,draws=20000):
    halves=[]
    for half in (0,1):
        designs,audit,support=select_half(rows,sessions,saved,geometry,base,half,maxiter)
        test=support["test"]; fits={}; information={}
        for reader in READERS:
            x=designs[reader][test]; y=support["accept"][test]; p=support["population"][test,0]
            writer=support["writers"][test]
            fits[reader]=variance_reader(x,y,p,writer,maxiter)
            information[reader]=score_information(x,p,writer).tolist()
        halves.append(dict(audit=audit,fits=fits,information=information))
    readers={}
    for index,reader in enumerate(READERS):
        statistic=float(np.mean([h["fits"][reader]["likelihood_ratio"] for h in halves]))
        ref=reference(halves[0]["information"][reader],halves[1]["information"][reader],statistic,seed+100*index,draws)
        readers[reader]=dict(likelihood_ratio=statistic,p_value=ref["p_value"],detected=ref["p_value"]<.05,reference=ref)
    return dict(halves=halves,readers=readers)
