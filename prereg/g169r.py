"""Pre-registration for G169-R — the span-level handling battery on the standing
long-form corpus (Phase 2.3 Wing D repair, part 2), frozen on the v2 CORPUS-STANDS.

THE QUESTION. L150 found an honest reader BLIND on concealed-vs-unnoticed at essay
grain, and named its own redesigns: longer artifacts, realized (audited) hedging, and
SPAN-LEVEL asking — where is the handling, not which class. The corpus now exists with
all three properties (v2 audit: hedging realized at 2.3x the unnoticed rate). The
battery asks whether the L150 wall was resolution or reality.

DISCLOSED AT FREEZE: the corpus's concealment hedging is MECHANICALLY measurable —
that is how the audit verified it — so a hedge-count baseline may separate the pair
without any semantics. That is not a defect; it is the design. Two separable claims:
(1) the pair is separable AT ALL at long form (any instrument), which alone breaks
L150's resolution wall; (2) the READER adds anything over the mechanical baseline.
Both are scored, neither is conflated with the other.

SUBSTRATE. corpora/g169_longform (v2): 20 corrected / 19 concealed / 20 unnoticed /
20 clean, 857 to 1400 words, both families, plants and corrections string-verified.

ARMS:
  V  validation-first (L139 order, gates ALL interpretation): two mechanically
     decidable questions per artifact ("does the exact figure X appear?", "is it
     explicitly corrected to Y later?"), negative-class-heavy across the 80.
     GATE: accuracy >= 0.75, false-yes <= 0.25, else everything below is
     UNINTERPRETED.
  CL whole-artifact classification, the L150 form on the new substrate: four family
     descriptions plus cannot-tell. The bridging arm: does length alone fix L150?
  SP span-locate, the redesign itself, on the 39 planted concealed/unnoticed
     artifacts: the reader is told the essay states the figure, and asked whether the
     essay's treatment of dependent claims CHANGES after that point — quoting the
     single clearest sentence if yes. Scored mechanically: a HIT is a yes whose
     quoted sentence lies after the plant and carries at least one hedge marker.
  B  context floor (descriptions without the essay, 20 events).
  M  the mechanical baseline (CPU, disclosed): post-plant hedge count with a
     leave-one-topic-out threshold, classifying concealed vs unnoticed.

DESIGN CHECK (2026-08-21)
lessons read: LESSONS §3 (ruler-first — V first; criterion-can-fail — every band
below is reachable; the format-is-the-instrument lesson — SP quotes are verified
mechanically, never trusted as claims; power before verdicts — n = 39 committed max
detects ~0.22 off 0.5 at 0.80 power, PARTIAL is underpowered territory and says so),
§4 (the adjudication of SP is string-mechanical on the quoted span), §5 complete.
gates, each with null and alternative and the failure direction:
  V as above (direction: false-yes UP, acquiescence).
  CLEAN FABRICATION in CL: clean must classify clean or cannot-tell; the L146/L150
    risk is UP and the recorded 0.30 is the warning label; banded CLEAN <= 0.15.
  SP QUOTE INTEGRITY (mechanical): a quoted sentence must appear verbatim (after
    whitespace normalization) in the essay, else the row is a fabricated span and
    scores as a miss AND increments a fabricated-span rate reported in the verdict
    (direction UP = the reader invents text; above 0.15 SP is UNINTERPRETED).
primary: concealed-vs-unnoticed separation on committed pairs in CL (the L150 primary
  on the new substrate) AND the SP separation (concealed yes-with-hit rate minus
  unnoticed yes rate).
bands for each, exhaustive (the L150 vocabulary):
  SEPARATES >= 0.70 committed-pair accuracy (CL) / hit-rate gap >= 0.40 (SP)
  PARTIAL   [0.60, 0.70) (CL) / gap [0.20, 0.40) (SP) — underpowered, says so
  BLIND     below, gates passed
the reader-vs-mechanical contest, reported never banded: M's leave-one-topic-out
  accuracy beside whichever reader arm separates.

RESPONSES, recorded now. Reader SEPARATES and beats M: the channel reopens at long
form; the D1 handling-transfer branch (constructed to natural revisions) is licensed.
SEPARATES but M does as well or better: the pair is separable and the reader adds no
semantics — the claim is trace-existence at long form, instrument mechanical, stated
without softening. BLIND on both reader arms with M separating: the signal exists and
this reader cannot read it even span-level — the reader family is the wall, not the
resolution. BLIND everywhere including M: the v2 hedging audit and this result
contradict (the audit measured separation M cannot find) — instrument investigation
before anything else. V fails: uninterpreted, no rerun without redesign.

Seed 16950; reader qwen3.5:9b at temperature 0; per-family confusion; every statistic
on disk; sha256 of this card in the landing entry.
"""

from __future__ import annotations

CARD = {
    "id": "G169-R",
    "phase": "2.3 Wing D repair, part 2 (the L150-owed redesign)",
    "theory_group": "Reader Heuristics / Decision Traces",
    "written_before_run": True,
    "seed": 16950,
    "substrate": "corpora/g169_longform (v2 CORPUS-STANDS)",
    "primary": "concealed-vs-unnoticed: CL committed pairs AND SP hit-rate gap",
    "bands": {"CL": "SEPARATES >= 0.70 / PARTIAL [0.60,0.70) / BLIND",
              "SP": "SEPARATES gap >= 0.40 / PARTIAL [0.20,0.40) / BLIND"},
    "validation_first": "V gates everything (acc >= 0.75, false-yes <= 0.25)",
    "disclosed": "the mechanical hedge baseline may separate; reader-vs-M is scored "
                 "separately from separability-at-all",
    "interfaces": {"all reader arms": "I1 final artifact"},
}
