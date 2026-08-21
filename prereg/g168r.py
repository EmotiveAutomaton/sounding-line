"""Pre-registration for G168-R — the role-recovery battery on the standing interaction
corpus (Phase 2.3 root P23-C0 proper), frozen on CORPUS-STANDS.

THE QUESTION (design brief Wing C, §10). The corpus records who proposed, whether
selection happened among alternatives, whether a veto reshaped the plan, and who
repaired — as logged events with 0.95 selection integrity. Can a reader recover any of
those ROLES from the final artifact, or is contribution auditable only where records
exist (the W4 boundary, already measured twice today on routes and handling)?

SUBSTRATE. corpora/g168_roles (CORPUS-STANDS): 40 cases, conditions balanced two-way
by construction on each question, so every analytic floor is 0.5.

THREE QUESTIONS per case, each a recorded fact:
  Q1 selection: did the writer choose among proposed alternatives, or accept the
     only proposal made?
  Q2 veto: did the second participant reject the plan and force a revision before
     writing?
  Q3 repair: after writing, was a paragraph rewritten by the participant who
     PROPOSED, or by the one who WROTE?

ARMS:
  P  process-aware ceiling (I3, GPU): essay plus the recorded event summary; gates
     interpretation per question at >= 0.85 (with the log the facts are decidable;
     below that the reader cannot represent the question).
  C  artifact-only (I1, GPU): essay plus the protocol description (which names the
     possible roles, never the answers).
  B  context-only floor (GPU, three deterministic calls): the protocol description
     without the essay; the marginal-behavior check.

DESIGN CHECK (2026-08-21)
lessons read: LESSONS §3 (ruler-first — P is the known-answer gate; criterion-can-
fail; floors are analytic 0.5 by balanced construction; power before verdicts — at
n = 40 per question the 0.80-power detectable accuracy is ~0.72, so PARTIAL is
underpowered territory and says so), §5 complete.
gates: P >= 0.85 per question (null: decidable with the log; direction DOWN voids
  that question's arms); pipeline purity (prompts byte-pure in essay + fixed
  question text; condition metadata permuted leaves hashes fixed; CPU, first);
  balanced-marginal check (each question's truth split is 20/20 by construction,
  asserted at build).
primary: artifact-only accuracy per question against 0.5, reported PER QUESTION,
  never aggregated (the brief's no-summing rule applied to the battery itself).
bands per question, exhaustive:
  READS   >= 0.70
  PARTIAL (0.60, 0.70) with one-sided p < 0.05 — underpowered, says so
  BLIND   everything else with the P gate passed

RESPONSES, recorded now (brief §10 routing). READS on any question: that role
survives into the artifact; branches C1 (selection adversary) and C4 (surface-match
repair) per the brief. BLIND across all three with P passed: contribution is
auditable and not inferable from product — the W4 boundary's third measurement, and
the audit-interface product (C5) is the wing's honest output, stated without
softening. P fails: the battery is uninterpreted and the question format redesigns.

Seed 16850; reader qwen3.5:9b at temperature 0; every statistic on disk; sha256 of
this card in the landing entry.
"""

from __future__ import annotations

CARD = {
    "id": "G168-R",
    "alias": "P23-C0",
    "phase": "2.3 Wing C root",
    "theory_group": "Decision Traces",
    "written_before_run": True,
    "seed": 16850,
    "substrate": "corpora/g168_roles (CORPUS-STANDS)",
    "primary": "artifact-only per-question accuracy vs 0.5, never aggregated",
    "bands": {"READS": ">= 0.70", "PARTIAL": "(0.60,0.70) sig, underpowered",
              "BLIND": "else with P passed"},
    "gates": ["pipeline_purity_first", "P >= 0.85 per question",
              "balanced marginals asserted"],
    "interfaces": {"P": "I3", "C": "I1", "B": "context only"},
}
