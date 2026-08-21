"""Pre-registration for G165 (Phase 2.3 root P23-G0) — the reader-ablation ruler:
does explicit route generation add anything to direct reading? Frozen before any arm runs.

THE QUESTION (design brief Wing G, §14). The project's central untested assumption is
that a reader models the generating process. The cheapest honest form: on events where
recorded process facts are recoverable by DIRECT reading (the G159 realized-choice set,
direct accuracy 0.86 recorded, L146/L148), does a reader that first GENERATES process
structure — its own production route, or predicted evidence per candidate — recover the
recorded facts better, the same, or worse? Existing data only; no new corpus.

SUBSTRATE. The frozen G159 manifest (results/g159/manifest.json, seed 15950): 100 P+
events with mechanically VERIFIED executed instructions (assigned-is-not-realized
satisfied at construction) and echo-matched decoys; the 100 P- twin events where nothing
was executed, as the leak construction. The recorded direct arm (0.86) and context-only
arm (0.32, the label-marginal floor) are REUSED as paired baselines: same reader, same
temperature 0, same events, so re-running them would reproduce them by determinism.

ARMS (new GPU work, both on the identical event list, paired to the recorded picks):
  SR self-route: the reader first writes three numbered production decisions it would
     have made to produce this essay (essay only, candidate-blind), then classifies with
     its own route in context.
  CD candidate-and-discriminate: for each candidate instruction the reader predicts the
     single most specific visible feature the rewrite would show (candidate only,
     essay-blind, cached by instruction string), then classifies with the predicted
     evidence lines beside the candidates.
  Leak arms: SR and CD on a seeded 50-event subsample of the P- twins.

DESIGN CHECK (2026-08-21)
lessons read: LESSONS §3 (ruler-first; criterion-can-fail; blind floors follow the truth
marginal; echo-split standing cells per L148; power before verdicts; gate-met language;
assigned-is-not-realized), §4 (the adjudication here is mechanical pick==truth, so no
model adjudicator exists to validate; the reader is the SUBJECT), §5 (produces guards,
gpu lock once per invocation, append-at-end, retry-with-backoff in every ollama call).
gates, each with null and alternative expectations and its failure direction:
  PIPELINE PURITY (mechanical, CPU, runs FIRST; the phase's exact-equivalence gate,
    brief §3.3): every arm's prompt must be a byte-pure function of (essay text,
    candidate list). Recomputed under permuted hidden manifest fields (family, amount,
    artifact_id, truth_idx) the sha256 set must be identical. Null: identical.
    Alternative (failure direction): ANY difference = hidden-history metadata reaches
    the prompt = INSTRUMENT-FAIL; no GPU arm runs (the queue gates on this produce).
  ANCHOR (known-answer wiring): the recorded direct arm must exist with accuracy >=
    0.80 on n >= 90 parsed (recorded: 0.86/100). Null (wiring intact): passes by
    construction. Alternative: manifest or results drift; direction: ABORT, no
    comparison is meaningful against a moved anchor.
  LEAK (negative construction, the twins): null (honest generation): SR and CD on P-
    sit at the 0.25 chance floor — nothing was executed, so generated routes and
    predicted evidence have nothing true to point at. Alternative (the guarded
    direction, UP): recovery of never-executed "truths" above floor means the
    candidate-set construction or the generation stage leaks; one-sided binomial
    p < 0.05 above 0.25 VOIDS any positive delta and routes to the single predeclared
    repair (re-drawn decoys under tighter echo tolerance), else retire.
  ECHO CELLS (CPU, standing per L148, report-only): score each generated route/evidence
    text by content-word overlap with each candidate; report recovery split by whether
    generation-echo points at the truth. Null: echo at the candidate marginal;
    alternative: echo concentrates on truth (direction UP = the generation stage
    embeds candidate vocabulary rather than process structure). No band; interprets
    the primary, never gates it.
  FLOOR: every arm is reported against the recorded context-only floor 0.32; an arm
    below it has destroyed artifact information (direction DOWN, lands in HURTS).
primary: per-arm paired accuracy delta against the recorded direct picks on the same
  100 events, exact McNemar on discordant pairs. TWO comparisons (SR-direct, CD-direct),
  declared now; both p-values enter runners/audit_multiplicity.py when the verdict lands.
bands, exhaustive (no silent interval):
  HELPS    delta >= +0.05 AND McNemar p < 0.05
  HURTS    delta <= -0.05 AND McNemar p < 0.05
  NO-GAIN  everything else, explicitly including the underpowered middle: at n = 100
           paired events the 0.80-power detectable delta is roughly 0.10, so deltas in
           (-0.10, +0.10) without McNemar significance are expected to land here and
           the band says so rather than reading them as evidence of absence.

RESPONSES, recorded now (brief §14 routing, adapted to the reconciled repo):
  HELPS on either arm: three default branches per §7.1 — reader-family transfer,
    adversarial rationale (a polished false route beside a terse true one), and the
    port to the G129b delta events; at least one on untouched data.
  NO-GAIN on both, gates quiet: the single predeclared null discriminator is the same
    ablation on the G129b delta event set, where the cheap change block beats the
    direct reader (0.5471 vs 0.4805, L141): if explicit generation closes the block
    gap there, it contributes representation where direct reading is weak; if null
    there too, Wing G narrows to "direct reading is the reader's best form" and the
    brief's own cheap-baseline routing row stands. No prompt search.
  HURTS: explicit generation is cognitive preemption by rhetoric (brief G0 routing);
    the generation stage is retired phase-wide, stated without softening.
  LEAK fires: INSTRUMENT-FAIL; the one repair above, then retire on a second failure.

Seed 16500 (the P- subsample draw only; everything else is the frozen G159 manifest).
Reader qwen3.5:9b at temperature 0; every statistic on disk; sha256 of this card in the
landing entry.
"""

from __future__ import annotations

CARD = {
    "id": "G165",
    "alias": "P23-G0",
    "phase": "2.3 Wing G root",
    "theory_group": "Reader Heuristics / Decision Traces",
    "written_before_run": True,
    "seed": 16500,
    "substrate": "results/g159/manifest.json (frozen, seed 15950)",
    "primary": "paired delta vs recorded direct picks, exact McNemar, two comparisons",
    "bands": {"HELPS": ">= +0.05 and p < 0.05", "HURTS": "<= -0.05 and p < 0.05",
              "NO-GAIN": "everything else, underpowered middle disclosed"},
    "gates": ["pipeline_purity_first", "anchor >= 0.80", "leak_on_twins_one_sided_up",
              "echo_cells_standing", "context_floor_0.32"],
    "interfaces": {"all arms": "I1 final artifact"},
}
