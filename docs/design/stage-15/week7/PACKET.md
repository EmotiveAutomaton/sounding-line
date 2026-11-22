# Sounding Line, Stage 15, Week 7: the week to Friday 27 November

*Spec sheet of 22 November 2026, from the implementation thread (the analyst) to the registered owner agent. It is this repository's part of the theory handoff of 22 November (Round 35). The Week 6 packet, its extensions and addenda stand unless a line here amends them. It carries no questions. Every choice in it is made here; the curator sees the ones he may want to veto in the reply that delivered it.*

## 0. Read first

- **What this is.** A week of rows in two phases. Phase 0 reads only the temporary data root and starts now, as a last extension of Week 6. Phase 1 opens when the curator says the bulk store is back: the sealed sets, voice, the games and scales, and the long histories. Results are read on the morning of Friday 27 November.
- **Why.** The curator's words of 22 November: "with a focus first and foremost, as always, on driving the engine forward." This repository's part of the handoff's tree is the person in diaries with a trait in hand, two reports of one moment, three trigger rows (the other three are the engine's), three small games and scales, how fast values move, laughter by sound, and the sealed sets.
- **Sizing, from what landed.** Yesterday five diaries went from the addendum's filing to results in two and a half hours, and the sixth in part, on about 100 CPU-seconds. A row on a source in hand takes minutes. What takes days is a tool this repository does not have (measures of sound), sources that sit on the store, and sealed runs. This packet is built around those three.
- **Left from yesterday.** Member 0049's effort item is not a grade of how good the event was. Its effort slope is fitted on the prompts that endorse helping, filed as a description under the label effort, kept internal, and left out of row PST9. The curator's approval of that is in the message that delivers this packet.
- **Where files go.** This file at `docs/design/stage-15/week7/PACKET.md`. The handoff beside the others as `THEORY_HANDOFF_R35.md`. The bundle `PREFLIGHT_2026-11-22.zip` beside the earlier bundles. Its scripts are the known answers named in each row.

## 1. Terms added

| Term | Meaning |
|---|---|
| Trait effect | How much a person's slope differs for each standard deviation of a trait score, beyond her level and spread, as a share of the absolute mean slope. Section 3, row TRX1 |
| Co-occurrence | For two feelings in one person: the share of her prompts with both at two or more steps above their lowest value, over the product of the two single shares. One means they come and go independently. Zero means they never meet |
| Fall | The change in a feeling since the previous prompt of the same day at prompts with an event, less the same change at prompts with none, taken only where the previous prompt left room to fall |
| Rebound | Playfulness beyond what the stress of the moment predicts, at prompts where stress has fallen since the previous prompt of the same day |
| Excess refusal | The share answering never, less the share a single smooth spread of prices would put above the top price |
| Kinds | Groups of laughs that are separate things and not regions of one continuum. A dip in density between two groups is one sign of it and is not required, since a rare kind near a common one leaves none |
| Sealed image | The software a sealed job runs in. It is distinct from the gate, which decides what may leave |

## 2. Rulings and amendments

Rulings are the curator's, with his words of 22 November. Amendments are the analyst's and are marked so.

| # | Item | Text |
|---|---|---|
| R38 | PRIDE | "I think I'm officially going to call pride as a channel at this point." Ten channels. The theory's claim id is T11, and the tag R33 on row PRD1 is read as T11. Its trigger is not ruled |
| R39 | Respect and Belonging | "I don't think similarity is a reason to copy." "I think it's a gate." Respect is the reason and sets its strength. Belonging is the gate. Row GAT1 |
| R40 | How a result is shown | "this style of reporting is absolutely worth carrying forward." A pooled table carries a ring where a guess was registered beforehand and a small X where the result parts from it |
| R41 | Odd results | "if we find weird results, it's worth quickly glancing a research pass at it to see whether other people have found similar weird results". The look is the theory thread's. Amendment CE says what the return owes it |
| R42 | The week | "We're about to make a week's worth of studies". The second machine runs for all of it |
| R43 | Smaller rulings, by his agreement to the theory thread's questions | Suddenness is not RAGE's own. A laugh aimed at someone in a work meeting is mostly a reward, and the kinds of laugh are to be found by sound. The tag named belonging is on a watch list. The safety tag stays where it is |
| CE | Result sheets, third part (analyst, under R40 and R41) | Amendment BH stands. Added: a pooled table marks each cell that had a registered guess and each cell that parts from it. The return has one line for every result that goes against its registered direction with its whole interval clear of zero, under the heading "Against, and clear". A single result whose interval includes zero is never listed there |
| CF | The store's return (analyst; shared with the engine) | Amendment BI ends when the curator says the store is back, and not before. For this repository, in this order on that day: step 6 of row DRT1; the three runs of row SMF1; phase 1. The engine's part is in its own packet |
| CJ | A frozen bundle for sealed reading (analyst; shared with the engine) | Row TMP1. The engine hands over its frozen readers and code as files with hashes. This repository runs them inside a sealed job. The engine's agent reads no sealed row |
| CK | Week 7's bounds, proposed (analyst). The curator's approval is in the message that delivers this packet | Week 7 opens when Week 6's drain reconciliation is filed. Until Week 6's freeze at 20:00 PT today, phase 0 runs as an extension of Week 6 inside its bounds, and whatever has not landed by then carries into Week 7 unchanged. Freeze Thursday 26 November 20:00 PT, drain 22:00, final addendum 23:00. CPU only, eight slots. A ceiling of 6,000,000 CPU-seconds. 20,000 CPU-seconds for a row on a source, replay included, and 200,000 for a row that measures sound in a corpus. Thirty sealed invocations for the week. The limit on threads for each worker, the start floors and the memory guard carry over unchanged |
| CL | Operators added (analyst) | The trait effect (`pf_trait.py`), co-occurrence and fall (`pf_dial.py`), the rebound (`pf_rebound.py`), excess refusal (`pf_price.py`), the product with squares held (`pf_gate.py`) and the test for kinds (`pf_cluster.py`). Each is qualified once against its script, for every row that uses it |
| CM | The sealed image (analyst). The curator's approval is in the message that delivers this packet | The gate's rule on what may leave does not change. Measures of sound are written with what the image already has. If the engine's bundle cannot run on that, the packages it needs are added from files, with no network, and are named in the record |
| CN | Admitting games and scales (analyst) | One design note covers the family: the money game, the sacredness scale, the choice table and the value survey. Each source adds its codebook check, its binding table and its licence line, and the repository's admission rules are unchanged. Where the catalogue's line says tests only, the row runs as a test and its figures go no further than this repository's record and the theory thread. A source whose rights are unresolved is not fetched or run |
| CO | Sound without voice prints (analyst) | Nothing that could pick out a speaker is computed, kept or released. No speaker embedding is made. A speaker's own median pitch is used inside a job to place her laughs against her speech and is not written out. Only tables over groups of laughs leave a sealed job. This amends the limit of 19 November that nothing opens audio or video: sound is opened for rows LGH1, LGH2 and CRV1 and for nothing else, and no video is opened. The curator's approval is in the message that delivers this packet |

**Stated by the curator and not ruled. Build nothing on these,** though several are tested below as his statements: stress raises the need for play; any large emotion shuts PLAY off; shame leads to isolation; impotent rage becomes sadness; a cultural overlay on Respect and Belonging. **No analysis by sex is made anywhere, and no demographic column is read, other than the country and round that row VAL1 is about.**

## 3. Phase 0: rows on the temporary root, starting now

Each row starts with a binding check against the codebook. Item names are from public lists and from this repository's own records.

### TRX1. The person in diaries, with a trait in hand (handoff leg PA4; claims S3, P4)

- **Why.** Rows PST1 to PST5 asked a rare event's slope to repeat, and it could not. The older road is a trait score that predicts the slope.
- **This repository's record.** The reactivity cards of 17 and 18 November gave no verdict at a fixed reliability floor. Row NT1.d found about 6% of a criticised moment's feeling left at the next prompt. The engine's card TP35 used a two-item score.
- **Operator** (amendment CL). The covariance across people of the trait score with her slope, less what her level and spread explain, with the level and spread terms taken between her two halves in time so that no prompt's error is shared: `[cov(T, b) - k' S^-1 c] / SD(T)`, as a share of the absolute mean slope. `b` is the mean of her two half slopes, `k` holds the trait's covariances with her level and spread, and `c` and `S` are amendment BN's. Support: two event prompts and two others in each half; one of each in a diary of one report a day.
- **Not to be substituted.** Regressing a person's slope on the trait and on her own level, in one model or two, shares the baseline's error between the slope and the level. In made worlds with nothing planted it found an effect in 3 to 100 of 100, and in 79 or more at the two larger shapes. The plain covariance of trait and slope found one in 100 of 100 whenever the feeling sat at the bottom of its scale.
- **Sources.** Members 0057 and 0056 when the data agent brings their person-level files (section 5); they carry the row. Members 0011 and 0027 when the store is back. Member 0010 now, as a small first run: it is a trial in two periods of about 47 prompts each, so only its first period is used, with halves inside it, and the check that its release holds a Neuroticism score comes first.
- **Events.** In member 0010 the rated thing is the person's appraisal of what she was doing, which this repository voided as an event, so the row there is labelled an appraisal and not an event: a prompt counts when its rating is in the least pleasant third of the values in use across the whole diary, a fixed cut that is the same for everyone. In the status diaries: criticised, ignored, sidelined and upstaged, each alone and any of them. In the others, by codebook.
- **Feelings.** Every unpleasant feeling item the diary has. Pleasant ones are filed apart.
- **Trait.** The release's own Neuroticism score, or emotional stability reversed. No other person-level column is read.
- **Pooled** over diaries by inverse variance, for each feeling that recurs and over all unpleasant feelings.
- **Registered** (the curator's one dial): less stable people react more to the same event, by about the same amount in every unpleasant channel. Bars (the analyst's): the pooled trait effect has its interval above zero; and inside a diary every difference between two feelings' effects has its interval inside 0.15 either side of zero, over 2,000 draws of people.
- **What each outcome means.** Both hold: one dial, seen through a trait. An effect clear for some feelings and a difference clear: more than one dial. A difference clear and no effect clear: the feelings differ in how the trait bears on them, and none can be placed. Nothing clear: the trait goes with a person's level and not with how she reacts, as far as these diaries see. An effect below zero is not read as the reverse: where less stable people only answer more noisily, or truly swing more from moment to moment, the operator reads below zero, by about 0.09 in the fixture's momentary diaries and 0.02 in its daily one. For the same reason a true effect under about 0.1 can be hidden.
- **Fixture, computed (`pf_trait.py`; worlds of 100).** Three shapes: 130 people with 100 prompts a half; 2,272 people with 14 a half; 2,000 people with four daily reports a half. With nothing planted the bar was met in 0 to 4, in every shape and world but one: daily reports with the feeling at the bottom of its scale, 9. With a planted effect of 0.30 it was met in 100, and in 85 in that same hardest case. The operator read the planted 0.30 as 0.22 to 0.28. No shape here is as short as member 0010's first period.
- **The checker's worlds (`chk_trait.py`), with nothing planted and the feeling at the bottom of its scale.** Where the trait raises how often events come, or goes with answering fewer prompts, the bar was met in 2 to 7 of 100. Where a person's level drifts between halves and the trait goes with the drift, in 2 to 10. Where less stable people truly swing more, it was met in 0 to 3, and the effect was clear below zero in 42 and 77 of 100 in the two momentary shapes.
- **Limits.** Every feeling, event and trait is the person's own report. The trait was measured once. The same event is the same rating, not the same thing that happened.
- **Prior art.** Reactivity has been tied to Neuroticism in diaries ([Suls, Green and Hillis 1998](https://doi.org/10.1177/0146167298242002)) and in the sealed diary ([Mroczek and Almeida 2004](https://doi.org/10.1111/j.0022-3506.2004.00265.x)); titles and abstracts were checked on 20 November and the papers were not opened. The row is not called new. The question here is whether it is the same in every channel.

### PSD1 to PSD3. PRIDE and SHAME: one dial or two (leg TG1; claims T11, T4)

- **Data.** The two status diaries, members 0057 and 0056.
- **PSD1, the four numbers the handoff asks for.** `ashamed` fitted to the same six status events as proud was in row PRD1, in Form O. Then side by side: proud on admired (filed: 0.681 and 0.844) and on criticised (filed: minus 0.049 and minus 0.026); ashamed on admired and on criticised. **Registered** (it follows from ruling R38): being admired lowers shame far less than being criticised raises it. Bar (the analyst's): the first is a quarter of the second or less in size, and the second less the first's size has its interval above zero, pooled over the two diaries.
- **PSD2, the test that decides.** Within a person: the co-occurrence of proud and ashamed, pooled over people who have each above its lowest value at least once. And the two falls: proud at criticised prompts where the previous prompt had proud above her own median; ashamed at admired prompts where the previous prompt had ashamed above its lowest value. Each fall is also given as a share of the feeling's own rise (proud on admired, ashamed on criticised). **Registered:** two channels. Bars: on ratings two or more steps above the lowest value, co-occurrence has its interval above 0.8 for two, below 0.5 for one, and is undecided between. The figure at one step above lowest is a description.
- **PSD3, a second look.** Across people, her proud-when-admired slope against her ashamed-when-criticised slope, by row PST3's operator. No verdict is expected, since only the first of the two has been held.
- **Fixture, computed (`pf_dial.py`; worlds of 100 at the large diary's size).** With one two-ended dial, the four numbers were 0.74, minus 0.46, minus 0.25 and 0.68, co-occurrence was 0.00 (by construction, since the made cuts could not overlap), and the falls were minus 0.48 and minus 0.24, each below zero in 100. With two dials: 0.74, 0.00, 0.00 and about 0.63; co-occurrence 1.00; falls of 0.00. With two dials that cross weakly (a quarter as strongly as each acts on its own): minus 0.14 and minus 0.09 for the crossed numbers, co-occurrence 0.96, and falls of minus 0.14 and minus 0.08, below zero in 99.
  - The falls measure how much each crosses into the other. The fixture's four numbers are plain differences of means and not Form O, so row PSD1's own form was not pre-flighted, and it does not carry the verdict.
  - **The checker's worlds (`chk_dial.py`), all with one dial.** Where a tenth to a fifth of answers sit one step above the lowest value with nothing felt, or the dial moves a good deal within the hour a prompt covers, co-occurrence at one step above lowest read two in 88 to 100 of 100, in three of five such worlds. At two or more steps it read one in 100 of 100 in four of the five, and was undecided in the fifth. That is why the bar is at two steps.
- **Limits.** Proud, ashamed and the events are one person's ratings at one prompt. Two feelings that can be reported together are two reports, which is weaker than two channels.
- **Prior art.** No search was made. Not called new.

### ISO1. After shame, no interaction? (leg TG5; claim T4)

- **Data.** The status diaries, with the item that asks whether she has had a social interaction since the last prompt. The feelings are the diary's own shame, anger and sadness items for interactions and for occupations, by the binding table.
- **Form.** Within a person and a day: whether the next prompt reports no interaction since this one, on ashamed, angry and sad at this prompt, each standardized inside the person, with the same answer at this prompt and the block of the day held. A linear fit with the person's mean removed, and 2,000 draws of people.
- **Registered** (his): shame is followed by a stretch without interaction more than anger or sadness of the same size is. Bar (the analyst's): ashamed's coefficient less the mean of the other two has its interval above zero.
- **Limit.** Row NT1.d found little of a moment carried to the next prompt in this diary, so could not say is the likely reading. A stretch without interaction is not a choice to be alone, and it is also the time of day.

### RBD1. PLAY's rebound (leg TG4; claim T7). Pre-flighted first, as the handoff asks

- **Data.** Member 0076 is not used: its stress item is asked once a day and its play item is about the last interaction, so no fall within a day exists there. The row runs on every diary in this repository's item inventory with a play item and a stress item at three or more prompts a day, and the list is filed first. If there is none, the row is blind and says so, and the question goes to row LGH2 and to the data agent's need 26.
- **Form** (amendment CL; `pf_rebound.py`). Within a person, with her means removed: playfulness on stress now, on how far stress has fallen since the previous prompt of the same day, and on how far it has risen. The rebound is the coefficient on the fall.
- **Registered** (his, in the theory's form): higher than her usual after a fall in stress. Bar (the analyst's): the fall's coefficient has its interval above zero. The handoff's second half, lower while stress is up, is the coefficient on stress now, with its interval below zero.
- **The handoff's own wording is not run as a test.** Playfulness after a fall against her usual was above zero in 100 of 100 made worlds with no rebound in them, because stress is lower after it falls and play is higher when stress is lower. It is filed as a description and labelled so.
- **Fixture, computed (worlds of 100).** With no rebound, the bar was met in 0, at every size, and the coefficient reads a little below zero. With a planted rebound of 0.15 it was met in 70 to 99: 70 and 81 with 200 people and 60 prompts, 93 to 99 at the larger sizes. The coefficient reads about a fifth of what was planted, so its sign is the result and its size is not.
- **What each outcome means.** Above zero: a rebound, his statement. An interval that includes zero in a diary at least as large as 130 people with 200 prompts, or 800 with 35: no rebound of that size, and the question goes to row LGH2. A smaller diary: blind, and declared so.

### Builds for phase 1, in the same hours

- The operators of amendment CL, each qualified against its script.
- The measures of sound of row LGH1, qualified on made sound: a tone of known pitch, bursts of known number, noise with no pitch.
- The sealed jobs of section 4 (SLD2, SLD3, LGH1's sealed half, LGH2, CAD1, CAD2, TMP1), each rehearsed on made files against the local copy of the gate, as row SMF1 was.
- The family note of amendment CN, from the catalogue's entries.

## 4. Phase 1: when the curator says the store is back

First, amendment CF's order. Then the rows below, in the handoff's order of priority.

### TWO1 and TWO2. Two reports of one moment (leg PA5; claims P2, T8)

- **TWO1, the teaching diary.** A teacher's and a mentor's assessment of the same occasion. For each assessed quantity: the correlation of the two raters over people's averages, and inside a person over her occasions with her average removed. **Registered** (the theory's): two people agree about a person's average more than about her moment. Averaging alone produces that, so the row's use is its two figures. The second is the nearest thing held to what one human reads of another's moment, and the engine's readings of a moment are set against it. The catalogue's line for this source is tests only, and it asks for a review before the source is used for independent ratings of one event, which is this row's use. The curator's word on that is in the message that delivers this packet. Without it the row waits.
- **TWO2, the couples' diary.** Both partners' own feelings at the same moments. Prompts are paired when within 30 minutes. With each person's own average removed: each of her feelings on each of his at the same moment, pooled over both directions, with the two partners treated alike. **Registered** (his trigger for CARE): a partner's sadness raises one's own worry more than one's own sadness. Bar (the analyst's): the first slope less the second has its interval above zero, over 2,000 draws of couples. Where the diary has a hassle or stress item, the person's own is held, since a shared bad moment raises both.
- **Limit.** Neither source has one person rating the other's feeling. That is still asked of the data agent.

### UGM1. The gap in a money game (leg GM1; claim A1)

- **Data.** The money-game release, with the valence and arousal each player expected and then felt for every offer. The codebook check says whether an expected offer is recorded. If it is not, what was expected is the mean of the offers she has already seen, and the row says so.
- **Form.** Within a player, in one fit: felt valence on the offer, on the offer less what was expected, and on the change from the previous offer. Felt arousal on the size of the gap, apart for gaps above and below zero.
- **Registered** (his, that the sensed line carries the error and its rates of change): the gap adds beyond the offer; the change adds beyond both; arousal follows the size of the gap whichever way it points. Bars (the analyst's): each coefficient has its interval above zero in the joint fit, over 2,000 draws of players; for arousal, both sides.
- **Limit.** The three are built from the same offers and travel together, so adds beyond is a weak statement where the game's offers follow a fixed list.

### SCR1. A rule or a price (leg GM2; claim TB1)

- **Data.** The sacredness scale's release: twenty items, each answered with a price in euros or with a refusal. Its catalogue line is tests only.
- **Form** (amendment CL; `pf_price.py`). For each item: the share who refuse; the excess refusal, from a normal spread fitted to the log prices of those who named one; and the dip, the share at the top price less the smaller of the share refusing and the share one step below the top. Averaged over items, with 2,000 draws of people.
- **Registered** (his, that an identity is applied and not priced): answers split into refusals and prices with little in between, and a person who refuses one item refuses many. Bars (the analyst's): excess refusal has its interval above zero, and the dip has its interval below zero.
- **The second half cannot be tested by counting.** People's counts of refusals were more spread than chance in every made world, with a rule or without one, because a person with high prices everywhere also crosses the top price often. It is filed as a description, beside the correlation of her refusals with her prices on the items she did price (0.46 to 0.51 in made worlds with no rule, 0.15 to 0.29 with one).
- **Fixture, computed (worlds of 100).** With no rule, excess refusal was above zero in 0 to 3, with normal or heavy-tailed prices, and the dip never appeared. With a rule both bars were met in 100. The fixture's prices were symmetric on the log scale and its fit was on price steps; skewed prices were not tried, and it paired odd items' refusals with even items' prices.

### GAT1 and GAT2. The reason and the gate, in choosing a person (leg GM3; claims N2, T9; ruling R39)

- **These rows wait** until the catalogue's line for the choice table is resolved (amendment CN). Its rights are recorded as unresolved.
- **GAT1.** A yes, fitted inside a rater to the reason (the mean of how attractive, ambitious and intelligent she rated the partner), to the gate (rated shared interests), and to their product. **Registered** (his shape, the theory's use): the product adds beyond the two alone. Bar (the analyst's): in a logistic fit inside raters that also holds the square of each of the two ratings, the product has its interval above zero, over 2,000 draws of raters. A plain linear fit is not used, and neither is the logistic fit without the squares.
- **Fixture, computed (`pf_gate.py`; worlds of 100).** With a reason and a gate that only add, the bar was met in 0 to 3: with a different link, and where liking coloured both ratings. With ratings piled at the top of a seven-point scale it was met in 6, where the linear fit found a product in 100 and the logistic fit without the squares in 17. With a true gate it was met in 100, with piled ratings too.
- **GAT2, one row for LUST's trigger** (his statement of 19 November): a yes rises with the partner's rated intelligence and ambition taken relative to the rater's own. Inside a rater her rating of herself does not vary, so a plain difference cannot stand beside the partner's rating. The row's form is the part of the partner's rating that lies above the rater's own rating of herself, added to the partner's rating, and its coefficient has its interval above zero.
- **No analysis by sex.** Raters are pooled.
- **Limit.** All ratings are one rater's, made at one sitting, and liking a person colours every rating of her.

### VAL1. How fast value priorities move (leg CU2; a description)

- **Data.** The survey export with twenty-one value items by country and round.
- **Form.** For each item, the variance between people inside a country and round, between countries, and inside a country across rounds, each as a share of the whole. Filed on raw answers and on answers with each person's own mean removed.
- **Registered** (the theory's): movement across rounds is small beside the spread between people. A marker for reading the table (the analyst's), and not a test: under a tenth of it, for every item. Answer noise counts as spread between people, which flatters the comparison, so the movement is also given in scale points a decade.

### LGH1. The kinds of laughter, by sound (leg VO1; claims T7, LP5; amendment CO)

- **Sources, in this order.** The sixty conversation recordings matched to transcripts. The sealed conversation set, inside a sealed job, only if a sealed check finds laughs marked in its transcripts: this repository's codebook note says a written mention of laughing is not an annotation, the set's `laughter` field is a survey answer, and one of its 34 media archives has been verified. If laughs are not marked, the sealed half waits on the data agent's need 25. The two meeting corpora when their close-talk sound arrives (section 5); this repository holds their marks and not their sound.
- **Measures of each marked laugh,** from the laugher's own channel where there is one: its length; its number of bursts; the share of it that is voiced; its median pitch in semitones above her own median speaking pitch in that recording; its spread of pitch; its loudness against her speech. Qualified on made sound before any recording is opened.
- **Grouping.** Measures standardized inside a corpus. Mixtures of one to six groups, the number chosen by the usual penalized fit. Groups are found on half the laughs and compared on the other half.
- **Kinds or a continuum** (amendment CL; `pf_cluster.py`). Two counts are filed for each corpus: the mixture's own number of groups, and the number left after joining any two groups with no dip in density between their centres (the density at the midpoint is 0.8 or more of the smaller density at the two centres). Neither settles it, and the result says so. In made worlds the mixture found about three groups in one skewed continuum, stable across halves and alike across two corpora. Joining by dips read one group in every continuum, which is right. It also read one, in most worlds (1.2 groups on average), where there were three true kinds of which two were uncommon and near the common one: it found the three in 0 to 2 of 55 worlds, because there is no dip there to find. Even with three kinds of equal size it found all three in 15 of 55. A kind that is rare and sits close to another, which is what the curator expects of mocking laughter, cannot be told from the tail of a continuum by sound alone.
- **Held-out facts,** which the grouping never sees: whether the laugher was the one speaking; whether another person laughed within a second; the share of the next minute's talk taken by the person laughed at, against the minute before, with the target as amendment BG rules; and in the sealed set the partner's later ratings of the laugher.
- **What sound cannot settle, the held-out facts bear on.** For each fact: whether the groups differ on it, scored against 200 shuffles of the fact among laughs; and inside the groups, whether the fact still follows a laugh's place along the main axis of the measures. Facts that differ between groups and are flat inside them point to kinds. Facts that follow the axis inside groups point to a continuum. The second of these was not pre-flighted and is a description this week.
- **Registered** (his): a few kinds that sound different; the reward kind is by far the commonest; the mocking kind is rare and sits close to the real thing. What can be scored now (the analyst's forms): the groups differ on at least two of the held-out facts, each beyond the 95th percentile of its shuffles; the largest group holds over half the laughs and has the highest next-minute share for the person laughed at; a group whose target's share falls holds under a tenth, and its centre is the nearest to the largest group's. Whether the groups are kinds is given no verdict this week. **Registered** (in print, from the handoff): spontaneous laughs are less voiced and higher. The analyst's stand-in for spontaneous is a laugh that another person joins, and the bar is each difference with its interval on the registered side.
- **What each outcome means.** The scored forms hold: what he hears is in these measures, as kinds or as regions of one continuum, and row LGH2 uses the largest group. The groups differ on no held-out fact: these measures do not carry what a listener hears. The print finding fails: the stand-in is poor, or these recordings differ from the printed ones.
- **Limits.** Six measures are a handful, as the handoff asks. The conversation recordings have every voice on one channel, so a laugh under someone's speech is measured with that speech in it, and such laughs are counted and filed apart.
- **Prior art.** The measures and the print finding are the handoff's. No search was made here. Not called new.

### LGH2. PLAY on that measure (leg VO2; claim T7)

- **Data.** The sealed conversation set, whose survey has mood before and after. The row needs row LGH1's laughs from that set. If laughs are not marked there, it runs once as a description on the survey's own laughter answer, labelled a report, and waits for marked laughs.
- **Form.** Across speakers, with conversations drawn whole: laughs a minute (of the reward kind if row LGH1 found kinds, of all laughs otherwise) on her mood coming in; and her mood going out on her laughs a minute, with her mood coming in held.
- **Registered** (his statements): fewer laughs with a loud unpleasant state coming in, its interval below zero; more laughing goes with a larger lift, its interval above zero.

### CAD1 and CAD2. SEEKING, attention and the speaker's own rating (leg VO4, as written on 19 November; claims T6, AT1, P2)

- **CAD1** (the handoff's leg E2 of 19 November). In the sealed conversation set, after its codebook check for which after-conversation items exist and how many speakers have more than one conversation: words a second over a speaker's turns, against her own rating of how enjoyable the conversation was (`how_enjoyable`), inside the speaker across her conversations, with her other ratings held. The set has no rating of interest, and that stand-in is the analyst's. **Registered:** above zero.
- **CAD2** (register row S14). The time before a word, on how surprising the word is under counts fitted to the speaker's own earlier conversations and under counts fitted to everyone else's, by card D33's operator. **Registered:** slower where surprise is higher (in print); her own counts add beyond the field's (the theory's).
- Register row S4 is voice against the speaker's own rating, and row CAD1 answers it.

### CRV1. CARE's voice (leg VO3; claim T8). It waits on the data agent's need 24

When a recording arrives with one adult speaking to a small child and to another adult: the measures that set the two apart in the same adult (pitch height, spread of pitch, rate of speech, length of vowels), and then whether that marker appears when an adult comforts another adult. Nothing is built before the source is admitted.

### SLD1 to SLD3. The sealed diary set (leg SD1; claims N1, S2, S3)

- **SLD1** is row SMF1's three runs, as built. They answer the handoff's leg C1 and register rows S16, S8b and S17 (cards MI1 to MI3), and the settled half of leg D5. The second row of leg D5, on carry between two different feelings, was never built and is not built here.
- **SLD2** (leg D4 of 19 November, never built). Purpose in life at the three waves, for people who lost a role between the first and the second, on the items the three waves share. **Registered** (the theory's): by the third wave it is back within the bar of its first-wave level. The rival: it settles lower. Bar (the analyst's): the third wave less the first has an interval inside a fifth of a standard deviation either side of zero. The store holds a folder for the second wave and one for the third, each joined inside itself. This row needs a first-wave folder and a join of the three by person, which the curator makes as he made those.
- **SLD3** (the handoff's addition). Row TRX1's operator in the daily reports: Neuroticism against the slope of each unpleasant feeling on a stressor day, with card MI2's two sides (angry, irritable, frustrated; afraid, nervous, jittery) and all negative feeling. Registered and read as row TRX1.

### TMP1. The map's trait labels (leg SD2; claims S3, T6, T7, P2; amendments CJ and CM)

The engine's card TP58 defines the tables and the bar. This row is the sealed job that runs the engine's bundle on the comment histories that carry trait scores: a rehearsal on made text first, then the run. Only card TP58's tables leave, with their intervals and counts. No demographic column is read, and comments in the communities where the scores were gathered are left out.

## 5. For the data agent

| Need | What | When |
|---|---|---|
| 27, new | The person-level questionnaire files and codebook of the two status diaries, from the study's own public deposit, for row TRX1 | now; they are small |
| 28, new | Close-talk sound for the two meeting corpora, for row LGH1 | when the store is back |
| 24, 25, 26 | As the handoff lists them: an adult speaking to a child and to an adult in one recording; conversation with laughter marked and mood before and after; a diary with a play item and a stress item several times a day | open |
| Still open | A source in which one person rates another's feeling at the same moment. The rights line for the choice table. The licence of member 0075. The key for the clinical diary | open |

## 6. Order and bounds

| When | What |
|---|---|
| Now | PSD1 to PSD3, ISO1, RBD1, TRX1 on member 0010. The builds of section 3 |
| When the store is back | Amendment CF's order. Then TRX1 on the rest, TWO1 and TWO2, UGM1, SCR1, VAL1, LGH1 on the conversation recordings |
| Through the week | The sealed rows as their rehearsals pass: SLD3, CAD1, CAD2, LGH1's sealed half, LGH2, TMP1, SLD2. LGH1 on the meeting corpora when their sound arrives |
| Waiting on something outside | GAT1 and GAT2 (rights). CRV1 (a source). SLD2 (a first-wave folder and a three-wave join). TWO1 (the curator's word). The sealed halves of LGH1 and LGH2 (marked laughs) |

Bounds are amendment CK's. **When building is the bottleneck,** drop from the bottom: PSD2; TMP1; TRX1; SLD1; LGH1 on the conversation recordings; TWO2; SCR1; UGM1; CAD1; SLD3; LGH1's sealed half; LGH2; TWO1; PSD1; ISO1; VAL1; CAD2; SLD2; RBD1; LGH1 on the meeting corpora; GAT1; GAT2; PSD3; CRV1.

## 7. Predictions before data (the analyst's guesses, filed so they can be scored)

| Row | Guess |
|---|---|
| TRX1 | Above zero pooled. No two feelings differ |
| PSD1, PSD2 | The ratio is under a quarter. Co-occurrence is above 0.8: two |
| ISO1 | Could not say |
| RBD1 | Blind: no admitted diary has both items often enough |
| TWO1 | Agreement about a moment is under half the agreement about a person |
| TWO2 | Could not say |
| UGM1 | The gap adds. The change does not |
| SCR1 | Both bars are met |
| VAL1 | Under a tenth for every item |
| LGH1 | The mixture gives three or four groups and joining by dips leaves one. The groups differ on whether others join. Laughs that are joined are less voiced and higher |
| LGH2 | Fewer laughs with a bad mood coming in. A lift with laughing |
| CAD1, CAD2 | Above zero. Slower where surprise is higher, and her own counts add |
| SLD2 | It settles lower |
| SLD3 | Above zero for both sides, alike |

## 8. The return

The Week 7 return has one row a result: who was measured and how, in a sentence or two a stranger could follow; the verdict word; the estimate, its interval and its bar; the limit sentence; the ledger row; which branch of "what each outcome means" it fell in; and which of section 7's guesses held. The heading "Against, and clear" of amendment CE comes first. It is pushed at least once a day as it grows, so that a midweek round can read it.

## 9. Limits of this packet

- The pre-flight covers the six operators of amendment CL in made worlds. With the checker's worlds it changed seven of the rows. Nothing else here was pre-flighted.
- Where each source sits, what the catalogue says of its licence, and this repository's records since 21 November were read through a helper's digest, with two spot checks.
- The analyst read the handoff and the curator's turn of 22 November first-hand.
- Item names for sources on the store are from the catalogue and from memory of the public releases, not from codebooks.
- Every diary result is a person's own report. Every result on sound is about marked laughs, and the marks are other people's.
- No row tries to name a participant or a speaker, and nothing is matched to any outside source.
