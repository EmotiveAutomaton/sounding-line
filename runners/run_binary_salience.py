"""G21 — is the first layer binary salience? A double dissociation, pre-registered.

His question, asked directly: *"the initial layer is binary saliency, do you think?"* The adjacent
literature finds affect **presence** dissociable from affect **category** early — no sign, no
intensity, just *something is here*.

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

Per layer, two cross-validated linear probes on human-labelled GoEmotions comments:

    PRESENCE   emotional versus neutral (balanced binary)
    CATEGORY   which of the 27 emotions (among emotional items only)

    SALIENCE       layer 0 carries presence near its best-layer level (>= 0.9x) while carrying
                   category at under twice chance -- the double dissociation
    NO DISSOCIATION anything else. Report the two curves either way; where each peaks is
                   evidence for the layer-ordering question (G20a vs G20b) regardless
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "binary_salience"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=40)
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415
    from datasets import load_dataset                                 # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression               # noqa: PLC0415
    from sklearn.model_selection import StratifiedKFold, cross_val_score  # noqa: PLC0415
    from sklearn.pipeline import make_pipeline                        # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler                  # noqa: PLC0415

    from soundingline.probe.activations import DEFAULT_MODEL, Reader  # noqa: PLC0415

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)

    ds = load_dataset("google-research-datasets/go_emotions", "simplified", split="train")
    names = ds.features["labels"].feature.names
    by: dict[str, list[str]] = {n: [] for n in names}
    for row in ds:
        if len(row["labels"]) != 1 or len(row["text"].split()) < 6:
            continue
        n = names[row["labels"][0]]
        if len(by[n]) < args.per_class:
            by[n].append(row["text"])
    classes = [n for n in names if len(by[n]) >= args.per_class // 2]
    print(f"  {len(classes)} classes at up to {args.per_class} items", flush=True)

    probe = reader.read("shape probe")
    n_layers = probe.n_layers
    X = [[] for _ in range(n_layers)]
    y = []
    total = sum(len(by[c]) for c in classes)
    for c in classes:
        for t in by[c]:
            a = reader.read(t)
            for L in range(n_layers):
                X[L].append(np.asarray(a.acts[L], dtype=np.float32))
            y.append(c)
            if len(y) % 200 == 0:
                print(f"  read {len(y)}/{total}", flush=True)
    y = np.array(y)
    is_neutral = y == "neutral"
    emo_mask = ~is_neutral
    n_emo_classes = len(set(y[emo_mask]))
    cat_chance = 1.0 / n_emo_classes

    def acc(Xl, yy, folds=5):
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=0.5))
        cv = StratifiedKFold(folds, shuffle=True, random_state=0)
        return float(np.mean(cross_val_score(clf, Xl, yy, cv=cv)))

    rng = np.random.default_rng(5)
    # balanced binary: all neutral items vs an equal random sample of emotional ones
    n_idx = np.where(is_neutral)[0]
    e_idx = rng.choice(np.where(emo_mask)[0], size=len(n_idx), replace=False)
    b_idx = np.concatenate([n_idx, e_idx])

    print(f"\n{'layer':>6}{'presence acc':>14}{'category acc':>14}{'cat/chance':>12}")
    print("-" * 48)
    out = []
    for L in range(n_layers):
        Xl = np.array(X[L])
        pres = acc(Xl[b_idx], is_neutral[b_idx])
        cat = acc(Xl[emo_mask], y[emo_mask], folds=3)
        out.append({"layer": L, "presence": pres, "category": cat})
        print(f"{L:>6}{pres:>14.3f}{cat:>14.3f}{cat / cat_chance:>12.2f}")

    best_p = max(o["presence"] for o in out)
    l0 = out[0]
    dissoc = (l0["presence"] >= 0.9 * best_p) and (l0["category"] < 2 * cat_chance)
    peak_p = max(out, key=lambda o: o["presence"])["layer"]
    peak_c = max(out, key=lambda o: o["category"])["layer"]
    verdict = "SALIENCE" if dissoc else "NO DISSOCIATION"
    print(f"\n  layer 0: presence {l0['presence']:.3f} (best {best_p:.3f} at layer {peak_p}), "
          f"category {l0['category']:.3f} vs chance {cat_chance:.3f}")
    print(f"  presence peaks at layer {peak_p}; category peaks at layer {peak_c}")
    print(f"\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = model_name.split("/")[-1]
    (RESULTS / f"{tag}.json").write_text(json.dumps(
        {"model": model_name, "n": int(len(y)), "n_neutral": int(is_neutral.sum()),
         "cat_chance": cat_chance, "layers": out, "presence_peak": peak_p,
         "category_peak": peak_c, "verdict": verdict}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
