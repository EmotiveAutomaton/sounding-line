"""G161 — the anomaly-handling ruler on known answers (Phase 2.2C), built in the
constructed world before any natural text, per the brief's hard ordering.

The handling ladder, generated mechanically so every episode's class is ground truth:
    no_anomaly      near-greedy walk to the goal
    unexplained     optimal under goal PLUS an undisclosed waypoint: ordered, odd under
                    the declared goal alone -- the class that must NEVER be called error
    unnoticed       one planted off-policy step, then OPEN-LOOP continuation of the
                    pre-error action plan (the displacement persists; actions stop
                    adapting)
    repaired        one planted step, then an explicit BACKTRACK to the pre-error cell,
                    then greedy resumption (visible correction, costlier than re-planning)
    concealed       one planted step, then CLOSED-LOOP re-plan from the new state
                    (recognition without visible correction)
    repeated        the same biased off-policy action at three separated steps, re-planned
                    between (habit signature)
    secondary       the unexplained shape evaluated TWICE: context withheld (must read as
                    unexplained order, never error) and context declared (the waypoint
                    supplied; must reclassify as clean) -- the 2.2E conditioning hook

The ruler is likelihood-grade per the G149 license (L127/L134: per-step likelihood
structure transfers; surface distances do not): per-step log-probability under the
declared goal's soft policy locates anomaly steps against a clean-walk null threshold;
post-anomaly behavior classifies handling (backtrack signature; adaptive vs non-adaptive
continuation likelihood; recurrence of the same action delta; waypoint search for an
ordering account). Abstention is a first-class output.

DESIGN CHECK (2026-08-20, at design time). Lessons read: LESSONS §3 to §5 complete
(including every 2026-08-19 entry), CONTROLS 6/7; the brief's twelve gates (§10) and
pre-mortem items 1/2/5/6. Gates, each with null and alternative expectations and the
guarded direction, thresholds preregistered here:
    no-signal gate: clean walks classify no_anomaly or abstain at >= 0.95. Null (ruler
      honest) = passes; alternative failure = invented anomalies, direction UP in the
      false-anomaly rate (pre-mortem 1, the projection failure).
    unfamiliar-order gate: unexplained-order episodes labeled any error class at <= 0.05.
      Null = passes; failure direction UP = projection-heavy instrument unusable on
      open-domain artifacts (pre-mortem 2). Abstain and unexplained both count as honest.
    known-answer gate: every planted class recovers above the 1/7 chance rate; the
      output is the full confusion matrix over handling states, never an aggregate
      (pre-mortem 5).
    repair-vs-concealment gate: the pairwise confusion between repaired and concealed
      <= 0.20 each direction. These two share an error step and differ only in what
      follows; their separation is the ruler's reason to exist.
    recurrence gate: repeated episodes classified repeated, not unexplained order (a
      constraint control: recurrence alone must not read as intent).
    context gate: secondary episodes flip from unexplained (withheld) to clean
      (declared) in >= 0.80 of episodes; failure = context cards act as labels or do
      nothing (2.2E's artifact-contribution question in miniature).
    FAIL on any gate = the ruler does not license 2.2D's text battery; the failed
      distinction is retired or redesigned, per the brief's completion conditions.
The anomaly-step threshold is the q01 of clean-walk per-step log-probabilities (a null
population threshold, CONTROLS class 3), computed on a disjoint clean sample, never on
scored episodes. Seeds deterministic per (class, episode); beta fixed at the BST fitted
human rationality 2.5; everything on disk.

Output: results/g161/ruler.json. CPU only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_bst_gridworld import World, ACTS, GRID_W, GRID_H              # noqa: E402

OUT = REPO / "results" / "g161"
SEED = 16100
BETA = 2.5
N_PER = 50
N_NULL = 200          # disjoint clean walks for the threshold population
MAXLEN = 60
CLASSES = ["no_anomaly", "unexplained", "unnoticed", "repaired", "concealed",
           "repeated", "secondary"]
START, GOAL, WAYPOINT = (1, 4), (15, 4), (1, 8)
BIAS_ACT = 2          # the repeated class's habitual deviation: (0, +1), downward

# Ruler iteration record (the construction is synthetic; the classifier is the thing
# under construction, and iterating it against known answers IS the build -- the run
# that counts is the recorded one). v1 (2026-08-20 morning) FAILED four gates and the
# diagnosis drove three structural changes: an EMPTY grid made a one-step error nearly
# consequence-free (open-loop replay of the old plan stayed near-optimal from the
# displaced cell, so unnoticed collapsed into concealed); a PER-STEP q01 threshold
# over-fires on clean episodes by construction (~ 1 - 0.99^len per walk); and the
# waypoint account searched only cells adjacent to low steps (missing real waypoints)
# while accepting trivial accounts (absorbing repeated deviations). v2: a wall with a
# door makes displacement change the required route; the threshold is the q05 of the
# EPISODE-MINIMUM per-step log-probability over disjoint clean walks (no-signal rate
# 0.95 by construction, an episode-level null population); the classifier checks
# recurrence first, requires a waypoint account to clean EVERY step with a detour of
# at least three, and uses goal-arrival plus continuation adaptivity for the
# unnoticed/concealed split. v3 exposed the deepest constraint: a SINGLE worst-case
# step cannot be honestly separated from the beta-rational walker's own softmax noise
# (the clean generator itself takes rare bad steps), so v4 plants THREE consecutive
# off-policy steps -- a wrong turn, not a stumble -- which is also the honest analogue
# of a categorical text error (a broken constraint or wrong fact spans a span, not a
# word twitch). The hard threshold recalibrates to q03 of clean-episode minima so the
# combined hard+run false-episode rate stays ~0.05, measured on the null sample and
# reported.
WALL_X = 8
DOOR_Y = 4


def build_world(np):
    walls = [(WALL_X, y) for y in range(GRID_H) if y != DOOR_Y]
    return World(walls, np)


def greedy_path(w, target, start, np, maxlen=MAXLEN):
    w.soft_vi(target, BETA)
    P = w._PI[(target, round(BETA, 6))]
    path = [start]
    while path[-1] != target and len(path) < maxlen:
        si = w.idx[path[-1]]
        a = int(np.argmax(P[si]))
        path.append(w.cells[w.nxt[si, a]])
    return path


def policy_step(w, target, cell, rng, np):
    w.soft_vi(target, BETA)
    P = w._PI[(target, round(BETA, 6))]
    si = w.idx[cell]
    a = int(rng.choice(len(ACTS), p=P[si] / P[si].sum()))
    return w.cells[w.nxt[si, a]]


def off_policy_step(w, target, cell, rng, np, forced_act=None):
    """The planted anomaly: the WORST available non-stay action. v2's mild non-argmax
    plants sat inside the clean walker's own softmax variation, which is not an anomaly
    under the declared account at all; a planted error must be behavior the account
    assigns distinctly low probability (v3 iteration note)."""
    w.soft_vi(target, BETA)
    P = w._PI[(target, round(BETA, 6))]
    si = w.idx[cell]
    best = int(np.argmax(P[si]))
    if forced_act is not None and w.avail[si, forced_act] and forced_act != best:
        return w.cells[w.nxt[si, forced_act]]
    cands = [a for a in range(len(ACTS)) if w.avail[si, a] and a != best
             and w.nxt[si, a] != si]
    a = min(cands, key=lambda x: float(P[si][x]))
    return w.cells[w.nxt[si, a]]


def gen_episode(w, cls, rng, np):
    """Ground-truth generation per class. Returns (path, meta)."""
    if cls == "no_anomaly":
        path = [START]
        while path[-1] != GOAL and len(path) < MAXLEN:
            path.append(policy_step(w, GOAL, path[-1], rng, np))
        return path, {}
    if cls in ("unexplained", "secondary"):
        p1 = greedy_path(w, WAYPOINT, START, np)
        p2 = greedy_path(w, GOAL, WAYPOINT, np)
        return p1 + p2[1:], {"waypoint": WAYPOINT}
    base = greedy_path(w, GOAL, START, np)
    t_err = max(3, len(base) // 3)
    if cls == "repeated":
        path = [START]
        planted = []
        step = 0
        while path[-1] != GOAL and len(path) < MAXLEN:
            if step in (t_err, t_err + 1, t_err + 6, t_err + 7,
                        t_err + 12, t_err + 13) and \
                    w.avail[w.idx[path[-1]], BIAS_ACT]:
                path.append(off_policy_step(w, GOAL, path[-1], rng, np,
                                            forced_act=BIAS_ACT))
                planted.append(len(path) - 2)
            else:
                si = w.idx[path[-1]]
                w.soft_vi(GOAL, BETA)
                a = int(np.argmax(w._PI[(GOAL, round(BETA, 6))][si]))
                path.append(w.cells[w.nxt[si, a]])
            step += 1
        return path, {"planted": planted}
    # single-error classes share the prefix + a planted WRONG TURN (three worst steps)
    prefix = base[:t_err + 1]
    seg = [prefix[-1]]
    for _ in range(3):
        seg.append(off_policy_step(w, GOAL, seg[-1], rng, np))
    err_cell = seg[-1]
    path = prefix + seg[1:]
    if cls == "repaired":
        path = path + seg[-2::-1] + greedy_path(w, GOAL, prefix[-1], np)[1:]
    elif cls == "concealed":
        path = path + greedy_path(w, GOAL, err_cell, np)[1:]
    elif cls == "unnoticed":
        # open-loop: replay the remaining PRE-error action deltas from the new cell
        deltas = [(b[0] - a[0], b[1] - a[1]) for a, b in zip(base[t_err:], base[t_err + 1:])]
        cur = err_cell
        for dx, dy in deltas:
            n = (cur[0] + dx, cur[1] + dy)
            if n not in w.idx:
                break
            path.append(n)
            cur = n
    return path[:MAXLEN], {"planted": [t_err]}


def mid_steps(target_lp, thr_mid):
    return [t for t, v in enumerate(target_lp) if v < thr_mid]


def low_steps(w, target_lp, thr_hard, thr_run):
    """Anomaly steps: any step below the hard episode-calibrated threshold, plus every
    step inside a run of three or more consecutive steps below the soft per-step
    threshold (the detour detector; a sustained mild deviation is low-likelihood as a
    SEQUENCE even when no single step is extreme — v3 iteration note)."""
    low = {t for t, v in enumerate(target_lp) if v < thr_hard}
    run = []
    for t, v in enumerate(target_lp):
        if v < thr_run:
            run.append(t)
        else:
            if len(run) >= 4:
                low.update(run)
            run = []
    if len(run) >= 4:
        low.update(run)
    return sorted(low)


def _lp_via(w, waypoint, path, thr_hard, thr_run):
    """Combined low-step count for the goal-via-waypoint account; huge on unusable."""
    try:
        k = path.index(waypoint)
        if k < 3 or k >= len(path) - 1:
            return 10 ** 9, k
        lp = list(w.step_logp(waypoint, BETA, path[:k + 1])) + \
             list(w.step_logp(GOAL, BETA, path[k:]))
        return len(low_steps(w, lp, thr_hard, thr_run)), k
    except (ValueError, AssertionError):
        return 10 ** 9, -1


def classify(w, path, np, thr_hard, thr_run, thr_mid, declared_waypoint=None):
    """The ruler: locate anomaly steps under the declared account, then classify
    handling by post-anomaly structure. Returns (label, evidence)."""
    if declared_waypoint is not None:
        n_low, _ = _lp_via(w, declared_waypoint, path, thr_hard, thr_run)
        if n_low == 10 ** 9:
            n_low = len(low_steps(w, w.step_logp(GOAL, BETA, path), thr_hard, thr_run))
        return ("no_anomaly" if n_low == 0 else "unexplained"), {"n_low": int(n_low)}
    lp = w.step_logp(GOAL, BETA, path)
    low = low_steps(w, lp, thr_hard, thr_run)
    # 1. recurrence first: the same action delta at mid-low steps in two or more
    #    SEPARATED clusters (a wrong turn is one consecutive cluster and must not fire
    #    this; habit recurs with clean stretches between -- the v5 separation rule)
    mids = mid_steps(lp, thr_mid)
    deltas = {t: (path[t + 1][0] - path[t][0], path[t + 1][1] - path[t][1])
              for t in mids}
    from collections import Counter
    for delta, n in Counter(deltas.values()).most_common(2):
        ts = sorted(t for t, d in deltas.items() if d == delta)
        clusters = 1 + sum(1 for a, b in zip(ts, ts[1:]) if b - a > 2)
        if n >= 3 and clusters >= 2:
            return "repeated", {"delta": list(delta), "n": int(n),
                                "clusters": int(clusters)}
    if not low:
        return "no_anomaly", {}
    # 2. ordering account: some visited cell between the first low step and the end
    #    cleans EVERY step, with a detour of at least three steps
    t0 = low[0]
    t_end = t0
    while t_end + 1 in low:
        t_end += 1                     # the anomaly CLUSTER; handling begins after it
    for cand in dict.fromkeys(path[t0 + 1:-1]):          # visit order, deduped
        n_low2, k = _lp_via(w, cand, path, thr_hard, thr_run)
        if n_low2 == 0:
            return "unexplained", {"waypoint_account": list(cand), "at": int(k)}
    # 3. repair: a return to the pre-anomaly cell shortly after the cluster ends
    pre = path[t0]
    if pre in path[t_end + 2:t_end + 5]:
        return "repaired", {"backtrack_to": list(pre)}
    # 4. unnoticed vs concealed: arrival plus continuation adaptivity AFTER the cluster
    post = path[t_end + 2:]
    if len(post) < 3:
        return "abstain", {"reason": "too little post-anomaly evidence"}
    arrived = path[-1] == GOAL
    lp_post = w.step_logp(GOAL, BETA, post)
    n_low_post = len(low_steps(w, lp_post, thr_hard, thr_run))
    if not arrived or n_low_post >= 2:
        return "unnoticed", {"arrived": bool(arrived), "n_low_post": n_low_post}
    if n_low_post == 0:
        return "concealed", {"post_clean": True, "arrived": bool(arrived)}
    return "abstain", {"reason": "post-anomaly evidence mixed"}


def main() -> None:
    import numpy as np
    w = build_world(np)
    # threshold population: DISJOINT clean walks (never scored). Episode-level null:
    # the q05 of each clean episode's MINIMUM per-step logp, so a clean episode crosses
    # the threshold at a 0.05 rate by construction (the no-signal gate's own calibration)
    rng0 = np.random.default_rng(SEED - 1)
    mins, pooled, null_paths = [], [], []
    for _ in range(N_NULL):
        path = [START]
        while path[-1] != GOAL and len(path) < MAXLEN:
            path.append(policy_step(w, GOAL, path[-1], rng0, np))
        lp = w.step_logp(GOAL, BETA, path)
        mins.append(float(np.min(lp)))
        pooled.extend(lp.tolist())
        null_paths.append(path)
    thr_hard = float(np.quantile(mins, 0.03))
    thr_run = float(np.quantile(pooled, 0.15))
    thr_mid = float(np.quantile(pooled, 0.005))
    # the combined false-episode rate, measured on the same disjoint null sample
    null_flagged = sum(1 for p in null_paths
                       if low_steps(w, w.step_logp(GOAL, BETA, p), thr_hard, thr_run))
    null_false_rate = round(null_flagged / N_NULL, 4)

    rows = []
    for ci, cls in enumerate(CLASSES):
        for i in range(N_PER):
            rng = np.random.default_rng(SEED + ci * 1000 + i)
            path, meta = gen_episode(w, cls, rng, np)
            if cls == "secondary":
                lab_w, ev_w = classify(w, path, np, thr_hard, thr_run, thr_mid)
                lab_d, ev_d = classify(w, path, np, thr_hard, thr_run, thr_mid,
                                       declared_waypoint=WAYPOINT)       # declared
                rows.append({"cls": cls, "i": i, "label_withheld": lab_w,
                             "label_declared": lab_d, "n_steps": len(path)})
            else:
                lab, ev = classify(w, path, np, thr_hard, thr_run, thr_mid)
                rows.append({"cls": cls, "i": i, "label": lab, "evidence": ev,
                             "n_steps": len(path)})

    def rate(cls, pred, key="label"):
        sel = [r for r in rows if r["cls"] == cls]
        return round(sum(1 for r in sel if r.get(key) == pred) / max(len(sel), 1), 4)

    conf = {c: {p: rate(c, p) for p in CLASSES[:6] + ["abstain"]}
            for c in CLASSES[:6]}
    err_classes = ("unnoticed", "repaired", "concealed", "repeated")
    gates = {
        "no_signal": {"clean_or_abstain": round(
            rate("no_anomaly", "no_anomaly") + rate("no_anomaly", "abstain"), 4),
            "threshold": 0.95},
        "unfamiliar_order": {"labeled_error": round(sum(
            rate("unexplained", e) for e in err_classes), 4), "threshold": 0.05,
            "direction": "UP = projection failure"},
        "known_answer": {c: rate(c, c) for c in CLASSES[:6]},
        "repair_vs_concealment": {"repaired_as_concealed": rate("repaired", "concealed"),
                                  "concealed_as_repaired": rate("concealed", "repaired"),
                                  "threshold": 0.20},
        "recurrence": {"repeated_as_unexplained": rate("repeated", "unexplained")},
        "context": {"flips_to_clean_when_declared": rate(
            "secondary", "no_anomaly", key="label_declared"),
            "unexplained_when_withheld": rate(
            "secondary", "unexplained", key="label_withheld"), "threshold": 0.80},
    }
    passes = {
        "no_signal": gates["no_signal"]["clean_or_abstain"] >= 0.95,
        "unfamiliar_order": gates["unfamiliar_order"]["labeled_error"] <= 0.05,
        "known_answer": all(v > 1 / 7 for v in gates["known_answer"].values()),
        "repair_vs_concealment":
            gates["repair_vs_concealment"]["repaired_as_concealed"] <= 0.20
            and gates["repair_vs_concealment"]["concealed_as_repaired"] <= 0.20,
        "recurrence": gates["recurrence"]["repeated_as_unexplained"] <= 0.05,
        "context": gates["context"]["flips_to_clean_when_declared"] >= 0.80,
    }
    verdict = "RULER-PASSES" if all(passes.values()) else "RULER-FAILS"
    out = {"prereg": "runner docstring DESIGN CHECK", "seed": SEED, "beta": BETA,
           "n_per_class": N_PER, "thr_hard_episode_q05": thr_hard,
           "thr_run_step_q15": thr_run, "thr_mid_step_q005": thr_mid,
           "null_false_episode_rate_measured": null_false_rate,
           "confusion": conf, "gates": gates, "gate_passes": passes,
           "verdict": verdict,
           "license": ("2.2D text battery is licensed" if all(passes.values()) else
                       "2.2D does NOT proceed; failed distinctions retire or redesign")}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ruler.json").write_text(json.dumps(out, indent=1),
                                    encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("gates", "gate_passes", "verdict")}, indent=1))


if __name__ == "__main__":
    main()
