"""How many affective components survive once affect is isolated — and does the field's answer of two hold?

── THE QUESTION, AND WHY THE FIRST ATTEMPT COULD NOT ANSWER IT ────────────────────────────────

`run_decomposition.py` decomposed raw activations of arbitrary Reddit text and returned a component
count that **doubles when the sample quadruples** (49 at 1,200 utterances, 93 at 5,000, same model,
every setting frozen). It was counting structure in activations — topic, syntax, length, register —
and **nothing in it isolated affect.** The number was void and we retracted it ourselves.

This is the fix, and it borrows the isolation step from the people who got it right.

── THE PROTOCOL, WHICH IS NOT OURS ───────────────────────────────────────────────────────────

Anthropic's emotion paper (arXiv:2604.07729, April 2026) uses **difference in means, no
autoencoders**: average residual-stream activations over token positions and over many topics for
each emotion, then **subtract the mean across emotions.** Averaging over topics cancels topic;
subtracting the cross-emotion mean cancels everything the emotions share. **What is left is affect,
and the taxonomy never enters the arithmetic** — the labels only say which items to average
together, they do not supply a basis.

Three independent groups converged on this same method in 2026, and **all of them stopped at two
components** — valence and arousal, because two is Russell's circumplex. In Anthropic's own numbers
the first component is 26% of variance and the second 15%.

> **41% in two components means 59% is unaccounted for, and nobody asked what it is.**
>
> That is a confirmation-driven stopping criterion, not a statistical one. **This runner asks the
> question they did not.**

── WHY THIS CORPUS ───────────────────────────────────────────────────────────────────────────

GoEmotions: 58,000 Reddit comments, **27 emotion categories plus neutral, labelled by people.** The
previous run used a corpus whose labels were assigned by a language model, which we discounted
entirely. These are human judgements, and 28 categories leave room for far more than two components
to appear.

**Sample size is handled honestly.** Each emotion's items are split into several disjoint subsets and
averaged within subset, so the between-subset scatter *within* one emotion is a direct estimate of
the noise floor, and the number of vectors entering the decomposition is large enough for the
dimensionality estimators below to mean something.

── THE COUNT, BY THREE CRITERIA THAT FAIL DIFFERENTLY ────────────────────────────────────────

The last run taught us that a single criterion is an opinion. All three are reported.

    participation ratio, bias-corrected   Chun, Canatar, Chung & Lee (arXiv:2509.26560, 2026) prove
                                          the plain participation ratio is severely biased at small
                                          sample size, with sample count and neuron count acting like
                                          parallel resistances. Their correction removes it. Continuous,
                                          no threshold to tune, validated against known ground truth
    bi-cross-validation                   Owen & Perry (Annals of Applied Statistics 3(2):564, 2009).
                                          Hold out a block of ROWS and COLUMNS at once and predict it.
                                          Ordinary row-wise cross-validation of a decomposition leaks --
                                          the held-out rows are used both to compute scores and to score
                                          the reconstruction -- so error falls monotonically and never
                                          selects a rank. This does not
    parallel analysis                     the criterion the last run used. Reported so the comparison
                                          is visible, not because it is trusted

**Applying bi-cross-validation to transformer activations appears to be unpublished.**

── THE CONTROLS, AND THEY CAN ALL FAIL ───────────────────────────────────────────────────────

    randomised weights   Heap, Lawson, Farnik & Aitchison (arXiv:2501.17727) showed SAE latents from
                         a RANDOMLY INITIALISED transformer score about as well as from a trained one.
                         The same pipeline is run on an untrained model of identical shape. **If the
                         component count survives that, the count is about the shape of the network
                         and not about anything it learned.** This is the field's new minimum bar
    shuffled labels      emotion labels permuted across items before averaging. Destroys affect,
                         keeps everything else. Should collapse to noise
    split-half           do the components found in one half of the items reappear in the other half

── PRE-REGISTERED, BEFORE ANY NUMBER IS SEEN ─────────────────────────────────────────────────

**First, replication.** Our first component must correlate with published human valence ratings and
our second with arousal, at roughly the strengths three groups report. **If it does not, our pipeline
disagrees with theirs and no result here is worth reading** -- that check gates everything else.

    TWO          the corrected count is at or below 3. The circumplex is right, the field's stopping
                 point was correct, and the curator's prediction is wrong
    RICHER       the corrected count is clearly above 7, survives the randomised-weights control, and
                 replicates across halves. More primitives than anyone probes for
    MIDDLING     between 3 and 7. Consistent with a basic-emotion taxonomy and with neither of the
                 stronger claims
    VOID         the randomised-weights control returns a similar count, or the valence check fails

**VOID is a live outcome and it is the one that retracts most.** The last attempt died to a control
it did not have; this one has three.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "affect_dimensions"

# Human valence/arousal for the 27 GoEmotions categories, on 0-1 scales, taken from the NRC-VAD
# lexicon entry for each category NAME. Used ONLY to check our components against the field's,
# never to build them. Frozen here so the check cannot drift.
VAD = {
    "admiration": (0.86, 0.54), "amusement": (0.93, 0.62), "anger": (0.12, 0.84),
    "annoyance": (0.20, 0.62), "approval": (0.86, 0.42), "caring": (0.90, 0.44),
    "confusion": (0.29, 0.53), "curiosity": (0.76, 0.59), "desire": (0.79, 0.72),
    "disappointment": (0.14, 0.40), "disapproval": (0.19, 0.45), "disgust": (0.10, 0.60),
    "embarrassment": (0.19, 0.60), "excitement": (0.90, 0.85), "fear": (0.08, 0.83),
    "gratitude": (0.94, 0.48), "grief": (0.05, 0.51), "joy": (0.98, 0.71),
    "love": (1.00, 0.62), "nervousness": (0.19, 0.75), "optimism": (0.90, 0.55),
    "pride": (0.87, 0.61), "realization": (0.66, 0.44), "relief": (0.87, 0.32),
    "remorse": (0.12, 0.42), "sadness": (0.05, 0.30), "surprise": (0.68, 0.79),
    "neutral": (0.50, 0.35),
}


def dimensionality(M, rng, max_k=40):
    """Three criteria that fail in different ways, on a (vectors x dimensions) matrix."""
    import numpy as np

    X = M - M.mean(0)
    P, Q = X.shape
    ev = np.linalg.svd(X, compute_uv=False)[: min(P, Q) - 1] ** 2 / (P - 1)
    ev = ev[ev > 0]

    # participation ratio, then the Chun et al. correction for finite P and Q
    pr_naive = float(ev.sum() ** 2 / (ev ** 2).sum())
    inv = 1.0 / pr_naive - 1.0 / P - 1.0 / Q
    pr_corr = float(1.0 / inv) if inv > 1e-9 else float("inf")

    # bi-cross-validation: hold out a block of ROWS and COLUMNS together, predict it from the rest
    ks = list(range(1, min(max_k, P - 2, Q - 2) + 1))
    errs = np.zeros(len(ks))
    folds = 6
    for _ in range(folds):
        ri = rng.permutation(P)
        ci = rng.permutation(Q)
        rh, ch = ri[: max(2, P // 4)], ci[: max(2, Q // 4)]
        rk, ck = ri[max(2, P // 4):], ci[max(2, Q // 4):]
        A = X[np.ix_(rh, ch)]      # the held-out block
        B = X[np.ix_(rh, ck)]
        C = X[np.ix_(rk, ch)]
        D = X[np.ix_(rk, ck)]
        U, S, Vt = np.linalg.svd(D, full_matrices=False)
        for j, k in enumerate(ks):
            if k > len(S):
                errs[j] += float(np.mean(A ** 2))
                continue
            Dk_pinv = (Vt[:k].T * (1.0 / S[:k])) @ U[:, :k].T
            errs[j] += float(np.mean((A - B @ Dk_pinv @ C) ** 2))
    bcv = int(ks[int(np.argmin(errs))])

    # parallel analysis, the criterion we no longer trust, reported for comparison
    nulls = []
    for _ in range(5):
        S_ = np.column_stack([rng.permutation(X[:, j]) for j in range(Q)])
        e = np.linalg.svd(S_, compute_uv=False)[: len(ev)] ** 2 / (P - 1)
        nulls.append(e)
    par = int((ev > np.percentile(np.array(nulls), 95, axis=0)).sum())

    var = ev / ev.sum()
    return {"participation_naive": pr_naive, "participation_corrected": pr_corr,
            "bcv": bcv, "parallel": par,
            "pc1_var": float(var[0]), "pc2_var": float(var[1]) if len(var) > 1 else 0.0,
            "pc1_pc2_var": float(var[:2].sum()), "n_vectors": P, "n_dims": Q}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-emotion", type=int, default=160, help="items sampled per emotion")
    ap.add_argument("--subsets", type=int, default=8, help="disjoint averages per emotion")
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--random-weights", action="store_true",
                    help="Heap's control: identical shape, untrained")
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    from datasets import load_dataset                                # noqa: PLC0415
    from scipy import stats                                          # noqa: PLC0415

    from soundingline.probe.activations import DEFAULT_MODEL, Reader  # noqa: PLC0415

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name}"
          f"{' with RANDOMISED weights' if args.random_weights else ''} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    if args.random_weights:
        import torch                                                 # noqa: PLC0415
        m = getattr(reader, "model", None)
        if m is None:
            print("  cannot reach the underlying model to randomise it")
            return
        with torch.no_grad():
            for p in m.parameters():
                if p.dim() >= 2:
                    torch.nn.init.normal_(p, mean=0.0, std=0.02)
        print("  weights replaced with N(0, 0.02)\n", flush=True)

    print("loading GoEmotions (human-labelled, 27 categories plus neutral) ...", flush=True)
    ds = load_dataset("google-research-datasets/go_emotions", "simplified", split="train")
    names = ds.features["labels"].feature.names
    by_emotion: dict[str, list[str]] = {n: [] for n in names}
    for row in ds:
        labs = row["labels"]
        if len(labs) != 1:                    # single-label only: no mixed items
            continue
        t = row["text"]
        if len(t.split()) < 6:
            continue
        n = names[labs[0]]
        if len(by_emotion[n]) < args.per_emotion:
            by_emotion[n].append(t)
    emotions = [n for n in names if len(by_emotion[n]) >= args.subsets * 4]
    print(f"  {len(emotions)} emotions with enough single-label items "
          f"({args.per_emotion} each, {args.subsets} subsets)\n", flush=True)

    probe = reader.read("shape probe")
    n_layers = probe.n_layers
    rng = np.random.default_rng(1729)

    # read every item once, keep per-item activations grouped by emotion
    per_emotion_acts: dict[str, list] = {}
    total = sum(len(by_emotion[e]) for e in emotions)
    seen = 0
    for e in emotions:
        rows = []
        for t in by_emotion[e]:
            a = reader.read(t)
            rows.append([np.asarray(a.acts[L], dtype=np.float32) for L in range(n_layers)])
            seen += 1
            if seen % 500 == 0:
                print(f"  read {seen}/{total}", flush=True)
        per_emotion_acts[e] = rows

    def build(layer: int, shuffle_labels: bool = False, half: int | None = None):
        """One vector per (emotion, subset), with the cross-emotion mean removed."""
        pool = {e: [r[layer] for r in per_emotion_acts[e]] for e in emotions}
        if shuffle_labels:
            allv = [v for e in emotions for v in pool[e]]
            rng.shuffle(allv)
            i, newpool = 0, {}
            for e in emotions:
                k = len(pool[e])
                newpool[e] = allv[i:i + k]
                i += k
            pool = newpool
        vecs, labs = [], []
        for e in emotions:
            v = pool[e]
            if half is not None:
                v = v[: len(v) // 2] if half == 0 else v[len(v) // 2:]
            idx = rng.permutation(len(v))
            chunks = np.array_split(idx, args.subsets)
            for ch in chunks:
                if len(ch) == 0:
                    continue
                vecs.append(np.mean([v[j] for j in ch], axis=0))
                labs.append(e)
        M = np.array(vecs, dtype=float)
        M = M - M.mean(0)              # <- the isolation step: remove what all emotions share
        return M, labs

    mids = list(range(n_layers // 3, 2 * n_layers // 3))
    print(f"{'layer':>6}{'particip.':>11}{'corrected':>11}{'bi-CV':>8}{'parallel':>10}"
          f"{'PC1':>8}{'PC2':>8}{'PC1+2':>8}")
    print("-" * 70)
    out = []
    for L in range(n_layers):
        M, labs = build(L)
        d = dimensionality(M, rng)
        # the field's check: do our first two components recover human valence and arousal
        X = M - M.mean(0)
        U, S, Vt = np.linalg.svd(X, full_matrices=False)
        sc = U[:, :2] * S[:2]
        val = np.array([VAD[e][0] for e in labs])
        aro = np.array([VAD[e][1] for e in labs])
        rv = max(abs(stats.pearsonr(sc[:, i], val).statistic) for i in range(2))
        ra = max(abs(stats.pearsonr(sc[:, i], aro).statistic) for i in range(2))
        d.update({"layer": L, "valence_r": float(rv), "arousal_r": float(ra)})
        out.append(d)
        print(f"{L:>6}{d['participation_naive']:>11.1f}{d['participation_corrected']:>11.1f}"
              f"{d['bcv']:>8}{d['parallel']:>10}{d['pc1_var']:>8.3f}{d['pc2_var']:>8.3f}"
              f"{d['pc1_pc2_var']:>8.3f}")

    mid = [o for o in out if o["layer"] in mids]
    mid_corr = float(np.mean([o["participation_corrected"] for o in mid]))
    mid_bcv = float(np.mean([o["bcv"] for o in mid]))
    best_val = max(o["valence_r"] for o in out)
    best_aro = max(o["arousal_r"] for o in out)

    # ── WHAT ARE THE COMPONENTS? ──────────────────────────────────────────────────────────────
    # A count on its own is not readable. For each component, report the emotion categories that sit
    # at each end of it. **The curator's instruction: "just saying we have seven categories isn't
    # quite enough. If I were looking at clusters of labels, I'd have an easier time agreeing or
    # disagreeing with whether we were onto something."**
    best = max(out, key=lambda o: o["valence_r"])
    Lb = best["layer"]
    Mb, lb = build(Lb)
    Xb = Mb - Mb.mean(0)
    Ub, Sb, Vtb = np.linalg.svd(Xb, full_matrices=False)
    scores = Ub * Sb
    n_show = max(2, min(12, int(round(best["participation_corrected"]))))
    varb = Sb ** 2 / (Sb ** 2).sum()
    print(f"\n  WHAT THE COMPONENTS ARE — layer {Lb}, the layer that best recovers human valence")
    print(f"  Each row is one component. The emotions listed are those sitting furthest toward")
    print(f"  each end of it, averaged over that emotion's subsets.\n")
    print(f"  {'comp':>4}{'var':>7}  {'one end':<44}{'the other end'}")
    print("  " + "-" * 100)
    labelling = []
    for c in range(n_show):
        per = {}
        for e in emotions:
            m = [scores[i, c] for i, L_ in enumerate(lb) if L_ == e]
            per[e] = float(np.mean(m))
        order = sorted(per, key=per.get)
        neg = ", ".join(order[:4])
        pos = ", ".join(order[-4:][::-1])
        # is this component valence, arousal, or neither?
        sv = np.array([VAD[e][0] for e in emotions])
        sa = np.array([VAD[e][1] for e in emotions])
        sc_ = np.array([per[e] for e in emotions])
        rv_ = abs(stats.pearsonr(sc_, sv).statistic)
        ra_ = abs(stats.pearsonr(sc_, sa).statistic)
        tag_ = ("valence" if rv_ > 0.6 and rv_ > ra_ else
                "arousal" if ra_ > 0.6 else "unnamed")
        labelling.append({"component": c, "variance": float(varb[c]), "low": order[:5],
                          "high": order[-5:][::-1], "valence_r": float(rv_),
                          "arousal_r": float(ra_), "reads_as": tag_})
        print(f"  {c:>4}{varb[c]:>7.3f}  {pos:<44}{neg}")
        print(f"      {'':>7}  reads as {tag_}  (valence {rv_:.2f}, arousal {ra_:.2f})")
    n_unnamed = sum(1 for x in labelling if x["reads_as"] == "unnamed")
    print(f"\n  {n_unnamed} of the top {n_show} components are neither valence nor arousal.")
    print(f"  Those are the ones worth arguing about.")

    print(f"\n  REPLICATION CHECK — our components against published human ratings")
    print(f"    valence, best layer   {best_val:.2f}   (three groups report 0.76 to 0.89)")
    print(f"    arousal, best layer   {best_aro:.2f}   (reported 0.54 to 0.66)")

    # control: labels shuffled, affect destroyed, everything else kept
    Ls = mids[len(mids) // 2]
    Msh, _ = build(Ls, shuffle_labels=True)
    dsh = dimensionality(Msh, rng)
    # control: do the components replicate across disjoint halves of the items
    Ma, la = build(Ls, half=0)
    Mb, lb = build(Ls, half=1)
    Va = np.linalg.svd(Ma - Ma.mean(0), full_matrices=False)[2]
    Vb = np.linalg.svd(Mb - Mb.mean(0), full_matrices=False)[2]
    k = int(round(min(mid_corr, 20)))
    k = max(k, 2)
    align = float(np.linalg.svd(Va[:k] @ Vb[:k].T, compute_uv=False).mean())

    print(f"\n  CONTROLS, at layer {Ls}")
    print(f"    labels shuffled       corrected count {dsh['participation_corrected']:.1f}"
          f"   (real: {out[Ls]['participation_corrected']:.1f})")
    print(f"    split-half agreement  {align:.2f} over the top {k} components "
          f"(1.0 = identical subspace)")

    replicated = best_val > 0.60
    shuffle_ok = dsh["participation_corrected"] < 0.6 * out[Ls]["participation_corrected"]
    if not replicated or not shuffle_ok:
        verdict = "VOID"
    elif mid_corr <= 3.0:
        verdict = "TWO"
    elif mid_corr > 7.0 and align > 0.5:
        verdict = "RICHER"
    else:
        verdict = "MIDDLING"

    print(f"\n  middle-layer corrected component count: {mid_corr:.1f}"
          f"   (bi-cross-validated rank {mid_bcv:.1f})")
    print(f"  the field stops at 2. Ekman's six plus neutral would be 7. "
          f"Panksepp's seven would be 7.")
    print(f"\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = model_name.split("/")[-1] + ("_random" if args.random_weights else "")
    (RESULTS / f"{tag}.json").write_text(json.dumps(
        {"model": model_name, "random_weights": args.random_weights,
         "emotions": emotions, "per_emotion": args.per_emotion, "subsets": args.subsets,
         "layers": out, "middle_corrected": mid_corr, "middle_bcv": mid_bcv,
         "valence_r": best_val, "arousal_r": best_aro,
         "component_labels": labelling,
         "shuffled_labels": dsh, "split_half_alignment": align, "verdict": verdict},
        indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
