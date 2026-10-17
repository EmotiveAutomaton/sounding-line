# Sounding Line packet, 17 October: the test tree

Public review copy: one local operational-calendar row is omitted. Scientific cards, controls, gates and scope are unchanged. The exact supplied/execution copy is retained locally; its hash is recorded in the dispatch and filing ledgers.


17 October 2026. **For the Sounding Line agent, from the curator.** Handing this packet over is the curator's authorization for everything in it, within section 10. It amends the 16 October drive packet (revision 2) and `docs/design/stage-15/drive/EXECUTION.md` where it says so; everything else in them stays in force, including the seven review amendments. Nothing is left open. Each choice is made here with its reason, and where two options were close, both run. Record the curator's handoff message verbatim, with its date and this packet's SHA-256: that is the authority sections 7 and 10 cite.

## 0. How to run this

1. **Make the operating changes in section 2 first,** time-boxed to 2 agent-hours. They exist because 17 hours after the 16 October handoff no D card had run, and the CPU sat idle from 00:40 with about fifteen cards runnable.
2. **Freeze one batch plan** for Tier 0, the passes P4 to P8, and the Tier 1 cards ranked 1 to 12 (section 4), with this packet's card text as the plan body. Dispatch at once, highest rank first, across the CPU slots and builders section 2 authorizes. Freeze the next wave whenever a slot is about to go idle.
3. **Climb the tree** (section 3). Every card ends in one state, and the state decides the next move: a null registers the card's ladder variants, which run at its rank; a positive gets its extension and then texture, and a marginal its extension first (section 3.2). A family stops after six nulls in a row, counted in ladder order (section 3.4).
4. **Land results in batches** (section 2), write a digest at 20:00 PDT every day, and the plain-language page on Tuesday.
5. **Come back to the curator only for the two triggers in section 10.4.** Everything else is decided here, and nothing waits on him.

## 1. State read (17 October, 10:00 PDT, `6c063f5cd`)

- **Running:** one worker, P1's suggestion main (v4, GPU), launched 08:20. Point estimate done about 22:45 tonight; hard stop about 03:36 Monday. It scores 16,855 menus and 69,109 suggestions with five readers in contexts c0 to c3. P1's typed-sentence and history parts are unbuilt.
- **Done since the handoff:**
  - P2 timelines: 1,399 sessions, 61 writers, 16,855 decisions, 2.41 million text deltas, 203,462 edit windows.
  - S0 twin references T1, T3 and T4, delivered to Ghost.
  - V2: the Phase 0 backbone beats population rates by +0.0240 half-Brier [0.0175, 0.0307]; no calibrated reader combination reaches +0.01 over the backbone.
  - V1 Phase 0: a constant offset of 0.8 log-odds came back in 10 of 10 worlds; planted taste and habit came back in 0 of 10 at every size; 0 of 30 null worlds gave a false positive.
  - Content features: 82,941 MiniLM vectors.
  - G3-A0, 4 cents: Haiku passes Q1, Q3, Q5, Q6, Q8 and Q9; it fails tone (Q4), contradiction (Q7) and themes (Q10).
- **Not done:** all 31 D cards (registered, none built), V1's other arms, V3, P3, P4's fit, the S0-T2 parser.
- **Why so little ran.** Process, not compute: a full executable plan per card before dispatch; one exclusive single-thread CPU lane; a watcher that wakes the agent only on terminal events and every six hours; a five-step landing per result, with operational events written up as findings; a no-retry rule that turned each P1 bug into a new versioned attempt (14 attempts); no time box on shared passes; and dependencies the registry added that the packet didn't have. Section 2 changes each of these.

## 2. Operating changes for this campaign

These hold from handoff to the Wednesday freeze. Then the prior rules return unless the curator says otherwise.

| # | Was | Now | Why |
|---|---|---|---|
| 1 | Each card gets its own frozen executable plan (design doc with DESIGN CHECK, pinned PLAN.json, owner identity, monitor handshake, claims, tests) before dispatch; "a registry entry is not a queue job" | **One frozen batch plan per dispatch wave**, `docs/design/stage-15/drive/BATCH_PLAN_20261017_W<n>.md`. Its body is this packet's card text. Per card it pins, at dispatch: code hash, input hashes, primary contrast and direction, initial sample, the one extension, controls. One DESIGN CHECK block in the batch plan, and one in a shared state module (`runners/drive/cards/states.py`) that every card imports; card runners don't redeclare the shared states. A runner that holds a card-specific band or gate (TC's bands, V4's states, D34's verdicts, D31's κ rung) carries its own DESIGN CHECK block. A card is queued the moment its row is frozen | The ceremony, not the computer, was the bottleneck. The card text already holds what a plan needs |
| 2 | One exclusive CPU lease (`results/.cpu.lock`), one numerical thread, below-normal priority | **A counted CPU lease with N slots:** N = 4 if the host shows at least 12 logical processors, 3 with 8 to 11, 2 below that. At most 2 numerical threads per worker. Below-normal priority stays. A new start needs 6 GiB free RAM. Ghost's three one-thread workers keep running; Sounding Line keeps priority | About fifteen CPU cards were runnable while the CPU idled |
| 3 | "Keep one operating session. Delegate only on an explicit per-task request" (STATE ruling 1) | **This packet is that request.** The owner may run up to three card builders (subagents) at once. Builders write card code, tests and draft reports in their own files. The owner alone holds the queue, leases, Gear 3, landings and commits | Writing code is now the critical path |
| 4 | Watcher `transition_only: true`: only terminal events and the six-hourly health wake the agent; a healthy run ends the turn | **Planned check-ins, reinstated for the campaign.** Set `transition_only: false`. While any card is building, queued or running, keep one check-in at most 60 minutes ahead (`tools/codex_watch.py schedule`, the 11 September planned-wake form). Terminal events and failures still notify at once. Every wake dispatches the next runnable card before it acknowledges anything. Restore `transition_only: true` at the freeze | The agent waited hours with runnable work |
| 5 | Six-hourly health: full inspection, FINDINGS entry, triplicated status edit, inspection and ACK JSONs, a commit, rehashing hundreds of pins | Keep the six-hourly wake. Its inspection writes **one receipt JSON and one line** in `results/phase_2_4_stage_15/DRIVE/OPS_LOG.md`. A FINDINGS entry only on a failure. Rehash only pins that changed since the last health | 22 operational FINDINGS entries in 17 hours; `FINDINGS.md` is 6.3 MB |
| 6 | Five steps per result in the same pass (FINDINGS, theory row, TODO, chat, roll-up), plus a full entry for every apparatus event | **Batch landing for descriptive cards.** At once: each card's `DRIVE/<card>.md` and `.json` and its INDEX line. Per landing batch (at most one per wake): one FINDINGS entry carrying each card's roll-up line, new p-values into `runners/audit_multiplicity.py`, and a chat summary. At the 20:00 digest: theory rows and afterwords, TODO. Operational events go to OPS_LOG, one line each | The five-step contract is right for findings and wrong for a screen of forty descriptive cards. Nothing waits more than one wake for its files, so nothing is lost |
| 7 | Status triplicated across CURRENT_STATUS.md, docs/STATE.md and docs/CODEX_OPERATIONS.md | CURRENT_STATUS.md and `DRIVE/INDEX.md` during the campaign; STATE and CODEX_OPERATIONS at each digest | Triple edits per event |
| 8 | Independent full replay of every output (605 files rehashed for V1) | Descriptive cards: input and output hashes, plus a fresh process recomputing the primary statistic from saved intermediates. Full replay only for outputs feeding Gear 3 spend, the engine, Ghost, or Tier 4 | Replay effort scaled with file count, not risk |
| 9 | No generic retry; each failure became a new versioned attempt with contract, tests, receipts and a FINDINGS entry | **One retry per card or pass to repair an engineering failure** (crash, out-of-memory, a code bug, a resource wait), without a new version, when inputs, comparators and the primary contrast are unchanged. Log it in OPS_LOG. A second failure records the card as invalid, with its reason. A retry never redraws seeds, relaxes a threshold or changes a contrast: EXECUTION.md's ban on rescue stays | Versioning turned every bug into a day |
| 10 | Three agent-hours per card; no box on shared passes | Cards keep 3 agent-hours to build, plus one 3-hour extension for marginal or positive results (16 October rule). **Shared passes** (typed P1, P3, the S0-T2 parser) get 4 agent-hours per attempt and at most 2 attempts, then the fallback named in section 6 | P1 absorbed the day |
| 11 | The registry added P1 to D2, D11, D18 and D19, P3 to D14, and TODO `S15-DRIVE-NATIVE` put blind native references before any paid annotation | **Dependencies are the ones in this packet's tables, and no others.** D18 needs P1 only for its fluency measure; its other measures run now | The 16 October packet listed "none" for these |
| 12 | Pilot actual cost and speed before any full workload; threefold factor; 10-hour minimum and 72-hour maximum | CPU cards forecast under 2 CPU-hours need no separate pilot: the first 10% of the run is the pilot. Cards forecast at 2 CPU-hours or more run one pilot cell first (V4: one world at δ = 0.4 per plant; D14: 10% of writers). Whenever a pilot projects past twice the forecast, the card continues but yields its slot to the next two ranked cards first, and OPS_LOG records the projection. GPU work keeps EXECUTION.md's pilot rule | Pilots doubled the work on one-hour cards |

**Stone, unchanged by this packet:**
- Gear 3 per-use approval, and never past $10 without the curator's detailed final approval, enforced in code (STATE ruling 6).
- Hash-locked files (`docs/SOUNDING_LINE_SPEC.md`, `prereg/*.py`, `soundingline/locks.py`).
- No author contact (ruling 2). Material spend only behind positive results (ruling 7).
- Privacy: raw CoAuthor text stays private; transfers only as section 10 states; public files hold aggregates only; no identification model is published.
- Every measure ships with a null that can fail it, written before the run. Per-card freeze of code and comparators with hash. DESIGN CHECK blocks where `tools/design_lint.py` requires them.
- Every result is DESCRIPTIVE: never promoted, never an admission witness.

## 3. The test tree

### 3.1 Tiers

- **Tier 0, instruments.** Can the lens see what we're asking about, and how much is there to see? The timing census (TC), V5, V4, and V1's Stage 14 arm. They run first, beside Tier 1. They label everything below them; they don't hold it back.
  - **Tier 1, the screen.** Eight theory families, each with a ladder of cards (3.4). Cards run in rank order across families on data in hand, one primary contrast each.
    - **Null:** the family's variants are registered, and six nulls in a row, counted in ladder order, stop the family.
    - **Positive or marginal:** texture (3.3).
      - **Tier 2, texture:** specification curve, second pipeline, second dataset, planted calibration.
        - **Tier 3, paid labels:** Gear 3 only where a card or texture move needs labels no local tool gives (section 7).
          - **Tier 4, confirmation:** frozen now, run after the talk on locked holdouts (FX1, and Padmakumar & He's writers, section 5).

### 3.2 States and moves

States are EXECUTION.md's five (positive, marginal, null, negative, invalid, with the 16 October definitions), plus **blind** (Tier 0 only: the instrument can't see planted effects at the sizes tested) and **blocked** (an input is missing; not a scientific state).

| State | Next move |
|---|---|
| positive | Its one frozen extension, then the texture moves; the family's null counter resets |
| marginal | Its one frozen extension. The state after it is the extension's own state in its own direction; for D30, D33, D34 and D36, whose extensions re-estimate the primary under a stricter specification, it is the primary's state under the extension. Positive then gets texture; anything else counts as a null. A card with no extension (every ladder variant; D15, D19, V3) keeps "marginal", which counts as a null and gets no texture |
| null | Record it; the family's null counter goes up by one; the card's ladder variants, if any, are registered and dispatched at its rank |
| negative | Record it; texture move (a) runs, because a reversed sign is a finding (this amends EXECUTION.md's "negative/null branches stop" for negatives only); the counter resets |
| invalid | One engineering retry (section 2, row 9); then record it with its reason; the counter doesn't change |
| blind | Every card that depends on the instrument carries the label (3.5) |
| blocked | Record the missing input; the card's ladder variants, if any, are dispatched |

### 3.3 Texture moves

Each move is its own card with its own frozen contrast, registered in a batch plan before it runs. Texture moves take the suffixes `.s`, `.p`, `.r` and `.c`; ladder variants are named `.v1`, `.v2`, `.v3`.
- **(a) Specification curve** (`.s`): every reasonable specification the card lists (covariates, thresholds, windows, estimators), with the median effect tested against a permuted-outcome null ([Simonsohn, Simmons & Nelson 2020](https://doi.org/10.1038/s41562-020-0912-z)).
- **(b) Second pipeline** (`.p`): a different estimator family on the same question, named in the card.
- **(c) Second dataset** (`.r`): replication where the card names one: ScholaWrite (already held; split by project, per its recorded leak caveat, with paper sections standing in for prompts), KLiCKe (one session per writer, so only for questions that need no repeated sessions), the Gutenberg sample, Jester.
- **(d) Planted calibration** (`.c`): for cards whose outcome is a handling decision only, plant the effect at its observed size into V4's base worlds and rerun the card's own pipeline on 5 worlds. The recovery rate says whether the observed effect is within the instrument's reach. For any other card, record (d) as not applicable.

Order: (a), (b), (c), (d); but (d) first when V4 reports blind for the effect's kind.

### 3.4 Families and their ladders

Each family is one of the curator's current questions. **Dispatch is by rank only** (section 4.3). A family's ladder does two things: it orders the family's null count, and it names the variants registered after a parent's null. Nulls are counted in ladder order over landed cards; when six in a row land null (blocked and invalid don't count), the family's unstarted cards are recorded "stopped". A card that sits in two families counts in the first one listed. A positive resets the counter, and once its texture runs, the family carries on: a positive opens questions, it doesn't close the family.

| Family | Question | Ladder |
|---|---|---|
| **K. Pervasive or local** | Is an autocompleted choice person-located and automatic, and does pervasiveness show it? | D30 (variants D30.v1, D30.v2, D30.v3) → D31 (variant D31.v1) |
| **B. The branch never drawn** | Is an absent option unconsidered or disliked? | D32 (variant D32.v1) → D6 → D2 → D28 → D38 |
| **A. Attention, trust, and System 2 training System 1** | Does attention follow trust, land where her own expectations fail, and compile into habit? | D35 → D33 → D39 → D17 → D23 → D3 → D16 → D7 |
| **G. Hidden goals and set points** | Do unexplained corrections serve goals nobody named? What do writers protect? | D34 (variant D34.v1) → D14 → D4 → D29 → D18 → D24 → D22 |
| **E. Three entries and structure** | How much do the page, the person and the process each carry? | D15 → V3 → P4/D1 → D37 → D20 → D11 → D5 → D19 → D27 |
| **R. Readers and context** | Do readers converge, and where does a writer depart from them? | D12 → D21 → D13 → D23's reader half |
| **S. Beauty as fast resolution** | Does liking track how fast something resolves? | D36 (variant D36.v1) → D13 (counted in R) |
| **P. Panels and other domains** | Does any of this hold off CoAuthor? | D9 → D10 → D8 → D23b |

### 3.5 Reporting

- **Each card** reports: question, data, hashes, the primary effect with a writer-cluster 95% interval, its state, the route line (what each state changes for ToMpathy and the theory, given in the card), and one sentence for the curator in plain words.
- **The screen** is reported at each digest as one table of every Tier 1 primary contrast landed so far, with:
  - Benjamini-Hochberg q-values at q = 0.10 across them (descriptive, nothing promoted);
  - shrunk estimates for positives on the z scale, since the cards' effects come in different units: z × τ²/(τ² + 1), with τ² = max(0, mean z² − 1) across the landed primaries, because the largest of forty estimates overstates its effect;
  - three positive controls (three constant-offset worlds at 0.8 log-odds, which V1 recovered 10 of 10; V4 cells rated "sees" are reported beside them but don't flag) and three negative controls (D30, D32 and D34 rerun with outcomes shuffled within writer). A negative control reaching positive, or a constant-offset world coming back null, flags the whole day's screen.
- **Tier 0 labels.** Every writer-level taste result carries V4's taste finding in its INDEX line: "the lens sees taste from δ = 0.4", "the lens sees taste only at δ = 0.8", or "the lens is blind to taste at every tested size". The same for habit. V5's headroom converts every forecast gain into a share of what is left to predict.
- **INDEX** shows the tree: per family, each card's state, and the family's null counter.

## 4. Lanes and running order

### 4.1 Shared passes

| Pass | What | Feeds | Cost | Fallback, decided here |
|---|---|---|---|---|
| **TC** (new, Tier 0) | Timing census, section 5 | every pause-based card | minutes | its own rule decides how timing cards measure |
| **P5** (new) | Encode writer-typed sentences and every edit's before and after span with the frozen MiniLM that made CONTENT_V2 | D4's split, D11, D18, D20, D32, D34.v1, D35, D38 | under 1 CPU-hour | none needed |
| **P6** (new) | Leave-writer-out word 3-gram Kneser-Ney models over writer-typed text, one per held-out writer | D30, D33 | under 1 CPU-hour | none needed |
| **P4** | The chronological fit, as frozen in `P4_CHRONOLOGY.md`. Builder 1 starts it Saturday, so it is frozen well before Monday 12:00 | D1, D37, G3-A's look | under 1 CPU-hour | none needed |
| **P7** (new) | GPT-2 medium on CPU (already cached, per `docs/TOOLS.md`), run unconditionally: per-word surprisal of writer-typed text and of the Jester jokes | D33's extension, D36, and P1's fallback for D13 and D27 | 1 to 2 CPU-hours | none needed |
| **P8** (new) | Extract GPT-3's logged `probability` and the decoding settings from the raw jsonl (`corpora/coauthor/coauthor-v1.0/*.jsonl`) into a private per-suggestion table | D2, D12, D15, D16 | under 1 CPU-hour | none needed |
| **P3** | 200 blind agent labels, the IteraTeR intent classifier (intake 7; GPU minutes, after the main), and G3-P as second labeler | D22, D4 intents | 4-hour box, 2 attempts | If the classifier is unavailable or fails κ ≥ 0.6 on meaning-changed against the agent labels, and Haiku passes, Haiku's labels serve D22 and D4. If both fail, D22 reports meaning-changed against fluency from the deterministic split only |
| **P1 typed and history** | Typed-sentence scores and c4 history packing | D21 typed half, D13 expectation term, D27, D18 typed spans | 4-hour box, 2 attempts; GPU after the main | P7's GPT-2 medium supplies D13's expectation term and D27's surprisal feature; D21's typed half and D18's typed spans move to the post-talk campaign |
| **S0-T2 parser** | Bounded streaming parse of the Lichess month | D23b, Ghost's T2 | 4-hour box, lowest priority | T2 stays undelivered; Ghost records it as blocked at its freeze |

**Intakes** (network lane, under `docs/design/stage-15/DATA_INTAKE.md`; if the policy refuses a source, skip it and record why):
1. **Gutenberg sample for D31:** 120 novels from the [Standardized Project Gutenberg Corpus](https://doi.org/10.3390/e22010126) (SPGC), chosen as section 5's D31 says. Public domain.
2. **Padmakumar & He's logs** ([repository](https://github.com/vishakhpk/hai-diversity)): 38 Upwork writers on the CoAuthor interface, with GPT-3, InstructGPT and no-model arms; raw logs in CoAuthor's replayable format. **This is the Tier 4 holdout.** Download, hash, and run a schema census only (counts, fields, writer identifiers). No card reads its outcomes before Tier 4. No license is stated, so it gets CoAuthor's handling: private, aggregates only.
3. **Jester Dataset 2+** ([Goldberg et al. 2001](https://doi.org/10.1023/A:1011419012209)): 150 jokes with their texts and ratings from tens of thousands of users. For D36.
4. **rJokes** ([repository](https://github.com/orionw/rJokesData); more than 550,000 rated Reddit jokes, under Reddit's terms): for D36's variant, only if the intake policy accepts those terms.
5. **KLiCKe** ([Tian, Crossley & Van Waes 2025](https://doi.org/10.17239/jowr-2025.17.01.02); 4,992 essays, one session per writer, full keystroke fields): for D17's choice of the number of components only. Optional.
6. **Yang et al. 2017 edit labels** for D8, carried from 16 October.
7. **The IteraTeR intent classifier** (`wanyu/IteraTeR-ROBERTA-Intention-Classifier` on Hugging Face) for P3. If it is gated or absent, P3's classifier counts as failed and P3's fallback applies.

### 4.2 Lanes

- **GPU:** P1's main finishes and is independently verified → P3's classifier pass (under 1 GPU-hour) → P1 typed and history (boxed) → D10's embeddings. One Sounding Line GPU job at a time, under the existing lock. ToMpathy may run one locked session of its battery reruns only when this queue is empty, unloading its model before it releases the lock.
- **CPU:** N slots (section 2, row 2), in rank order. ToMpathy's battery reruns (its packet, section 2) run on CPU at below-normal priority and count as one of these slots while they run.
- **Builders**, split so they don't collide:
  - **builder 1, menus and models:** P8, V4, V5, P4, D34, D34.v1, D2, D12, D15, V3, D37;
  - **builder 2, timing and text:** TC, P6, P7, D30 and its variants, D33, D17, D3, D23, D36;
  - **builder 3, corrections and events:** P5, D4's deterministic split, D35, D32, D38, D39, D6, D14, D28, D18;
  - **owner:** section 2's changes, batch plans, intakes, Gear 3, D31, landings and digests. Later cards go to whichever builder is free.
- **Network:** intakes.
- **Gear 3:** G3-K first, then G3-P, then G3-A's first look if P4 is frozen in time (section 7).

### 4.3 Ranks

Tier 0 runs first, whatever its rank: **TC, V5, V4,** and **V1's Stage 14 arm** (only if its code runs offline without paid calls; its process-identity arm runs with D16; its text arm moves to the post-talk campaign).

| Rank | Card | Family | Needs | Cost |
|---|---|---|---|---|
| 1 | **D30** Pervasive or local: Kelley's test on writers' own choices (new) | K | P2, P6, TC | 1 to 2 CPU-hours |
| 2 | **D32** Unseen or declined: the branch never drawn (new) | B | P2, P5 | under 1 |
| 3 | **D35** Do corrections become defaults? (new) | A | P5, D4's split | under 1 |
| 4 | **D33** Surprise against her own past (new) | A | P2, P6, TC; P7 for its extension | 1 to 2 |
| 5 | **D34** Hidden goal or noise (new) | G | Phase 0 predictions, CONTENT_V2; V4's taste worlds for its positive control (V1's taste worlds if V4 hasn't landed); P4 for its extension | 1 |
| 6 | **D31** Author or character: Kelley's test on fiction (new) | K | Gutenberg intake, G3-K | 1, plus about $1.50 |
| 7 | **D39** Trust sets attention (new) | A | P2 (menu events) | under 1 |
| 8 | D17 Pauses in boxes (revised) | A | P2, TC | under 1 |
| 9 | D6 Attention against preference | B | P2 | 1 to 3 |
| 10 | D2 Near-ties, and whether writers differ in taste | B | CONTENT_V2, P8 | under 1 |
| 11 | D14 Controlled variables, local half | G | CONTENT_V2, spaCy | 2 to 3 |
| 12 | D4 Corrections as preference records, deterministic split | G | P2, P5, spaCy | 1 to 2 |
| 13 | D23 Play, non-reader measures | A | P2 | under 1 |
| 14 | D12 Departures from the model's favorite, GPT-3's logged probability | R | P8 | under 1 |
| 15 | D28 Going back and forth, hover half | B | P2 | under 1 |
| 16 | D29 Where writers stop | G | P2 | under 1 |
| 17 | **D38** One bad accept: how wide does avoidance spread? (new, exploratory) | B | P2, P5 | under 1 |
| 18 | D3 Reversal timing | A | P2 | under 1 |
| 19 | D18 Sacrifice, prompt-fit half | G | P2, P5 | under 1 |
| 20 | D15 Holding the common pieces constant | E | P2, P8 | under 1 |
| 21 | V3 A reliability table | E | D15 | hours |
| 22 | P4/D1 Content features | E | CONTENT_V2 | 1 to 3 |
| 23 | **D37** Three entries: page, person, process (new) | E | P4, D17, D15, V3 | 1 |
| 24 | D16 Writer verification | A | D17, D15, V3, P8 | 1 to 2 |
| 25 | D24 A need switch at the timer | G | P2 | under 1 |
| 26 | D20 Influence without selection | E | P5 | under 1 |
| 27 | D11 Expertise in what gets accepted | E | P5 | under 1 |
| 28 | **D36** Beauty as fast resolution: jokes (new, exploratory) | S | Jester intake, P7 | under 1 |
| 29 | D5 The leapfrog inside a session | E | P2 | 1 to 2 |
| 30 | D7 Dwell decomposed | A | P2 | under 1 |
| 31 | D19 A dictionary of shared recipes | E | P2, CONTENT_V2 | under 1 |
| 32 | D9, D10 Panels | P | panels; GPU for D10 | 1 to 3 |

**Tier 1b**, after P1's main lands and is verified: D21, D13, D27; the P1 extensions of D12 (local readers) and D18 (fluency); and the P1 measures added to D28 (reader spread) and D23 (reader half), reported beside those cards and not their frozen extensions. **After P3:** D22, D4's intents. **Held:** D8 (fetch its labels first), D23b (needs the parser). **Moved to the post-talk campaign:** D24b. **Closed:** S0-T4-104. The released exclusion roster doesn't exist, and author contact is barred, so it can never run.

## 5. New cards

Every card has one primary contrast with its direction, an initial sample, one frozen extension, and its controls, as EXECUTION.md requires. "Route" says what each state changes, so no result waits on a decision. Intervals are writer-cluster bootstrap 95% intervals (2,000 resamples) unless a card says otherwise.

**Defaults, where a card is silent:**
- **Initial sample:** every writer and every eligible unit in P2's 1,399 sessions; a card on other data uses the whole intake as the card defines it.
- **Ladder variants** inherit their parent's direction, controls and route unless they state their own, and have no extension of their own.

### TC. Timing census (Tier 0, before any pause-based card)

**Why.** CoAuthor logs text deltas, not keypresses, and the replay code says so ("logged delta event, not individual keypress"). Before any card reads a pause, we need to know what a pause is in this data.

**Count:**
- the share of writer-typed characters that arrive as single-character insert deltas;
- timestamp resolution: the smallest nonzero interval, and the share of zero intervals;
- multi-character inserts that aren't suggestions (autocorrect, paste).

**Rule, decided here** (the bands are exhaustive; resolution is the smallest nonzero interval):
- At least 80% of typed characters arrive singly, at a resolution of 100 ms or finer: timing cards measure per character.
- 50% to under 80% arrive singly, at that resolution: timing cards measure the interval before the delta holding the target's first character, and report the share.
- Anything else: pause outcomes are invalid.

**If invalid:**
- D30's primary becomes D30.v1's contrast (revision), and D30.v1 is recorded as run;
- D17 and D33 are blocked;
- D16 and D37 drop D17's pause shares, and their dependency on D17, and keep their other process features;
- D3 and D39 read menu-event timestamps, so TC doesn't touch them.

### V4. Can the lens see taste and habit? (Tier 0)

**Why.** V1 recovered a planted constant offset every time, and planted taste and habit never, at any size. Either writers have no taste or habit at that scale, or our readers can't see them. The research pass's arithmetic says which to expect:
- one writer's slope on a feature needs 0.77 to 1.18 log-odds to be seen in about 250 decisions;
- variation in slopes across 60 writers should show from about 0.21.

V1's readers were never built to ask the population-level question. V4 builds readers aimed at each planted structure, and asks it.

**Base:** the Phase 0 population model's handling probabilities, fitted chronologically, as in V1.

**Plants,** on the accept log-odds:
- **Taste.** Writers share a low-dimensional taste space, as R-taste assumes. The space is 16-dimensional and lexical: character 3-gram TF-IDF of offered suggestions, reduced by truncated SVD fitted on suggestions only. Fix one 16 × 4 basis Λ for all worlds, and give each writer w the direction u_w = normalize(Λ z_w), with z_w ~ N(0, I₄). The plant is δ × the standardized projection of each suggestion on u_w. Readers see MiniLM features instead: a different representation, on purpose, because a real writer's taste isn't stored in our reader's coordinates. A **matched arm** builds the same plant in 16 MiniLM principal components, where R-taste with K = 4 can represent it exactly; it is the upper bound.
- **Habit.** A choice kernel over handling classes: K_t = λ K_(t−1) + (1 − λ) × (the class chosen at t − 1), with λ_true = 0.7. The plant is δ × s_w × (K_t for accept, centered within writer), with s_w ~ N(0, 1) drawn once per writer. Writers then differ in how hard the kernel pulls them, which is the writer-specific component the existence test looks for. The kernel is regenerated recursively from each world's own simulated choices, as EXECUTION.md's V1 amendment requires.
- **Sizes:** δ in {0, 0.2, 0.4, 0.8}. Run 5 worlds per cell first. Add 5 more at δ = 0 and δ = 0.4, and in any cell whose count is 2 or 3 of 5.
- **Pilot:** one world at δ = 0.4 for each plant, timed, before the rest (section 2, row 12).

**Readers:**
- **R-kernel:** a choice kernel ([Miller, Shenhav & Ludvig 2019](https://doi.org/10.1037/rev0000120), habits as "direct strengthening of recently taken actions"), with λ in {0.5, 0.8, 0.95} and partially pooled writer weights.
- **R-taste:** K = 2 and 4 shared taste dimensions over CONTENT_V2, with partially pooled writer loadings (a factor-analytic random-coefficient logit).
- **R-both:** both together.
- **R-oracle:** the planted feature itself, with writer-specific slopes. If R-oracle sees a plant that R-both misses, what's lost is representation, which a better reader can fix, not information.
- **R-Phase0:** V1's pipeline, for continuity.

**Existence test:**
- the likelihood ratio for the writer-specific component, referred to the 50:50 mixture of χ²₀ and χ²₁ when that component is one variance ([Self & Liang 1987](https://doi.org/10.1080/01621459.1987.10478472)); when it has K variance parameters (R-taste with K dimensions), referred to χ²_K, which is conservative on the boundary;
- size-checked on 20 null worlds with writer identities permuted across sessions;
- **detection** means rejection at α = 0.05.

**Usefulness:** half-Brier gain on each writer's last 20% of sessions, over the refit population model.

**Primary contrast:** R-both's detection rate at δ = 0.4 minus at δ = 0, separately for taste and habit. Direction: positive.

**States, exhaustive,** read as shares because cells hold 5 or 10 worlds:
- **sees:** a detection share of at least 0.8 at δ = 0.4 (10 worlds), and at most 0.1 at δ = 0 (10 worlds);
- **sees large only:** at least 0.8 at δ = 0.8 (4 of 5, or 8 of 10) but not at δ = 0.4, with δ = 0 still at most 0.1;
- **blind:** anything else, including a false-positive share above 0.1 at δ = 0.

**Route:**
- **Sees:** earlier writer-level nulls at δ ≥ 0.4 were about writers, not instruments. ToMpathy may show a taste or habit panel built on the reader that saw it.
- **Blind:** those nulls are instrument limits. FX1 stays unrunnable, and ToMpathy shows only population taste.
- **R-oracle sees, R-both doesn't:** the next round builds a better reader.

**Cost:** about 8 CPU-hours across two slots (V1's simpler readers took 7.3); the pilot checks it.

### V5. How much is there to predict? (Tier 0)

**Why.** No reader can predict a person better than the person predicts themselves on a repeat. Simulation studies of people use retest as the yardstick:
- [Park et al.](https://arxiv.org/abs/2411.10109) report agents at 83%, 82% and 86% of participants' own two-week test-retest accuracy;
- [Twin-2K-500](https://arxiv.org/abs/2505.17479) measured retest at 81.72% against twins at 71.72%.

The research pass worked out the exact version for our score.

**Definitions.** For a decision whose true handling probabilities are π over four classes:
- The best possible half-Brier is **B\* = ½(1 − Σ_k π_k²)**, half the chance that two repeats of the same decision disagree.
- Write **A_w** for the agreement between a writer's near-repeat decisions, and **A_b** for the agreement between different writers on matched decisions. Then:
  - the personal floor is ½(1 − A_w);
  - the pooled floor is ½(1 − A_b);
  - **the personal headroom is H = ½(A_w − A_b)**. That's the most any reader of a person can gain over the best reader of people in general, on these decisions.

**Near repeats:**
- pairs of decisions by the same writer in different sessions, on the same prompt, with context cosine at least ε and menu-mean suggestion cosine at least ε (MiniLM), for ε in {0.6, 0.7, 0.8, 0.9};
- A_b uses the same matcher across writers;
- same-session pairs minus cross-session pairs estimate a transient-state term.

**Primary contrast:** H at ε = 0.8. Direction: positive (lower bound above 0).

**Report:**
- the curves over ε, pair counts, both floors, and H;
- every forecast card's gain as a share of (population Brier minus the personal floor), and as a share of H ("completeness", [Fudenberg et al. 2022](https://doi.org/10.1086/718371)).

**Control:** writer labels shuffled across sessions, 200 times; H should fall to zero.

**Caveat.** Near repeats differ slightly in context, which lowers both agreements. Read the trend as ε rises.

**Route** (exhaustive):
- **Upper bound of H below 0.005 half-Brier:** near zero. Personal readers have little to gain on handling at matched contexts, and ToMpathy's personal claims move to process (the how).
- **Lower bound above 0, upper bound at or above 0.005:** H is the size of the prize for every personal card.
- **Anything else:** undetermined; report H with its interval, and use its upper bound when converting gains into shares.

Deliver the aggregates to Ghost (section 8).

**Cost:** under 1 CPU-hour.

### D30. Pervasive or local: Kelley's test on writers' own choices (rank 1, family K)

**Theory.** The curator, 17 October: "The biggest thing to tell a branch that has been autocompleted is the pervasiveness of similar-looking decisions," and "attention is limited."

Attribution theory has the instrument. Kelley's covariation model reads where a cause sits from three facts ([Kelley 1973](https://doi.org/10.1037/h0034225); [McArthur 1972](https://doi.org/10.1037/h0032602)):
- **consensus:** do others do it here?
- **distinctiveness:** does she do it only here?
- **consistency:** does she do it every time here?

Low consensus, low distinctiveness and high consistency locate the cause in the person.

The research pass found one gap and one correction.
- **The gap: consensus.** People underweight it too: in McArthur's data it explained 6.25% of the variance in person attributions, against 21.72% for distinctiveness. Without it, a prompt's conventions pass as a writer's habit.
- **The correction: covariation shows where a cause sits, not whether the choice was automatic.** A deliberate global policy is pervasive and attended. Poe claimed that no point in "The Raven" was "referrible either to accident or intuition" ([1846](https://www.eapoe.org/works/essays/philcomp.htm)). A habit tied to one cue is automatic and local ([Wood & Neal 2007](https://doi.org/10.1037/0033-295X.114.4.843)).

So this card tests both halves of the restated claim: an autocompleted choice is located in the person, and it carries the marks of automaticity (fast, rarely revised).

**Data:** writer-typed text and P2's timelines; the prompt of every session.

**Markers:**
- word unigrams and bigrams and punctuation habits in writer-typed text;
- per writer and marker, over-use is the log-odds ratio with an informative Dirichlet prior ([Monroe, Colaresi & Quinn 2008](https://doi.org/10.1093/pan/mpn018)), against other writers' text **on the same prompts**, with z of at least 1.96. That builds consensus in.

**Classes, decided here:**
- **pervasive:** over-used on at least 3 of the writer's distinct prompts. Writers with fewer than 3 distinct prompts are excluded.
- **local:** over-used on exactly one prompt, at or below the population rate on her other prompts, while other writers' rate on that prompt is not over-used (low consensus).
- A writer-marker needs at least 5 occurrences.

**Outcomes,** measured under TC's rule (if TC rules pauses invalid, the primary becomes D30.v1's contrast):
- the pre-marker pause (log seconds before the marker's first character);
- the typing rate within the marker;
- later revision: the marker's span is deleted or rewritten before the session ends.

**Primary contrast:** within writer, the mean log pre-marker pause of local markers minus pervasive ones. Adjust for marker length, population frequency, position (sentence start, after punctuation) and leave-writer-out surprisal (P6). Direction: positive (local markers are slower, because attended).

**Initial sample:** every eligible writer and marker.

**Extension:** add the writer's own count of the marker as a covariate. This is the sharper form of the claim: does spread across prompts matter beyond sheer repetition?

**Secondary, reported beside the primary:**
- **revision rate, pervasive minus local,** described here and tested only as D30.v1. The restated rule predicts negative (automatic choices are seldom revised); the curator's "your job, in part, as the attention, is to squash those habits" predicts positive.
- **first against later occurrences of each pervasive marker.** The pause should fall with repetition: System 2 compiling into System 1.

**Controls:**
- pervasive and local labels shuffled within writer;
- writer identities shuffled;
- a positive control for the timing pipeline: intervals inside words are shorter than intervals at word onsets.

**Prediction:** positive. If the extension erases it, pervasiveness is only practice count.

**Route:**
- **Positive:** ToMpathy routes recurring departures to the habits panel and one-off departures to the attention panel, citing this card (labeled descriptive). The reader heuristic becomes the restated rule: located in the person, and automatic.
- **Null:** pervasiveness locates choices but doesn't diagnose automaticity in typing. The habits panel keeps the covariation display without the word "autocomplete".
- **Negative:** pervasive choices are slower, the Poe case of deliberate policy, and the rule reverses.

**Second pipeline (for texture):** a mixed model with crossed random effects for writer and marker, on every occurrence.

**Cost:** 1 to 2 CPU-hours.

**Variants on the ladder** (each keeps D30's controls):
- **D30.v1, revision:** same markers; primary = later revision rate, pervasive minus local. Direction: negative, since automatic choices are seldom revised. A positive result reads as attention squashing habits: attention catches recurring choices that misfire. Route: negative, the habits panel can say recurring choices are seldom revisited; positive, the attention panel can say attention catches recurring choices; null, revision doesn't separate them.
- **D30.v2, function words:** function words and punctuation only, the features stylometry treats as least under conscious control ([Kestemont 2014](https://doi.org/10.3115/v1/W14-0908)); D30's primary, direction and route.
- **D30.v3, ScholaWrite:** D30 on ScholaWrite, with paper section types (introduction, methods, results and the like, across papers) standing in for prompts, so consensus comes from other writers in the same section type. TC's census is rerun on ScholaWrite first, with the same bands. D30's primary, direction and route.

### D31. Author or character: Kelley's test on fiction (rank 6, family K)

**Theory.** The curator: "Other characters being fearful imply that this character being fearful is about the author, not about the character."

In Kelley's terms:
- authors are persons, characters and scene types are entities, books are occasions;
- the author's other characters being fearful is low distinctiveness.

The research pass adds two things:
- **consensus:** what other authors' characters do in matched scenes;
- **Kelley's discounting principle:** fear in a low-threat scene is stronger evidence about the author than fear in a high-threat one, because the threat explains less of it.

Computational literary studies found author and character signals "fused in novels" ([Bamman, Underwood & Smith 2014](https://doi.org/10.3115/v1/P14-1035)). The fear here is Panksepp's FEAR system as it shows on the page.

**Data:** from SPGC, 40 English-language novelists born 1790 to 1890 (SPGC's metadata gives authors' birth years, not publication dates), with at least 3 novels each, spread over at least 3 Library of Congress subject labels. Draw the authors, and 3 novels per author, with seed 20261017: 120 novels. A series sharing a protagonist counts as one book. Below, "decade" means the author's birth decade.

**Labels** (G3-K, section 7):
- **Passages:** about 300 words around hits from a 30-word fear lexicon, frozen in the batch plan; at most 100 passages per book.
- **Haiku codes each passage:**
  - threat present (yes/no);
  - threat intensity (low, medium, high);
  - the focal character (the name as written);
  - the focal response (confront, flee, freeze or submit, seek help, other);
  - stated fear (yes/no).
- **Known-answer rung first.** The agent labels 100 passages blind, from at least 30 authors, disclosed as agent labels.
  - Required: κ of at least 0.6 on threat and on a binary fearful response (flee, freeze or submit, seek help, or stated fear; against confront or other).
  - If the five-way response misses κ of 0.5, only the binary runs. That fallback is declared here.

**Model:**
- fearful ~ intensity + genre × decade + (1 | author/book) + (1 | author:character) + an author slope on intensity;
- consensus is the leave-author-out fearful rate in matched genre × decade × intensity cells.

**Primary contrast:** the coefficient on the leave-book-out author fearful rate (her characters in her other books), predicting a character's fearful response beyond intensity, genre × decade and consensus. Direction: positive.

**Extension:** the discounting interaction, the author coefficient in low-intensity scenes minus high-intensity ones. Direction: positive.

**Secondary:**
- author against author:character variance, on the latent-scale ICC for binary codes ([Nakagawa & Schielzeth 2010](https://doi.org/10.1111/j.1469-185X.2010.00141.x));
- a restricted permutation null, shuffling author labels among books within genre × decade blocks ([Winkler et al. 2014](https://doi.org/10.1016/j.neuroimage.2014.01.060)).

**Controls:**
- genre × decade blocks;
- first-person narrators flagged and tested as a covariate;
- extraction error checked across authors with the 100 blind labels, so labeling noise that tracks the author can't pose as an author effect.

**Prediction:** positive and small.

**Route:**
- **Positive:** "pervasive across characters, so about the author" gets a measured base rate in fiction, and ToMpathy's attribution copy can cite it.
- **Null:** in published fiction the author shows in voice, not in characters' fear.

**Cost:** about $1.50 paid (cap $5), 1 CPU-hour, and the intake.

**Variant D31.v1:** the same labels on CoAuthor's story sessions (transfer authorized in section 10).
- Writer = author; prompt = scene type.
- Primary: a writer's leave-prompt-out fearful rate predicting a story character's response. Direction: positive.

### D32. Unseen or declined: the branch never drawn (rank 2, family B)

**Theory.** The curator: a branch can be absent because she never considered it, or because she considered it and turned it down. His case of the first: "You can have sudden expertise that appears through trauma," which pattern-matches where it shouldn't, until "she can't even see that her characters could fight back." "Your autocomplete is broken."

Economics separates the two:
- **consideration sets against preference:** "revealed attention" ([Masatlioglu, Nakajima & Ozbay 2012](https://doi.org/10.1257/aer.102.5.2183)), and the random attention model ([Cattaneo et al. 2020](https://doi.org/10.1086/706861));
- **a consideration shifter:** something that puts an option in view without changing its value, the role advertising plays in [Goeree 2008](https://doi.org/10.3982/ECTA4158).

In CoAuthor the model's menu is a consideration shifter. It offers branches she wouldn't draw herself, and the hover logs show whether she examined them.

**Repertoire:**
- k-means (k = 50, fixed seed) over P5's vectors of writer-typed sentences;
- a writer's repertoire at a point in time is the set of clusters she typed in earlier sessions;
- each offered suggestion is assigned to its nearest centroid (CONTENT_V2 and P5 come from the same frozen MiniLM);
- a suggestion is out-of-repertoire for her if its cluster is outside her repertoire and at least 10 other writers have typed in it.

**Primary contrast:** within writer, the log-odds of accepting out-of-repertoire minus in-repertoire suggestions. Adjust for:
- the cluster's leave-writer-out acceptance rate (its appeal to others);
- position and length;
- menu dissimilarity;
- her base rate;
- session index.

Direction: negative (branches she never draws stay undrawn, beyond their appeal).

**Extension:** the examination split. Among declined out-of-repertoire suggestions, compare:
- the share never hovered with a short dwell (unexamined, like pruning);
- the share hovered (examined and declined, like dislike);

against the same shares for in-repertoire suggestions. Keep D6's amendment: no hover is not no exposure, so include arrow-key moves through the menu and the first-item auto-highlight.

**Controls:**
- repertoire labels shuffled within writer;
- k = 20 and k = 100 as specifications.

**Prediction:** negative, with the gap mostly unexamined.

**Route:**
- **Gap mostly unexamined:** ToMpathy's "branch never drawn" reading needs process evidence of examination, not absence alone.
- **Gap mostly examined and declined:** absence reads as dislike.

**Cost:** under 1 CPU-hour.

**Variant D32.v1:** repertoire expansion. After she accepts an out-of-repertoire suggestion, does its cluster enter her later typed text more than after a matched in-repertoire accept? Direction: positive. Route: positive, offers widen what she writes; null, an accepted branch stays a one-off.

**Tier 4:** Padmakumar & He's no-model arm gives what writers produce unprompted, for confirmation.

### D33. Surprise against her own past (rank 4, family A)

**Theory.** The curator:
- "What you have attention over is System 2, and System 2 creates System 1 over time."
- An automatic choice runs on her own autocomplete, and "your autocomplete is broken" when it misfires.

If attention engages where her own expectations fail, pauses should track surprise relative to her own history, beyond the crowd's.

The nearest method is LambdaG ([Nini et al. 2026](https://doi.org/10.1057/s41599-025-06340-3)): the likelihood of a text under an author's own grammar against a reference population's. The research pass found no writing study that links language-model surprisal to pauses before words, so this card is new. It doesn't test the agreeable-or-devoted question the curator called untestable.

**Models:**
- **population:** P6's leave-writer-out 3-gram;
- **own:** the population model interpolated with a model of her earlier sessions (a cache of unigrams and bigrams), with its weight tuned chronologically on her calibration sessions.

**Personal surprise** per word = own surprisal minus population surprisal. Negative means her history predicts the word better than the crowd does.

**Primary contrast:** the coefficient of personal surprise on the log pause before the word, measured under TC's rule. Control for population surprisal, word length, log frequency, position, and writer random intercepts. Direction: positive.

**Extension:** replace the 3-gram population model with P7's GPT-2 medium. Does the personal term survive a stronger crowd model?

**Controls:**
- **donor:** an own-model built from another writer's history; the personal term should vanish;
- writer shuffle.

**Prediction:** positive, with the donor control near zero.

**Route:**
- **Positive:** ToMpathy's deviation map scores against the person's own history whenever records exist (a personal deviation map).
- **Null:** the crowd model is enough for pauses.

**Cost:** 1 to 2 CPU-hours.

### D34. Hidden goal or noise (rank 5, family G)

**Theory.** The curator's teardrops: goals emerge mid-work and editors overlay theirs. A reader has to decide whether corrections serve a goal nobody named, or are noise.

Robotics names the problem **hypothesis-space misspecification**: correction learners assume the true objective is among their hypotheses ([Bobu et al. 2020](https://arxiv.org/abs/2002.00941)). The research pass's test: a hidden goal makes the best reader's errors point the same way across sessions; noise doesn't.

**Data:**
- decisions, with the best current reader's predicted probabilities (the Phase 0 backbone now, P4 when it lands);
- content features z: 16 principal components of MiniLM suggestion vectors, fitted on other writers.

**Statistic T1:**
1. For each writer and session, v_ws is the mean over decisions of the residual (accepted minus predicted) times z, centered within session.
2. For each writer, take the mean cosine between her sessions' v_ws.
3. Average over writers.

**Primary contrast:** observed T1 minus its null mean. The null permutes residuals within writer × session × predicted-probability decile, 1,000 times. Direction: positive.

**Extension:** the same with P4's predictions. A real hidden goal survives a better reader.

**Variants reported beside the primary:**
- z replaced by position and time features (session state);
- z replaced by the reader's own features (wrong functional form).

**Verdicts, exhaustive:**
- **HIDDEN GOAL:** content beats both variants, and a direction fitted without her last session predicts that session's residual signs above chance.
- **STATE OR MISFIT:** only a variant fires.
- **NOISE AT THIS POWER:** null, while T1 detects V4's planted taste at δ = 0.4 in at least 4 of 5 worlds.
- **UNDETERMINED:** everything else.

**Positive control:** T1 on 5 of V4's taste worlds at δ = 0.4 (V1's taste worlds if V4 hasn't landed).

**Route:**
- **Hidden goal:** ToMpathy adds a probe line, "something unexplained points this way", with the direction's top examples.
- **Noise:** the engine's residuals display as noise bands.

**Cost:** 1 CPU-hour.

**Variant D34.v1, T2 cohesion:**
- "Unexplained" corrections are those above the 80th percentile of surprisal simulated from the reader itself.
- Primary contrast: the cross-session cosine among a writer's unexplained corrections (P5 edit vectors), minus count-matched explained ones. Direction: positive.
- Control: other writers' unexplained corrections.

### D35. Do corrections become defaults? (rank 3, family A)

**Theory.** The curator: "What you have attention over is System 2, and System 2 creates System 1 over time."

Research names two routes for automatization:
- retrieving stored past solutions ([Logan 1988](https://doi.org/10.1037/0033-295X.95.4.492));
- compiling slow rules into fast ones ([Anderson 1982](https://doi.org/10.1037/0033-295X.89.4.369)).

Current usage says Type 2 and Type 1 ([Evans & Stanovich 2013](https://doi.org/10.1177/1745691612460685)). A writer's content corrections are attended choices. If they compile, her later unattended text drifts the way her corrections pushed it.

**Data:**
- content corrections: accept-then-edit, and edits to her own typed spans, that meet D4's content threshold (MiniLM cosine distance of at least 0.15 between before and after, or a clause added or removed; section 6);
- writer-typed sentences.

**Direction d_w:** the mean unit vector of (after minus before) P5 embeddings over her content corrections in the odd-numbered sessions of the first half of her sessions (chronological), residualized on prompt means.

**Primary contrast:** the change in the mean projection of her typed sentences on d_w, from the even-numbered sessions of her first half to her second half, minus the same change on other writers' directions (averaged over donors). Residualize on prompt. Direction: positive.
- Every sentence any content correction touched is excluded from both halves.
- Why the split and the exclusion: corrections pick out text that was off her course, so a baseline from the same sessions would let regression to the mean make the contrast positive on its own.

**Extension:** the rate of new corrections along d_w (cosine above 0.5), second half against the even first-half sessions. Direction: negative: what was corrected stops needing correction.

**Eligibility:** writers with at least 4 sessions, and at least 5 content corrections in the odd sessions of their first half.

**Controls:**
- shuffled directions;
- donor directions;
- prompt fixed effects;
- the share of accepted model text as a covariate, because suggestion uptake also moves her style.

**Route:**
- **Positive:** ToMpathy's process panel can show "corrections that became habits".
- **Null:** corrections stay local fixes at this scale.

**Cost:** under 1 CPU-hour.

### D36. Beauty as fast resolution: jokes (rank 28, family S, exploratory)

**Theory.** The curator: "Interest is disassembly, and beauty is the rapid disassembly."

The research homes:
- **the Aesthetic Aha:** insight and its intensity predict gains in liking ([Muth & Carbon 2013](https://doi.org/10.1016/j.actpsy.2013.05.001));
- **insight as a sudden gain in fluency** ([Topolinski & Reber 2010](https://doi.org/10.1177/0963721410388803));
- **compression progress** ([Schmidhuber 2009](https://doi.org/10.1007/978-3-642-02565-5_4)). Schmidhuber puts beauty on compressibility and interest on progress; the curator puts beauty on fast progress.

The research pass found no study of resolution speed against beauty. Jokes are the everyday case of sudden resolution.

**Data:** Jester's 150 jokes, with mean ratings. rJokes as the variant, if intake allows.

**Setup and punchline:** the punchline is the joke's final sentence; the setup is everything before it. One-sentence jokes are excluded.

**Measures,** from P7's GPT-2 medium:
- **resolution gain:** mean surprisal of the setup read alone, minus the setup re-read after setup plus punchline, minus the same quantity with another joke's punchline (a mismatched control);
- **rate:** resolution gain per punchline token.

**Primary contrast:** the correlation across jokes between mean rating and rate. Direction: positive.

**Extension:** a partial correlation, controlling punchline surprisal and length. Is it resolution, or just surprise?

**Route:**
- **Positive:** "beauty as fast resolution" gets its first measured hook.
- **Null:** the claim stays untested at this resolution; nothing else changes.

**Cost:** under 1 CPU-hour, plus the intake.

**Variant D36.v1:** do Jester users differ reliably in how much rate predicts their ratings? Random slopes; primary = the split-half reliability (odd and even jokes) of users' slopes. Direction: positive. This is personal taste in the aesthetic itself.

### D37. Three entries: the page, the person, the process (rank 23, family E)

**Theory.** The curator restated the triple inference as "one big inference of empathy" with three entries:
1. functional reverse engineering from the top;
2. the person;
3. the process.

The research homes:
- Bayesian theory of mind is one joint inference over hidden causes ([Baker et al. 2017](https://doi.org/10.1038/s41562-017-0064));
- the goal-first entry is the teleological stance ([Gergely & Csibra 2003](https://doi.org/10.1016/S1364-6613(03)00128-1)), together with anchoring on oneself ([Epley et al. 2004](https://doi.org/10.1037/0022-3514.87.3.327)).

The research pass found no model of inference from artifacts with these three entries, so this is a first measurement, on the one task we can score: the next handling decision.

**Entries:**
- **page:** P4's content features, meaning what the work so far calls for;
- **person:** writer effects and her handling history, with V3's reliabilities as priors;
- **process:** timing and interaction state before the decision: D17's pause shares, request latency, hovers before this menu, recent editing.

**Readers:** each entry alone, and all three stacked, with weights learned on the calibration split (reliability weighting). EXECUTION.md's chronological 60/20/20 split.

**Primary contrast:** half-Brier of the best single entry (chosen on the calibration split) minus that of the stacked reader, on the scoring split. Half-Brier is a loss, so a stack that beats every single entry gives a positive number. Direction: positive (the joint inference beats any one entry).

**Extension:** the stack's weights by how many sessions she has so far. The curator's account predicts the page entry leads early, and the person and process entries gain with records.

**Report:** as a share of V5's headroom.

**Caveat:** handling prediction is a proxy for what empathy infers.

**Route:** sets the reliability weights for ToMpathy's three-entry design.

**Cost:** 1 CPU-hour.

### D38. One bad accept: how wide does avoidance spread? (rank 17, family B, exploratory)

**Theory.** The curator: fear blurs discrimination because it is "an incredibly highly weighted one-shot experience", while expertise sharpens it.

The research supports him, with qualifications.
- Stronger threats widen fear generalization gradients, with no change in initial learning ([Dunsmoor et al. 2017](https://doi.org/10.1037/bne0000186)).
- Expertise is perceptual differentiation ([Goldstone 1998](https://doi.org/10.1146/annurev.psych.49.1.585)).

Two findings cut the other way:
- broad generalization from one example is ordinary Bayesian behavior, not special to fear ([Tenenbaum & Griffiths 2001](https://doi.org/10.1017/S0140525X01000061));
- aversive learning sharpened discrimination in one study ([Li et al. 2008](https://doi.org/10.1126/science.1152837)).

CoAuthor holds a mild analog: a writer deletes a suggestion she had accepted. That is a one-shot bad outcome, not fear. The card measures the shape of what follows, and says no more.

**Events:**
- **model failure:** deletion of at least 80% of a previously accepted suggestion's characters;
- **own failure** (control): deletion of her own typed span, of matched length.

**Drop:** offered suggestions fall into terciles by MiniLM distance to the deleted span. For each tercile, the drop is her acceptance over the 10 menus before the event minus over the 10 menus after it, in the same session, leaving out the menu where the deleted suggestion was accepted. An event needs at least 5 menus on each side.

**Gradient:** the near-tercile drop minus the far-tercile drop.

**Primary contrast:** the gradient after model failures in her later sessions (second half), minus the same in her earlier sessions. Direction: positive (sharper with experience).

**Extension:** model failure minus own failure, in the overall acceptance drop. Direction: positive; this is the trust half, which D39 takes further.

**Route:**
- **Positive:** a first hook for "expertise sharpens".
- **Flat in both halves:** one bad outcome generalizes broadly in writing, which says nothing about fear.

**Cost:** under 1 CPU-hour.

### D39. Trust sets attention: checking after a bad suggestion (rank 7, family A)

**Theory.** The curator: "attention is deciding to run an inference on whether to trust in a given specific setting."

The research terms:
- **precision weighting:** attention as the estimated reliability of a signal ([Feldman & Friston 2010](https://doi.org/10.3389/fnhum.2010.00215));
- **trust calibration:** in work on people using automation, trust sets how much people rely on a system and how often they check it ([Lee & See 2004](https://doi.org/10.1518/hfes.46.1.50_30392)).

If her trust in the model drops when it fails, she should examine its next offers harder.

**Events:** as in D38, model failures against own failures.

**Outcomes** on the next menu, from menu-event timestamps (TC's rule doesn't apply):
- hovers per menu;
- time from menu open to decision.

**Primary contrast:** within writer, hovers on the first menu after a model failure minus after an own failure. Direction: positive.

**Extension:** the decay of that difference over the next 5 menus. Direction: falling (trust recovers).

**Controls:**
- matched on time since the last request and on session index;
- writer shuffle.

**Route:**
- **Positive:** ToMpathy's attention panel can say attention follows trust: checking rises after the source fails.
- **Null:** hovers don't track trust here.

**Cost:** under 1 CPU-hour.

### FX1. The falsifier (Tier 4, frozen now, not run in this campaign)

Write it now, hash it, and leave it.

**The claim at risk:** inferring goals from a writer's records predicts that writer better than the same records without a goal model.

**Split:** 5-fold by writer. Within each held-out writer, sessions in time order: the first half are records, the second half are targets.

**Readers,** with matched records, features and tuning budget:
- R0: pooled;
- R1: records, no goal latent;
- R2: records plus inferred goals.

**Gain and margin:**
- G = Brier(R1) − Brier(R2);
- m = 0.10 × (Brier(R1) − the personal floor from V5), registered before unblinding.

**Verdicts:**
- **FALSIFIED** only if G's upper bound is below m and every precondition holds.
- **SUPPORTED** if G's lower bound is above 0 and Ĝ ≥ m.
- **INCONCLUSIVE** otherwise, naming the failed bound or precondition.

**Preconditions:**
- **P1:** headroom H's lower bound is above 0.
- **P2:** Brier(R1) sits above the floor.
- **P3:** on twins of these writers with goals planted so the oracle gain equals m, G's lower bound clears 0 in at least 13 of 16 law blocks at goal strength m with 81 records per writer, and 0 of 16 habit-only blocks return SUPPORTED. Ghost's N13 builds this, in Ghost's conditional-study form (16 law blocks of 64 cases).
- **P4:** R1 at least matches R0.
- **P5:** the theory names goal-bearing decision types in advance.

**Status:** P3 fails today, since V1 saw no taste or habit. A FAIL now would indict the pipeline, not the framework.

**When it runs:** after the talk, when V4 sees, a goal reader exists, and N13 passes.

**Data:** the Padmakumar & He holdout and fresh CoAuthor folds.

## 6. Carried cards: primary contrasts and changes

Methods stay as in the 16 October packet, with EXECUTION.md's amendments. This table supplies what each batch plan row needs, so no card waits on design work. "Ext." is the one frozen extension.

| Card | Primary contrast (direction) | Ext. | Changes from 16 October |
|---|---|---|---|
| D2 | Content choice model's log-loss gain over uniform, most dissimilar quintile minus most similar (positive) | The hierarchical multinomial logit's between-writer coefficient spread, with interval (positive) | No P1 dependency; uses P8. Read the spread against V4's label |
| D3 | Reversal rate (accepted span later deleted or at least half edited) in the shortest within-writer latency quintile minus the middle quintile (positive; the curator's flow account) | Longest minus middle (positive; the near-tie account) | None |
| D4 | Gain in later-choice half-Brier from projecting on pooled content-correction directions, minus the same from housekeeping corrections (positive) | D4b: edits move toward her own earlier typed style (positive) | Runs now on the deterministic split, frozen here. **Housekeeping:** a change of at most 3 characters (Levenshtein) within one word, or punctuation only. **Content:** MiniLM cosine distance of at least 0.15 between before and after, or a clause added or removed (a change in spaCy's count of finite verbs). Anything else is left out of both. P3's intents join when they land. **Corrections are soft votes with slack, not hard half-spaces**: Ghost's N3 showed hard constraints empty the hypothesis set |
| D5 | Slope of rank-1 writer identification from her own typed text, length-matched, across model-share bins (negative) | The same slope for the selection and timing channel (flat) | None |
| D6 | Hover probability at slot 1 minus slot 5 (positive: examination falls with position) | Shrinkage of the content coefficient when examination is modeled (positive) | Amendment kept: audit arrow-key moves and the first-item auto-highlight first; no hover is not no exposure |
| D7 | Gain of the dwell model with an information term over preference alone (positive) | As F11, 14 October | None |
| D9 | Pooling curve: individual prediction at 10 own records minus 0 (positive) | Rank-1 identification from choices alone, above chance | Runs on DICES and Community Alignment now; D10's embeddings join later |
| D11 | Population coefficient of own-fit (P5 similarity of the suggestion to her earlier typed text) on acceptance (positive) | Between-writer slope spread (positive) | No P1 dependency |
| D12 | Split-half (odd and even sessions) correlation of each writer's mean standardized logged probability of chosen minus menu mean (positive) | The same with P1's local readers | Uses P8 (section 4.1). The primary runs now; only the P1 extension waits |
| D13 | Quadratic coefficient of acceptance on per-token surprisal at c3, within writer (negative: an inverted U) | Acceptance on surprisal relative to her recent text, at fixed raw surprisal (negative: "easier than expected") | After P1's main; the expectation term uses typed P1, or P7's GPT-2 medium as the fallback |
| D14 | Population slope of dismiss-or-edit on topic drift beyond D1's features (positive) | Restoration: an edit after accepting moves topic drift back (positive) | No P3 dependency. Literal features join only if G3-A runs |
| D15 | Split-half reliability of fine-grained writer dissimilarities (context-conditional residuals) minus coarse ones (handling rates) (positive) | None needed | Uses P8 |
| D16 | Equal error rate from outcomes alone minus from process features (positive) | Decision latency alone below 50% equal error rate (the cognitive check) | After D17, D15 and V3; uses P8 |
| D17 | Writer ICC of the slowest (reflective) between-word mixing weight across sessions (positive: lower bound above 0). Each interval is first divided by the writer's median within-word interval in that session, and the component distributions are shared on that scale, so typing speed alone can't make writers differ | The same between sentences | **Revised for the curator's "different boxes"**: first choose the number of components per location by BIC, following [Hall, Baaijen & Galbraith 2022](https://doi.org/10.1007/s11145-022-10284-4) (three between words: lexical, supra-lexical, reflective). The research pass found no test of whether those weights are stable per writer, so this is new. TC runs first. KLiCKe has one session per writer, so it serves only the choice of the number of components |
| D18 | Split-half reliability of each writer's prompt-fit sacrifice rate (deleted spans that fit the prompt less than surviving ones) (positive) | Fluency sacrifice, after P1 | The prompt-fit primary runs now (rank 19); only the fluency extension waits for P1 |
| D19 | Split-half reliability of writer loadings on components stable across bootstraps (positive) | None needed | None |
| D20 | Overlap of a dismissed suggestion with her next 50 typed words minus the permutation baseline (positive) | Between-writer reliability of that uptake | Uses P5 |
| D21 | Kendall's τ between readers' within-menu rankings at c3 minus c0 (positive) | Agreement slope along the Pythia size ladder | After P1's main |
| D22 | Share of higher-order intents on edits to model spans minus her own spans, matched for length and position (positive) | Restoration on D14's variables | After P3 |
| D23 | Within writer, requests per 100 words in her first session on a prompt minus her repeats (positive) | Decline across session order | Reader-based measures (D12, D13) join after P1 |
| D24 | Discontinuity at the timer in the closure content of accepted suggestions (positive) | Window-width sensitivity | None |
| D27 | Writer-identity AUC from final text over the prompt-only baseline (positive) | Each process target's improvement over its baseline | Report improvements over each baseline, never ratios (EXECUTION.md) |
| D28 | Hover switches per menu, least dissimilar quintile minus most (positive: more alternation on near-ties) | Alternation predicts later reversal (positive) | The primary runs now on CONTENT_V2's dissimilarity (rank 15); reader spread joins as a second near-tie measure after P1 |
| D29 | Split-half reliability of each writer's final length (positive) | Bunching just past the timer | None |
| V3 | ICC of handling, with interval, and the decisions needed for 0.8 reliability, per feature (positive) | None needed | Feeds D16 and D37 |
| P4/D1 | Half-Brier gain over the backbone (positive), with whether it reaches 0.01 | Added gain from partially pooled writer offsets (expected under 0.01) | P4's freeze gates G3-A's first look |
| D8 | Intent accuracy from summary alone minus diff alone, in the smallest diff tercile (positive) | Next-intent prediction from editor history | After its labels are fetched |
| D23b | Opening novelty after win streaks minus after loss streaks (positive) | Rating above against below her recent mean | After the parser |

## 7. Gear 3

Campaign `G3-S15-DRIVE-1` continues: 4 cents spent; the first $10 is authorized; nothing past $10 runs without the curator's detailed final approval, which the route enforces in code. Prices as checked 16 October (Anthropic batch, per million tokens): Claude Haiku 5.5 $0.05 input, $0.25 output. A0's reconciled 4 cents matches them. Count deduplicated inputs before each reservation.

| Node | What it buys | Rungs | Forecast | Cap |
|---|---|---|---|---|
| A0 | Done | | 4 cents | $1 |
| **K** (new) | D31's fiction labels, then D31.v1's CoAuthor story labels if D31.v1 is dispatched | Known-answer rung first (D31's 100 blind agent labels; κ thresholds there). Labels are inputs, not forecasts, so no futility looks | about $1.50 | $5 |
| **P** (new) | Second labeler for P3's edit intents: the 200 calibration pairs first, then about 5,000 content-correction pairs (D4's content class; a sample of 5,000 with seed 20261017 if there are more) | Known-answer: κ of at least 0.6 on meaning-changed against not, against the agent labels | about $0.40 | $2 |
| A, first look only | Haiku literal features (Q1, Q3, Q5, Q6, Q8, Q9, the questions A0 passed) for D14, D22, D1 and D4 | Only if P4 is frozen before Monday 12:00 PDT. The 20% look and its futility stop as on 16 October; stopping or continuing past it needs the final approval | about $3.70 | first look only |
| B | Deferred to the post-talk campaign, unless the past-$10 request below includes it | | | |
| D | Deferred: needs the S0-T2 parser and Maia-2 | | | |
| F | **Dropped.** Local Qwen 3.5 9B and Llama 3.2 3B already pass constructed Q4 and Q7; they run locally when the GPU is free, if any card still needs tone or contradiction | | | |
| Reserve | Unchanged: unusable without a reviewed recovery plan | | | $5 |

**Order inside the first $10:** K, then P, then A's first look only if booked spend plus A's reservation stays at or under $10. Forecast total: about $5.64.

**Code changes:**
- add nodes K and P to `runners/drive/budget.py` with the caps above;
- write `.agent-state/drive-20261017/APPROVAL.json` holding the curator's handoff message, this packet's SHA-256, and the approved nodes (K, P, and A's first look). `guard()` refuses any node the file doesn't name, so a later approval adds nodes by writing a new file, never by editing code;
- remove F;
- keep the 6,000-cent gross ceiling and the 1,000-cent first-tranche refusal;
- `max_tokens` 32, thinking off;
- reservations before every POST; no automatic resubmission.

**The past-$10 request.** Ruling 7 gates material spend behind explicit positive results, so a node's extension is requested only behind that node's own positive result. Submit it within 2 hours of the result, and no later than Monday 19 October, 12:00 PDT. It carries what the stone rule requires: exact commands, wall-clock per node, test details, total dollars, and its hash. Pre-scoped extensions:
- **K on 40 more authors, about $1.50:** only if D31 lands positive.
- **A's remaining run, about $14.80 more** (A totals $18.50, inside its $20 node cap): only if A's first look clears its futility stop and P4/D1 lands positive on the free path.
- **B's 1% slice, $3.40:** only if A runs in full.

The ceiling requested is $26 for the campaign: the first tranche's forecast of $5.64 plus $19.70 of extensions, rounded up. The paid dispatch cutoff stays Monday 19 October, 17:00 PDT, in code.

## 8. Cross-repository deliveries

**To Ghost Scale,** as aggregates through `docs/exchange` notes:
- at the first digest after V5 lands: V5's curves (A_w, A_b, both floors, H), for Ghost's N13;
- at the first digest after P5 and D4's split land: content corrections per writer, for Ghost's N10;
- at the first digest after D34.v1 lands, if it runs: the unexplained-correction rate, for Ghost's N10 (Ghost uses its own noise levels until then);
- D30's counts of pervasive and local markers per writer, for Ghost's N14;
- S0-T2: not this round. Ghost records T2 as blocked at its freeze.

**From Ghost:** N13 validates FX1's precondition P3, with the rates FX1 states (13 of 16 law blocks; 0 of 16 habit-only blocks). FX1 stays frozen either way.

**To ToMpathy,** at the digests, as plain-language result notes with numbers:
- D30's split rule;
- V5's ceiling, for its consistency display;
- D33, for the personal deviation map;
- D38 and D39, for the attention panel's trust copy;
- D37's weights;
- D17's boxes;
- D21 and D27, after P1.

**Pin.** Sounding Line keeps ToMpathy pinned at `82789fd` through the campaign. Re-pin at the Tuesday digest only if ToMpathy's commit tagged `certified-fit-1` (its question-gate and convergence fixes) has landed with its tests passing. Sounding Line's own F4 receipts can't be reused by the engine, because their pins differ; ToMpathy reruns its batteries under its own backend.

## 9. Schedule (PDT)

| When | Sounding Line | Gear 3 |
|---|---|---|
| **Sat 17, kickoff** | Section 2 changes (2-hour box). Batch plan W1: Tier 0, the passes P4 to P8, and ranks 1 to 12. Intakes start | K's known-answer rung, then K |
| **Sat evening** | Wave 2 (ranks 13 to 32) as slots free; variants are registered on nulls | P's known-answer rung |
| **Sat 20:00** | Digest 1 | |
| **Sat about 22:45** | P1's main ends; verify it independently. GPU: P3's classifier, typed P1 (boxed), D10 | |
| **Sun 18** | Tier 1b; D37 and D16; texture on positives. 20:00 digest 2 | A's first look once P4 is frozen; a past-$10 request within 2 hours of any qualifying positive |
| **Mon 19** | Ladders and texture. 20:00 digest 3 | 12:00: last moment for a past-$10 request. 17:00: paid dispatch cutoff |
| **Tue 20** | By 18:00: one plain-language page for the talk: what we can say Thursday, with numbers and intervals | Close and reconcile |
| **Wed 21** | No new starts after 06:00; running work drains by 12:00; restore `transition_only: true`. The machine goes to ToMpathy's rehearsal | |

## 10. Authorization (in force at handoff)

1. **Operating changes:** section 2, rows 1 to 12, for this campaign, including delegation to up to three builders and up to N CPU slots.
2. **Cards:** every card and pass in sections 4 to 6, at Gear 2, descriptive, on data held or freely downloadable:
   - CoAuthor;
   - ScholaWrite;
   - DICES and Community Alignment;
   - the Gutenberg sample;
   - Jester;
   - rJokes, if intake policy allows;
   - KLiCKe;
   - Padmakumar & He's logs, as a locked holdout;
   - the Yang et al. labels;
   - the Lichess month.

   S0-T4-104 is closed; D24b moves to the post-talk campaign.
3. **Gear 3:** nodes K and P, and A's first look, inside the first $10, as section 7 says, each named in the approval file section 7 writes. G3-F is dropped; B and D are deferred.
4. **Return triggers.** Come back to the curator only for:
   - (a) the past-$10 request;
   - (b) a stone rule blocking a card this packet requires. Record it, skip the card, report it in the digest, and don't wait for an answer.

   Everything else is decided in this packet.
5. **Data transfer.** On top of 16 October's section 8, the curator accepts sending these to the Anthropic API:
   - CoAuthor story passages, for K's D31.v1;
   - CoAuthor edit before-and-after pairs, for P.

   Gutenberg text is public domain. No raw text appears in public outputs.

## 11. Pre-mortem

| Failure | Guard |
|---|---|
| More CPU slots slow P1's main or Ghost | Below-normal priority and slots sized to the core count. Each health compares P1's rate with its forecast; if it falls more than 20% after slots open, drop one slot |
| ToMpathy's battery reruns take CPU or GPU from cards | CPU: at most 2 threads, below-normal priority, one of the N slots. GPU: one locked session that unloads before release, only when the section 4.2 GPU queue is empty |
| Six nulls stop a family whose lens is blind | V4's label sits on every taste and habit result and on a stopped family's INDEX line, so a stop under a blind lens reads as an instrument limit, not a finding |
| Forty cards, shallow work, many false positives | One frozen primary contrast each; screen-level q-values; three positive and three negative controls per digest; texture before any claim; nothing promoted |
| Pauses are artifacts of delta logging | TC decides, before any timing card runs |
| Frequency poses as automaticity (D30) | The extension adds her own count; first against later occurrences |
| Prompt conventions pose as habits | Markers are defined against the same prompts; "local" requires low consensus |
| A deliberate global policy reads as autocomplete | D30 tests the automaticity half (speed, revision) separately from where the choice sits |
| Genre conventions pose as authors (D31) | Genre × decade blocks, a consensus baseline, restricted permutations |
| Label noise tracks the author (D31) | Known-answer labels spread over at least 30 authors; error checked across authors |
| Hovers read as reading (D32, D39) | D6's amendment; "examination", never "attention", in the write-up |
| D38's mild analog read as evidence about fear | The exploratory label, and the card says what it isn't |
| V4's plants don't resemble real taste | The representation mismatch is deliberate; R-oracle separates information from detection |
| Batched landing loses a result | Card files and INDEX lines land at once; the digest follows within 24 hours |
| Builders collide | Separate files per card; only the owner merges, lands and commits |
| The holdout gets spent | Padmakumar & He: schema census only; outcome fields hashed and unread until Tier 4 |
| Theory rows lag a day | The digest updates rows the same evening |

## Sources

**Repositories read 17 October.**
- **Sounding Line `6c063f5cd`:**
  - `AGENTS.md` (section A, waiting override, six-hour health, delegation);
  - `docs/CODEX_OPERATIONS.md` (`transition_only`, planned wakes);
  - `docs/design/stage-15/drive/EXECUTION.md`;
  - `REGISTRY.json`;
  - `runners/drive/budget.py`;
  - `runners/next_round/queue.py`;
  - `tools/design_lint.py`;
  - `results/phase_2_4_stage_15/DRIVE/`.
- **Ghost Scale `6162cc1af`:** `ADDENDUM_IMPLEMENTATION_2026-10-16.md` (three workers, Sounding Line priority).

**Attribution and habit:**
- [Kelley 1973](https://doi.org/10.1037/h0034225); [McArthur 1972](https://doi.org/10.1037/h0032602)
- [Monroe, Colaresi & Quinn 2008](https://doi.org/10.1093/pan/mpn018)
- [Wood & Neal 2007](https://doi.org/10.1037/0033-295X.114.4.843)
- [Poe 1846](https://www.eapoe.org/works/essays/philcomp.htm)
- [Kestemont 2014](https://doi.org/10.3115/v1/W14-0908)
- [Bamman, Underwood & Smith 2014](https://doi.org/10.3115/v1/P14-1035)
- [Nakagawa & Schielzeth 2010](https://doi.org/10.1111/j.1469-185X.2010.00141.x)
- [Winkler et al. 2014](https://doi.org/10.1016/j.neuroimage.2014.01.060)
- [Gerlach & Font-Clos 2020](https://doi.org/10.3390/e22010126)

**Consideration and attention:**
- [Masatlioglu, Nakajima & Ozbay 2012](https://doi.org/10.1257/aer.102.5.2183)
- [Cattaneo et al. 2020](https://doi.org/10.1086/706861)
- [Goeree 2008](https://doi.org/10.3982/ECTA4158)
- [Feldman & Friston 2010](https://doi.org/10.3389/fnhum.2010.00215)
- [Lee & See 2004](https://doi.org/10.1518/hfes.46.1.50_30392)

**Habit, automaticity and dual process:**
- [Miller, Shenhav & Ludvig 2019](https://doi.org/10.1037/rev0000120)
- [Logan 1988](https://doi.org/10.1037/0033-295X.95.4.492)
- [Anderson 1982](https://doi.org/10.1037/0033-295X.89.4.369)
- [Evans & Stanovich 2013](https://doi.org/10.1177/1745691612460685)

**Fear and generalization:**
- [Dunsmoor et al. 2017](https://doi.org/10.1037/bne0000186)
- [Tenenbaum & Griffiths 2001](https://doi.org/10.1017/S0140525X01000061)
- [Li et al. 2008](https://doi.org/10.1126/science.1152837)
- [Goldstone 1998](https://doi.org/10.1146/annurev.psych.49.1.585)

**Writing process:**
- [Hall, Baaijen & Galbraith 2022](https://doi.org/10.1007/s11145-022-10284-4)
- [Nini et al. 2026](https://doi.org/10.1057/s41599-025-06340-3)
- [Padmakumar & He 2024](https://arxiv.org/abs/2309.05196)
- [Tian, Crossley & Van Waes 2025](https://doi.org/10.17239/jowr-2025.17.01.02)

**Aesthetics:**
- [Muth & Carbon 2013](https://doi.org/10.1016/j.actpsy.2013.05.001)
- [Topolinski & Reber 2010](https://doi.org/10.1177/0963721410388803)
- [Schmidhuber 2009](https://doi.org/10.1007/978-3-642-02565-5_4)
- [Goldberg et al. 2001](https://doi.org/10.1023/A:1011419012209)

**Theory of mind:**
- [Baker et al. 2017](https://doi.org/10.1038/s41562-017-0064)
- [Gergely & Csibra 2003](https://doi.org/10.1016/S1364-6613(03)00128-1)
- [Epley et al. 2004](https://doi.org/10.1037/0022-3514.87.3.327)

**Ceilings, hidden goals and screening:**
- [Park et al.](https://arxiv.org/abs/2411.10109); [Toubia et al., Twin-2K-500](https://arxiv.org/abs/2505.17479)
- [Fudenberg et al. 2022](https://doi.org/10.1086/718371)
- [Bobu et al. 2020](https://arxiv.org/abs/2002.00941)
- [Self & Liang 1987](https://doi.org/10.1080/01621459.1987.10478472)
- [Simonsohn, Simmons & Nelson 2020](https://doi.org/10.1038/s41562-020-0912-z)
