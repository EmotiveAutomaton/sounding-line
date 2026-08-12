"""G20a/G20b + G143 — where valence, category, and beyond-lexicon decodability sit per block.

The two mappings (THREE_COGNITIVE_LAYERS §2), never tested directly:
    G20a: core affect (valence) decodable EARLY, drive/category structure MID
    G20b: early blocks are the input adapter, valence MID, categories LATE
And G143's interface claim: the emotion vocabulary's elaboration output should look like an
input for a mid-stack transformation, operationalized here as the block where decodability
beyond the lexicon starts to rise.

Per block, three curves:
    valence   pos-vs-neg accuracy on single-label emotion sentences
    category  emotion-category accuracy among emotional sentences
    lexical   the same valence probe on WORD-SHUFFLED copies of the same sentences, which
              keeps the lexicon and destroys composition; the (original - shuffled) gap is
              decodability beyond the lexicon, and the block where the gap first rises and
              stays is the handoff candidate

Lessons applied (docs/method/LESSONS.md §3): a label-permutation ruler gate runs before any
verdict (probe on shuffled labels must sit at chance, else VOID); peaks are only called at
prominence >= 0.03 over the curve median, else the curve is FLAT and no address is claimed
(the L14/G21 precedent says flat is the expected deflationary outcome); depths are reported
as fractions, and the mapping verdict uses pre-registered thirds: G20a needs valence peak in
the first third and category in the middle third; G20b needs valence middle and category
last. Anything else is NEITHER.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "results" / "g20_mapping"

POS = {"admiration", "amusement", "approval", "caring", "desire", "excitement",
       "gratitude", "joy", "love", "optimism", "pride", "relief"}
NEG = {"anger", "annoyance", "disappointment", "disapproval", "disgust", "embarrassment",
       "fear", "grief", "nervousness", "remorse", "sadness"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--per-class", type=int, default=30)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    tag = args.model.split("/")[-1]

    import numpy as np                                                # noqa: PLC0415
    from datasets import load_dataset                                 # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression               # noqa: PLC0415
    from sklearn.model_selection import StratifiedKFold, cross_val_score  # noqa: PLC0415
    from sklearn.pipeline import make_pipeline                        # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler                  # noqa: PLC0415

    from soundingline.gpulock import acquire_gpu_lock                 # noqa: PLC0415
    from soundingline.probe.activations import Reader                 # noqa: PLC0415

    rng = np.random.default_rng(20)

    ds = load_dataset("google-research-datasets/go_emotions", "simplified", split="train")
    names = ds.features["labels"].feature.names
    by: dict[str, list[str]] = {n: [] for n in names}
    for row in ds:
        if len(row["labels"]) != 1 or len(row["text"].split()) < 6:
            continue
        n = names[row["labels"][0]]
        if len(by[n]) < args.per_class:
            by[n].append(row["text"])
    classes = [n for n in names if n != "neutral" and len(by[n]) >= args.per_class // 2]
    texts, labels = [], []
    for c in classes:
        texts.extend(by[c])
        labels.extend([c] * len(by[c]))
    labels = np.array(labels)
    val_mask = np.array([l in POS or l in NEG for l in labels])
    is_pos = np.array([l in POS for l in labels])
    print(f"{len(texts)} sentences, {len(classes)} emotional classes, "
          f"{int(val_mask.sum())} valenced", flush=True)

    def shuffle_words(t: str, r) -> str:
        w = t.split()
        r.shuffle(w)
        return " ".join(w)

    shuf_texts = [shuffle_words(t, rng) for t in texts]

    acquire_gpu_lock(f"g20:{tag}")
    print(f"loading {args.model} ...", flush=True)
    reader = Reader(args.model, device=args.device)
    n_layers = reader.read("shape probe").n_layers

    def read_all(ts):
        X = [[] for _ in range(n_layers)]
        for i, t in enumerate(ts):
            a = reader.read(t)
            for L in range(n_layers):
                X[L].append(np.asarray(a.acts[L], dtype=np.float32))
            if (i + 1) % 200 == 0:
                print(f"  read {i + 1}/{len(ts)}", flush=True)
        return [np.array(x) for x in X]

    print("reading originals ...", flush=True)
    X_orig = read_all(texts)
    print("reading word-shuffled copies ...", flush=True)
    X_shuf = read_all(shuf_texts)

    def acc(Xl, yy, folds=5):
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=0.5))
        cv = StratifiedKFold(folds, shuffle=True, random_state=0)
        return float(np.mean(cross_val_score(clf, Xl, yy, cv=cv)))

    # ── ruler gate: permuted labels must sit at chance at a mid block, else VOID
    mid = n_layers // 2
    perm = rng.permutation(is_pos[val_mask])
    gate_acc = acc(X_orig[mid][val_mask], perm)
    if abs(gate_acc - 0.5) > 0.07:
        out = {"model": args.model, "verdict": "VOID",
               "reason": f"label-permutation gate {gate_acc:.3f} at block {mid}"}
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"{tag}.json").write_text(json.dumps(out, indent=1),
                                             encoding="utf-8", newline="\n")
        print(f">>> VOID: permuted-label probe scored {gate_acc:.3f}")
        sys.exit(1)
    print(f"gate ok: permuted-label probe {gate_acc:.3f} at block {mid}", flush=True)

    rows = []
    for L in range(n_layers):
        v = acc(X_orig[L][val_mask], is_pos[val_mask])
        c = acc(X_orig[L], labels, folds=3)
        lx = acc(X_shuf[L][val_mask], is_pos[val_mask])
        rows.append({"layer": L, "depth": L / max(1, n_layers - 1), "valence": v,
                     "category": c, "lexical_valence": lx,
                     "beyond_lexicon_gap": round(v - lx, 4)})
        print(f"  L{L:>3} d{L / max(1, n_layers - 1):.2f}  val {v:.3f}  cat {c:.3f}  "
              f"lex {lx:.3f}  gap {v - lx:+.3f}", flush=True)

    def peak(key):
        vals = np.array([r[key] for r in rows])
        med = float(np.median(vals))
        i = int(np.argmax(vals))
        prom = float(vals[i] - med)
        return {"depth": rows[i]["depth"], "value": float(vals[i]),
                "prominence": round(prom, 4), "flat": prom < 0.03}

    pv, pc = peak("valence"), peak("category")
    gap = np.array([r["beyond_lexicon_gap"] for r in rows])
    rise = next((rows[i]["depth"] for i in range(len(rows))
                 if all(g >= 0.03 for g in gap[i:i + 3]) and i + 2 < len(rows)), None)

    if pv["flat"] or pc["flat"]:
        mapping = "FLAT, no address claimable"
    elif pv["depth"] < 1 / 3 and 1 / 3 <= pc["depth"] < 2 / 3:
        mapping = "G20a"
    elif 1 / 3 <= pv["depth"] < 2 / 3 and pc["depth"] >= 2 / 3:
        mapping = "G20b"
    else:
        mapping = "NEITHER"

    out = {"model": args.model, "n_texts": len(texts), "gate_perm_acc": round(gate_acc, 3),
           "valence_peak": pv, "category_peak": pc, "mapping_verdict": mapping,
           "beyond_lexicon_rise_depth": rise, "rows": rows}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{tag}.json").write_text(json.dumps(out, indent=1),
                                         encoding="utf-8", newline="\n")
    print(f">>> {tag}: mapping {mapping}; valence peak d{pv['depth']:.2f} "
          f"(prom {pv['prominence']:.3f}), category d{pc['depth']:.2f} "
          f"(prom {pc['prominence']:.3f}); beyond-lexicon rise at "
          f"{'none' if rise is None else f'd{rise:.2f}'}")
    print(f"wrote {(OUT_DIR / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
