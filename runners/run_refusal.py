"""The refusal rescore, and the no-maker control that Gate 3 never had.

── PRE-REGISTERED BEFORE THE NUMBERS ARE SEEN ────────────────────────────────────────────────

**R-1, the real test.** The three locked generated artifacts have **no reconstructible maker** by
construction. If refusal measures resistance to a maker-shaped explanation, they must refuse MORE
than human artifacts.

    PASS   generated exceeds the human mean on at least 3 of the 5 components
    FAIL   2 or fewer

This is the N28-analogue Gate 3 never had, applied to the successor measure BEFORE it is used for
anything. Method unlock failed exactly this check — generated artifacts unlocked at 1.111 against
commercial work at 0.917 — and the whole reason to write the criterion first is that the last
measure was allowed to skip it.

**R-2, exploratory and labelled as such.** Half A against Half B. **No directional prediction is
made**, and that is deliberate: the theory's refusal claim is about NON-INVERTIBLE content, which
is machine content, not commercial content. A careful essay and a competent sales page may both be
perfectly invertible. Anything R-2 shows is a hypothesis for a later corpus, not a result.

**R-3.** Does refusal correlate with method unlock? If it does, it is the same broken measure in
new clothes. **It should not.**

── WHAT THIS CANNOT SHOW ─────────────────────────────────────────────────────────────────────

Three generated artifacts. n = 3 against n = 50. A pass licenses building on refusal; it does not
establish anything about prevalence, and it certainly does not detect machines — a human artifact
that resists explanation refuses too, which is the point rather than a flaw.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.measures.refusal import Refusal, from_profile, summarise   # noqa: E402

RESULTS = REPO / "results" / "refusal"
GEN = REPO / "results" / "generated_refusal.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-generated", action="store_true",
                    help="read the three locked generated artifacts through the live pipeline")
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    d = json.loads((REPO / "results" / "gate3" / "gate3_local_k5.json").read_text(encoding="utf-8"))
    arts = {k: v for k, v in d["artifacts"].items() if v.get("bounded", {}).get("k", 0) >= 2}
    halves = {h: [from_profile(v["bounded"]) for v in arts.values() if v["half"] == h]
              for h in ("A", "B")}
    human = halves["A"] + halves["B"]

    if args.run_generated:
        from soundingline.locks import verify_all                     # noqa: PLC0415
        from soundingline.loop.run import run_loop                    # noqa: PLC0415
        from soundingline.probe.client import make_client             # noqa: PLC0415
        from soundingline.probe.render import Artifact                # noqa: PLC0415
        from runners.run_gate3 import profile                         # noqa: PLC0415
        verify_all()
        out = {}
        for p in sorted((REPO / "docs" / "gate1" / "artifacts").glob("item_*.md")):
            text = p.read_text(encoding="utf-8")
            runs = []
            for s in range(args.k):
                try:
                    runs.append(run_loop(make_client("local", seed=s),
                                         Artifact(text=text[:12000], source_id=p.stem), seed=s))
                except Exception as e:                                # noqa: BLE001
                    print(f"  {p.stem} seed {s}: {type(e).__name__}", flush=True)
            out[p.stem] = profile(runs, text)
            print(f"  {p.stem:<8} k={out[p.stem].get('k', 0)}/{args.k}", flush=True)
        GEN.write_text(json.dumps(out, indent=2), encoding="utf-8")

    if not GEN.exists():
        print("no generated-artifact readings yet; run with --run-generated")
        return
    gen = [from_profile(v) for v in json.loads(GEN.read_text(encoding="utf-8")).values()
           if v.get("k", 0) >= 2]

    hs, gs = summarise(human), summarise(gen)
    print(f"\nREFUSAL PANEL   human n={hs['n']}   generated n={gs['n']}")
    print(f"  {'component':<18}{'human':>9}{'generated':>12}{'diff':>9}")
    wins = 0
    for key in ("unnameable", "unconcentrated", "unconverged", "unattempted", "unmoved"):
        diff = gs[key] - hs[key]
        wins += diff > 0
        print(f"  {key:<18}{hs[key]:>9.3f}{gs[key]:>12.3f}{diff:>+9.3f}"
              f"{'  <-- refuses more' if diff > 0 else ''}")
    print(f"  {'n_refused (of 5)':<18}{hs['n_refused']:>9.2f}{gs['n_refused']:>12.2f}")

    verdict = "PASS" if wins >= 3 else "FAIL"
    print(f"\n>>> R-1 {verdict}   generated refuses more on {wins} of 5 components")
    if verdict == "PASS":
        print("    No-maker content resists a maker-shaped explanation more than human content.")
        print("    Method unlock failed this same check. Refusal may be built on.")
    else:
        print("    Refusal does not distinguish no-maker content. It fails the control that")
        print("    disqualified method unlock, and it should not be built on either.")

    print(f"\nR-2 (exploratory, no prediction was made)")
    print(f"  {'component':<18}{'half A':>9}{'half B':>9}{'diff':>9}")
    for key in ("unnameable", "unconcentrated", "unconverged", "unattempted", "unmoved"):
        a, b = summarise(halves['A'])[key], summarise(halves['B'])[key]
        print(f"  {key:<18}{a:>9.3f}{b:>9.3f}{b - a:>+9.3f}")

    # R-3: is this the broken measure again?
    from scipy import stats                                          # noqa: PLC0415
    pairs = [(from_profile(v["bounded"]), v["bounded"]["unlock"]) for v in arts.values()]
    for key in ("unnameable", "unconcentrated", "unconverged"):
        r, p = stats.spearmanr([x.components[key] for x, _ in pairs], [u for _, u in pairs])
        print(f"R-3  {key:<16} vs method unlock:  rho={r:+.3f}  p={p:.3f}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "refusal.json").write_text(json.dumps(
        {"human": hs, "generated": gs, "halves": {h: summarise(v) for h, v in halves.items()},
         "R1_verdict": verdict, "R1_components_higher": wins}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
