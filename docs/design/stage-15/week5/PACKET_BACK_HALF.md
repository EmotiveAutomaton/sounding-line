# Sounding Line, Stage 15, week 5, back half (11 to 15 November): lift three gates, run the theory handoff's tests, hand the engine its first ground truth

*Spec sheet for the Sounding Line agent. It amends `docs/design/stage-15/week5/PACKET.md` (7 November) and runs inside the same campaign, `S15-WEEK5`, to the same clock: no new starts after Sunday 15 November, 20:00 PST (2026-11-16T04:00Z), drain by 22:00, addendum by 23:00. File it as `docs/design/stage-15/week5/PACKET_BACK_HALF.md`. Every decision is made here. Where this packet and the 7 November packet disagree, this one wins. As of Wednesday 11 November 2026, written against `origin/main` at `0bafb81c8`.*

**What the back half is for.** Three things, in this order.
1. **Lift the gates only a packet can lift.** Through the 10 November digest this campaign supplied 607.9 slot-hours and occupied 145.7; 462.2 sat idle (76%). The work is not short of ideas. It is held at three design-level gates the owner rightly refused to lift itself (section 1), and behind one operating session that qualifies and admits cards one at a time with no builder running since 8 November.
2. **Run the theory thread's ranked tests.** The theory thread filed its Round 12 handoff on 11 November (`claude/THEORY_HANDOFF_2026-11-11.md` in the project; supplied with this packet). It writes no packets. Section 2 turns its tests 1 to 7 into cards on sources this repository has already qualified, plus one card that waits on a source. The cards were then checked against the thread itself: the curator's 11 November turn there, and the Round 12 messages sent to him, which end in five open questions. Where a card bears on one of those questions, it says so.
3. **Hand the engine ground truth.** The curator, 11 November: "We want accuracy and speed." Nothing in ToMpathy's engine has yet been scored against real writing. Section 2.6 exports what it needs.

**Lessons this packet is built on** (quotes are this repository's):
- **The 7 November design put its slowest gate in front of four cards.** AT2 had to finish ten readers before AT3, AT4, GO1's reader and LA1 could start, and it scored the engine's own two models last. One memory rule then held everything: reader ordinal 128 "remains unadmitted because Windows commit headroom is below the unchanged 26-GiB start gate". That ordering was the analyst's error. Rulings R1 and R4 undo it.
- **Gates sized to forecasts, not measurements.** `AT_GUARDED_BANK.md` says of its own 26 and 20 GiB thresholds: "These thresholds are not measurements of any reader's memory use." The observed peak working set for one chunk is 4.69 GiB.
- **A fourth month nobody can store.** July 2026 projects to 153.51 GiB for two databases against 77.50 GiB free, plus about 541,000 CPU-seconds. Three complete months sit ready, and "All 44 frozen CH cells remain dependency-, qualification- and cost-gated."
- **One failed control holding a family.** The mood kink control "Expected support; returned inconclusive", and "every human mood descendant remains held under the all-twelve-control requirement".
- **Builders delivered and were not restarted.** "No new delegation is inferred from this event."
- **Separate sensitivity cards** (IN3.ic, IN4.ic, SP3.ic) each needed their own design, fixture, adapter and replay to say what one line beside the estimate can say. Amendment P.

## 0. How to run this

### 0.1 Unchanged

- Campaign, clock, ledger and result paths, the stone rules, and amendments A to M except as amended below. Amendment I stays replaced by the curator's 8 November instruction. Section 0.7's privacy rules stand, with the one named exception in amendment T.
- **Wakes.** The curator's instructions of 8 and 9 November stand as written in `AGENTS.md`: "wake on events and after four hours of owner inactivity", and "keep at most one pending operational wake in the owner thread". This packet adds no schedule and restores no hourly wake. Tokens are short this week, so the fix for idle slots here is long admitted work and builders, not more wakes.
- No GPU, no paid work, no Ollama calls from Week 5 cards.

### 0.2 Standing amendments, 11 November

Write these into `AGENTS.md` under "Standing amendments, 11 November". There is no amendment R, to keep the letters apart from rulings R1 to R4.

**N. Long queues, and the order of a wake.**
- Filler work (CH1's collection, reader scoring, encoder and masked-model passes) is admitted as queues: one admitted plan covers consecutive checkpointed batches for up to 12 hours in one slot. A batch checkpoints at least every 30 minutes, so a yield loses at most that. A queue is landed once, when it ends. This replaces the 30-minute filler bound in the 7 November packet's section 3.
- Queues take at most six of the eight slots. Two stay for short cards, and run one-hour filler batches when nothing short is staged.
- At every wake, in this order: (1) start staged or admissible work in every idle slot; (2) review any builder delivery and stage it; (3) land what finished; (4) anything else. A wake that ends with an idle slot while staged or admissible work exists records the reason in OPS_LOG.

**O. Builders by queue (amends J).**
- This packet lists builder assignments, so it is the explicit per-task request `AGENTS.md` requires. Start three builders at handoff on section 3's queues.
- A builder builds and stages: the design note with its DESIGN CHECK block, the handler or config, the fixture, and a plan ready to admit. The owner reviews, admits and launches.
- Amendment J had a finishing builder take the next card by itself. Under O the owner restarts it at the wake its delivery arrives, on the next unbuilt item of its queue. A builder with an empty queue takes the last item of the longest other queue.
- The 8 November reading "No new delegation is inferred from this event" does not apply while any queue in section 3 holds an unbuilt item.

**P. Say what the design could see.**
- Every primary landed under this packet reports, beside its estimate, interval and bar, two approximate numbers from its own bootstrap standard error (SE):
  - **sees:** 2.8 × SE, about the smallest true effect whose interval would exclude zero four times in five;
  - **supports at:** bar + 2.8 × SE, about the smallest true effect the three-way rule would support four times in five.
- These rest on a normal approximation and run a little optimistic: for IN3 it gives 76% detection at the bar where the calibration measured 70%. Where a calibration card exists for the same design, cite its measured rates instead.
- When "sees" is larger than the bar, the record's first line reads "limited sensitivity: sees effects of about X or more; the bar is B".
- This replaces separate sensitivity cards for new work. The calibrations already run keep their records. No verdict already in the ledger changes.

**Q. Small cards admit on design and fixture.**
- For the new cards of section 2 whose ceiling is 60,000 CPU-seconds or less and which read only sources already qualified this campaign, admission is the design note committed and the fixture passed (amendment K, restated), with the plan pinned as the owner already does. Their cost probe is the first stage of the run. No separate native qualification campaign, bounded variant or timing pilot is required for them.
- If such a card fails in its first run for a runtime reason, it gets one repair and one rerun under its own ceiling.
- Cards above that ceiling (CH1, GO1, GO2) keep the owner's existing admission.

**S. Three tags on new rows.** Every ledger row written under this packet carries `record_kind` (claim, run or texture), `theory_tags` (the handoff tests it bears on, as `H12-T1` to `H12-T7`, for Round 12's tests 1 to 7) and `by_construction` (true or false). A run is a row that records an operation, such as a census, an export or a scoring pass; it has no supports or against field. A by-construction row is a scale report.

**T. Engine exports: the one exception to section 0.7.**
- Section 0.7 says outputs are aggregate only and no raw text leaves the repository. Section 2.6's four exports are the exception, and only as written there:
  - EX1 holds per-word timing labels, word sources and offsets for CoAuthor, with no text. The older rule for that corpus stands untouched: "No raw CoAuthor text leaves `private/` or `raw/`."
  - EX2 and EX4 hold text only from sources whose recorded licence permits copies (Stack Exchange under CC BY-SA; KLiCKe under CC BY 4.0). Each README carries the attribution, and EX2's states the share-alike condition.
  - EX3 holds identifiers and offsets for public documents.
- Every export stays on this machine's local disk, under paths git ignores in both repositories. None is committed, pushed, published or sent to any provider.
- Handing over this packet approves these four copies into ToMpathy's `.local/bench/`, by EV4's procedure (copy, hash, record). Nothing else about section 0.7 changes.

### 0.3 Ceilings

- MD rises from 34,400 to 120,000 CPU-seconds (18,751 charged), for MD3.s, TR1 and RR1.
- A new family, EX, has 100,000 CPU-seconds from the campaign's unallocated remainder: EX1 10,000; EX2 10,000; EX3 5,000; EX4 60,000; EM1 10,000. RR2 charges IN.
- Every other family ceiling and the campaign's 6,000,000 stand. Native charges at the 10 November digest sum to about 584,000.
- New cards carry their own ceilings in section 2.

## 1. Rulings

Each of these is a design decision the owner could not make for itself. Each is made here before any outcome of the affected cards exists, and the reason is recorded with it.

**R1. Reader memory and cost (family AT).**
- **(a) Build the measured guard.** `AT_GUARDED_BANK.md` anticipates it: "a later measured lower-memory guard would be a separately reviewed successor."
  - From now on every chunk records its peak private commit as well as its working set.
  - A reader's declared peak is 1.25 × the highest peak private commit seen on its completed chunks, rounded up to 0.5 GiB. Until a private-commit peak exists, use 1.5 × the working-set peak. That factor is a margin, not a measurement, and it is replaced by the reader's own first recorded commit peak.
  - For a reader with no completed chunk, use 2.5 × the bytes of its float64 weights.
  - A reader may start when commit headroom is at least its declared peak plus 7 GiB and free RAM is at least its declared peak plus 8 GiB. For a reader with a measured peak, the 26, 20 and 28 GiB gates are retired. For a reader with none, the commit line is the lower of this one and the existing gate (26 GiB, or 28 for the largest reader), but never less than its declared peak plus the 6 GiB hard floor.
  - The yield request line (7 GiB) and the hard floor (6 GiB) are unchanged.
- **What that does and doesn't do.** For GPT-2 medium (4.69 GiB working set) the start line falls from 26 GiB to about 14.5. For the engine's models it is about 14 (SmolLM2-360M) and 16.5 (Qwen2.5-0.5B). The 10 and 11 November readings were 11.99 and 10.54 GiB, with 34 to 40 GiB of RAM free. So (a) alone does not release a reader today. (b) finds out what would.
- **(b) Name the holder.** Every resource hold record adds: the commit limit, the commit charge, the page-file size and its peak use, and the five processes with the largest private commit (image name and GiB only). Write the first one at the first wake after handoff and copy it into that day's digest. The owner ends its own finished or orphaned processes. It stops nobody else's and does not change the page file.
- **(c) Engine models first.** Scoring order becomes: Qwen2.5-0.5B, then SmolLM2-360M, final-text context; then GPT-2 medium's remaining 37 chunks; then the rest in the original order. The float64 bank rule (AT-FP64-1) and the 0.0001-nat check are unchanged.
- **(d) Size the engine readers' bank to the ceiling.** GPT-2 medium's pilot ran at about 1.2 CPU-seconds per word (20,957 words in 25,189 CPU-seconds), so full banks may not fit AT2's 550,000. After an engine reader's first 20 chunks, project both engine readers' full final-text banks. If together they project to 400,000 CPU-seconds or less, score every writer's words. If not, score for every writer whole sessions in time order, up to the same number of writer-typed words each, the largest number that keeps the two readers together within 400,000.
- **(e) AT2's primary lands on the 3-gram and the two engine models.** Its definition is unchanged: the better engine model's held-out gain over the 3-gram, bar 0.002 nats per word. It lands when the two engine readers' banks under (d) are complete and verified. The curve over model size is secondary, is reported as readers complete, and blocks nothing.
- **(f) The selected reader is the better engine model.** AT3 and AT4 use the engine model with the larger AT2 gain (Qwen2.5-0.5B on a tie). The route to the engine is what the engine's own marks are worth, so the best of ten was never the right dependency.
- **(g) Nothing else waits on AT.** GO1 is released by R4. LA1 uses the better engine model when it exists and ranks after LA3 and LA4; its masked-model scoring needs no reader and may run as filler now. If commit headroom never reaches a reader's line this week, AT2 is recorded as held on memory with (b)'s record, and the engine's accuracy against stops comes from ToMpathy's benchmark on EX1.

**R2. Chess frame (family CH).**
- **(a)** The admitted month set for this campaign is April, May and June 2017, the three months whose census and independent replay are complete. July 2026 is withdrawn from Week 5. Its archive, pilot and conversion stay on disk, untouched. No July storage or latency qualification runs this week.
- **(b)** CH1's quotas keep their sizes and are filled from the three months: 7,000 blitz players and 1,000 each in bullet, rapid and classical, each player sampled once across the three months, months in proportion to each month's eligible players.
- **(c)** The policy-entropy temperature is fitted on April's sampled positions and applied to May and June; cells that use policy entropy exclude April.
- **(d)** The "2017 against 2026" texture cells (CH2, CH6) are withdrawn. Every other cell of the 44-cell grid stands.
- **(e)** The scaffold's merge and its qualification stand as designed, over three months instead of four. Report the merged frame's measured size at the wake after it is built. If it would leave less than the 20 GiB disk floor, stop chess there and say so in the digest's first line. Nothing is substituted.
- **Reason:** storage. No chess effect exists yet. A recent month can be commissioned later as a replication.

**R3. Mood controls (family MD).**
- **(a)** Controls qualify descendants one at a time. A human descendant may start when the controls that exercise its own handler have passed. MD3.s's three cases have passed with replay, so MD3.s starts now.
- **(b)** MD3.m is withdrawn from this week. Its record already says it is unqualified: its positive control, on 96 constructed participants by 30 trials, planted an effect and returned inconclusive. That says nothing about people. No further repair is commissioned.
- **(c)** MD3.p and the eight unrun controls are not required this week. MD3.p runs only if its own controls are built and pass after everything in section 3.

**R4. GO1's primary.**
- GO1's one primary becomes the encoder reader minus TF-IDF, at the same bar (0.05). The language-model reader becomes secondary and is added on the same roster when R1 delivers a reader.
- Today's pipeline refuses to run without AT2's receipt, and its support rule is the intersection of all three readers' context support. So a two-reader variant is built first (section 3): the same roster, the same distractors and the same author sample, the language-model arm switched off, and support defined as the intersection of the two readers.
- GO2's inference and ID1 are already built and start under the owner's existing admission.

## 2. New cards

Every card's design note records, before outcomes, the items section 2 of the 7 November packet lists, plus amendment P's two numbers once it lands. Seed 20261107. Uncertainty follows amendment L(c).

### 2.1 Family IN, extended (Crowd-enVENT; one handler extension, one fixture)

**IN5. FEAR's trigger, rebuilt** (H12-T1).
- **Why.** FEAR is the one tested trigger whose estimate sits at zero: 0.03 [-0.05, 0.10]. RAGE (0.27) and DISGUST (0.20) support, and PANIC/GRIEF leans yes at 0.18 and landed inconclusive. The handoff asks whether FEAR answers predicted harm, an unresolved and uncontrollable threat, or urgency. The theory thread's reason for the second candidate is two outside studies: some dopamine neurons answer unpredicted threat, and people take shocks to resolve uncertainty. In its words, FEAR's trigger may be closer to "unresolved" than to "harmful".
- **Data.** IN1's 547 prompted fear reports.
- **Three profiles**, frozen here:
  - **H, predicted harm** (IN1's items and signs): goal_support down, predict_conseq up, urgency up, self_control down;
  - **U, unresolved and uncontrollable:** predict_event down, self_control down, suddenness up;
  - **G, urgent:** urgency up, attention up.
- **Model.** IN1's: intensity on the index, controlling unpleasantness, confidence and the response-style mean. The style mean is cut to the six items in no profile: familiarity, goal_relevance, chance_responsblt, self_responsblt, chance_control, effort. H is re-estimated with that control, so its slope can differ a little from IN1's 0.03.
- **One primary:** U's standardized slope in fear reports. Bar 0.10.
- **Secondary:**
  - G's slope;
  - U minus H, and U minus G, on the same resamples;
  - the itemwise model: intensity on all of a profile's items together, for FEAR's seven distinct items and for RAGE, PANIC/GRIEF and DISGUST (this discharges IN1.w);
  - specificity: each profile's slope in fear reports minus its pooled slope in the anger, sadness and disgust reports, computed on unique items (below).
- **Fixed by construction, and what is done about it.** The six profiles share items, sometimes with opposite signs: self_control is down in H, U and PANIC/GRIEF and up in RAGE; urgency is in H, G and RAGE; goal_support is in H, RAGE and PANIC/GRIEF; other_responsblt is in RAGE and DISGUST. So one profile's slope in another channel's reports is partly set by that channel's own known loading. Every cross-channel number is therefore computed twice: with full profiles, for scale only; and with each profile cut to the items no other profile uses, which is the row to read. Those unique items are: H, predict_conseq; U, predict_event and suddenness; G, attention; RAGE, other_control; PANIC/GRIEF, accept_conseq; DISGUST, standards, social_norms and not_consider.
- **Map** (texture, 200 resamples): the 6 by 4 table of every profile (IN1's four, plus U and G) in every mapped prompt, in both versions. Its summary is the mean of IN1's four own-channel slopes minus the mean of their twelve cross-channel slopes, on unique items. This asks what IN1 did not: whether a channel's own trigger predicts its loudness better than another channel's trigger does (the analyst's addition). If it doesn't, the RAGE and DISGUST supports are about loud events in general.
- **Reading, fixed here.**
  - "Unresolved fits best": U supports and U minus H's interval lies above zero.
  - "Unresolved fits, not shown to fit better": U supports and U minus H spans zero.
  - "Urgent fits": G supports and U doesn't.
  - "None fits": no profile's interval clears the bar.
  - "FEAR's own" is added to any of the first three when the unique-item specificity interval lies above zero.
- **What it can see.** IN1's FEAR interval was 0.15 wide, so a slope near 0.21 supports about four times in five and a slope between 0.10 and 0.21 will mostly land inconclusive, as PANIC/GRIEF's 0.18 did.
- **Status: exploratory.** These 547 reports have already carried two FEAR tests. A support here is a lead for IN8 or a fresh sample, and its row says so.
- **Ceiling:** 8,000 CPU-seconds.

**IN6. Can a reader's trigger reading grade the writer's loudness?** (the analyst's addition; the engine's backward run).
- **Data.** The validation table's mapped prompts: 396 texts, five readers each.
- **Design.** Per text, the mean of the five readers' fit index for the text's channel (IN1's profiles). Regress the writer's own intensity on it, with prompt intercepts, controlling the readers' mean unpleasantness.
- **One primary:** the standardized slope. Bar 0.10. Writer-cluster interval.
- **Secondary:** the writer's intensity on the readers' mean attributed intensity (how much loudness gets through a text at all); each reader's own attributed intensity on her own fit index (same rater, scale only); U and G in place of H for fear texts.
- **What it can see.** 396 texts give an SE near 0.05, so it sees about 0.14 and supports at about 0.24. Expect an estimate with a wide interval. The size is the point: it prices panel three's route from trigger features to loudness with five human readers doing the reading.
- **Ceiling:** 5,000.

**IN7. What a text doesn't carry: stance against event** (H12-T3).
- **Why.** IN4 found readers miss the writer no more on trigger items than on others (0.009 [-0.04, 0.05]). The handoff adds that, descriptively, readers "miss the writer's stance toward consequences most", and names three stance items for a registered test: acceptance of consequences, not considering consequences, familiarity.
- **What the record already shows, declared here.** IN4 used the 396 validation texts of the four mapped prompts, and its per-item numbers are in `IN4_PRIMARY.json`. On those texts the three named items exceed the eight event items below by 0.10 rating points. They were named from those same numbers, so that lead is by selection. The five other stance items below exceed the event items by 0.004. So on those 396 texts the class does not reach beyond the three named items.
- **The clean test.** IN4 never used the validation texts of the other prompts: about 790 to 800 after the usual exclusions, with the count recorded at intake. The registered hypothesis is tested there. The handler extension lifts the filter that keeps only the four mapped prompts.
- **Classes, frozen here by wording, with no reassignment.** An item is *stance* when its statement is about what the writer expected, anticipated, held as a standard or did in her own mind. It is *event* when its statement is about what happened, who caused it or who controlled it.
  - Stance, named in the handoff: accept_conseq, not_consider, familiarity.
  - Stance, others: predict_event, goal_relevance, predict_conseq, goal_support, standards.
  - Event: suddenness, self_responsblt, other_responsblt, chance_responsblt, urgency, other_control, chance_control, social_norms.
  - Unclassed, reported only: self_control, attention, effort, pleasantness, unpleasantness.
- **Measures per item.** Excess error, as IN4 defined it (reader-to-writer error minus reader-to-reader error). Transmission: across texts, the correlation between the writer's rating and the mean of the five readers' ratings.
- **One primary:** the mean excess error of the three named stance items minus the mean of the eight event items, on the texts IN4 did not use. Bar 0.10 rating points. Text-cluster interval. Predicted positive.
- **Secondary:**
  - the five other stance items minus the eight event items, on the same texts (does the class reach beyond the three);
  - both contrasts by prompt group (negative, positive, other), with the grouping recorded before outcomes;
  - transmission: the event items' mean correlation minus the stance items' (Fisher z), predicted positive. Absolute error grows with an item's spread, so an item can look "missed" because writers differ more on it. If the error contrast is positive and the transmission contrast is not, the record's first line says "spread, not transmission".
- **Reading.** The primary supports: the handoff's hypothesis holds on texts it wasn't drawn from, for those three items. The second line then says whether it is a class (the writer's expectations and standards too) or just those three (how she takes the consequences, and whether she has been here before).
- **Ceiling:** 8,000.

**IN8. Control, FEAR and RAGE on a second corpus** (H12-T2). It waits on a source and never holds a slot.
- If `data/external/isear/` holds the ISEAR databank at any wake, together with a note from the curator stating the terms shown where he downloaded it, take it in under `DATA_INTAKE.md`'s rules. No note, no intake. If it's absent at the freeze, record "waiting on source".
- **Design.** Within fear reports and within anger reports, standardized intensity for respondents who said they could influence the event, minus those who said they were powerless. Map both options from the codebook's own value labels and freeze the mapping before outcomes. If the codebook has no such options, record "unsupported at source".
- **One primary:** the anger difference minus the fear difference. Predicted positive: control goes with stronger anger and weaker fear. Bar 0.30 standard deviations, because a slope of 0.15 per standard deviation, IN3's bar, corresponds to a difference of 0.30 between two equal halves. Respondent-cluster interval.
- **Secondary:** fear intensity on unexpectedness and powerlessness, against the other emotions (U's partial replication).
- **Ceiling:** 5,000.

### 2.2 Family LA, extended (AMI, ICSI; one handler, one fixture; no language model)

**LA3. Fresh lines against repeats** (H12-T4).
- **The prediction** (the handoff records it as the curator's): "repeats come without a preceding pause; fresh ones follow one." This is the first of three laughter tests the theory thread offered him (its question 5): fresh against repeat, laughs right after a boundary is tested, and encryption. He hasn't picked. The first runs here and the third inside LA4. The boundary test isn't in the handoff's ranked list and isn't run.
- **Units.** Dialogue acts laughed after by someone other than the speaker (LA0's window).
- **Groups.** An AMI scenario series (one team's four meetings); other AMI meetings singly; ICSI meetings by their series. Record the group map before outcomes.
- **Repeat.** The act shares at least two content lemmas, in order, with an earlier laughed-after act in the same group that ended at least 30 seconds before. Content lemmas exclude the corpus's 200 most frequent. **Fresh:** it shares none with any earlier laughed-after act in the group. Everything between is set aside and counted.
- **Pause.** Seconds from the end of the previous speech by anyone to the act's start, floored at zero, as log(1 + seconds).
- **Model.** Log pause on repeat, with speaker fixed effects, controlling act length, dialogue-act type, corpus, minutes into the meeting, whether the previous speaker was the same person, and log seconds since the last laugh by anyone.
- **One primary:** fresh minus repeat. Bar: a difference of 0.10 in log(1 + seconds), that is, 10% more in (1 + seconds). Meeting-cluster interval. Predicted positive.
- **Secondary:**
  - the same contrast among acts never laughed after, matched as LA1 matched (the general cost of saying something new);
  - the difference between the two;
  - fresh laughed-after acts against fresh acts not laughed after;
  - the rate of a filled pause (um, uh) at the act's start.
- **Rivals.**
  - *Quick wit.* A late quip gets no laugh, so laughed-after fresh lines are selected for speed. That selection runs against the prediction. A null therefore can't separate "joking needs no attention" from "slow jokes die". The third secondary shows which.
  - *Bouts.* Lines inside a laughing bout come fast and are often riffs. The laugh-recency control answers this, with a texture cell dropping acts within 5 seconds of an earlier laugh.
- **Null.** Shuffle the repeat labels within speaker and meeting, 20 times. The working bar is the larger of two numbers: 0.10; and the null's mean absolute contrast, doubled, plus three of the null's standard deviations. MD3's threshold was built the same way.
- **Case:** at least 200 repeat acts from at least 30 meetings. Fallback: two shared content lemmas in any order, 10 seconds, reported "below floor, descriptive".
- **Texture:** 5-second and 120-second exclusions; three shared lemmas; AMI and ICSI separately; the speaker's own silent gap where she was also the previous speaker.
- **Ceiling:** 40,000.

**LA4. Shared background, after the social layer** (H12-T5).
- **Why.** LA2's raw comparison returned 0.003 [-0.022, 0.029] against a bar of 0.02 on AMI. Its interval was wider than its bar, so it could not see the registered effect. Ghost's V27 found a laugh-like marker worth only as much as the reader's model of its other causes.
- **Units.** Each laugh that starts after at least 3 seconds with no laugh has a starter. Every other participant present is a possible joiner, and joins if she starts laughing within 1 second.
- **Model.** Linear probability of joining, with a fixed effect for each laugh and for each person within a meeting. Those absorb how funny the moment was, who else laughed, and each person's base rate and role. Situational terms: she spoke the line just before the laugh; she spoke in the previous 10 seconds; her laughs in the previous 60 seconds.
- **One primary:** on AMI, the coefficient on starter and joiner sharing a native language. Bar 0.02, as LA2. Meeting-cluster interval. AMI is the corpus with native-language metadata; ICSI has varieties of English and regions, which LA2 rightly keeps as different constructs.
- **Secondary:**
  - ICSI, separately: shared English variety, and shared region;
  - ICSI prior co-attendance, as log(1 + earlier corpus meetings both attended). This is the theory thread's encryption test in the form these corpora allow: does a laugh that needs shared history draw in those who have it? Shared history is closer to what the account means by shared background than native language is (the analyst's addition);
  - whether the starter spoke the laughed-at line.
- **Scale report:** the social layer's own coefficients, with roles in place of person effects, and the fit with and without the situational terms.
- **Null.** Permute background labels among a meeting's participants, 20 times.
- **Reading** (the handoff's): "If the residual predicts shared background where the raw rate did not, the three-layer account has its first support on people."
- **Texture:** 2-second and 3-second windows.
- **Ceiling:** 30,000.

### 2.3 TR1. Is a trait a level or a sensitivity? (H12-T7; family MD; Rutledge repeat plays)

- **Why.** The handoff: "A level predicts rebound toward the person's own usual amount after a forced high or low. A sensitivity predicts a bigger response per unit of input and no rebound." The theory thread's question 4 to the curator offers three answers: both, the level only, or sensitivity only. Its own read of the outside evidence is both. In the handoff's control terms this is a difference in reference against a difference in gain (the analyst's reading).
- **Units.** The participants in MD3's repeat set with at least two completed plays (about 15,000).
- **Per play, two numbers.** Regress the play's happiness ratings on recent luck. Luck on a trial is the chosen gamble's outcome minus its expected value, zero when she took the sure option, summed over earlier trials with MD1's forgetting factor (0.65). The intercept is her **level**: her rating at zero recent luck. The slope is her **gain**: her response per unit of input. Luck is random by the game's design.
- **Stability.** For consecutive plays, the correlation of gains across the two plays divided by the square root of the product of the two plays' reliabilities. Two estimators of reliability are built: from each play's sampling variance, and from split halves of each play's rating occasions. The planted controls choose: the one with the smaller error on the planted 0.5 case is frozen before the human run. A play has few ratings (record the count at build), so the ratio can pass 1; report it unclipped.
- **One primary:** the gain's stability. Reading bands fixed here: above 0.5, a stable property of the person; below 0.2, not one; between, partly. "Supports a stable sensitivity" only when the whole interval lies above 0.5.
- **Case check first.** The gain's true variance across people must be positive with its interval clear of zero. If it isn't, the record says no between-person differences in sensitivity could be measured in this task, with the smallest variance the design would have seen. That is a limit of this design, not a finding of absence.
- **Secondary:**
  - the level's stability. This is a scale report: a person's habitual use of the rating scale is stable for reasons that aren't mood;
  - the gain divided by the play's rating spread;
  - carry-over: the next play's first rating on the previous play's total luck, within person. A level predicts she starts at her own usual place (slope near zero). Where play times are recorded, by gap;
  - the correlation of level with gain.
- **Planted controls:** 2,000 synthetic participants on the real trial structure, with residual autocorrelation matched to the real plays, at gain stability 1, 0.5 and 0. The frozen estimator must return each within 0.1. If neither estimator does, TR1 is recorded "estimator unqualified" and does not run on people.
- **Outside evidence.** In this task, depressive symptoms tracked the baseline mood parameter while the response to prediction errors was intact ([Rutledge et al. 2017](https://doi.org/10.1001/jamapsychiatry.2017.1713)). That is one published vote for level.
- **Ceiling:** 40,000.

### 2.4 CH7. A floor or a ladder (H12-T6; family CH; no engine analysis)

- **Why.** The handoff: "Do players change risk more after dropping below a personal reference (a rating floor, a previous peak) than after rising above it?" Standing is under review in the theory, so this card reports and builds nothing on it. The theory thread's question 1 to the curator offers good standing only (a floor everyone can hold), two set points, or rank only. A game rating is not standing in a room, so this card can only say which of those shapes behaviour takes around a personal reference.
- **Data.** CH6's sessions as CH6 builds them, from the three months' player histories (the 2% player sample). The source has no game end times, so a session is consecutive rated games whose starts are less than 30 minutes apart, and each player's last record is censored, as in CH6. Blitz first. Sessions containing a game with a rating change above 25 points are dropped and counted (provisional ratings).
- **Two personal references.**
  - *Recent level:* her rating at the session's first game.
  - *Window best:* her highest rating so far in that time-control class since her first game in the three months, after her first 30 games.
- **Outcome: playing on.** After each game, does she start another within 30 minutes? Each further rated game puts her rating at stake, which makes it the nearest thing here to taking the next gamble.
- **Model.** A linear probability model of playing on, with player fixed effects, games so far in the session, the last result, a losing-streak term, the last opponent's rating gap and hour of day; then distance from the reference in units of 20 rating points, with separate slopes below and above it. A slope is a change in the probability of playing on per 20 points.
- **One primary** (recent level): the size of the slope below minus the size of the slope above. Bar: one tenth of the sample's overall probability of stopping, in the same units. Player-cluster interval.
  - *Floor:* the contrast supports and the slope above lies inside the bar's band.
  - *Ladder:* both slopes lie outside the band and the contrast lies inside it.
  - Anything else is reported as mixed.
- **Secondary.**
  - *Window best.* Among wins only: stopping after a win that sets a new best, against a win that leaves her within 15 points below it, at equal rating gain. Then the slope of playing on over distance below the best. A published study of 133 million games found players "exert effort to set new personal best ratings and quit once they have done so" ([Anderson & Green 2018](https://doi.org/10.1073/pnas.1706530115)).
  - *Pace:* the median share of the clock used per move in the next game, on the same terms.
- **Rivals.** Loss-chasing: the last result and the streak term are in the model, and the claim is the slope on distance beyond them. Rating drift back toward skill: answered by the null.
- **Null.** For each player, 20 simulated histories in which results follow the rating gap's expected score and playing on depends only on games so far, last result and hour, fitted on her own data. The working bar is built as LA3's is.
- **By construction:** a rating can't sit below the session's start without a loss or a draw as favourite; the last-result term removes that. A new best always follows a win, hence wins only. The window best understates a true personal best, which pulls its estimate toward zero; a cell restricted to accounts whose first game in the window shows a provisional-size change has the true best.
- **Case:** at least 3,000 players with 5 or more sessions. Fallback: rapid pooled with blitz.
- **Ceiling:** 60,000.

### 2.5 Re-reads (H12-T6, H12-T2)

**RR1. The phone game's other rows.** The handoff cites MD3's first-play result as one vote for a floor, and the theory thread noted that on repeat plays "the answer depends on which reference you assume". `WEEK5/MD3_PRIMARY.md` holds those repeat-play rows, and they read differently from the first play:
- against the play's start, on repeat plays: slope below -0.001 [-0.023, 0.019], slope above -0.169 [-0.182, -0.156]. The first-play pattern (0.260 below, -0.021 above) is reversed: nothing below the start, less gambling the further ahead;
- against the best earlier score: below -0.090 [-0.102, -0.079], above -0.109 [-0.124, -0.094], contrast 0.019 [-0.003, 0.041]. No kink at a previous best.

File these in the return (section 5) and add one computation: the same two-slope fit by play number (first, second, third, fourth and later), within participants who have at least three plays, so that who comes back is held fixed. Config of MD3's handler; no new fixture. Ceiling 10,000 from MD.

**RR2. IN3, restated.** In the return, restate IN3 with: its estimate and interval; its calibration's measured detection rate at the bar (0.70 and 0.69 against the 0.80 required); and amendment P's two approximate numbers from IN3's own bootstrap SE. Add one sentence: the design fell just short of seeing an effect of the registered size, and the estimate lay inside the band. No verdict changes. IN8 is the larger sample.

### 2.6 Engine exports (to ToMpathy; local disk only; amendment T)

ToMpathy's packet of the same date runs benchmarks on these. Write each under `corpora/store/exports/engine_bench_20261111/` with a README (definition, counts, licence, the ledger rows it rests on), then copy to ToMpathy's `.local/bench/` by EV4's procedure (copy, hash, record). Never commit either copy. Never send either to a provider.

**EX1. Stop labels for CoAuthor's final texts. No text.**
- For every word in each session's final text: session id, hashed writer id, the writer's fold (five folds by writer), start and end as Unicode code points in the normalised final text, and its source (typed by the writer, inside an accepted suggestion, or part of the prompt).
- For writer-typed words only: the stop label (Week 4's defaults: fluent posterior below 0.5 on the preceding interval) and the log pause.
- Per session: the SHA-256 of the final text after NFC normalisation, line endings as `\n`, trailing whitespace stripped. The spans refer to that normalised text. ToMpathy replays the same sessions from its own local copy of the logs and checks the hash.
- The README states the number of words in the final texts by source. ToMpathy uses the stop labels for its attention benchmark and the sources for its first test of AI involvement.

**EX2. Edit-reason bundle (Stack Exchange).** From GO3's held-out folds: 5,000 body edits, 1,000 per reason category, each with before and after text, the reason category, the post id (for attribution under CC BY-SA), the user fold (five folds), and GO3's classifier output. Include the frozen feature definitions.

**EX3. Goal task file.** GO1's task for PEPs and EIPs: document ids, the pinned commits, section offsets, each document's 49 distractor ids, and a hashed first-author id. Public sources.

**EX4. Essays with stops (KLiCKe).** The corpus is CC BY 4.0 ("The source licence is CC-BY-4.0 as previously inspected"). For each replayed session: the final essay text, and for every word typed in order its start and end as Unicode code points in that text, the pause before its first keystroke, a stop label at 2 seconds and one at the essay's own 80th percentile, and a flag for words inserted later. It carries no writer id: the corpus's sessions can't be linked to writers. Sessions with parse failures are excluded and counted. The README carries the attribution. Build this last.

**EM1. Materials for the two emails.** The handoff's housekeeping: the curator emailed the style-change shared task organizers and the ScholaWrite authors on 11 November, and "The repo should be able to produce them the day a reply arrives." Build two private folders, each with a README and a one-paragraph plain summary: hash lists and scripts for the cross-year overlap in the 2024 hard validation set; fold definitions and a per-project table for the shared before-text prefixes. Hashes and counts only, no third-party text. The agent sends nothing and contacts nobody.

## 3. Dispatch and builders

**At handoff, the owner:**
1. files this packet and records R1 to R4 in the Week 5 index;
2. writes amendments N to T, edits `FAMILY_CEILINGS` in `runners/drive/cards/week5_policy_v2.py` (MD 120,000; EX 100,000) and pins it before the first MD3.s, TR1 or EX plan, and writes the first resource record (R1(b));
3. starts three builders;
4. starts what is already built: MD3.s, GO2's inference, ID1;
5. then works the chess frame until CH1's collection is running.

**Builder queues.**
- **Builder A (chess):** the three-month frame and roster; CH1's collection as queues; CH7; then CH2 to CH6's analysis plans as positions arrive.
- **Builder B (appraisals and laughter):** IN5 to IN7 as one extension; then LA3 and LA4 as one handler; then IN8 if its source is present.
- **Builder C (engine and mood):** GO1's two-reader variant (R4); EX1, EX2, EX3; then TR1; RR1; EM1; EX4.
- **The owner:** every review, admission and landing; R1's guard; RR2; BK. Recoveries of the full comparison take owner time only after the first four items of the next list are staged.

**Order for staged cards.**
1. CH1's collection queues (up to six slots; everything else fits around them);
2. IN5, IN6, IN7;
3. EX1, EX2, EX3;
4. CH7;
5. MD3.s, GO1's two-reader variant, GO2, ID1;
6. LA3, LA4, and IN8 if its source is present;
7. TR1, RR1;
8. readers, whenever R1's gate passes, engine models first; then AT2, AT3, AT4;
9. EM1, EX4;
10. LA1's masked scoring and the BK backlog, as filler.

A builder delivery is reviewed at the wake it arrives, ahead of everything except starting admitted work.

**What isn't built by the freeze** is listed in the final digest by name with the step it stopped at. Nothing carries over silently.

## 4. What each result changes

| Handoff test | Card | If it holds | If it doesn't |
|---|---|---|---|
| 1. Rebuild FEAR's trigger | IN5 | FEAR's row moves toward "an unresolved threat", and its overlap with Stress has to be separated on people (the handoff's words) | "Prompted fear events are too mixed to read from appraisals, and the row needs a different kind of data" |
| 1, beyond the ask | IN5's map | Each channel's own trigger predicts its loudness best: the RAGE and DISGUST supports are about those channels | They are about loud events in general, and the trigger reading needs a sharper test |
| 2. Control, FEAR and RAGE | IN8, if the source arrives. RR2 restates IN3 and decides nothing | With sensitivity passed and a flat contrast, the brake cells come out of the table as written | A contrast at the bar keeps them |
| 3. Where readers miss the writer | IN7 | The first measured statement of what a text doesn't carry, on texts the hypothesis wasn't drawn from. Its second line says whether that is a class or three items | The lead of the three named items was particular to the four mapped prompts |
| Engine | IN6 | A price for grading loudness from trigger features read off a text | The same number says the route is too weak to show |
| 4. Laughter, fresh against repeat | LA3 | Pauses separate made jokes from habit jokes: a clean positive class for the departure detector | Joking doesn't need a pause, or slow jokes die; the third secondary says which |
| 5. Laughter, social layer first | LA4 | The three-layer account's first support on people | Shared background doesn't show in joining even with the social layer removed, at the sensitivity the record states |
| 6. A floor or a ladder | CH7, RR1 | Floor only: supports reading Standing as good standing. Symmetric: rank (the handoff's words) | Mixed, reported as such. RR1 already qualifies the phone game's vote |
| 7. A level or a sensitivity | TR1 | Gain is a stable property: sensitivity is a trait here | Level only, or differences in gain too small for this design to measure |
| 8. Edit reasons, personal habit | parked | n/a | The reason labels come from a keyword map of editors' comments, so a "habit" would be a habit of commenting. It needs labels made another way |
| 9. Engine note: joint inference | Ghost V28's G1; ToMpathy's TP2, TP5 and TP4 | n/a | n/a |

## 5. Return to the theory thread

Write `results/phase_2_4_stage_15/WEEK5/THEORY_RETURN.md`. Update it at each daily digest and close it with the drain addendum. It lives with the results, not under `docs/theory/`, which this packet does not touch. It mirrors the handoff:
1. **One table, one row per handoff test:** the card; its state (landed, running, or waiting, and on what); the estimate with its interval; the bar; amendment P's two numbers; which of section 4's two branches the result falls in; anything fixed by construction.
2. **Maps:** IN5's 6 by 4 table in both versions; IN7's per-item table with classes; LA4's social-layer coefficients; CH7's slopes by reference; TR1's stability table.
3. **Re-reads:** RR1 and RR2.
4. **Could not do, and why,** one line each.
5. **Sources not present.**

It names the branch and stops. The theory thread does the reading.

## 6. Cross-repository

| To | What | When |
|---|---|---|
| ToMpathy, `.local/bench/` | EX1 to EX4, each with its README and hash (amendment T) | As each is built |
| ToMpathy, `docs/` | Reviewed handoffs as in the 7 November packet, plus AT2's primary under R1(e) | As each lands |
| Ghost, `docs/exchange/sounding-line-week5-2026-11-07/` | CH7, TR1, IN5 and LA4, as each lands | As each lands |

When Ghost's V28 table for visible stocks arrives in `docs/exchange/`, CH4's record cites its row for records needed. Nothing waits on it.

## 7. Reporting

The daily digest keeps its order and adds, at the top: the day's resource record (R1(b)); each builder's queue and state; the idle slot-hours by cause, with the single step holding the most slot-hours named first. The final digest and the drain addendum are as the 7 November packet set them, with section 5's return attached.

## 8. Pre-mortem

- **Slots idle again.** The narrow point is the owner's serial review. *Guard:* long queues (N), builders that stage (O), small cards on design and fixture (Q), two slots kept for short cards, and the order of a wake.
- **Commit headroom stays under R1's line.** Then readers wait and nothing else does (R1(g)). R1(b)'s record says who holds the commit.
- **The three-month frame doesn't fit the disk.** R2(e): chess stops there and the digest says so first.
- **IN5 is a third look at the same reports.** It's labelled exploratory, and IN8 is the fresh sample.
- **IN7's classes are the analyst's.** They are frozen here by a stated wording rule, the three picked items are tested only on texts they weren't picked from, and what the used texts already show is declared.
- **LA3 finds too few repeats.** Its floor and fallback.
- **CH7's playing-on isn't risk.** It is stated as the nearest measure, and pace is beside it.
- **TR1's variance isn't measurable.** The record says so as a limit of the design.
- **An export leaks.** Amendment T: local disk, ignored paths, hashes, no commits, no providers, and EX1 holds no text.

## 9. Triggers

Unchanged from the 7 November packet's section 9.

## Sources

- **This repository, at `0bafb81c8`:** `AGENTS.md`; `CURRENT_STATUS.md`; `results/phase_2_4_stage_15/WEEK5/DIGEST_20261107.md` to `DIGEST_20261110.md`; `AT_M00_CHUNK0128_RESOURCE_HOLD_20261110.md`; `IN4_PRIMARY.json`; `IN_IC_COMPLETE_CONTINUATION_20261111.md`; `IN3_IC_HUMAN_COMPLETE_20261111.md`; `CH0_JULY_PILOT_20261108.md`; `CH_JUNE_CENSUS_COMPLETE_20261110.md`; `MD3_PRIMARY.md`; `MD3_M_POSITIVE_GATE_FAILURE_V4_20261110.md`; `KLICKE_SOURCE_COMPLETE.md`; `docs/design/stage-15/week5/AT_GUARDED_BANK.md`, `CH_CENSUS_STORAGE_V1.md`, `CH_SCIENTIFIC_ADMISSION_SCAFFOLD.md`, `GO1-grid.md`, `GO1-selected-reader.md`, `LA.md`, `MD3-followup-implementation.md`; `docs/design/stage-15/drive/PACKET.md` (privacy).
- **The theory handoff:** `claude/THEORY_HANDOFF_2026-11-11.md` (Round 12).
- **The curator's message of 11 November 2026, 08:03 PST.**
- **Outside:** [Anderson & Green 2018, Personal bests as reference points](https://doi.org/10.1073/pnas.1706530115); [Rutledge et al. 2017](https://doi.org/10.1001/jamapsychiatry.2017.1713).
