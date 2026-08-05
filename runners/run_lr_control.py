"""The control the human/machine layer-ratio result has not had.

Only the LADDER was shuffled. The ladder holds register and topic constant by construction; the
human/machine comparison holds nothing constant -- real web pages against generated prose, differing
in register, topic, formatting and provenance at once. A 52% gap between populations that differ in
everything is the shape of a confound, and shuffling is what has killed nine measures.

Three controls, all pre-registered here before the run:

    C1  SHUFFLE. Human and machine, word-shuffled. If the gap survives, it is vocabulary and the
        result dies. If it collapses, the measure needed word order on the comparison that matters.
    C2  LENGTH. Correlation of ratio with word count across the pooled set. Above 0.4 voids.
    C3  REGISTER-MATCHED. Gate 3's Half B is commercial web copy -- much closer in register to
        generated prose than Half A's essays are. If the gap is register, Half B should sit nearer
        the machine kinds than Half A does. If it is not, both halves sit together.

C3 is the one that cannot be faked by any shuffling argument, and it uses data already in hand.
"""
from __future__ import annotations
import json, random, statistics, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(REPO))
from runners.run_layer_ratio import load, ratio_for                    # noqa: E402
from runners.run_gate3 import load_corpus                              # noqa: E402

def main() -> None:
    from soundingline.probe.activations import DEFAULT_MODEL, Reader, fit_directions
    from runners.run_b import split
    from scipy import stats
    r = Reader(DEFAULT_MODEL, device="cuda")
    fit, _ = split(); d = fit_directions(r, fit)
    rng = random.Random(31)
    def shuf(t):
        w = t.split(); rng.shuffle(w); return " ".join(w)

    corpus = load_corpus()
    human = [(h, t) for _, h, t in corpus]
    nm = load(REPO / "corpora" / "nomaker", "kind")

    print("computing intact and shuffled ratios ...", flush=True)
    hi = [ratio_for(r, d, t) for _, t in human]
    hs = [ratio_for(r, d, shuf(t)) for _, t in human]
    mi = [ratio_for(r, d, x["text"]) for x in nm]
    ms = [ratio_for(r, d, shuf(x["text"])) for x in nm]

    def rep(label, a, b):
        t, p = stats.ttest_ind(a, b, equal_var=False)
        g = statistics.fmean(a) - statistics.fmean(b)
        print(f"  {label:<12} human {statistics.fmean(a):.4f}  machine {statistics.fmean(b):.4f}"
              f"   gap {g:+.4f}  p={p:.2e}")
        return {"human": statistics.fmean(a), "machine": statistics.fmean(b),
                "gap": g, "p": float(p)}

    print("\nC1  SHUFFLE")
    intact = rep("intact", hi, mi)
    shuffled = rep("shuffled", hs, ms)
    survival = abs(shuffled["gap"]) / abs(intact["gap"]) if intact["gap"] else float("nan")
    print(f"  gap survival under shuffling: {survival:.0%}"
          f"   >>> {'VOCABULARY — result dies' if survival > 0.5 else 'needs word order'}")

    print("\nC2  LENGTH")
    allr = hi + mi; allw = [len(t.split()) for _, t in human] + [len(x['text'].split()) for x in nm]
    rho, p = stats.spearmanr(allw, allr)
    print(f"  ratio vs word count: rho={rho:+.3f} p={p:.4f}"
          f"   >>> {'VOID' if abs(rho) > 0.4 else 'ok'}")

    print("\nC3  REGISTER  (Half B is commercial copy; if the gap is register it sits near machine)")
    A = [v for (h, _), v in zip(human, hi) if h == "A"]
    B = [v for (h, _), v in zip(human, hi) if h == "B"]
    tAB, pAB = stats.ttest_ind(A, B, equal_var=False)
    print(f"  half A {statistics.fmean(A):.4f}   half B {statistics.fmean(B):.4f}"
          f"   machine {statistics.fmean(mi):.4f}")
    print(f"  A vs B p={pAB:.4f}   B sits "
          f"{(statistics.fmean(B) - statistics.fmean(A)) / max(statistics.fmean(mi) - statistics.fmean(A), 1e-9):.0%}"
          f" of the way from A to machine")

    (REPO / "results" / "layer_ratio" / "control.json").write_text(json.dumps(
        {"C1_intact": intact, "C1_shuffled": shuffled, "survival": survival,
         "C2_length_rho": float(rho), "C3_halfA": statistics.fmean(A),
         "C3_halfB": statistics.fmean(B), "C3_machine": statistics.fmean(mi),
         "C3_p": float(pAB)}, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
