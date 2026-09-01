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

- **Match the readout class to the behavior the intervention moves.** M01's policy line
  visibly steers GENERATED choices (S02's makers) yet shifts the committed-answer
  likelihood mass by 0.03 — the whole localization program had no signal in its readout
  while its patch controls sat at exactly zero (L203, 2026-08-26). A likelihood readout
  is not a generation readout; pick the one the effect lives in, or run both.
- **Read the baseline marginal of a forced-choice battery before interpreting steering
  deltas.** A07's unsteered baseline put 0.75 of its mass on one tendency (the probe
  frame primed curiosity), so the pooled sign pair rides one attractor and one tendency
  steers backwards (L202, 2026-08-26). Report per-option baselines beside every steering
  table.
- **A manipulation check needs dynamic range in the corpus it checks.** A06's
  suppression check compared emotion-word rates of 0.006 versus 0.005 — the "expressive"
  corpus never used emotion words (makers write tendency through action), so suppression
  was unverifiable by construction (L201, 2026-08-26). Measure the check's baseline
  before building the manipulation on it.
- **A gate dependency is the gate's VERDICT, not its file.** V02/V04/V05 and the C cells
  ran because the queue's needs only test file existence; the V01 and C01 rulers had
  failed in part or whole, and every downstream entry now carries the scoping by hand
  (2026-08-26). Runners behind a gate read the gate's verdict at start (A07's pattern)
  — existence is a scheduling fact, not a license.
- **Gate every cell on realization before any posterior, contrast, or verdict touches it.**
  E01's first analysis compared a "paraphrase-frame" posterior built from ONE realized
  episode (1 of 40; the other domain 0 of 40) against a 39-of-40 plain-frame cell and printed
  "frame_stable: false" (audit 2026-08-24, L176). A cell under 75 percent realized is an
  instrument event and reports as undetermined; per-cell attempted/realized/yield sit beside
  every accuracy in the Stage-3 runners now. The global yield number does not catch this —
  the failure was one cell inside a 0.79 overall.
- **Check that a known-answer design's "known answer" can exist in the environment before
  writing the runner.** E05's first design offered the reader an "uninformative scenario"
  (one where two profiles agree); in this environment every profile's argmax is its own
  option in every scenario, so the item list was empty by construction and the cell would
  have LANDED on zero rows (audit 2026-08-24). The repair is graded: exact expected
  information gain per offer, kept only where the max/min ratio exceeds 1.5.

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

- **A verdict band on a small-probe gate needs its sampling width derived before freezing.**
  A shuffle-floor band of [0.15, 0.35] around a 0.25 expectation excluded two of nine
  readers at 0.375 on 24 probes — inside ordinary sampling noise (standard error ~0.09), so
  the frozen band was ~1.1 standard errors wide and the exclusions were conservative luck,
  not measurement. The exclusion stood because frozen is frozen; the next card derives the
  band from the probe count. Same family as "power before verdicts", applied to the GATES
  rather than the primary. (L163, G172 reader gates)

- **A factorial whose treatment can be silently refused needs a compliance pilot before the
  full grid.** Three instruct makers followed two of four assigned preference profiles at
  0.9-plus and refused the other two at 0.0 to 0.3, because the models hold strong intrinsic
  appetites a one-line instruction does not override; the full 120-cell grid was spent
  discovering what a 12-cell pilot would have shown. Related: L156's accept-time rule covers
  mechanical compliance; this covers PREFERENCE compliance, which no accept gate can force
  without destroying the object being studied. (L169, scout_stage2_p.py)

- **Score the short hypothesis text given the long evidence, never the reverse.** A
  likelihood reader conditioning a hundred-word artifact on a one-sentence hypothesis gives
  the hypothesis one sentence of leverage over a long likelihood, and the known-answer gate
  read exactly chance; flipping the direction makes every scored token hypothesis-bearing.
  The goal-candidate form (short artifact-anchored candidates) never hit this because its
  conditions named content; abstract hypothesis descriptions do. (L169)

- **A session log's document state may exist nowhere in the log.** CoAuthor's field that
  looks like the document holds only the initial prompt, once; the final document must be
  replayed from the edit deltas, and the selected suggestion's text lives on the preceding
  shown-event rather than the selection event. Two silent zeros (0 taken, then 0.2 percent
  retained) were the only symptoms; both were caught because the numbers were behaviorally
  impossible, which is the check that matters. (L167 fold-in, scout_stage2_h.py)

- **A one-number contrast averaged over a heterogeneous comparison set can stay positive
  while the decisive pairwise comparison inside it flips; report the matrix beside the
  contrast.** An own-family-minus-other-family statistic remained positive for both corpora
  at a surface-heavy rung even though the head-to-head between the two strong families had
  reversed, because two weak architectures in the "other" average propped it up. The summary
  was not wrong, it was answering a different question than the one being claimed. Any
  crossed or reversal claim reports its cells. (L166)

- **A transformer used as an ERASER is an instrument and needs an echo gate: measure how much
  it actually changed, per item, and exclude un-transformed items from any survival claim.**
  An instruct paraphraser returned 13 to 27 percent of its inputs essentially unchanged, and
  the rate was twice as high on its OWN family's text as on the other family's, which biases
  exactly the comparison the erasure was built to make. The gate is one character-overlap
  ratio per pair: fail the arm if the median rewrite is cosmetic, and filter the individual
  echoes out of the contrast. Costs nothing; the alternative is a survival claim resting
  partly on artifacts that were never erased. (L165, scout_stage2_s.py erasure_gate)

- **An analysis stage that reads another stage's outputs checks their completion markers
  before computing anything relative.** A crossed own-versus-other contrast was computed over
  a reader matrix that was five of eleven readers deep, so both sides of the comparison were
  set by whichever families had finished, and the cell read 40 percent high. This is "score
  once, at the end" applied to a shared analysis stage rather than to a single gate: the
  produces marker exists, so the reader of a partial directory must consult it. (L165)

- **A dev-selected hyperparameter (block, locus, threshold) is part of the instrument and
  validates like one: the selection must be stable across seeds before anything downstream
  is interpretable, and the dev set must be sized for THAT, not for the headline metric.**
  The first affect ruler selected block 27 at one seed and block 1 at the other from an
  eighteen-item dev split; block 1 is the input-adapter edge, and amplifying there moved
  neutral-text likelihood 2.55×, a lesion recorded as INSTRUMENT-FAIL. Corollary: a
  ratio-shaped control gate ("controls under half the primary effect") degenerates when
  the primary effect is near zero — write the control gate's own failure condition for the
  null-effect case before the run. (L162, run_g174_affect.py)

- **An instructed-handling corpus verifies REALIZED handling at accept time, never only
  at audit time.** The long-form concealment corpus generated to completion and then
  refused itself: the generator concealed by omission (plant presence 0.63) and realized
  hedging sat under its floor — the same assigned-is-not-realized class as L137, caught
  by the audit gate built from L150's post-mortem, at the price of a full regeneration
  pass. The v2 form checks each family's mechanical criteria inside the generation
  accept loop (plant present, correction present or absent as instructed, hedge count),
  so a non-compliant artifact costs one retry instead of a corpus. (L156, run_g169_longform.py)

- **A representation-space separation claim needs the cheap scalars in its surface
  control before it is a claim: sequence count, mean value, spread, length.** The
  transmission carrier read 4/4 in representation space against a digit-profile surface
  control and was cited as the L trunk's standing positive; the adversary's three-scalar
  summary reached 3/4 on the same cells and length-matching dropped the representation
  read to 2/4. A surface control that omits length is not a surface control. (L184
  retracted by L226, s3_run_x.py arm xv4)

- **A known-answer ruler's easy band must have variance in the ANSWER, not only in the
  evidence.** The late-fusion ruler's easy doses were all HOLD by construction, so a
  reader answering HOLD every time would have passed at 1.0 and a passing ruler would
  have been ambiguous between tracking Bayes and emitting a constant. The readers failed
  anyway (0.48 and 0.29 on two domains), which is unambiguous, but the design would have
  hidden a false pass. Check the truth marginal inside every gate band before the run,
  the sibling of the known-answer existence check. (L209/L229, s3_run_c.py)

- **A realization filter that keeps a minority of the sample is a selection on the
  outcome side; report the kept fraction beside the effect and treat the cell as a
  different population.** The OLMo bottleneck realized 35 percent of regenerations (the
  SmolLM eraser realized 64) and the surviving 88 read null where 159 had read positive;
  whether the eraser or the survivors' composition removed the effect is undecidable from
  that cell alone. (L180/L225, s3_run_s.py arm s05x3)

- **A pre-declared analysis over a matrix that contains the frozen reserve runs BY
  SIDE, or the reserve stops being a confirmation set.** The three expansion contrasts
  pooled discovery and reserve cases (no fitting, so no leak, but no split either), and
  the split-half rerun had to be built afterwards to show each side alone. Any analysis
  arm that reads the reader matrix takes the side as an argument from the start.
  (L217-L219 and L235, s3_run_x.py)

- **Aggregation over a reader matrix is order-invariant and gives every eligible reader
  its declared weight; a dictionary keyed by artifact keeps whichever reader loaded
  last.** The S-trunk own-family side was such a dictionary at four sites, so each
  artifact's own margin was one arbitrary same-family reader against the mean of all
  other-family readers. The headline survived the correction (all three families at
  p = 5e-5) but Qwen's magnitude fell a fifth and the reserve's SmolLM verdict flipped
  from weak to confirmed. Found by the Stage-4 handoff audit, verified by recomputation;
  the S05 bottleneck arms carry the same code and are owed the same recompute. (L236,
  s3_run_s.py; the Stage-4 contract's verification item 5)
- **A paired contrast on raw per-item correctness is not the balanced-accuracy estimand it
  was frozen as; under a skewed truth marginal the two can land on opposite sides of the
  threshold.** P01's first landing paired raw correctness (+0.08, a support candidate) on
  a split where one quadrant held 60 percent of the drawings; on the frozen balanced
  estimand (per-item correctness reweighted by label share) the same rows read +0.04 with
  the interval crossing zero. Pair on the estimand's own per-item quantity. (L237)
- **The per-item best of several comparators is an oracle over comparators, not the
  comparator the card names.** P02's first landing subtracted, per drawing, whichever of
  two geometry rules happened to be right, and read +0.05 against the single rule's +0.20;
  the single comparator is chosen on the training split and the per-item best is kept as
  the severe form. (L238)
- **Count a construction's identity space against its unit count before the run, per
  domain and per split, and let the unit be the construction, not the id.** A constructor
  that drew its rule family from a four-deep pool and ignored its domain rendered 128
  lesson worlds as 54 distinct texts and its 256 confirmation worlds as twins of discovery
  worlds; with greedy readers and deterministic readouts a twin adds no information, so the
  cluster bootstrap resampled 128 units that were 54 and the interval was too narrow by
  the square root of the ratio. The fix is structural: enumerate the identity (a seeded
  permutation of the space, split blocks disjoint, over-allocation raising), hash every
  construction's content onto its lineage, cluster every interval on the hash, and audit
  the whole ledger by rebuilding from ids before the clock starts. And the reason it was
  missed is the recurring one: the duplicate-content control existed and was never called,
  so it returned no duplicates over a ledger it had never looked at, a criterion that
  could not fire wearing the face of a clean result. A control reports what it checked
  beside what it found. (L244 correction, TODO R7; s4_worlds.py, s4_run_common.py,
  tools/s4_construction_audit.py, 2026-08-28)
- **A primary frozen against a matched-cost comparator must also be read against the plain
  route, or a mechanism that only hurts less than its comparator reads as support.** T02's
  source-reconstruction route beat its equally expensive factual-summary route by 0.62 nats
  and landed SUPPORT_CANDIDATE on the frozen band, while both routes lost to the direct read
  (reconstruction by a quarter of a nat, the summary by up to a nat) and the readers never
  inferred the rule at all; the card had frozen the comparator to match cost, which is right,
  and had no clause requiring the treated route to clear the untreated one, which is the
  hole. Every route contrast carries the plain-route row beside the matched one, and the
  roll-up class is read off both. (L245, s4_run_t.py)
- **Steering with the true class's direction is an oracle intervention; the causal-use claim
  lives in the controls, never in the congruent arm alone.** Adding the held-out maker's true
  tendency direction raised the reader's log score on that tendency by up to 0.8 nats, which
  on its own says only that the label's direction moves the label; the claim that the
  representation is USED is the difference between that and a norm-matched random direction
  (quiet) and the wrong tendency's direction (quiet or negative), plus the decode of the same
  directions reported beside it. Write the selective signature as the primary and the
  congruent arm as one of its three legs. (L255, s3_run_a.py arm a07b)
- **An exact ruler is validated on the construction it rules, before the clock: print one
  world per class and read the numbers.** The Stage-5 learning-progress ruler read zero on
  every foraging item because every generator was pinned by the four shown elements (no
  ambiguity, no progress), and the joint world's goal latent carried the LOWEST posterior mass
  after all routes because its bonus was too weak against the profile and a quarter of notes
  lied; both were invisible to the self-tests (which checked sums and ranges) and obvious in a
  ten-line print of one assembled case. A sweep over the construction constant, read against
  the latent it must leave live, is the gate: goal 0.82 and preference 0.64 at 1.0, the
  preference drowned at 1.5. (Stage-5 inspection, 2026-08-29)
- **A counterfactual question must be counterfactual in every cell.** "What would the source
  do after counterevidence?" was asked with a survey that CONFIRMED the claim on half the
  worlds, so the willingness-to-correct latent had no test there. Read the question's
  premise against every factor level, not the modal one. (Stage-5 inspection, 2026-08-29)
- **An instrument gate carries its band's definition, not only its number.** The Stage-4
  position swing was an accuracy difference between two orderings; rebuilt as a per-item
  probability wobble under the same 0.10 it failed every reader (0.13 to 0.19), which would
  have closed the model tracks on a stricter statistic wearing the old band's name. (Stage-5
  smoke, 2026-08-29)
- **A quiet control in one run licenses nothing until its replicate is quiet too, and the
  specificity battery runs before the word 'selective' is written.** L255's random direction
  was quiet by fold (−0.09, +0.04) and the entry called the effect selective causal use; the
  same construction's battery found a random direction at +0.40 and every coordinate and
  label control as loud as the true direction (L260). A control with one realization per
  artifact and no second seed is one draw, and 'random quiet' was the whole claim. (Stage 5
  B03, 2026-08-29) **Resolved the same day: the loud controls were order noise**, see next.
- **A paired contrast on the letter-likelihood readout must ask every arm under the same
  option order.** The readout scores the same answer two nats apart by the letter the truth
  sits under (A −2.71, B −0.75 in the zero arm); the bridge cards drew a fresh order per arm
  from one shared generator, so each paired difference carried two nats of order noise and
  a 135-item mean a standard error of 0.17, which produced a +0.40 random arm in one run and
  0.00 in the next on identical seeds. With the order fixed per artifact across arms the
  random arm is 0.00 and the selective signature is clean (L283). Hold the nuisance fixed
  across arms, or average it with enough draws, and say which. (Stage 5 post-run,
  2026-08-29)
- **A mean per-token log probability is not an ease ruler: padding a text with predictable
  tokens raises it.** The Stage-5 ease manipulation was checked on that ruler and every degraded
  rendering, capitals and a mid-dot after every word included, scored as easier than the plain
  record (L301), so the manipulation could never register. The known-answer renderings were the
  test the ruler failed; run them on any ease or fluency measure before a card depends on it.
  (Stage 5R, 2026-08-29)
- **A lesson re-read is not a lesson applied: check each readout's candidate set against
  §3's short-candidates rule at build time, by name.** The Stage-5 future-choice question was
  built the day after §3 was re-read with the option sentences as its candidates; the reader
  answered from their wording in seven of ten worlds, the oracle variant included, and 30
  GPU-minutes of a six-variant comparison measured nothing (L263). The known-answer probe
  that caught it (the oracle variant against the uniform floor and the exact ceiling) costs
  under a minute and belongs in the pre-run inspection of every choice readout. (Stage 5
  J02, 2026-08-29)

- **A harder rendering is also an anomalous one, and a menu whose options differ in surface form
  carries an attraction bias before any content is read.** With ease crossed inside a route type, both
  readers took the mid-dotted description a quarter more often than the plain one beside it, the
  larger reader four times more strongly; the fluency policy predicted the reverse (L311), and the
  same direction showed on a reliance question (capitals trusted slightly more, L314). Any forced
  choice whose options differ in length, case, or punctuation is confounded by this bias; match the
  options' surface form, or measure the bias with a content-free cell, before reading a preference.
  And ease is a total, not a rate: the mean per-token log probability inverts every known-answer
  rendering while the total and the token count pass all of them (L310). (2026-08-30)
  **Resolved 2026-09-01 (L327): difficulty itself is the attractor.** An archaic rendering,
  harder by the validated ruler and not visually deviant, is taken more by the same quarter of
  probability; matching case and punctuation does not remove the bias — match the options'
  ruler-measured hardness, or measure the bias with a content-free cell.
- **A distinctness gate on candidate hypotheses is sized by identifiability at the observation
  count, never by a nominal epsilon.** Eight candidate attention schedules passed a 0.05-TV
  pairwise policy gate and were still inseparable from sixty choices (sanity recovery 0.25
  against a 0.95 bar, twice); the gate a known-answer arm needs is derived from n, since at
  sixty draws a 0.05 TV is noise, and the sanity arm runs on gated worlds under the same
  constants as the main loop. (L329, runners/s6_consolidation.py, 2026-09-01)

## §4. Before the model arm

- **Base language models below the low billions cannot satisfy multi-constraint generation;
  plan maker matrices around instruction-capable checkpoints or budget for retirement.** Two
  base Pythia makers landed 17 and 28 percent accept-time compliance on a four-constraint
  task (mention A before B, avoid C and D, length band) where same-size base Qwen landed 94
  to 98 — the difference is the pretraining mix, not scale alone, and one predeclared repair
  (better example, more attempts) bought only ~20 points. A yield-gated corpus with a
  retirement clause survives this; a corpus without one ships thin cells. (L163, G172 corpus)

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

- **A cell's status belongs to its runner once the runner might have run.** A batch flipping
  Stage-3 cells PLANNED→BUILT clobbered a LANDED status that a background run had set minutes
  earlier (H05, 2026-08-24; caught because the validator's valid-attempt count came up one
  short). Flip to BUILT in the same edit that writes the runner, before it is queued or run,
  and never touch a cell's status in later batches — landings write their own.
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
- **Killing a GPU stage by pid orphans its lock: release `results/.gpu.lock` in the same
  action, after verifying no compute process survives.** A mid-run stage killed to pick up
  a code repair left its lock holding the dead pid; with the staleness window deliberately
  at 22 hours, every later GPU stage spun on "lock held" for six hours until the wake
  watcher's deadline fallback surfaced it. The kill checklist is now: Stop-Process, confirm
  via nvidia-smi that nothing holds the card, delete the lock. The deadline fallback on
  watchers is what bounded the loss — never arm a change-only watcher without one.
  (2026-08-22, g172_corpus repair pass)

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
- **Useless compute stops the moment it is known useless, before the cell finishes; repair,
  then the real run** (his ruling, 2026-08-28). A cell 94 minutes into a two-hour run on
  worlds a repair would rebuild was killed rather than allowed to land, because a landed
  result that must be superseded costs a reset and a correction on top of the compute; the
  scheduler's `reset` op preserves the first attempt and re-plans the cell so the stop is
  cheap. Corollary for tools that take a root argument: every side effect, the log included,
  goes to that root, or a guard test writes a line into the live run's log (it did).
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
- **Process-pattern checks are repo-scoped by path, never by runner naming convention
  alone.** The drain check matched any python whose command line contained
  runners\run_, which a sibling project's runner (ghost-scale-sim run_v13.py) satisfied,
  so the until-empty waiter held for good after the queue had drained. Match the
  repository path first. (2026-08-27, queue_drain_check.ps1)
- **Every gate-bearing runner runs end to end on a scratch root at a few units per cell
  before the contract clock starts; unit tests cannot see a construction that is empty,
  a gate that measures the wrong thing, or a formula with the wrong sign.** The Stage-4
  smoke (three units per cell, an environment-variable root) found nine defects across
  fourteen runners after all eleven verification guards had passed: an empty gate
  battery, a reader gate that would have failed every reader on the science instead of
  the instrument, a dose ladder without its controls in the loop, a negative 'expected
  gain', a four-letter label alphabet under a five-option question, a raster that did not
  divide its canvas, a parser that rejected the makers' actual output shapes, a freeze
  step no loop could start, and unmapped control cells in the validator. Each cost
  minutes on the smoke and would have cost the window. (2026-08-27, Stage-4 build)
- **A card-by-card smoke proves the code runs; it does not prove the construction asks
  the question. A manual read-through of every runner against the brief, before the
  clock, is its own step.** The Stage-4 validation pass (his order, after the smoke ran
  clean) found twenty-one defects the smoke could not see: known answers that did not
  exist (a target choice drawn from a hash), factors that were not realized (benefit and
  induce messages identical in half the worlds), controls that were not what they
  claimed (an 'exact collision' with different draws; a technique cue that was a string
  match for falsity), estimands that were not the estimand (raw accuracy where a
  constant answer passes; an interaction carrying a main effect through a sign
  imbalance; a realized gain moved by restatement), routes that did not see the same
  observations, and a scheduler loop that had never been run at all. Every one is a
  class already on this shelf; the smoke passed them because a smoke checks yield, not
  meaning. (2026-08-27, Stage-4 validation pass)
- **A loop that has only ever driven cards by hand has not been smoked; drive the loop
  itself on the scratch root, closure block and packet included, under a compressed
  window.** The Stage-4 scheduler's first real iteration would have crashed on a
  constant read from the wrong module, and its pilot cell would have failed three times
  on a produce path no runner wrote; both surfaced in the first second of the loop
  smoke, after fourteen runners had each passed their own. The same smoke's receipts
  showed the loop reading a frozen design it never saw: it held the contract object it
  loaded at start-up while the freeze subprocess wrote the design to disk, so deferred
  cards ran and no expansion was admitted, and its first lost-time record would have
  written the stale object back over the freeze. **A record that several processes
  write is reloaded before every decision and before every save; an object loaded once
  is a snapshot, not the record.** (2026-08-27)
- **On Windows an atomic replace fails with a sharing violation while any other process
  holds the target open for reading; every shared JSON writer retries the replace.** The
  live Stage-4 freeze died on its first attempt while a CPU card was loading the lineage
  file it was rewriting; the cell-level retry carried it, and the writer now retries for
  five seconds before raising. (2026-08-27, soundingline/s4.py write_json)
- **A stage whose produce can never appear leaves the stage list the moment its cell
  resolves; a queue-empty test counts it forever.** The M02 interchange exited cleanly
  without a produce every pass after its gate failed, and any emptiness test over
  produces would never have reached zero. Resolved cells retire their stages in the same
  pass, a tombstone comment keeping the history. (2026-08-27, run_queue.py)
