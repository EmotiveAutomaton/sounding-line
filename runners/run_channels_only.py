"""G150 reference arm — the channels ALONE on the 2025 sentence-pair task, local CPU.

The shelf's own lesson (L85: nineteen string-diff features beat a thousand embedding
dimensions on the published pair task) demands this baseline before the fusion A/B is
interpretable: if the channels alone approach the substrate, the fusion result means
something different than if they sit near chance. Gradient-boosted trees on the 158-dim
pair channels, train split only, scored with the pooled evaluator form on validation and
test. Free, minutes, no GPU.

Output: results/pan25_winner/channels_only_{difficulty}.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))

from run_pan25_winner import PAN25, load_split, pooled_macro_f1   # noqa: E402

RESULTS = REPO / "results" / "pan25_winner"
CHAN = REPO / "results" / "pan25_channels"


def main() -> None:
    import numpy as np                                             # noqa: PLC0415
    from sklearn.ensemble import HistGradientBoostingClassifier    # noqa: PLC0415

    diff = sys.argv[1] if len(sys.argv) > 1 else "hard"
    splits = {}
    for name in ("train", "validation", "test"):
        X = np.load(CHAN / f"{diff}_{name}.npz")["X"]
        meta = json.loads((CHAN / f"{diff}_{name}_meta.json").read_text(encoding="utf-8"))
        probs = load_split(PAN25 / diff / name)
        y, spans, k = [], {}, 0
        for m in meta["problems"]:
            spans[m["id"]] = (k, k + m["n_pairs"])
            k += m["n_pairs"]
        for q in probs:
            if q["ok"]:
                y.extend(q["changes"])
        assert len(y) == X.shape[0] == k, (name, len(y), X.shape, k)
        splits[name] = {"X": X, "y": np.array(y), "spans": spans, "probs": probs}

    clf = HistGradientBoostingClassifier(max_iter=400, random_state=42)
    clf.fit(splits["train"]["X"], splits["train"]["y"])

    out = {"arm": "channels_only", "difficulty": diff, "dims": int(X.shape[1]),
           "model": "HistGradientBoostingClassifier(max_iter=400, seed 42)"}
    for name in ("validation", "test"):
        s = splits[name]
        pred = clf.predict(s["X"])
        truths, preds = [], []
        for q in s["probs"]:
            if not q["ok"]:
                continue
            a, b = s["spans"][q["id"]]
            truths.append(q["changes"])
            preds.append(pred[a:b].tolist())
        out[f"{name}_pooled_macro_f1"] = round(pooled_macro_f1(truths, preds), 4)
    out["printed_test_gate"] = {"hard": 0.830, "easy": 0.958, "medium": 0.823}[diff]

    RESULTS.mkdir(parents=True, exist_ok=True)
    dest = RESULTS / f"channels_only_{diff}.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    print(f"wrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
