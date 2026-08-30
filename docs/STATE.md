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
   his); second gear = everything, loaded about a day deep, ONLY on his call, **and with no
   time window: it runs until the queue is empty (his standing ruling, 2026-08-28). A stated
   hours argument is an optional cap, never a default; a Stage contract's deadline is
   accounting, not a stop.** The engine exiting is a wake-and-decide event.
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

## PHASE 2.4 GOVERNS (ratified 2026-08-22, continuous second gear authorized)

**Shared-architecture inversion and affective-prior engineering.** Briefs at
`docs/design/PHASE_2_4_CONTEXT.md` + `_EXPLORATION_ADDENDUM.md`; live registry
`docs/design/PHASE_2_4_REGISTRY.md` (which also carries the Phase 2.3 closure
dispositions — the ratification closed the 2.3 Stage-1 gate; the audit-interface
product is DEFERRED, not dropped). The Phase 2.4 theory errata is applied
(`docs/design/PHASE_2_4_THEORY_ERRATA.md`): invertibility is reader-qualified three
ways (model / engineered human-shaped / human), similarity is a shortcut not a proof,
27 is a soft ceiling never a count. Two lanes: confirmatory trunk G172-G180 (only
route to verdicts, cards frozen before scoring) and the quarantined E24 discovery
forest (five status words, data firewall, automatic closure rules). **STAGE 1 COMPLETE
in one day (2026-08-22, L161-L163) and the COLD ROOT MAP IS FROZEN**
(`docs/design/PHASE_2_4_ROOT_MAP.md`, written before any scout output): G172
SIMILARITY-GRADED (exact +0.035 and sibling +0.025 margin units over cross-family
readers, both at the permutation floor, capacity failing inside the battery; Pythia
makers retired by the card's second-failure clause, single-maker-family limitation
recorded); G174 INSTRUMENT-FAIL (dev-power block selection flipped between seeds, one
degenerate input-edge selection lesioned the model 2.55x; an emotion-word-free decoding
grain survived above every control at the functioning seed; predeclared repair declined
with reasoning); G177 COMPLETE (anchor READS 0.78 vs 0.25 through the non-generative
reader; ScholaWrite prospective floors 0.04-0.08 mapped LOPO; reader arm unvalidated at
an unpowered gate; CoAuthor imported, 1447 sessions). **STAGE 2 RATIFIED 2026-08-23** (brief `docs/design/PHASE_2_4_STAGE_2_CONTEXT.md`, its
theory errata applied same day; three waves, six-queue-day arc, daily cold maps at
`docs/design/PHASE_2_4_DAILY_MAPS.md`, pursuit and warrant ledgers separate; the
SmolLM2-instruct pair added as the non-Qwen instruct family). **DAY-2 STATE
(2026-08-24 early), findings L161-L170:** Tree S holds the CROSSED REVERSAL (each maker
family's artifacts read best by its own relatives, surviving mechanical normalization,
cross-family erasure, and the mirror arm — the advantage follows the original maker, and
it dies at literal instruction wording, so it is not surface-shaped) plus the
twice-measured geometry correlate (alignment predicts who-inverts-whom at 0.50
process-matched and 0.77 neutral, double-centered), with the causal transfer branch
CLOSED (generic-steering signature, one direction unmappable). Tree A CLOSED at the
tested scale with the representation retained: readable at twice chance without emotion
words at one unanimous consensus block, causally inert under every tolerated dose. Tree
P v1 CLOSED at its resolution boundary (assigned preferences refusable, appetites
converge, item-attractiveness rival recorded). Tree H holds the retention substrate
(11,773 decidable accepted suggestions, 68.7 percent verbatim survival) and the SCOPED
prospective boundary (prompted and likelihood readers fail where trained encoders
demonstrably succeed). The spine is guard-tested and field-validated; scale limitations
(12GB, 0.35B-3B) recorded in every finding that inherits them; his walkthrough is the
gate on every promotion and successor construction.

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
`docs/design/archive/PHASE_2_0_CONTEXT.md`; the live sub-goal map (2.0A to 2.0H, identifiers G152 to
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

**Phase 2.2 is GOVERNED (2026-08-19 evening: his second handoff brief, archived at
`docs/design/archive/PHASE_2_2_CONTEXT.md`; sub-goal map 2.2A to 2.2G with identifiers G159 to
G164 in `TODO.md`).** The pivot: binary adjudication of who "made the decisions" is
retired as the primitive question — the curator's standing unease about the adjudication
ask, named. The core representation is the trajectory reconstruction profile (brief §9)
over the visual map's nine objects; provenance and reconstruction are separate outputs
forever; the observational-equivalence rule and twelve ruler gates bind every new reader;
"decision weight" is retired as a primitive in favor of five separated quantities
(formation difficulty, trajectory leverage, episode control, trace support, historical
shaping — temporary labels, not canon). Execution order: G159's realized-choice card
first (written to Phase 2.1's question, unreshaped), then schema and interface guards,
then the anomaly-handling ruler in a constructed world BEFORE any natural-text anomaly
battery. 2.0F stacking now sits behind the Phase 2.1 gates AND 2.2G's eligibility ruling.
The adjudication set is unfrozen, superseded as ontology, retained as history. The
curator-first theory loop (brief §13) is folded into `CLAUDE.md`.**

**Phase 2.3 STAGE 1 IS COMPLETE (2026-08-21, one gear-2 day, L151 to L160; the root
map at `docs/design/archive/PHASE_2_3_ROOT_MAP.md` waits on the curator's pass and Stage 2 is
gated on it by the brief's own rule). All seven roots hold states: Wing G CLOSED
(explicit route generation null where reading is strong, HURTS with induced
fabrication where it is weak); Wing B blind-with-residue (the reader abstains on
route identity at 0.07 committed while a five-feature surface baseline reads it at
0.48); Wing A PAUSED (a false production fact steers 95 percent as hard as a true one
where evidence is absent and still wins the toss-up against readable 0.86 evidence,
conflict named 15 percent of the time); Wing C blind at exactly chance under passed
ceilings (ratification is real and invisible; the product is the audit interface);
Wing D POSITIVE (concealed-vs-unnoticed separates at 0.77 at long form against the
0.417 essay-grain reference, at parity with a mechanical hedge counter, zero span
localization, after the corpus refused itself once and the accept-time repair stood
same day); Wing F POSITIVE (the ordered-accident ruler passes both seeds with origin
abstention enforced at zero violations); Wing E NOT RUN, design-blocked by Wing A's
result and put to the curator. The world-model summary: W4 three constructions deep,
W1 alive in the two content channels, W3 confirmed for context, W5 claims the
generation strategy. Content carries; topology does not. The wake watcher entered
service after two verdicts sat unreported (the gear engines are detached; the watcher
is harness-tracked and re-armed each pass).**

**Phase 2.3 is GOVERNED (2026-08-21: his third work package, archived at
`docs/design/archive/PHASE_2_3_CONTEXT.md`, operational registry at
`docs/design/archive/PHASE_2_3_REGISTRY.md`). Seven wing roots, each ending in exactly one
declared outcome state, routing predeclared; the reconciliation against the live head
(the brief predates the 2.2 landings) is the registry's first table. His rulings this
morning: Wing D enters at its predeclared repair (the L150 null's own redesigns), the
brief moved to its canonical home, second gear loaded for the day. Stage 0 landed same
pass: the process-record / contribution-network / anomaly-trajectory schemas with the
curator's §2.1 non-recognition ruling enforced in code (twelve new guard tests pass,
the author-share scalar raises by construction), the reading profile extended with the
§3.4 sections, the G165 reader-ablation card frozen with its pipeline-purity gate
passed, and the G166 route-varied corpus construction queued. Detector stacking stays
prohibited; drives and values stay deferred (brief §2.4). The design folder now carries
an authority index (its README: one OPERATIVE phase, status labels on every file); the
evaluation contract is v0.3 DRAFT DO-NOT-FREEZE with the reconstruction profile as the
primary task and the binary form demoted to the optional downstream product layer. What
survives into 2.3 unchanged: the delta choice-recovery positive (L141), the realized-
choice artifact-only positive (L146/L148), the ruler pass and the text-sampler null
(L127/L134), and the G131/G153 records as process substrate under their documented
limits.**

**Phase 2.2 second wave (2026-08-20 evening, L149/L150): the anomaly-text corpus stood
its self-gate (correction markers 0.75 where instructed, 0.00 where forbidden, clean
uncontaminated) and the reading battery returned the harshest preregistered branch,
cleanly: validation-first PASSES at 0.95 with 0.054 false-yes, and the reader is BLIND
on concealed-vs-unnoticed (0.417 vs 0.5) on BOTH interfaces — an honest instrument
finding no signal at essay grain. Error handling is real in construction (L147) and
unmeasurable in short text at current resolution; redesigns owed are span-level asking,
longer artifacts, audited hedging density. Secondary: deliberate constructions read as
nothing; rewritten clean text pulls 0.30 over-attribution (L146's effect replicated).
First gear from 16:59 on his call; the machine is his.**

**Phase 2.2 first wave (2026-08-20 morning): the anomaly-handling ruler PASSES all six
gates in the constructed world and replicates on fresh seeds (L147) — 2.2C met, 2.2D
licensed, with the six build iterations recorded as design knowledge. The echo
decomposition (L148) then overturned L146's cap: where word overlap points at the wrong
candidate the reader still recovers executed instructions at 0.852 against chance-level
twins — the realized-choice evidence is echo-independent semantic reading, and the
stacking gates stand three-quarters green in exploratory form. Next careful design: the
2.2D process-recorded text corpus (the does-instructed-concealment-actually-conceal
question), deliberately not rushed.**

**PHASE 2.1 CLOSED (2026-08-19 night, L146): the G159 realized-choice battery landed
SUPPORTED under its frozen card — execution effect 0.64 (recovery 0.86 in BOTH families
against 0.22 on uninstructed twins, z = 9.1), every gate quiet in its guarded direction,
and the echo-disclosure rule fired honestly: word overlap alone recovers executed
instructions at 0.73 (execution embeds vocabulary), so the reader's demonstrated
above-trivia margin is 13 points, family-stable. Realization evidence is licensed;
attribution is not; echo shifts from a matching target to a decomposition target in every
Phase 2.2 card. The 2.2 theory errata is applied across all five owners same night
(quotes inserted at their canonical homes, the corporate/machine table rebuilt as
conditional organizations, the calibration rule split, ALIGNMENT's governor and
anti-capture logic repaired, value-similarity trust gating held unresolved in the errata).**

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
- **Agent-loop hardening landed 2026-08-28** (source: the curator's handoff, applied to
  Stage-3-and-earlier code only, with Stage 4 running and untouched throughout).
  **Five defects, all reproduced first, all now covered by `tests/test_agent_hardening.py`:**
  the queue lock was released unconditionally from `main`'s `finally`, so a process REFUSED the
  lock deleted the owner's on its way out (acquisition is now `O_CREAT|O_EXCL`, ownership is
  pid plus process-create-time plus host plus token, release is owner-checked, and unverifiable
  ownership HOLDS the launch instead of clearing it); twenty-one `s3x_` stages escaped the
  no-GPU hold because the prefix list carried `s3_` and `s3x_` does not start with it, plus
  three `activation_variance` stages that default to `--device cuda` (resource is now declared
  per stage by produces-path, so a rename cannot change resource permission, and `gpu_eligible`
  is the one shared check with undeclared meaning held); `s3.set_status` was an unlocked
  load-modify-save with a non-atomic write (now a lock-held transaction plus temp-and-replace,
  and the two are documented as different fixes for different failures); completion was
  `Path.exists()` in both the scheduler skip and the program validator, so a truncated or
  wrong-card produce read as done (now `soundingline/completion.py`, shared by both, validating
  by declared artifact type and keeping execution-resolved, instrument-valid and
  scientific-result separate, so a valid negative completes and a legacy artifact reports
  UNVERIFIABLE rather than being relabelled invalid); and `design_lint` accepted the literal
  string DESIGN CHECK, certifying the presence of two words rather than a design.
- **The linters are now command-line tools, not hook-only** (`tools/lintio.py`,
  `tools/lint_hook.py`, both stdlib-only and resolved from `__file__`, so they work from any
  cwd on any machine). This was found the hard way: two `theory_lint.py` processes had been
  hung since 2026-08-24 16:19 on `json.load(sys.stdin)`, because the script ignored argv
  entirely and someone had reasonably run it with a file path. **A rule enforced only by a
  PostToolUse hook is not enforced at all against a `sed` edit or a runner write.**
  `design_lint --changed` and `theory_lint --all` are the CI-shaped entry points.
  **Still open for the curator: `.claude/settings.json` names machine-specific absolute Windows
  paths for both hooks, and the project's `command`+`args` hook form is unverified on this
  install (the user-level hooks use the single-command form). The portable adapter is written
  and tested; rewiring live hooks was left as his call.**
- **Stage 5R CLOSED 2026-08-29 16:32 (RUN_TO_EMPTY, 1.35 h; launched 15:11 under second gear via
  `run_stage5r.sh`, restarted 15:24 for the source-text repair; root `results/phase_2_4_stage_5r`;
  packet and synthesis at its CURATOR_PACKET_FINAL.md; landings L284 to L308; two confirmations, R02 and
  P02). The wrapper chained into the general queue (two stages: the second family on the second
  domain under fixed order; the design-1-against-design-2 table).**
- **Stage 5 CLOSED 2026-08-29 13:04 (RUN_TO_EMPTY, 1.25 hours; launched 11:49 under second gear via
  `run_stage5.sh`; brief at docs/design/PHASE_2_4_STAGE_5_CONTEXT.md; packet and synthesis at
  results/phase_2_4_stage_5/CURATOR_PACKET_FINAL.md; landings L256 to L281; one confirmation, R02).**
  Post-run receipts reversed the bridge's kill (L283: the loud controls were order noise; with the
  order fixed, L255's selective signature stands on two domains for the anchor). As it ran: the scheduler serializes GPU
  cards through the gpu lock, runs two CPU cards beside them, walks rung 1 of the expansion ladder
  while the accounting clock is under hour 20, runs the two confirmation cards on exhaustion, and
  writes the one packet; the wrapper then chains into the general queue. The reader gate admitted
  Qwen2.5-1.5B only (L256), so the stage is single-reader; the bridge on SmolLM2 failed to replicate
  L255 (L257); on the anchor the effect transferred to a second domain with the random arm not
  quiet (L258); the next-stroke predictor never beat the priors (L259); the specificity battery killed L255's
  selectivity clause (L260); the reader reads the goal's axis as the standing preference (L261); the
  future-choice readout died to option wording and runs repaired as /v2 cells (L263); the appraisal
  track landed on a reader at chance on the source world (L265 to L269); R01's support is a fluency
  policy (L270); R02's ease arm was unrealized (L271); demonstrations are followed as instructions (L272); the forensic purchase is cost-blind (L273); drawing orders enactable but equifinality unread
  (L274); the reader forages for the familiar with no hope bias (L275 to L277); the repaired joint question
  lands every reader under uniform (L278) and the note's conflict goes undetected (L279); the inferred preference fails across episodes (L280).
  Discovery and repair cells exhausted; the closure block ran last. Stop:
  `taskkill //F //T //PID $(sed -n 2p results/.gear2.lock)`, then clear results/.gpu.lock after
  confirming the card is free; a restart resumes from rows.** The Stage-5 machinery is the Stage-4
  machinery subclassed (paths, lanes, registry), so every Stage-4 guard still binds it.
- **Stage 4 CLOSED 2026-08-28 19:33 (RUN_TO_EMPTY; 21.2 h elapsed, 14.95 GPU-h held; 307 of 322
  expected cells; A01 and T01 confirmed on the fresh reserve; packet plus analyst synthesis at
  results/phase_2_4_stage_4/CURATOR_PACKET_FINAL.md). The chained gear then ran the five Stage-3
  re-runs (L251 to L255) and exited empty at 21:22; the Stage-3 validator reads exhausted again
  (78 cells). Nothing is running; every landing is written through.** The run's history: Stage 4
  ran under second gear via `run_stage4.sh`, launched
  2026-08-27T22:22:50, STOPPED 05:57 on his order for the T-track construction repair (TODO R7)
  and RESTARTED at half past six with T01 and T02 reset to the head of the queue; the contract's deadline
  is accounting only, the closure block (F01) begins on exhaustion, and the wrapper then execs
  `run_second_gear.sh` (until empty) for the five Stage-3 re-runs R1 to R5. Stop:
  `taskkill //F //T //PID $(sed -n 2p results/.gear2.lock)`, then clear results/.gpu.lock after
  confirming the card is free; a restart resumes from rows.** Nine cards had landed and were
  written through (L237 to L244) before the stop; T01 re-landed 08:07 on the repaired
  construction in the same band (L244 carries the history); by 16:53 every discovery card and
  the whole expansion rung had landed (L245 to L250 and five fold-ins, written through at 20:00
  after the agent's 08:10 session loss); F01 opened 16:52 on the two eligible candidates, A01
  confirmed on the fresh reserve, T01's confirmation running; the science waits for the final
  packet. His standing rule from the stop: useless compute stops the
  moment it is known useless, before the cell finishes; repair, then the real run.
- **Stage-4 concurrency audit, 2026-08-28: NO corruption, and none reachable in what
  remains.** `soundingline/s4.py`'s `Lineages` has a lost-update shape (each runner holds a
  whole-file snapshot from its own start-up and writes the whole dict back), the same class
  `_fresh()` already closes for `RunContract`. It has not fired. Verified two ways: every one
  of the 768 `inspected` flags that should exist does exist, zero used-but-unmarked lineages
  across all eight cards carrying case rows, and zero confirmation lineages contaminated; and
  structurally, of the four cards that can run beside a GPU cell (`CPU_CARDS` = I01, H03, P01,
  P02) P01 and P02 never reference `Lineages` at all and H03's arm contains no lineage write,
  the two `mark_inspected` calls in `s4_run_h.py` living in the H01 and H02 arms. The one long
  overlap, H03 beside C02 for 3.7 hours, therefore had a single writer. **All seven remaining
  cells are gpu=True, GPU cells serialize through the gpu lock, expansion rungs are admitted
  gpu=True, and no CPU card is left, so no two lineage-writing processes can overlap again this
  run.** Fix the snapshot at cutover, not mid-run.
- **Two dead controls found in the same audit, WIRED LIVE 2026-08-28.** `mark_generated` was
  never called by any runner, so all 3904 lineage rows carried `generation_hash: None` and
  `duplicate_content()`, which the scheduler writes into COVERAGE as `duplicate_lineages`,
  returned `[]` unconditionally: the packet would have read `no duplicates` where the truth
  was `not checked`. Now every root construction registers its content hash through
  `CardRun.register_world`, COVERAGE carries `generation_hash_coverage` (checked or not, per
  card) and the rebuilt-from-id `construction_audit`, the `Lineages` ledger is a lock-held
  reload-modify-write (the lost-update shape closed at this cutover), and the T-track
  constructor enumerates a per-domain identity space with the expanded and confirmation
  blocks disjoint (2,368 root units audit all distinct).
  Performed by hand instead, it found the T-track construction defect now recorded as TODO R7
  (`make_lesson_world` ignores its domain argument; 128 nominal T01 units are 31 distinct
  worlds). This is the project's named recurring death, a criterion that could not fire.
- **Stage-4 theory errata APPLIED 2026-08-28** (`docs/design/PHASE_2_4_STAGE_4_THEORY_ERRATA.md`,
  now the source record). Five small theory additions across the four owners, each carrying a
  reconstructed-speech attribution; eight evidence corrections to the Stage-3 record; six
  afterwords revised in the same edit. The corrections narrow how existing measurements may be
  read and retract none of the larger hypotheses. Where the working tree had moved past the
  errata's reviewed base the errata's own reconciliation clause governed: L236's corrected
  aggregation is landed rather than owed, and the landed Stage-4 rows (T01-S4, C01, C02) stay in
  their afterwords. Corrections are linked in FINDINGS' known-weaknesses table as item 0; the
  re-runs they imply are TODO Phase 0, R1 to R6, none startable until Stage 4 frees the GPU.
  **No Stage-3 artifact is corrupt:** 72 of 73 produces read intact, the absent one being M02,
  INSTRUMENT_FAILED with a recorded reason and zero GPU minutes.
- **Stage 3 (E24-S3) is PROGRAM-EXHAUSTED by its validator (73 cells resolved, 72 of 48 valid attempts); the queue drained inside one second-gear window and the until-empty chain ended on its own; gear is idle.** Everything is written through (L171-L235) and the build and record are committed and pushed (6feda02, 858f83a). Open: the two-pass curator packet, then his assessment (the reserve refresh landed, L235). History that still binds operations: the 08-17 power-loss audit found no unrecorded findings (write-through discipline held); the GPU lock's staleness window is 22h (raised 2026-08-17 after a live 620-minute rung was reclaimed at hour nine); the regear waiter cancels by FILE (`results/.regear.cancel`), never by pid; drain checks are repo-scoped by path (2026-08-27).
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

- **His:** the Stage-5 and Stage-5R assessments (both packets carry a synthesis; the second contract's work order is in its packet), the Stage-4 and Stage-3 assessments; the standing decision: a reader that passes the latents-to-choice and source-register gates before the joint and appraisal tracks run a third time; the commit of the two contracts' build and record when he authorizes it. Standing from earlier phases: interest ratings (HH-14, informs READER_HEURISTICS only); PAN22 Aston access; rotate the early-project API key.
- **Mine, in order:** the two general-queue stages' write-through when they land; the post-run items still open (m: an ease ruler validated on known-answer renderings; o: the echo rule; u: the twin-abstention clause; v: the integrity runners' cell override; l: ease crossed within a route type; t: the source gate re-measured on the repaired text; b: a same-family second checkpoint that passes the gate); the two-pass Stage-3 curator packet if he wants it separate; the design-lint residue on six headers (TODO); the commit when he authorizes it. The pre-Phase-2.4 owed builds (the 9-action BST rebuild, G130c floor decomposition, G94 Taramsa, G97 maker-as-random-effect, the specification-percentile function) remain in `TODO.md`'s backlog, superseded in priority by the Stage-3 endgame.
- **The one-maker-many-kinds corpus problem** stands (CROSSNEWS pseudo-documents only;
  Guardian small; CMCC request-only); the program's G133 commissioned pilot leads this thread.
