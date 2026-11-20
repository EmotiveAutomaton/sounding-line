# Sounding Line, Stage 15, Week 6: the build order of 20 November

*Spec sheet of 20 November 2026, from the implementation thread (the analyst) to the registered owner agent. It stands beside `docs/design/stage-15/week6/PACKET_EXTENSION_2026-11-19.md`, whose cards keep their text unless a line here amends them. It carries no questions. Every choice in it is made here; the curator sees the ones he may want to veto in the reply that delivered it.*

## 0. Read first

- **What this is.** A build order for one owner working alone until the builders return on 22 November: the nine legs of the theory handoff of 20 November, mapped onto what this repository has already built, with five amendments that cut what a test costs to build. New here: the Neuroticism row, a second sample for suddenness and anger, a length-held laughter row, the pooled act table, the reference card, and two tables inside the sealed job. No new family is added.
- **Why it is short.** Between yesterday's packet and the push of 20 November, 06:58 PT, the record shows components qualified (the above-the-floor operator, the diary source adapter, the diagnostics, the structure probe on the joined folders) and no research card from that packet admitted. The slots were about a tenth occupied on 19 November (about 17 of 192 slot-hours in the digest). Building is the limit, so this sheet ranks and does not pile on.
- **The standing rule it relies on** (the curator's instruction of 20 November, as this repository records it): "An empty ready list while a commissioned runner can be built is an instruction to build it in the current turn."
- **Where files go.** This file at `docs/design/stage-15/week6/PACKET_EXTENSION_2026-11-20.md`. The theory handoff of 20 November beside the filed Round 29 handoff, as `THEORY_HANDOFF_R32.md`. The 19 November handoff is refiled from the supplied copy, because its sections 10 and 11 were added after the copy this repository holds. The bundle `PREFLIGHT_2026-11-20.zip` beside yesterday's bundle; its `pf_n1.py` is the known answer for section 4, and its `dot_table.py` is the renderer of amendment AS.
- **The clock is unchanged:** freeze 22 November 20:00 PST, drain 22:00, final addendum 23:00.

## 1. Terms this packet uses

| Term | Meaning |
|---|---|
| Row | One registered contrast on one source: a line in the rows table. From this packet a diary test is a row and not a card (amendment AU) |
| Producer | The program that turns a row into an estimate with its interval. One producer serves every diary row |
| Form O, Form L | The two forms of yesterday's packet, section 3.0. Form O asks whether an answer is above the scale's lowest point, on the logit scale |
| Trait | One score per person from a questionnaire answered once, here Neuroticism |
| Lag | The previous answered prompt of the same person on the same day |
| First size, what is left | How much a bad feeling rises at the prompt that reports the event, and how much of that rise is still there at the next prompt |
| RATIO | The contrast of section 4 that asks whether a trait goes with what is left more than with first size. Answers that are only noisier cancel out of it. A feeling that saturates does not, and section 4 says which way that pushes it |
| Support count | How many prompts and people a row has, counted before any outcome is read |
| Description row | A count, a codebook check or a table with no registered contrast |
| Result sheet | The picture and short text of amendment AS, written at every landing for the curator |
| Claim ids | As the two handoffs list them, always written with the word claim. Need codes are written with the words need code |

## 2. Rulings and amendments

Rulings are the curator's, with his words and their dates. Amendments are the analyst's and are marked so.

| # | Item | Text |
|---|---|---|
| R26 | Belonging and Compassion | One need, named Belonging (20 November): "We'll get rid of compassion, merge it into belonging." Need code N5 and its tag stay in every export. He asked for results "to be reported with both so I can change my opinion during the next round." A table with need-level rows gives them apart and merged |
| R27 | SADNESS | The channel long written PANIC/GRIEF is SADNESS (19 November): "If his questionnaire named it sadness, we will also name it sadness." This repository's errata note marks the rename unconfirmed; it is confirmed. New rows say SADNESS. Older cards and results keep their wording |
| R28 | RAGE's aim | RAGE aims at a schema and not at a person (20 November): "We'll incorporate that." Row R1.i follows from it |
| R29 | People differ in the channels | "So there is variation in the channels themselves." (20 November). The twin leg (E3) stays parked |
| R30 | How a result is shown to him | "I don't need the methodology details. I'm more interested in your conclusions and how to interact with that." "I kind of want graphs and tables. Graphs more so" (20 November). Amendment AS |
| R31 | The machines | "We're trying to keep the spark and my GPU maximally tasked for at least until tomorrow's theory walk morning thing." (20 November). Nothing in this repository's queue needs a GPU, and none is asked for here. The engine's packet fills both. This repository's part is the slots and the sealed runner |
| AS | Result sheets (analyst, under R30) | Every landing with a table of signed numbers writes one picture and one short text beside its record. Picture: `dot_table.py` of the bundle, from a file of cells (row, column, estimate, low, high). A positive cell is a white dot, a negative one red, the dot's area shrinks toward zero, and a cell whose interval includes zero is blank, on a dark background 680 units wide with no text under 9.5 units. Text: three to six plain sentences on what to look at, then the limit sentence in the record's own words. No method paragraph |
| AT | No machine names in records (analyst) | A record names the Spark as the Spark and reaches it as `ssh spark`. Host names, network names and addresses stay out of packets, records and receipts. This repository's filing of yesterday's packet already removed one |
| AU | Rows, not cards (analyst). Reason: the record of 19 and 20 November, in which building and not machine time set the pace | A diary test that uses only operators already qualified is a line in the rows table. It needs a binding check (each item is in the member's codebook; amendment AI still applies to members not yet admitted) and a support count. It needs no producer of its own and no new qualification. A row that needs a new operator names it, and that operator is qualified once, for every row that uses it |
| AV | Description rows need no draws (analyst). Reason: a count has no interval to draw | A count, a codebook check or a table with no registered contrast is filed from one pass, with its hash. No 2,000-draw run and no replay. Every registered contrast keeps its draws and its replay |
| AW | Family ties in sealed draws (analyst) | A sealed job draws whole families where the joined folder carries the study's family number, and whole people where it does not. If it does not, the status table says so and each verdict carries the sentence: intervals treat relatives as unrelated. SM1 and SM2 no longer wait on the family fields |
| AX | One sealed job, several tables (analyst) | Each sealed job is a build, so SM1's job also writes the two tables of section 5.4. A table whose variables the status table shows missing is skipped and named; it does not hold the others |
| AY | A ledger row may be written by hand (analyst) | Card RC1 asks for one ledger row at every landing. Until the ledger's tool exists, the owner appends the row as one line of JSON in the landing's own change, in `results/EVIDENCE_LEDGER.jsonl`, with the eleven fields of yesterday's card. LA6's landing gets its row this way first |

**Stated by the curator and not ruled. Build nothing on these:** a reference is set by whatever sets the schema; a social contract as a second convergent solution; where Neuroticism sits (row NT1 tests it and assumes no answer); Belonging as being predicted by other people; second-order slopes as triggers; a channel taken up and used by a schema.

## 3. The build order

One owner, from the top. While a long job runs, the next item is built.

| # | Build | What it yields | Handoff leg |
|---|---|---|---|
| 1 | The policy transition that the open item S15-W6-LATTICE-POLICY names, from the bounds of yesterday's section 6 | KP1's remaining draws start in the same turn (about 67,525 CPU-seconds by the projection yesterday's packet cites), which is the slots' first long job. Every diary row can then be charged | |
| 2 | The diary producer, reading the rows table | LD2 in its three forms, then LD1, then LD3, each as 2,000 draws and a replay | 6 (A4) |
| 3 | Rows NT1.d and NT1.e, from operators this repository already has. Then, only if NT1.d clears the way, the trait file and rows NT1.a to NT1.c | Section 4 | 3 (N1), 4 (D5) |
| 4 | LA6.s as frozen; LA6.sl; the pooled act table | Rows LA6.s, LA6.sl and LA9 | 7 |
| 5 | The reference card | Row D3 | 8 |
| 6 | SM1's job, with amendments AW and AX | The MIDUS table and two added tables | 9 (C1) |
| 7 | The second sample for suddenness | Row R1.i | 2 (R1) |
| 8 | The rest of yesterday's packet, in its own order | LD4, LB1, LB3, LB2, SM2, SC1, LA7, LA8, LB4 to LB6, SC2, SC3 | |

**Not in this order, with the reason.** Leg 1 (the word table) and leg 5 (which need tags part) are the engine's. The suddenness leg's first sample is the engine's too, on the recalled-event reports with 21 ratings. The twin leg is parked by the handoff. CH14 is closed and is not reopened. The withdrawn row of leg D2 is not built.

## 4. Row NT1: where Neuroticism sits (handoff leg 3; claim S3)

- **Why.** The curator reopened it and asked for a clean test. The two readings that explain the most differ on one thing: whether Stress is stronger in a person high on the trait, or drains more slowly.
- **What this repository's record already says.** The handoff asks that two cards be read before designing. The first found a person's own reactivity too unsteady across halves of the diary to compare, so no row here compares people's own slopes. The second, the persistence grid on the same large diary (S15-W6-ES3-GRID-0057-20261118), left its primary inconclusive with limited sensitivity; by the independent checker's reading of that record, anger carried into the next activity at about 0.07 to 0.09 in standard units (the analyst did not open the record). So little is left at the next prompt in this diary, and the fixture's second setting below is the realistic one.
- **Two stages, because of that.**
  - **Stage 1 is rows NT1.d and NT1.e:** what is left at the next prompt after a criticised moment, whatever the trait, and how that falls with the hours between prompts. They need no trait file and no new operator.
  - **Stage 2 is rows NT1.a to NT1.c,** and it runs only if stage 1 finds that what is left has an interval above zero and is at least three tenths of first size. If not, the row files that this diary cannot place the trait at this spacing, the trait file is not fetched, and the question rests on the sealed table NT1.s (section 5.4).
- **The codebook check the handoff asks for, done by the analyst from public records.** The two status diaries prompt six times a day for fourteen days, at least 40 minutes apart, with time stamps. Their momentary tables carry no trait score. The study's own data paper says a person-level questionnaire was answered on the first and the sixteenth day, with a Big Five short form in the large sample and sixteen Neuroticism adjectives in the small one, and that all data sets and codebooks are in its public deposit under CC BY 4.0 ([Ryvkina and others 2023](https://doi.org/10.5334/jopd.83); read through a page summary, so the codebook governs).
- **Data step, stage 2 only.** The data agent fetches the person-level files and codebook from that deposit, whose address is in the admitted member's own record, and files an admission note with the licence as the deposit states it. Nothing else is fetched.
- **Join.** By participant id. First check that the ids of the admitted copy match the deposit's. If they do not, the row reads the deposit's own momentary file for the same sample, after showing it matches the admitted copy on the number of prompts and on each item's mean.
- **The score.** The mean of the scale's items after reverse-keying by the codebook, from the first questionnaire, standardized across people.
- **Prompts used.** An answered prompt whose previous answered prompt of the same day was an interaction prompt, with four hours or less between the two by the time stamps.
- **Outcome.** Form O. Primary: any of five bad feelings above its floor at this prompt (angry, ashamed, insecure, anxious, sad; the `int_` item at an interaction prompt, the `occup_` item at an activity prompt, with a flag for which).
- **Predictors.** `status_criticised` at this prompt (zero at an activity prompt) and at the previous prompt, each centred and scaled as Form O says, with the person's own means; the other five status events at both prompts; the hours between the prompts. In stage 2, also the score, the score times criticised now, and the score times criticised before.
- **Read.** $B_1$ and $B_2$ are the coefficients of criticised now and criticised before: first size and what is left. $C_1$ and $C_2$ are the coefficients of the two products with the score.

$$\text{RATIO} = \frac{C_2}{B_2} - \frac{C_1}{B_1}$$

  Each fraction is the proportional change in an effect per standard deviation of the trait. If a high scorer's answers are only noisier, a logit shrinks both of her effects by the same proportion, the two fractions move together, and RATIO stays at zero. The plain difference $C_2 - C_1$ does not have that property and is filed without a verdict.
- **Support, counted before any outcome is read.** At least 300 used prompts with criticised before above its floor, from at least 150 people.
- **Rows.**

| Row | What | Registered |
|---|---|---|
| NT1.d | $B_2$ by itself: what is left at the next prompt, whatever the trait (claims S2 and S4) | positive, at the default bar for a Form O coefficient, 0.10 log-odds per within-person standard deviation, with its interval above zero. Both claims expect something left while the cause is still open, so this row does not separate them. It decides whether stage 2 runs |
| NT1.a | RATIO, large sample, the primary outcome | positive (the theory thread's: the score goes with what is left more than with first size). Bar: its interval above zero |
| NT1.b | RATIO for each of the five feelings, large sample | description, one dot row |
| NT1.c | NT1.a in the small sample | description; the fixture shows it cannot decide |
| NT1.e | $B_2$ by thirds of the hours between prompts (stage 1) | description |

- **What each outcome means,** with every pattern the fixture produced. The row also files the trait's own coefficient, which says whether high scorers start from a higher baseline.
  - RATIO's interval is above zero and the trait's own coefficient is positive: the trait goes with how slowly the feeling drains, the theory thread's reading. With a higher baseline, saturation pushes RATIO down and not up, so this reading survives that rival.
  - RATIO's interval is above zero and the trait's own coefficient is not positive: not read. The fixture produces this with nothing planted when high scorers start lower and the feeling saturates.
  - RATIO's interval includes zero and $C_1$'s interval is above zero: the trait goes with a stronger push at both prompts in proportion. That is the analyst's reading of the curator's standing ruling, "how strong the down is, is neuroticism."
  - RATIO's interval includes zero and $C_1$'s interval is not above zero: no placement. Three of the fixture's worlds look like this, and nothing about what is left is planted in any of them.
  - RATIO's interval is below zero and $C_1$'s interval is above zero: the trait goes with first size more than with what is left.
  - RATIO's interval is below zero and $C_1$'s interval is not above zero: read as saturation at a higher baseline, which the fixture produces with nothing planted. Not a finding.
- **Fixture, computed (`pf_n1.py`).** Thirty made worlds a row, 2,272 invented people, about 20,000 used prompts, a tenth of them with criticism before; spreads in brackets.

| World | Plain difference | RATIO |
|---|---|---|
| Nothing planted | plus 0.003 (0.017) | plus 0.009 (0.086) |
| **High scorers' answers only noisier** | **plus 0.024 (0.023); its interval is above zero in 23% of worlds** | minus 0.029 (0.099); above zero in 3% |
| The trait raises first size and what is left in proportion | minus 0.053 (0.024) | plus 0.007 (0.121); above zero in 10% |
| The trait raises only what is left, by half per standard deviation | plus 0.088 (0.020) | plus 0.517 (0.107); above zero in every world |
| The same, and answers noisier too | plus 0.114 (0.021) | plus 0.499 (0.109); above zero in every world |
| The trait raises only first size | minus 0.109 (0.027) | minus 0.305 (0.114); below zero in 77% |
| *Worlds that break the form; nothing is planted about what is left (the independent checker's)* | | |
| High scorers meet criticism more often | minus 0.006 (0.027) | minus 0.015 (0.109); below zero in 7% |
| **The feeling saturates, and the trait raises its baseline** | minus 0.011 (0.032) | **minus 0.117 (0.056); below zero in 67%** |
| Normal noise in place of logistic; the trait raises the baseline | minus 0.002 (0.039) | minus 0.031 (0.094); below zero in 13% |
| **The feeling saturates, and the trait lowers its baseline** | plus 0.019 (0.030) | **plus 0.124 (0.045); above zero in 70%** |

  **What the design can see.** The realistic setting first. A second run made what is left between a seventh and a fifth of first size, as the form reads them: RATIO's interval was then 0.7 either way or wider, a planted half was seen in 40% of worlds, RATIO still read near zero when answers were only noisier (minus 0.042, spread 0.334), and the plain difference was fooled in half of those worlds. In the table's first six worlds what is left was half of first size, and RATIO's interval was about 0.2 either way. With 327 people it was 0.6 to 0.9 either way even then. So this row can place the trait only if a good share of the feeling is still there at the next prompt, which is why stage 1 comes first. Where the trait raises the baseline and the feeling saturates, RATIO reads about 0.12 too low, so a true excess of that size or less would be hidden.
- **Qualification.** The product with a trait and RATIO are one new operator, qualified only if stage 2 runs. The build reproduces the ten worlds of `pf_n1.py` within two of the listed spreads. In the noisier-answers world the first product reads near minus 0.06; a build that reads it at zero has not reproduced the world.
- **Limits.** One kind of event, reported by the person it happened to. The feeling at the next prompt is about the next interaction or activity, so what is left is carried into a new moment and is not the old feeling measured again. The trait is a questionnaire score. The form is exposed to saturation, as the fixture shows.
- **Prior art.** Reactivity and carry-over have both been tied to Neuroticism in diaries ([Suls, Green and Hillis 1998](https://doi.org/10.1177/0146167298242002); title and abstract opening checked, paper not opened), and day-level reactivity in the sealed diary ([Mroczek and Almeida 2004](https://doi.org/10.1111/j.0022-3506.2004.00265.x); abstract checked). The same project's data has a paper on Neuroticism and negative feeling in daily life ([Kroencke and others 2020](https://doi.org/10.1016/j.jrp.2020.104038); title checked); under amendment AI its design and stated hypotheses are read before stage 2 is frozen, and its result tables are not used. Not found in a light search: the two put against each other as a ratio after one kind of event within a day.

**Leg D5, the settled half.** No held open diary asks whether an event was settled (the analyst's keyword scan of the public item lists of the 63 members in the catalogue copy it read; a scan, not a reading of each codebook). The leg is parked for open diaries, and row NT1.d carries its plain half. The settled half rides in SM1 (section 5.4).

## 5. The other items

### 5.1 LA6.s, LA6.sl and LA9 (handoff leg 7 and its section 11.7; claim T7)

- **LA6.s** runs as this repository froze it in its follow-up record of 19 November, both windows, unchanged. It keeps the prior-art line of LA6's own card.
- **LA6.sl, a new row beside it (the theory's ask).** The same labels and pairs with utterance length held: each matched pair is also matched on word count within two words or a fifth, whichever is larger. Where that leaves under half the pairs, word count enters both arms as a covariate and the figure is given with and without it. Bar and reading as registered for LA6. If LA6.s lands and LA6.sl does not, length was doing the work. No new search was made for it: it is the same test with one more thing held.
- **LA9, the pooled act table.** LA6's act-type table had no result because every resample lacked a label. The labels are pooled into each annotation scheme's own published general classes, the mapping is filed with its hash before any outcome is read, and the table is run again. A class with under 50 utterances in the held-out meetings is listed and not scored. No prior-art search was made for it: it is LA6's own table with pooled labels, and nothing in it is called new.
- **Limit**, as LA6's record has it: this tests an observable context of laughter, not PLAY or its trigger.

### 5.2 Row D3: the reference in the phone game (handoff leg 8; claims N3, N5)

- **Do.** Refit the repeat-play model of the set-point cards on the same held-out split with three references: the starting score, the last session's end, and the best level held so far. The repository gives the card the next id in its set-point family.
- **Registered** (the theory's): the best level held so far fits best on repeat plays. **Bar** (the analyst's): its held-out log-likelihood per play is above each of the other two, with both intervals above zero, by 2,000 draws of whole players.
- **Limit**, the handoff's: a game score is not anyone's meaning. The leg tests the shape.
- **Prior art.** A reference point that follows a past peak is an established idea in the study of choice under risk (from the analyst's memory; not looked up for this packet). The card refits this repository's own model, and nothing in it is called new.
- This is the card to which the handoff now gives more weight, because the two results under claim N3 show two different things.

### 5.3 Row R1.i: suddenness and anger, the second sample (handoff leg 2; claim T1)

- **Source.** The older recalled-event set of seven feelings this repository holds (ISEAR), in which each person wrote one event to each feeling and rated it.
- **Binding check first** (amendment AU): the items for how intense the feeling was, whether the event was expected, who caused it, and how pleasant it was. A missing item voids the row.
- **Form.** Within anger reports: intensity on expectedness reversed, with who caused it and pleasantness as covariates, standardized within the feeling. The same within sadness reports. Draws are of whole people, since each person gives both reports.
- **Registered** (the theory's): the slope is positive for anger and larger than for sadness. Bars as the engine's card TP35, in standard deviations of intensity per standard deviation of the predictor: 0.08 for the slope and 0.08 for the difference, each with its interval above zero.
- **Limits.** Expected is not the same word as sudden. A report is a remembered case of a feeling word.
- **Prior art.** As for the engine's card TP35: which appraisals predict how intense anger is has been studied ([Van Mechelen and Hennes 2009](https://doi.org/10.1080/02699930902958297); title checked, paper not opened). Not found in a light search: this slope within anger against the same slope within sadness.

### 5.4 SM1's job (handoff leg 9; amendments AW and AX)

Yesterday's card stands. Its job reads `midus-m2-joined`. Two tables are added to the same `run.py`:

- **NT1.s, where Neuroticism sits at one report a day.** Negative feeling today on any stressor today and any stressor yesterday, each centred on the person's own mean, with the survey's Neuroticism scale as the trait and RATIO as in section 4, read by the same branches. Registered as NT1.a. The handoff says one report a day cannot separate the two readings; with yesterday's stressor and today's in one model it can, coarsely. Limits: a day is a coarse step, so what is left here is what is left the next day; stressors and feelings come from the same evening call; and RATIO's exposure to saturation applies here as in section 4.
- **D5.s, settled or not** (claims S4 and S2). If the status table shows a variable for whether an argument was resolved: negative feeling on the day of an argument and on the day after, by resolved or not. Registered (the curator's reading): what is left the next day is larger when the argument was not resolved. Bar: that difference above zero with its interval, by the draws of amendment AW. This contrast is in print for a daily diary of this family ([Witzel and Stawski 2021](https://doi.org/10.1093/geronb/gbab006); title and abstract opening checked, paper not opened), so the table is labelled a replication, and what the paper found is not restated here because the analyst has not opened it. Limit: whether an argument was resolved is the person's own report on the same call, and a resolved argument may differ from an unresolved one in more than being resolved.
- Both tables keep the three habits of yesterday's section 3.7 and return totals only.

## 6. Predictions before data (the analyst's guesses, filed so they can be scored)

| Row | Guess |
|---|---|
| LD2 (b) | positive and under its bar |
| LD1 | positive: an audience turns shame up |
| NT1.d | positive, and under three tenths of first size, so stage 2 does not run |
| NT1.s | RATIO's interval includes zero and $C_1$ is positive: at one report a day the trait goes with first size |
| LA6.sl | the with-history arm falls under 0.60 once length is held |
| D3 | the best level held so far fits best |
| R1.i | the anger slope is positive and not larger than the sadness slope |
| D5.s | larger when not resolved |

## 7. Bounds

Unchanged from yesterday's section 6. Each row of this packet is charged to the family its source belongs to: 20,000 CPU-seconds a row including replay for diary rows, 30,000 for LA6.s as registered and the same for LA6.sl, 10,000 for LA9 and for D3. Sealed runs stay within the thirty of yesterday's table.

## 8. The return

The Week 6 return gains one row for each row of this packet: verdict word, estimate, interval, bar, the limit sentence, the ledger row's id and the result sheet's path. It names which branch of "what each outcome means" a result falls in and stops there. It lists which of section 6's guesses held.

## 9. Limits of this packet

- The pre-flight covers one new operator (the product with a trait, and RATIO) in constructed worlds, four of which break it. Nothing else here was pre-flighted.
- The trait's presence in the deposit is taken from a summary of the data paper, not from the codebook.
- The scan for a settled item was by keyword.
- The persistence grid's figures in section 4 are from the checker's reading of this repository's record, not the analyst's.
- The build order is a judgment about cost. If an item turns out to need a decision this sheet did not make, the owner files it as blocked with its reason and builds the next one.
- Every source here is self-report.
