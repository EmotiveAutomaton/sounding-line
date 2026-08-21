"""Multiple-comparison audit — every p-value this project has ever quoted, corrected at last.

── WHY ───────────────────────────────────────────────────────────────────────────────────────

`FINDINGS.md`, known weakness 1: **this project has never corrected for multiple comparisons.**
Roughly twenty-five tests have been run and reported at p < 0.05 as though each were the only one.
At that rate at least one false positive is expected from chance alone, and we have no idea which
of our numbers it is.

This does the correction retrospectively. It is deliberately unflattering and it should be.

── HOW THE LIST WAS BUILT ────────────────────────────────────────────────────────────────────

**Hand-collected from the verdict files, with the source named for every row**, rather than scraped.
Scraping JSON for anything called "p" would silently mix primary tests with diagnostics and controls,
and the whole point is to be able to argue about what belongs in the family.

**Family definition matters more than the arithmetic here**, so it is explicit and contestable:

    PRIMARY     a test whose result was used to support or reject a claim about the instrument.
    CONTROL     a test run to invalidate one of our own measures.
    DIAGNOSTIC  descriptive, never used to support a claim. Excluded from both families.

── WHICH FAMILY GETS CORRECTED — AN ARGUMENT WE HAD, SETTLED BY REPORTING BOTH ───────────────

I originally corrected only the primary family, on the grounds that correcting controls "makes it
harder to kill a measure, which is backwards." **The curator pushed back and he is substantially
right:** killing a good measure is a real error with a real cost, and weakness 3b is a demonstrated
instance of exactly that happening here.

Where I still disagree, and it is narrow: **multiplicity correction is the wrong instrument for that
failure.** The control over-firing we actually found was C2's length correlation at rho = −0.274,
p = 0.0102, and the error was interpretive — treating any length correlation as fatal without
checking the *direction* of the relationship. No FDR adjustment would have caught it.

The residual disagreement is a judgement about relative costs, not a fact:

    correcting controls   fewer good measures killed for nothing  (fewer Type I on the control)
    NOT correcting them   fewer confounded measures survive       (fewer Type II on the control)

I think the second matters more, because a confounded measure that survives becomes a claim. That is
a position, not arithmetic, so **both families are now reported under both corrections** and the
reader can hold whichever bar they prefer. It costs nothing and removes my judgement from the result.

Both Benjamini-Hochberg and Benjamini-Yekutieli are reported. **BY is the honest one here** -- our
tests reuse the same corpora and the same measures, so they are dependent in unknown directions, and
BH is only valid under independence or positive dependence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "audit"

# (name, p, family, source)  -- family: primary | control | diagnostic
TESTS = [
    # ── PRIMARY: used to support or reject a claim ────────────────────────────────────────────
    ("G3.1 method unlock, A vs B",        0.68,      "primary", "results/gate3/VERDICT.md"),
    ("W-1 wall as displacement",          0.53,      "primary", "results/wall/VERDICT.md"),
    ("rich vs thin, scale_gain",          0.0032,    "primary", "results/controls/VERDICT.md"),
    ("human vs no-maker, scale_gain",     0.0005,    "primary", "results/controls/VERDICT.md"),
    ("ladder: causal_rate vs rung",       1e-6,      "primary", "results/ladder/ladder.json"),
    ("ladder: you_rate vs rung",          1e-7,      "primary", "results/ladder/ladder.json"),
    ("ladder: insight_rate vs rung",      0.0009,    "primary", "results/ladder/ladder.json"),
    ("ladder: i_rate vs rung",            0.0034,    "primary", "results/ladder/ladder.json"),
    ("L23 fair induction, ladder",     3.727e-04, "primary", "results/induction_v2/ladder.json"),
    ("L23 fair induction, ladder2",    1.223e-05, "primary", "results/induction_v2/ladder2.json"),
    ("L23 fair induction, ladder3",    2.155e-06, "primary", "results/induction_v2/ladder3.json"),
    ("L1 held-out ratio, length ctrl",   2.897e-05, "primary", "results/induction/layer_ratio_induction.json"),
    ("L24 biber_COND fair, ladder",        3.402e-07, "primary", "results/fair_features/summary.json"),
    ("L24 biber_PHC fair, ladder",        3.423e-03, "primary", "results/fair_features/summary.json"),
    ("L24 biber_COND fair, ladder2",       4.834e-08, "primary", "results/fair_features/summary.json"),
    ("L24 biber_PHC fair, ladder2",       6.980e-03, "primary", "results/fair_features/summary.json"),
    ("L44 ratio-vs-rung, mean pooling",   7.843e-01, "primary", "results/pooling_falsifier/Qwen2.5-1.5B.json"),
    ("L44 ratio-vs-rung, last pooling",   1.776e-01, "primary", "results/pooling_falsifier/Qwen2.5-1.5B.json"),
    ("L44 ratio-vs-rung, max pooling",    3.450e-02, "primary", "results/pooling_falsifier/Qwen2.5-1.5B.json"),
    ("L47 late agreement falls, ladder",  1.857e-03, "primary", "results/coherence_v2/Qwen2.5-1.5B.json"),
    ("L47 late agreement falls, ladder2", 3.842e-03, "primary", "results/coherence_v2/Qwen2.5-1.5B.json"),
    ("L47 late agreement falls, ladder3", 2.270e-04, "primary", "results/coherence_v2/Qwen2.5-1.5B.json"),
    ("L53 PD-1 v3 side difference",       2.600e-08, "primary", "results/positional_polish/summary.json"),
    ("L55 essay-boundness split",         1.000e-04, "primary", "results/positional_polish/summary_b.json"),
    ("L57 author-share split",            6.090e-07, "primary", "results/positional_polish/pd33_decomposition.json"),
    ("L71 PD-33b books polish-vs-depth",  2.825e-07, "primary", "results/positional_polish/pd33_books.json"),
    ("L73 G130c matched margin McNemar",  4.534e-04, "primary", "results/arg_recovery/matched_k4_recovery.json"),
    ("L132 G129 reader-vs-block McNemar", 9.750e-03, "primary", "results/g129/verdict.json"),
    # L138 G158 baselines: permutation p at the 200-draw floor (0.005) except where noted;
    # exploratory measurements of how readable the G131 cells are from cheap features,
    # classed as diagnostics (they gate nothing; they set the bar recovery must beat)
    ("L138 G158 target from length",      0.0050, "diagnostic", "results/g158/baselines.json"),
    ("L138 G158 target from paragraphs",  0.0249, "diagnostic", "results/g158/baselines.json"),
    ("L138 G158 target from punctuation", 0.0050, "diagnostic", "results/g158/baselines.json"),
    ("L138 G158 target from lexical echo", 0.0050, "diagnostic", "results/g158/baselines.json"),
    ("L138 G158 target from all combined", 0.0050, "diagnostic", "results/g158/baselines.json"),
    ("L138 G158 amount from length",      0.8657, "diagnostic", "results/g158/baselines.json"),
    ("L138 G158 amount from all combined", 0.0050, "diagnostic", "results/g158/baselines.json"),
    ("L141 G129b reader-vs-block McNemar", 1.571e-02, "primary", "results/g129b/verdict.json"),
    # L142 G97: the intercept p is VOID-BY-CONSTRUCTION (pool z-scoring forces the mean
    # to zero); registered as diagnostic so the quoted number is on the ledger with its label
    ("L142 G97 diff intercept (void-by-construction)", 0.8702, "diagnostic",
     "results/g97/maker_effect.json"),
    ("L146 G159 execution effect two-proportion z", 1.1e-19, "primary",
     "results/g159/verdict.json"),
    ("L151 G165 self-route McNemar vs direct", 1.0, "primary",
     "results/g165/verdict.json"),
    ("L151 G165 cand-disc McNemar vs direct", 0.79053, "primary",
     "results/g165/verdict.json"),
    ("L153 G165-D self-route McNemar vs direct (HURTS)", 0.00062, "primary",
     "results/g165d/verdict.json"),
    ("L153 G165-D cand-disc McNemar vs direct", 0.16092, "primary",
     "results/g165d/verdict.json"),
    ("L74 PD-34 books movement split",    1.263e-05, "primary", "results/positional_polish/pd34_books.json"),
    ("L74 PD-34 essays movement split",   4.207e-01, "primary", "results/positional_polish/pd34_argrewrite.json"),
    ("L89 PD-3 machine movement",         2.015e-06, "primary", "results/positional_polish/pd3_ladder3.json"),
    ("L89 PD-33 books w40",               3.608e-06, "primary", "results/positional_polish/pd33_books_w40.json"),
    ("L89 PD-2 books signed wilcoxon",    1.180e-02, "primary", "results/positional_polish/pd2_signed_books.json"),
    ("L89 PD-2 essays signed wilcoxon",   3.600e-06, "primary", "results/positional_polish/pd2_signed_argrewrite.json"),
    ("L89 PD-34 books w40",               1.501e-01, "primary", "results/positional_polish/pd34_books_w40.json"),
    ("L89 PD-34 essays w40",              2.831e-01, "primary", "results/positional_polish/pd34_argrewrite_w40.json"),
    ("L90 machine signed rise wilcoxon",  3.000e-06, "primary", "results/positional_polish/pd2_signed_ladder3.json"),
    ("L90 essays w40 signed wilcoxon",    4.000e-06, "primary", "results/positional_polish/pd2_signed_argrewrite_w40.json"),
    ("L90 books w40 signed wilcoxon",     1.000e+00, "primary", "results/positional_polish/pd2_signed_books_w40.json"),
    ("L90 machine w40 movement",          2.030e-04, "primary", "results/positional_polish/pd3_ladder3_w40.json"),
    ("L91 G29 leaked author perm",        3.280e-02, "primary", "results/g28_twolayers/g29_layers.json"),
    ("L91 G29 emblematic author perm",    1.640e-02, "primary", "results/g28_twolayers/g29_layers.json"),
    ("L92 G80 human vs machine",          2.820e-03, "primary", "results/g80_scaffolding/summary.json"),
    ("L92 G80 human vs books",            1.590e-01, "primary", "results/g80_scaffolding/summary.json"),
    ("L94 G76 fw fair perm, ladder",      2.200e-01, "primary", "results/g76_fw_induction.json"),
    ("L94 G76 fw fair perm, ladder2",     2.500e-03, "primary", "results/g76_fw_induction.json"),
    ("L94 G76 fw fair perm, ladder3",     2.500e-03, "primary", "results/g76_fw_induction.json"),
    ("L95 PD-11 powered rerun binomial",  2.641e-09, "primary", "results/d0b/d0b_rerun_k20.json"),
    ("L97 fiction qwen signed wilcoxon",  8.788e-03, "primary", "results/positional_polish/pd2_signed_fiction_qwen.json"),
    ("L97 fiction ds signed wilcoxon",    5.513e-02, "primary", "results/positional_polish/pd2_signed_fiction_ds.json"),
    ("L97 fiction qwen unsigned MW",      5.280e-04, "primary", "results/positional_polish/pd34_fiction_qwen.json"),
    ("L97 fiction ds unsigned MW",        1.590e-01, "primary", "results/positional_polish/pd34_fiction_ds.json"),
    ("L98 G80 human vs fiction qwen",     4.760e-01, "primary", "results/g80_scaffolding/summary_fiction.json"),
    ("L98 G80 human vs fiction ds",       3.370e-01, "primary", "results/g80_scaffolding/summary_fiction.json"),
    ("L99 G107 powered count",            1.000e+00, "primary", "results/audit/nomaker_permutation_powered.json"),
    ("L99 G107 second-family count",      1.650e-01, "primary", "results/audit/nomaker_permutation_ds.json"),
    ("L100 fiction qwen r2 wilcoxon",     7.020e-03, "primary", "results/positional_polish/pd2_signed_fiction_qwen_r2.json"),
    ("L100 fiction ds r2 wilcoxon",       4.447e-02, "primary", "results/positional_polish/pd2_signed_fiction_ds_r2.json"),
    ("L101 books vs fiction qwen",        5.560e-01, "primary", "results/activation_variance/summary_fiction.json"),
    ("L101 books vs fiction ds",          2.740e-04, "primary", "results/activation_variance/summary_fiction.json"),
    ("L103 llama-reasoning wilcoxon",     2.800e-03, "primary", "results/positional_polish/pd2_signed_fiction_r1l8.json"),
    ("L103 llama-instruct wilcoxon",      3.800e-05, "primary", "results/positional_polish/pd2_signed_fiction_llama.json"),
    ("L105 w40 qwen signed",              1.293e-01, "primary", "results/positional_polish/pd2_signed_fiction_qwen_w40.json"),
    ("L105 w40 ds signed",                1.776e-01, "primary", "results/positional_polish/pd2_signed_fiction_ds_w40.json"),
    ("L105 w40 r1l8 signed",              5.800e-03, "primary", "results/positional_polish/pd2_signed_fiction_r1l8_w40.json"),
    ("L105 w40 llama signed",             1.000e-04, "primary", "results/positional_polish/pd2_signed_fiction_llama_w40.json"),
    ("L105 reader books vs r1l8",         1.000e-05, "primary", "results/activation_variance/summary_fiction4.json"),
    ("L105 reader books vs llama n3",     4.610e-02, "primary", "results/activation_variance/summary_fiction4.json"),
    ("L105 g80 drafts vs r1l8",           4.520e-02, "primary", "results/g80_scaffolding/summary_fiction4.json"),
    ("L113 pd34 r1l8 unsigned",           3.785e-01, "primary", "results/positional_polish/pd34_fiction_r1l8.json"),
    ("L113 pd34 llama unsigned",          8.100e-03, "primary", "results/positional_polish/pd34_fiction_llama.json"),
    ("L116 pd34 qwen w40",                7.834e-04, "primary", "results/positional_polish/pd34_fiction_qwen_w40.json"),
    ("L116 pd34 ds w40",                  3.661e-02, "primary", "results/positional_polish/pd34_fiction_ds_w40.json"),
    ("L116 pd34 llama w40",               2.663e-01, "primary", "results/positional_polish/pd34_fiction_llama_w40.json"),
    ("L116 pd34 r1l8 w40",                8.105e-02, "primary", "results/positional_polish/pd34_fiction_r1l8_w40.json"),
    ("L44v2 pooling max arm",             2.900e-03, "primary", "results/pooling_falsifier/Qwen2.5-1.5B_v2.json"),
    ("L44v2 pooling last-token arm",      2.820e-01, "primary", "results/pooling_falsifier/Qwen2.5-1.5B_v2.json"),
    ("L24 biber_CONT fair, ladder",       1.700e-03, "primary", "results/fair_features/summary.json"),
    ("L24 biber_CONT fair, ladder2",      4.490e-07, "primary", "results/fair_features/summary.json"),
    ("L24 biber_COND fair, ladder3",      1.590e-13, "primary", "results/fair_features/summary.json"),
    ("L24 biber_CONT fair, ladder3",      5.290e-03, "primary", "results/fair_features/summary.json"),
    ("L24 biber_PHC fair, ladder3",       7.100e-05, "primary", "results/fair_features/summary.json"),
    ("L19 echo restriction, ladder2",     3.068e-01, "primary", "results/spec_recovery/ladder2_noecho.json"),
    ("L28 gpt2-medium, ladder",           3.246e-05, "primary", "results/induction_v2/ladder_gpt2-medium.json"),
    ("L28 gpt2-medium, ladder2",          4.623e-08, "primary", "results/induction_v2/ladder2_gpt2-medium.json"),
    ("L28 gpt2-medium, ladder3",          8.486e-04, "primary", "results/induction_v2/ladder3_gpt2-medium.json"),
    ("L28 SmolLM2, ladder3",              9.441e-03, "primary", "results/induction_v2/ladder3_SmolLM2-360M.json"),
    ("L28 Qwen-0.5B, ladder3",            2.547e-03, "primary", "results/induction_v2/ladder3_Qwen2.5-0.5B.json"),
    ("L28 gpt2-large, ladder",            8.601e-05, "primary", "results/induction_v2/ladder_gpt2-large.json"),
    ("L28 gpt2-large, ladder2",           2.291e-06, "primary", "results/induction_v2/ladder2_gpt2-large.json"),
    ("L28 pythia-410m, ladder3",          3.029e-03, "primary", "results/induction_v2/ladder3_pythia-410m.json"),
    ("L32 nomaker specrec wins",          6.100e-03, "primary", "results/spec_recovery/nomaker_control.json"),
    ("L33 provenance framing, ratio",     5.588e-09, "primary", "results/provenance_framing/ladder2.json"),
    ("ladder: tentative_rate vs rung",    0.0133,    "primary", "results/ladder/ladder.json"),
    ("ladder: exclusive_rate vs rung",    0.0917,    "primary", "results/ladder/ladder.json"),
    ("ladder: TTR vs rung",               1e-5,      "primary", "results/ladder/ladder.json"),
    ("ladder: scale_gain vs rung",        1e-5,      "primary", "results/ladder/ladder.json"),
    ("layer ratio vs rung (THE ONE)",     0.0529,    "primary", "results/layer_ratio/layer_ratio.json"),
    ("layer ratio human vs machine",      1.96e-15,  "primary", "results/shuffle_sweep/VERDICT.md"),
    ("causal_rate transfer: vs rich",     0.0011,    "primary", "results/rung_minus1/VERDICT.md"),
    ("causal_rate transfer: vs thin",     0.025,     "primary", "results/rung_minus1/VERDICT.md"),
    ("causal_rate transfer: vs averaged", 0.069,     "primary", "results/rung_minus1/VERDICT.md"),
    ("diversity: career vs breadth",      0.65,      "primary", "results/diversity/VERDICT.md"),
    ("diversity: sign test",              0.62,      "primary", "results/diversity/VERDICT.md"),

    # ── CONTROL: run to invalidate our own measures. Excluded from the family. ─────────────────
    ("C2 layer ratio vs word count",      0.0102,    "control", "results/layer_ratio/VERDICT_CONTROL.md"),
    ("C3 register: half A vs half B",     0.0033,    "control", "results/layer_ratio/VERDICT_CONTROL.md"),
    ("ladder void: rung vs length",       0.0037,    "control", "results/ladder/VERDICT.md"),
    ("sweep: sentence-shuffled gap",      1.97e-14,  "control", "results/shuffle_sweep/VERDICT.md"),
    ("sweep: word-shuffled gap",          5.83e-16,  "control", "results/shuffle_sweep/VERDICT.md"),
]


def bh(ps: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted p-values (step-up, monotone-enforced)."""
    n = len(ps)
    order = sorted(range(n), key=lambda i: ps[i])
    adj = [0.0] * n
    prev = 1.0
    for rank, i in enumerate(reversed(order), start=1):
        k = n - rank + 1
        prev = min(prev, ps[i] * n / k)
        adj[i] = prev
    return adj


def by(ps: list[float]) -> list[float]:
    """Benjamini-Yekutieli: BH scaled by the harmonic number. Valid under arbitrary dependence."""
    n = len(ps)
    c = sum(1.0 / k for k in range(1, n + 1))
    return [min(1.0, p * c) for p in bh(ps)]


def report(fam: list[tuple], title: str) -> tuple[list[dict], dict]:
    ps = [t[1] for t in fam]
    a_bh, a_by = bh(ps), by(ps)
    print(f"\n{'=' * 82}\n{title}  (n = {len(fam)})\n{'=' * 82}")
    print(f"{'test':<36}{'raw p':>11}{'BH':>11}{'BY':>11}  verdict")
    print("-" * 82)
    rows = []
    for (name, p, kind, src), b, y in sorted(zip(fam, a_bh, a_by), key=lambda z: z[0][1]):
        mark = ("survives" if y < 0.05 else
                "SURVIVES BH ONLY" if b < 0.05 else
                ">>> LOST" if p < 0.05 else "was never significant")
        print(f"{name:<36}{p:>11.2e}{b:>11.3f}{y:>11.3f}  {mark}")
        rows.append({"test": name, "kind": kind, "p_raw": p, "p_bh": b, "p_by": y,
                     "sig_raw": p < 0.05, "sig_bh": b < 0.05, "sig_by": y < 0.05,
                     "source": src})
    summ = {"n": len(fam),
            "n_sig_raw": sum(r["sig_raw"] for r in rows),
            "n_sig_bh": sum(r["sig_bh"] for r in rows),
            "n_sig_by": sum(r["sig_by"] for r in rows),
            "expected_false_positives": round(0.05 * len(fam), 1),
            "lost_to_BY": [r["test"] for r in rows if r["sig_raw"] and not r["sig_by"]]}
    print(f"\nsignificant uncorrected {summ['n_sig_raw']:>3} | BH {summ['n_sig_bh']:>3} | "
          f"BY {summ['n_sig_by']:>3}   (expected false positives uncorrected: "
          f"{summ['expected_false_positives']})")
    if summ["lost_to_BY"]:
        print("LOST TO CORRECTION: " + "; ".join(summ["lost_to_BY"]))
    return rows, summ


def main() -> None:
    fam = [t for t in TESTS if t[2] == "primary"]
    ps = [t[1] for t in fam]
    a_bh, a_by = bh(ps), by(ps)

    print(f"{len(TESTS)} tests collected; {len(fam)} in the correction family "
          f"(controls excluded, see module docstring)\n")
    print(f"{'test':<36}{'raw p':>11}{'BH':>11}{'BY':>11}  verdict")
    print("-" * 82)
    rows = []
    for (name, p, _, src), b, y in sorted(zip(fam, a_bh, a_by), key=lambda z: z[0][1]):
        keep_raw = p < 0.05
        keep_bh = b < 0.05
        keep_by = y < 0.05
        mark = ("survives" if keep_by else
                "SURVIVES BH ONLY" if keep_bh else
                ">>> LOST" if keep_raw else "was never significant")
        print(f"{name:<36}{p:>11.2e}{b:>11.3f}{y:>11.3f}  {mark}")
        rows.append({"test": name, "p_raw": p, "p_bh": b, "p_by": y,
                     "sig_raw": keep_raw, "sig_bh": keep_bh, "sig_by": keep_by, "source": src})

    n_raw = sum(r["sig_raw"] for r in rows)
    n_bh = sum(r["sig_bh"] for r in rows)
    n_by = sum(r["sig_by"] for r in rows)
    lost = [r["test"] for r in rows if r["sig_raw"] and not r["sig_by"]]

    print("\n" + "=" * 82)
    print(f"significant at p<0.05 uncorrected : {n_raw} of {len(fam)}")
    print(f"                    after BH      : {n_bh}")
    print(f"                    after BY      : {n_by}   <- the honest one")
    print(f"expected false positives, uncorrected: {0.05 * len(fam):.1f}")
    if lost:
        print("\nLOST TO CORRECTION:")
        for t in lost:
            print(f"  - {t}")
    print("=" * 82)

    # ── the curator's position, run as a sensitivity analysis rather than argued about ─────────
    ctrl = [t for t in TESTS if t[2] == "control"]
    rows_c, summ_c = report(ctrl, "CONTROLS, corrected — the curator's position")
    rows_all, summ_all = report([t for t in TESTS if t[2] in ("primary", "control")],
                                "EVERYTHING IN ONE FAMILY — the most conservative reading")

    print("\n" + "=" * 82)
    print("DOES THE CHOICE OF FAMILY CHANGE ANY CONCLUSION?")
    print("=" * 82)
    by_prim = {r["test"]: r["sig_by"] for r in rows}
    flips = [r["test"] for r in rows_all
             if r["kind"] == "primary" and by_prim.get(r["test"]) != r["sig_by"]]
    if flips:
        print("  Conclusions that FLIP when controls join the family:")
        for t in flips:
            print(f"    - {t}")
    else:
        print("  No primary conclusion changes. The disagreement about family membership is")
        print("  real but does not move a single verdict, so it can be recorded and set aside.")
    ctrl_lost = summ_c["lost_to_BY"]
    print(f"\n  Controls that would stop firing if corrected: "
          f"{', '.join(ctrl_lost) if ctrl_lost else 'none'}")
    if not ctrl_lost:
        print("  -> every control that killed a measure would still kill it under correction.")
        print("     So the argument is moot on this data, whichever side is right in principle.")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "multiplicity.json").write_text(json.dumps(
        {"primary": {"summary": {"n_family": len(fam), "n_sig_raw": n_raw, "n_sig_bh": n_bh,
                                 "n_sig_by": n_by, "lost_to_correction": lost}, "tests": rows},
         "controls_corrected": {"summary": summ_c, "tests": rows_c},
         "all_one_family": {"summary": summ_all, "tests": rows_all},
         "primary_conclusions_that_flip": flips,
         "controls_that_would_stop_firing": ctrl_lost}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / 'multiplicity.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
