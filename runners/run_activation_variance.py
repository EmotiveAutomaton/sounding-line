"""HH-3 / PD-3 reader-side — within-artifact variance of the reader's own affective series.

The field measures within-document variation with perplexity (burstiness) and surface style (PAN);
**nobody found doing it with probe activations** (HH-3, "not pre-empted by anyone"). And PD-3
predicts the machine signature is *a polish that does not move* — flat within-artifact series,
because there is no maker to tire.

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

Per artifact: the early/late affective ratio per 200-word window — a positional series. Keep
artifacts with >= 4 windows; the statistic is the within-artifact variance of the series
(subsampled to 6 windows where longer, so human books and machine ladders compare at matched
series length).

    HUMAN-MOVES    books' variance exceeds the machine ladders' at matched windows (MWU p < 0.01)
                   — the human series moves, the machine one is flat (PD-3's signature)
    RUNG-TRACKS    |spearman(rung, variance)| > 0.3 at p < 0.01, length partialled, either ladder
                   — within-artifact movement itself carries the dose
    (independent verdicts; either can fail alone)
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "activation_variance"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--fiction", action="store_true",
                    help="the register-matched arm L39 owed: books against machine fiction, "
                         "two generator families, same statistic, own output file")
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415
    from scipy.stats import rankdata                                  # noqa: PLC0415

    from runners.run_b import split                                   # noqa: PLC0415
    from runners.run_layer_ratio import windows                       # noqa: PLC0415
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    n = dirs.n_layers
    lo_hi = max(2, round(n * 0.07))
    hi_lo = round(n * 0.76)

    def series(text: str) -> list[float]:
        out = []
        for w in windows(text):
            p = dirs.project(reader.read(w))
            early = statistics.fmean(abs(v[L]) for v in p.values() for L in range(lo_hi))
            late = statistics.fmean(abs(v[L]) for v in p.values() for L in range(hi_lo, n))
            if late > 1e-9:
                out.append(early / late)
        return out

    rng = np.random.default_rng(11)

    def var6(s: list[float]) -> float:
        if len(s) > 6:
            s = list(rng.choice(s, 6, replace=False))
        return float(np.var(s))

    rows = []
    machine_corpora = (("machine_fiction_qwen", "machine_fiction_ds") if args.fiction
                       else ("ladder2", "ladder3", "nomaker"))
    for corpus in machine_corpora:
        d = REPO / "corpora" / corpus
        if args.fiction:
            for p in sorted(d.glob("*.txt")):
                s = series(p.read_text(encoding="utf-8", errors="replace"))
                if len(s) >= 4:
                    rows.append({"group": corpus, "id": p.stem, "rung": None,
                                 "n_windows": len(s), "variance": var6(s),
                                 "mean": statistics.fmean(s)})
            print(f"{corpus}: {sum(r['group'] == corpus for r in rows)} artifacts", flush=True)
            continue
        man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        for it in man["items"]:
            p = d / f"{it['id']}.txt"
            if not p.exists():
                continue
            s = series(p.read_text(encoding="utf-8"))
            if len(s) >= 4:
                rows.append({"group": corpus, "id": it["id"], "rung": it.get("rung"),
                             "n_windows": len(s), "variance": var6(s),
                             "mean": statistics.fmean(s)})
        print(f"{corpus}: {sum(r['group'] == corpus for r in rows)} artifacts", flush=True)

    lut = {}
    for m in (REPO / "corpora" / "store").glob("*.meta.json"):
        meta = json.loads(m.read_text(encoding="utf-8"))
        for k in ("requested_url", "final_url"):
            if meta.get(k):
                lut[meta[k]] = m.with_name(m.name.replace(".meta.json", ".txt"))
    books = json.loads((REPO / "corpora" / "manifests" / "books.json").read_text(encoding="utf-8"))
    for it in (books["items"] if isinstance(books, dict) else books):
        p = lut.get(it.get("url")) or lut.get(it.get("final_url"))
        if not (p and p.exists()):
            continue
        text = " ".join(p.read_text(encoding="utf-8", errors="ignore").split()[2000:3500])
        s = series(text)
        if len(s) >= 4:
            rows.append({"group": "human_books", "id": it["id"], "rung": None,
                         "n_windows": len(s), "variance": var6(s), "mean": statistics.fmean(s)})
    print(f"human_books: {sum(r['group'] == 'human_books' for r in rows)} artifacts", flush=True)

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    out = {"model": model_name, "rows": rows, "tests": {}}
    hb = [r["variance"] for r in rows if r["group"] == "human_books"]
    if args.fiction:
        # the register-matched comparisons, one per generator family, L39's stated direction
        for fam in ("machine_fiction_qwen", "machine_fiction_ds"):
            mv = [r["variance"] for r in rows if r["group"] == fam]
            if hb and mv:
                u, p = stats.mannwhitneyu(hb, mv, alternative="greater")
                out["tests"][f"books_vs_{fam}"] = {
                    "books_median": float(np.median(hb)), "fiction_median": float(np.median(mv)),
                    "n_books": len(hb), "n_fiction": len(mv), "p": float(p)}
                print(f"  books {np.median(hb):.4f} vs {fam} {np.median(mv):.4f} "
                      f"(one-sided p={p:.4f})")
        ps = [t["p"] for t in out["tests"].values()]
        out["verdicts"] = {"register_matched": "HUMAN-MOVES" if ps and min(ps) < 0.01
                           else "NO-DIFFERENCE"}
        print(f"\n  >>> {out['verdicts']['register_matched']}")
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "summary_fiction.json").write_text(json.dumps(out, indent=2),
                                                     encoding="utf-8", newline="\n")
        print(f"wrote {(RESULTS / 'summary_fiction.json').relative_to(REPO)}")
        return
    mach = [r["variance"] for r in rows if r["group"] in ("ladder2", "ladder3")]
    if hb and mach:
        u, p = stats.mannwhitneyu(hb, mach, alternative="greater")
        out["tests"]["human_vs_machine"] = {
            "books_median": float(np.median(hb)), "machine_median": float(np.median(mach)),
            "p": float(p)}
        print(f"\n  variance: books median {np.median(hb):.4f} vs machine {np.median(mach):.4f}"
              f"  (one-sided p={p:.4f})")
    for corpus in ("ladder2", "ladder3"):
        sub = [r for r in rows if r["group"] == corpus and isinstance(r["rung"], int)]
        rung = np.array([r["rung"] for r in sub], float)
        wds = np.array([r["n_windows"] for r in sub], float)
        v = np.array([r["variance"] for r in sub], float)
        rho, p = stats.spearmanr(rres(v, wds), rres(rung, wds))
        out["tests"][f"rung_vs_variance_{corpus}"] = {"rho": float(rho), "p": float(p)}
        print(f"  {corpus}: rung vs within-artifact variance rho {rho:+.3f}  p={p:.4f}")

    hm = out["tests"].get("human_vs_machine", {})
    v1 = "HUMAN-MOVES" if hm.get("p", 1) < 0.01 else "NO-DIFFERENCE"
    tracks = any(abs(t["rho"]) > 0.3 and t["p"] < 0.01
                 for k, t in out["tests"].items() if k.startswith("rung_vs"))
    v2 = "RUNG-TRACKS" if tracks else "RUNG-FLAT"
    out["verdicts"] = {"human_vs_machine": v1, "rung": v2}
    print(f"\n  >>> {v1} | {v2}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(out, indent=2),
                                          encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
