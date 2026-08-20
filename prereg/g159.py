"""Pre-registration for G159 — realized-choice recovery on the rebuilt factorial corpus.

Phase 2.1.5's decisive study and Phase 2.2's closure boundary (2.2A). Written to Phase
2.1's frozen question, per the 2.2 brief's explicit instruction ("do not rewrite the
preregistration to fit this context"): the question is REALIZATION EVIDENCE, never
attribution, never a human-versus-AI verdict. The freeze is the git commit landing this
file; the sha256 is recorded in the FINDINGS entry reporting the result.

THE QUESTION. Can the artifact-only bounded reader distinguish verified executed
instructions from uninstructed twins and unexecuted alternatives when lexical echo and
consequence are controlled? (Brief §8/2.2A wording, which is the 2.1.5 TODO row's.)

THE CORPUS (L144, self-gate passed). 160 rewrites of the twenty recorded zero-instruction
bases: per family x topic x target {surface, problem} x amount {1, 4}, TWO arms — R+ was
instructed to apply the drawn set; R- received the identical rewrite request with NO
instructions shown, the set recorded as counterfactual. R+ executes exact-grade formal
instructions at 0.625; R- satisfies the same checks spontaneously at 0.281.

DESIGN CHECK (2026-08-19, at design time, before any arm runs). Lessons read: LESSONS §3
to §5 complete including all six 2026-08-19 entries; CONTROLS 6 and 7; the L138-L143
constraint set this design exists to satisfy.
  gates, each with null expectation, alternative expectation, and guarded direction:
    blind (candidates only, P+ sets): null = alternative = analytic 1/k = 0.25 (truth
      position uniform by seeded shuffle; the blind arm cannot see an effect). Guarded
      failure: construction leak, direction UP. VOID if one-sided p(acc > 0.25) < 0.05.
    P- twin gate (the leak gate AND the realization null, forced choice, no none option):
      the R- twin never saw the instructions, so nothing was executed and nothing echoes.
      Null (construction clean) = 0.25; alternative (execution effect real) = STILL 0.25;
      any above-floor read is a candidate-construction leak, direction UP. VOID if
      one-sided p(acc > 0.25) < 0.05. This gate has the same expectation under null and
      alternative BY DESIGN, which is what makes it a pure leak instrument (CONTROLS 7).
    echo bar on P+ (CPU, matching validation): decoys are echo-matched at construction
      (the three unassigned instructions with content-word-overlap scores closest to the
      truth's on this text). Null (matching worked) = echo picks at ~0.25; failure
      direction UP = the matching failed and the L138/L140 echo channel is open — NOT a
      void, but the P+ margin is then read against max(echo, 0.25) instead of 0.25, and
      the failure is disclosed in the verdict file.
    fabrication arm (P- sets WITH an explicit "none of these was given" option, separate
      from the leak gate): honest behavior = the none option (the R- twins truly received
      none). Over-attribution rate reported beside the L143 reference (~0.10); direction
      UP = the reader asserts instructions on uninstructed text. Reported, not banded
      (exploratory calibration of the same reader; the banded fabrication instrument is
      L140/L143's).
    surface oracle: the mechanical check identifies the surface truth at 1.0 by
      construction; anything else aborts interpretation (wiring).
  primary quantity: the EXECUTION EFFECT = P+ accuracy minus P- accuracy on identically
  constructed candidate sets (same decoy rule, twin texts). Bands, exhaustive, no gaps:
      SUPPORTED      >= 0.15
      PARTIAL        [0.08, 0.15)   (interpretable but under the powered margin)
      NOT-DETECTED   < 0.08
  power, computed before the run: P+ n = 100 assigned problem instructions (2 families x
  10 topics x (1+4)), P- n = 100 counterfactual twins. Two-proportion test at alpha 0.05,
  power 0.80, baseline 0.25: the detectable-at-power execution effect is ~0.18. Effects
  in [0.08, 0.18) land PARTIAL underpowered and say so; nothing is silently accepted.
  n is fixed by the corpus and this is disclosed now, not after.
  secondary arms, reported never banded: S+ surface events (exact-grade realized truths
  with mechanically-unsatisfied decoys, n ~20 — L140 predicts reader ~chance, the
  mechanical channel is the oracle's); the DELTA arm (base + rewrite delta + candidates
  on P+ sets, interface I2) — the interface gate requires it reported separately from
  artifact-only, never pooled; per-cell tables by family, amount; per-decoy pick rates.

RESPONSES, recorded now:
  if_SUPPORTED: realized choices leave artifact-only evidence under echo and consequence
    control -- licenses continued trajectory recovery (2.2C onward), NOT provenance
    attribution, NOT stacking (2.2G holds its own gates).
  if_PARTIAL: the effect exists below power; the follow-up is a larger corpus under the
    same frozen construction, not a reinterpretation.
  if_NOT_DETECTED_and_delta_positive: the final-artifact interface narrows; realization
    evidence is a process-trace, paired-delta interface property (brief §11.1's stated
    routing); the artifact-only claim weakens and says so.
  if_P_minus_voids: the candidate construction leaks; every number quarantines pending
    the leak hunt.
  if_echo_bar_fails_upward: echo matching is insufficient at this pool size; the P+
    margin reads against the measured echo bar and the rebuild's next corpus widens the
    instruction pool before any stronger claim.
  amount_comparison: measures trace dilution or overlap (L143's curve), never "total
    decision mass" (brief §11.1).

REPORTING. Every statistic on disk; per-instruction confusion; new p-values registered in
runners/audit_multiplicity.py the same pass; the curator roll-up at theory-group level.
"""

from __future__ import annotations

CARD = {
    "id": "G159",
    "phase": "2.1.5 / 2.2A",
    "theory_group": "Decision Traces",
    "written_before_run": True,
    "seed": 15950,
    "k": 4,
    "corpus": "corpora/g159_rebuild (L144; realization self-gate passed 0.625 vs 0.281)",
    "primary": "execution effect = P+ minus P- on echo-matched candidate sets",
    "bands": {"SUPPORTED": ">= 0.15", "PARTIAL": "[0.08, 0.15)", "NOT-DETECTED": "< 0.08"},
    "gates": ["blind one-sided vs 0.25", "P- twin one-sided vs 0.25 (leak gate)",
              "echo bar disclosure rule", "fabrication reported", "surface oracle wiring"],
    "interfaces": {"primary": "I1 final artifact only",
                   "secondary": "I2 paired delta, never pooled with I1"},
}
