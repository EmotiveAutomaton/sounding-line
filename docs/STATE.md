# STATE: the agent's operational file

> ## ⚠ IF YOU HAVE JUST BEEN COMPACTED: RELOAD THE THEORY FIRST
>
> Before any research, any literature reading, or any judgement about a result:
> **read the whole of `docs/theory/`, newest first, then `FINDINGS.md`, then this file.** A
> compaction preserves what happened and loses the framework's shape, which is exactly the state
> in which confident literature overwrites it. That has happened twice. See `CLAUDE.md`, first
> section. Then read `docs/method/LESSONS.md`'s trigger index before designing or building
> anything.

**Rewritten 2026-08-14 immediately before an expected compaction; consolidated 2026-08-16 at
the curator's direction for the Phase-1 wrap (the distilled-chronology section is the load-
bearing addition — it exists because interim summaries kept outliving their corrections).**
Everything below is current.

## ⚠ HARD CONSTRAINTS AND STANDING RULINGS, SET BY THE CURATOR

1. **SUBAGENTS ONLY WHEN HE ASKS.** He asks → spawn (recent asks have been Opus referees and a
   nine-agent consensus fleet, all his explicit orders); "ultracode" → Workflow tool; otherwise
   inline. The consensus-ballot form (fixed claims, dual coverage, capped findings channel) is
   the preferred fleet shape — he ordered it because open-ended agents each returned a new path.
2. **AUTHOR CONTACT IS OFF THE TABLE (2026-08-14).** Never suggest contacting a paper's authors
   for any purpose — not for irreproducibility, not for corpora. Irreproducibility wording
   stands on exhausted-public-routes evidence alone. This ruling is also in LESSONS §1c.
3. **The recreation pass standard (his ruling, 08-10):** a recreation passes only by reproducing
   published exact values; a large shortfall is a defect in our model of their pipeline, hunted
   not caveated. Refined by the referee arc: verdicts on fine-tune arms need the three-seed
   interval (§1c), faithful means the training framework not the printed hyperparameters (§1b),
   and underdetermined protocols report the specification curve.
4. **Token posture:** he opens budget explicitly when he wants fleets; otherwise dense and
   inline. Model is Fable at max effort.
5. **Gears, not day/night (renamed 2026-08-12).** First gear = his machine (serial, GPU mostly
   his); second gear = everything, loaded about a day deep, ONLY on his call, sized to his
   stated window. A deadline exit is a wake-and-decide event.
6. **GEAR 3 (cloud burst, Modal) IS STONE (his ruling 2026-08-16): it NEVER runs without his
   explicit per-use approval, and no more than $10 may ever run without a fresh detailed
   final-approval request to him (exact commands, durations, test details, total dollars) —
   both enforced in code by `runners/gear3.py` (refusal paths, the ledger at
   `results/gear3_ledger.json`), never by memory. Gear 3 is for RARE bursts; recreation-gate
   arms stay local (hardware/precision drift). The Modal token lives in `~/.modal.toml`,
   outside the repo, and was pasted in-chat 2026-08-16 — rotation owed on his side.**
7. **ALL MATERIAL SPEND IS GATED BEHIND POSITIVE RESULTS (his ruling 2026-08-16).** The $120
   pilot generation envelope is NOT APPROVED, and no comparable dollar amount will be, unless
   prior free-path results make an unequivocally positive outcome close to certain. His words:
   *"I would like to have that monetary cost be gated behind explicit positive results that
   strongly imply that we're going to find exactly what we want... I'm not willing to spend
   any amount twice at this point... These dollar amounts are far too large. This is a home
   project."* Consequence: the Phase 2.0 slice proceeds on the free path (local generation,
   held corpora, CPU/local-GPU analysis); frontier-API acquisition unlocks only after (a) the
   decision reader passes its known-answer gates AND (b) the stack shows held-out lift on the
   local-family benchmark, so spend buys generalization evidence, never discovery. **Research
   grant applications are likewise REJECTED as premature** — no initial results justify them,
   they slow us down, and actual research funding "would require a different conversation
   entirely." Do not re-raise either without new positive results in hand.

## The priority ladder, his words, in order

1. **`docs/theory/` files (not `essays/`) perfectly interpretable at a glance and very clean.**
   His quotations are the most valuable information in the project.
2. **The model and all the tests** (the record's integrity; the referee arc is this item).
3. **Minor errors**, prioritised at my discretion.

## The five-file contract and style rules (unchanged, binding)

    THE_TRIPLE_INFERENCE     what is inferred; dependencies among targets; identifiability
    THREE_COGNITIVE_LAYERS   what architecture might support the inference
    DECISION_TRACES          what observable traces the maker's decisions leave
    READER_HEURISTICS        how a bounded reader finds, combines, and calibrates those traces
    ALIGNMENT                what objective should govern a system after it can read them

Blockquotes are the curator's words only; his blockquotes are untouchable; structural changes
are proposals in chat first. No em/en dashes in prose in curated markdown; colons only in
headers and labels; no "it's not A, it's B" constructions. Reserved vocabulary: functional
level / region / block / subspace; "layer" unqualified is banned. Format spec and afterword
rules in `docs/theory/README.md`; the linter enforces the mechanical half.

## Where the program stands (2026-08-17)

**Phase 1 (frontier recreations) is at wrap: three anchors closed, BST's Experiment 1
complete with Experiments 2-3 open behind their stimulus decodes, PAN's tail (wqd test
gates, ernie head-scope, vote, the deberta stabilizer ladder) in the machine. Phase 2 is
OPEN and its first result is in: the detector-layering A/B ran on gear 3 and returned a
NULL under its preregistered rule (L125) — the channels lose to the substrate at naive
late-fusion (means 0.8278 vs 0.8343), with the channels-alone reference at 0.6283 and the
next designs filed (more seeds, earlier fusion, the document-grain task). Gear 3 itself is
VALIDATED and live-fired (L124/L125), stone rules enforced in code.** The
scorecard, settled by two adversarial Opus referees, a nine-agent consensus fleet, and an
eight-agent external-verification fleet (L107, L108, L109, L123):

- **Armstrong–Mindermann**: PASSED exactly (analytic 0.5/0.5), extended (bounded family 20×,
  both priors 40×).
- **ScholaWrite: CLOSED (L117), the F1 headline REPRODUCED on the seed interval.** The
  framework-faithful three-seed interval [0.639, 0.660] contains the printed 0.64; seed 44
  finals on it to the third decimal; all four trajectories (both architectures) cross it
  mid-training, so the identical 0.64/0.64 print reads as one pipeline at unstated stopping
  points. The paper's internal inconsistency (its own table implies 0.59, accuracy 0.56)
  stands as a literature fact, explicable as different checkpoints of the same pipeline.
  Accuracy residue recorded (ours 0.61-0.63 vs their 0.56). Tag typo inert; 0.741 is the
  non-faithful recipe.
- **ArgRewrite: FULLY SETTLED (L115), nothing left to run.** Composition exact (3,236/3,238);
  binary Majority to the digit; the printed Majority rows mutually incompatible (fleet's
  strengthening); the oversampling claim inference only; faithful Features .883 vs .90; the
  embedding rows TERMINALLY CLOSED as not reproduced from the released materials — grid-max
  refuted (fixed config ranks 15/26 of 36) and the four-block encoding refuted (+1 point,
  still 3-4 short), every public route measured, gap bounded.
- **PAN 2024**: two members above their validation gates under the corrected recipe
  (ernie 0.8798, roberta 0.8558), but all validation numbers (theirs and ours) blend ~16%
  cross-year memorization. **The contamination account is CLOSED from three directions
  (L118): rescore 0.8273 / strict tier 0.8235 / retrain-leak-free 0.8108 (−0.032 below the
  winner's own gate) — the recipe's edge IS the leak; capability is 0.81-0.83.** The
  all-module dropout collapse is stochastic (L118 fold to L111). **THE ANCHOR IS CLOSED
  (L133). 2024: all three head-scope members above gate (roberta +0.021, ernie +0.030,
  deberta +0.0045 at seed 43 after the collapse account closed as seed fragility) and the
  VOTE at 0.8799 vs 0.8658 (+0.0141), every validation number still carrying the blended
  leak, honest capability 0.81 to 0.83. PAN 2025: all three test gates REPRODUCED on
  complete seed intervals (easy at one ten-thousandth, medium bracketed, hard at typo
  distance) over contamination-clean data. The wqd recipe is a validated trained substrate
  for the Phase 2.0 detector (2.0E). The recreation scorecard is complete across all five
  anchors; BST Experiments 2 and 3 are the one open extension.**
- **BST**: reference data validated (Exp 1 fully; Exp 2 fully after the fleet found the
  column-major grouping — stimulus i = rows i, i+95, i+190; all sums pass; my earlier
  narrowing was wrong and is reversed). Design corrected by the referees: NINE actions
  including Stay at cost −1, 36 = 4 goal configs × 3 path groups × 3 route conditions, the
  goal prior is a source contradiction (both readings run as arms; it sets K in the γ factor).
  **EXPERIMENT 1 COMPLETE AT EXACT-VALUE GRADE (L119/L120/L122): fourteen printed values
  reproduced at printed precision — the four Fig-5 correlations, the cell-level prediction
  columns (≤0.001 across 297 cells), the goal prior resolved at K=3 (only the cell-level
  gate could tell), the appendix grid maxima with the argmaxes reproducing their best-fit
  parameters model for model, and the Table-1 BSCV at N=10,000. The 99-vs-100
  contradiction is located (ref index 92). Remaining: Exp 2 and Exp 3, each behind its own
  stimulus decode (the L114 machinery).** Old 4-action results archived as
  summary_4action.json.

**Phase 2.0 is GOVERNED (2026-08-16): his handoff brief landed and is archived at
`docs/design/PHASE_2_0_CONTEXT.md`; the live sub-goal map (2.0A to 2.0H, identifiers G152 to
G157 plus the absorbed G129/G130/G131/G149) is the Phase 2.0 section of `TODO.md`.** The
mission: a deployable binary AI-provenance classifier whose differentiating contribution is
recoverable decision structure, one vertical slice from benchmark through release, with the
decision representation validated on known answers BEFORE any fusion and the curator
interface running at theory-group level (roll-ups: Strengthens | Narrows | Kills |
Infrastructure — the contract is folded into `CLAUDE.md` and the grind skill). **2.0D STATUS RECLASSIFIED
(2026-08-19, curator-ratified after an external read-only audit he commissioned): the G129
battery stands as STRONG REPLICATION, not confirmatory grade — recovery replicates (0.4854
vs the 0.25 analytic floor), the balanced matched margin survives at 16.5 points at the
pilot evidence tier (n 176 of the powered 283, the card's own downgrade clause now
applied), fabrication is 0.000 on no-op deltas, and the 19-dim change block beats the
zero-shot reader head to head. But the shuffle gate fired VOID under the card's own terms
(0.110 vs a misspecified 0.25 expectation; the corrected label-marginal expectation ~0.125
was derived after seeing the result, so it repairs the next card, not this run's grade).
Confirmatory grade requires the fresh G129b battery. **CURED SAME WEEK (L141, 2026-08-19
afternoon): G129b ran with every gate carrying both expectations and a direction from
freeze, all gates landed quiet (shuffle 0.1136 beside its frozen 0.125 alternative
expectation), recovery replicated seed-stable (0.4805), fabrication 0.000 again, the
change block beat the reader a second time — confirmatory grade EARNED and the 2.0D
real-text gate is formally MET, scope one corpus one reader family, matched arm at its
pre-committed pilot tier (200 of 283 after the one specified caliper relaxation).**

**Phase 2.1 is DECLARED (2026-08-19, his naming): the repair-and-foraging phase between
the 2.0D evidence and any stacking. Sub-items 2.1.1 to 2.1.6 in `TODO.md`: reclassification
(landed), the inference-input interface freeze in the evaluation contract, the G131
epistemic-foraging battery (G158 — the corpus is reclassified EXPLORATORY: ~36% of
mechanically checkable assigned instructions were not executed, so assigned-instruction
ground truth is invalid for a known-answer test until realization is adjudicated), the
G129b fresh confirmatory, the decisive G131 rebuild on paired base material, and the
benchmark human-negative repair. Stacking (2.0F) re-gates behind the four Phase 2.1
decision gates now written into the contract. The free-path pilot corpus (240
process-recorded artifacts, two local lineages) remains complete at zero dollars.**

**Phase 2.1 execution status (2026-08-19, same day):** the foraging battery's first
stages landed and cut deep — checkable realization 0.586 (L138), cheap features read the
factorial target axis at 0.95 (L138), and the reader adjudicator FAILED its validation
(L139: over-credit 0.688 on exact-grade rows; a yes-machine in verification format,
honest in forced choice — realization ground truth is mechanical-only). Stage (c)
recovery runs on the mechanical exact-grade subset with verified-unsatisfied decoys.
`prereg/g129b.py` is frozen with directional gates carrying both expectations; its
manifest's pre-committed caliper relaxation fired (matched 200 of the powered 283), so
H-B runs at the pilot tier declared BEFORE any arm ran. **Both batteries LANDED same day:
G129b all-gates-quiet, confirmatory EARNED (L141). Stage (c) split (L140): the reader is
chance on mechanically verified surface constraints once truth-balanced (word-echo beats
it, 0.375 vs 0.25) but clears the problem-pool echo bar by 11 points in BOTH families
(0.909 vs 0.798) — a transferring margin the exploratory corpus cannot split into
executed choices versus assignment-vocabulary leak. Stacking gate 1 (realized
problem-directed recovery, artifact-only) is unmeasurable until the 2.1.5 rebuild;
gates 2/4 behave; gate 3 is the open contest. The rebuild's design constraints are now
measured: echo equalized by construction, consequence-matched decoys, mechanical scoring
for formal constraints, forced-choice-with-none formats only (L139/L140).**

**The artifact-side science meanwhile (the movement family, settled at four generator
families):** rising positional polish is the machine default (3 of 4 base × post-training
cells, window-robust in the llama cells), the lone human-direction decay is one model at one
window, the magnitude square is window-conditional (the wide-window post-training alignment
scrambled at 40 words, L116), and the one constant across instruments and windows is
qwen-instruct — mobile on the artifact side at both windows AND the reader-side instrument's
lone mobile family, so the dissociated instruments reconverge on that single model (G146's
re-aimed question). The scaffolding instrument measures prompt burden not provenance, and
the no-maker control is clean at n=108 with the reader family-neutral (weakness 6's
load-bearing cell closed, weakness 4 narrowed). The maker-signature results (PD-33 family)
stand untouched. Function words carry state at the pre-registered bar (PD-11 at power) and
survive the fair induction control on the two strong ladders (G76/L94).

## Queue / infrastructure state

- **Two infra defects found and structurally fixed 2026-08-19 (LESSONS §5, both):** the GPU
  lock self-deadlocked a runner that acquired per arm (five hours of a live window; the lock
  is now reentrant by pid and runners acquire once per invocation), and shard ownership by
  list index re-owned stages when the list changed under a live lineage (a blocked stage
  launched under two owners; ownership now digests the stage name). No data lost either time:
  checkpoints carried every resume.
- **Engines:** first gear `run_first_gear.sh` (serial), second gear `run_second_gear.sh
  [hours] [workers]` (sharded; locks `.gear1.lock`/`.gear2.lock`, winpid line 2; legacy lock
  paths still checked). Kill by winpid tree; sweep orphans; standalone GPU arms need queue
  membership, checkpoint-resume, or the sweep keep-list. The queue asserts produces-path
  uniqueness at load; a clean exit with no produce records FAILED.
- **In flight (2026-08-17 evening, after the circuit-breaker outage):** a power loss killed
  the whole machine mid-day. Recovery audit found NO unrecorded findings (every result file
  newer than the last write-through was already in the record; the one arm running at the
  cut was still in its lock-wait loop with zero events processed). Compute lost: the deberta
  s43 stabilizer rung died at epoch 7 of 10, ~17 hours in, training healthily (loss 0.000),
  and restarts from zero because the training runners have no mid-run checkpoint-resume
  (build now owed, TODO infra row; the orphan-sweep lesson's protection list has its first
  outage receipt). Stale gpu/gear locks cleared. **FIRST GEAR is running (his call): all
  pending GPU stages held for second gear** — the deberta restart, wqd medium + six
  seed-interval arms, the G129 reader arms, both G153 generation arms — and the G129
  verdict defers on its arms. The GPU lock's staleness window is 22h (raised 2026-08-17
  after a live 620-minute rung was reclaimed at hour nine); the regear waiter cancels by
  FILE (`results/.regear.cancel`), never by pid.
- **The audit-history index:** L26 (the first fleet), L61 (recreation re-audit), L93 (the
  methods pass), L107/L108 (the two referees), L109 (the consensus fleet), L123 (the external
  verification fleet). The old solo-audit scope table this file used to carry is superseded by
  that chain.

## THE PHASE-1 CHRONOLOGY, DISTILLED — read before believing any summary of Phase 1

Compactions preserve summaries, and several interim summaries of this phase were later walked
back by our own audits. This section exists so a future context lands on the END STATES and
cannot resurrect a dead interim claim. Per anchor: the final verdict, then the claims that
died on the way and must stay dead.

- **Armstrong–Mindermann.** Final: PASSED exactly, extended (bounded family 20×, both priors
  40×). Never swung, and carried ZERO internal contradictions — never lump it into the
  contradiction tally (L123 corrected the loose "all five papers" phrasing; the true tally is
  four of five works, matching meta-research base rates).
- **ScholaWrite.** Final (L117): the printed F1 headline is REPRODUCED — inside the
  three-seed framework interval, one seed on it to the third decimal, every trajectory
  crossing it on both architectures. The paper stays internally inconsistent (its own table
  implies 0.59, accuracy 0.56), explicable as one pipeline read at different checkpoints; the
  shipped split leaks by construction; the accuracy residue is open. DEAD, do not resurrect:
  "0.64 is stale/unreachable" (the 08-11/08-12 closed-as-correction story — reversed when the
  framework arms landed); "flawlessly matched" (never true at any point); 0.741 as anything
  but the non-faithful recipe.
- **ArgRewrite.** Final (L115/L123): composition exact (3,236/3,238); binary Majority to the
  digit; faithful Features .883 vs .90; the embedding rows not reproduced from public
  materials with the gap bounded at 3-4 points AND the surviving candidates named (search
  optimism past their grid; an unstated vector combination — "nothing left WE can run," never
  "nothing left to run"); the fine half rests on the independently confirmed Table-4
  contradiction, with the augmentation story held as inference-with-counter-evidence. DEAD,
  do not resurrect: ".895 Features reproduced" (it carried our change block); "fine half
  closed, composition demonstrated in-pipeline" (downgraded by L107); L109's "Majority rows
  mutually incompatible independent of Table 4" (downgraded by L123 — a second derivation
  could not reconstruct it).
- **PAN.** Final: the metric is POOLED two-class macro-F1 (evaluator read verbatim in all
  three years, twice-derived, no reconciling reading); the contamination account is closed
  three ways with honest capability 0.81-0.83; members reproduce above validation gates under
  the head-scope one-recipe set; the 2025 labeled test split is genuine and its three printed
  test values are the phase's exact-value crown. DEAD: "nothing here has the inflation
  signature" (L104, falsified by L106); "their run cannot have been all-module dropout"
  (downgraded to knife-edge instability by L118).
- **BST.** Final (L119/L120/L122): Experiment 1 complete at exact-value grade — fourteen
  printed values at printed precision, the sweep re-deriving their best-fit parameters, the
  goal prior resolved at K=3 by the cell-level gate, the 99-stimulus set decoded label-perfect
  (L114). Experiments 2 and 3 open behind their own stimulus decodes. DEAD: the 4-action
  hard-max engine (the paper's Eq. 4 is the SOFT Bellman fixed point); my Exp-2 reference
  narrowing (reversed by L109 — column-major grouping validates the file); "text says 99,
  caption says 100" (both say 99; the 100th datum exists only in the plotted vector content).
- **The shape to internalize:** every one of those dead claims was retired by the audit chain
  above, not by outside correction — and each was, for a time, the confident summary a
  compacted context would have inherited. The standing conclusions live in the TODO Phase-1
  rows and FINDINGS end-states as folded; an interim summary, including one written by a
  previous self in chat, is evidence of what was believed, never of what is true.

## Open decisions / owed

- **His:** the Phase-1 final assessment when the queue lands + BST rebuild finishes; the
  Phase-2 go; interest ratings (HH-14, informs READER_HEURISTICS only); PAN22 Aston access;
  rotate the early-project API key.
- **Mine, in order:** the 9-action BST rebuild (decode gate passed L114; the phase's last
  open implementation); write-throughs as tonight's arms land (head-scope members, vote,
  deberta, three wqd test gates, batch-8); then the owed CPU builds (G130c floor
  decomposition, G94 Taramsa, G97 maker-as-random-effect, the specification-percentile
  function).
- **The one-maker-many-kinds corpus problem** stands (CROSSNEWS pseudo-documents only;
  Guardian small; CMCC request-only); the program's G133 commissioned pilot leads this thread.
