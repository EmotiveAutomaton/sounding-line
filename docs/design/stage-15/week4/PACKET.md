# Sounding Line, Stage 15, week 4 (2 to 8 November): from steps to the top

*Spec sheet for the Sounding Line agent. It runs from handoff to Sunday 8 November, 22:00 PST (2026-11-09T06:00Z). Every decision is made here. Return to the curator only on the triggers in section 10.*

**What this week is for.** The curator's walk of 1 November named the program's critical issue: readers recover the bottom of a writer's hierarchy (who she is; whether she's drafting or revising) and not the top (her higher-order goals). This week attacks the top from four directions, all on real records:
- **System 2 markers inside the process record:** stops before planning, flow as compiled expertise, global revision, moves away from the leading edge (family S);
- **the top of the hierarchy itself:** plan roles of sentences, reading the process from the finished text, personal chunk libraries learned from steps, choices among offers read at each writer's own competence, plans inferred with a language model's expertise and checked against her later choices, and texts with planted goals as a known-answer test bed (family T);
- **value data with error bars,** which the curator calls the first step (family V);
- **the bottom layer the rest needs:** a provenance-tagged event record, a repair for the shared extractor, and sample routes for the cost-held cards whose floor fits (family R; section 6 runs the rest in idle slots).

**Lessons this packet is built on** (week 3):
- About 98% of research slot-hours sat idle from 27 to 29 October, and the ready buffer never reached eight cards. Causes: full-corpus process cards projected 10 to 17 times their caps with no route to a frozen sample (the packet's rule), one shared extractor blocked four cards, and replacement cards were built one at a time. Amendment E and section 6's idle-slot allowance address the first, amendment G the third, and R1 the second.
- The paid campaign spent 1 cent of $10, because a repair waited mid-week for a further transfer approval. Amendment H moves every approval to handoff.
- The week 3 identification reference built by leaving the writer out was flawed; the three-role independent-donor control (WA0.h1) is now the standard (section 0.4).

## 0. How to run this

### 0.1 Window

- This packet opens a new window at handoff, in a new runtime version; if `transition_only` is restored, clear it at handoff. Clocks changed on 1 November; times are in UTC:
  - no new starts after Sunday 8 November, 20:00 PST (2026-11-09T04:00Z);
  - drain by 22:00 PST (2026-11-09T06:00Z), then restore `transition_only: true`.
- Stage 15 continues; this is its week 4. Results go to `results/phase_2_4_stage_15/`, designs to `docs/design/stage-15/week4/`, and this packet to `docs/design/stage-15/week4/PACKET.md`.

### 0.2 Rules in force

Everything in force at the end of week 3 stays: section 2 of the 17 October packet; the 18 October mid-run errata as week 3 amended them; standing decisions S1 to S7; the stone rules (Gear 3 per-use approval and the $10 ceiling enforced in code, material spend only behind positive results, hash-locked files, no author contact, privacy, a null that can fail every measure, every result descriptive); and the standing amendments of 25 October (A never idle, B automatic healing, C automatic follow-ups, D the claim ledger). Section 0.3 adds four.

### 0.3 Standing amendments, 2 November (permanent)

Write these at handoff into `AGENTS.md` and `.agents/skills/grind/SKILL.md`, in a section headed "Standing amendments, 2 November", beside the 25 October section.

**E. Cost overruns get a sample route.** This amends standing decision S4 and amendment B's cost line.
- If a card's cost probe projects more than twice its ceiling:
  1. run a **frozen sample**: whole writers (or whole annotators, raters or projects, by the card's unit), drawn with seed 20261102, stratified by each writer's majority genre where the card analyses genres, sized from the probe to fit twice the card's ceiling less what the card has already been charged (standing decision S4's limit);
  2. report it as **sample-scoped**, with its size and its share of the full population, using the verb rules of amendment D;
  3. queue the full run in section 6's backlog for idle slots;
  4. if even the card's declared floor doesn't fit (default: 20 CoAuthor writers, 200 Community Alignment annotators, all 123 DICES raters, all ScholaWrite identities), record it cost-held, as before.
- A sample run is neither a heal nor a new hypothesis. It inherits the card's estimand, controls and route, at sample scope.
- A cheaper exact implementation remains welcome; it no longer has to come first.
- For sample-scoped runs only, this supersedes any record that forbids a reduced population (D33's follow-ups and CA1 among them); full-population records stay.

**F. Design pre-mortem before admission.** Every card records two lines before its first draw:
1. **The case and its check.** The situation the question is about, and the check that these data can produce it: a support count, a planted-recovery check, or a structural argument. A card whose data can't produce its case is recorded **"design cannot test"**, with the reason and the numbers. It isn't a null, and it gets no `.ic`.
2. **The smaller route.** What the card runs if it costs too much (normally amendment E's sample).

**G. The texture lane builds the ready buffer.** While fewer than two ready cards per counted slot exist:
- the owner builds **texture cards**: declared variants of landed or running cards (another threshold, genre, population or specification), each frozen before outcomes, capped at 1 CPU-hour, ranked below this packet's cards;
- texture results are descriptive and never upgrade a claim; they register no follow-ups;
- a family's texture lane stops after five consecutive texture cards in which no texture estimate differs from its parent card's estimate by more than half the parent's 95% interval width;
- section 2 lists each family's texture grid.

**H. One paid approval, at handoff.** Before any paid call, the owner sends the curator one request covering every node in section 5: each node's payload, destination, rung, cap, and one recorded prompt fix with its rerun. His words go verbatim into the approval file. No node waits mid-week for a further approval inside that list. If he declines a node, it is blocked under standing decision S6, naming it.

### 0.4 Identification controls

- **Every identification claim** uses the three-role independent-donor reference that WA0.h1 introduced and the curator approved: donor, probe and gallery writers in separate roles, the context reference built from donors only, 1,000 conditional reassignments and 2,000 paired probe-writer resamples. A pass needs its permutation p below 0.05 and real minus context-only accuracy with its interval above zero.
- The literal leave-writer-out reference stays diagnostic only. It licenses no badge.
- The same rule applies to annotators in Community Alignment and raters in DICES, with the item or prompt cluster as context.

### 0.5 Defaults

Unless a card says otherwise:
- week 3's defaults (one primary contrast with its direction; writer-cluster 95% intervals from 2,000 resamples; at least 200 within-writer permutations; choices from P2's canonical choices (the replayed record of which offer was actually inserted), never the logged selection field);
- seed 20261102;
- **within-writer timing controls:** word length, population word frequency, the writer's own frequency, sentence and paragraph boundary, the writer's own median interval for the same letter pair (bigram typing difficulty), time on task and session order;
- **hesitation** is the posterior of the middle (slow) component of a three-component lognormal mixture fitted to each writer's own intervals, each divided by her within-word geometric median after PP1's mechanical correction (initialised as in `runners/drive/cards/week3_pause_model.py`; fluent-plus-hesitant mixtures follow Roeser et al. 2024, who fitted two components; the very long third follows D17). This per-writer fit is new: PP1 and D17, the earlier timing-mixture card, pooled their components across writers, and PP1's own runs keep its pooled fit. The slowest component isn't read as disengagement: in D17's pooled fit it held a fifth of ordinary word onsets. A **hesitant interval** (a stop) is a word onset whose fluent (fastest) posterior is below 0.5, so a long pause counts as one; intervals inside a word don't count as stops. A stretch of writer-typed text (a window or a sentence) is classed by its **hesitancy**: the mean, over its word onsets (the interval before each word's first character, its first word's onset excluded), of one minus the fluent posterior. Within each writer and kind of stretch, her lowest third by hesitancy is **flow** (the routes' flow runs) and her highest third **hesitant**, the middle third reported separately; a stretch with an interval over 60 seconds inside it, its first onset aside, is dropped as a break and counted;
- **provenance** comes from R2's tags (section 2.1); until R2 lands, ready cards read `runners/drive/timeline.py`'s typed and accepted origins directly. Timing and production cards use writer-typed text only;
- **embeddings** come from the encoder pinned in CA1 (revision `e8f8c211...`);
- **function-word skeletons:** each sentence with every word outside a frozen list of the 150 most frequent writer-typed words in CoAuthor replaced by a placeholder. The list is frozen before any outcome is computed.

### 0.6 Resources and pins

- **CPU:** the counted lease of the 17 October packet's row 2.
- **GPU:** none. D10 stays held.
- **Paid work:** section 5 only, under amendment H.
- **Network:** section 4's intakes only, under `docs/design/stage-15/DATA_INTAKE.md`.
- **Pins:** ToMpathy at `certified-fit-1` (`5f3ad0a`) wherever the engine is used.
- **Privacy:** aggregate outputs only. No per-writer, per-annotator or per-rater profile leaves the repository, and identifiers stay hashed. Raw CoAuthor text goes to the paid provider only inside section 5's nodes, and only the material section 5 lists.

## 1. State on 1 November (`0b449a457`)

| Item | State |
|---|---|
| Licensed on real records | Final-page habit identification beyond context, CoAuthor (0.422 in galleries of 30; three-role control). Process-only labels of drafting against revising, ScholaWrite (macro-F1 excess 0.123; planning never predicted). Recurring personal harm-topic judgments, DICES (0.140). A personal-history association with pauses (0.038 per nat) |
| Constructed calibration | The fitted 199-null reference sees taste planted in the reader's own features (10 of 10 at medium strength, 0 of 10 false alarms); lexical taste fails its false-alarm gate; habit plants stay unseen |
| Not detected | An adaptive-forecast advantage (TR4.h1); a directed-reading advantage (DR1); a general fiction advantage, with an instrument that can't reach 80% power (GEN1.ic) |
| Blocked | WC2 (does her direction survive a deleted AI span), FR1 (does she show more of herself after the AI fails her), TR5 (how her trust moves after a failure) and WC4 (what she holds steady), by the shared extractor (`accepted origin reused`; both repairs spent) |
| Cost-held | PP1 (the timing pyramid), WB1's effects (pieces), CA1's encoder (Community Alignment value directions), WD1.h1 (lean against sensitivity), D7 (writing durations), D19 (shared recipes), D33.s (D33's specification curve), PP3.p (PP3's second classifier); D5's remaining calibration (writer identification across AI-share bins; 4,515 CPU-seconds left against 6,542 for one world) |
| Failed instruments | P3c, the CPU edit-intent classifier (κ 0.18); TR3, capture of seen suggestions in later typing (avoidance gate 17 of 20); D37, the page, person and process comparison (calibration) |
| Paid | 1 of 1,000 cents; PROC's format repair never ran; window closed |
| Queue | Zero ready cards against eight; four slots idle |
| Pending | The WA0 receiving copy to ToMpathy, waiting on the curator's destination confirmation |

**What the CoAuthor log can and can't show.** It records text inserts and deletes with their source (typed or accepted), suggestion events (get, open, hover, up, down, select, close, reopen), and cursor events (forward 21,764; backward 15,334; select 6,899) carrying a document position. It has no mouse or click event. Pointer use shows only as suggestion-hover (76,210 events), against keyboard menu moves (suggestion-up and -down, 2,498). ScholaWrite records timestamped before-and-after text with labels, and no cursor or mouse.

## 2. The tree

### 2.1 Family R: the record (ready at handoff)

**R1. Repair the shared extractor with the insertion identity. (engineering successor, `.h1`; ready)**
- **Why.** The shared span extractor failed on its first run and both repairs, each on a different case; the last was `accepted origin reused`. WB1.h1's physical-insertion identity got WB1's effects step past the same case.
- **Do.** Build `shared_spans.h1`, using the insertion identity. Validate it on constructed fixtures reproducing all three recorded failure cases (a replayed span that differs from the canonical offer; an accepted menu with no unchosen comparator; a reused acceptance origin), then on a full replay.
- **Case and check.** The three fixtures each reproduce their recorded failure on the old extractor before the new one runs.
- **Route.** Passing: WC2, FR1, TR5 and WC4 re-enter at their week 3 designs, ranked after family S. Failing: they stay blocked, recorded with this card's reason; no further repair this week.
- **Cost.** At most 1 CPU-hour.

**R2. The provenance census. (infrastructure; ready)**
- **Do.** For every session, replay with `runners/drive/timeline.py` and tag every final-document character: typed by her, accepted from an offer and never touched, accepted and later edited (`accepted_edited`, a span-level tag), prompt text, or API text of unknown origin, as `timeline.py` emits them. Report:
  - sessions whose replay reproduces the final document exactly, and the rest with their reasons (listed, never patched);
  - shares of characters by tag, by genre and writer;
  - for comparison, the share of accepted characters that survive to the final document (a preprint reports about 93% on CoAuthor).
- **Route.** Every card below that uses provenance reads these tags. A session that doesn't replay exactly is excluded from them and counted.
- **Cost.** At most 2 CPU-hours.

**R3. Routes for the held cards (CA1.s1 ready; D33.s and PP3.p1 in section 6's backlog).** CA1.s1 and PP3.p1 are frozen-sample runs of their week 3 designs under amendment E, sized by their probes; D33.s runs in full:
- **CA1.s1**, the Community Alignment encoder and value directions, on a frozen sample that contains the 836-annotator subset approved for CA3 (stated reasons against chosen directions) plus a seeded draw of further whole annotators, sized under amendment E (rank 8, as V1's and V2's input);
- **D33.s**, D33's specification curve in full: its forecast plus its charges (about 1,238 CPU-seconds) fits twice its 786-second cap, so it runs under standing decision S4, which this packet allows for this follow-up despite its record's no-doubling rule (backlog);
- **PP3.p1**, PP3's second classifier on whole projects, sized by its probe, with a declared floor of 3 of the 5 projects (backlog).

PP1, WB1's effects, WD1.h1, D7 and D19 have no sample route: at their measured projections, twice their ceilings holds fewer writers than the 20-writer floor (PP1 about 3, WB1 about 1, WD1.h1 about 8, D7 about 11 of 38). They are recorded cost-held under amendment E step 4 at handoff, and their full runs go to section 6's idle-slot allowance, except D19's, which stays held.

### 2.2 Family S: System 2 markers in the process record

**The theory.** Production runs on compiled expertise; the writer stops to plan where it won't do; a flow run enacts higher-order decisions made earlier; global revision realigns autopilot output with a goal settled later; and moving the cursor away from the leading edge is a higher-order move. Every S card is within-writer, with the controls of section 0.5.

**S1. Do flow runs reuse her own structural templates? (hypothesis test; ready)**
- **Unit.** 8-word windows of writer-typed text in CoAuthor, each starting at the first word after a hesitant interval that lies outside any earlier window. Each window is classed **flow** or **hesitant** by her thirds of window hesitancy (section 0.5); the middle third and windows with a break are left out and counted. Both arms start right after a stop and have the same length, so only their internal fluency differs. Skeleton 4-grams made only of placeholders are dropped.
- **Measure.** For each window, the share of its function-word skeleton 4-grams that occur in the same writer's earlier sessions, minus the same share against a prompt-matched donor writer's earlier sessions (D33's donor matching).
- **Primary.** Within-writer difference, flow windows minus hesitant windows, in that own-minus-donor share. Direction: positive. The null is an interval that includes or falls below zero.
- **The rival.** In the writing literature, burst length mostly tracks typing skill, and bursts aren't mainly prefabricated text. Within-writer designs remove skill differences between writers, so a null here counts against "flow is compiled templates", not for skill.
- **Controls.** Equal window length by design; 200 within-session permutations of the window labels; genres separately.
- **Case and check.** At least 20 windows of each kind in each of at least 25 writers.
- **Route.** Positive: "flow enacts her own compiled templates" gets real support, and the expertise panel can mark flow runs as her recurring structure. Null: `.ic`, with templates planted in constructed sessions.
- **Texture grid:** skeleton 3- and 5-grams; a 100- or 300-word list; windows of 5 or 12 words.
- **Cost.** At most 1 CPU-hour.

**S2. What gets revised later: flow or hesitation? (hypothesis test with rival predictions; after R2)**
- **Unit.** Writer-typed sentences.
- **Outcome.** Later changed by a non-local edit: an edit made while the cursor is at least one sentence away from the leading edge.
- **Predictor.** Produced in flow or with hesitation: her thirds of sentence hesitancy (section 0.5), with the middle third and sentences holding a break reported separately. T2's target (a) is the same split, hesitant third against flow third.
- **Primary.** Within-writer difference in the probability of later non-local revision, flow minus hesitant. Two predictions, stated before the run:
  - the curator's: **positive**, because autopilot output gets realigned with the goal settled later;
  - the difficulty account's: **negative**, because hard sentences are the ones that get fixed.
- **Controls.** Sentence length; distance from the leading edge at writing time; time remaining in the session; genre; writer random effects; 200 within-session permutations.
- **Case and check.** At least 300 non-local revision events across at least 25 writers. If CoAuthor falls short, run **S2.sw** on ScholaWrite: production spans reconstructed from consecutive inserts, the outcome a later edit that overlaps the span, with ScholaWrite's revision labels reported beside it.
- **Route.** Positive: revision is where higher-order goals act on autopilot output, and the expertise panel gains a "realigned here" mark backed by real records. Negative: the difficulty account wins this contrast, and hesitation marks difficulty more than deliberation.
- **Texture grid:** non-local threshold of one paragraph; revision within 2 minutes against later; argumentative and creative separately.
- **Cost.** At most 1 CPU-hour.

**S3. Does revision move text toward the finished piece? (hypothesis test; after R2)**
- **Unit.** Non-local revision events on writer-typed sentences (R2's tags), against matched local edits of the same size in characters to the last complete sentence at the leading edge, so both arms change complete sentences. Edits of 3 or fewer characters and edits that delete a whole sentence are excluded from both; edits to accepted AI text are reported separately.
- **Measure.** Cosine similarity, in the pinned encoder's space, between the edited sentence and the rest of the document as it stood just before the edit (that sentence excluded), after the edit minus before. Text written after the edit can't enter, so an edit can't score as alignment because later text was built around it or because its new wording survives to the end.
- **Primary.** Within-writer difference, non-local minus local, with each local edit matched to a non-local one on writer, edit size in characters and session-time decile. Direction: positive.
- **Controls.** Edit size; document position; time remaining in the session; writer-cluster intervals; 200 permutations of the event labels within session. The same change measured against the rest of the final document is reported as descriptive only, since it favours later edits by construction.
- **Case and check.** As S2's.
- **Route.** Positive: revision aligns parts with the whole, which is the curator's account and a usable signal for panel two's top.
- **Texture grid:** similarity to the next paragraph only; to the session's prompt.
- **Cost.** At most 1 CPU-hour.

**S4. Is moving away from the leading edge a higher-order move? (instrument census, then hypothesis test; ready)**
- **The curator's idea.** Writers shift a hand to the mouse to make higher-order decisions about the document.
- **What the log allows.** CoAuthor's cursor events come from one editor event, so a click and an arrow key look identical. (a) therefore tests how far the cursor moves, not the hand. The device is visible only in the suggestion menu, (b). Section 4's intake of a public keystroke dataset that may log left clicks (S4.k) is the direct test, if it qualifies.
- **(a) Jumps.** Classify each cursor event by its change in document position from the previous event: a **step** (one character, or one word) or a **jump** (more than 40 characters, or onto a different line). Exclude cursor events whose `eventSource` is `api` (programmatic moves after an insertion). A word step is a move that lands on the adjacent word boundary; a different line means a different paragraph.
  - Census first: the distribution of position changes. It must show steps and jumps as separable groups, with at least 5% jumps; otherwise record "design cannot test" for (a).
  - **Primary (a).** Within writer, among cursor events that land at least one sentence behind the leading edge: the probability that she edits within one sentence of the landing point within 30 seconds, after a jump minus after the last step of a run of steps that lands the same distance back (a run: consecutive steps with no text change between them and no gap over 2 seconds; matched in sentence-distance bins). The bins are 1, 2, 3 to 5 and more than 5 sentences back. At least 10 landings of each kind, counted only in bins that hold both kinds, in each of at least 20 writers, or record "design cannot test" for (a). A jump followed within 2 seconds by another jump is a pass-through, not a landing, as a step inside a run is. Holding the landing distance fixed keeps the contrast from being true by definition. Direction: positive.
  - Also: the log interval before a jump against before a step, each divided by her within-word geometric median.
- **(b) Pointer and keyboard in the menu.** For each opened menu, whether she browsed by pointer (a suggestion-hover event, not the opening hover snapshot), by keyboard (up and down), by both, or neither, the last two reported separately.
  - Census: each writer's pointer share (pointer-only menus over pointer-only plus keyboard-only) and its split-half reliability across sessions.
  - Descriptive contrast: within writer, whether pointer-browsed choices differ from keyboard-browsed ones in how close the chosen option sits to her own earlier text (pinned encoder).
- **Route.** Positive (a): panel one can treat jumps away from the leading edge as candidate System 2 moves on logged text. (b) is descriptive this week.
- **Texture grid:** jump thresholds of 20 or 80 characters; 60-second windows.
- **Cost.** At most 1 CPU-hour.
- **S4.k (after its intake).** On the public dataset, if it logs left clicks and arrow keys with cursor positions: (a)'s primary with a mouse click against an arrow-key move as the predictor, within writer, both arms restricted to moves that land at least one sentence from the leading edge and matched on landing distance, with the outcome an edit within one sentence of the landing point within 30 seconds. The human-computer interaction literature's standard timings give a modelling convention for a hand switch: about 0.4 seconds to move a hand between keyboard and mouse, with a separate 1.35-second mental-preparation operator that the keystroke-level model's heuristics place before pointing.

**S5. Do planning labels follow a stop? (hypothesis test, ScholaWrite; ready)**
- **Why.** The curator: planning is the moment someone stops to plan. Process features never predicted planning in PP3, so this asks the simpler question. Planning also runs alongside typing (Roeser et al. 2025), so not every plan will show as a stop.
- **Unit.** ScholaWrite actions, with their expert labels.
- **Primary.** Within-author difference in the log gap, divided by her median gap, before the first action of each run of consecutive same-label actions, planning-run starts minus implementation-run starts, with the posteriors of each author's own mixture of gaps reported beside it. A run is a stretch of consecutive actions with the same high-level label (planning, implementation or revision). Gaps inside runs are reported separately. Direction: positive.
- **Expected size.** In stimulated recall, planning figured in about 40% of recall comments on long pauses between sentences and about 34% between words (12 second-language writers; Révész et al. 2019). So even a true "planning follows a stop" link caps how pure a timing-based planning label can be.
- **Also report:** the same for each of the 15 labels; the gap distribution by label.
- **Controls.** Project and author random effects; edit size; time since session start.
- **Case and check.** At least 30 planning-run starts in each of at least 6 authors. ScholaWrite's timestamps are per released change, and the publisher filtered some events, so a gap can span filtered changes. Report how many gaps are longer than 30 minutes and analyse gaps under 30 minutes, with longer ones as a separate disengagement class.
- **Route.** Positive: "planning follows a stop" holds in expert-labelled data, and panel one can mark long stops as candidate planning on logged text.
- **Texture grid:** gaps under 10 or 60 minutes; per project.
- **Cost.** At most 0.5 CPU-hour.

**S6. Deliberation or difficulty: does choice conflict explain pauses? (packet card testing D33's mechanism, on a frozen sample; ready)**
- **Why.** In the response-time literature, long times often track how close the competing options are, not which system ran.
- **Unit.** D33's word onsets, on a frozen sample of 20 writers.
- **Add** two measures of choice conflict under D33's population three-gram model to D33's joint model: next-word entropy (how many continuations compete), and the margin between the two likeliest next words (a near-tie is the writing analogue of a hard choice).
- **Primary.** The own-history coefficient with both conflict terms in D33's joint model, fitted on the 20-writer sample, with writer-cluster intervals from 2,000 resamples. Direction: positive (it stays above zero). Beside it: the same coefficient without the conflict terms on the same sample, their paired difference, and the two conflict coefficients (predicted positive).
- **Also:** whether the pause left over after conflict and own-history predicts S2's later revision. If it does, the leftover is more than retrieval difficulty.
- **Route.** If own-history shrinks to zero with conflict in, D33's personal signal was choice conflict.
- **Cost.** At most 0.8 CPU-hour, granted by this packet; it isn't one of D33's three 786-second follow-up slots and doesn't draw on them.

### 2.3 Family T: the top of the hierarchy

**The theory.** People reach the top of someone's hierarchy "with nothing", from finished work, by slotting in their own expertise. These cards test four routes: what the finished text's structure says (T1, T2), what her steps compress into (T3), what her choices among offers reveal at her own competence (T4), and what a language model's expertise infers, checked against her later choices (T5). T6 builds texts with known goals to test the readers.

**T1. Plan roles and their process signatures. (hypothesis test; needs PROC)**
- **Why.** This takes up week 3's plan-role cards, PP5 and PP6, which waited on PROC.
- **Labels.** PROC (section 5) gives each sentence of each final document a plan role, using week 3's role grammar and the format repair (constrained output).
- **Primary.** Within-writer difference in the log pause before a sentence, divided by her within-word geometric median, higher-order roles minus elaboration roles, in PROC's codes: for arguments, position or claim against evidence; for stories, setting or any sentence PROC marks central (c = 1, a necessary plot turning point) against action, dialogue, inner_thought or description with c = 0. Other codes are reported separately. The pause is the interval before the sentence's first writer-typed character (R2's tags); sentences accepted from an offer are excluded. Direction: positive. The pause's hesitation and slowest posteriors are reported beside it; the middle posterior alone falls as a pause runs long, so it can't carry the contrast.
- **Also:** the same contrast for later non-local revision (S2's outcome).
- **Route.** Positive: roles read from the finished text carry a process signature, and panel two's top tier can use them on web text, with this measured link.
- **Cost.** At most 1 CPU-hour, plus PROC.

**T2. Reading the process from the finished text. (engine instrument; after R2 and S2)**
- **Why.** Web text has no process log. If the finished text predicts its own process on held-out writers, the engine can mark candidate attention and revision on any page, with a measured accuracy.
- **Targets,** per sentence: (a) produced with hesitation; (b) later revised non-locally; (c) accepted from an offer.
- **Features.** Final text only: the pinned encoder's embedding, length, position, punctuation and the function-word skeleton.
- **Model.** Ridge logistic, trained leaving writers out (5 folds by writer).
- **Primary.** Held-out-writer AUC for (a), minus a baseline using position and length only, with writer-cluster intervals. A gain of at least 0.05 counts as useful.
- **Also:** (b) and (c) the same way; REV's AUC on each target from its per-sentence scores (section 5), a language model reading the final document with nothing else, as a second baseline.
- **Expected sizes.** A literature search on 1 November found no published model that predicts revision or hesitation from the final text and checks it against keystroke logs, so (a) and (b) have no outside benchmark. For (c), AI-span detection on CoAuthor reached only κ 0.40 in one study, and boundary detectors lose much of their accuracy on text from new generators (Qu & Meng 2024; Wang et al. 2024, the SemEval-2024 Task 8 overview).
- **Route.** (a) or (b) useful: the engine may show candidate attention and revision marks on web pages, with this AUC beside them. (c) useful: the engine can mask likely AI spans before reading a maker.
- **T2.r, an outside test (after its intake).** Wikipedia articles carry public revision histories, a coarse process log for web text. On a frozen sample of 200 English Wikipedia articles, apply T2's model, trained on CoAuthor, to predict (b): which sentences of the current version were rewritten, meaning that a revision after the one that introduced the sentence changed at least 20% of its tokens, excluding reverted revisions (a repeated revision hash) and bot accounts, with templates, tables and references dropped. Primary: AUC minus the position-and-length baseline, with article-cluster intervals. This is the cheapest check that a process reader trained on co-writing logs transfers to the web.
- **Texture grid:** argumentative and creative separately; gradient-boosted trees.
- **Cost.** At most 1.5 CPU-hours.

**T3. From steps to pieces: does a personal chunk library compress her later work? (hypothesis test; ready)**
- **Why.** If people work with reusable pieces, a chunk library learned from her earlier sessions should compress her later sessions better than one learned from someone else's.
- **Sequences.** (i) Each session's function-word skeleton; (ii) each session's event tokens: insert-word, delete, pause (hesitant), jump, step, suggestion-get, select, dismiss.
- **Libraries.** Byte-pair merges learned on a writer's first half of sessions (by date): 100 merges for (i), 50 for (ii). The same number learned on a prompt-matched donor's first half, and on a population sample with the same token count.
- **Primary.** Code length of her second-half sequences in bits per original symbol (skeleton word or event token, before merges), own library minus donor library, by sequence type. Each library's merged tokens are scored by a unigram model fitted on that library's own training half with add-one smoothing. Direction: negative (her library compresses her better).
- **Also: reuse.** The share of her library's learned chunks that occur at least twice in her second half. Audits of language-model library learners found learned functions were reused extremely infrequently (Berlot-Attwell et al. 2024), so a compression gain without reuse doesn't count as pieces.
- **Controls.** Matched training token counts; 1,000 reassignments of session ownership within prompt.
- **Case and check.** At least 2,000 skeleton tokens in each half for at least 25 writers.
- **Route.** Negative for (i) or (ii): personal pieces are learnable from steps, and panel two can display her recurring chunks, with this compression gain.
- **Texture grid:** merges 25 to 400; first-third against last-third splits.
- **Cost.** At most 1 CPU-hour.

**T4. Choices among offers, read at her own competence. (choice model; ready)**
- **Why.** The curator: the engine assumes "a level of competence that is commensurate with the level of competence displayed elsewhere." CoAuthor's menus are known choice sets, the setting in which revealed preference is best identified.
- **Unit.** Each opened menu: the options shown, and her canonical choice (an option, or dismissal).
- **Model.** Conditional logit over options plus dismissal, on option features: closeness to her own earlier text, closeness to the population's, length, position in the menu, and fit to the preceding sentence (all with the pinned encoder). Her state enters too: her acceptance rate over the previous five menus, and time since her last acceptance. In both versions the dismissal alternative has a constant per writer, estimated on her earlier sessions, so differences in how often writers dismiss can't register as a temperature difference. In AI-assisted programming, adding the programmer's current state to a telemetry model raised acceptance-prediction accuracy from 61.9% to 83.6% in 21 programmers, though the suggestion's own features were the strongest single predictors (Mozannar et al. 2024). Two versions:
  - a shared temperature (how sharply choices follow the features) for everyone;
  - a temperature per writer, estimated on her earlier sessions.
- **Primary.** Held-out log-likelihood per choice on her later sessions, per-writer minus shared temperature. Direction: positive.
- **Also report:** the spread of writer temperatures with intervals; whether a writer's temperature correlates with the similarity margin of her WA0.h1 probe (true writer's score minus the best other gallery writer's) or her mean window hesitancy (S1), descriptively.
- **Case and check.** At least 20 menus in each half for at least 25 writers.
- **Route.** Positive: the engine reads each maker at her own competence, estimated from her other choices, as the curator proposed. It extends D2's pooled conditional logit over the same menus with the program's first per-writer competence estimate.
- **Texture grid:** per-writer feature weights as well as temperatures; creative and argumentative separately.
- **Cost.** At most 1 CPU-hour.

**T5. Plans inferred by a language model's expertise, checked against her later choices. (hypothesis test; needs PLAN)**
- **Why.** This is the curator's route to the top: "identifying how it could be done... given the same limitations that they had." Here a language model supplies the expertise, explicit Bayesian updating supplies the inference, and her later choices supply the check.
- **Procedure,** per session with at least four menus after its midpoint (by event count):
  1. PLAN reads her text up to the midpoint and proposes five one-line plans for how the piece continues;
  2. for each later menu, PLAN rates how well each option fits each plan (1 to 5);
  3. a plan posterior starts uniform and updates on each of her later choices, with T4's model adding a plan-fit term;
  4. each menu's choice is predicted from the posterior before it is updated (prequential).
- **Primary.** Prequential log-likelihood per later choice, updated plan posterior minus a frozen uniform posterior. Direction: positive (her own choices reveal her plan, and the plan predicts her next choice).
- **Also:** against T4's model without plans.
- **No circularity.** Plans come from text before the menus they're scored on; options she never saw are never used.
- **Case and check.** At least 300 sessions qualify.
- **Route.** Positive: inferring the top with a language model's expertise has a real-record validation, and the engine's expertise panel can show its inferred plan with this measured gain. Ghost's H1 and E2 say how much the reader's own expertise should help and when it misleads.
- **Cost.** At most 1 CPU-hour, plus PLAN.

**T6. Texts with planted goals: a known-answer bed for readers of the top. (instrument; needs PLANT and REV)**
- **Why.** The curator: if the puzzle can be cracked now, "it has to come somehow from the fact that AI is on the scene." A text written to a known hidden goal is a planted ground truth, as alignment auditing uses planted objectives.
- **Build.** PLANT writes 600 short pieces (300 arguments, 300 stories), each under 0 to 2 hidden higher-order goals from a frozen library of 12 (for example: make the reader trust the narrator; move the reader toward caution without saying so; honour tradition). 100 of them have none.
- **Read.** REV, given each piece alone and the goal library, returns either "none" or up to two goal codes, most likely first.
- **Primary.** Top-1 recovery: the share of goal-bearing pieces whose first-named goal is one of their planted goals, with a binomial interval, reported separately for one-goal pieces (chance 1/12) and two-goal pieces (chance 2/12), with the pooled chance computed from their counts. Beside it, the false-goal rate: the share of the 100 control pieces for which REV names any goal. PLANT's 500 goal-bearing pieces split 250 one-goal and 250 two-goal, frozen before generation.
- **Also:** the confusion structure: which goals alias with which.
- **Route.** A measured known-answer accuracy for top-level readers. The engine's top tier may cite it only as planted-text calibration; human makers' goals are harder.
- **Cost.** At most 0.5 CPU-hour, plus PLANT and REV.

### 2.4 Family V: value data, with error bars

**V1. Individual value directions from designed choices. (Community Alignment; after CA1.s1)**
- **Unit.** Annotators in CA1.s1's frozen sample (at least 800).
- **Model.** Per annotator, CA1's conditional logit over each turn's four candidates (pinned embeddings reduced by PCA fitted on candidates only), shrunk toward her country's mean direction computed without her.
- **Primary.** Split-half reliability of annotator directions, halves formed by assigning her whole conversations alternately in a seed-20261102 random order: the mean cosine between her two half-directions, minus the mean cosine between each of her halves and the opposite half of each comparator (an annotator of her country and her group, the seeded draw or the subset, whose most frequent prompt cluster of CA0's 50 is the same as hers, ties broken by a seed-20261102 draw), with annotator-cluster intervals from 2,000 resamples. Direction: positive. Report it separately for CA1.s1's seeded random draw and for the 836-annotator subset, which was chosen by having explanations, with the count of annotators dropped for having no comparator. This replaces CA2's reliability primary for the week; CA2 runs only its decomposition into country, annotator within country and residual.
- **Route.** Positive: individual value directions from designed choices, with error bars. CA4 (identification under section 0.4) follows from it.
- **Cost.** At most 1.5 CPU-hours.

**V2. Stated reasons against chosen directions. (CA3 on the approved 836-annotator subset; after CA1.s1 and VAL)**
- As week 3's CA3, with VAL's Schwartz codes. Directions use CA1.s1's embeddings, which cover the 836; prototypes come from VAL-coded explanations of CA1.s1's other annotators, which narrows CA3's prototype pool, so record V2 as a separately labelled supported variant (standing decision S1). Primary as specified there.

**V3. Does a writer's mix of drive cues recur? (hypothesis test; needs DRIVE)**
- **Why.** The curator's plan of 21 October: assume a need, track how often people use each drive, and first establish that there is any signal at all. Ghost's E1 asks whether usage ratios can tell terminal from circulating values; this asks whether a usage profile is personal at all.
- **Labels.** DRIVE codes each writer-typed sentence for Panksepp-system cues (SEEKING, RAGE, FEAR, LUST, CARE, PANIC/GRIEF, PLAY, none), as cues in the text, not inferred feelings.
- **Primary.** Split-half correlation of a writer's channel-share profile across her sessions, minus the same between prompt-matched donor writers (section 0.4's roles). Direction: positive.
- **Controls.** Prompts drive content heavily (a story about a storm draws FEAR), so profiles are residualised on prompt means first. Genres separately.
- **Case and check.** At least 200 coded sentences per writer in each half for at least 25 writers.
- **Route.** Positive: the core values panel's drive channels get a personal-recurrence basis, as usage ratios. Ghost's E3 (feelings as cached solutions) says what such a profile can and can't reveal.
- **Cost.** At most 1 CPU-hour, plus DRIVE.

**V4. Paying to say it herself, broadened. (hypothesis test, PR1 broadened; after R2)**
- **Why.** PR1, week 3's paying-to-say-it-herself card, fell one writer short of its event minimum. Costly choices are where values show.
- **Event.** She dismisses every option of a menu (P2's canonical handling), then within 60 seconds types at least 10 words. Her advantage is the highest cosine between her next 50 typed words and the dismissed options, minus the same for other writers' typed text at the same prompt and relative position against the same options (PR1's context-only reference). The event is "close" when her advantage exceeds the 95th percentile of the same advantage computed with another same-prompt writer's text in place of hers, so shared context can't make an event.
- **Primary.** PR1's contrast, broadened: within writer, her advantage after examined dismissals (her upper tercile of open time, or a suggestion-hover event while the menu was open) minus after fast ones (her lower tercile with no such event, so no dismissal is in both arms; a duration tied at a tercile cutoff is in neither), writer-clustered, with PR1's balance check (the options' similarity to her preceding text, and P8's logged GPT-3 probability for each option, added as covariates if the arms differ). Predictability raises both arms; only the contrast can show paying to say it herself. Support, counted on these disjoint arms: at least 20 writers with at least 6 examined and 6 fast dismissals each (PR1 required 25 writers with 10 and 10; on PR1's events, 24 writers had 10 and 10 with overlapping arms and 19 with disjoint ones). Direction: positive.
- **Also:** each writer's rate of close events per dismissed menu and its split-half reliability (odd against even prompts, against writer-label permutations within prompt), descriptive only, since predictability alone can make it recur; and whether writers with higher rates have larger WA0.h1 probe margins.
- **Route.** Positive: paying to say it herself, once she has read the offer, becomes a measured marker of "what she won't delegate" (PR1's route).
- **Cost.** At most 0.5 CPU-hour.

### 2.5 Family U: uptake (intake-dependent)

**U1. Does modelling the source protect? (public co-writing logs with attitudes)**
- **Intake first** (section 4): the public logs of the opinionated-language-model study (Jakesch et al. 2023) that a CHI 2026 study reanalysed. If the release has no post-task attitude measure, record "unsupported at source".
- **Unit.** Sessions with the biased assistant.
- **Primary.** Post-task attitude toward the assistant's position, writers who edited accepted suggestions minus writers who accepted verbatim, adjusted for the pre-writing measure, at matched exposure (suggestions shown). Two predictions: modelling the source protects (negative difference), or exposure captures regardless (zero).
- **Case and check.** The release must hold an attitude or opinion measure taken before writing (or a frozen pre-writing proxy). Without one, record "design cannot test" under amendment F, with the counts: writers who already disagree with the assistant would both edit more and end less aligned, so a negative difference is expected under either prediction.
- **Route.** Either way, a real-record contrast for Ghost's U1 (the opacity gate) and the curator's question on what gates uptake.
- **Cost.** At most 1 CPU-hour.

### 2.6 Carried cards

- **WC2, FR1, TR5, WC4:** if R1 passes, at their week 3 designs, ranked after family S.
- **CA2, CA4:** after V1, on CA1.s1's sample: CA2 as its decomposition only (V1 carries its reliability primary), CA4 at its week 3 design.
- **FIC1** (a stronger fiction-against-argument author test on GEN1's writers): its calibration under standing decision S4, or, if its probe projects more than twice its ceiling, on an amendment E sample with a declared floor of 16 of GEN1's 24 writers; AUTH (section 5) for its primary, on all 24.
- **TR3:** frozen; no further repairs; its human run stays held.
- **D5:** held; its remaining calibration needs a faster exact implementation (backlog).

### 2.7 Dispatch order

**Ready at handoff,** in this order:
1. R1
2. R2
3. S5
4. S1
5. S4
6. T4
7. T3
8. CA1.s1
9. S6

**Then, as gates open:**
- S2, S3 and V4 (after R2); T2 (after R2 and S2)
- V1 (after CA1.s1); then CA2 and CA4
- T1 (after PROC and R2); T5 (after PLAN and T4); T6 (after PLANT and REV); V2 (after CA1.s1 and VAL); V3 (after DRIVE). V3's and T5's case checks run before DRIVE's and PLAN's main batches; a failed check cancels the batch.
- FIC1 (its calibration as slots allow; its primary after AUTH)
- U1, S4.k and T2.r (after their intakes)
- WC2, FR1, TR5, WC4 (after R1 passes)

**Idle slots:** the texture lane (amendment G), then section 6.

## 3. What each result changes

| Result | Route |
|---|---|
| R1 passes | Four blocked cards re-enter |
| S1 positive | Flow runs are her compiled templates; panel two can mark them |
| S2 positive | Revision realigns autopilot output with later goals; panel two gains "realigned here" |
| S2 negative | Hesitation marks difficulty more than deliberation |
| S3 positive | Revision aligns parts with the whole |
| S4 (a) positive | Jumps away from the leading edge are candidate System 2 moves |
| S5 positive | Planning follows a stop in expert-labelled data |
| S6 own-history vanishes | D33's personal signal was choice conflict |
| T1 positive | Plan roles from finished text carry a process signature |
| T2 useful | Candidate attention and revision marks on web text, with a measured AUC |
| T3 negative | Personal pieces are learnable from steps |
| T4 positive | Each maker is read at her own competence |
| T5 positive | A language model's expertise infers plans that predict her later choices |
| T6 | A known-answer accuracy for top-level readers, on planted text |
| V1 positive | Individual value directions from designed choices, with error bars |
| V3 positive | Drive-cue profiles are personal |
| V4 positive | A measured basis for "what she won't delegate", once she has read the offer |
| U1 | A real-record contrast on what gates uptake |
| Any card unsupported, or "design cannot test" | Recorded with its counts; no `.ic` follows |

## 4. Intakes (network lane, under `DATA_INTAKE.md`)

- **Jakesch et al. 2023 co-writing logs** (for U1): locate the public release, record its licence and fields, and confirm whether it includes pre-writing and post-task attitudes and keystroke or suggestion logs. Licence unclear or post-task attitudes absent: U1 is unsupported at source; pre-writing attitudes absent: "design cannot test" (U1's case check).
- **Wikipedia revision histories** (for T2.r): a frozen random sample of 200 English Wikipedia articles with at least 50 revisions, through the public API, under the CC BY-SA licence, with aggregate outputs only.
- **The 2023 Kaggle "Linking Writing Processes to Writing Quality" keystroke logs** (for S4.k): confirm whether its events include left clicks and arrow keys with cursor positions (unverified), and whether its terms allow research use outside the competition. If either fails, S4.k is unsupported at source. A download that needs an account or acceptance of competition rules fails `DATA_INTAKE.md`; use a public copy only if the data's owner releases it under a stated licence, and otherwise record S4.k unsupported at source. Its letters are masked, so only timing, event and position cards can use it.
- Nothing else is required this week. Carried intakes stay optional.

## 5. Gear 3 campaign `G3-S15-WEEK4`

- **Authority.** The curator's per-use approval, requested once at handoff under amendment H. On 1 November, of the one-day Gear 2 package he first planned, he said: "If you want to follow up with some gear three action at the same time, I'm down for that." That isn't the approval; his reply to the handoff request is. Record it verbatim in `.agent-state/drive-20261102/APPROVAL.json`.
- **Total cap:** $10 gross, enforced in code; nothing past $10 without his detailed final approval.
- **Paid dispatch closes** Friday 6 November, 17:00 PST (2026-11-07T01:00Z).
- **Prices:** the rates `budget.py` already uses. Reconcile each node's actual spend from the provider's usage records before reserving the next.
- **Data sent to the API,** and nothing else:
  - **PROC:** every sentence of every CoAuthor final document, with the document's preceding sentences as context;
  - **PLAN:** each qualifying session's text up to its midpoint, and the option texts of its later menus (the assistant's offered continuations);
  - **DRIVE:** each writer-typed CoAuthor sentence, with its preceding sentence;
  - **VAL:** Community Alignment explanations (public, CC-BY-4.0) from week 3's frozen VAL sample (up to 10 per annotator, seed 20261026), restricted to annotators in CA1.s1's sample, which contains the approved 836-annotator subset;
  - **REV:** each CoAuthor final document, and each of PLANT's pieces;
  - **PLANT:** no source text; it receives only the goal library and genre prompts;
  - **AUTH:** pairs of typed texts, each from one writer's own keystrokes, up to 400 words each.
- **Code.** In a new module `runners/drive/budget_week4.py`, modelled on `budget_week3.py` (leave `budget.py` and `budget_week3.py` unchanged; import `ceiling` from `budget.py`): `CAMPAIGN = 'G3-S15-WEEK4'`; `APPROVAL` at the path above, naming the approved nodes and holding this packet's SHA-256 and the curator's statement verbatim; `PACKET` at `docs/design/stage-15/week4/PACKET.md`, checked against the approval's `packet_sha256`; `CUTOFF` at 2026-11-07T01:00:00+00:00; `CAPS` as below; no Reserve node; keep the 1,000-cent refusal; `max_tokens` sized per node: 32 for single labels (PROC, DRIVE, VAL, AUTH, and REV's planted-piece readings); 300 for PLAN's plans; 120 for PLAN's ratings, one call per later menu returning the plan-by-option matrix as constrained JSON; 10 per sentence plus 20 for REV's document readings, set per document, which return for each numbered sentence three 0 to 9 scores (hesitated, revised non-locally, accepted from an offer); 700 for PLANT's pieces; thinking off; reserve before every POST; no automatic resubmission; deduplicated input counts before each reservation; reconcile before each next node.
- **Known-answer rung first,** for every node:
  - **Labelling nodes (PROC, DRIVE, VAL):** the owner labels the node's first 100 items blind, as agent labels; the node continues past κ of at least 0.6 (pooled for DRIVE and VAL, with per-category κ reported where prevalence is at least 5%). Every response must parse (constrained output); 98 of 100 is the format floor.
  - **PLAN:** format on 100 sessions, and agreement of its option-fit ratings with the owner's blind ratings on 100 pairs of an option and a plan, collapsed to three levels, κ of at least 0.6.
  - **PLANT:** format, and the owner's blind check that at least 45 of 50 sampled pieces don't state their hidden goal outright.
  - **REV:** format only; its accuracy is T2's and T6's result.
  - **AUTH:** AUC of at least 0.6 on its first 100 argument pairs, which FIC1's primary then excludes.
  - A node that fails its rung may have one recorded prompt fix, rerun on 100 fresh items, inside the handoff approval. A second failure stops it.

| Node | What it buys | Forecast | Cap |
|---|---|---:|---:|
| PROC | Plan roles for every final-document sentence (T1) | about $1.20 | $2.00 |
| VAL | Schwartz codes for explanations of CA1.s1's annotators, the 836-annotator subset included (V2) | about $1.00 | $2.00 |
| PLAN | Plans and option-fit ratings for qualifying sessions (T5) | about $0.60 | $1.50 |
| DRIVE | Drive-cue codes for writer-typed sentences (V3) | about $0.80 | $1.50 |
| AUTH | 4,000 same-author pair judgments (FIC1) | about $0.30 | $1.00 |
| PLANT | 600 planted-goal pieces (T6) | about $0.15 | $0.50 |
| REV | Readings of final documents and planted pieces (T2, T6) | about $0.20 | $0.50 |

**Order:** PROC, PLAN, DRIVE, PLANT, REV, VAL, AUTH (REV follows PLANT because it reads PLANT's pieces). The caps total $9.00, under the $10 campaign cap; the forecast total is about $4.25.

## 6. Backlog, idle slots only

**Holds lifted, idle slots only.** Each full run queued under amendment E may run in idle counted slots to its last recorded full projection plus 50%, logged, CPU only, as week 3's section 6 allowed: PP1 (121,121 CPU-seconds projected), CA1 (148,034, after CA1.s1), WD1.h1 (100,969), D7 (25,682), and WB1's effects after a fresh cost probe of at most 2 CPU-hours, charged to this allowance (its 222,717-second projection is unverified). D19 (802,268) stays held. In order, after the texture lane: D33.s; PP3.p1; then these full runs, smallest first (D7, WD1.h1, PP1, CA1, then WB1's effects), each started only if its measured wall-time projection ends before the 2026-11-09T06:00Z drain or it checkpoints for the next window; a faster exact implementation for D5; P7's remaining precision (GPT-2 word-event probabilities); D36, the joke-rating card (after P7); TR3c's census (capture on the randomized holdout; stays frozen otherwise).

## 7. Cross-repository

| To | What | When |
|---|---|---|
| Ghost, `docs/exchange/sounding-line-week4-2026-11-02/` | WB1's effects table, if its full run lands under section 6 (Ghost holds it for its next version's W5 calibration (its study of what a wrong piece library costs); no V26 card waits on it); S1 to S6 results (for the reports of Ghost's H2, pauses and deliberation, and H3, global revision); T5's result (for the reports of Ghost's H1, the top of the hierarchy, and E2, one model run both ways) | As each lands |
| ToMpathy, `docs/` | The WA0 receiving copy, once the curator confirms its destination; T2's and T5's results with their routes | As each lands |
| From Ghost | V26's (Ghost's current version's) primaries with stated routes | Optional; nothing waits |

Handing over this packet approves this week's aggregate-only copies into Ghost's `docs/exchange` and into a ToMpathy `docs/` folder named for the card, by EV4's procedure (copy, hash, record). The WA0 receiving copy is the exception: it still waits for the curator's destination confirmation. Don't commit or push in the recipient repository.

## 8. Reporting

- **Daily digest** at 20:00 PST: corrections first, with their class; landed results with ledger ids, control status and follow-ups registered; idle slot-hours with causes; ready cards against eight; the texture lane's count per family; paid spend by node.
- **Final digest** by Sunday 8 November, 20:00 PST: positives first, each with its ledger id and control status; then a one-page map of the hierarchy, marking which levels have real-record support and which don't; then nulls with their sensitivity; then "design cannot test" records; then operations.
- **Drain addendum** by 23:00 PST (2026-11-09T07:00Z): results that land between 20:00 and the 22:00 drain.

## 9. Pre-mortem

- **Cards are built one at a time again and slots idle.**
  - *Guard:* nine cards ready at handoff, amendment G's texture lane, amendment E's sample route for anything that projects over twice its cap, and section 6's idle-slot allowance for the full runs.
- **R1 fails.**
  - *Guard:* nothing in families S, T, V or U needs the shared extractor; R2 uses the canonical timeline.
- **A design can't produce its case** (too few non-local revisions in short sessions; too few menus after the midpoint).
  - *Guard:* amendment F's check before any draw, and ScholaWrite fallbacks where they exist.
- **Hesitation reads typing skill.**
  - *Guard:* within-writer designs, each writer's own mixture, and bigram-difficulty controls.
- **Within-writer contrasts confound position.** Late sentences are both more often in flow and less often revised.
  - *Guard:* distance from the leading edge and time remaining as controls in S2, and session-time matching in S3.
- **Paid approval doesn't come at handoff.**
  - *Guard:* every paid-dependent card is blocked under standing decision S6, naming its node; the nine ready cards need no node.
- **A language-model node's labels are invalid.**
  - *Guard:* each node's rung, one prompt fix, then stop.
- **T5's plans fit choices for shallow reasons** (an option's length, say).
  - *Guard:* T4's features stay in the model, so the plan term must add beyond them.
- **T6 overstates top-level reading.** Planted goals in model-written text are easier than a person's.
  - *Guard:* the route limits T6 to planted-text calibration.
- **Multiple comparisons.**
  - *Guard:* every result is descriptive, with one primary per card.

## 10. Triggers (the only reasons to contact the curator)

1. The handoff approval request for section 5 (amendment H).
2. A result reverses a delivered public claim.
3. A paid spend would pass $10.
4. An outage longer than 12 hours.
5. Privacy: any writer, annotator or rater identity, or raw text, would leave the repository other than through section 5's nodes.

## Sources

Repository records at `0b449a457`: `FINDINGS.md`, `results/phase_2_4_stage_15/CLAIM_LEDGER.json`, `DRIVE/DIGEST_20261030.md` and `DIGEST_20261031.md`, `DRIVE/D6.json` (event census), `DRIVE/PAID_CUTOFF_20261030.md`, `TODO.md`, `docs/design/stage-15/week3/PACKET.md`.

Literature cited in the cards:
- Krajbich et al. 2015, response times and the critique of reverse inference: https://doi.org/10.1038/ncomms8455.
- Révész, Michel & Lee 2019, second-language writers' pausing and revision, with stimulated recall, *Studies in Second Language Acquisition*: https://doi.org/10.1017/S027226311900024X.
- Card, Moran & Newell 1980, the keystroke-level model, *Communications of the ACM*: https://doi.org/10.1145/358886.358895 (operator timings read through a secondary course page).
- Evans, Dillon & Rand 2015, decision conflict drives reaction times in social dilemmas: https://doi.org/10.1037/xge0000107 (abstract).
- Roeser et al. 2025, parallel planning in typing: https://par.nsf.gov/biblio/10614280 (abstract).
- Roeser, De Maeyer, Leijten & Van Waes 2024, typing disfluencies as a finite mixture process, *Reading and Writing*: https://doi.org/10.1007/s11145-021-10203-z (abstract).
- Limpo & Alves 2017, bursts and transcription skill, *Written Communication*: https://doi.org/10.1177/0741088317714234; Olive & Cislaru, the linguistic content of bursts (abstract): https://www.benjamins.com/catalog/z.194.06oli.
- Wang et al. 2024, SemEval-2024 Task 8, machine-text boundary detection on new generators: https://aclanthology.org/2024.semeval-1.279; Qu & Meng 2024, TM-TREK at SemEval-2024 Task 8: https://arxiv.org/abs/2404.00899.
- Davalos & Zhang 2026, AI assistance and temporal fingerprints on CoAuthor: https://arxiv.org/pdf/2609.17883 (preprint, abstract).
- Jakesch et al. 2023, co-writing with opinionated language models: https://par.nsf.gov/biblio/10562907 (abstract); reanalysed in Bhat et al. 2026, CHI: https://arxiv.org/html/2603.10374v1.
- Marks et al. 2025, auditing language models for hidden objectives: https://arxiv.org/abs/2503.10965 (preprint, abstract).
- Berlot-Attwell, Rudzicz & Si 2024, library learning and single-use abstractions: https://arxiv.org/abs/2410.20274 (preprint, abstract).
- Mozannar, Bansal, Fourney & Horvitz 2024, when to show a suggestion in AI-assisted programming (its latent-state analysis reuses the 21-programmer study of their CHI paper, https://arxiv.org/abs/2210.14306): https://arxiv.org/abs/2306.04930 (preprint).
- Zeng et al. 2024, detecting AI-generated sentences in human-AI collaborative hybrid texts: https://arxiv.org/abs/2403.03506 (preprint).
