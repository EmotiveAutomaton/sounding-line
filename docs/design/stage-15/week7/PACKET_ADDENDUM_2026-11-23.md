# Sounding Line, Stage 15, Week 7: addendum of 23 November

*Repository path: `docs/design/stage-15/week7/PACKET_ADDENDUM_2026-11-23.md`. It adds to the Week 7 packet and changes none of its rows. It carries no questions. Every choice in it is made here, and the curator's approvals are in the message that delivers it.*

## 0. Read first

- **Why.** The Week 7 packet's runnable work ended about nine hours after it was delivered. Of its 22 rows, 10 gave a measurement. The others waited on an input from outside this repository or met a source that could not carry them. The fault was the analyst's: the packet was sized by a count of rows, and rows were given sources by their catalogue names. This addendum holds only work on sources that are admitted and readable today, with items this repository has already bound or can bind from a codebook it holds.
- **What it is.** Seven families, each defined by a rule, so that no cell waits on a question:
  - CAL: calibration of the rows already read.
  - ATL: the whole table of events by feelings.
  - LAG: what an event leaves at the next prompt.
  - PLX: the person's own slope, in the diaries not yet tried.
  - LGH3 to LGH5: the meetings' laughs against what happened around them.
  - MIB, SLD4 and CAL3: sealed returns that were withheld, asked again on rosters already released, and two checks on row SLD3.
  - ADM: admission of two sources already collected.
- **Sizing, from what was measured.** On 22 November this repository filed ten units in the two hours after the packet arrived and about ten more in the two and a half hours after phase 1 opened, runner builds included: four to five units an hour (a unit is one family's work on one source). Week 7 has used 9,458 CPU-seconds of its 6,000,000, so compute is not what limits it. This addendum holds 69 units and seven runner builds, which is 15 to 20 hours at that rate. It does not reach Thursday's freeze. Section 10 lists what else is open, and none of that is counted.
- **Checked before filing.** A helper checked this addendum against the repository's records and code and found seven errors and nine weaknesses. All are fixed here; they are listed in the corrections addition of this date.
- **Prior art.** No search was made for any family here and none is called new. Shuffle tests and tables of every pair are ordinary practice.

## 1. Terms added

| Term | Meaning |
|---|---|
| Unit | One family's work on one source |
| Void | A cell or unit whose item does not bind, whose support is under the family's floor, or whose table the release checks withhold. A void is recorded with its reason, counted in the return, and stops nothing |
| Event item | An item that asks what is happening or has just happened to the person: an activity, an encounter, something done to her or by her. An item that rates the event (how pleasant, how expected, how important) is an event item labelled "appraisal". An item derived from a feeling item is not an event item |
| Rated event | Where an event item is a rating and a rule needs "prompts with the event", those are the prompts in the upper third of the scale's range |
| Record | In diaries filled in at each encounter and not at timed prompts (0042, 0043, 0044, 0076), a record takes the place of a prompt, and nothing that needs prompts within a day is run |
| Above floor | A feeling rated above the lowest point of its scale, as in row PSD1 |
| Free shuffle | Within one person, the answers to the event items are moved to other prompts of hers at random. All event items of one prompt move together |
| Day shuffle | The same, within one study day. Used only where a diary has three or more timed prompts a day |
| Feeling family | RAGE words (angry, irritated, resentful, scornful); FEAR words (afraid, anxious, nervous, worried); PANIC/GRIEF words (sad, lonely); SEEKING words (curious, interested, enthusiastic, inspired, excited); PLAY words (playful, silly, fun); PRIDE (proud); shame words (ashamed, guilty, embarrassed); calm words (relaxed, calm, content); other |

## 2. Amendments

| Id | Subject | Text |
|---|---|---|
| CQ | The rule of the lattice (analyst) | Every family below is defined by rule over sources already admitted. A cell that does not bind, lacks support or is withheld is void, and the family goes on. No cell waits on a question to the curator. Where the rule leaves a choice open, the agent takes the reading that scores fewer cells and writes the choice in the row. Readiness is unchanged: a design note for each family, the source hashes, a native fixture, the review manifest |
| CR | Running dry (analyst). The curator's approval is in the message that delivers this addendum | Section 9 is a standing queue. When a slot is free and a unit in the queue is ready, it starts. The row status table (landed, running, ready, or blocked with its one input and its owner) is kept in the Week 7 README and refreshed at each push, and at least every twelve hours. If the ready list is empty while a slot is free, the return's first line says so and says why |
| CS | Sealed returns asked again (analyst). The curator's approval is in the message that delivers this addendum | Up to ten of Week 7's thirty sealed invocations are for section 7. The gate and its rules do not change. Each job is rehearsed first against the gate's local copy. A job that is withheld is filed with its reason code and is not tried again |
| CT | Bounds (analyst) | Unchanged from amendment CK: 20,000 CPU-seconds for a unit and 200,000 for a unit that measures sound in a corpus, replay and shuffles included, and the freeze on Thursday 26 November at 20:00 PT |

**Runners to build or extend, each qualified once under amendment CL:** the shuffle harness (CAL); row PSD1's operator for members other than 0056 and 0057 (ATL); the clock binding of the answered-prompt runner for further diaries (LAG); the member branches of the PST4 and PST5 runner (PLX); further facts in the LGH1 runner (LGH3, LGH4); a trait argument for row SLD3's job (SLD4, CAL3); and a draw that treats a person with no family number as a family of one (MIB3).

## 3. CAL: calibration of what has been read

Most rows read so far carry the same limit sentence: one person answered the event and the feelings at one prompt, and unequal answer noise can change slopes taken above the floor. CAL measures how much of each reading that could be.

**CAL1, the shuffle.** For each unit, 1,000 free shuffles, and the row's own estimate (the point only, by the row's own form) on each. Where the diary has three or more timed prompts a day, 1,000 day shuffles as well.

- Units, 19 in all. From the Week 6 lattice, the thirteen decided diary rows: 5 and 6 (member 0057), 7 (0056), 11 and 16 (0060), 18 (0042), 19 (0043), 22 and 24 (0072), 26 (0070), 29 (0076), 32 and 33 (0063). From Week 7: PSD1 on 0056 and on 0057, and PSD2's falls on each. From rows PST4 and PST5: the slopes that held, as one unit for 0057 and one for 0056.
- Filed for each: the observed estimate; the shuffles' mean, standard deviation, and 2.5th and 97.5th percentiles; the share of shuffles at least as far from zero as the observed, in the plus-one form; and the row's own standard error (its interval's width over 3.92) divided by the shuffles' standard deviation.
- Reading. A row holds under shuffle if the observed estimate lies outside the 2.5th to 97.5th range of every shuffle run for it. A ratio under 0.8 is flagged: the row's interval is narrower than the noise the data make with no link in them. A ratio above 1 is not a fault, because people who differ in their slopes widen a row's interval and not the shuffles'.
- Fixture (the agent's): a made world built from member 0057's own rows with the event answers shuffled once within person. In it, the estimate lies outside the range of a fresh set of shuffles in 2 to 8 of 100 repeats.

**CAL2, the equal effect.** For the six rows that compare feelings on one event (rows 5, 6, 11, 16, 22 and 24). Take the free shuffle, so that no real link is left. On prompts with the event (section 1 for a rated event), raise each feeling in the contrast by one step with the same chance q, stopping at the top of the scale. Find the q at which the mean of the planted slopes equals the mean of the observed slopes (six halvings on the point estimates). At that q, 500 shuffles give the range of the contrast that an equal effect makes through unequal floors alone. The contrast is computed by the row's own form each time: row 11's is linear, and row 22's first side is the mean of its two feelings.

- Filed: q; the 2.5th and 97.5th percentiles of that range; the observed contrast.
- Reading. A row is marked "floors could make this" if the observed contrast lies inside the range. It is a description. It uses one meaning of an equal effect, an equal chance of one step. The rows' own models use others, and none of them is the truth.
- Fixture (the agent's): two made items with 80% and 50% of answers at the floor. With an equal chance of a one-step rise on both, the contrast lies inside the range in at least 90 of 100 made worlds. With the rise on the first item only, outside in at least 80 of 100.

## 4. ATL: every event by every feeling

The Week 6 lattice read 44 chosen contrasts. ATL reads the whole table those were chosen from, so that the theory thread sees which events move which feelings and which do not.

- **Rule.** For each diary below, every event item by every feeling item gives one cell: the slope of the feeling above floor on the event, within person, with the person's means held, by row PSD1's operator, with 2,000 whole-person draws.
- **Sources, 13 units.** The diaries in which the record shows event items and feeling items bound: 0056, 0057, 0003, 0049, 0073, 0042, 0043, 0044, 0060, 0063, 0070, 0072, 0076. Any other admitted diary enters if its codebook check binds at least one event item and one feeling item; otherwise it is void for ATL. In 0042 and 0043 the unpleasantness score is derived from a feeling and is not an event item. Member 0049's cells stay internal, as its binding note says, and are left out of the pooled table.
- **Support.** The floors of row PSD1 and of the Week 6 lattice, unchanged. A cell under them is void.
- **Beside each cell:** the plain slope on the raw rating; the slope with each day's mean removed, where the diary has three or more timed prompts a day; and 200 free shuffles.
- **Pooled table.** Rows are event families, named by the agent from the items' own wording and listed in the design note before any outcome is opened, with appraisals marked. Columns are the feeling families of section 1. Each cell gives the number of diaries whose slope is clear above zero, clear below, not clear, and void, with the median estimate. Diaries are not weighted by their size: row PST9 showed one diary carrying nearly all of such a pool.
- **What is registered.** A cell that an earlier row has read (a row of the Week 6 lattice, PSD1, a PST row) is shown with that row's verdict and carries no ring. Section 11's guesses are scored only on cells that no earlier row read. Every other cell is a description.
- **The yardstick for many cells.** For each diary, the share of its cells whose observed slope lies outside its shuffle range. With nothing in the data that share is 5%.
- **Limit sentence.** One person rated the event and the feeling at one prompt. A table of every pair finds some pairs by chance; the shuffle share says how many.

## 5. LAG: what an event leaves at the next prompt

- **Rule.** For each cell of ATL whose same-prompt slope is clear of zero: the slope of the feeling at the next prompt on the event at this prompt, holding the same feeling at this prompt and the same event at the next prompt. Prompts are paired by the rule of 22 November 10:50: consecutive answered prompts on one study day, the distribution of gaps filed, a second reading with gaps capped at twice the diary's median, and "undecided" if the two readings disagree.
- **Sources, 7 units.** Diaries of ATL with three or more timed prompts a day and an order that binds (a timestamp, or day and prompt number): 0056, 0057, 0003, 0049, 0060, 0063, 0073. A feeling item that asks about the time since the last prompt is left out, which in member 0003 removes sadness and worry. A diary whose order does not bind is void.
- **Filed:** the lagged slope with its interval, and its ratio to the same-prompt slope, pooled by feeling family as in ATL.
- **Limit sentence.** An event that lasts across two prompts reads as carry-over. Holding the event at the next prompt takes out some of that and not all. A missed prompt may not be missed at random.

## 6. PLX: the person's own slope, in the diaries not yet tried

- **Rule.** Rows PST4 and PST5, with their operators and bars unchanged, on each event family of ATL that has support in both chronological halves.
- **Sources, 5 units.** 0042, 0043, 0044, 0063, 0070. Where chronological halves cannot be formed the unit is void.
- **Filed:** for each diary, the slopes that hold, by feeling family. Then one line pooled with the eleven diaries rows PST1 to PST9 ran on: in how many of sixteen diaries any slope holds, and for which feelings.
- **Limit sentence.** A slope that does not hold in a short diary has not been shown absent.

## 7. Sealed: returns asked again, and two checks on SLD3

All on the wave-two folder, with items the contract already binds. One invocation each unless said. The release rule compares the people behind each returned row with the people behind everything already released, so a table of estimates alone does not pass by being alone.

- **MIB1, MIB2, DFB1.** Cards MI1 (Week 6 lattice rows 34 to 37), MI2 and D5.s were withheld by that rule. Each is fitted again on the people of a table already released, so that its members are already protected and its count is that table's count. The agent takes the largest released roster on which every member can contribute to the fit. If there is none, the unit is void and no invocation is spent.
- **MIB3.** Card MI3 (lattice row 42) returned a point with no interval, because the family number is missing for some people. Each such person is treated as a family of one, and the interval is taken by whole-family draws on the roster already released with the point. Limit sentence: relatives whose link is missing are drawn as strangers, which can narrow the interval a little.
- **SLD4, two invocations.** Row SLD3 found the trait effect above zero for the anger group. SLD4 asks whether that belongs to Neuroticism: SLD3's job once with agreeableness and once with extraversion, the other two traits the contract binds, on SLD3's roster. If a trait is missing for some of that roster and the gate withholds the table, the unit is void.
- **CAL3.** Row SLD3 with the trait scores moved between people at random, 1,000 times inside one job, on SLD3's roster. It returns the percentiles of each estimate under that shuffle and where the observed estimate falls among them. Nothing about a person leaves.
- Card MI4 fell under the release floor and is not asked again.

## 8. LGH3 to LGH5: laughs against what happened around them

Row LGH1 on the ICSI meetings found that the groups a laugh's sound puts it in say something about whether others joined it. These rows ask what else they say, with LGH1's own operator: the share of a fact's variance that lies between the fitted components, against the 95th percentile of 200 shuffles. The same exclusions and the same rule for silent frames apply.

- **LGH3, 8 units** (four facts, on the ICSI meetings and on the 12 complete AMI meetings). Each fact is computed from the laughter marks and the speaker turns alone:
  1. it began within 3 seconds after another speaker's laugh began;
  2. three or more speakers laughed within 5 seconds of it;
  3. the laugher began to speak within 2 seconds after it ended;
  4. it fell in the last third of the meeting.
  Filed beside each fact: its rate in each component, next to that component's means on the six measures, which LGH1 has filed.
- **LGH4, 2 units.** The dialogue-act layers of both corpora are already bound. If a scheme's own manual defines a tag for humour or joking, one more fact joins LGH3: the laugh began within 3 seconds after the end of an utterance with that tag. If a scheme has no such tag, its unit is void.
- **LGH5.** As further AMI meetings are completed, rows LGH1 and LGH3 are run again on AMI at 24 complete meetings, at 48, and at the full set. Each run is filed beside the earlier ones.
- On AMI, a fact whose table fails the release checks is void with its reason code.
- **Limit sentence.** Laughter that overlaps speech is not in the sample, and that may be a kind of its own. A fact taken from marks is only as good as the marks.

## 9. Order, and ADM

1. The shuffle harness, then CAL1 on PSD1 and on PSD2's falls, then the rest of CAL1, then CAL2.
2. ATL on 0057 and 0056, then the other diaries, largest first.
3. Sealed: rehearse MIB1 at once. Invocations go out as rehearsals pass, in the order MIB1, SLD4, MIB3, CAL3, MIB2, DFB1. They run on the second machine while the CPU slots work.
4. LGH3, and LGH4.
5. LAG.
6. PLX.
7. **ADM, 2 units.** Admit, from what is already on the store and with nothing fetched: the couples diary and the time-use survey's wellbeing module. Each takes its codebook check, its binding table, its licence line and its design note, under the repository's admission rules. If a source's files are not on the store the unit is void and the row status table says so. Then, by rule: a source with an event item and feeling items repeated for the same person enters ATL, and LAG if its order binds. The couples diary opens row TWO2 only if a worry item and usable timestamps bind.
8. LGH5, whenever meetings arrive.

Anything in section 10 goes to the front of the queue when its input arrives. If Thursday's freeze nears, drop in this order: PLX, ADM, LAG's capped readings.

## 10. Opens when (counted as zero hours)

| Row | The one input it waits on | Owner |
|---|---|---|
| TRX1 on 0056 and 0057, and its pooling | The provider's note on the person key | data agent |
| GAT1, GAT2 | The curator's rights disposition | curator |
| VAL1 | The portal's receipt for the export | data agent, then curator |
| SLD2 | One folder of three waves with its manifest | data agent |
| MIB1 on wave three (lattice rows 38 to 41) | Wave three's family field and diary row count resolved | data agent |
| LGH1 on the remaining AMI meetings | Complete meetings | data agent |
| LGH1 on the Santa Barbara recordings | The sealed mount with its map | data agent |
| LGH1 and LGH2 on the sealed conversation set, CAD1, CAD2 | The dictionary, laugh times, word times | data agent |
| PSD2's co-occurrence on the everyday emotions set | The curator's review of a source with no stated licence | curator |
| UGM1 | A release with felt ratings for each offer | data agent |
| CRV1, RBD1 | Data needs 24 and 26 | data agent |
| TMP1's study | The engine's bundle | engine |
| TMP1's image identity | The owner's inspection | curator |

## 11. Guesses before data (the analyst's, filed so they can be scored)

Nothing here is about a quantity already filed. Where a family has cells that an earlier row read, the guess is scored on the other cells only.

- CAL1: all thirteen lattice rows hold under the free shuffle. Of the seven with a day shuffle (rows 5, 6, 7, 11, 16, 32 and 33), at least five hold under it. The slopes that held in PST4 and PST5 hold. No ratio is under 0.8.
- CAL2: rows 16 and 22 lie outside the equal-effect range. Row 5 lies inside it.
- ATL, on the pooled table's unread cells, each as "more diaries clear above than clear below":
  - being blocked, argued with or criticised, on RAGE words;
  - a threat to health or money, on FEAR words;
  - being left out or ignored, on PANIC/GRIEF words;
  - thinking hard or doing something one is good at, on SEEKING words;
  - being admired or respected, on PRIDE;
  - fun or play, below zero on FEAR words.
- ATL's yardstick: more than 30% of cells outside their shuffle range in each of the two status diaries.
- LAG: PANIC/GRIEF words carry over more than RAGE words (a larger ratio).
- PLX: a slope holds in at most one of the five diaries.
- LGH3: facts 1, 2 and 3 meet the bar on ICSI; fact 4 does not.
- MIB1: if released, all four contrasts are above zero and at least two are clear of it.
- SLD4: if released, the anger group's effect is smaller for agreeableness and for extraversion than SLD3's for Neuroticism.

## 12. The return, and limits

- **Return.** Added to the Week 7 return named in the packet's section 8, under the heading "Against, and clear" first. ATL's pooled table, with a ring on each cell that had a guess and an X on each that parts from it, is the first exhibit. CAL's table is the second.
- **Limits of this addendum.**
  - The shuffles answer chance and the shape of the answers. They do not answer the rival every diary row shares: one person, one sitting.
  - ATL is a description outside its guessed cells, and several of its event items are appraisals.
  - LAG cannot tell a lasting event from a lasting feeling.
  - A sealed job asked again may be withheld again.
  - The sizing is 15 to 20 hours and rests on one day's filing times.
