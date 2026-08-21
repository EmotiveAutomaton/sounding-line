"""Pre-registration for G165-D — the single predeclared null discriminator of the
G165 root (prereg/g165.py, ROOT-NULL at L151), frozen before any arm runs.

THE QUESTION. G165 found explicit route generation redundant where direct reading is
STRONG (0.86). The card's null route names exactly one follow-up: the same ablation
where direct reading is WEAK and a cheap representation is known to beat it — the G129b
revision-delta events, where the 19-feature change block wins the instrument contest
(0.5471 against the reader's 0.4805, McNemar p = 0.0157, L141). If explicit generation
contributes representation rather than rhetoric, this is the substrate with seven
points of room for it to show. If it is null here too, Wing G narrows to "direct
reading is this reader's best form" and the wing stops, per the brief's own
cheap-baseline routing row. No prompt search follows a null.

SUBSTRATE. The frozen G129b manifest (seed 37): the full 616-event set, identical
events and candidate labels as the recorded recovery arm, paired at the event level
to the recorded picks. Temperature-zero determinism makes the recorded direct arm the
exact baseline without a re-run.

ARMS (GPU, checkpointed):
  SR-delta  self-route on the delta interface: the reader first writes two numbered
     decisions describing how it would revise the BEFORE sentence to the AFTER under
     the assignment (candidate-blind), then classifies with its own route in context.
  CD-delta  candidate-and-discriminate: per candidate purpose LABEL (a small fixed
     vocabulary, cached across events) the reader predicts the single most specific
     visible change that purpose would produce; then classifies with the predictions
     beside the labels.
  SR-unchanged  self-route on the 100 recorded no-revision events with the explicit
     no-revision option: the fabrication gate for the new generation stage (the direct
     battery's recorded bound is 0.000 twice; generation could plausibly induce
     invented purposes, so the new stage owes its own measurement).

DESIGN CHECK (2026-08-21)
lessons read: LESSONS §3 (ruler-first; criterion-can-fail; power before verdicts;
gate-met language; the pair-task change-stated rule — every arm here reads the
explicit delta, same as the recorded battery), §4 (adjudication is mechanical
pick==truth), §5 (produces guards, gpu lock once, append-at-end, retries).
gates, each with null and alternative and the failure direction:
  ANCHOR (known-answer wiring): the recorded recovery arm must exist at 0.4805 on 616
    with its partials readable. Null: passes by construction. Alternative: drift;
    direction ABORT.
  FABRICATION (SR-unchanged): null (the recorded direct bound): rate ~0.00 against
    the explicit no-revision option. Alternative (guarded direction UP): route
    generation invents purposes on unrevised text; band CLEAN <= 0.05, above it the
    SR arm's positives are read with the fabrication rate as a warning label and
    above 0.15 the SR arm is UNINTERPRETED.
  PIPELINE PURITY: same mechanical rule as the root (prompts byte-pure in the event's
    old/new text, assignment, and candidate labels; hidden fields permuted leave
    hashes fixed). Runs first, CPU; any defect is INSTRUMENT-FAIL.
primary: paired accuracy delta vs the recorded direct picks on identical events, exact
  McNemar, TWO comparisons (SR-direct, CD-direct), declared now; p-values to
  runners/audit_multiplicity.py at landing. The gap-closure quantity is reported
  beside the bands, never banded itself: each arm's accuracy against the change
  block's 0.5471.
bands, exhaustive (no silent interval):
  CONTRIBUTES  delta >= +0.04 AND McNemar p < 0.05 (0.04 is ~60% of the block gap;
               at n = 616 with the observed ~30% discordance the 0.80-power
               detectable delta is ~0.05, so the band is powered, barely, and says so)
  HURTS        delta <= -0.04 AND McNemar p < 0.05
  NO-GAIN      everything else

RESPONSES, recorded now. CONTRIBUTES on either arm: the wing reopens with the three
default branches (transfer, adversarial rationale, mechanism against the block: does
the generation arm's margin survive ADDING the change block's features to the direct
prompt?). NO-GAIN both: Wing G closes at "direct reading is this reader's best form;
explicit generation adds nothing on strong or weak substrates" — stated without
softening, the wing's registry row takes the ruling, and the null discriminator rule
is spent (no further follow-up exists on this card or its parent). HURTS: same closure
with the sharper sentence. FABRICATION fires: the SR positives are uninterpreted and
the closure is decided by CD alone.

Seed 16550 (prompt-shuffle seeds only; events and candidates are the frozen G129b
manifest). Reader qwen3.5:9b at temperature 0; every statistic on disk; sha256 of this
card in the landing entry.
"""

from __future__ import annotations

CARD = {
    "id": "G165-D",
    "parent": "G165 (prereg/g165.py), the predeclared null discriminator",
    "phase": "2.3 Wing G, terminal follow-up",
    "theory_group": "Reader Heuristics",
    "written_before_run": True,
    "seed": 16550,
    "substrate": "results/g129b/manifest.json (frozen, seed 37), 616 events + 100 unchanged",
    "primary": "paired McNemar delta vs recorded G129b recovery picks, two comparisons",
    "bands": {"CONTRIBUTES": ">= +0.04 and p < 0.05", "HURTS": "<= -0.04 and p < 0.05",
              "NO-GAIN": "everything else"},
    "gap_reference": "change block 0.5471 vs direct 0.4805 (L141), reported not banded",
    "gates": ["pipeline_purity_first", "anchor 0.4805/616",
              "sr_unchanged fabrication CLEAN <= 0.05, uninterpreted above 0.15"],
    "interfaces": {"all arms": "I2 paired delta, matching the recorded battery"},
}
