"""Pre-registration for G129b — the fresh confirmatory battery for event-level choice
recovery on ArgRewrite, re-earning the grade the first battery's own gate denied it.

Phase 2.1.4 (the repair phase declared 2026-08-19; external audit and ratification L137).
Theory group: Decision Traces. Written before any arm runs; the freeze is the git commit
that lands this file, and the card's sha256 is recorded in the FINDINGS entry that reports
the result.

WHY A SECOND CONFIRMATORY EXISTS. The first battery (prereg/g129.py, L132) landed H-A
REPLICATES, H-B SURVIVES, A7 CLEAN, H-C LOSES -- and its shuffle gate fired VOID as
written (0.110 against a stated 0.25 expectation). The corrected expectation (~0.125, the
label-marginal signature of a delta-tracking reader) is sound and was derivable a priori,
but it was derived AFTER the result, and a post-hoc-repaired gate cannot restore a run's
confirmatory grade (LESSONS §3, the gate-met lesson; curator-ratified demotion, L137).
This card is the same battery under gates specified correctly from birth, fresh seed, so
that a clean pass is confirmatory with nothing to explain.

DESIGN CHECK (2026-08-19, at design time, before any run).
  lessons read: LESSONS §3 (including the two banked at L137: gate-met terms;
  assigned-is-not-realized -- not implicated here, ArgRewrite purposes are recorded by
  the revisers themselves), §4, §5; CONTROLS entries 6 and 7 in full.
  gates, each with null expectation, alternative expectation, and guarded direction:
    blind / blind_matched: null (construction clean, reader has nothing) = analytic 1/k
      = 0.25 on the truth-balanced sets; alternative (recovery real) = the same 0.25,
      the blind arm cannot benefit from an effect it cannot see. Guarded failure:
      construction leak, direction UP. Gate: VOID if one-sided p(acc > 0.25) < 0.05.
      Below-chance blind is sampling noise, not a leak signature; reported, never gating.
    shuffle: truth replaced by another event's label, delta still shown. Null (reader
      ignores the delta) = 0.25, candidate-uniform. Alternative (reader tracks the real
      delta, scoring clean) = the label-marginal match rate between a permuted label list
      and delta-consistent picks, approximately 1/n_labels = 0.125 with 8 eligible fine
      labels -- BELOW candidate chance, derived here a priori, the L132 signature.
      Guarded failure: scoring leak, direction UP toward the recovery number. Gate: VOID
      if one-sided p(acc > 0.25) < 0.05. The observed value is also reported against the
      0.125 alternative expectation descriptively.
    A7 fabrication: null (reader honest on no-ops) = picks the explicit no-revision
      option; alternative failure = asserted purposes on unchanged text, direction UP in
      fabrication rate. Band: CLEAN <= 0.10, OVER-READS above, rate carried as the
      warning label. Symmetric changed-side miss rate reported, not banded.
  bands: exhaustive, no silent intervals (the L73 lesson): H-A REPLICATES >= 0.15 /
  PARTIAL [0.08, 0.15) / FAILS < 0.08; H-B SURVIVES >= 0.08 / WEAKENED [0.04, 0.08) /
  COLLAPSED < 0.04; H-C BEATS / TIES / LOSES, all three named.
  power, decided before the run (the L132 shortfall clause was disclosed-not-applied;
  here the handling is pre-committed): matched target n >= 283. If the balanced matched
  draw lands short, ONE specified relaxation runs -- the covariate coarsening drops from
  terciles to medians (2 bins per covariate instead of 3), widening common support at a
  disclosed matching-quality cost, recorded in the manifest as caliper_relaxed. If still
  short, the matched arm runs anyway and its verdict is REPORTED AT THE PILOT EVIDENCE
  TIER, stated in the verdict file itself, with no confirmatory language attached to H-B.
  H-A, A7, and H-C are unaffected by the shortfall either way.
"""

from __future__ import annotations

CARD = {
    "id": "G129b",
    "title": "Recorded revision purposes are recoverable from the delta by a bounded "
             "reader, beyond matched contextual alternatives -- the fresh confirmatory "
             "run under gates carrying both expectations and a direction",
    "phase": "2.1.4",
    "theory_group": "Decision Traces",
    "written_before_run": True,
    "depends_on": ["prereg/g129.py battery (L132)", "L137 demotion ruling",
                   "L126 floor decomposition", "CONTROLS entries 6 and 7"],

    "construction": {
        "dataset": "results/arg_baselines/events.json, fine labels with >= 30 events, "
                   "truth-balanced, uniform decoys, k = 4 -- identical to prereg/g129.py",
        "seed": 37,
        "note": "fresh seed; everything else held so a difference from L132 is seed "
                "variance, not design drift",
        "matched_draw": "CEM on the L66/L73 strata, truth-balanced within common support "
                        "(the L126 amendment); the pre-committed caliper relaxation and "
                        "pilot-tier fallback are in the DESIGN CHECK above",
    },

    "arms": "identical to prereg/g129.py Amendment 1: recovery, blind, shuffle, brief, "
            "source, unchanged-with-no-revision-option (+ symmetric control), "
            "recovery_matched, blind_matched, and the 19-dim change block under "
            "author-grouped CV as the declared baseline",

    "hypotheses": {
        "H-A": "full-set recovery margin over the analytic 0.25 floor lands in the "
               "REPLICATES band, reproducing L132's 0.235 within band",
        "H-B": "the balanced matched margin holds at or above 8 points",
        "H-C": "reader vs change block on identical events (exact McNemar), all three "
               "outcomes named; L132 read LOSES and a repeat LOSES is expected, the arm "
               "exists so the confirmatory record contains the contest",
        "A7":  "fabrication stays <= 0.10 (L132 read 0.000)",
    },

    "responses": {
        "if_all_gates_clean_and_H-A_replicates":
            "confirmatory grade is EARNED; the demotion language in STATE/theory lifts to "
            "confirmed-on-this-corpus; the public claim may say confirmatory with the "
            "one-corpus one-reader scope attached",
        "if_shuffle_voids_again_upward":
            "a real scoring leak exists and L132's explanation was wrong; every recovery "
            "number this substrate produced is quarantined pending the leak hunt",
        "if_H-A_fails":
            "L132 was seed-lucky; the claim drops to the pilot tier permanently on this "
            "corpus and 2.1.5's constructed corpus becomes the only path to the gate",
        "if_H-B_collapses_at_power":
            "the delta-specific matched margin was fragile; the roll-up KILLS the "
            "matched half of the real-text evidence and says so without softening",
    },

    "reporting": "per-arm accuracies, confusions with declared label lists, per-decoy "
                 "pick rates, every verdict statistic on disk, new p-values registered "
                 "in runners/audit_multiplicity.py the same pass (the standing rules)",
}
