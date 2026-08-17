"""G149 ruler gate — can a window-local shift sampler LOCATE known motivation switches?

The curator's reframe (G149): what the movement instruments capture is shifting motivations
over time, sampled as the policy-propensity landscape's peaks move. Before any such sampler
touches provenance-adjacent text, the concept gets its known-answer gate where motivation
shifts are planted by construction: the BST gridworld engine (validated to printed precision,
L119/L120/L122) generates Boltzmann paths whose active goal SWITCHES at a known step, and the
sampler must find the switch without being told the generative parameters.

    SAMPLER     for each interior step t, Delta(t) = best two-goal split fit minus best
                single-goal fit (sum of step log-likelihoods, argmax over marked goals);
                detected switch = argmax_t Delta(t), detection threshold = the 95th
                percentile of max-Delta on NO-SWITCH paths (false alarms priced at 5%
                by construction)
    GATES       planted switches detected above threshold and localized within +/-2 steps
                at the paper's own fitted beta (2.0); no-switch worlds stay quiet at the
                threshold's own rate. A sampler that cannot pass this on paths where the
                switch is REAL never touches text
    ARMS        beta in {0.5, 1.0, 2.0, 4.0} crossed with switch/no-switch, 200 paths per
                cell, worlds and goals drawn from the decoded Fig-3 stimuli

Output: results/g149/switch_sampler.json (detection rate, localization MAE, threshold, and
the full Delta distributions' summaries -- every statistic on disk).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))

RESULTS = REPO / "results" / "g149"
BETAS = (0.5, 1.0, 2.0, 4.0)
N_PATHS = 200
PATH_LEN = 20
LOC_TOL = 2
SEED = 47


def sample_path(world, np, rng, goals, beta, t_switch=None):
    """A Boltzmann path; the active goal switches at t_switch (None = single goal)."""
    labels = list(goals)
    g0 = labels[rng.integers(len(labels))]
    g1 = g0
    if t_switch is not None:
        others = [l for l in labels if l != g0]
        g1 = others[rng.integers(len(others))]
    for _attempt in range(50):
        start = world.cells[rng.integers(len(world.cells))]
        if start in (goals[g0], goals[g1]):
            continue
        path = [start]
        ok = True
        for t in range(PATH_LEN - 1):
            g = g1 if (t_switch is not None and t >= t_switch) else g0
            target = goals[g]
            if path[-1] == target:                    # absorbed early: resample the path
                ok = False
                break
            world.soft_vi(target, beta)
            P = world._PI[(target, round(beta, 6))]
            si = world.idx[path[-1]]
            a = rng.choice(len(P[si]), p=P[si] / P[si].sum())
            path.append(world.cells[world.nxt[si, a]])
        if ok and len(path) == PATH_LEN:
            return path, g0, g1
    return None


def delta_curve(world, np, goals, beta, path):
    """Delta(t) for interior t: best split fit minus best single fit."""
    lps = {}
    for g, cell in goals.items():
        try:
            lp = world.step_logp(cell, beta, path)
        except AssertionError:
            lp = np.full(len(path) - 1, -np.inf)
        lps[g] = np.nan_to_num(lp, neginf=-1e9)
    G = list(goals)
    pre = {g: np.concatenate([[0.0], np.cumsum(lps[g])]) for g in G}
    total = {g: pre[g][-1] for g in G}
    best_single = max(total.values())
    T = len(path) - 1
    curve = []
    for t in range(2, T - 1):
        split = max(pre[g][t] for g in G) + max(total[g] - pre[g][t] for g in G)
        curve.append(split - best_single)
    return np.array(curve), 2                         # scores index t = offset + position


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    import run_bst_gridworld as bst                                   # noqa: PLC0415

    rng = np.random.default_rng(SEED)
    stims = bst.load_stimuli()
    seen, worlds = set(), []
    for s in stims:
        if s["walls"] not in seen:
            seen.add(s["walls"])
            worlds.append((bst.World(s["walls"], np), s["goals"]))
    print(f"{len(worlds)} distinct worlds from the decoded stimuli")

    out = {"seed": SEED, "n_paths": N_PATHS, "path_len": PATH_LEN, "loc_tol": LOC_TOL,
           "betas": {}}
    for beta in BETAS:
        null_max = []
        for _ in range(N_PATHS):
            world, goals = worlds[rng.integers(len(worlds))]
            s = sample_path(world, np, rng, goals, beta, t_switch=None)
            if s is None:
                continue
            curve, _ = delta_curve(world, np, goals, beta, s[0])
            null_max.append(float(curve.max()))
        thr = float(np.quantile(null_max, 0.95))

        det, loc_err, planted = 0, [], 0
        for _ in range(N_PATHS):
            world, goals = worlds[rng.integers(len(worlds))]
            t_sw = int(rng.integers(PATH_LEN // 3, 2 * PATH_LEN // 3))
            s = sample_path(world, np, rng, goals, beta, t_switch=t_sw)
            if s is None:
                continue
            planted += 1
            curve, off = delta_curve(world, np, goals, beta, s[0])
            if float(curve.max()) > thr:
                t_hat = int(np.argmax(curve)) + off
                err = abs(t_hat - t_sw)
                loc_err.append(err)
                if err <= LOC_TOL:
                    det += 1
        out["betas"][str(beta)] = {
            "threshold_null_q95": round(thr, 3),
            "n_null": len(null_max), "n_planted": planted,
            "null_max_median": round(float(np.median(null_max)), 3),
            "detected_and_localized": det,
            "detection_rate": round(det / max(planted, 1), 4),
            "over_threshold_rate": round(len(loc_err) / max(planted, 1), 4),
            "localization_mae": round(float(np.mean(loc_err)), 3) if loc_err else None,
        }
        print(f"beta {beta}: detect+localize {det}/{planted} "
              f"(thr {thr:.2f}, over-thr {len(loc_err)})")

    RESULTS.mkdir(parents=True, exist_ok=True)
    dest = RESULTS / "switch_sampler.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
