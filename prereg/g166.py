"""Pre-registration for G166-R — the equifinality reading battery on the route-varied
process-recorded corpus (Phase 2.3 root P23-B0-near), frozen on CORPUS-STANDS (L152).

THE QUESTION (design brief Wing B, §9). Five recorded production routes reached
surface-matched essays on identical briefs. Can a reader recover WHICH route made an
essay from the final artifact alone — and is whatever it recovers process evidence
rather than a surface tell a cheap classifier reads equally well?

SUBSTRATE. corpora/g166_routes: 100 artifacts (10 topics x 5 routes x 2 families),
route logs schema-validated, degeneracy gate green, route length means within seven
percent. Route ground truth is what HAPPENED by construction (the logs are the
record), so assigned-is-realized holds by construction here.

ARMS:
  P  process-aware ceiling (I3, GPU, runs FIRST among reader arms — the
     validation-first analog): the reader sees the essay AND its recorded
     intermediates (outline, thesis candidates with the seeded selection, critique,
     or base-draft note) and classifies the route. GATE: P accuracy >= 0.75, else the
     route question is not answerable by this reader even with the record shown and
     every arm below is UNINTERPRETED (instrument, not signal).
  C  artifact-only classification (I1, GPU): forced choice over the five route
     descriptions plus an explicit "cannot tell", per artifact; per-route confusion
     is the output, never an aggregate.
  B  context-only floor (GPU): descriptions without the essay; label-marginal
     behavior, leak direction UP.
  S  surface baseline (CPU, mechanical, disclosed): nearest-centroid on cheap
     features (length, mean sentence length, type-token ratio, paragraph count,
     first-person rate), leave-one-topic-out within family. The corpus was built to
     be surface-matched; if S is high the matching premise failed and C is read
     against S, disclosed.
  X  exact-equivalence discipline (CPU, mechanical, runs before any GPU arm): the
     C-arm prompt must be a byte-pure function of (essay text, candidate list) —
     route metadata, lineage, and event logs permuted leave prompt hashes fixed. Any
     defect is INSTRUMENT-FAIL and no arm runs.

DESIGN CHECK (2026-08-21)
lessons read: LESSONS §3 (ruler-first — P is the reader-side known-answer gate and X
the mechanical one; criterion-can-fail — C can land at chance and P can fail;
blind floors follow the truth marginal — routes are balanced by construction so the
analytic floor is 0.2 and B measures the realized marginal; power before verdicts;
per-class confusion mandatory), §4 (adjudication mechanical), §5 (produces guards,
gpu lock once, append-at-end, retries).
gates, each with null and alternative and the failure direction:
  X purity: null identical hashes; alternative ANY drift = metadata leak,
    INSTRUMENT-FAIL (direction: abort).
  P ceiling: null (records shown, reader competent) >= 0.75; alternative below it =
    the reader cannot represent the route taxonomy at all; direction DOWN voids
    interpretation of C and B.
  B floor: null = label marginal ~0.2; alternative UP = candidate-order or
    description leakage; C is read against max(B, 0.2), disclosed.
  S contest: null (matching held) S near 0.2; alternative UP = the routes are
    surface-separable and C's claim ground shrinks to its margin over S, disclosed
    in the verdict whatever happens.
primary: artifact-only route recovery (C) against the analytic 0.2 floor, one-sided
  binomial at n = 100, with the S contest reported beside it.
bands, exhaustive (no silent interval):
  SEPARATES  C >= 0.40 (twice chance) AND C > S by >= 0.10
  PARTIAL    C in [0.28, 0.40) with one-sided p < 0.05 against 0.2 — underpowered
             territory (0.80-power detectable is ~0.32 at this n) and says so; also
             any C >= 0.40 that fails the S margin lands here with the surface
             caveat named
  BLIND      everything else with gates passed

RESPONSES, recorded now (brief §9 routing). SEPARATES: route classes carry from final
artifacts; branches B1 trace erasure, B2 family transfer, B3 withheld-process
confirmation (one on untouched data). PARTIAL: the one follow-up is more corpus under
the identical frozen construction (topics 10-19), nothing else. BLIND with P passed:
final artifacts do not carry route identity at this construction — the W4 boundary
(process records auditable, artifacts silent), stated without softening; the wing's
artifact-only claim narrows and the interface product is the audit form. P FAILS: the
battery is uninterpreted and the route taxonomy redesigns before any rerun. X FAILS:
instrument failure, nothing interprets.

Seed 16650; reader qwen3.5:9b at temperature 0; per-route confusion in the verdict;
every statistic on disk; sha256 of this card in the landing entry.
"""

from __future__ import annotations

CARD = {
    "id": "G166-R",
    "alias": "P23-B0-near",
    "phase": "2.3 Wing B root",
    "theory_group": "Decision Traces / The Triple Inference",
    "written_before_run": True,
    "seed": 16650,
    "substrate": "corpora/g166_routes (CORPUS-STANDS, L152)",
    "primary": "artifact-only route recovery vs 0.2, S contest reported beside",
    "bands": {"SEPARATES": ">= 0.40 and beats surface by >= 0.10",
              "PARTIAL": "[0.28, 0.40) sig, or >= 0.40 without the S margin",
              "BLIND": "everything else with gates passed"},
    "validation_first": "P (process-aware ceiling) >= 0.75 gates C and B",
    "interfaces": {"P": "I3", "C": "I1", "B": "context only", "S": "CPU baseline"},
}
