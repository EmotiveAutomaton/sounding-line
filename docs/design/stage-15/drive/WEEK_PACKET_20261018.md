# Sounding Line packet, 18 to 25 October: finish the screen, test the engine's own outputs, then directed reading

*Spec sheet for the Sounding Line agent. It runs from handoff to Sunday 25 October, 22:00 PDT. Every decision is made here, including the kinds you have been asking the curator. Return to him only on the triggers in section 8.*

## 0. How to run this

- **What stays and what's replaced.**
  - Rules 1 to 7 of the 18 October mid-run errata stay in force.
  - Its section 3 dispatch order for cards not yet started is replaced by sections 2 to 6 here.
- **What changes this week: the screen narrows.**
  - The work turns to the engine. The person shows far more in production than in selection. PMAP identifies:
    - 98% of writers from rhythm;
    - 47% from style;
    - 16% from handling, seven times chance.
    
    The content channel is uninterpretable: its control is invalid, and the taste instruments are blind.
  - The question now is whether ToMpathy's own outputs carry that signal, and which records the engine should read first.
- **New cards and the family counters.** EV, DR and NP cards are instruments; GEN1 and SDT1 are hypothesis tests. None of them counts toward family null counters. The remaining screen cards keep their families.
- **Defaults hold** unless a card says otherwise:
  - one primary contrast with its direction;
  - writer-cluster 95% intervals from 2,000 resamples;
  - at least 200 within-writer permutations (seed 20261018), flagged when the permutation mean exceeds a quarter of its standard deviation;
  - same-row fake-writer controls with a real-writer paired bootstrap;
  - a known-answer check before production;
  - descriptive probabilities only.

## 1. Standing decisions (do these; don't ask)

Today the curator answered three questions by hand: the D33 supported match, the V4.c split and the Jester complete records. These rules cover that class of question from now on.

| # | Situation | Do this |
|---|---|---|
| S1 | Required support is incomplete (missing matches, unsupported controls) | Run the supported subset as a separately labelled variant. Report the retained and dropped units. The original question stays open; never impute |
| S2 | A source has a few incomplete records | Quarantine the minimal set, label the changed population, proceed. Keep the original files |
| S3 | A source defect affects completed results | Hold the affected results. Run one canonical successor per affected primary, separately labelled. Keep the originals as history |
| S4 | A card projects past its cost ceiling | Up to 2× the ceiling: continue and log it. Past 2×: pause at a checkpoint, dispatch the next card, report at the digest |
| S5 | A card's wording is ambiguous | Take the reading that keeps the original question open and is cheapest to reverse. Record it in the card |
| S6 | A dependency won't arrive before the Wednesday freeze | Mark the card blocked, naming the dependency, and move on |
| S7 | Anything else | Choose by S1 to S6's spirit, record the choice and the reason in the card, and report at the digest. No waiting |

## 2. Finish the running wave (Sunday to Tuesday)

In this order, as slots free:

1. **V4.c is done and failed its null gates** (`V4.c-split.md`, 09:56).
   - The taste lens stays blind. D2's hierarchical extension and D11's writer-slope extension close for this campaign.
   - The untried remedy is the 199-null whole-pipeline Monte Carlo reference, a simulated null in place of the approximate one. It goes last in the post-talk backlog.
2. **D33 supported match:** launched at 10:26 (`102d317e3`). Let it finish.
3. **Continue as authorized:**
   - D33.fake, D30.v2 and D30.fake, the full D30.p;
   - P7-D33 at its scope, with the common word-event validation;
   - the Jester ratings recovery;
   - P1 on the GPU when its floor is met;
   - D24's saved repaired attempt, which is about 2× its cap and continues under S4.
4. **Canonical-choice successors (CC).**
   - One card per affected primary, each rerunning its frozen primary with canonical inserted choices: **D38, then D32, D4, D14, D2** (D2's primary only; its extension is closed).
   - Each is labelled "canonical successor", with the original kept. Reuse saved extractions where the defect doesn't touch them.
   - D38 goes first because its primary was the only exposed positive.
   - **Costs.** The originals of D38, D4 and D14 took under 20 minutes each. D32's took about 9.5 CPU-hours, so its successor needs a verified pilot and about 10 to 12 CPU-hours. Start it right after D38 so it finishes before Wednesday 06:00. If its pilot projects past that, it moves to the post-talk window.
5. **Gear 3 K and D31** as authorized: intake and the known-answer rung by Monday 12:00, spend cutoff Monday 17:00, at most $10.

**Demo-preparation reservation.** ToMpathy needs its essay reading finished for the Thursday talk.
- ToMpathy writes `tompathy-demo-prep.lock` beside the shared slot directory at handoff. It stays until ToMpathy writes `availableModulesComplete` or Tuesday 20:00 passes, whichever comes first.
- While it exists:
  - keep one counted CPU slot free for ToMpathy;
  - start a card only if free RAM after its measured peak stays at least 8 GiB. Take the peak from the card's pilot receipt, or assume 4 GiB if it has none.
- Running cards continue.

## 3. Pruned from this campaign

| Card | Disposition |
|---|---|
| D16 writer verification | Closed as answered by PMAP; no run |
| D37 three entries, D19 shared recipes, D36 jokes, D5, D7, D9, D10 | Post-talk backlog; run only when no section 4 or 6 card can use the slot |
| Tier 1b after P1 (D21, D13, D27 and the P1 extensions) | Run if P1 lands before Wednesday 06:00; otherwise post-talk backlog |

## 4. Does the engine's own output carry the person? (Monday to Wednesday 06:00)

- **The pin.** This packet amends the 17 October pin rule (ToMpathy at `82789fd`) for the EV cards only. They pin ToMpathy at `certified-fit-1` (`5f3ad0a`). Its engine package is byte-identical to ToMpathy's frozen demo build. Every other card keeps the old pin.
- **The tool.** ToMpathy delivers `scripts/export-engine-features.py` at that pin by Monday 12:00. It is offline: texts in, per-text JSON out.
  - **Output:** habits, per-word departure scores from its Qwen2.5-0.5B preview reader with character spans, recurring-departure ("signature") phrases, and pins.
  - **If it isn't there by Monday 14:00,** write a thin wrapper that imports `tompathy_engine` at that pin and calls the same functions.
  - **Record** the engine and reader pins in every card.
- **The input.** Run it over the 1,399 final documents. Keep P5's character provenance so writer-typed spans can be separated from accepted suggestion text.

### EV1. Do the engine's departures mark hesitation?

- **Question.** ToMpathy marks high-departure phrases (one to three content words, plus its top-decile sentences) "where attention likely went; untested". In human writing logs, do the words it scores high follow longer pauses than words it scores low, within writer?
- **Rows.**
  - D33's primary rows (78,602 writer-typed words, 41 writers, with their pre-word intervals and covariates), restricted to words that survive into the final document and that the engine scores.
  - The engine scores only content words: no stop words, numbers, names or code. Report how many rows remain.
  - Departure is the exporter's per-word score, (surprisal in nats minus the page median) divided by the page interquartile range.
- **Primary.**
  - The within-writer slope of log pre-word pause on departure.
  - Writer and session intercepts.
  - Covariates: exactly D33's (population surprise, word length, log frequency, sentence start, following punctuation) plus D33's history-surprise term.
  - Direction: positive.
- **Controls:**
  - 200 within-session permutations of departure;
  - a known-answer check: a planted pause on high-departure words is recovered.
  - A fake-writer control doesn't apply, because departure is computed per document; say so in the card.
- **Route.** The result becomes ToMpathy's departure badge:
  - positive: "tested on human writing logs: flagged words came after longer pauses";
  - null: "tested: no pause association".
- **Cost.** About 3 to 4 CPU-hours for the export, under 1 for the analysis.

### EV2. Do the engine's signatures belong to the writer?

- **Question.** Are the phrases ToMpathy calls signatures the writer's, recurring in her other sessions, or the page's?
- **Measure.**
  - For each session's signature phrases, the rate per 10,000 words at which they appear (lowercase exact match) in the same writer's sessions on other prompts.
  - Against that, the rate in other writers' sessions on those same prompts.
- **Primary.** Own minus other, writer bootstrap. Direction: positive.
- **Support floor.** A signature needs a positive-departure phrase among the top 15 that recurs in at least two sections or paragraphs of one document, and short CoAuthor documents may yield few.
  - Count signatures on 100 documents first.
  - If the full corpus would give fewer than 200 signature phrases, or fewer than 20 writers with any, record EV2 as unsupported and skip it.
- **Controls:**
  - 200 session reassignments to fake writers on the same sessions;
  - a known-answer check with a phrase planted across one writer's sessions.
- **Route.**
  - Positive: the signature badge says "recurs in the writer's other work".
  - Null: "page-local".
- **Cost.** Under 1 CPU-hour after EV1's export.

### EV3. Do the engine's habit cards identify the writer?

- **Design.**
  - **Profile:** each writer's half-A and half-B averages of the engine's habit vector: connectives and punctuation per 1,000 words, sentence-length mean and spread, quoted share.
  - **Text used:** two variants, the final document as ToMpathy would read it, and writer-typed text only.
  - **Procedure:** PMAP's procedure exactly (prompt-alternating halves, fixed gallery, nearest neighbour).
- **Primary.** Final-document identification accuracy minus the fake-writer mean, paired. Direction: positive.
- **Report.** Both variants beside PMAP's style row.
- **Cost.** Under 1 CPU-hour.

### EV4. The engine feature table

Deliver `ENGINE_FEATURE_TABLE.json` and `.md` at the Tuesday 20:00 digest, to ToMpathy and Ghost.

**Rows:** every channel from PMAP, V3, D17, D29 and EV1 to EV3.

**Fields:**
- the input it needs (final text, revision history, timing log or suggestion log);
- the exact definition;
- real and fake identification;
- median split-half reliability;
- records needed for 0.8 reliability;
- control flags;
- caveats, including that logged rhythm carries device and recording context;
- FINDINGS identifiers.

**Word lists.** Export the style channel's 100 most frequent words and 22 punctuation marks, and the rhythm channel's 20 bigrams, as aggregate definitions. They are common words and letter pairs, not participant text. If the dataset's licence forbids it, export their hash instead. Then ToMpathy's badge quotes the 47% only for "Sounding Line's definition", and its own list is labelled as its own.

ToMpathy's person entry (its B2) and badges (its B8) read from this file.

## 5. Wednesday freeze (unchanged)

- No new starts after 06:00. Running work drains by 12:00. The machine goes to ToMpathy until Thursday 07:00.
- The Wednesday 20:00 digest covers everything landed.

## 6. Post-talk campaign: directed reading (Thursday 07:00 to Sunday 22:00)

**Opening the window.** This packet is the curator's authority to reopen dispatch after the talk.
- From Thursday 22 October 07:00 to Sunday 25 October 22:00 PDT, the 17 October packet's section 2 operating rules and the mid-run errata's rules 1 to 7 apply again.
- The current batch runtime hard-codes Wednesday's no-new-start time. Open the window in a new runtime version with its own no-new-start time of **Sunday 20:00** and a drain by 22:00.
- Restore `transition_only: true` at Sunday 22:00.

### DR1. Which records should the engine read first?

- **Question.** For a writer with many sessions, does choosing the next session by expected information reach a stable person estimate with fewer sessions than chronological or random reading?
- **Writers:** those with at least 12 sessions on at least 3 prompts.
- **Reference:** each writer's style, rhythm and lean profiles from all her sessions.
- **Policies:**
  - chronological;
  - random (200 orders);
  - directed: the next session is the one expected to reduce the variance of her profile most, judged only from what is known before reading it (prompt identity and novelty, length, date). A session's own profile is never used to choose it; say so in the card;
  - directed with 20% of picks at random.
- **Measures:**
  - sessions until PMAP's gallery identifies her and stays correct;
  - sessions until every profile feature is within one standard deviation of its reference.
- **Primary.** Directed minus random sessions needed, on style. Style is the channel ToMpathy has on web pages. Direction: fewer.
- **Selection probabilities.** Log them for every pick. Any population estimate built from directed samples is reweighted by them, since actively chosen samples are unrepresentative.
- **Route.** This gates the order in which ToMpathy reads a maker's other works (its B2), not its within-page scheduler.
  - If directed reading at least matches random, ToMpathy reads a maker's other works prompt-diverse first.
  - If it does worse than random, ToMpathy reads them in date order.
- **Cost.** Under 2 CPU-hours.

### NP1. How often do the logs contain probes?

- **Question.** Ghost's results say probes, not passive choices, separate mechanisms. How often do real sessions contain probe-like events?
- **Count per session:**
  - substantial corrections of accepted text (D38's event definition);
  - runs of three or more consecutive dismissals;
  - repeat sessions on the same prompt.
- **Report.** Rates per session and per writer. CoAuthor's events don't map cleanly onto Ghost's probe types, so report rates only, not expected information.
- **Route.**
  - **Rare probes,** under one per session: ToMpathy must ask (its owner probe card) to learn goals.
  - **Common probes:** directed reading should mine them.
- **Cost.** Under 1 CPU-hour.

### GEN1. Is the writer easier to find in stories than in arguments?

- **Question.** The curator holds that "you find the author in fiction more". Nobody seems to have tested it with the same writers in both genres. CoAuthor has creative and argumentative prompts.
- **Writers:** those with at least 4 sessions on at least 2 prompts in each genre, as PMAP's split needs. Report how many qualify. If fewer than 15 do, use one prompt-alternating split across both genres and report genre-specific accuracy within it, labelled as the fallback.
- **Design.** PMAP's procedure (fixed gallery, nearest neighbour) run separately within each genre, for the style and rhythm channels, on matched numbers of sessions and typed words per writer.
  - Match by subsampling the longer genre.
  - 2,000 paired real-writer draws.
  - 200 session reassignments.
- **Primary.** Style identification in stories minus style identification in arguments. Direction: positive.
- **Route.**
  - **Positive:** ToMpathy's play and fiction weighting gains a measured basis (with Ghost's N18 threshold).
  - **Null or negative:** the claim stays a hypothesis, and ToMpathy weights genres equally.
- **Cost.** Under 1 CPU-hour.

### SDT1. Lean as criterion (conditional on Ghost N17)

**Runs only if** Ghost's N17 shows that criterion and sensitivity separate at about 100 records per maker, with its no-taste gate passing.

**Design:**
- Estimate each writer's criterion (lean) and sensitivity against a leave-one-writer-out population acceptance model (P4's backbone) as the quality reference.
- Split-half reliability of each.
- The same-row fake-writer control.

**Primary:** sensitivity reliability. Direction: positive.

**Backlog, idle slots only, in order:** D37, D19, D36, D5, D7, D9, D10, Tier 1b if P1 is still not landed, then V4.c's 199-null Monte Carlo reference.

## 7. Theory filing and reporting

- File the curator's 18 October walkthrough at the next 20:00 digest, from `SOUNDING_LINE_THEORY_FILING_2026-10-18.md`, under the theory format rules and `tools/theory_lint.py`.
- **Digests:** daily at 20:00, as now.
- **The final digest is Sunday 25 October, 20:00.** It includes:
  - the EV, DR, NP and GEN1 results;
  - the campaign's positives, listed first, each with its control status.

## 8. Triggers (the only reasons to contact the curator)

1. A paid spend would pass $10.
2. Privacy: any writer identity or raw text would leave the repository.
3. A result that reverses a delivered public claim.
4. The machine or GPU is unavailable for more than 12 hours.

## 9. Pre-mortem

- **EV1 only re-finds the surprisal and pause effect.** That still validates the engine's specific readout. The badge says "tracks hesitation", not "attention".
- **Rhythm's 98% is partly the device.** EV4 carries the caveat. ToMpathy shows rhythm only for owner captures, where the device is the owner's.
- **The export at the demo tag drifts from later engine versions.** Every card records the engine pin; post-talk reruns name their pin.
- **The demo hold slows Sunday night.** Accepted: the talk is the week's priority.
- **The canonical successors flip D38's positive.** Report it as found. The original stays as history.
- **DR1's "directed" reduces to "prompt-diverse".** Then that is the finding, and the engine's rule is that simple.
