"""G87 — stage-differentiated features: low-visibility carries who, high-visibility carries what.

The pottery import (Gosselain): low-visibility, early-acquired habits mark deep identity; visible,
easily-copied features mark situational register. Text partition: function-word/syntactic-reflex
features versus lexical-richness/readability features.

    STAGE-DIFFERENTIATED   low-visibility features beat high-visibility at author ID (books) while
                           high-visibility features beat low at draft-stage separation (argrewrite)
    UNDIFFERENTIATED       no crossover — the partition carries nothing
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "feature_visibility"
LOW_VIS = ("biber_", "fw_", "pron", "prep", "conj", "aux", "punct", "comma", "stopword")
HIGH_VIS = ("ttr", "type_token", "readability", "flesch", "smog", "syll", "char", "word_len",
            "subtlex", "zipf", "kincaid", "coleman")


def main() -> None:
    import numpy as np                                                # noqa: PLC0415

    cache = json.loads((REPO / "results" / "features" / "argrewrite.json")
                       .read_text(encoding="utf-8"))["items"]
    keys = sorted(set.intersection(*(set(it["whole"]) for it in cache)))
    low = [k for k in keys if any(p in k.lower() for p in LOW_VIS)]
    high = [k for k in keys if any(p in k.lower() for p in HIGH_VIS)]
    print(f"{len(low)} low-visibility features, {len(high)} high-visibility")

    def acc_partition(X, y, rng):
        # leave-one-out nearest-centroid
        X = (X - X.mean(0)) / (X.std(0) + 1e-9)
        correct = 0
        labs = sorted(set(y))
        for i in range(len(y)):
            cents = {l: X[[j for j in range(len(y)) if y[j] == l and j != i]].mean(0)
                     for l in labs}
            pred = min(cents, key=lambda l: np.linalg.norm(X[i] - cents[l]))
            correct += pred == y[i]
        return correct / len(y)

    rng = np.random.default_rng(3)
    out = {}
    # argrewrite: draft-stage separation (situational register)
    ids = [it["id"] for it in cache]
    stages = [i.split("_d")[-1] for i in ids]
    for name, ks in (("low_vis", low), ("high_vis", high)):
        X = np.array([[float(it["whole"].get(k, 0.0) or 0.0) for k in ks] for it in cache])
        a = acc_partition(X, stages, rng)
        out[f"draft_stage_{name}"] = a
        print(f"draft-stage separation, {name}: {a:.3f} (chance {1 / len(set(stages)):.3f})")

    # books: author identity, via raw function-word/lexical stats computed here (no cache)
    lut = {}
    for m in (REPO / "corpora" / "store").glob("*.meta.json"):
        meta = json.loads(m.read_text(encoding="utf-8"))
        for k in ("requested_url", "final_url"):
            if meta.get(k):
                lut[meta[k]] = m.with_name(m.name.replace(".meta.json", ".txt"))
    books = json.loads((REPO / "corpora" / "manifests" / "books.json")
                       .read_text(encoding="utf-8"))
    FW = ("the of and to in a is was that it he she they for with as on at by not this "
          "but from or which you his her had have be were are").split()
    rowsL, rowsH, authors = [], [], []
    for it in (books["items"] if isinstance(books, dict) else books):
        p = lut.get(it.get("url")) or lut.get(it.get("final_url"))
        if not (p and p.exists()):
            continue
        words = re.findall(r"[a-z']+", p.read_text(encoding="utf-8", errors="ignore").lower())
        for chunk_start in (3000, 13000):
            chunk = words[chunk_start:chunk_start + 3000]
            if len(chunk) < 3000:
                continue
            c = Counter(chunk)
            rowsL.append([c[w] / 3000 for w in FW])
            rowsH.append([len(set(chunk)) / 3000,
                          float(np.mean([len(w) for w in chunk])),
                          sum(1 for w in chunk if len(w) > 8) / 3000])
            authors.append(it["author"])
    for name, rows in (("low_vis", rowsL), ("high_vis", rowsH)):
        a = acc_partition(np.array(rows), authors, rng)
        out[f"author_id_{name}"] = a
        print(f"author identification, {name}: {a:.3f} (chance {1 / len(set(authors)):.3f})")

    crossover = (out["author_id_low_vis"] > out["author_id_high_vis"]
                 and out["draft_stage_high_vis"] >= out["draft_stage_low_vis"])
    out["verdict"] = "STAGE-DIFFERENTIATED" if crossover else "UNDIFFERENTIATED"
    print(f"\n  >>> {out['verdict']}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(out, indent=2),
                                          encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
