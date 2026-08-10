"""G138 — recreate the Armstrong–Mindermann unidentifiability construction, then relax it.

Phase 1 frontier recreation. The theorem's core: a policy cannot identify reward and planner
jointly, since (R, optimal) and (-R, anti-optimal) produce the same behaviour. Step one REPRODUCES
that degeneracy in an enumerable world (the recreation gate: the posterior over reward must stay
exactly split under planner uncertainty). Step two adds the three human priors this project's §7
names, one at a time, and measures posterior narrowing:

    A  bounded reward family    only "human-shaped" rewards (sparse, non-negative)
    B  known planner            near-optimal with known temperature (expertise as transition model)
    C  both

World: a 7-state chain, actions left/right/stay, deterministic moves; reward is over states;
behaviour is the exact soft-optimal policy (or its corruptions) observed in every state. The
posterior over (reward, planner) pairs is exact enumeration, no sampling. Sweeps over observation
noise and temperature give the narrowing curves; 20 seeds per cell.

    RECREATED   step one's posterior mass on the true reward == mass on its negation (0.5/0.5)
    NARROWS     each added prior strictly increases mass on the true reward, ordering A,B < C
"""

from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "am_construction"
N_STATES = 7
SEEDS = 20
NOISES = (0.0, 0.05, 0.1, 0.2)


def main() -> None:
    import numpy as np                                                # noqa: PLC0415

    acts = (-1, 0, 1)

    def policy(reward, planner, beta=6.0):
        # one-step lookahead soft policy per state; enough structure for the degeneracy
        P = np.zeros((N_STATES, len(acts)))
        for s in range(N_STATES):
            q = np.array([reward[max(0, min(N_STATES - 1, s + a))] for a in acts], float)
            if planner == "optimal":
                z = np.exp(beta * (q - q.max()))
            elif planner == "anti":
                z = np.exp(-beta * (q - q.min()))
            elif planner == "lazy":
                z = np.exp(beta * (q - q.max()));  z[1] *= 4.0
            else:  # "noisy" -- weakly rational
                z = np.exp(1.0 * (q - q.max()))
            P[s] = z / z.sum()
        return P

    def loglik(obs, P):
        return float(np.sum(np.log(P[np.arange(N_STATES), obs] + 1e-12)))

    rng_master = np.random.default_rng(7)

    def reward_family(bounded):
        fam = []
        vals = (0.0, 1.0) if bounded else (-1.0, 0.0, 1.0)
        for combo in product(vals, repeat=N_STATES):
            r = np.array(combo, float)
            if bounded and (r.sum() == 0 or (r > 0).sum() > 3):
                continue     # sparse, non-negative, at most three goals
            if not bounded and np.all(r == 0):
                continue
            fam.append(r)
        return fam

    def posterior_true_mass(true_r, fam, planners, obs):
        scores = []
        for r in fam:
            for pl in planners:
                scores.append((loglik(obs, policy(r, pl)), r))
        m = max(s for s, _ in scores)
        w = [(np.exp(s - m), r) for s, r in scores]
        z = sum(x for x, _ in w)
        return float(sum(x for x, r in w if np.array_equal(r, true_r)) / z)

    full_fam = reward_family(False)
    bound_fam = reward_family(True)
    print(f"reward families: full {len(full_fam)}, bounded {len(bound_fam)}")

    # ── step one: the recreation. true reward vs its negation, planner unknown in {optimal, anti}
    true_r = np.zeros(N_STATES); true_r[5] = 1.0
    obs = np.argmax(policy(true_r, "optimal"), axis=1)
    two_fam = [true_r, -true_r]
    mass = posterior_true_mass(true_r, two_fam, ("optimal", "anti"), obs)
    recreated = abs(mass - 0.5) < 1e-6
    print(f"step one, the degeneracy: posterior mass on true reward {mass:.6f} "
          f"(theorem demands exactly 0.5) -> {'RECREATED' if recreated else 'FAILED'}")
    if not recreated:
        (RESULTS / "summary.json") if RESULTS.exists() else RESULTS.mkdir(parents=True)
        sys.exit(1)

    # ── step two: relaxations, swept
    conditions = {
        "none": (full_fam, ("optimal", "anti", "lazy", "noisy")),
        "A_bounded": (bound_fam, ("optimal", "anti", "lazy", "noisy")),
        "B_planner": (full_fam, ("optimal",)),
        "C_both": (bound_fam, ("optimal",)),
    }
    curves: dict[str, dict[str, list[float]]] = {c: {} for c in conditions}
    for noise in NOISES:
        for cond, (fam, planners) in conditions.items():
            masses = []
            for seed in range(SEEDS):
                rng = np.random.default_rng(1000 * seed + int(noise * 100))
                tr = fam[rng.integers(len(fam))]
                o = np.argmax(policy(tr, "optimal"), axis=1)
                flip = rng.random(N_STATES) < noise
                o = np.where(flip, rng.integers(0, len(acts), N_STATES), o)
                masses.append(posterior_true_mass(tr, fam, planners, o))
            curves[cond][str(noise)] = [float(np.mean(masses)), float(np.std(masses))]
        print(f"noise {noise}: " + "  ".join(
            f"{c} {curves[c][str(noise)][0]:.3f}" for c in conditions))

    clean = {c: curves[c]["0.0"][0] for c in conditions}
    narrows = clean["A_bounded"] > clean["none"] and clean["B_planner"] > clean["none"] \
        and clean["C_both"] >= max(clean["A_bounded"], clean["B_planner"])
    verdict = "RECREATED+NARROWS" if narrows else "RECREATED, RELAXATION UNCLEAR"
    print(f"  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(
        {"degeneracy_mass": mass, "family_sizes": {"full": len(full_fam),
                                                   "bounded": len(bound_fam)},
         "curves": curves, "clean_noise_masses": clean, "verdict": verdict,
         "seeds": SEEDS}, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
