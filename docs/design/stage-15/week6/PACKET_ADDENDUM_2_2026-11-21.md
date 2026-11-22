# Sounding Line, Stage 15, Week 6: second addendum of 21 November

*From the implementation thread (the analyst) to the registered owner agent. It adds to this morning's packet extension and to the afternoon addendum, whose text, terms, rulings and bounds stand. It carries no questions. The storage hold of amendment BI stands until the curator says the store is back.*

## 0. Read first

- **Why.** The afternoon addendum went from filing to its commit in under two hours, and its rows used under 200 CPU-seconds. Machine time is not what limits this repository, and neither is building a row on a diary already admitted: what the twelve admitted diaries can say about a person's own slopes is now said. Three slopes are held in member 0057 and two in 0056, all on pleasant events. No unpleasant slope is held, row PST6 had one pair, and no admitted diary rates how bad an event was. The work that takes a night is admitting diaries that do.
- **What this is.** Six open diaries to admit, in order (a seventh is named and held back), each chosen from its public item list because it rates an event on three or more values. Then one pooled picture, and two rows on what is already here.
- **Where files go.** This file at `docs/design/stage-15/week6/PACKET_ADDENDUM_2_2026-11-21.md`. It needs no new bundle: the operators are the ones already qualified under amendments BN and BR.
- **Amendment BT (analyst).** The diaries below are commissioned for admission under amendment AI and this repository's own admission rules, none of which changes. One design note covers the family, and each diary adds its binding table, its codebook check, a reading of its source paper's design and its support count. A diary's file is the member's release in the collection's own archive (the `zenodo_doi` of its metadata), so that it is the same file the store holds. The data agent fetches it into the temporary root's `incoming` folder with its hash, under the 1 GB limit of amendment BI, and when the store is back the hash is compared with the store's copy.

## 1. The diaries, in this order

Item names are from public item lists. Each is confirmed against the codebook before any row is frozen, and a row whose item does not bind is void.

| Order | Member | People, length as listed | Event items | Feelings | Why it is here |
|---|---|---|---|---|---|
| 1 | 0010 | 130; 20 days, 10 prompts a day | pleasantness of the most important event, 8 values | cheerful, worried, fearful, sad, relaxed | A long diary (200 prompts), so the gap split has room. A third diary for PLAY's off switch. A clinical sample in a trial with two study periods: every form is run inside the first period, the second is filed beside it, and every result says so |
| 2 | 0073 | 227; 10 days, 6 a day | how bad the worst experience was, and a positive event, 7 values each | a two-axis mood rating. Its guilty and embarrassed items are about her own emotion and are not used | The plainest rating of how bad an event was |
| 3 | 0003 | 122; 10 days, 3 a day | five kinds of stressor (argument, let pass, friend or relative, health, other), each not endorsed or rated on four steps | nervous, afraid, scared, distressed, worried. Its sadness item asks how often since the last prompt and is filed apart | Unpleasant slopes on different events in one person, which rows PST3 and PST6 have lacked |
| 4 | 0055 | 72; 21 days, 6 to 7 a day | family members fighting, 1 to 100 | sad, anxious, angry | Long, with three unpleasant feelings on one event |
| 5 | 0023 | 213; 22 days, 3 or 5 a day | dealt with stress, 0 to 100 | overwhelmed | A second graded stress item |
| 6 | 0049 | 803; 7 days, 5 a day | whether she helped someone, and her effort, 0 to 100 | valence, calm, energy, stressed | A pleasant slope at scale. Effort is not how good the event was, and the row says so |

**Held back.** Member 0075 (1,284 people, 30 days) reports whether a stressor happened and, apart from that, how stressful it was, which is the cleanest form there is. This repository's tools record its licence as unresolved, so it is not fetched. The data agent is asked to resolve it.

## 2. Rows on each new diary

For every event and feeling pair that binds: rows PST1 (the raw slope), PST4 (the graded slope) and PST5 (the gap split), exactly as built. A slope is held on the afternoon's definition.

- **Families.** A slope belongs to the unpleasant family when its event is an unpleasant one and to the pleasant family when its event is a pleasant one, whatever the feeling item. Where one event item runs from bad to good, its lower half is an unpleasant event graded by distance below the midpoint and its upper half a pleasant one, and the codebook check must confirm the midpoint. If it cannot, that item is void.
- **One dial (row PST3's form and bars), where a diary has unpleasant slopes on different events:** member 0003. This is the curator's reading tested as he states it, a person's steepness shared across kinds of event. Registered (the curator's): one. Pairs on different events only.
- **Member 0010 also gets row PBK1's form:** cheerful on fearful and on sad in one model, and the contrast enters the pool beside the two filed diaries. The pooled row is filed again with three, and it says that one of the three is a clinical sample.
- **Member 0003 also gets a description in row ANX1's form:** nervous and worried each on afraid. It has no curiosity item and no plain sadness item.

## 3. Rows on what is already here

| Row | What | Registered |
|---|---|---|
| PST8 | A reconciliation. Row PST7 reports that, for every slope that could not say this morning, spread was dropped and the slope went unadjusted in every draw, while level repeats between halves at 0.34 to 0.83 and several raw variances are clear of zero (for one, 0.45 with an interval of 0.23 to 0.71). If the slope was unadjusted, the adjusted variance is the raw one and should be clear too. The row states, for three such slopes, the raw variance, the adjusted variance, the two fallback shares and the level covariance in its own units, from one run, and says which of the morning's or PST7's figures was wrong, or why both are right. It also explains row PST6's one pair, whose covariance of minus 0.079 lies outside its own interval of minus 0.029 to 0.042 | none. A check on the build. If it finds a fault in the operator, the morning's and afternoon's person rows are run again and filed as corrections before any new diary's rows |
| PST9 | The pooled picture (amendment BH). For each form, over the new diaries only, one slope a diary a family (the one with the most people): the level-adjusted variance as a share of the squared mean slope, pooled by inverse variance within two families, slopes of unpleasant feelings on unpleasant events and slopes of pleasant feelings on pleasant events, with the single results beside the pooled figure and their disagreement stated. Every other slope, old and new, is shown beside as description | the theory's claim P4: people differ in their slopes. Bar (the analyst's): the pooled share has its interval above zero in all three forms, for each family apart |

- **What each outcome means for PST9.** Both families clear: slopes are a person's own for unpleasant and pleasant events alike, as far as her own ratings reach. Only the pleasant family: what has been found so far, at more diaries. Neither: the held slopes of the status diaries do not generalize.
- **Limit.** The pooled share weights long diaries heavily and rests on five diaries at most. It is a picture first.

## 4. Order and bounds

| When | What |
|---|---|
| First | PST8. The request to the data agent for the six releases. The family's design note |
| Then | The diaries in the order of section 1, each through admission and its rows before the next is started. PST9 is filed after the third diary and again after each one that follows |
| If a diary cannot be admitted | Its reason is filed and the next is started. Nothing waits |
| When the lattice's open rows can run | Any row left open on the 19 November lattice whose source is in the temporary root may run in the slots the sweep leaves idle, under its own existing allowance |
| When the curator says the store is back | The morning's section 3 step 6 and SMF1's three runs go ahead of everything here |

Each new diary has 20,000 CPU-seconds for its rows including replay. The freeze, the drain and the addendum times are unchanged. When building is the bottleneck, drop from the bottom of section 1.

## 5. Predictions before data (the analyst's guesses)

| Item | Guess |
|---|---|
| PST8 | PST7's two shares were computed on the wrong object, and the operator is sound |
| Admissions by 08:00 on 22 November | Three of six |
| Member 0010 | A cheerful slope on a pleasant event is held. No unpleasant slope is |
| Member 0073 | The slope of the mood rating on how bad the event was is stable in the graded form |
| One dial, member 0003 | Undecided |
| PST9 | The pleasant family clears. The unpleasant family does not |

## 6. The return and limits

- One row a result in the Week 6 return, and one line a slope saying held or not and which form failed.
- Every rating here is the person's own. Member 0010 is a clinical sample in a trial. Sizes, lengths and item names are from public listings and not from codebooks. No file size is listed for any of the six.
- Nothing here was pre-flighted anew. Row PST9's pooling and row PST3's form on more than two slopes have not been run on made worlds.
- Picking a person out is not run on the new diaries. Nothing is matched to any outside source.
