# Sounding Line, Stage 15, Week 6: the person rows of 21 November

*Spec sheet of 21 November 2026, from the implementation thread (the analyst) to the registered owner agent. It stands beside the packet extensions of 19 and 20 November, whose text stands unless a line here amends it. It carries no questions. Every choice in it is made here; the curator sees the ones he may want to veto in the reply that delivered it.*

## 0. Read first

- **What this is.** One day of work, to the morning of Sunday 22 November: a temporary data root so work goes on while the bulk store is repaired; the theory handoff's legs 2 to 7 of 21 November; and the repair of the sealed job that returned nothing.
- **Why these.** The curator's ruling of 21 November is that the target is reading a person. Legs 2 and 3 ask whether a person's own slopes repeat and whether they share one dial. Legs 4 to 7 are small rows on operators this repository already has.
- **What yesterday showed.** Twenty-six rows went from packet to ledger in about twenty hours once a test was a row and not a card. The slots were still about a tenth occupied. So today's rows are many and cheap, and one new operator is the only real build.
- **Where files go.** This file at `docs/design/stage-15/week6/PACKET_EXTENSION_2026-11-21.md`. The theory handoff of 21 November beside the others, as `THEORY_HANDOFF_R34.md`. The bundle `PREFLIGHT_2026-11-21.zip` beside the earlier bundles; its `pf_slopes.py` is the known answer for section 4.
- **The clock is unchanged:** freeze 22 November 20:00 PST, drain 22:00, final addendum 23:00.

## 1. Terms this packet uses

Terms of the last two packets stand (row, producer, Form O, Form L, support count, description row, result sheet). Added:

| Term | Meaning |
|---|---|
| Temporary data root | A verified copy, on the workstation's own main disk, of the open sources today's rows read. Section 3 |
| Halves | A person's diary split into its first half and its second half in time. Odd days against even days is filed beside it |
| Raw slope | For one person in one half: her mean on a feeling at prompts where the event is above its floor, minus her mean at prompts where it is not, in units of the diary's pooled within-person standard deviation. It exists only with two or more prompts of each kind in that half |
| Stable slope variance | The covariance, across people, between a raw slope in her first half and the same slope in her second. The halves share no prompt, so chance error at single prompts does not covary, and what covaries is what lasts: how much people differ, and any state that outlasts the split. It needs no reliability floor and comes with an interval. Alone it carries no verdict: where a feeling sits at the bottom of its scale, a person with a higher level shows a larger slope |
| Level-adjusted | The stable slope variance less the part that a person's level and spread on that feeling explain, where level is her mean at prompts without the event and spread her standard deviation there. Every term is a covariance between the two halves, so no prompt's error is shared. It asks whether a slope differs beyond where a person sits on the scale |
| Picking her out | Ranking every person's second half by how well it matches one person's first half, and asking whether her own comes in the first ten |

**Diaries, by the names used here.** The long student diary is member 0060. The large status diary is 0057 and the second status diary 0056. The working-adults diary is 0063, the parents' diary 0072, and the clinical diary that stopped on a coding conflict 0064.

## 2. Rulings and amendments

Rulings are the curator's, with his words and their dates. Amendments are the analyst's and are marked so.

| # | Item | Text |
|---|---|---|
| R32 | Emergent goals | "Emergent goals are definitely just schemas." (21 November). No target is added for autonomy, the social contract, cognitive power or capital |
| R33 | PRIDE | A candidate tenth channel, drawn with a question mark (21 November): "you can put it as a tenth one in the picture, it's fine." Every table keeps proud and any praise or success item. A row on the word proud is still reported as a row on a word |
| R34 | The body | The body's needs stand apart from the four needs (21 November). Body items are reported as their own block |
| R35 | The target | Reading a person (21 November): "the biggest gap is going to be whatever it is that converges the inference of the model on allowing us to get closer to identifying people." |
| R36 | How a result is shown, added | "you kind of need to sell it on me as if I'm like someone from a bar or something that you need to explain the whole concept to really quick like" (21 November). Amendment BH |
| R37 | The day | "I don't really want to lose a day of grinding." (21 November). Amendment BI |
| BH | Result sheets, second part (analyst, under R36) | The text of a result sheet opens with who was measured and how, in one or two sentences a stranger could follow. Several rows on one question are pooled into one number and one picture where their scales allow, by inverse variance, with the rows shown beside the pooled figure and their disagreement (Cochran's Q) stated |
| BI | Storage for a day (analyst, under R37). **This is the owner-reviewed step this repository requires before data moves** | Section 3. Nothing reads or writes the bulk store from the moment the temporary root is verified until the curator says the store is back. No sealed run is started in that time. No download over 1 GB starts. The curator proposed a temporary home and left its place to this layer. The analyst puts it on the workstation's own main disk and not on the other disk he had in mind, and his approval of that is in the message that delivers this packet |
| BM | The sealed job's repair (analyst) | Section 6. Yesterday's amendment AX put three tables in one job and said only that a table with a missing variable is skipped. It did not say the same for a table with too little support, and one failed check ended everything. That gap is the analyst's |
| BN | One new operator for a person's own slopes (analyst) | Section 4. Raw slope, stable slope variance, its level-adjusted form, the cross-slope form and the ranking are qualified once against `pf_slopes.py`, for every row that uses them. The operator has its own support rule, two event prompts and two others in each half. The support rule and the reliability floor of the reactivity cards of 17 and 18 November are not carried over, because this estimator needs no floor |

**Stated by the curator and not ruled. Build nothing on these:** all four needs are outside the person; surprise may be SEEKING with FEAR; art passes through Respect more than Belonging.

## 3. First: the temporary data root (row DRT1; amendment BI)

1. **List.** Every open source that a row of this packet, or an unfinished row of the last two, reads: the admitted diaries, the recalled-event set, the writing logs and the phone-game set where they sit on the bulk store. Nothing under the private tree is listed or copied. A source over 50 GB stays on the store and is named, and its rows wait. If the list still totals over 150 GB, the row stops after the manifest and files the sizes.
2. **Copy and verify.** A manifest of each listed file from the bulk store (path, bytes, SHA-256, licence line), a copy to a folder on the workstation's own main disk, and a second hash of every copy. The manifest is filed with its own hash.
3. **Switch.** The data root variable points at the copy. Every record written while it does names the temporary root and the manifest's hash. Sources are pinned by hash, so a row's result does not depend on which root served it.
4. **Say so.** The status file gets the line: temporary root verified, bulk store no longer read. The curator starts the repair after that line exists.
5. **Small deposits** from the data agent go to an `incoming` folder inside the temporary root, each with its hash.
6. **Back.** When the curator says the store is back: hash the store's originals against the manifest; move `incoming` to the store and hash again; switch the root back; then delete the temporary copy and record the deletion. If any hash differs, nothing is deleted and the difference is filed.

Done when step 4's line is in the status file. Rows that read only files already inside the repository do not wait for it.

## 4. The person ladder (handoff legs 2 and 3; claims P4, P2, S3; amendment BN)

- **Why.** A slope that repeats in a person is that channel's steepness for her. If the unpleasant slopes rise and fall together across people, there is one dial.
- **What this repository's record already says.** The reactivity cards of 17 and 18 November on the large status diary found the same slopes unsupported at a fixed odd and even reliability floor, so no corrected correlation and no one-dial verdict came out. Read those two records before freezing (S15-W6-ES2-PRIMARY-0057-20261117 and S15-W6-ES2-FLOOR-0057-20261118) for their item bindings and exclusions, which carry over. Their support rule and floor do not (amendment BN). The difference here is the estimator: the stable slope variance needs no floor, so a diary that cannot see a difference still returns an upper bound on it.
- **Sources, in this order.** The long student diary first, because it has the most prompts a person (199 people; its public listing gives 109 time points). Then the large status diary, then every other admitted diary with seven or more days.
- **Slopes.** In each diary, every row the ledger grades as supported or as on its registered side with an interval clear of zero. The handoff names: criticism to anger and to shame; argument to anger over fear; demanding thought to curiosity; stress to playfulness; a health or money stressor to fear and to worry.

| Row | What | Registered |
|---|---|---|
| PST1 | For each slope: the mean raw slope; the stable slope variance; its level-adjusted form with an interval from 2,000 draws of whole people; and the square root of the adjusted form as a share of the absolute mean slope, with the upper end of its interval (where the mean slope's own interval includes zero the share is left out) | the theory's: in the large status diary the two criticism slopes are stable. Bar (the analyst's): the level-adjusted variance has its interval above zero. The raw variance carries no verdict |
| PST2 | Picking her out, with three sets added one at a time: her mean on each feeling item; her spread on each; her slopes (a slope that does not exist counts as the group's mean). People are split into two folds, ranking is within a fold, and the match is the likelihood score below. First ten, against chance | the theory's: slopes add to means and spreads. Bar (the analyst's): first-ten with slopes, minus without, is 0.02 or more with its interval above zero, paired over people |
| PST3 | One dial or several. For each pair of unpleasant slopes whose level-adjusted variances are both clear of zero: the adjusted cross-slope covariance and, from it, the correlation between people's true slopes. Pairs within a diary are pooled by inverse variance. The share the first factor carries is filed beside it as a description | the curator's reading, which the handoff registers as one factor carrying most. The analyst restates it on the correlation, because with two slopes and no correlation at all a first factor already carries half. Bars (the analyst's). One: a pooled correlation of 0.50 or more with the lower end of its interval above 0.30. Several: under 0.30 with the upper end under 0.50. Pairs clear of zero and neither bar met: undecided. No pair clear of zero: no verdict |

- **The operator, in full.** `pf_slopes.py` in the bundle is the reference. Where this text and that script differ, the script stands.
  - Weights: a person counts by the smaller of her two halves' event-prompt counts.
  - Level-adjusted variance: `V_adj = V - c' S^-1 c`. `V` is the covariance of the slope between halves. `c` holds the covariances of the slope in one half with level and with spread in the other half, averaged over the two directions. `S` holds the same covariances of level and spread with each other. Spread enters only when its correlation between halves is 0.30 or more, decided once on the full sample and held in every draw.
  - Adjusted cross-slope covariance, for feelings A and B: `C_adj = C - b_A' k_AB - b_B' k_BA + b_A' S_AB b_B`, with `b_A = S_A^-1 c_A`, `k_AB` the covariances of A's level and spread in one half with B's slope in the other, and `S_AB` the covariances of A's level and spread with B's. The correlation is `C_adj / sqrt(V_adj,A * V_adj,B)`.
  - For a pair of slopes, the people are those with both slopes in both halves, and a person counts by the smallest of her four event-prompt counts.
  - Fallbacks, applied in every draw: if the two-by-two matrix has an eigenvalue at or under 1e-6, spread is left out of that draw; if the level's covariance between halves is at or under 1e-6, that draw is not adjusted.
  - Likelihood score (PST2): for reading k, with `r_k` its correlation between halves among the other fold's people, held between 0 and 0.95, and `x`, `y` the standardized values of one person's first half and another's second half: `s_k = (2*r_k*x*y - r_k^2*(x^2 + y^2)) / (2*(1 - r_k^2))`. A pair's score is the sum over readings. It is the log of how much likelier the two values are from one person than from two, so a reading that does not repeat gets no say.
- **Support, counted first:** people with the slope in both halves, and their event prompts, for every slope and diary.
- **What each outcome means.**
  - PST1 lands: people differ in that slope beyond their level and spread, or in how bad their events are, or the slope ran in a spell that covered both halves. Claim P4 is the first of these, and this row cannot tell the three apart. Its interval includes zero and the upper end of the share is under 0.5: people differ in this slope by less than half its average size, a flat result. Otherwise: could not say, with the bound stated. Sizes are on the scale as rated, and a feeling near the bottom of its scale hides part of any difference.
  - PST2 lands: a person's slopes help tell her from others beyond where she sits, the first support for reading a person from how she reacts. It does not land: no evidence either way, for the reason the fixture gives below. PST1 carries the verdict on claim P4.
  - PST3 reads one: one dial, the curator's reading, or one kind of day shared by slopes on the same event. Several: more than one dial. Undecided: the correlation is stated with its interval. No verdict: the slopes could not be held apart from level.
- **Fixture, computed (`pf_slopes.py`).** Each cell is 100 made worlds, and each count is worlds out of 100, for the short diary and then the long. The short diary has 2,272 people and 14 prompts a half, of whom about 710 have the slope in both halves. The long has 199 people and 80 prompts a half. Where differences are planted, people's slopes differ by half the mean slope.

| Made world | Raw variance above zero | Adjusted above zero (the bar) | Flat call | Dial verdict |
|---|---|---|---|---|
| Nothing personal in the slopes | 6, 3 | 5, 3 | 92, 93 | none 99, 100 |
| Nothing personal, and the feeling sits at the bottom of its scale | 54, 96 | 2, 2 | 61, 91 | none 100, 100 |
| One dial | 100, 100 | 100, 100 | 0, 0 | one 100, 100 |
| Two dials | 99, 100 | 99, 100 | 1, 0 | several 89, 100 |
| One dial, and the feeling sits at the bottom of its scale | 100, 100 | 82, 98 | 0, 2 | one 54, 98 |

  - No cell gave a wrong dial verdict. The planted variance of 0.09 came back as 0.088 to 0.091 without a floor and as 0.029 to 0.030 with one. The planted correlations of 1 and 0 came back as 0.92 to 1.00 and as 0.01. The rest of each cell gave no verdict or was undecided: in the short diary, 10 two-dial worlds were undecided, and with one dial and a floor 42 gave no verdict and 4 were undecided.
  - **The checker's worlds (`chk_worlds.py`), with nothing personal in the slopes.** The bar was met, in worlds of 100, short then long: where the chance of an event rises with a person's level, 0 and 1; with five-point ratings, a floor and a ceiling, 3 and 1; with a level that drifts over the diary, 3 and 1. Where people differ only in how bad their events are it was met in 45 and 88, and the dial read one in 7 and 45. Where slopes run in spells of several days it was met in 28 and 8 on first and second halves and in 52 and 37 on odd and even days, which is why the halves are split in time.
  - **PST2 cannot be expected to land.** With slopes added, the first-ten rate moved by between minus 0.007 and plus 0.011 in every cell. The bar was met in at most 1 of 100 worlds with nothing personal and in at most 14 of 100 where slopes truly differed. At these diary lengths a miss says nothing against claim P4.
  - Two simpler forms failed in these worlds and are not to be substituted. Regressing each half's slope on the other half's level shares an error between the halves, and it met the bar in 12 of 20 short worlds with nothing planted (first round, from the helper's report; that file was not kept). Adjusting for spread where spread does not repeat turns the adjustment to noise. A weighted distance in place of the likelihood score lowered the first-ten rate whenever any set was added.
  - Not covered: 300 draws a world and not 2,000; two slopes on one event, and not more or on different events; one event rate; people without the slope, who in the build count at the group's mean. The long made diary has 80 prompts a half, more than the long student diary's listing allows (about 54), so its column is optimistic.
- **Qualification.** Run on the worlds `pf_slopes.py` makes with its seeds, the build matches the script's table to three decimals in the columns for the two variances and the correlation, and within 0.05 in the columns that count intervals.
- **Limits.** Every feeling and event is the person's own report at one prompt. Slopes on one event for several feelings share how bad her events are, so one factor here can be one dial or one kind of day. A slope exists only for people who met the event at least twice in each half, and they are not everyone. A slope that runs in spells of days reads as stable, more so in a short diary.
- **Prior art.** That a person's own couplings in a diary are hard to measure reliably is a known problem in print (from the analyst's memory; no paper looked up for this packet). The rows are not called new.

## 5. Small rows on operators already qualified

Each starts with a binding check against the member's codebook. Item names below are from public item lists.

### ANX1. What anxious is made of (handoff leg 4; claim W1)

- **The curator's ask of 21 November,** as the handoff quotes it: "seeking fear and sadness would be interesting."
- **Form.** Inside one person, Form L: anxious on afraid, sad and curious or interested, in one model. Reported: the three weights with intervals, the share of anxious's within-person variance they explain, and the share left over.
- **Sources.** The long student diary lists all four. Its general anxious item is primary, and its item on anxiety about schoolwork is filed beside it. Two more diaries (members 0062 and 0072) list worried, afraid and sad with no curiosity item; they run as descriptions with two weights. The clinical diary lists all four and joins when its key arrives.
- **Registered** (the theory's): all three weights are above zero, each with its interval.
- **What each outcome means.** All three: anxious is a mix that includes SEEKING. Afraid and sad only: his earlier reading, FEAR with predicted grief. Afraid only: the plain reading.
- **Limit.** Words rated together at one prompt share mood and answering style.

### PRD1. PRIDE as a candidate (handoff leg 5; ruling R33)

- **What the handoff asks and what the diaries allow.** The handoff asks for proud on being appreciated against inspired on the same. No admitted diary lists proud beside an appreciated item, and the diary with inspired lists no proud item. Row a is the nearest test the held diaries allow, with being admired in place of appreciated and enthusiastic in place of inspired. That substitution is the analyst's.
- **Row a,** the two status diaries, interaction prompts, Form O: proud on being admired and on being respected, with the other status events held, and the same for enthusiastic. Registered (the theory's claim, in a form one diary can test): proud's link to being admired is larger than enthusiastic's, by 0.10 or more with its interval above zero.
- **Row b,** the large status diary: the mirror of row LD1. Feeling successful and proud after an interaction against after time alone, with enthusiastic as the comparison feeling. A description: the thread's older card expected company to turn pride up, and LD1 left the same contrast for shame inconclusive.
- **Row c.** Any other admitted diary with proud beside a praise, success or appreciated item gets row a's form. A diary without such an item is void for this row.
- **One picture** (amendment BH): rows a and c beside the two filed rows for inspired in the working-adults diary.
- **Limit.** Proud, admired and successful are rated at one prompt by one person.

### PBK1. PLAY's off switch, pooled (handoff leg 6; claim T7)

- **Form.** In every admitted diary with a playful, silly or fun item beside a fear item and a sadness item: inside one person, Form L, the play item on fear and on sadness in one model. The contrast is fear's weight minus sadness's.
- **Pool.** The contrasts are pooled by inverse variance (amendment BH). Of the two filed rows the handoff names, the one on the diary with a silly item (member 0070) is already this contrast and enters unchanged. The other, on the parents' diary, ran the other way round, with fear and sadness on fun, so that diary is run again in this form and the new row takes its place. Member 0076 lists a playful item and no fear or sadness item, and is void. That leaves two diaries until a third is deposited.
- **Registered** (the curator's ruling of 19 November that PLAY is off above a lot of FEAR): the pooled contrast is below zero with its interval.
- **Limit.** A weight is not a switch: this reads whether play is lower when fear is higher, not whether it shuts off past a point.

### WLG1 and WLG2. Writing logs, two last looks (handoff leg 7; claim AT1)

- **The curator's ask,** as the handoff quotes it: "maybe we try a really obvious test with the writing logs".
- **WLG1.** A writer's pause before the first word of a sentence against her pause before a word inside one: the ratio of her two medians, per writer, then the median over writers with an interval from draws of writers. Registered: above 1. Bar: 1.5 or more with its interval above 1. This is the plainest timing result in the study of writing (from the analyst's memory; not looked up). This repository has already looked for it in these logs as a difference (row S15-W4-PP1-FULL-20261103) and did not detect it in either genre. WLG1 is the same question in its plainest form and is reported beside that row. If it lands, the earlier miss was its form. If it does not, these logs' timing cannot carry claim AT1, and that is the answer.
- **WLG2.** Her pause just before she asks for a suggestion against her median pause at the same kind of place. Same form, same bar. It is read as a test only if WLG1 lands. Otherwise it is filed as a description.
- **If WLG2 is already among this repository's writing-log results,** its record is cited and it is not run again.
- **After these two, no further theory row is pointed at the writing logs.**

## 6. The sealed job's repair (row SMF1; amendment BM)

- **Diagnosis** (the analyst's, from the disposition record through a digest; the job's code was not read). Both runs on the second-wave folders ended with the study's exit 12 and no table. The record says that code covers too little support or a complement check, and cannot tell which. So one failed check anywhere ended the job, and nothing came back to say where.
- **Repair.**
  1. No check on one table ends the job. A table that fails is dropped whole and the others are written.
  2. The status table has one row per table: its name; kept or dropped; a reason from a fixed list (kept; variable missing; too few people; a complement would reveal a small cell). Its count column is the number of people in the file the table read, never the count that failed.
  3. The complement check drops only the rows it must, the smaller of a pair, and drops the table only if fewer than two rows would remain.
  4. Exit 12 is kept for one case: the file itself holds fewer than 11 people.
  5. Three jobs in place of one: the main table, table NT1.s, table D5.s. Each is its own run, so the gate judges each alone.
- **Rehearsal, today, on made files and the local copy of the gate:** one table with too few people (the others return, the status row says why); one complement case (only the offending rows go); all tables sound.
- **Real runs wait** for the curator's word that the store is back (amendment BI): three runs on the joined second-wave folder, within the thirty of the 19 November table.

## 7. Order

| When | What |
|---|---|
| First | DRT1. Then bind and launch ANX1, PRD1 and PBK1, which need no build |
| While they run | Build the operator of section 4 and qualify it. PST1 to PST3 on the long student diary, then the large status diary, then the rest |
| Then | WLG1 and WLG2. SMF1's repair and rehearsal |
| When the curator says the store is back | DRT1's step 6. SMF1's three runs |

**When building is the bottleneck,** drop from the bottom: DRT1; the three small rows; PST1 and PST2 on the first two diaries; PST3; SMF1's repair; the writing logs; PST on the other diaries.

## 8. Predictions before data (the analyst's guesses, filed so they can be scored)

| Row | Guess |
|---|---|
| PST1 | In the large status diary: could not say again, with a bound near half the mean slope. In the long student diary: the curiosity slope is stable |
| PST2 | Slopes do not add to means and spreads |
| PST3 | No verdict |
| ANX1 | Afraid and sad are above zero. Curious is not |
| PRD1 | Row a lands |
| PBK1 | The pooled contrast's interval includes zero |
| WLG1, WLG2 | WLG1 is above 1 and under its bar, as the earlier row suggests. WLG2 is then a description |

## 9. Bounds

Yesterday's bounds stand. Picking her out matches a participant's two halves inside one file. Nothing is matched to any outside source, and no row tries to name a participant. PST rows: 20,000 CPU-seconds a diary including replay. The small rows: 20,000 each as diary rows. WLG1 and WLG2: 10,000 each. Sealed runs stay within the thirty of the 19 November table.

## 10. The return

The Week 6 return gains one row for each row here: verdict word, estimate, interval, bar, the limit sentence, the ledger row and the result sheet. It names the branch of "what each outcome means" each result fell in, and which of section 8's guesses held.

## 11. Limits of this packet

- The pre-flight covers the one new operator in made worlds, and it changed the operator twice. Nothing else here was pre-flighted. A helper wrote the fixture's code from the analyst's specification; the analyst read its tables, and an independent checker read the code.
- Which diary carries which item is from public item lists by keyword, not from codebooks.
- The checker's worlds were written and run by the checker. The analyst read their table.
- The sealed job's diagnosis is from a record, not from its code.
- This repository's records since 20 November were read through a helper's digest, with one spot check.
- Every source here is self-report.
