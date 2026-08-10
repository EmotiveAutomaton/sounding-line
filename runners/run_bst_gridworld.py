"""G137 v1 — the Baker–Saxe–Tenenbaum maze-world, model side, with internal known-answer gates.

Recreates the three inverse-planning models of the 2009 paper on a reconstructed maze (the
published stimuli exist only as figures; the reconstruction is the recorded deviation). Exact
value iteration per goal, Boltzmann action noise beta, observed path prefixes, online posterior
over goals.

    M1(beta)        static goal
    M2(beta,gamma)  goal may switch each step with probability gamma
    M3(beta,kappa)  goal pursued via a possible subgoal (via-point), prior kappa

Internal gates, run before anything is reported (all analytic, no figure needed):
    GATE-A  M2 with gamma -> 0 must equal M1 exactly (max posterior gap < 1e-6)
    GATE-B  full-path posterior on the true goal -> 1 as beta grows (monotone, > 0.95 at beta 4)
    GATE-C  in a mid-path goal-switch world, M2's posterior tracks the new goal while M1 stays
            stuck (M2 final mass on the new goal > 0.8, M1 < 0.5)

The paper's best-fit parameters are then run (M2 beta 2.0 gamma 0.25; M2 beta 0.5 gamma 0.65;
M3 beta 5.0 kappa 0.6) and the online posterior curves saved for figure-level comparison next
pass. Passing the internal gates is required; the figure comparison is the second half of the
recreation and is not claimed here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "bst_gridworld"

W, H = 9, 7
WALL = {(4, y) for y in range(1, 6)} - {(4, 3)}     # a wall with one gap, per the figures
GOALS = {"A": (8, 0), "B": (8, 6), "C": (0, 6)}
ACTS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def main() -> None:
    import numpy as np                                                # noqa: PLC0415

    cells = [(x, y) for x in range(W) for y in range(H) if (x, y) not in WALL]
    idx = {c: i for i, c in enumerate(cells)}

    def step(c, a):
        n = (c[0] + a[0], c[1] + a[1])
        return n if n in idx else c

    def values(goal):
        V = {c: -1e9 for c in cells}
        V[GOALS[goal]] = 0.0
        for _ in range(W * H):
            for c in cells:
                if c == GOALS[goal]:
                    continue
                V[c] = max(-1.0 + V[step(c, a)] for a in ACTS)
        return V

    VAL = {g: values(g) for g in GOALS}

    def policy(goal, beta):
        P = {}
        for c in cells:
            q = np.array([(-1.0 + VAL[goal][step(c, a)]) for a in ACTS])
            z = np.exp(beta * (q - q.max()))
            P[c] = z / z.sum()
        return P

    POL = {}

    def pol(goal, beta):
        if (goal, beta) not in POL:
            POL[(goal, beta)] = policy(goal, beta)
        return POL[(goal, beta)]

    def path_from(c0, goal, beta, steps, rng):
        path = [c0]
        for _ in range(steps):
            p = pol(goal, beta)[path[-1]]
            a = ACTS[rng.choice(len(ACTS), p=p)]
            path.append(step(path[-1], a))
        return path

    def m1_posterior(path, beta):
        logp = {g: 0.0 for g in GOALS}
        out = []
        for t in range(1, len(path)):
            a = (path[t][0] - path[t - 1][0], path[t][1] - path[t - 1][1])
            ai = ACTS.index(a) if a in ACTS else None
            for g in GOALS:
                pr = pol(g, beta)[path[t - 1]]
                logp[g] += np.log(pr[ai] + 1e-12) if ai is not None else 0.0
            mx = max(logp.values())
            zs = {g: np.exp(v - mx) for g, v in logp.items()}
            s = sum(zs.values())
            out.append({g: zs[g] / s for g in GOALS})
        return out

    def m2_posterior(path, beta, gamma):
        b = {g: 1.0 / len(GOALS) for g in GOALS}
        out = []
        for t in range(1, len(path)):
            b = {g: (1 - gamma) * b[g] + gamma / len(GOALS) for g in GOALS}
            a = (path[t][0] - path[t - 1][0], path[t][1] - path[t - 1][1])
            ai = ACTS.index(a) if a in ACTS else None
            if ai is not None:
                b = {g: b[g] * (pol(g, beta)[path[t - 1]][ai] + 1e-12) for g in GOALS}
            s = sum(b.values())
            b = {g: v / s for g, v in b.items()}
            out.append(dict(b))
        return out

    def m3_posterior(path, beta, kappa):
        # goal g via optional subgoal s (the wall gap); hypothesis space {(g, None), (g, gap)}
        gap = (4, 3)
        hyps = [(g, None) for g in GOALS] + [(g, gap) for g in GOALS]
        prior = {h: (1 - kappa) / 3 if h[1] is None else kappa / 3 for h in hyps}
        logp = {h: np.log(prior[h]) for h in hyps}
        out = []
        for t in range(1, len(path)):
            a = (path[t][0] - path[t - 1][0], path[t][1] - path[t - 1][1])
            ai = ACTS.index(a) if a in ACTS else None
            for h in hyps:
                g, s_ = h
                if s_ is not None and path[t - 1] != s_ and \
                        VAL_SUB[s_][path[t - 1]] < -0.5:      # still en route to subgoal
                    pr = pol_sub(s_, 2.0)[path[t - 1]]
                else:
                    pr = pol(g, beta)[path[t - 1]]
                if ai is not None:
                    logp[h] += np.log(pr[ai] + 1e-12)
            mx = max(logp.values())
            zs = {h: np.exp(v - mx) for h, v in logp.items()}
            s = sum(zs.values())
            marg = {g: sum(v / s for h, v in zs.items() if h[0] == g) for g in GOALS}
            out.append(marg)
        return out

    VAL_SUB = {}
    POL_SUB = {}

    def val_sub(s_):
        if s_ not in VAL_SUB:
            V = {c: -1e9 for c in cells}
            V[s_] = 0.0
            for _ in range(W * H):
                for c in cells:
                    if c == s_:
                        continue
                    V[c] = max(-1.0 + V[step(c, a)] for a in ACTS)
            VAL_SUB[s_] = V
        return VAL_SUB[s_]

    def pol_sub(s_, beta):
        if (s_, beta) not in POL_SUB:
            V = val_sub(s_)
            P = {}
            for c in cells:
                q = np.array([(-1.0 + V[step(c, a)]) for a in ACTS])
                z = np.exp(beta * (q - q.max()))
                P[c] = z / z.sum()
            POL_SUB[(s_, beta)] = P
        return POL_SUB[(s_, beta)]

    val_sub((4, 3))
    rng = np.random.default_rng(29)

    # ── GATE-A: M2(gamma->0) == M1
    p = path_from((0, 0), "A", 2.0, 10, rng)
    gap_a = max(abs(m1_posterior(p, 2.0)[t][g] - m2_posterior(p, 2.0, 1e-12)[t][g])
                for t in range(len(p) - 1) for g in GOALS)
    print(f"GATE-A m2(gamma->0) vs m1 max gap: {gap_a:.2e}")

    # ── GATE-B: posterior -> 1 with beta
    masses = []
    for beta in (0.5, 1.0, 2.0, 4.0):
        m = np.mean([m1_posterior(path_from((0, 0), "B", beta, 12, rng), beta)[-1]["B"]
                     for _ in range(40)])
        masses.append(float(m))
    print(f"GATE-B true-goal mass by beta: {[round(m, 3) for m in masses]}")

    # ── GATE-C: switch world
    m1f, m2f = [], []
    for _ in range(40):
        first = path_from((0, 0), "A", 3.0, 6, rng)
        second = path_from(first[-1], "C", 3.0, 8, rng)
        full = first + second[1:]
        m1f.append(m1_posterior(full, 3.0)[-1]["C"])
        m2f.append(m2_posterior(full, 3.0, 0.25)[-1]["C"])
    m1c, m2c = float(np.mean(m1f)), float(np.mean(m2f))
    print(f"GATE-C after-switch mass on new goal: M1 {m1c:.3f}, M2 {m2c:.3f}")

    gates = {"A": bool(gap_a < 1e-6),
             "B": bool(all(b >= a - 1e-9 for a, b in zip(masses, masses[1:]))
                       and masses[-1] > 0.95),
             "C": bool(m2c > 0.8 and m1c < 0.5)}
    verdict = "GATES-PASSED" if all(gates.values()) else "GATES-FAILED"
    print(f"  >>> {verdict}  {gates}")

    # ── best-fit parameter curves for the figure-level comparison, next pass
    curves = {}
    demo = path_from((0, 0), "B", 2.0, 14, rng)
    curves["exp1_m2_b2.0_g0.25"] = m2_posterior(demo, 2.0, 0.25)
    curves["exp2_m2_b0.5_g0.65"] = m2_posterior(demo, 0.5, 0.65)
    curves["exp3_m3_b5.0_k0.6"] = m3_posterior(demo, 5.0, 0.6)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(
        {"gates": gates, "gate_values": {"A_gap": gap_a, "B_masses": masses,
                                         "C_m1": m1c, "C_m2": m2c},
         "verdict": verdict,
         "curves": {k: [{g: round(x[g], 4) for g in x} for x in v]
                    for k, v in curves.items()},
         "deviation": "maze reconstructed from figure descriptions; published stimuli are "
                      "figures only"}, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")
    if verdict != "GATES-PASSED":
        sys.exit(1)


if __name__ == "__main__":
    main()
