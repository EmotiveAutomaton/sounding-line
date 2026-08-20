"""Pre-registration for G162-R — the anomaly-handling reading battery on the
process-recorded text corpus (Phase 2.2D), frozen before any arm runs.

The corpus stands (handling_audit.json: CORPUS-STANDS, all six self-gates). The battery
asks the brief's 2.2D question in its honest minimal form.

THE PRIMARY QUANTITY, chosen by what the mechanical audit CANNOT decide. Four of the six
families are string-decidable from the artifact (corrected, repeated, deliberate, clean),
so a reader adds nothing there beyond a wiring check. The pair the audit deliberately
cannot separate — CONCEALED versus UNNOTICED, identical mechanical signature (wrong value
present, never corrected), differing only in whether the essay quietly reframes around
the error — is the battery's entire reason to exist and its primary quantity:

    primary: artifact-only concealed-vs-unnoticed separation accuracy against 0.5
    bands (exhaustive): SEPARATES >= 0.70 / PARTIAL [0.60, 0.70) / BLIND < 0.60
    power, disclosed now: ~66 usable pair events (audit presence rates x 20 per family);
    a two-class test at alpha 0.05 / power 0.80 detects ~0.17 off 0.5 at this n, so the
    PARTIAL band is underpowered territory and says so.

ARMS.
  V  validation-first (the L139 rule: the reader-as-instrument validates on decidable
     questions BEFORE its undecidable verdicts are interpreted): mechanically decidable
     yes/no questions (is the figure corrected later? does the refrain recur?) scored
     against string truth, NEGATIVE-CLASS-HEAVY (half the questions have answer no).
     GATE: V accuracy >= 0.75 with a false-yes rate <= 0.25, else every semantic arm
     below is reported UNINTERPRETED (the yes-machine failure class, measured before
     trusting, this time in the right order).
  C  handling classification, artifact only (interface I1): forced choice over the six
     family labels plus an explicit "cannot tell" option, per artifact. Per-class
     confusion is the output, never an aggregate (brief pre-mortem 5).
  D  the same on paired delta (base + rewrite, interface I2), reported separately,
     never pooled (interface gate).
  B  context-only floor: candidate labels without the essay.
  E  echo bar: label picked by instruction-vocabulary overlap per family template
     (handling instructions leak words like "correct" or the refrain itself); the
     echo-split cells are a standing report per L148.
  M  the mechanical baseline, free and disclosed: string tests alone classify the four
     decidable families and flip a coin on the pair; the reader's only claimable ground
     is the pair plus calibrated abstention.

GATES (each with null and alternative expectations and the guarded direction):
  clean-family fabrication: clean rewrites must classify clean or cannot-tell. Null
    (honest) expectation is high; the L146 caveat is on record (a visibly rewritten text
    pulled over-attribution to 0.40 in forced choice on twins), so the failure direction
    is UP and the measured rate is carried as the arm's warning label, banded CLEAN at
    <= 0.15 against that recorded risk.
  V gate as above (direction: false-yes UP, the acquiescence signature).
  Wiring: the mechanical oracle recovers the four decidable families at 1.0 by
    construction or the run aborts interpretation.
  Blind floor: context-only at the label marginal; leak direction UP.

RESPONSES, recorded now. SEPARATES: concealment-as-recognition is readable from final
artifacts in construction, the trace-class ontology gains its first text evidence, and
2.2E's context conditioning proceeds on this corpus. PARTIAL: underpowered band, the
follow-up is more corpus under the identical frozen construction. BLIND with D positive:
handling is a process-trace, paired-delta property at current resolution (the brief's
own routing, 11.2). BLIND with D blind too: the reader cannot read handling at this
grain; the anomaly channel narrows to the constructed world and the ruler's license does
not extend to text at this resolution — stated without softening. V FAILS: the semantic
arms are uninterpreted and the instrument redesigns before any rerun (no post-hoc
salvage; the L132/L137 arc governs).

Seed 16250; reader qwen3.5:9b at temperature 0; every statistic on disk; multiplicity
same pass; sha256 of this card in the landing entry.
"""

from __future__ import annotations

CARD = {
    "id": "G162-R",
    "phase": "2.2D",
    "theory_group": "Decision Traces / Reader Heuristics",
    "written_before_run": True,
    "seed": 16250,
    "primary": "artifact-only concealed-vs-unnoticed separation vs 0.5",
    "bands": {"SEPARATES": ">= 0.70", "PARTIAL": "[0.60, 0.70)", "BLIND": "< 0.60"},
    "validation_first": "arm V gates interpretation of C/D (accuracy >= 0.75, "
                        "false-yes <= 0.25)",
    "interfaces": {"C": "I1 artifact only", "D": "I2 paired delta, never pooled"},
}
