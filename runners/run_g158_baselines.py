"""G158 — Phase 2.1.3 stage (b): cheap-baseline sweep on the G131 exploratory corpus.

Before any reader is credited with recovering choice structure from these artifacts, measure
how much of the cell structure is readable from features no one would call decision recovery.
The external audit's probe found a length-only classifier separating surface from problem
targets at 73.1% leave-one-topic-out; this stage reproduces that with the full baseline
family, each feature set alone, so every later recovery claim has the exact number it must
beat. EXPLORATORY grade, declared.

Feature sets, each its own classifier (logistic regression, leave-one-topic-out by GroupKFold
so topic can never carry the answer): length (word count alone); paragraphs (paragraph count,
mean paragraph length); punctuation (per-1000-word rates of question marks, parentheses,
semicolons, dashes, numbered-list lines, exclamations); lexical echo (share of the target
pool's content words appearing in the text, both pools scored); all combined. Tasks: target
(surface vs problem, instructed cells only) and amount (0 vs 3 vs 8, all cells).

DESIGN CHECK (2026-08-19, at design time). Lessons read: LESSONS §3 to §5, CONTROLS 6/7.
Exploratory, no gates, nothing VOIDs; expectations derived both ways anyway: under the null
(cells differ only in their instructions and the instructions left no cheap trace) every
baseline sits at its class base rate (0.5 for target on the balanced instructed cells; 0.333
balanced / observed marginal for amount); under the alternative (instruction-following leaves
gross artifacts: surface constraints shorten essays, lists and question marks are literal
instruction products) the punctuation and length arms climb well above it. Failure direction
of the instrument: OVER-crediting the baselines is the safe direction here (they are the
bar recovery must beat, so an inflated bar is conservative for later claims); the seed is
fixed and recorded; permutation p-values (label shuffle within topic, 2000 draws) are written
to disk and registered in audit_multiplicity when the landing is written through.

Output: results/g158/baselines.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "corpora" / "g131_factorial"
OUT = REPO / "results" / "g158"
SEED = 15800
N_PERM = 200      # each draw refits every fold; 200 gives p-resolution 0.005, honest floor
                  # p >= 1/201; raise with a fresh seed if a verdict ever needs finer

STOP = set("the a an and or but if of to in on for with as by at from is are was were be "
           "been being it its this that these those not no than then so such".split())


def load_corpus():
    arts = []
    for fam_dir in sorted(CORPUS.iterdir()):
        if not fam_dir.is_dir():
            continue
        for p in sorted(fam_dir.glob("*.json")):
            if p.name != "manifest.json":
                arts.append(json.loads(p.read_text(encoding="utf-8")))
    return arts


def pool_words():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "g131gen", REPO / "runners" / "run_g131_gen.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    def content(pool):
        ws = set()
        for ins in pool:
            ws |= {w.lower() for w in re.findall(r"[a-zA-Z']+", ins)} - STOP
        return ws
    return content(mod.SURFACE), content(mod.PROBLEM)


def features(a, surface_w, problem_w):
    text = a["text"]
    words = text.split()
    nw = max(len(words), 1)
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    toks = {w.lower().strip(".,!?;:()\"'") for w in words}
    per_k = 1000.0 / nw
    return {
        "length": [len(words)],
        "paragraphs": [len(paras), nw / max(len(paras), 1)],
        "punctuation": [text.count("?") * per_k, text.count("(") * per_k,
                        text.count(";") * per_k,
                        (text.count("—") + text.count("--")) * per_k,
                        len(re.findall(r"^\s*\d+[.)]\s", text, re.M)) * per_k,
                        text.count("!") * per_k],
        "lexical_echo": [len(toks & surface_w) / max(len(surface_w), 1),
                         len(toks & problem_w) / max(len(problem_w), 1)],
    }


def run() -> None:
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline

    arts = load_corpus()
    surface_w, problem_w = pool_words()
    feats = [features(a, surface_w, problem_w) for a in arts]
    sets = list(feats[0].keys())
    sets.append("all")
    topics = np.array([a["topic"] for a in arts])
    rng = np.random.default_rng(SEED)

    def loto_acc(X, y, groups):
        gkf = GroupKFold(n_splits=len(set(groups)))
        correct = 0
        for tr, te in gkf.split(X, y, groups):
            clf = make_pipeline(StandardScaler(),
                                LogisticRegression(max_iter=2000, random_state=SEED))
            clf.fit(X[tr], y[tr])
            correct += int((clf.predict(X[te]) == y[te]).sum())
        return correct / len(y)

    def matrix(name, idx):
        if name == "all":
            return np.array([[v for s in sets[:-1] for v in feats[i][s]] for i in idx])
        return np.array([[v for v in feats[i][name]] for i in idx])

    results = {}
    tasks = {
        "target": ([i for i, a in enumerate(arts) if a["target"] != "none"],
                   lambda a: a["target"]),
        "amount": (list(range(len(arts))), lambda a: str(a["amount"])),
    }
    for task, (idx, label_fn) in tasks.items():
        y = np.array([label_fn(arts[i]) for i in idx])
        g = topics[idx]
        classes, counts = np.unique(y, return_counts=True)
        base = counts.max() / len(y)
        results[task] = {"n": len(idx), "classes": {c: int(n) for c, n in
                                                    zip(classes, counts)},
                         "majority_base_rate": round(float(base), 4), "arms": {}}
        for name in sets:
            X = matrix(name, idx)
            acc = loto_acc(X, y, g)
            # permutation null: shuffle labels within topic so the group structure holds
            null = []
            for _ in range(N_PERM):
                yp = y.copy()
                for t in set(g):
                    m = g == t
                    yp[m] = rng.permutation(yp[m])
                null.append(loto_acc(X, yp, g))
            p = (1 + sum(1 for v in null if v >= acc)) / (1 + len(null))
            results[task]["arms"][name] = {
                "loto_accuracy": round(float(acc), 4),
                "perm_p": round(float(p), 5), "n_perm_effective": len(null),
                "null_mean": round(float(np.mean(null)), 4),
                "null_q95": round(float(np.quantile(null, 0.95)), 4)}
            print(f"{task}/{name}: acc {acc:.4f}  p {p:.4f}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "baselines.json").write_text(json.dumps(
        {"seed": SEED, "n_perm_requested": N_PERM, "results": results}, indent=1),
        encoding="utf-8", newline="\n")
    print("written: results/g158/baselines.json")


if __name__ == "__main__":
    run()
