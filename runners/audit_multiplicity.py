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
    ("L161 G177 anchor binomial vs 0.25 floor", 1.5774e-28, "primary",
     "results/g177/anchor.json"),
    ("L163 G172 exact-vs-cross permutation", 4.9998e-05, "primary",
     "results/g172/verdict.json"),
    ("L163 G172 sibling-vs-cross permutation", 4.9998e-05, "primary",
     "results/g172/verdict.json"),
    ("L164 S02 paraphrased exact-vs-cross permutation", 4.99975e-05, "primary",
     "results/scouts/s02_erasure.json"),
    ("L164 S02 paraphrased sibling-vs-cross permutation", 4.99975e-05, "primary",
     "results/scouts/s02_erasure.json"),
    ("L165 crossed reversal, qwen makers (independent eraser)", 4.99975e-05, "primary",
     "results/scouts/s_wave1.json"),
    ("L165 crossed reversal, smollm makers", 4.99975e-05, "primary",
     "results/scouts/s_wave1.json"),
    ("L168 S07 alignment-inversion linkage", 8.7996e-03, "primary",
     "results/scouts/geo_link.json"),
    ("L168 S07 neutral-corpus replication", 4.99975e-05, "primary",
     "results/scouts/geo_link_neutral.json"),
    ("L168 S08 amp true-direction delta", 3.5e-03, "primary",
     "results/scouts/s8_transfer.json"),
    ("L168 S08 amp shuffled-control delta", 3.04e-02, "control",
     "results/scouts/s8_transfer.json"),
    ("L171 E02-S3 record-vs-nothing paired", 2.5999e-03, "primary",
     "results/phase_2_4_stage_3/E/E02/gate.json"),
    ("L177 S01-S3 qwen own-vs-other (all readers)", 4.9998e-05, "primary",
     "results/phase_2_4_stage_3/S/S01/verdict.json"),
    ("L177 S01-S3 smollm own-vs-other (all readers)", 4.4998e-04, "primary",
     "results/phase_2_4_stage_3/S/S01/verdict.json"),
    ("L177 S01-S3 olmo own-vs-other (all readers)", 4.9998e-05, "primary",
     "results/phase_2_4_stage_3/S/S01/verdict.json"),
    ("L179 S03-S3 exact-minus-cross gradient", 4.9998e-05, "primary",
     "results/phase_2_4_stage_3/S/S03/verdict.json"),
    ("L180 S05-S3 bottleneck qwen", 9.0995e-03, "primary",
     "results/phase_2_4_stage_3/S/S05/verdict.json"),
    ("L180 S05-S3 bottleneck smollm", 3.5498e-03, "primary",
     "results/phase_2_4_stage_3/S/S05/verdict.json"),
    ("L182 S07-S3 reserve olmo", 4.9998e-05, "primary",
     "results/phase_2_4_stage_3/S/S07/verdict.json"),
    ("L182 S07-S3 reserve qwen", 9.9995e-05, "primary",
     "results/phase_2_4_stage_3/S/S07/verdict.json"),
    ("L197 A02-S3 steering plus-shift", 6.4997e-04, "primary",
     "results/phase_2_4_stage_3/A/A02/anchor.json"),
    ("L197 A02-S3 steering minus-shift", 7.9996e-04, "primary",
     "results/phase_2_4_stage_3/A/A02/anchor.json"),
    ("L205 H01-S3 purpose-minus-detail qwen", 2.3299e-02, "primary",
     "results/phase_2_4_stage_3/H/H01/verdict.json"),
    ("L222 L01/X1-S3 twelve-seed pooled owl gap", 1.0000e+00, "primary",
     "results/phase_2_4_stage_3/L/L01/seeds7to12.json"),
    ("L223 V04/X4-S3 third-domain qwen binomial", 7.2000e-03, "primary",
     "results/phase_2_4_stage_3/V/V04/domain3.json"),
    ("L225 S05/X3-S3 olmo-eraser qwen", 6.8010e-01, "primary",
     "results/phase_2_4_stage_3/S/S05/eraser3.json"),
    ("L225 S05/X3-S3 olmo-eraser smollm", 7.8210e-01, "primary",
     "results/phase_2_4_stage_3/S/S05/eraser3.json"),
    ("L228 E03/X4-S3 process-domain qwen binomial", 7.4700e-03, "primary",
     "results/phase_2_4_stage_3/E/E03/domain2.json"),
    ("L229 C01/X4-S3 order-effect perm", 1.0000e+00, "primary",
     "results/phase_2_4_stage_3/C/C01/domain2.json"),
    ("L231 XV3-S3 stranger-hope above 0.833 binomial", 1.0000e-02, "primary",
     "results/phase_2_4_stage_3/X/XV3_verdict.json"),
    ("L233 H03-S3 social-intent qwen vs question-only", 1.0000e-08, "primary",
     "results/phase_2_4_stage_3/H/H03/verdict.json"),
    ("L233 H03-S3 social-intent smollm vs question-only", 7.0000e-06, "primary",
     "results/phase_2_4_stage_3/H/H03/verdict.json"),
    ("L235 S07-S3 reserve-only exact-minus-sibling qwen", 1.3000e-03, "primary",
     "results/phase_2_4_stage_3/S/S07/xfills.json"),
    ("L235 S07-S3 reserve-only exact-minus-sibling smollm", 8.7000e-03, "primary",
     "results/phase_2_4_stage_3/S/S07/xfills.json"),
    ("L236 S01-S3 corrected equal-reader qwen", 5.0000e-05, "primary",
     "results/phase_2_4_stage_4/AUDIT_STAGE3/s_trunk_equal_reader_contrast.json"),
    ("L236 S01-S3 corrected equal-reader smollm", 5.0000e-05, "primary",
     "results/phase_2_4_stage_4/AUDIT_STAGE3/s_trunk_equal_reader_contrast.json"),
    ("L236 S07-S3 corrected reserve qwen", 8.5000e-04, "primary",
     "results/phase_2_4_stage_4/AUDIT_STAGE3/s_trunk_equal_reader_contrast.json"),
    ("L236 S07-S3 corrected reserve smollm", 1.0000e-03, "primary",
     "results/phase_2_4_stage_4/AUDIT_STAGE3/s_trunk_equal_reader_contrast.json"),
    # Stage 4 landings (interval-first cards; the sign-flip permutation p is reported beside
    # every paired contrast and enters here when the entry quotes it)
    ("L239 C01-S4 bundle-minus-facts future choice", 1.9130e-01, "primary",
     "results/phase_2_4_stage_4/C01/metrics.json"),
    ("L239 C01-S4 incorrect-bundle cost (must be negative)", 5.0000e-05, "control",
     "results/phase_2_4_stage_4/C01/metrics.json"),
    ("L241 C02-S4 misleading-prior correction, 6 minus 0 records", 2.1000e-02, "primary",
     "results/phase_2_4_stage_4/C02/metrics.json"),
    ("L241 C02-S4 valid-prior benefit at 0 records", 2.5000e-03, "control",
     "results/phase_2_4_stage_4/C02/metrics.json"),
    ("L241 C02-S4 misleading-prior cost at 0 records", 5.0000e-05, "control",
     "results/phase_2_4_stage_4/C02/metrics.json"),
    ("L244 T01-S4 support effect on as-taught application, aligned (re-run 08-28 on 128 distinct constructions)", 5.0000e-05, "primary",
     "results/phase_2_4_stage_4/T01/metrics.json"),
    ("L244 T01-S4 support effect on as-taught application, misaligned (re-run 08-28)", 5.0000e-05, "primary",
     "results/phase_2_4_stage_4/T01/metrics.json"),
    ("L244 T01-S4 support effect on all-attempt relay, honest-aligned (re-run 08-28)", 1.0920e-01, "control",
     "results/phase_2_4_stage_4/T01/metrics.json"),
    ("L244 T01-S4 aligned primary, expanded to 256 worlds", 5.0000e-05, "primary",
     "results/phase_2_4_stage_4/T01/metrics.json"),
    ("L245 T02-S4 reconstruction minus summary, 256 worlds", 5.0000e-05, "primary",
     "results/phase_2_4_stage_4/T02/metrics.json"),
    ("L245 T02-S4 uptake clause, reconstruction minus direct accuracy", 4.3000e-02, "control",
     "results/phase_2_4_stage_4/T02/metrics.json"),
    ("L245 T02-S4 oracle minus reconstruction", 5.0000e-05, "control",
     "results/phase_2_4_stage_4/T02/metrics.json"),
    ("L239 C01-S4 bundle minus facts, expanded to 256 worlds", 1.3300e-01, "primary",
     "results/phase_2_4_stage_4/C01/metrics.json"),
    ("L239 C01-S4 unrelated negative control, 256 worlds", 1.1000e-02, "control",
     "results/phase_2_4_stage_4/C01/metrics.json"),
    ("L241 C02-S4 misleading-prior rise 6 minus 0, expanded to 256 worlds", 1.6000e-01, "primary",
     "results/phase_2_4_stage_4/C02/metrics.json"),
    ("L241 C02-S4 valid-prior benefit at 0 records, 256 worlds", 5.0000e-05, "control",
     "results/phase_2_4_stage_4/C02/metrics.json"),
    ("L241 C02-S4 summary route minus direct, misleading, 256 worlds", 7.0000e-03, "control",
     "results/phase_2_4_stage_4/C02/metrics.json"),
    ("L241 C02-S4 self-initialized route minus direct, valid, 256 worlds", 3.1000e-02, "control",
     "results/phase_2_4_stage_4/C02/metrics.json"),
    ("L244 T01-S4 aligned primary, confirmation on the fresh reserve", 5.0000e-05, "primary",
     "results/phase_2_4_stage_4/T01/confirmation/metrics.json"),
    ("L251 S05/X3b own-minus-other, Qwen, powered", 6.0900e-01, "primary",
     "results/phase_2_4_stage_3/S/S05/eraser3b.json"),
    ("L251 S05/X3b own-minus-other, SmolLM, powered", 3.6200e-01, "primary",
     "results/phase_2_4_stage_3/S/S05/eraser3b.json"),
    ("L252 C06/R2 conflict minus none, chose hinted, likelihood", 5.0000e-05, "primary",
     "results/phase_2_4_stage_3/C/C06/verdict_b.json"),
    ("L252 C06/R2 stranger minus none, chose hinted, likelihood", 5.0000e-05, "primary",
     "results/phase_2_4_stage_3/C/C06/verdict_b.json"),
    ("L252 C06/R2 agree minus none, accuracy", 1.0000e-03, "control",
     "results/phase_2_4_stage_3/C/C06/verdict_b.json"),
    ("L254 XV4/R4 scalar readout, swap null", 3.1000e-02, "control",
     "results/phase_2_4_stage_3/X/XV4b_verdict.json"),
    ("L254 XV4/R4 representation readout, swap null", 3.1000e-02, "primary",
     "results/phase_2_4_stage_3/X/XV4b_verdict.json"),
    ("L255 A07/R5 congruent minus zero, SmolLM to Qwen fold", 5.0000e-03, "primary",
     "results/phase_2_4_stage_3/A/A07/verdict_b.json"),
    ("L255 A07/R5 congruent minus zero, Qwen to SmolLM fold", 7.0000e-03, "primary",
     "results/phase_2_4_stage_3/A/A07/verdict_b.json"),
    ("L255 A07/R5 incongruent minus zero, fold 1", 3.5900e-01, "control",
     "results/phase_2_4_stage_3/A/A07/verdict_b.json"),
    ("L255 A07/R5 random minus zero, fold 1", 6.4300e-01, "control",
     "results/phase_2_4_stage_3/A/A07/verdict_b.json"),
    ("L257 S5/B01 congruent minus zero, SmolLM2 checkpoint, pooled", 7.4180e-01, "primary",
     "results/phase_2_4_stage_5/B01/verdict.json"),
    ("L257 S5/B01 incongruent minus zero, SmolLM2 checkpoint", 5.0000e-05, "control",
     "results/phase_2_4_stage_5/B01/metrics.json"),
    ("L257 S5/B01 random minus zero, SmolLM2 checkpoint", 5.0000e-05, "control",
     "results/phase_2_4_stage_5/B01/metrics.json"),
    ("L258 S5/B02 congruent minus zero, anchor, second domain, pooled", 5.6500e-03, "primary",
     "results/phase_2_4_stage_5/B02/verdict.json"),
    ("L258 S5/B02 incongruent minus zero, anchor, second domain", 3.7500e-03, "control",
     "results/phase_2_4_stage_5/B02/metrics.json"),
    ("L258 S5/B02 random minus zero, anchor, second domain", 1.0700e-01, "control",
     "results/phase_2_4_stage_5/B02/metrics.json"),
    ("L260 S5/B03 congruent minus zero, anchor", 5.0000e-05, "primary",
     "results/phase_2_4_stage_5/B03/verdict.json"),
    ("L260 S5/B03 random minus zero, anchor", 2.3900e-02, "control",
     "results/phase_2_4_stage_5/B03/metrics.json"),
    ("L260 S5/B03 shifted blocks minus zero", 1.0000e-04, "control",
     "results/phase_2_4_stage_5/B03/metrics.json"),
    ("L260 S5/B03 random blocks minus zero", 9.3000e-03, "control",
     "results/phase_2_4_stage_5/B03/metrics.json"),
    ("L260 S5/B03 permuted labels minus zero", 3.0000e-04, "control",
     "results/phase_2_4_stage_5/B03/metrics.json"),
    ("L260 S5/B03 reversed minus zero", 7.1400e-02, "control",
     "results/phase_2_4_stage_5/B03/metrics.json"),
    ("L260 S5/B03 incongruent minus zero", 4.7540e-01, "control",
     "results/phase_2_4_stage_5/B03/metrics.json"),
    ("L260 S5/B03 half dose minus zero", 2.4000e-03, "control",
     "results/phase_2_4_stage_5/B03/metrics.json"),
    ("L260 S5/B03 double dose minus zero", 4.0000e-04, "control",
     "results/phase_2_4_stage_5/B03/metrics.json"),
    ("L263 S5/J02 v1 recurrent minus best comparator (instrument dead)", 5.6970e-01, "primary",
     "results/phase_2_4_stage_5/J02/verdict.json"),
    ("L267 S5/A03 audience prompt gain, plain maker", 1.3430e-01, "control",
     "results/phase_2_4_stage_5/A03/metrics.json"),
    ("L267 S5/A03 audience prompt gain, audience-modeling maker", 6.1230e-01, "control",
     "results/phase_2_4_stage_5/A03/metrics.json"),
    ("L269 S5/A05 uptake reliable minus unreliable", 9.4040e-01, "primary",
     "results/phase_2_4_stage_5/A05/metrics.json"),
    ("L269 S5/A05 content-support shift", 7.9300e-02, "control",
     "results/phase_2_4_stage_5/A05/metrics.json"),
    ("L269 S5/A05 communicative-goal shift", 5.1000e-03, "control",
     "results/phase_2_4_stage_5/A05/metrics.json"),
    ("L270 S5/R01 reader minus first-listed", 5.0000e-05, "control",
     "results/phase_2_4_stage_5/R01/metrics.json"),
    ("L270 S5/R01 reader minus easiest", 5.0000e-05, "control",
     "results/phase_2_4_stage_5/R01/metrics.json"),
    ("L270 S5/R01 reader minus exact", 5.0000e-05, "control",
     "results/phase_2_4_stage_5/R01/metrics.json"),
    ("L271 S5/R02 reliance, six records minus two, plain", 5.0000e-05, "primary",
     "results/phase_2_4_stage_5/R02/metrics.json"),
    ("L271 S5/R02 reliance, plain minus stilted, six records", 7.7350e-02, "control",
     "results/phase_2_4_stage_5/R02/metrics.json"),
    ("L272 S5/R03 demonstration effect, diagnostic worlds", 4.5000e-04, "control",
     "results/phase_2_4_stage_5/R03/metrics.json"),
    ("L272 S5/R03 demonstration effect, non-diagnostic worlds", 6.0000e-04, "control",
     "results/phase_2_4_stage_5/R03/metrics.json"),
    ("L272 S5/R03 misleading minus none", 5.0000e-05, "control",
     "results/phase_2_4_stage_5/R03/metrics.json"),
    ("L273 S5/R04 reader minus random buyer, net gain per cost", 4.3640e-01, "primary",
     "results/phase_2_4_stage_5/R04/metrics.json"),
    ("L276 S5/F02 reader minus best raw baseline, realized gain", 9.8120e-01, "primary",
     "results/phase_2_4_stage_5/F02/metrics.json"),
    ("L277 S5/F03 pursuit, plain minus counter-bias, incongruent", 5.0000e-05, "primary",
     "results/phase_2_4_stage_5/F03/metrics.json"),
    ("L278 S5/J02 v2 recurrent minus best comparator", 5.5720e-01, "primary",
     "results/phase_2_4_stage_5/J02/v2/verdict.json"),
    ("L279 S5/J04 v2 opened minus fixed, conflict worlds", 2.9420e-01, "primary",
     "results/phase_2_4_stage_5/J04/v2/metrics.json"),
    ("L279 S5/J04 v2 opened minus fixed, consistent worlds (false alarm)", 7.3300e-02, "control",
     "results/phase_2_4_stage_5/J04/v2/metrics.json"),
    ("L280 S5/J05 v2 inferred preference minus topic baseline", 5.0000e-05, "primary",
     "results/phase_2_4_stage_5/J05/v2/metrics.json"),
    ("L285 S5R/B01 congruent minus zero, SmolLM2, fixed order", 9.0630e-01, "primary",
     "results/phase_2_4_stage_5r/B01/verdict.json"),
    ("L286 S5R/B02 congruent minus zero, anchor, second domain, fixed order", 1.0000e-04, "primary",
     "results/phase_2_4_stage_5r/B02/verdict.json"),
    ("L286 S5R/B02 incongruent minus zero", 1.1600e-02, "control",
     "results/phase_2_4_stage_5r/B02/metrics.json"),
    ("L286 S5R/B02 random minus zero", 6.3800e-01, "control",
     "results/phase_2_4_stage_5r/B02/metrics.json"),
    ("L288 S5R/B03 congruent minus zero, fixed order", 1.0000e-04, "primary",
     "results/phase_2_4_stage_5r/B03/verdict.json"),
    ("L288 S5R/B03 random minus zero", 9.9720e-01, "control",
     "results/phase_2_4_stage_5r/B03/metrics.json"),
    ("L288 S5R/B03 incongruent minus zero", 6.0130e-01, "control",
     "results/phase_2_4_stage_5r/B03/metrics.json"),
    ("L288 S5R/B03 reversed minus zero", 8.6000e-03, "control",
     "results/phase_2_4_stage_5r/B03/metrics.json"),
    ("L288 S5R/B03 shifted blocks minus zero", 2.0000e-04, "control",
     "results/phase_2_4_stage_5r/B03/metrics.json"),
    ("L288 S5R/B03 random blocks minus zero", 3.4200e-02, "control",
     "results/phase_2_4_stage_5r/B03/metrics.json"),
    ("L288 S5R/B03 permuted labels minus zero", 4.6000e-03, "control",
     "results/phase_2_4_stage_5r/B03/metrics.json"),
    ("L288 S5R/B03 half dose minus zero", 9.0000e-04, "control",
     "results/phase_2_4_stage_5r/B03/metrics.json"),
    ("L288 S5R/B03 double dose minus zero", 3.9000e-03, "control",
     "results/phase_2_4_stage_5r/B03/metrics.json"),
    ("L291 S5R/J02 recurrent minus best comparator, two readers", 2.6960e-01, "primary",
     "results/phase_2_4_stage_5r/J02/verdict.json"),
    ("L293 S5R/J05 inferred preference minus topic baseline, two readers", 5.0000e-05, "primary",
     "results/phase_2_4_stage_5r/J05/verdict.json"),
    ("L294 S5R/J04 opened minus fixed, conflict worlds, two readers", 3.3400e-01, "primary",
     "results/phase_2_4_stage_5r/J04/metrics.json"),
    ("L294 S5R/J04 opened minus fixed, consistent worlds (false alarm)", 9.3000e-02, "control",
     "results/phase_2_4_stage_5r/J04/metrics.json"),
    ("L297 S5R/A03 audience prompt gain, plain maker, two readers", 1.2000e-02, "control",
     "results/phase_2_4_stage_5r/A03/metrics.json"),
    ("L297 S5R/A03 audience prompt gain, audience-modeling maker", 6.4300e-01, "control",
     "results/phase_2_4_stage_5r/A03/metrics.json"),
    ("L299 S5R/A05 uptake reliable minus unreliable, two readers", 9.9010e-01, "primary",
     "results/phase_2_4_stage_5r/A05/metrics.json"),
    ("L299 S5R/A05 content-support shift", 1.4000e-02, "control",
     "results/phase_2_4_stage_5r/A05/metrics.json"),
    ("L299 S5R/A05 communicative-goal shift", 5.0000e-05, "control",
     "results/phase_2_4_stage_5r/A05/metrics.json"),
    ("L300 S5R/R01 reader minus first-listed, two readers", 5.0000e-05, "control",
     "results/phase_2_4_stage_5r/R01/metrics.json"),
    ("L300 S5R/R01 reader minus easiest", 5.0000e-05, "control",
     "results/phase_2_4_stage_5r/R01/metrics.json"),
    ("L300 S5R/R01 reader minus exact", 5.0000e-05, "control",
     "results/phase_2_4_stage_5r/R01/metrics.json"),
    ("L301 S5R/R02 reliance, six records minus two, two readers", 5.0000e-05, "primary",
     "results/phase_2_4_stage_5r/R02/metrics.json"),
    ("L301 S5R/R02 reliance, plain minus fallback rendering", 5.0000e-05, "control",
     "results/phase_2_4_stage_5r/R02/metrics.json"),
    ("L303 S5R/R04 reader minus random buyer, paying step", 9.3760e-01, "primary",
     "results/phase_2_4_stage_5r/R04/metrics.json"),
    ("L306 S5R/F02 reader minus best raw baseline, two readers", 4.8150e-01, "primary",
     "results/phase_2_4_stage_5r/F02/metrics.json"),
    ("L307 S5R/F03 pursuit, plain minus counter-bias, incongruent, two readers", 6.0000e-04, "primary",
     "results/phase_2_4_stage_5r/F03/metrics.json"),
    ("L311 S5R post R01-ease, record taken when plain minus when hard, pooled", 5.0000e-05, "primary",
     "results/phase_2_4_stage_5r/post/R01_EASE.json"),
    ("L311 S5R post R01-ease, note taken when plain minus when hard, pooled", 5.0000e-05, "primary",
     "results/phase_2_4_stage_5r/post/R01_EASE.json"),
    ("L314 S5R post R02-ease, reliance six minus two records, plain, pooled", 5.0000e-05, "primary",
     "results/phase_2_4_stage_5r/post/R02_EASE.json"),
    ("L314 S5R post R02-ease, reliance plain minus capitals, six records, pooled", 2.5000e-04, "control",
     "results/phase_2_4_stage_5r/post/R02_EASE.json"),
    ("L320 S6 M08/x1 CR minus AD at x40, sign-flip perm", 5.0000e-05, "primary",
     "results/phase_2_4_stage_6/M08/x1/verdict.json"),
    ("L321 S6 M08/x2 CR minus AD, surface axis, sign-flip perm", 5.0000e-05, "primary",
     "results/phase_2_4_stage_6/M08/x2/verdict.json"),
    ("L321 S6 M04/x8 TT minus L, approximation axis, sign-flip perm", 5.0000e-05, "primary",
     "results/phase_2_4_stage_6/M04/x8/verdict.json"),
    ("L322 S6 M02/x1 L minus D at x40, sign-flip perm", 5.0000e-05, "primary",
     "results/phase_2_4_stage_6/M02/x1/verdict.json"),
    ("L326 S6 M06/x8 EX minus GS at x40, sign-flip perm", 2.0000e-03, "primary",
     "results/phase_2_4_stage_6/M06/x8/verdict.json"),
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
