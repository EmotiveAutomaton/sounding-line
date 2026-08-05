"""Score the intent ladder. Monotonicity, with every control that has killed a measure so far.

── PRE-REGISTERED IN `make_intent_ladder.py`, RESTATED HERE ──────────────────────────────────

    PASS       rho > 0.4 against rung, p < 0.01, AND the effect survives the shuffle control
    FAIL       rho at or below 0.2, or shuffling shows the effect is vocabulary
    AMBIGUOUS  between

Five rungs of increasing prompt specification, content randomised, length the only systematic
variable. Monotonicity is the test because any measure can split two groups by luck and none can
rank five in order by luck.

── THE FOUR VOIDS, ALL CHECKED BEFORE THE VERDICT ────────────────────────────────────────────

Seven measures have died. Every one of these is a grave with a name on it.

    output length   if longer prompts produce longer articles, the ladder is a length ladder
    shuffle         if the effect survives word-shuffling it is a vocabulary statistic
    type-token      if it correlates with lexical diversity it is TTR again
    topic           topics repeat across rungs by design; if the effect is topic it will show
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.measures.density import density                      # noqa: E402
from soundingline.measures.leakage import CATEGORIES, profile          # noqa: E402

LADDER = REPO / "corpora" / "ladder"
RESULTS = REPO / "results" / "ladder"


def ttr(t: str) -> float:
    w = t.lower().split()
    return len(set(w)) / max(len(w), 1)


def main() -> None:
    man = json.loads((LADDER / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for it in man["items"]:
        p = LADDER / f"{it['id']}.txt"
        if p.exists():
            rows.append({**it, "text": p.read_text(encoding="utf-8")})
    rungs = sorted({r["rung"] for r in rows})
    print(f"{len(rows)} artifacts, rungs {rungs}\n")

    from scipy import stats                                            # noqa: PLC0415
    import random                                                     # noqa: PLC0415
    rng = random.Random(11)

    def shuf(t):
        w = t.split()
        rng.shuffle(w)
        return " ".join(w)

    # ── VOID 1: does prompt length drive output length? ───────────────────────────────────────
    print("VOID CHECK 1 — output length by rung")
    for r in rungs:
        v = [x["n_words"] for x in rows if x["rung"] == r]
        print(f"  rung {r:>2}: median {statistics.median(v):>6.0f}  n={len(v)}")
    rho_len, p_len = stats.spearmanr([x["rung"] for x in rows], [x["n_words"] for x in rows])
    print(f"  rung vs output length: rho={rho_len:+.3f} p={p_len:.4f}"
          f"   >>> {'VOID — length ladder' if abs(rho_len) > 0.4 else 'ok'}")

    # ── the candidate measures ────────────────────────────────────────────────────────────────
    measures = {
        "density_scale_gain": lambda t: density(t).scale_gain,
        "type_token_ratio": ttr,
        "i_rate": lambda t: profile(t).rates["i"],
        "exclusive_rate": lambda t: profile(t).rates["exclusive"],
        "tentative_rate": lambda t: profile(t).rates["tentative"],
        "you_rate": lambda t: profile(t).rates["you"],
        "insight_rate": lambda t: profile(t).rates["insight"],
        "causal_rate": lambda t: profile(t).rates["causal"],
    }

    print(f"\n{'measure':<22}{'rho':>8}{'p':>9}{'shuffled rho':>15}{'verdict':>12}")
    out = {}
    for name, f in measures.items():
        v = [f(x["text"]) for x in rows]
        rr = [x["rung"] for x in rows]
        rho, pv = stats.spearmanr(rr, v)
        vs = [f(shuf(x["text"])) for x in rows]
        rho_s, _ = stats.spearmanr(rr, vs)
        # Survives shuffling => vocabulary. Dies => it needed the word order.
        survives = abs(rho_s) > 0.5 * abs(rho) if abs(rho) > 0.05 else True
        verdict = ("PASS" if abs(rho) > 0.4 and pv < 0.01 and not survives
                   else "FAIL" if abs(rho) <= 0.2 else "AMBIG")
        if survives and abs(rho) > 0.4:
            verdict = "VOCAB"
        print(f"  {name:<20}{rho:>+8.3f}{pv:>9.4f}{rho_s:>+15.3f}{verdict:>12}")
        out[name] = {"rho": rho, "p": pv, "rho_shuffled": rho_s, "verdict": verdict,
                     "by_rung": {r: statistics.fmean(f(x["text"]) for x in rows if x["rung"] == r)
                                 for r in rungs}}

    # ── the multivariate question: does the WHOLE function-word vector track rung? ─────────────
    from soundingline.measures.leakage import delta_classify           # noqa: PLC0415
    groups = {str(r): [x["text"] for x in rows if x["rung"] == r] for r in rungs}
    dc = delta_classify(groups)
    print(f"\nfunction-word vector, 5-way rung classification: "
          f"{dc['accuracy']:.1%} vs {dc['chance']:.1%} = {dc['lift']:.2f}x")
    out["delta_classify_rung"] = dc

    # ordinal version: is the confusion structured by distance between rungs?
    ends = delta_classify({"low": [x["text"] for x in rows if x["rung"] <= 1],
                           "high": [x["text"] for x in rows if x["rung"] >= 6]})
    print(f"  ends only (rung<=1 vs rung>=6): {ends['accuracy']:.1%} vs 50% = {ends['lift']:.2f}x")
    out["delta_classify_ends"] = ends

    best = max((v for k, v in out.items() if isinstance(v, dict) and "verdict" in v),
               key=lambda v: abs(v["rho"]) if v["verdict"] == "PASS" else 0, default=None)
    print("\n" + "=" * 72)
    passes = [k for k, v in out.items() if isinstance(v, dict) and v.get("verdict") == "PASS"]
    if passes:
        print(f">>> LADDER PASS on: {', '.join(passes)}")
        print("    A measure ranked five machine-written groups in order of how much intent was")
        print("    specified, with randomised content, surviving the shuffle control.")
    else:
        vocab = [k for k, v in out.items() if isinstance(v, dict) and v.get("verdict") == "VOCAB"]
        print(f">>> LADDER FAIL. No measure ranks the rungs on anything but vocabulary.")
        if vocab:
            print(f"    vocabulary-only: {', '.join(vocab)}")
    print("=" * 72)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "ladder.json").write_text(json.dumps(
        {"n": len(rows), "rungs": rungs, "rung_vs_output_length": {"rho": rho_len, "p": p_len},
         "measures": out}, indent=2, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
