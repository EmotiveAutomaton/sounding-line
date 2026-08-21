# LESSONS — read the matching section before designing, building, or adopting anything

**This file exists so a mistake is made once.** It is for the agent, not the curator: every entry
is a rule earned by a failure or a win in this project, stated as an instruction, with the receipt
(FINDINGS entry or file) so the evidence can be re-examined. **The binding moments are wired into
the grind skill (steps 1 and 6) and `CLAUDE.md`: when a hypothesis becomes a test design, and when
a design becomes a runner, the matching section here gets read first.**

Maintenance: a new lesson lands in the same pass as the finding that earned it, in the section
matching its trigger moment, one entry per lesson, receipt required. When a lesson is refined,
fold it; never append a contradiction. **Reorganised 2026-08-14 at the curator's direction**
(the gate section had grown into a wall; it is now four trigger moments with an index), entries
preserved whole.

**What the recreation phase did to this file, in one paragraph (consolidated 2026-08-16).**
Phase 1 tripled the shelf and changed its center of gravity: the project entered the phase
believing a recreation was a run and left knowing it is a chain of custody. The pattern that
recurred at every scale — in the papers we checked, and three times in our own record — is
that a conclusion outran its verification and was later walked back by a stricter pass
(closed-as-correction twice before the headline turned out reproducible; a "reproduced" cell
carrying our own features; a fleet strengthening recorded without its arithmetic). Every §1
entry is a scar from that pattern, and the audit chain that caught each instance
(L26→L61→L93→L107→L108→L109→L123) is itself the method: verdicts are provisional until an
adversarial pass has tried to kill them, corrections get the same rigor as findings, and the
current truth lives in the folded end-state of the record, never in an interim summary.

## THE TRIGGER INDEX — the moment you are in → the section you read

| you are about to… | read |
|---|---|
| adopt a published number as a gate, or believe a benchmark cell | **§1a** |
| build or modify a faithful/recreation arm (theirs, re-run) | **§1b** |
| issue a MATCHED / NOT-MATCHED / irreproducible verdict | **§1c** |
| train on any corpus that blends editions, years, or releases | **§1d** |
| write an extractor over someone else's data | **§2** |
| build a statistic, instrument, control, or falsifier | **§3** |
| train or configure a model arm | **§4** |
| add a queue stage, touch the loop scripts, or launch anything long-running | **§5** |
| choose or doubt a control | `CONTROLS.md` |
| touch a hash-locked file or protocol | `DEVIATIONS.md` |
| claim novelty, adopt a field framing, pick a corpus | `LITERATURE.md` |
| map model quantities onto brain vocabulary | `NEURAL_ANALOGUES.md` |

---

## §1a. Before adopting a published number as a gate

- **Run the self-consistency check first.** Test the number against every other number in the
  paper that constrains it: the majority-F1 identity ((2s/(1+s))/k pins a majority share), class
  distributions reweighting per-class tables, subtotal sums, printed accuracy against printed F1.
  Stated precisely (L123's correction of the loose tally): four of the five works checked this
  phase carried internal inconsistencies (ArgRewrite's Majority rows vs Table 4; ScholaWrite's
  0.64 vs its own table and accuracy; BST's stimulus count vs plotted content and its M3 β
  captions; the PAN metric prose vs its own evaluator, one defect shared across sibling overview
  papers) — the analytic paper was clean, and the hit rate matches the meta-research base rates,
  not a broken check. (L77, L78, L79, L102, L107, L123; the check is a TOOLS instrument row.)
- **An evaluator's source outranks its paper's prose, and baselines back-calculate.** All three
  PAN overview papers describe per-document macro-averaging; the shipped evaluator pools every
  decision and macro-averages over the two classes. Six published baseline cells back-calculated
  exactly from the implied class priors under the pooled reading and falsified the prose. Before
  gating on a benchmark number: read the evaluator's code, and check that predict-all-X baselines
  reproduce from the class marginal under your reading of the metric. (L102)
- **A held-back test set makes the printed headline unreachable by construction; the notebook's
  own validation table is the honest gate.** Check which split a published number lives on before
  adopting it — TIRA-style shared tasks never release theirs. (L102)
- **Best-fit and cross-validated cells are different numbers.** Never cross them when recording
  gates; record both if the paper reports both. (L78)
- **State which of reproduce / replicate / robustness a row attempts** (same artifacts, same
  methods on our artifacts, or our methods entirely), because "not reproducible" means a
  different thing in each. (L107)
- **Re-check paper, repo, and dataset versions before closing a row** — a revision posted after
  a bug fix can silently invalidate a closure, and ScholaWrite's per-class table first appeared
  eleven days after its training-script fix. (L107)
- **Before weighting "someone would have noticed," check whether anyone ever ran the
  numbers.** The external sweep found zero third-party reproductions for either ScholaWrite
  (twelve citing papers, none using its labels) or ArgRewrite (no classification code ever
  released, zero issues) and no BST replication in seventeen years: absence of complaints
  measured absence of scrutiny, not correctness. The meta-research base rates (statcheck
  49.6 percent of articles with at least one internal inconsistency; GRIM 50.7; ML audits
  44.9) make at-least-one-hit-per-paper the modal outcome of running real checks. (L123)
- **A strengthened claim whose derivation is not written into the record is not yet a
  claim.** L109's "Majority rows mutually incompatible independent of Table 4" could not be
  reconstructed by a second verifier and was downgraded; the conclusion had been recorded
  without its arithmetic. Fleet findings enter the record with their derivation spelled out
  or they enter as PLAUSIBLE, never CONFIRMED. (L123)

## §1b. Before building a faithful or recreation arm

- **Composition before tuning, always.** Every recreation gap that closed, closed through
  construction (the unit rule, the split, the oversample), never hyperparameters. If n or a
  baseline row is off, stop modeling and hunt the construction; the n is the search map. (L72,
  L76, L79, L80)
- **Protocol leverage dwarfs model leverage.** Measured here: split leakage 20-30 points;
  pre-evaluation oversampling 32 macro points; the non-faithful-to-faithful recipe composite (input side + loss + epochs together) ~16 points; cross-year
  memorization ~3 blended points; class weighting 2-3; architecture 1-6; encoder version ≤0.3.
  A benchmark number is mostly its construction. (L82, L81, L86, L85, L106)
- **A faithful arm reproduces the training FRAMEWORK, not the printed hyperparameters.**
  Framework defaults are load-bearing and unstated by construction: HF Trainer silently
  supplies linear LR decay to zero, gradient clipping at 1.0, and weight-decay exclusion of
  bias/LayerNorm. If the authors used Trainer, match Trainer — a hand-rolled loop matching
  the four printed numbers is a different pipeline. (L107, the ScholaWrite reopening)
- **Expect the published protocol to include the paper's own bugs — and then measure whether
  the bug has any leverage before citing it.** ScholaWrite's token-wrapper typo was faithfully
  reproduced, and the second referee then showed it inert: same tag on both sides in the
  paper-era code, truncated away on 89 percent of inputs. Reproducing a bug is correct;
  attributing any gap to an unmeasured bug is not. (L77, L86, corrected by L108)
- **A confirmatory arm implements the NAMED mechanism, not just the target number.** If the
  source says training-fold synonym replacement, the arm is that; reproducing the printed
  cell by pre-CV duplication — a mechanism the source disclaims — is a coincidence read as
  confirmation, the modeling face of the criterion that cannot fail. Check the inference
  against every sibling cell it also constrains before calling it demonstrated. (L107, the
  ArgRewrite downgrade)
- **When a number resists, breaking your pipeline the way you suspect theirs was broken is a
  DIAGNOSTIC, never a demonstration.** The duplication probe reproduced the "impossible"
  majority row to the digit and was recorded as confirming their mechanism — then the paper's
  own text named a different, fold-safe mechanism, and sibling cells contradicted the
  inference. The probe's honest product is the signature of what a defect class looks like
  from outside. (L81 as corrected by L107)
- **Persist predictions from every model arm** — id, truth, prediction, score — so any later
  split (contamination, per-class, per-covariate) is minutes instead of a retrain. (L107;
  the PAN contamination split took two minutes because predictions existed)

## §1c. Before issuing a MATCHED / NOT-MATCHED / irreproducible verdict

- **No verdict on a fine-tune arm from one seed.** Single-seed fine-tuning moves task metrics
  one to two points routinely (Dodge 2020; Mosbach 2021); the minimum standard is three seeds,
  mean and spread reported, the published value judged against the seed interval, and
  irreproducibility stated as a bounded gap, never a binary. (L107)
- **When a protocol is underdetermined, report the specification curve, not one faithful
  point.** Enumerate the defensible readings of every unstated choice (epochs, batch,
  schedule, checkpoint rule, input variant), run the set, and state where the published value
  falls in that band — "above the k-th percentile of the protocol space" is falsifiable where
  "our faithful run missed it" is one point against one point. (L107)
- **Grid searches over-select.** Our grid picked a learning rate the authors' own footnote
  contradicts and still explained nothing; prefer published hyperparameters when they exist,
  treat search-maxima cells as possibly optimistic, and when running a grid-max arm persist
  every candidate with the published config's rank so the optimism is measured, not assumed.
  (L80, L85, L108)
- **Author contact is OFF THE TABLE, the curator's standing ruling (2026-08-14).** Do not
  suggest it, file it, or condition any wording on it. Irreproducibility wording stands on the
  exhausted-public-routes evidence alone, stated as "not reproduced by us from the released
  materials" with the gap bounded. (Overrides the referee import that briefly made contact a
  required step.)
- **Overshooting a published gate diagnoses differently from undershooting**: overshoot says
  inflation (leakage, duplication, memorization) somewhere, OR a stopping-rule difference —
  check the per-epoch history before alleging inflation, because a print that sits inside the
  faithful arm's own training trajectory is consistent with an unstated earlier checkpoint,
  no inflation required. Undershoot says a missing lever. (L68, L75, L106, L110)
- **A mid-trajectory crossing is a checkpoint-rule HYPOTHESIS, never a closure; its
  discriminating test is the second architecture.** Both ScholaWrite framework seeds cross the
  printed 0.64 mid-training and pass the table-implied 0.59 at epoch five — and the
  same-shaped PAN epoch-four coincidence died when the second member's trajectory refuted it.
  A paper printing one value for two architectures hands you the test: the reading survives
  only if both trajectories cross it. Report the bracket (the print inside the specification
  range) and run the second arm before believing the crossing. (L108, L110)

## §1d. Before training on blended corpora — benchmark data hygiene

- **Sibling-edition augmentation gets exact-hash dedup against every evaluation split before
  training.** PAN deduplicates within-year and not across years: the winner's own recipe put
  16 percent of validation pairs verbatim into training, and the models scored 1.0 on them.
  A leaked-subset score at ceiling is the memorization signature; rescore blended results on
  the leak-free subset before quoting capability. Exact-hash proved tight here (normalization
  moved nothing), but the near-duplicate pass is part of the gate until measured. (L106, L107,
  L108)
- **Check within-year too.** PAN's own easy and medium splits leak their validation from their
  own training data (13-19 percent); only hard was clean. Organizer dedup is a claim to verify,
  never an assumption. (L108)
- **A settling arm must be identified.** Removing a whole augmentation to test its leak
  confounds the leak with the data volume; the identified form drops only the contaminated
  documents (210 of 4,200 here, keeping 97 percent). (L108)
- **Audit the shipped split before trusting any number computed on it.** ScholaWrite's shipped
  train/test is within-project with 85 percent before-text overlap, and that leak IS the
  published protocol. Grouped (leave-one-project-out) evaluation is the leak-free form, and any
  program use of such data must be grouped by construction. (L68, L82)

## §2. Before building an extractor over someone else's data

- **The unit of analysis is theirs, not yours.** Find the corpus's canonical reader (ArgRewrite:
  the toolkit's mergeUnit over Revision Index; ScholaWrite: the authors' training script) before
  writing your own. Two plausible-but-wrong unit definitions cost three runs. (L79, L77)
- **Multi-label handling is a named rule, never a default.** ArgRewrite discards multi-purpose
  units outright; our silent first-listed pick redistributed classes. (L79)
- **Parse compound references completely.** Our aligned-index reader truncated comma-separated
  many-to-many indices to their first entry, orphaning sentences into fake deletions. (L79)
- **Look for the absent class.** A class present in the data but missing from the paper's
  per-class table (Scientific Accuracy) is a protocol clue, not noise. (L77, L86)
- **Pinned revisions rot.** The dataset revision ScholaWrite's code pins no longer exists even
  under gated access; record what is canonical-by-default when the pin is dead. (L82)
- **A decode of published figures has its own known-answer gate: the paper's printed counts.**
  The Fig-3 stimulus decode looked healthy at the panel level and held a third of the paper's
  99 stimuli; nothing downstream of an extraction means anything until the extraction hits the
  source's own totals. (L107, L108, the BST decode gate)

## §3. Before building a statistic or instrument

**STRUCTURAL, 2026-08-18 (his ruling, after the class recurred through the prose rule):**
every new prereg card or gate-bearing runner carries a **DESIGN CHECK block** in its header,
naming the sections of this file read for that design and deriving, for every gate, its
expectation under the null AND under the alternative with the failure direction it guards,
bands exhaustive. The `design_lint` PostToolUse hook enforces presence; the derivations'
correctness still binds by being read. Receipts for the class: L73 (silent verdict band),
L132 (a shuffle gate that voided the alternative's own signature).

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
- **Fix the label set in every averaged F1.** Macro-F1 without labels= silently shrinks its
  denominator when a near-empty class misses a fold, inflating the score; every per-class
  average declares its class list. (L108)
- **In the n << d regime, raw similarity magnitudes are uninterpretable.** Independent noise
  scores 0.985 under CKA at 30×2048; only null-tested match structure is ever quotable. (L61)
- **Blind floors follow the truth's label marginal, whatever the decoys.** The estimand is the
  margin over the MEASURED floor; truth-balanced subsampling makes the floor analytic. (L62,
  L64, L65)
- **Matching can raise the floor instead of lowering the signal.** The G130c collision left
  recovery untouched and moved the blind floor from 0.23 to 0.40; always re-measure the floor on
  the matched subset. And leave no silent band between pre-registered verdict thresholds. (L73)
- **Every void gate states its DIRECTION and its expectation under the ALTERNATIVE, not only
  under the null.** The G129 shuffle gate said "at chance or void" and then fired on a
  below-chance read that is the a-priori signature of the very success the battery was testing
  (shuffled labels fall outside truth-anchored candidate sets, expected 0.125 for a
  delta-tracking reader, observed 0.110), while the leak it guarded against pushes the number
  UP. A gate that can void the alternative's own fingerprint is mis-specified; derive both
  expectations before the run and write the failure direction into the card. Same defect class
  as the silent-band lesson above. (L132)
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
- **Magnitude and signed forms of a trend statistic dissociate; run both.** Essays showed no
  |trend| asymmetry yet decay cleanly in signed form, because many small sign-consistent
  slopes are invisible to magnitude statistics. A movement claim and a direction claim are
  different instruments. (L89)
- **Window size is a member of the statistic family, not a nuisance choice.** The books
  movement asymmetry held at the 80-word window and vanished at 40, and later the one machine
  decay cell did exactly the same; claim nothing from one window. (L89, L105)
- **Run the interpretation control before adopting the reading, not after.** PD-3's machine
  corpus was queued as a formality and instead reversed the interpretation of a standing human
  positive. A control that cannot flip the result can still flip the reading. (L89)
- **Every statistic a verdict rests on gets written to the output file, not only printed.**
  The signed arm's Wilcoxon backed its verdict and existed nowhere on disk; it had to be
  recomputed before it could be quoted. (L89; runner patched same pass)
- **A falsifier is an instrument, and its baseline arm is a known-answer gate.** Before an attack
  run's deltas mean anything, the arm that reproduces our own published pipeline must land on the
  known value; a mismatch there is hunted, never explained away in the verdict prose. And after
  any truncation or subsetting, print the design composition (rung counts, class counts) —
  ordered manifests turn head-truncation into silent selection, which is how a pooling attack was
  run on two rungs of five and read as a dose result. (L44 correction, L93)
- **Run the explored-paths check before adopting any established technique.** Three questions,
  all must pass: what is this technique's ceiling, and is our question below it (stylometry's
  ceiling is author identity; LIWC's is r≈0.3 self-report correlation)? What do we have that its
  builders did not? Which of our unique assets does it use? Our assets, for question two: the
  worked theory, the ground-truth simulation, model internals plus a theory of what to look
  for, the curator's high-resolution readings, and the unclaimed forward predictions in the
  sim's EVIDENCE.md. When choosing an instrument, open EVIDENCE.md and prefer questions sitting
  in an unclaimed row. (archive/method/ANTI_CONVENTION.md, kept whole)
- **"Gate met" language only follows every gate passing under the card's own terms.** The G129
  battery had a voided control and a disclosed-but-unapplied power downgrade, and the record
  still said the gate was met; an external audit had to force the demotion. A post-hoc-derived
  correction to a gate's expectation, however sound, repairs the NEXT card — the run whose gate
  fired keeps its void, the claim demotes to the highest tier the passing gates support, and a
  fresh run under the corrected card is what re-earns the grade. Disclosing a clause is not
  applying it. (L132 → L137)
- **Assigned is not realized.** Ground truth from generated-instruction corpora is what the
  generator was ASKED, and a 9B model executed only ~64% of mechanically checkable
  instructions; a reader scored against assignments is penalized for correctly seeing an
  instruction was ignored. Realization must be verified (mechanical checks first, adjudication
  with evidence spans for the rest) or crossed as its own intervention before any
  known-answer claim; instruction-following side effects (surface constraints shortening
  essays out of their length band) are themselves confounds to match. (L137; G131 first corpus)

- **An instructed-handling corpus verifies REALIZED handling at accept time, never only
  at audit time.** The long-form concealment corpus generated to completion and then
  refused itself: the generator concealed by omission (plant presence 0.63) and realized
  hedging sat under its floor — the same assigned-is-not-realized class as L137, caught
  by the audit gate built from L150's post-mortem, at the price of a full regeneration
  pass. The v2 form checks each family's mechanical criteria inside the generation
  accept loop (plant present, correction present or absent as instructed, hedge count),
  so a non-compliant artifact costs one retry instead of a corpus. (L156, run_g169_longform.py)

## §4. Before the model arm

- **Set model internals structurally, assert the change took, and record the measured value.**
  A dropout setter keyed on one attribute silently missed roberta's (it lives on the
  classifier), and the output file recorded the requested 0.25 while the model ran 0.1 — a
  false provenance record, worse than a missing one. Iterate modules, assert, write what was
  measured, never what was asked. (L108)
- **Record environment versions in every output that will be compared to a published number**
  (transformers, torch, sklearn at minimum); the comparison is across days and against a
  foreign machine by construction. (L108; every active model runner now does)
- **Watch for architecture-specific training hazards**: roberta-base collapses to constant
  predictions at lr 5e-5 without warmup; DeBERTa-v1's disentangled attention overflows under
  fp16 autocast. A member that diverges is rerun under a recorded stabilizer, never quietly
  dropped, and every member of an ensemble shares one recipe. (L104, L108)
- **A printed regularizer without a stated scope is ambiguous, and the scopes are not
  interchangeable; run the readings as arms — and treat a member-level collapse as evidence
  of an instability region, never as proof of the paper's scope.** All-module dropout 0.25
  flatlined roberta-base for nine epochs, then a near-identical run trained normally
  (L118): the collapse is stochastic fragility. A configuration that sometimes collapses
  cannot anchor a comparison in either direction; the one-recipe vote uses the scope that
  trains reliably, with the fork recorded as a specification axis. Fragility is
  model-conditional besides (roberta is also the member that collapsed without warmup).
  (L111, corrected by L118)
- **Class/sample weighting is a small lever** (2-3 macro points against 24-point gaps); do not
  expect it to explain a collapse. (L81 supplement, in-house confirmation)
- **Difference features rescue exactly the classes defined by small edits** (grammar/spelling
  .06 → .49); apply them where the class semantics are about the change. (L85)
- **Pin determinism**: fixed seeds, fixed thread counts (`n_jobs=-1` ties results to host load;
  boosted trees are thread-order dependent). (L85)
- **Encoder/library version drift is usually small** (≤0.3 points across sentence-encoder
  checkpoints; ≤0.3 across tree-method variants) — measure it before blaming it. (L85)

- **A model adjudicator is a ruler and gets the ruler treatment: validate on a decidable
  subset before consuming a single verdict.** The G158 realization adjudicator (local
  reader, temperature 0, required evidence spans, an explicit honest-no option) credited
  69% of instructions an exact string test proves were ignored, never used its ambiguous
  option in 636 judgments, and produced verbatim spans that did not satisfy the
  instruction they were quoted for. Acquiescence has a signature: near-zero under-credit
  beside massive over-credit. Requiring evidence is not the same as requiring the evidence
  to discriminate; the validation must be stratified toward the negative class, and it
  runs BEFORE the adjudication arms, not after (here it ran after and voided 556 landed
  verdicts). (L139)

## §5. Before queueing or touching the loop infrastructure

- **Every stage carries a `produces` guard**; one without it re-ran 160 minutes per pass. **And
  no two stages may ever share a produces path** — the earlier stage runs first, writes, and
  the later (corrected) stage skips forever; the queue asserts uniqueness at load. (L108)
- **A corrective stage list is audited with the same rigor as the results it corrects.** The
  second referee found the fix-arms themselves carrying three recipe divergences, one of them
  training at that moment. (L108)
- **A clean exit that wrote no produce is a failure, not a DONE** — the queue enforces it; a
  silent per-corpus skip ran "DONE" for a day while its consumers sat deferred. (2026-08-13)
  **And the exists() check retries up to ten seconds before declaring no-produce**: one stage
  recorded a false failure with its produce on disk at the stage-end minute (mechanism
  unidentified; filesystem visibility straight after subprocess exit is not trusted bare). A
  false no-produce costs a 150-minute rerun; the poll costs nothing. (gridmax, 2026-08-14)
- **The GPU lock's staleness window must exceed the longest queued stage's REAL runtime,
  which is its estimate times the 2-3× underestimate rule — and QUEUEING A LONGER STAGE IS
  THE TRIGGER TO RE-CHECK.** The 5-hour window sat under the 5-to-7-hour framework arms and
  collided two trainings (the fp32 deberta OOM); raised to 9 hours, and then a 620-minute
  stabilizer rung outran THAT window at hour nine, its live lock reclaimed by an ollama
  generation that then shared the 12GB card with a mid-epoch training. Same failure, second
  window. Now 22 hours, and the re-check is part of adding any stage whose estimate exceeds
  a third of the current window. (L111 then 2026-08-17, gpulock.py)
- **A filename two code paths share is built by ONE helper, never by two hand-written
  f-strings.** The vote consumer built `{enc}_{difficulty}_val_preds{tag}.json` while the
  trainer wrote `{enc}_{difficulty}{tag}_val_preds.json`; the vote failed on every tagged
  member across three queue passes before the constructions were unified, and the defect was
  invisible in review because each f-string read plausibly alone. (L133, run_pan_winner.py)
- **A model-serving endpoint under VRAM churn throws transient 500s; every caller retries
  with backoff before dying, and a generation stage never writes its manifest over a thin
  yield.** An arm died at 0.6 minutes to one transient 500; and the generation runner's
  produces-guard would have been satisfied by a manifest written after silent per-artifact
  failures, permanently freezing a thin corpus. Retry loops in every ollama caller;
  manifests withheld (nonzero exit, stage retries) below 90% yield. (2026-08-17,
  run_g129_confirm.py / run_g153_local_gen.py)
- **Underestimate runtimes 2-3×** and keep the queue loaded to the gear: second gear
  (`run_second_gear.sh`, the whole machine) carries about a day's worth of analyses, first gear
  (`run_first_gear.sh`, part of the CPU, the GPU mostly the curator's) four to eight hours of
  light stages. GPU stages serialize through `results/.gpu.lock` inside the runner, so shards
  cannot collide on the card while the lock's staleness window exceeds every stage's runtime
  (the staleness entry above); expect lock-queue starvation to reorder stages and read
  per-stage logs, not shard logs, for stage output. (TOOLS gear-scripts row; gears replaced day/night
  2026-08-12)
- **Bare-launched shells have no PATH** (`date`/`cat` silently empty, deadline arithmetic
  collapses); loop scripts export PATH first. Kill loops by the lock's WINDOWS pid (line 2) with
  a tree kill; msys pids do not map. Sweep orphans at startup. (G121 history)
- **The regear waiter checks for a LIVE ENGINE before relaunching, not only for a drained
  queue.** A drain-triggered waiter fired while the prior lineage was still mid-window,
  running two second-gear engines side by side (harmless only because produces-guards and
  the gpu lock held); the waiter's precondition is drained AND no live gear process by
  enumeration. (2026-08-18)
- **A harness-killed background shell can survive as an msys child and keep executing; any
  long-lived waiter honors a CANCEL FILE checked every poll and again immediately before its
  action.** A relaunch waiter reported successfully stopped fired its relaunch thirty seconds
  later, colliding a fresh second-gear lineage into a first-gear shift; the rogue lineage ran
  LOCKLESS (its lock file lost to an rm race), so it was findable only by process enumeration,
  never by lock. When a lineage might be lockless, verify by enumerating processes, not by
  reading locks. (2026-08-14, the gear-shift incident; regear2_when_idle.sh carries the
  cancel-file protocol)
- **The orphan sweep kills what no live loop owns — including legitimate standalone arms.** A
  training launched outside the queue dies at the next engine relaunch and, if a waiter restarts
  it, loops from epoch zero forever; the failure is invisible until someone asks for an ETA. A
  long standalone GPU arm gets one of three protections before launch: queue membership (a stage
  with a produces guard), checkpoint-resume, or its winpid on the sweep's keep-list. (L93)
- **A produces-guard protects ownership, not compute: any training longer than a few hours owes
  checkpoint-resume.** A circuit-breaker outage killed a 620-minute deberta rung at epoch 7 of
  10 (~17 hours with contention), and the produces-guard's only recovery is a restart from
  epoch zero — the guard made the loss safe, not small. Per-epoch checkpointing with resume is
  the owed build for the long training runners; until it lands, every 10-hour stage carries a
  full-restart risk priced at its own runtime. (2026-08-17, the outage)
- **A deadline exit with no successor idles the machine silently.** Second gear stopped at its
  deadline mid-morning and nothing relaunched it; seven hours of a prescribed 24-hour window
  burned before the evening check noticed. Size the deadline to the curator's stated window at
  launch, and treat "the engine exited" as a wake-and-decide event, never as background noise.
  (2026-08-13; the launcher's exit notification is the wake signal)
- **Verify hash locks and read git-status deletion lines before any commit — from the repo
  root, with the commit GATED on the check's exit.** A lock check chained before a commit
  failed on a wrong working directory and the commit ran anyway (clean by luck, verified
  post hoc). Locked files live at recorded paths in DEVIATIONS when they move. Never grep a
  pid out of tasklist by substring (it matches memory columns); query the process list
  structurally. (the waiter bug, 08-10; the ungated commit, 08-14)
- **Long jobs run in the background and wake the agent**; results are written through the same
  message they land, and a queue log line counts as landing. (CLAUDE.md grind contract)
- **Gear 3 (cloud burst) runs ONLY through `runners/gear3.py`, never a bare modal call.** The
  wrapper is where the curator's stone rules live: per-use approval required, the $10 window
  with launch-time reservation under a file lock (parallel chains cannot both pass the
  ceiling) and the final-approval-request refusal path, the ledger, the timeout kill, and
  the estimate tax. Recreation-gate arms stay local; gear-3 comparisons are internal to one
  cloud run. **And the produce retrieval brings home every sibling sharing the produce's
  stem** — the persist-predictions lesson crosses the wire; the first package's error-overlap
  read was lost with the containers before this was fixed. (his rulings 2026-08-16; STATE
  standing ruling 6; L124, L125)
- **A lock without a same-holder check deadlocks its own process; every per-arm lock
  acquisition inside one runner is that bug waiting.** The stage-c runner took the GPU lock
  per arm; arm one held it, arm two waited on it, and the process starved itself for five
  hours of a live gear window while the 22-hour stale sweep sat 17 hours away (2026-08-19).
  Two rules, both now structural: `acquire_gpu_lock` is reentrant by pid (re-acquisition
  under a new tag rewrites the tag and returns), and a runner acquires the card ONCE per
  invocation, never per arm. The kill followed the standing protocol: verify the lock's pid
  against the live process table by command line, stop the tree by Windows pid, clear the
  dead holder's lock, let checkpoints carry the resume. (the g158 stage-c stall; the fix is
  pipe-proven on a throwaway lock before trust)
- **Stage ownership must key on something the stage list cannot move.** Shard ownership by
  list index (stage i to shard i % N) is only race-free while the list never changes; one
  mid-list insertion under a live lineage re-owned every later stage between passes, and a
  stage blocked on the GPU launched under BOTH its old and new owner (2026-08-19, the
  duplicate shuffle arms — benign only because the gpu lock serialized them and checkpoints
  made the loser a no-op). Ownership now digests the stage NAME (md5, because Python hash()
  is process-salted); and while a lineage is live, new stages append at the end, never
  insert mid-list, so even index-keyed consumers see a stable prefix. (run_queue.py fix,
  same pass)
