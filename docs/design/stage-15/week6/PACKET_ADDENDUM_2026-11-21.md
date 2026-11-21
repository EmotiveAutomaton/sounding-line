# Sounding Line, Stage 15, Week 6: addendum of 21 November, afternoon

*From the implementation thread (the analyst) to the registered owner agent. It adds to the packet extension of this morning, whose text, terms, rulings and bounds stand. It carries no questions. The storage hold of amendment BI stands until the curator says the store is back: nothing here reads the bulk store, and every row reads the temporary data root.*

## 0. Read first

- **Why.** This morning's rows all landed or voided by 09:42, and the slots are idle until the store returns. Four person slopes came back stable beyond level and spread in each of the two status diaries (members 0057 and 0056), and every return row carries the same limit: how bad her events are, and a mood that lasts, can also repeat. This addendum goes at those two limits directly, on the same files.
- **Where files go.** This file at `docs/design/stage-15/week6/PACKET_ADDENDUM_2026-11-21.md`. `PREFLIGHT_2026-11-21b.zip` beside the earlier bundles; its `pf_addendum.py` is the known answer for rows PST4 and PST5.
- **Amendment BR (analyst).** Two forms are added to the operator of amendment BN and qualified against `pf_addendum.py`: the graded slope and the gap split. Nothing in BN changes.

## 1. Terms added

| Term | Meaning |
|---|---|
| Graded slope | For one person in one half: the least-squares slope of the feeling on the event's own rating, over that half's prompts. It needs two prompts at the rating's lowest value, two above it, and two different values above it. A person counts by the smaller, over her two halves, of prompts times the variance of the rating. Level and spread are as before, taken at prompts where the rating is lowest |
| Gap split | The two halves are the first third and the last third of a person's diary in time. The middle third is not used |
| Held | A slope whose level-adjusted variance has its interval above zero in the morning's form, in the graded form and across the gap |

## 2. Rows

Each runs on every slope that row PST1 ran in members 0057, 0056, 0060, 0072 and 0076, the morning's first sets and the expanded sets alike. Bars are the morning's: the level-adjusted variance has its interval above zero, from 2,000 draws of whole people. One result sheet for a diary shows the three forms side by side for every slope (amendment BH).

| Row | What | Why | Registered |
|---|---|---|---|
| PST4 | The graded slope in place of the raw slope. A slope whose event item has fewer than three rating values in its codebook is void for this row, which a binding check settles first. The parents' diary records its event as yes or no and is void | A person whose events are worse rates them higher, so a slope for each step of her own rating does not grow with how bad her events are | the analyst's: the slopes that were stable this morning stay stable. No theory claim is registered |
| PST5 | The raw slope on the gap split | A mood that runs for days sits in both of two adjoining halves and rarely in the first and last thirds | the analyst's: the same |
| PST6 | One dial or several, among held slopes of any kind, pleasant ones included. Form and bars as row PST3, on graded slopes. Pairs on different events are pooled apart from pairs on one event. Only plain slopes enter, not differences of two slopes. The two status diaries are pooled by inverse variance, and any other diary is filed alone | This morning no pair of unpleasant slopes qualified. The slopes that did are mostly pleasant | none. A description: the curator's reading of one dial is about unpleasant slopes, and this row is not that test |
| PST7 | For each slope that could not say this morning: people with the slope, her median count of event prompts a half, the correlation of level between halves, the share of draws in which spread was dropped, the share that went unadjusted, and the raw variance with its interval | Intervals such as minus 3.1 to 0.08 did not occur in any made world, so the fixture does not explain them | none. A description |

- **What each outcome means.**
  - A slope is held: people differ in it beyond where they sit, beyond how bad they rate their events, and beyond a spell of days. That is the strongest reading of claim P4 these diaries can give. It still rests on her own rating of the event.
  - Stable this morning and not in PST4: the morning's result is as well explained by whose events are worse.
  - Stable this morning and not in PST5: as well explained by a spell. In the short diary the gap split keeps under half the people, so a miss there is weak.
  - PST6 reads one on pairs from different events: a general readiness to respond, of any sign. One only on pairs from one event: one kind of day. Several: the slopes are a person's separately. One on pairs from one event and several on pairs from different events: one kind of day, and separate slopes. Undecided: the correlation with its interval. No held pair: no verdict.
- **Fixture, computed (`pf_addendum.py`; worlds of 100, short diary then long).**

| Made world | Bar met, raw slope | Bar met, graded slope |
|---|---|---|
| Nothing personal | 3, 2 | 6, 1 |
| Nothing personal, feeling at the bottom of its scale | 2, 3 | 3, 3 |
| Slopes truly differ | 100, 100 | 100, 100 |
| People differ only in how bad their events are | 91, 99 | 2, 6 |
| The same, feeling at the bottom of its scale | 43, 68 | 5, 3 |
| The same, and her rating is a poor copy of how bad the event was | 82, 98 | 27, 66 |

| Made world | Bar met, halves | Bar met, gap split |
|---|---|---|
| Nothing personal | 1, 1 | 1, 3 |
| Nothing personal, feeling at the bottom of its scale | 2, 1 | 0, 1 |
| Slopes truly differ | 100, 100 | 69, 98 |
| Slopes run in spells of several days | 23, 8 | 1, 2 |

  - So the graded slope removes the severity reading only as far as her rating tracks it, and the last row of the first table is the limit that travels with PST4.
  - In the short made diary the gap split kept about 309 of 2,272 people.
  - A steadier interval was tried, with the adjustment's coefficients held fixed across draws. It raised the bar count by up to 13 in 100 where slopes differ under a heavy floor and left the worlds with nothing personal unchanged. It is not used today.
- **Qualification.** Run on the worlds `pf_addendum.py` makes with its seeds, the build matches its two tables within 0.10 in every column that counts worlds. The fixture used 300 draws a world, and the rows use 2,000.
- **Limits.** Every feeling, event and rating is the person's own report at one prompt. The fixture has one event rate and one rating scale, and in it the feeling rises evenly with each step of the rating. If a feeling instead jumps once and stays flat across ratings, the graded slope moves with how a person uses the rating, which is the reverse fault. The fixture compares the raw and graded forms on slightly different sets of people. Row PST6 was not pre-flighted beyond the morning's two-slope worlds.
- **Prior art.** No search was made. Nothing here is called new.

## 3. Order and bounds

| When | What |
|---|---|
| First | PST7, which needs no build. Build the two forms and qualify them |
| Then | PST4 and PST5 on member 0056, then 0057, then the other three. PST6 last |
| When the curator says the store is back | The morning's section 3 step 6, then SMF1's three runs, ahead of anything left here |

Under amendment BR each diary has a new allowance for rows PST4 to PST7 together, apart from the morning's: 20,000 CPU-seconds including replay. The freeze, the drain and the addendum times are unchanged. When building is the bottleneck, drop from the bottom: PST7; PST4 on the two status diaries; PST5 on the same; the other diaries; PST6.

## 4. Predictions before data (the analyst's guesses)

| Row | Guess |
|---|---|
| PST4 | The pride and admiration slopes stay stable in member 0056. Criticised anger in 0056 does not |
| PST5 | Could not say in the short diaries |
| PST6 | No verdict |
| PST7 | The slopes that could not say have few people with two events in each half |

## 5. The return

One row a result in the Week 6 return, with the verdict word, estimate, interval, the limit sentence and the ledger row, and one line a slope saying held or not, and which form failed.
