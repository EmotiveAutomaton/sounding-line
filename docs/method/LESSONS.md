# LESSONS — read the matching section before designing, building, or adopting anything

**This file exists so a mistake is made once.** It is for the agent, not the curator: every entry
is a rule earned by a failure or a win in this project, stated as an instruction, with the receipt
(FINDINGS entry or file) so the evidence can be re-examined. **The binding moments are wired into
the grind skill (steps 1 and 6) and `CLAUDE.md`: when a hypothesis becomes a test design, and when
a design becomes a runner, the matching section here gets read first.**

Maintenance: a new lesson lands in the same pass as the finding that earned it, in the section
matching its trigger moment, one entry per lesson, receipt required. When a lesson is refined,
fold it; never append a contradiction.

---

## §1. Before adopting a published number as a gate

- **Run the self-consistency check first.** Test the number against every other number in the
  paper that constrains it: the majority-F1 identity ((2s/(1+s))/k pins a majority share), class
  distributions reweighting per-class tables, subtotal sums. Three papers checked this way, three
  internal contradictions found: ArgRewrite's fine Majority row contradicts its own Table 4;
  ScholaWrite's 0.64 is unreachable from its own per-class table; BST's text and figures disagree
  on a count and a parameter. (L77, L78, L79; the check is a TOOLS instrument row.)
- **Composition before tuning, always.** Every recreation gap that closed, closed through
  construction (the unit rule, the split, the oversample), never hyperparameters. If n or a
  baseline row is off, stop modeling and hunt the construction; the n is the search map. (L72,
  L76, L79, L80)
- **Protocol leverage dwarfs model leverage.** Measured here: split leakage 20-30 points;
  pre-evaluation oversampling 32 macro points; input truncation side ~16 points; class weighting
  2-3; architecture 1-6; encoder version ≤0.3. A benchmark number is mostly its construction.
  (L82, L81, L86, L85)
- **Best-fit and cross-validated cells are different numbers.** Never cross them when recording
  gates; record both if the paper reports both. (L78)
- **Expect the published protocol to include the paper's own bugs.** ScholaWrite's 0.64 was
  produced with a token-wrapper typo its senior author later confirmed; a faithful arm reproduces
  the bug, and "fixing" it silently is a deviation from the recreation. (L77, L86)
- **When a number resists, try to reproduce it by breaking your pipeline the way you suspect
  theirs was broken.** The duplication probe (seeded pre-CV oversampling) turned an augmentation
  inference into a demonstration by reproducing the "impossible" majority row to the digit; its
  signature is exact majority reproduction plus rare-class overshoot. (L81)
- **Grid searches over-select.** Our grid picked a learning rate the authors' own footnote
  contradicts and still explained nothing; prefer published hyperparameters when they exist,
  and treat search-maxima cells as possibly optimistic. (L80, L85)

## §2. Before building an extractor over someone else's data

- **The unit of analysis is theirs, not yours.** Find the corpus's canonical reader (ArgRewrite:
  the toolkit's mergeUnit over Revision Index; ScholaWrite: the authors' training script) before
  writing your own. Two plausible-but-wrong unit definitions cost three runs. (L79, L77)
- **Multi-label handling is a named rule, never a default.** ArgRewrite discards multi-purpose
  units outright; our silent first-listed pick redistributed classes. (L79)
- **Parse compound references completely.** Our aligned-index reader truncated comma-separated
  many-to-many indices to their first entry, orphaning sentences into fake deletions. (L79)
- **Audit the shipped split before trusting any number computed on it.** ScholaWrite's shipped
  train/test is within-project with 85 percent before-text overlap, and that leak IS the
  published protocol. Grouped (leave-one-project-out) evaluation is the leak-free form, and any
  program use of such data must be grouped by construction. (L68, L82)
- **Look for the absent class.** A class present in the data but missing from the paper's
  per-class table (Scientific Accuracy) is a protocol clue, not noise. (L77, L86)
- **Pinned revisions rot.** The dataset revision ScholaWrite's code pins no longer exists even
  under gated access; record what is canonical-by-default when the pin is dead. (L82)

## §3. Before building a statistic or instrument

- **Validate the ruler on data whose answer you know, before the signal.** Hard rule; planted
  known-answer gates are cheap and they fire (a trusted criterion once returned 335 components
  on pure noise; PD-34's planted-trend gate; the event-harness gates caught two of its own
  faults). (CLAUDE.md hard rules; L74, L56)
- **Check that the criterion CAN fail.** A z-scored variance is 1 by construction; a
  shuffle-ratio of an order-invariant statistic cannot exceed 1 for any data. Write the failure
  condition before the run and confirm it is reachable. (L53, L55)
- **Match the statistic's invariances to the question.** Variance cannot see movement; an
  order-sensitive statistic (trend, changepoint) can, and it re-licenses the within-item shuffle
  null that dispersion voided. (L55, L74)
- **In the n << d regime, raw similarity magnitudes are uninterpretable.** Independent noise
  scores 0.985 under CKA at 30×2048; only null-tested match structure is ever quotable. (L61)
- **Blind floors follow the truth's label marginal, whatever the decoys.** The estimand is the
  margin over the MEASURED floor; truth-balanced subsampling makes the floor analytic. (L62,
  L64, L65)
- **Matching can raise the floor instead of lowering the signal.** The G130c collision left
  recovery untouched and moved the blind floor from 0.23 to 0.40; always re-measure the floor on
  the matched subset. And leave no silent band between pre-registered verdict thresholds. (L73)
- **Power before verdicts.** The leaked channel was measured three times at sample sizes that
  could not see it; near-significance means raise n with everything frozen, not report a
  failure. (FINDINGS L16 history; D5 in the methodology record)
- **Denominators are declared opportunities, never words.** Per-word density resurrects the
  length trap that killed the first generation of measures. (DECISION_TRACES §1)
- **Measures of the reader's state die; within-reader ratios on the same text survive.** The
  design lesson of the whole reader-side battery: cancel the big confounds by construction
  before measurement. (THREE_COGNITIVE_LAYERS §7)
- **Pair tasks need the change stated.** A revision is defined by its delta; concatenated
  representations never state it. Nineteen string-diff features beat a thousand embedding
  dimensions on the published pair task, and embeddings ADDED to change signal can hurt. Any
  reader arm judging a revision sees the diff explicitly, and the 19-dim change block is a
  declared baseline it must beat. (L85; `change_features()` in `run_arg_replication.py`)
- **Run the explored-paths check before adopting any established technique.** Three questions,
  all must pass: what is this technique's ceiling, and is our question below it (stylometry's
  ceiling is author identity; LIWC's is r≈0.3 self-report correlation)? What do we have that its
  builders did not? Which of our unique assets does it use? Our assets, for question two: the
  worked theory, the ground-truth simulation, model internals plus a theory of what to look
  for, the curator's high-resolution readings, and the unclaimed forward predictions in the
  sim's EVIDENCE.md. When choosing an instrument, open EVIDENCE.md and prefer questions sitting
  in an unclaimed row. (archive/method/ANTI_CONVENTION.md, kept whole)

## §4. Before the model arm

- **Class/sample weighting is a small lever** (2-3 macro points against 24-point gaps); do not
  expect it to explain a collapse. (L81 supplement, in-house confirmation)
- **Difference features rescue exactly the classes defined by small edits** (grammar/spelling
  .06 → .49); apply them where the class semantics are about the change. (L85)
- **Pin determinism**: fixed seeds, fixed thread counts (`n_jobs=-1` ties results to host load;
  boosted trees are thread-order dependent), record library versions when a number will be
  compared across days. (L85)
- **Encoder/library version drift is usually small** (≤0.3 points across sentence-encoder
  checkpoints; ≤0.3 across tree-method variants) — measure it before blaming it. (L85)
- **Overshooting a published gate diagnoses differently from undershooting**: overshoot says
  inflation (leakage, duplication) somewhere; undershoot says a missing lever. (L68, L75)

## §5. Before queueing or touching the loop infrastructure

- **Every stage carries a `produces` guard**; one without it re-ran 160 minutes per pass.
- **Underestimate runtimes 2-3×** and keep the queue 4-8 hours deep. GPU stages serialize
  through `results/.gpu.lock` inside the runner, so shards cannot collide on the card; expect
  lock-queue starvation to reorder stages and read per-stage logs, not shard logs, for stage
  output. (TOOLS loop-scripts row)
- **Bare-launched shells have no PATH** (`date`/`cat` silently empty, deadline arithmetic
  collapses); loop scripts export PATH first. Kill loops by the lock's WINDOWS pid (line 2) with
  a tree kill; msys pids do not map. Sweep orphans at startup. (G121 history)
- **Verify hash locks and read git-status deletion lines before any commit**; locked files live
  at recorded paths in DEVIATIONS when they move. Never grep a pid out of tasklist by substring
  (it matches memory columns); query the process list structurally. (the waiter bug, 08-10)
- **Long jobs run in the background and wake the agent**; results are written through the same
  message they land, and a queue log line counts as landing. (CLAUDE.md grind contract)
