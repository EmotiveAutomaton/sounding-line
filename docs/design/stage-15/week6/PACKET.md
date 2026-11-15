# Sounding Line Stage 15, Week 6 packet

14 November 2026, late evening. For the registered owner of Sounding Line and the three builders. It starts when Week 5 closes on 15 November. It continues `SOUNDING_LINE_STAGE15_WEEK5_TWO_DAY_PACKET_2026-11-12.md`: every card there keeps its identifier, its design and its place in the record, and section 4 gives the new order.

This is a spec sheet. It carries no questions for the curator. Choices are made here and listed in section 2.

## 0. Read first

**Sources.** The repository at `c03fc1620` (14 November, 20:13): `DIGEST_20261114.md`, `HEALTH_20261114_1700.md`, `BUILD_FILING_20261114.md`, `THEORY_RETURN.md`, `CURRENT_STATUS.md`. The Round 16, 17 and 18 theory handoffs and the curator's three turns behind them, read in full; the first lines of Round 19 (14 November, 16:35). The engine branch at `d49be5f` and Ghost at `2962c7098`. The public Crowd-enVENT archive, downloaded and read by the analyst (section 2, R12). Four capped lookups by a cheaper model.

**What landed from the two-day packet.** LA3 (descriptive), LA4 (inconclusive), IN9's item analysis (inconclusive at 0.625 against 0.60), TR1 (stability 0.73 against 0.5), RR3 (the next choice follows distance from the start more than recent luck: a difference of 0.091 against a bar of 0.05). SG1's source and the clock-flag instrument. All three of CH7's constructed qualification cases, and CH6's native bridge.

**What waits.** CH8 to CH12 behind CH6 and CH7's production admission. RF1 and CP1 behind marker qualification. IN9's cues, IN11, IN12, LA5, EX4 and EX5 with components delivered. The original chess scoring at position 96,576 of 398,065.

## 1. The fact that sizes this packet

The 14 November digest records 190.81 authorized slot-hours, 19.57 occupied and 171.24 idle: 89.74% idle, after 85.49% on the 12th. It names the cause in the same words both times: owner review and source-specific production admission. No new human finding landed in the interval. The queue landed seven results on the 11th, three on the 12th, at least two on the 13th (TR1 and RR3) and none on the 14th.

So this packet is ordered, not sized. A week at that rate is somewhere between ten and twenty reviews. What matters is which ones. The order in section 4 puts first the one export the engine has waited on since the 12th, then a block of cards that all read one table the handler already holds, then everything else.

## 2. Amendments and rulings

**Amendment Z. The engine's export goes first.** EX5 is the first review of the week. ToMpathy's choice benchmark (TP7) has been built and waiting on it since 12 November.

**Amendment AA. One table, many cards.** IN13 to IN16 read only the Crowd-enVENT generation and validation tables that the IN handler already loads. Each is a configuration or a small extension of that handler, with a fixture whose expected values are computed and given below. They are table cards under amendment U and do not wait behind chess production admission.

**Amendment AB. Idle builders.** A builder with nothing ready for review prepares, in this order: RW1's intake and marker check; LA6; DC1; then texture on landed IN cards.

**Ruling R10. Theory text and names.** On 14 November the curator asked the theory thread for a theory errata file as part of its next round. Apply it on arrival through the usual errata verification. This packet changes no theory text. In new reports use the current names: Nest; visibly respectable; visibly compassionate; the marketplace of ideas. The curator withdrew the word "Freedom" the same day; write "the stock" until he names it.

**Ruling R11. Columns admitted.** In addition to R7's duration and personality columns: the twelve "right now" ratings each writer and each reader gave before the task; `timestamp`; `round_number`. No demographic column is read (age, gender, education, ethnicity), and no analysis of sex differences is made.

**Ruling R12. What the analyst already computed.** The analyst downloaded the public archive (SHA-256 `61c22527795669a0556df8d7441d3a7bf13ef8b2266b0433881645e92bf885e6`, CC BY 4.0 by its `LICENSE.txt`) and ran design checks; scripts and outputs are in `PREFLIGHT_2026-11-14.zip`, folder `corpus/`. Computed: sizes and support for every card below; the two reference rows of IN13's Part B; the order of items in a questionnaire printout. Not computed and not looked at: any outcome of IN14, IN15, IN16, DC1, LA6 or RW1. IN13's Part B is therefore a replication under this repository's controls of numbers the analyst has seen, and its report says so. Parts A and C and the other cards are blind.

## 3. Cards

### 3A. The export

**EX5 (carried, unchanged).** Questions and the answer the asker chose, as specified on 12 November. Copy to ToMpathy's `.local/bench/EX5/` by EV4's procedure.

**IM1 (arrives from ToMpathy).** A table of `text_id` and three motive scores from each of two published coders, for all 6,600 reports, with pins. Verify hashes on arrival and place under `docs/exchange/`. Only IN13's Part C reads it.

### 3B. Appraisal reports (family IN, Crowd-enVENT)

#### IN13. What separates the near-twins (Round 18's S1, extended)

- **Why.** The curator: "Maybe we just do blind inference and try to fill in a row." S1 asks for a 13 by 21 table of what moves each feeling, confirmed on held-out writers. The analyst's pre-flight says the rows of that table come in near-identical pairs: correlated across the 21 ratings, pride and joy at 0.99, guilt and shame 0.95, trust and joy 0.94, fear and sadness 0.92, anger and disgust 0.91. A table whose rows cannot tell SHAME from guilt or FEAR from PANIC/GRIEF fills the rows without separating the channels. IN13 runs S1 as written and adds the test of what does separate them.
- **Part A, S1 as the handoff wrote it.** Split writers in half by a hash of `prolific_id`. In the first half fit each label's signed profile over the 21 ratings (that label against the rest, standardised, with the response-style control). Freeze it. Confirm in the second half at the family's bar of 0.10 with a writer-cluster interval. For fear, anger, sadness and disgust this is a replication.
- **Part B, the twins.** For the five pairs above, with writers held out in five folds: the area under the curve for telling the two labels apart (i) from the writer's own 21 ratings and (ii) from the words of her report (`hidden_emo_text`, unigrams and bigrams, logistic). The analyst's numbers: ratings 0.613, 0.627, 0.728, 0.749, 0.798 for pride and joy, guilt and shame, fear and sadness, anger and disgust, trust and joy; words 0.757, 0.700, 0.863, 0.787, 0.891.
  - **Primary.** The mean over the five pairs of words minus ratings, with a writer-cluster interval. Bar 0.05. The analyst's value is 0.097.
  - **Secondary.** For each pair, the six ratings with the largest standardised gap, and the thirty words with the largest weights each way.
- **Part C, needs** (after IM1). Add the three motive scores to the 21 ratings inside each pair. Predictions, written in the engine packet before any run (the analyst's): achievement and power higher in pride than joy; affiliation higher in guilt than shame; affiliation higher in sadness than fear; power higher in anger than disgust; affiliation higher in trust than joy. Primary: a gain of at least 0.03 in area with the predicted sign on at least three of the five pairs.
- **What each outcome changes.** B clears and C clears: the channels are told apart by which need the event touched, and a reader of needs is the missing instrument. B clears and C fails: something in the words separates them and it is not these three motives; the next candidate is the kind of thing involved (a person, a contaminant, a danger ahead). B fails under this repository's controls: the analyst's pre-flight was wrong and S1's table stands alone.
- **Fixture, computed.** 4,000 synthetic reports by 400 writers in two labels. One rating differs by half a standard deviation: area 0.638 in closed form, 0.649 from all 21 ratings with writers held out in the fixture's own draw. A marker word in 30% of one label's reports and none of the other's: 0.650. Both together: 0.761. A second fixture with no difference gives 0.50 by definition.
- **Tags.** `H18-S1`, `TRIGGER-CONTENT`. **Ceiling.** 20,000.

#### IN14. What a recalled feeling leaves

- **Why.** The curator's rulings in Rounds 17 and 18: Stress that is bound has a trigger's shape, and a channel is holding it; anxiety is leftover bound in FEAR's shape; the idle mind turns to "whatever's currently bound". Ghost's V30 family L asks in built worlds whether a reader can tell a channel fired by a trigger from one fired by leftover. The archive holds the question in people. Each report is one survey. The survey's third item, before the recall, asks: "Do you feel any of the following emotions right now, just before starting this survey?" with twelve feelings rated 1 to 5 (read by the analyst in the round 5 printout). Then the writer recalls an event for a named feeling. 1,186 writers did two or more surveys, and their consecutive surveys are minutes apart.
- **Support, computed.** 4,221 consecutive pairs. Median gap 4.8 minutes: 3,346 pairs under 10 minutes, 697 from 10 to 60, 142 from one hour to a day, 36 longer. In 64.1% of pairs at least one of the twelve ratings changed. Timestamps carry two zone labels; no pair runs against the order of `round_number`.
- **Before building.** Read every round's questionnaire printout in the archive. Keep a round only if the "right now" item comes before the recall and before the prompted feeling is named. Drop pairs whose second survey has the same prompt as the first.
- **Model.** One row per pair and rated feeling: the rating at the second survey on the same feeling's rating at the first; an indicator that this feeling was the first survey's prompt; an indicator that it is another feeling of the prompt's valence (negative: anger, boredom, disgust, fear, guilt, sadness, shame; positive: joy, pride, relief, trust; surprise set aside); an indicator that it is the second survey's own prompt, as a control; and writer intercepts.
- **One primary.** The coefficient on the prompt indicator among pairs under 10 minutes apart: what recalling a feeling adds to that feeling a few minutes later, beyond what it adds to the others. Bar 0.10 rating points. Writer-cluster interval.
- **Secondary.**
  - Decay: the same coefficient at 10 to 60 minutes and beyond.
  - Shape or mood: the prompt indicator against the same-valence indicator. A leftover with a channel's shape predicts the first above the second. A general mood predicts them equal.
  - Dose: the coefficient by the first report's intensity and by how long the writer said that emotion lasted.
  - Reach: whether a raised rating at the second survey goes with a stronger report in that survey when its prompt is the same feeling family.
  - The person: for writers with four or more pairs, TR1's recipe on her own coefficient, and its relation to the two emotional-stability items. Lowercase evidence.
- **By construction.** Ratings regress toward the mean; the first survey's rating is in the model for that reason. The first report in a session has no pair.
- **Fixture, computed.** A planted carry-over of 0.5 that decays with a time constant of 20 minutes, gaps uniform from 2 to 10 minutes: the expected coefficient is 0.373 (0.379 in one draw of 40,000 pairs); at 30 to 60 minutes, 0.058. A second fixture with none: zero.
- **Tags.** `H18-G3`, `H17-BOUND`. **Ceiling.** 20,000.

#### IN15. What the reader brought

- **Why.** The curator's new word, schema, is a fluency held in attention: "That's just schemas highlighting or removing the triggers, really." If a held state highlights its own triggers, a reader who arrives angry reads more anger into the same report than the four others who read it. For the engine it measures how much of a human reader's answer is the reader: the engine's readers are held to that answer.
- **Rows.** The validation table: 1,200 reports, five readers each, each reader's own twelve "right now" ratings, her label and her 21 ratings. Support, computed: the spread of prior ratings among the five readers of one report averages 0.31 for anger, 0.36 for fear, 0.68 for sadness, 0.95 for joy.
- **One primary.** Over every report and label where at least one of the five readers named the label and at least one did not: the mean prior rating of that feeling, standardised across readers, among those who named it minus among those who did not. Average over cells. Reader-cluster interval. Bar 0.10.
- **Secondary.** By label. The reader's prior negative state against how unpleasant she rated the event, centred within report. Whether readers who brought more match the writer's label less often.
- **By construction.** A reader's standing habits count as brought: state and setting are not separated here.
- **Fixture, computed.** A planted slope of 0.4 per standard deviation in a choice among 13 labels, five readers a report, 20,000 reports: the statistic is 0.395. With no slope: 0.0005.
- **Tags.** `H18-SCHEMA`, `READER-CEILING`. **Ceiling.** 20,000.

#### IN16. Reaction or clearing (a rider on IN12)

- **Why.** Round 18's third surprise: the trait the theory reads as trigger strength goes, in the literature, with three things: meeting more problems, reacting more, and clearing more slowly. Prompts are assigned here, so exposure is fixed. IN12's primary is reaction. IN16 adds clearing and asks whether there is a person in the strength at all.
- **Writer share.** Among writers with three or more reports (772 writers, 4,579 reports): the share of variance in intensity that belongs to the writer after prompt intercepts and the 21 ratings. Writer bootstrap.
- **Clearing.** The emotion's duration (ordered; "I had none" set aside) on the two emotional-stability items, holding intensity, the event's duration, prompt and the response-style control. Bar 0.10, standardised.
- **Reading.** IN12 above its bar and this below: the trait goes with reaction. The reverse: with clearing. Both: the theory's one sentence covers two things that the Ghost family L shows a reader of shows alone cannot tell apart.
- **Fixture.** A planted writer share of 0.20 recovered within 0.03; a planted clearing slope of 0.2, and zero.
- **Tags.** `H18-SURPRISE-3`. **Ceiling.** 20,000.

**Carried in this family:** IN9's cues, IN11, IN12.

### 3C. The phone game

#### DC1. Slopes for feelings, levels for acts (Round 17's test 1)

- **Why.** The thread's proposal, awaiting the curator's ruling: "Feelings follow the slope and acts follow the level." The pieces exist apart: TR1 and MD1 on ratings, MD3 and RR3 on choices. They have never been in one registered comparison on the same people.
- **Rows.** People who are in both TR1's and RR3's rosters. First plays for the primary.
- **Terms.** RECENT is RR3's recent luck. LEVEL is RR3's distance above the play's starting score; its distance below the start did nothing in that cohort and is reported beside it. Both standardised.
- **Fits,** each with person intercepts and RR3's controls: the happiness rating, standardised; the next choice, as a linear probability, standardised.
- **One primary, two parts, both required.** RECENT minus LEVEL on ratings at or above 0.05. LEVEL minus RECENT on choices at or above 0.05. Person-cluster intervals.
- **Prediction row.** Held-out error for ratings from RECENT alone and from LEVEL alone; held-out log score for choices from each. A gap between coefficients that prediction does not share is reported as such.
- **Secondary.** Across people, TR1's rating sensitivity against how far her choices follow RECENT, corrected for TR1's stability. Repeat plays, with each reference.
- **Not blind on choices.** RR3 already found the choice half on a larger roster with the same terms (0.091 against the same 0.05). What is new here is the ratings half, the common scale and the person-level row.
- **Cautions already in the record.** RECENT and LEVEL correlate at about 0.28. "Choices are not feelings." A game with a running score puts the level on display, so "acts follow the level" may hold best here and say less about a text.
- **What each outcome changes.** As the Round 17 handoff's table: both hold, the first result on people for slopes against levels; ratings follow LEVEL as strongly, the level is felt too; choices follow RECENT as strongly, slopes reach acts.
- **Fixture, computed.** Planted loads of 0.3 and 0.1 on ratings and 0.1 and 0.3 on choices, predictors correlated at 0.28: the two parts sum to 0.40 (0.406 recovered in 200,000 rows). A world with all four loads at 0.2: zero.
- **Tags.** `H17-T1`. **Ceiling.** RR3's.

### 3D. Meetings

#### LA6. Before a laugh (Round 18's S5)

- **Why.** PLAY has no trigger table made from an outcome. LA's prepared tables mark every utterance that a laugh followed.
- **Cases and controls.** Each utterance with `laughed_after` true, matched to the nearest utterance by the same speaker in the same meeting with `laughed_after` false and at least 30 seconds away.
- **Features.** `act_type`; length in words; whether the speaker had just changed; word overlap with the two utterances before; whether it repeats words of the previous speaker; first person singular; a negation; a question; tenth of the meeting; seconds since the last laugh.
- **One primary.** The held-out area under the curve of a logistic model on these, meetings held out. Bar 0.60. With it, the odds for each act type with meeting-cluster intervals. No direction is registered: this is a first table.
- **By construction.** Laughs cluster. Report with and without seconds since the last laugh.
- **Fixture, computed.** One act type at 0.2 among controls with planted odds of 2.0: its share among cases is 0.333 and it alone gives an area of 0.567.
- **Tags.** `H18-S5`. **Ceiling.** LA's.

### 3E. The person

#### TR2. Three more settings (Round 18's S4)

TR1's recipe (true between-person variance first, then corrected split-half) on three settings named in the handoff. Each begins with its support check and is filed as unsupported if the check fails: refusing across sessions (the B2 cohort, by ID1's design); slowing, the per-writer slope of pause on surprise (the D33 rows); returning to a word class across prompts. Bar 0.5, as TR1. Two further settings are already inside IN14 and IN16.

### 3F. A new public text source (builders start the intake on day one)

#### RW1. Worry, in the writer's own number

- **Source.** The Real World Worry Dataset ([Kleinberg, van der Vegt and Mozes 2020](https://arxiv.org/abs/2004.04225), read by a helper): 2,500 people in the United Kingdom in April 2020 each wrote a long text (500 characters or more, 128 tokens on average) and a short one about how they felt about the pandemic, and rated their own worry and eight feelings from 1 to 9. Data in the authors' repository `ben-aaron188/covid19worry` and at OSF `awy7r`. A helper found no licence stated: read the terms at intake, and stop there if they forbid this use.
- **Why.** Round 18 looked for a text corpus carrying the writer's own stress rating and found none. This is the nearest found in this pass. "A plan is resolved energy" predicts that, at the same amount of bad news in a text, a writer who states plans rates her worry lower. ToMpathy's packet benchmarks a reader on the same source (TP16); RW1 is the test.
- **Markers.** A plan sentence: first person with will, going to, plan to, decided to, intend to, or have arranged. Instrument check: two builders mark 200 sentences by the list and by hand; agreement of 0.80 or one revision of the list. Bad news: the share of sentences holding one of the 200 words most associated with worry, learned in a random half of the people and applied to the other half, then swapped.
- **One primary.** The partial correlation between the share of plan sentences in the long text and the writer's worry, holding length and bad news. Prediction: negative. Bar -0.05. Person bootstrap.
- **Secondary.** The same for anxiety and fear, and with the sign reversed for relaxation. Plans that name a time or a place against plans that do not (Ghost's family K asks why that should matter). Whether plan share adds to worry beyond the fear and sadness ratings.
- **Cautions.** One topic, one month, one country. A correlation: calm people may plan more. Worry sits high (mean 6.55, spread 1.76).
- **Fixture.** A planted partial correlation of -0.15, and zero.
- **Tags.** `H17-PLAN`, `STRESS-KEY`.

### 3G. Carried

CH6 and CH7's production admission, then CH8 to CH12. RF1 and CP1. LA5. EX4. IN9's cues. The original chess scoring under amendment V. RR2.

## 4. Review order

| Step | Review | Why here |
|---|---|---|
| 1 | EX5 | Amendment Z |
| 2 | IN13 Parts A and B | One table; reference rows in hand |
| 3 | IN14 | One table; the people-side of Ghost's family L |
| 4 | IN11, IN12 with IN16 | Components already delivered |
| 5 | IN15 | One table |
| 6 | DC1 | Reuses TR1's and RR3's rosters and fits |
| 7 | CH8, CH12 | When CH6 and CH7 are admitted; they do not block steps 1 to 6 |
| 8 | LA5, LA6 | LA's prepared tables |
| 9 | RF1, CP1 | As their markers qualify |
| 10 | RW1 | After intake and its marker check |
| 11 | IN13 Part C | When IM1 arrives |
| 12 | TR2; CH9 to CH11; EX4; IN9's cues | |

Steps 1 to 6 hold eight reviews. At two to three a day that is three to four days.

## 5. When review is the bottleneck

Idle slots and builders take these, in order. None needs a new admission beyond amendments U and AA.

1. Amendment AB's list.
2. Chess scoring shards (amendment V) and the activation log (amendment X), as before.
3. **Follow-ons allowed without a new packet.**
   - IN14 above its bar: the same model within each prompt, and by round.
   - IN13 Part B above its bar: the same two rows using the five readers' ratings in place of the writer's, on the 1,200 validated reports.
   - IN15 above its bar: the same statistic for the readers' unpleasantness and responsibility ratings.
   - DC1 with both parts holding: by tenths of the play.
   - RW1 below zero: the short texts.

## 6. The return

`THEORY_RETURN.md` gains one paragraph per landed card in the standing shape, and a short section "what a trigger is made of" holding IN13's twins table. Routes:

| To | What | When |
|---|---|---|
| ToMpathy, `.local/bench/EX5/` | EX5 | first |
| ToMpathy, `docs/exchange/` | IN13's twins table; IN15's size (how much of a reader's answer is the reader) | as each lands |
| Ghost, `docs/exchange/` | IN14's decay and shape results, for family L | as it lands |

## 7. Limits

- Every IN card reads adults' own reports of remembered events, written to order for a named feeling. It is lowercase evidence about channels.
- IN14's feeling was brought back by recall, in a survey, minutes before the next rating. It says what a recalled feeling leaves, and nothing about hours or about feelings met in life.
- IN13's Part B was seen by the analyst before this packet. Its landing confirms a computation; it is not a blind test.
- DC1 inherits the phone game's display of a running score, and its choice half repeats RR3.
- RW1 is one population in one month, and a correlation.
