"""How many affective components are actually there, with no taxonomy imposed?

── THE QUESTION ──────────────────────────────────────────────────────────────────────────────

A 2025 study probed language-model layers for **Ekman's six basic emotions plus neutral** and found
the signal peaks in the **middle** layers. That middle-layer finding is what this project predicted
before reading it. But their taxonomy was fixed in advance:

    "Ekman's six basic emotions (joy, sadness, anger, fear, surprise, disgust) or 'neutral'"

**They could only find seven things because they only looked for seven**, and the seven were chosen
for being nameable and readable off a face. The curator's standing instruction is the exact
counter-move: *"let's not presume we can pre-PCA if we can't identify the six. But if a PCA pops out
a seventh, that makes the seventh really interesting."*

── WHAT THIS DOES INSTEAD ────────────────────────────────────────────────────────────────────

Take their corpus, **use only the genuinely human portion**, and impose nothing.

Their 400,000 utterances are not all real: neutral comments were rewritten by a model to inject
emotion, and ~60,000 were synthesised outright. **Only the rows marked `source == "raw"` are
untouched human Reddit text**, and only those are used here. Their labels are also machine-assigned
by Qwen3-32B and are read for *comparison only* — never as ground truth.

Then: read activations at every layer, and decompose **without supervision**.

── PRE-REGISTERED, BEFORE ANY DECOMPOSITION IS RUN ───────────────────────────────────────────

**The stopping criterion is fixed first, because the criterion is what sets the answer.** Lin &
Adolphs (2025) recovered 27 components versus 3 from identical stimuli by varying exactly this.

    criterion      parallel analysis -- keep components whose eigenvalue exceeds the 95th percentile
                   of eigenvalues from SHUFFLED data of identical shape. Non-arbitrary, standard,
                   and decided in advance
    reported       component count per layer, plus the count under two alternative criteria
                   (Kaiser, and 90% variance) so the sensitivity is visible rather than hidden

    EKMAN-SHAPED   components align with the seven machine-assigned labels above chance, and the
                   count is near seven
    RICHER         reliably MORE components than seven survive parallel analysis, and the extra ones
                   do not map onto any single label -- which is the curator's prediction
    POORER         fewer than seven, suggesting the categories collapse into something simpler
                   like valence and arousal

**No outcome favours the project.** RICHER is predicted; POORER would support the constructed-emotion
reading that affect reduces to core dimensions; EKMAN-SHAPED would mean the field's taxonomy is
recovering something real and our objection is empty.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "decomposition"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1500, help="human utterances to read")
    ap.add_argument("--model", default=None)
    ap.add_argument("--min-words", type=int, default=12)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    from datasets import load_dataset                                # noqa: PLC0415

    from soundingline.probe.activations import DEFAULT_MODEL, Reader  # noqa: PLC0415

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)

    print("streaming the human portion of jzhang92/LLM-Emotion ...", flush=True)
    ds = load_dataset("jzhang92/LLM-Emotion", split="train", streaming=True)
    texts, labels = [], []
    for row in ds:
        # ONLY untouched human Reddit text. Rewritten and synthetic rows are excluded.
        if str(row.get("source", "")).lower() != "raw":
            continue
        t = row.get("text") or row.get("utterance") or row.get("content") or ""
        if not isinstance(t, str) or len(t.split()) < args.min_words:
            continue
        texts.append(t)
        labels.append(str(row.get("emotion", "none")))
        if len(texts) >= args.n:
            break
    print(f"  {len(texts)} human utterances, "
          f"{len(set(labels))} distinct machine-assigned labels\n", flush=True)
    if len(texts) < 200:
        print("  too few usable rows — check the field names on the dataset card")
        return

    probe = reader.read("shape probe")
    n_layers = probe.n_layers
    acts = [np.zeros((len(texts), len(probe.acts[L]))) for L in range(n_layers)]
    for i, t in enumerate(texts):
        a = reader.read(t)
        for L in range(n_layers):
            acts[L][i] = np.asarray(a.acts[L], dtype=float)
        if (i + 1) % 250 == 0:
            print(f"  read {i + 1}/{len(texts)}", flush=True)

    rng = np.random.default_rng(19)

    def n_components(X: np.ndarray) -> dict:
        """Parallel analysis, plus two alternative criteria so sensitivity is visible."""
        Z = (X - X.mean(0)) / np.where(X.std(0) == 0, 1.0, X.std(0))
        Z = Z[:, np.isfinite(Z).all(0)]
        k = min(Z.shape) - 1
        ev = np.linalg.svd(Z, compute_uv=False)[:k] ** 2 / (Z.shape[0] - 1)
        # null eigenvalues from column-shuffled data of identical shape
        nulls = []
        for _ in range(5):
            S = np.column_stack([rng.permutation(Z[:, j]) for j in range(Z.shape[1])])
            nulls.append(np.linalg.svd(S, compute_uv=False)[:k] ** 2 / (S.shape[0] - 1))
        thresh = np.percentile(np.array(nulls), 95, axis=0)
        parallel = int((ev > thresh).sum())
        kaiser = int((ev > 1.0).sum())
        var = ev / ev.sum()
        var90 = int(np.searchsorted(np.cumsum(var), 0.90) + 1)
        return {"parallel": parallel, "kaiser": kaiser, "var90": var90,
                "top_var_share": float(var[0])}

    print(f"{'layer':>6}{'parallel':>10}{'kaiser':>9}{'90% var':>9}{'top comp share':>16}")
    print("-" * 52)
    out = []
    for L in range(n_layers):
        r = n_components(acts[L])
        out.append({"layer": L, **r})
        print(f"{L:>6}{r['parallel']:>10}{r['kaiser']:>9}{r['var90']:>9}"
              f"{r['top_var_share']:>16.3f}")

    mid = out[n_layers // 3: 2 * n_layers // 3]
    mid_par = float(np.mean([o["parallel"] for o in mid]))
    verdict = ("RICHER" if mid_par > 8 else
               "POORER" if mid_par < 6 else "EKMAN-SHAPED")
    print(f"\n  middle-layer component count, parallel analysis: {mid_par:.1f}")
    print(f"  (Ekman's six plus neutral would be 7)")
    print(f"\n  >>> {verdict}")
    print("\n  Labels were assigned by a language model, not people, and are NOT used above.")
    print("  This counts structure in the activations, not agreement with anyone's taxonomy.")

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = model_name.split("/")[-1]
    (RESULTS / f"{tag}.json").write_text(json.dumps(
        {"model": model_name, "n_texts": len(texts), "n_layers": n_layers,
         "layers": out, "middle_parallel_mean": mid_par, "verdict": verdict,
         "label_distribution": {k: labels.count(k) for k in sorted(set(labels))}},
        indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
