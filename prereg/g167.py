"""Pre-registration for G167 (Phase 2.3 root P23-A0) — context conditioning: does a
true production-context card move the route reading toward the truth where a false one
must not? Frozen before any arm runs.

THE QUESTION (design brief Wing A, §8). L154 measured the reader abstaining on route
identity almost everywhere (committed-correct 0.07, cannot-tell 0.70 to 0.85). Context
that changes route FEASIBILITY without naming a route should, on the curator's
reweighting model (Q23-2: context shifts the generations of the generative model, it
does not dictate a story), move committed probability mass onto the card-compatible
routes. A FALSE card must not steer equally — if it does, context is suggestion, not
evidence (the brief's W3, context-conditioned projection).

SUBSTRATE. The G166 route corpus (CORPUS-STANDS, L152) and the RECORDED artifact-only
classify arm as the no-card baseline (temperature-zero determinism licenses reuse).
The context axis is draft availability, true by construction from the route logs:
rewrite and revise makers had a complete prior version; direct, outline, and select
makers did not. Cards are mechanical, vocabulary-audited against the route
descriptions so no card shares a content word with any candidate:

    true card     the fact matching the artifact's route subset
    false card    the opposite fact (draft claimed where none existed, and vice versa)
    irrelevant    a production fact with no feasibility consequence (time of day)

The compatible subset under draft-available is {rewrite, revise}; under no-draft it is
{direct, outline, select}. A card narrows five to two or three and can never name the
answer.

ARMS (GPU, each 100 events, same shuffled candidates as the recorded arm):
  T  classify with the true card    F  with the false card    I  with the irrelevant
  (artifact-only baseline: the recorded L154 classify arm, reused)

DESIGN CHECK (2026-08-21)
lessons read: LESSONS §3 (ruler-first — the leak audit is mechanical and runs before
any arm; criterion-can-fail — INERT is reachable because the recorded reader mostly
abstains; blind floors — movement is measured against the recorded no-card mass, not
chance; power before verdicts), §5 (produces guards, gpu lock once, append-at-end,
retries).
gates, each with null and alternative and the failure direction:
  CARD-LEAK AUDIT (mechanical, CPU, FIRST): no card shares a content word with any
    route description. Null: zero overlaps by construction. Alternative: any overlap
    = the card states the answer's vocabulary; INSTRUMENT-FAIL, no arm runs.
  PIPELINE PURITY: prompts byte-pure in (essay, card text, candidates); hidden route
    metadata permuted leaves hashes fixed. Same failure direction.
  IRRELEVANT-CARD STABILITY: null: the irrelevant arm reproduces the recorded no-card
    behavior (committed mass within 0.10). Alternative (direction EITHER WAY): any
    card's mere presence changes behavior — the true/false contrast is then read
    against the irrelevant arm instead of the recorded baseline, disclosed.
primary quantities (all on committed picks, with abstention rates reported beside):
  true movement    compatible-subset committed mass under T minus under the baseline
  false movement   wrong-subset committed mass under F minus under the baseline
bands, exhaustive (no silent interval; movement floor 0.15 chosen against the
recorded baseline's committed mass of roughly 0.2, so the floor is most of a
doubling; at n = 100 a 0.15 mass shift is detectable at 0.80 power):
  CONDITIONS   true movement >= 0.15 AND false movement < half the true movement
  PROJECTION   true movement >= 0.15 AND false movement >= half the true movement
  INERT        true movement < 0.15 (with the leak and purity gates passed)

RESPONSES, recorded now (brief §8 routing). CONDITIONS: context conditions a real
artifact inference; branches A1 minimum-sufficient context and A3 false-biography
adversary (one on untouched data). PROJECTION: suggestion or prior overwrite — the
A5 evidence-conflict test is the single follow-up, then the wing pauses per the
brief's W3 row. INERT: this reader does not use context on this construction; one
predeclared higher-resolution case (the same cards on the process-aware arm, where
the reader demonstrably engages) and then stop. Gates fail: INSTRUMENT-FAIL.

Seed 16700; reader qwen3.5:9b at temperature 0; abstention shifts reported in the
verdict; every statistic on disk; sha256 of this card in the landing entry.
"""

from __future__ import annotations

CARD = {
    "id": "G167",
    "alias": "P23-A0",
    "phase": "2.3 Wing A root",
    "theory_group": "Reader Heuristics",
    "written_before_run": True,
    "seed": 16700,
    "substrate": "corpora/g166_routes + recorded L154 classify arm as baseline",
    "primary": "compatible-subset committed-mass movement, true vs false cards",
    "bands": {"CONDITIONS": "true >= 0.15, false < half of true",
              "PROJECTION": "true >= 0.15, false >= half of true",
              "INERT": "true < 0.15"},
    "gates": ["card_leak_audit_first", "pipeline_purity",
              "irrelevant_card_stability_0.10"],
    "interfaces": {"all arms": "I1 plus declared context"},
}
