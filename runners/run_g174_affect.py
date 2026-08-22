"""G174 causal affect ruler — fit emotion directions on explicit sentences, decode scrubbed
situations, then amplify/ablate fear and joy during continuation reading and watch a benign
approach/withdraw preference. Card: prereg/g174.py (frozen; all stimuli live there).

Output: results/g174/ruler.json (both seeds, all gates, band). GPU; lock once.
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from prereg.g174 import (ACTOR_FRAMES, ALPHA_P, BANDS, CAPABILITY_TOL,           # noqa: E402
                         CAUSAL_PREDICTIONS, CONCEPTS, CONTROL_RATIO,
                         DEV_PER_CONCEPT, DOSES, MODEL, N_PERMUTATIONS,
                         N_SHUFFLES, NEUTRAL_PASSAGES, SCENARIOS, SCRUBBED,
                         SEED_A, SEED_B, TRANSFER_TOL, assert_lexicon_clean,
                         explicit_sentences)
from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock              # noqa: E402
from soundingline.probe.conditional_reader import artifact_logprob, load_reader  # noqa: E402
from soundingline.probe.interventions import SubspaceIntervention, get_blocks    # noqa: E402

OUT = REPO / "results" / "g174"


def pooled_states(model, tok, texts: list[str]) -> np.ndarray:
    """(n_texts, n_blocks, d) mean-pooled block outputs."""
    rows = []
    for t in texts:
        enc = tok(t, return_tensors="pt", add_special_tokens=False).to("cuda")
        with torch.no_grad():
            hs = model(**enc, output_hidden_states=True).hidden_states[1:]
        rows.append(np.stack([h[0].mean(0).float().cpu().numpy() for h in hs]))
    return np.stack(rows)


def fit_dirs(X: np.ndarray, labels: list[int], n_classes: int):
    """Per block: class-mean minus grand-mean directions (unit norm) and the grand mean."""
    mu = X.mean(0)                                             # (blocks, d)
    dirs = np.zeros((n_classes, X.shape[1], X.shape[2]))
    for c in range(n_classes):
        d = X[[i for i, l in enumerate(labels) if l == c]].mean(0) - mu
        dirs[c] = d / (np.linalg.norm(d, axis=-1, keepdims=True) + 1e-9)
    return dirs, mu


def decode_acc(dirs, mu, X, labels, block: int) -> float:
    proj = np.einsum("nd,cd->nc", X[:, block] - mu[block], dirs[:, block])
    return float((proj.argmax(1) == np.array(labels)).mean())


def pref(model, tok, scenario: str, approach: str, withdraw: str, iv) -> float:
    """log P(withdraw | scenario) - log P(approach | scenario), per-token means."""
    lw, _, _ = artifact_logprob(model, tok, scenario, withdraw, intervention=iv)
    la, _, _ = artifact_logprob(model, tok, scenario, approach, intervention=iv)
    return lw - la


def perm_p(diffs: list[float], seed: int) -> float:
    rng = random.Random(seed)
    obs = sum(diffs) / len(diffs)
    ge = sum(1 for _ in range(N_PERMUTATIONS)
             if abs(sum(d * rng.choice((1, -1)) for d in diffs) / len(diffs)) >= abs(obs))
    return (ge + 1) / (N_PERMUTATIONS + 1)


def run_seed(model, tok, seed: int) -> dict:
    rng = random.Random(seed)
    n_c = len(CONCEPTS)

    exp_texts, exp_labels = [], []
    for ci, c in enumerate(CONCEPTS):
        for s in explicit_sentences(c):
            exp_texts.append(s)
            exp_labels.append(ci)
    dev_t, dev_l, test_t, test_l = [], [], [], []
    for ci, c in enumerate(CONCEPTS):
        idx = list(range(len(SCRUBBED[c])))
        rng.shuffle(idx)
        for j in idx[:DEV_PER_CONCEPT]:
            dev_t.append(SCRUBBED[c][j]); dev_l.append(ci)
        for j in idx[DEV_PER_CONCEPT:]:
            test_t.append(SCRUBBED[c][j]); test_l.append(ci)

    X_exp = pooled_states(model, tok, exp_texts)
    X_dev = pooled_states(model, tok, dev_t)
    X_test = pooled_states(model, tok, test_t)
    dirs, mu = fit_dirs(X_exp, exp_labels, n_c)

    n_blocks = X_exp.shape[1]
    dev_accs = [decode_acc(dirs, mu, X_dev, dev_l, b) for b in range(n_blocks)]
    block = int(np.argmax(dev_accs))
    test_acc = decode_acc(dirs, mu, X_test, test_l, block)

    frame_accs = []
    for frame in ACTOR_FRAMES[1:]:
        X_f = pooled_states(model, tok, [frame + t for t in test_t])
        frame_accs.append(decode_acc(dirs, mu, X_f, test_l, block))

    null_accs = []
    for _ in range(N_SHUFFLES):
        sh = exp_labels[:]
        rng.shuffle(sh)
        d_sh, mu_sh = fit_dirs(X_exp, sh, n_c)
        null_accs.append(decode_acc(d_sh, mu_sh, X_test, test_l, block))
    null95 = float(np.quantile(null_accs, 0.95))

    from sklearn.feature_extraction.text import CountVectorizer                  # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression                          # noqa: PLC0415
    vec = CountVectorizer(lowercase=True)
    lr = LogisticRegression(max_iter=2000, random_state=seed)
    lr.fit(vec.fit_transform(exp_texts), exp_labels)
    lex_acc = float(lr.score(vec.transform(test_t), test_l))

    decoding_pass = test_acc > null95 and test_acc > lex_acc
    transfer_pass = all(abs(a - test_acc) <= TRANSFER_TOL for a in frame_accs)

    # causal half — fear and joy directions at the chosen block
    scen = list(SCENARIOS)
    rng.shuffle(scen)
    dev_sc, test_sc = scen[:4], scen[4:]
    d_model = X_exp.shape[2]
    base = {i: pref(model, tok, *s, iv=None) for i, s in enumerate(test_sc)}
    causal = {}
    for concept in CAUSAL_PREDICTIONS:
        ci = CONCEPTS.index(concept)
        u = torch.tensor(dirs[ci, block], dtype=torch.float32).reshape(d_model, 1)
        m = torch.tensor(mu[block], dtype=torch.float32)
        want_withdraw = CAUSAL_PREDICTIONS[concept] == "withdraw"

        def effect(iv) -> list[float]:
            return [pref(model, tok, *s, iv=iv) - base[i] for i, s in enumerate(test_sc)]

        dose = None
        for a in DOSES:
            iv = SubspaceIntervention({block: u}, {block: m}, alpha=a, mode="amplify")
            dev_eff = [pref(model, tok, *s, iv=iv) - pref(model, tok, *s, iv=None)
                       for s in dev_sc]
            if abs(sum(dev_eff) / len(dev_eff)) > 1e-4:
                dose = a
                break
        dose = dose or DOSES[-1]

        amp = SubspaceIntervention({block: u}, {block: m}, alpha=dose, mode="amplify")
        abl = SubspaceIntervention({block: u}, {block: m}, alpha=1.0, mode="ablate")
        e_amp, e_abl = effect(amp), effect(abl)
        sgn = 1.0 if want_withdraw else -1.0     # positive pref = withdraw-leaning
        amp_mean = sgn * sum(e_amp) / len(e_amp)
        abl_mean = sgn * sum(e_abl) / len(e_abl)
        p_amp = perm_p(e_amp, seed + 31 + ci)
        p_abl = perm_p(e_abl, seed + 61 + ci)

        g = torch.Generator().manual_seed(seed + 97 + ci)
        u_rand = torch.randn(d_model, 1, generator=g)
        sh_labels = exp_labels[:]
        rng.shuffle(sh_labels)
        d_sh, mu_sh = fit_dirs(X_exp, sh_labels, n_c)
        u_shuf = torch.tensor(d_sh[ci, block], dtype=torch.float32).reshape(d_model, 1)
        e_rand = effect(SubspaceIntervention({block: u_rand}, {block: m}, dose, "amplify"))
        e_shuf = effect(SubspaceIntervention({block: u_shuf}, {block: m}, dose, "amplify"))
        ctrl_quiet = (abs(sum(e_rand)) / len(e_rand) < CONTROL_RATIO * abs(amp_mean)
                      and abs(sum(e_shuf)) / len(e_shuf) < CONTROL_RATIO * abs(amp_mean))

        cap_base = [artifact_logprob(model, tok, "Text follows.", p)[0]
                    for p in NEUTRAL_PASSAGES]
        cap_amp = [artifact_logprob(model, tok, "Text follows.", p, intervention=amp)[0]
                   for p in NEUTRAL_PASSAGES]
        cap_change = abs(sum(cap_amp) / len(cap_amp) - sum(cap_base) / len(cap_base)) \
            / abs(sum(cap_base) / len(cap_base))

        causal[concept] = {
            "dose": dose, "amp_mean_signed": amp_mean, "abl_mean_signed": abl_mean,
            "p_amp": p_amp, "p_abl": p_abl,
            "sign_pair": amp_mean > 0 and p_amp < ALPHA_P and abl_mean < 0,
            "controls_quiet": ctrl_quiet, "capability_change": cap_change,
            "capability_pass": cap_change < CAPABILITY_TOL,
        }

    return {"seed": seed, "block": block, "dev_acc": dev_accs[block],
            "test_acc": test_acc, "frame_accs": frame_accs, "null95": null95,
            "lexical_acc": lex_acc, "decoding_pass": decoding_pass,
            "transfer_pass": transfer_pass, "causal": causal}


def band_of(seeds: list[dict]) -> str:
    if any(not all(c["capability_pass"] for c in s["causal"].values()) for s in seeds):
        return "INSTRUMENT-FAIL"
    dec = all(s["decoding_pass"] for s in seeds)
    trans = all(s["transfer_pass"] for s in seeds)
    ctrl = all(c["controls_quiet"] for s in seeds for c in s["causal"].values())
    sign = all(c["sign_pair"] for s in seeds for c in s["causal"].values())
    if not dec or not trans:
        return "LEXICAL-ONLY"       # the card folds a transfer failure into this band
    if not ctrl:
        return "GENERIC"
    if sign:
        return "RULER-STANDS"
    return "DECODES-ONLY"


def main() -> int:
    assert_lexicon_clean()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    acquire_gpu_lock("g174_affect")
    try:
        model, tok = load_reader(MODEL, device="cuda", dtype="float16")
        n_blocks = len(get_blocks(model))
        print(f"{MODEL}: {n_blocks} blocks")
        seeds = [run_seed(model, tok, SEED_A), run_seed(model, tok, SEED_B)]
    finally:
        release_gpu_lock()
    band = band_of(seeds)
    assert band in BANDS
    import transformers                                                          # noqa: PLC0415
    (OUT / "ruler.json").write_text(json.dumps({
        "prereg": "prereg/g174.py", "model": MODEL, "band": band, "seeds": seeds,
        "minutes": round((time.time() - t0) / 60, 1),
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__},
    }, indent=1), encoding="utf-8", newline="\n")
    print(f"BAND: {band}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
