"""G116 — the Kolmogorov claim and the regression-to-the-mean claim, both from the essays, neither
ever tested here.

The virus paper's crash mechanics lean on: machine output "lacks the high Kolmogorov complexity
(description length) inherent to biological constraint satisfaction." The unifying essay adds:
generation is "a regression towards the mean... the average fish" — idiosyncrasy sanded away.

── TWO TESTS, CPU-ONLY ───────────────────────────────────────────────────────────────────────

1. DESCRIPTION LENGTH: per-artifact incompressibility (lzma bytes out / bytes in). If specified
   intent adds real structure-that-must-be-described, incompressibility should RISE with rung,
   with length partialled out (the ladders); and human long-form should sit above machine text at
   matched length.
2. MEAN-REGRESSION: distance from each artifact's feature vector (342 features, z-scored over the
   pooled set) to the pooled centroid. The essay predicts machine text hugs the centroid; human
   text scatters. Register differences ride along — reported, not controlled, and flagged as such.

    KOLMOGOROV-TRACKS-INTENT   rho(rung, incompressibility | length) > 0, p < 0.01, >= 2 ladders
    MEAN-REGRESSION            human mean centroid distance > machine, both human groups
    (each verdict independent; either can fail alone)
"""

from __future__ import annotations

import json
import lzma
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "compression"


def incompress(text: str) -> float:
    raw = text.encode("utf-8")
    return len(lzma.compress(raw, preset=6)) / max(len(raw), 1)


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415
    from scipy.stats import rankdata                                  # noqa: PLC0415

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    out = {"ladders": {}, "groups": {}}
    print(f"{'corpus':<10}{'n':>5}{'rho(rung,K|len)':>17}{'p':>9}")
    hits = 0
    for corpus in ("ladder", "ladder2", "ladder3"):
        d = REPO / "corpora" / corpus
        man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        rows = []
        for it in man["items"]:
            if not isinstance(it.get("rung"), int):
                continue
            t = (d / f"{it['id']}.txt").read_text(encoding="utf-8")
            rows.append((it["rung"], len(t.split()), incompress(t)))
        rung = np.array([r[0] for r in rows], float)
        wds = np.array([r[1] for r in rows], float)
        k = np.array([r[2] for r in rows], float)
        rho, p = stats.spearmanr(rres(k, wds), rres(rung, wds))
        out["ladders"][corpus] = {"n": len(rows), "rho": float(rho), "p": float(p)}
        hits += bool(rho > 0 and p < 0.01)
        print(f"{corpus:<10}{len(rows):>5}{rho:>+17.3f}{p:>9.4f}")

    # human-vs-machine at matched length: books truncated to the ladder band
    def truncate(t, n=1400):
        return " ".join(t.split()[:n])

    groups = {}
    books = json.loads((REPO / "corpora" / "manifests" / "books.json").read_text(encoding="utf-8"))
    bitems = books["items"] if isinstance(books, dict) else books
    vals = []
    for it in bitems:
        p = REPO / "corpora" / "store" / f"{it['id']}.txt"
        if p.exists():
            vals.append(incompress(truncate(p.read_text(encoding="utf-8", errors="ignore")[5000:])))
    groups["human_books"] = vals
    for corpus in ("ladder2", "nomaker"):
        d = REPO / "corpora" / corpus
        man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        groups[corpus] = [incompress(truncate((d / f"{it['id']}.txt")
                                              .read_text(encoding="utf-8")))
                          for it in man["items"]
                          if (d / f"{it['id']}.txt").exists()]
    print()
    for g, v in groups.items():
        out["groups"][g] = {"n": len(v), "mean_incompressibility": float(np.mean(v))}
        print(f"  {g:<14} n={len(v):>3}  incompressibility {np.mean(v):.4f}")

    # mean-regression on the cached feature space
    feats, labels = [], []
    for corpus, label in (("ladder2", "machine"), ("argrewrite", "human")):
        cache = REPO / "results" / "features" / f"{corpus}.json"
        if not cache.exists():
            continue
        for it in json.loads(cache.read_text(encoding="utf-8"))["items"]:
            f = it.get("whole") or {}
            if f:
                feats.append(f); labels.append(label)
    keys = sorted(set.intersection(*(set(f) for f in feats))) if feats else []
    X = np.array([[float(f.get(k, 0.0) or 0.0) for k in keys] for f in feats])
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)
    dist = np.linalg.norm(X - X.mean(0), axis=1)
    hm = {lab: float(np.mean(dist[[i for i, l in enumerate(labels) if l == lab]]))
          for lab in set(labels)}
    out["centroid_distance"] = hm
    print(f"\n  centroid distance: {hm}")

    v1 = "KOLMOGOROV-TRACKS-INTENT" if hits >= 2 else "NO-TRACK"
    v2 = ("MEAN-REGRESSION" if hm.get("human", 0) > hm.get("machine", 0) else "NO-REGRESSION") \
        if len(hm) == 2 else "N/A"
    out["verdicts"] = {"kolmogorov": v1, "mean_regression": v2}
    print(f"\n  >>> {v1} | {v2}  (register uncontrolled in the group comparison — flagged)")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(out, indent=2),
                                          encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
