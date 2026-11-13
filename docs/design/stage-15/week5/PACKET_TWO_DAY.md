# Sounding Line Stage 15, Week 5 close: two-day packet

12 November 2026. For the registered owner of Sounding Line. Sized for 13 and 14 November, ahead of the Week 5 cutoff on the 15th. File in the repository as `docs/design/stage-15/week5/PACKET_TWO_DAY.md`. It adds to `PACKET_BACK_HALF.md`. Nothing there is withdrawn unless section 2 says so.

This is a spec sheet. It carries no questions for the curator. Choices are made here and listed in section 2.

## 0. Read first

**Sources.** The Round 15 theory handoff (`claude/THEORY_HANDOFF_2026-11-12_R15.md`), the Round 14 and Round 13 handoffs, and the theory thread itself for 11 and 12 November (the curator's three turns and Round 15's messages in full; the result and test sections of Rounds 13 and 14). This repository at `e81f11648` (re-fetched just before this packet was filed): `THEORY_RETURN.md`, the health record of 12 November 13:29, the 12 November digest, the chess source code, and the designs named below, including the five prepared designs filed that evening. Three capped lookups by a cheaper model for outside data and prior work; where a fact rests on those it is marked with how it was read.

**The build rule from Round 15.** Safe to build on: Standing recorded as two variables (seen as competent, seen as kind); Stress identified with free energy; channels able to serve any set point; the rule that a channel needs a tissue study; the corrections in that handoff's section 7. Everything marked "mine, awaiting his ruling" there is a proposal. A card may test a proposal. Its record may not speak as if the proposal were settled, and each card below names whose idea it carries.

**Standing rules.** No analysis of sex differences (note a one-sex sample in a clause). Adult self-report is lowercase evidence. No human participants. CPU only; GPU, Ollama and paid calls stay off. No raw CoAuthor text leaves `private/` or `raw/`. The handoff's sensitive item stands: the curator's account of shame and suicide is theory on record, nothing here collects data on it, and no card selects, counts or reports texts about self-harm.

## 1. The state this packet starts from

| Fact | Value | Where |
|---|---|---|
| Counted slots in use | 1 of 8; "the immediate gap is review/admission of those implementations, not hardware saturation" | `HEALTH_20261112_1329.md` |
| Slot-hours, 12 November digest | 27.32 occupied, 160.88 idle (85.49% idle); "Owner review and unfinished source/interface qualification are the directly observed bottleneck" | `DIGEST_20261112.md` |
| Ready cards waiting | 0 against the 16 required | same |
| Landed since the back-half packet | IN5, IN6, IN7, RR1, EX1, EX2, EX3 on the 11th; GO1, GO1.d and the chess source on the 12th | `THEORY_RETURN.md` |
| Built and waiting for review | LA3, LA4, TR1, CH7, EX4 (prepared designs filed 12 November: `LA_BACK_HALF.md`, `TR1_BACK_HALF.md`, `CH7_BACK_HALF.md`, `EX4_BACK_HALF.md`), RR2, the R1 reader work | `DIGEST_20261112.md` |
| Chess engine scoring | the 19,904-position prefix of 398,065 is authenticated and the continuation is running; 2.971987 CPU-seconds per position | `CH1_N_PREFIX_20261112.md` |
| Scoring left | about 312 CPU-hours: 6.5 days on the one two-thread slot now used | computed here |
| Sampled-player histories | 412,173 + 425,932 + 425,267 = 1,263,372 complete games with clocks, April to June 2017 | the three census records |

Two things follow, and the packet is built on them.

1. **The queue is bound by review.** So the cards below are ordered by how much theory each buys per review. Most are formulas on a table that is already verified.
2. **Round 15's chess tests do not need engine scores.** The handoff calls test 1 "cheap once scoring finishes". Its outcomes (stopping, rematching, playing on) are in the histories now. Waiting for scores would cost about a week.

## 2. Amendments and rulings

**U. Table cards (extends amendment Q).** A card is a table card when its only inputs are a table or bank already landed and verified in this stage, or SG1 once SG1 has landed and been verified, and its computation is written out in this packet. It admits on a design commit and the packet's fixture. Its independent replay is a second implementation of the formula on the same table. It needs no source re-qualification.

**V. Shards for chess scoring.** If the committed queue manifest admits disjoint position ranges, the scoring continuation runs as up to five shards of two threads each, with contiguous ranges fixed by position ordinal before launch, the same pins, the same per-unit native replay and one cost record per shard. Shards pause in reverse order if commit headroom nears the floor. Five shards finish the remaining 312 CPU-hours in about 31 hours. If the manifest does not admit ranges, record why and continue serially. Scoring never takes review time from section 3.

**W. Fixtures come with the packet.** Each new card below has a hand-checkable fixture or a planted-effect fixture stated here. A builder may add cases. A fixture's expected values are never produced by calling the adapter under test. This answers the health note on CH7 ("the native source fixture also derives its expected rows by calling the adapter it is testing").

**X. The activation log.** The curator: "God, I wish I had more examples of when various networks went off." Every result filed from now on carries, beside amendment S's tags, an `activation` list: channel in capitals, set point if any, what moved, what could be done, what was observed, and whether it goes with the theory's table, against it, or says nothing. One pass with no computation tags the Stage 15 results already landed and files `results/phase_2_4_stage_15/ACTIVATION_LOG.md` as one table. Ghost's V29 family C1 will send the list of event kinds on which the theory's two trigger tables disagree; mark those rows when it arrives.

**Y. Review order.** Section 4. The owner reviews in that order unless a gate fails.

**R5. Chess tests of Round 15 run on histories now.** Reason in section 1. "Safer play" in the handoff is measured here from moves and clocks (CH11 and pace) and not from engine scores.

**R6. No classifier-labelled emotion as a measure of shame, guilt, pride or contempt.** The published baseline on the 27-label Reddit emotion set reports F1 of 0.36 for pride, 0.43 for embarrassment, 0.45 for disgust, 0.47 for anger and 0.66 for remorse ([Demszky et al. 2020](https://arxiv.org/abs/2005.00547); read by a helper, table values as it reported them). Handoff tests 4 and 5 are therefore drawn with rule-based markers and self-labelled reports. Any word list used as a measure is frozen in the design commit and passes an instrument check before its card runs.

**R7. Two more Crowd-enVENT column groups may be loaded as numbers:** the event and emotion durations, and the short personality inventory's item scores. They serve IN11 and IN12 only. Demographic columns stay unloaded. Personality here is adult self-report.

**R8. Two new public sources are admitted for intake:** the Stanford wiki-RfA file and ConvoKit's Wikipedia talk-pages corpus (section 3E). Usernames become salted keys at intake. Text is used only to count frozen markers. Only aggregates leave.

**R9. ISEAR stays conditional,** as IN8 is. Section 3F runs only if the source and the curator's terms note are present under `data/external/isear/`.

**New family ceilings** for `FAMILY_CEILINGS` in `runners/drive/cards/week5_policy_v2.py`, in CPU-seconds: RF 40,000; CP 60,000; IS 40,000; SV 60,000. CH, IN, LA, MD and EX keep theirs.

## 3. Cards

Every card reports its estimate and interval, its bar, and amendment P's two numbers (what it sees; what it supports at). "Player-cluster" and "writer-cluster" intervals are 2,000 whole-unit resamples.

### 3A. Chess histories, no engine (family CH)

**Why this family first.** The histories hold a number that is public, changes after every game, and comes with a forecast: the rating gap says what result to expect. That makes them the only data in the program where "a drop below forecast" is measured and not rated. A game rating is not standing in a room, and every record in this family says so.

**Published neighbours, so the cards don't re-find them.**
- On another site's blitz games, about 60% of players were more likely to stop after a loss and about 25% after a win, and the types were stable across years ([Avoyan, Khubulashvili and Mekerishvili](https://www.ifo.de/DocDL/cesifo1_wp8603.pdf); read by a helper through a summary). It does not use the forecast.
- Players "exert effort to set new personal best ratings and quit once they have done so" ([Anderson and Green 2018](https://doi.org/10.1073/pnas.1706530115)).
- The template for an unexpected loss comes from football: losses when the home team was favoured by more than 3 points raised police reports of family violence by about 8%, and upset wins had at most a small effect ([Card and Dahl](https://www.nber.org/papers/w15497), abstract).
- A helper's search of about 20 queries found no study that compares unexpected with expected losses for ending a chess session. That search was not exhaustive.

#### SG1. The session-game table (one traversal, extending CH7's source wrapper)

`CH7_BACK_HALF.md`, filed on the evening of the 12th, notes that the earlier history projection omits pregame ratings, and prepares `week5_ch7_source_v1`: the existing source traversal and full raw replay, adding each sampled player's pregame rating, the opponent's pregame rating and the source ordinal. That wrapper has not had its first production run. **Extend it before it runs, so the three raw months are traversed once and not twice.** SG1 is that wrapper with the further fields below. CH7's fields keep their exact names and values, and a parity check on the fixture shows SG1 restricted to CH7's columns equals CH7's projection. The health note's two conditions for CH7 apply to SG1 as written: a read-only source open, and expected fixture values that no adapter produced (the table below).

One row per sampled player per game, kept under `private/`.

| Column group | Columns |
|---|---|
| Already in CH7's wrapper | player key, month, source ordinal, start time, time-control class, result, own rating change, own and opponent pregame rating |
| Added from the header | opponent key, colour, initial, increment, opponent's rating change, the Event tag reduced to tournament or not plus a salted tournament id, the Termination text |
| Added from the moves | plies; own and opponent first clock; own and opponent last clock; `duration_est` (defined below); own first move and, as Black, the opponent's first move; whether the last move gave checkmate (replay that one move from its stored position); final material balance, own minus opponent, with pieces at 1, 3, 3, 5, 9 |
| Derived, by CH7's session rule (within time-control class and month, starts under 1,800 seconds apart) | session id, index in session, seconds to her next game, STOP (no next game in the session), REMATCH (her next game in the session is against the same opponent key), censored (her last record in a class and month) |
| Flags | CH7's provisional rule: a session containing any rating change above 25 in size |

**Compute the move-level fields during the traversal, while the whole game is in hand.** The stored history payload keeps only the sampled player's own move rows (`week5_ch_source.py` filters rows to the chosen players), so the opponent's clocks, the final position and the mate flag cannot be rebuilt from it afterwards. `duration_est` is the summed think time of both sides plus, when the Termination is "Time forfeit", the loser's last recorded clock, since that time ran out unrecorded.

**Fixture (hand-checkable).** One player, one month, blitz 180+0, five games. Expected score in the fixture is `1/(1 + 10^(-(own - opponent)/400))`.

| Game | Start (s) | Own, opponent rating | Opponent | Result | Expected score | Surprise | First clock | Event | Expected flags |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 1500, 1400 | A | 0 | 0.6401 | -0.6401 | 180 | game | session 1; REMATCH |
| 2 | 400 | 1488, 1412 | A | 1 | 0.6077 | 0.3923 | 180 | game | session 1; plays on |
| 3 | 900 | 1499, 1700 | B | 0 | 0.2392 | -0.2392 | 180 | game | session 1; STOP (next start is 1,860 s later) |
| 4 | 2,760 | 1495, 1300 | C | 1 | 0.7545 | 0.2455 | 90 | tournament | session 2; plays on; BERSERK |
| 5 | 3,100 | 1498, 1500 | D | 0.5 | 0.4971 | 0.0029 | 180 | tournament | session 2; censored |

Add to the builder's fixture: a record with "Time forfeit", one with an unknown Termination (kept as found), and one malformed record (counted, never dropped silently).

**What the public files give, and the one inference.**
- The files mark arena games in the Event tag with a tournament address, and carry clock comments from April 2017 ([Lichess database](https://database.lichess.org/); read by a helper).
- Berserking halves the player's clock, cancels any increment, and makes a win worth one more tournament point; it is not offered when the initial time is zero ([Lichess tournament help](https://lichess.org/tournament/help); read by a helper).
- **BERSERK** is the analyst's inference and is unverified until the check below: a tournament game in a zero-increment control where her first clock is between 0.45 and 0.55 of the initial time.
- **Instrument check SG1.v.** File the histogram of first clock over initial time in 20 bins, for tournament and other games separately. The flag is admitted only if under 0.2% of non-tournament games fall in the berserk band and tournament games show two modes, near 0.5 and near 1. If it fails, CH10 holds and nothing else changes.
- Termination values confirmed in the public documentation are "Normal" and "Time forfeit". Record any others as found.

**Ceiling.** 40,000 beyond CH7's own envelope.

#### The forecast, used by CH8 to CH12

Players whose salted key begins with hex digit 0, 1 or 2 are the calibration players. On their games, per time-control class, fit an ordered model of loss, draw and win on the pregame rating gap in hundreds and colour. Expected score E is P(win) plus half P(draw). On everyone else, file the calibration table (deciles of E against mean score). If any decile is off by more than 0.03, use the decile-calibrated E. Cards use only non-calibration players. *Surprise* is the score minus E.

Cards CH8 to CH12 reuse CH7's within-player fit and its 2,000 whole-player resamples. They do not use its simulated-history null; each states its own bar.

#### CH6 and CH7 (carried)

Both read SG1's rows. CH6 is specified in the 7 November packet and CH7 in the back-half packet and `CH7_BACK_HALF.md`. They are the first consumers, and their review is SG1's review.

#### CH8. A loss below forecast (handoff test 1)

- **Why.** Round 15's proposal, awaiting the curator's ruling: SHAME's trigger is a drop below forecast. The handoff: "After a loss to a lower-rated player, compare what follows (quitting, shorter sessions, safer play) with what follows a loss to a higher-rated one. If the unexpected loss gives more yielding: SHAME's trigger is a drop below forecast. If the two look alike: any drop will do, and the trigger cell reverts." The table "Which channel fires" adds a third reading: a sudden drop that looks recoverable by pushing is RAGE's row.
- **Rows.** SG1 rows that are blitz, lost, not provisional, not censored.
- **Model.** A linear probability model of STOP with player fixed effects; E in three bins (at most 0.35; between; at least 0.65); games so far in the session; form so far (the sum of surprise over her earlier games in the session); losing streak; hour of day as sine and cosine; SG1's tournament flag.
- **One primary.** Adjusted STOP after a loss as clear favourite (E at least 0.65) minus after a loss as clear underdog (E at most 0.35). Bar: one tenth of the overall probability of stopping after a loss. Player-cluster interval.
  - Above the bar: more yielding after the loss below forecast.
  - Inside the band: any loss will do.
  - Below minus the bar: the unexpected loss is met by playing on, which is the RAGE row and Card and Dahl's direction.
- **Secondary.**
  - *Three acts.* STOP, REMATCH and playing on against someone else, by bin of E, in non-tournament games.
  - *The curve.* STOP by decile of surprise over all results. Round 14 asked whether leaving is U-shaped in surprise; the win side is where the published personal-best effect sits.
  - *Points or surprise.* Among losses, STOP on E and on rating points lost together. The points lost per unit of surprise differ across players, so the two can part. If STOP follows points at equal E, the size of the drop matters; if it follows E at equal points, the forecast does.
  - *What is left of the session.* Games played after the loss before the session ends.
- **Falsification row.** The seconds between her previous game and this one, regressed on this game's E bin with the same controls, among the same lost games. That gap was fixed before she was paired, so it should not differ across bins. If it does, the kind of session differs across bins and the primary inherits that.
- **Rival.** Her state. A favourite who loses may be tired or already tilted and would stop anyway. Form so far, streak, games so far and hour are the controls, and CH9 is the sharper answer. This card stays descriptive.
- **By construction.** Losses as favourite cost more points. E bins differ in who the opponent was.
- **Fixture.** Planted: 400 synthetic players, STOP probability 0.20 after underdog losses and 0.26 after favourite losses; the primary must return 0.06 within its interval, and 0 when the planted gap is removed.
- **Case.** At least 3,000 players with 5 or more sessions and 10 or more losses. Fallback: blitz pooled with rapid.
- **Tags.** `H15-T1`. Activation: SHAME, seen as competent (by analogy only), drop below forecast, observed act.
- **Ceiling.** 60,000.

#### CH9. Whether it can be contested (the table's second column)

- **Why.** In "Which channel fires", the same drop goes to RAGE when "I can get it back by pushing" and to SHAME when "it can't be contested". Two kinds of loss differ on that and are visible without an engine.
- **Rows.** Lost, non-tournament, not provisional, using SG1's Termination and tournament fields.
  - FLAGGED-AHEAD: Termination is "Time forfeit" and her final material balance is at least +2. She was ahead and ran out of time.
  - OUTPLAYED: she was checkmated, or Termination is "Normal" with a final balance of at most -3.
  - Everything else is counted and left out.
- **Outcome.** QUICK: her next game starts within 120 seconds of this game's estimated end (start plus `duration_est`).
- **One primary.** Adjusted QUICK after FLAGGED-AHEAD minus after OUTPLAYED, with E, the CH8 controls and player fixed effects. Bar 0.03. The table predicts above the bar.
- **Secondary.** Among QUICK next games, the share that are rematches, by kind of loss. STOP by kind of loss. Both again for losses as clear favourite.
- **Rival.** A player who was ahead was playing well, and that alone predicts another game. It does not predict another game against the same opponent, which is why the rematch share is reported. A rematch also needs the winner's consent, which pulls the share toward zero for both kinds.
- **By construction.** The two kinds differ in game length and clock state.
- **Fixture.** Four synthetic losses, one of each kind plus two that must be excluded (a time forfeit while behind; a resignation at balance 0).
- **Tags.** `H15-T1`. Activation: RAGE against SHAME by what could be done.
- **Ceiling.** 40,000.

#### CH10. The claim (handoff test 2)

- **Why.** Round 15's proposal, awaiting ruling: pride is the claim rising; the claim is raised by wins and lowered by a loss below forecast, on different machinery. The handoff: "Do wins raise who a player takes on next, and unexpected losses lower it, on different time courses? If the two decay differently: one dial with two update paths, as in the animal work. If they mirror each other: pride may be SHAME's other output after all." Pairing in these games is mostly not her choice, so "who she takes on" is replaced by something that is: a berserk is a public, costly bet that she is the stronger player.
- **Rows.** Tournament games in zero-increment controls, after the berserk check SG1.v passes.
- **Model.** A linear probability model of BERSERK with player fixed effects; the previous game's result in the same tournament; this opponent's rating gap per 100 points; her own previous berserk; streak state (0, 1, or 2 and more wins in a row before this game); game number in the tournament; minutes since her first game in it.
- **One primary.** BERSERK after a win minus after a loss. Bar: one tenth of the base berserk rate.
- **Secondary.**
  - *By surprise.* After a win as underdog against a win as favourite; after a loss as favourite against a loss as underdog.
  - *Time courses.* The effect of a result at lags 1 to 4, for wins and for losses. Report the ratio of lag 3 to lag 1 for each and their difference with its interval. This is the handoff's fork.
  - *A failed claim.* After a loss while berserking against a loss without. Round 14's upper side of Standing: "Too high is more than I can back up."
  - *The claim follows the forecast.* The slope of BERSERK on the rating gap.
- **Rival.** Arena scoring. As the analyst recalls the rules (verify against the help page at intake): two wins in a row start a streak that doubles points, which changes what the extra berserk point is worth. The streak state is in the model for that reason. A player who is behind near the end has reason to berserk; the files have no standings, and minutes since her first game is the only stand-in.
- **By construction.** A berserked loss is shorter. A berserk cannot occur outside a tournament.
- **Fixture.** Planted: berserk rate 0.10 after losses and 0.14 after wins in 300 synthetic players; decay planted at 0.5 per lag for wins and 0.8 for losses; the card must return both.
- **Tags.** `H15-T2`.
- **Ceiling.** 60,000.

#### CH11. Habit and departure after a loud result

- **Why.** The curator: "If any of the emotions get too loud does it turn off play?" The thread's check found it mostly true in animals, and that stress "[led to habit performance](https://doi.org/10.1523/jneurosci.0979-09.2009)". A first move is a choice made thousands of times by the same person, so her habit can be estimated and each choice scored as a departure from it. This is the engine's own measure, on moves in place of words.
- **Context.** As White: her first move. As Black: her reply, given the opponent's first move. Per time-control class.
- **Measures**, each from her earlier games in the window only:
  - DEPARTURE: minus the log of her smoothed habit probability for the move she chose (add one half per cell, over the moves she has played plus one cell for any other). Needs 20 earlier games in the context.
  - NOVEL: a move she has never played in that context, after 30 earlier games.
  - SHIFT: a different move from her last game in that context.
- **One primary.** DEPARTURE in her next game after a loss as clear favourite, minus after a win as clear favourite; player fixed effects; games so far, hour, the next opponent's gap and the count of earlier games in the context as controls. Bar: one twentieth of mean DEPARTURE. If a loud drop shuts PLAY and hands over to routine, the primary is below minus the bar.
- **Secondary.** NOVEL and SHIFT on the same terms. Reinforcement predicts more SHIFT after a loss. SHIFT up with NOVEL down is switching inside the familiar set. Also: the same three measures in a calm stretch (three games in a row with surprise under 0.35 in size).
- **By construction.** Smoothing makes rare moves large. The habit estimate sharpens with games played, hence the control.
- **Case.** At least 2,000 players with 20 earlier games in a context and at least 5 losses as clear favourite. Fallback: pool time-control classes with a class term.
- **Fixture.** A synthetic player with habit (0.7, 0.2, 0.1) over three moves and 40 earlier games: with counts 28, 8 and 4 and a fourth empty cell, the smoothed probabilities are 28.5/42, 8.5/42, 4.5/42 and 0.5/42, so DEPARTURE must be 0.388, 1.598 and 2.234 nats for the three moves and 4.431 for a move she has never played.
- **Tags.** `H14-play-trigger`. Activation: PLAY, any set point, a loud drop, observed choice.
- **Ceiling.** 60,000.

#### CH12. Level and gain as two stable things, or one (handoff test 11 without trait scales)

- **Why.** The curator has ruled resolution one dial: "how hard to push should just echo how narrow the band is once accounted for context". The thread kept a caution: level and reactivity have each been found stable in people. Test 11 is parked for want of trait scales. Chess gives the same question in behaviour.
- **Split.** Games before 16 May 2017 UTC and after. Players with at least 20 sessions and 30 losses in each half.
- **Indices per player per half.** LEVEL: probability of stopping after a win as favourite. GAIN: probability of stopping after a loss minus after a win. FORECAST-GAIN: the slope of stopping after a loss on E.
- **One primary.** The stability of GAIN across halves, corrected for within-half reliability from odd and even sessions, after TR1's gate that true variance is above zero. TR1's bands: under 0.2, no stable difference; over 0.5, stable.
- **Secondary.** The same for LEVEL and FORECAST-GAIN. The corrected correlation of LEVEL with GAIN across players. Two stable indices that barely correlate would be two dials as far as this record can see; a stable LEVEL with an unstable GAIN would be one.
- **Case.** At least 1,000 players meeting the per-half minimum. Fallback: 10 sessions and 15 losses per half, labelled low reliability. Under 300 players: descriptive only.
- **Fixture.** TR1's constructed controls, re-pointed at these three indices.
- **Tags.** `H15-T11`, `H12-T7`.
- **Ceiling.** 40,000.

### 3B. Appraisal reports (family IN, Crowd-enVENT)

#### IN9. Shame and guilt: one thing or two (handoff test 5, in self-reports)

- **Why.** The curator: "I think guilt and shame are the same thing." Round 15's eighth disagreement says they differ by who is sending, by what they make people do, and by tissue, and proposes guilt as CARE's alarm and shame as the alarm of the two seen variables.
- **Rows.** The shame and guilt prompts. As the analyst recalls the corpus paper (unverified), these two prompts have about half the texts of the others, near 275 each; report the counts and hold if either is under 200.
- **One primary.** The cross-validated area under the curve of a ridge logistic model telling the two prompts apart from the 21 appraisal items and intensity, with folds by writer. Bar 0.60. Writer-cluster interval.
  - Interval above 0.60: the two prompts draw different appraisal profiles.
  - Interval inside 0.45 to 0.55: the same thing, at the level of appraisals.
  - At about 275 texts each the standard error is near 0.024, so the card sees 0.067 and supports at about 0.67.
- **Directed secondaries.**
  - *Forecast.* `suddenness` and `predict_event`, shame minus guilt. The thread's proposal predicts shame is the more sudden and the less predicted.
  - *Who and what.* `self_responsblt`, `standards`, `social_norms`, `other_control`.
  - *Cues in the text.* Three frozen word lists, counted per text and never exported as text. VICTIM (for example: hurt, upset her, upset him, let down, lied to, broke, forgot). AUDIENCE (in front of, everyone, people saw, caught, embarrassed). SENDER, in two halves: ANGRY-AT-ME (angry at me, mad at me, yelled at me, furious with me) and LAUGHED-AT (laughed at me, made fun of me, mocked, looked down on, sneered). Report the odds of the shame label against the guilt label by cue. Round 15 cites the pairing: "[angry expressions led to greater guilt and less shame than did disgusted expressions](https://doi.org/10.1177/0956797610392925)". A cue family that appears in under 5% of the two prompts' texts is reported as unsupported.
- **By construction.** Writers were asked for an event that fit the word. The model separates prompts, which is how people use the two words, and not two feelings.
- **Fixture.** Planted: two synthetic prompts of 2,000 texts each, differing by 0.5 SD on three independent items, must give an area near 0.73 (0.64 if only one item differs); identical prompts must give 0.50 within the interval.
- **Tags.** `H15-T5`. Activation: SHAME, CARE.
- **Ceiling.** 20,000.

#### IN11. Strength follows the jump; duration follows what can't be fixed

- **Why.** Round 14: "a set point pushes according to how far off it is. A trigger, on this table, answers how fast it's moving", and "slow drift should never fire a channel. It should only raise the bill." Round 15's proposal, awaiting ruling: arousal is the size of the latest jump and stress is the level. In the reports this predicts a crossover: how sudden an event was should tell how strong the feeling was more than how long it lasted, and having no remedy should tell how long more than how strong.
- **Rows.** The six negative prompts (anger, disgust, fear, guilt, sadness, shame). Needs R7's duration columns; without them the card is unsupported.
- **Indices,** standardised within prompt. JUMP: `suddenness` minus `predict_event`. NO-REMEDY: `chance_control` minus `self_control` minus `accept_conseq`.
- **Model.** Two fits with prompt intercepts: intensity, and the emotion's duration, each on JUMP, NO-REMEDY, `unpleasantness`, the event's duration, and a response-style control rebuilt for this card from the six of its nine items that are in neither index (`familiarity`, `goal_relevance`, `chance_responsblt`, `self_responsblt`, `attention`, `effort`). The standing control includes `suddenness`, `predict_event` and `chance_control`, which would put the indices on both sides.
- **One primary.** (JUMP on intensity minus JUMP on duration) plus (NO-REMEDY on duration minus NO-REMEDY on intensity). Bar 0.10. Writer-cluster interval.
- **By construction.** A long event allows a long emotion; the event's duration is in both fits.
- **Fixture.** Planted crossover of 0.3 in 2,000 synthetic rows; and a planted zero.
- **Tags.** `H14-rate-level`, `H15-Q2`.
- **Ceiling.** 20,000.

#### IN12. One band or several strengths (toward handoff test 11)

- **Why.** Round 15, on what favours the curator's reading of traits over the Panksepp group's: "FEAR, SADNESS and ANGER all go with Neuroticism. On their account three separate systems happen to rise together. On yours there's one cause: a narrow band on the bill fires all three." The Big Five mapping is the thread's proposal, awaiting ruling.
- **Rows.** All prompts. Needs R7's personality items; the card uses only the two that measure emotional stability, reversed into one score N. If the archive's inventory is not a Big Five short form, the card is unsupported.
- **One primary.** The pooled slope of intensity (standardised within prompt) on N across the six negative prompts, with confidence and the response-style control. Bar 0.10.
- **Secondary.**
  - The spread of the six prompt slopes around the pooled one, with its interval. A band predicts a small spread; separate strengths predict a spread.
  - The same slope for joy and pride. A general habit of reporting strong feelings raises these too; a band on Stress should not.
  - If at least 300 writers gave two or more negative prompts: the within-writer correlation of intensity across different negative prompts, minus the same correlation between a negative and a positive prompt.
- **Standing.** Adult self-report: lowercase evidence. No demographic column is read.
- **Fixture.** Planted common slope 0.2 across six prompts with zero spread; and planted slopes of 0.4, 0.4, 0, 0, 0, 0 with the pooled value 0.13.
- **Tags.** `H15-T11`, `DISAGREE-6`.
- **Ceiling.** 20,000.

### 3C. Meetings (family LA)

**LA3 and LA4 (carried).** Built and fixtured on 11 November. They are first in the review order.

#### LA5. Laughed at, and not joining

- **Why.** The curator in Round 14: mockery works by "pointing out someone else's problematic status actions and then trying to summon a bunch of other people to laugh with you". The thread: "mockery is PLAY's signal carrying SHAME's trigger", and the handoff's test: the target doesn't join, and the target's share of talk drops.
- **Rows.** AMI first, ICSI second, from LA's prepared laugh onsets and dialogue acts. LA's pipeline already carries a `laughed_after` field; reuse its timing convention where it matches the definition below and record any difference.
  - A LAUGHED-AFTER event: an act of at least 3 words by X, followed within 2 seconds of its end by laugh onsets from at least two other people.
  - JOINED: X has a laugh onset between 1 second before the first of those and 3 seconds after.
- **Outcome.** X's share of all words in the 60 seconds after the last of those onsets, minus her share in the 60 seconds before the act began.
- **One primary.** The outcome for not joined minus joined, with speaker and meeting fixed effects, minute of the meeting, act length and number of laughers. Bar 0.02. The prediction is below minus the bar.
- **Rival.** A speaker who doesn't laugh may be holding the floor, which pushes her share up and works against the prediction. Laughter at a remark and laughter at a person can't be told apart by timing. Both go in the record.
- **Secondary.** By AMI's scenario role, only if the role is already in LA's qualified metadata.
- **Case.** At least 300 events in each group, else a pooled description.
- **Fixture.** A synthetic meeting of four speakers with two planted events, one joined and one not, and hand-computed shares.
- **Tags.** `H14-mockery`. Activation: SHAME carried on PLAY's signal.
- **Ceiling.** 30,000.

### 3D. The phone game (family MD)

**TR1 (carried).** Constructed checks passed on the 11th. Review, then run.

#### RR3. Slope against level (handoff test 6)

- **Why.** Round 15's first disagreement: pleasure is the slope of free energy and not its level. The handoff: "Does a player's next choice follow the change in their deficit more than its size? If slope: Disagreement 1 has support in the program's own data. If level: his sentence does."
- **Rows.** RR1's fixed cohort (completed actual attempts 1, 2 and 3).
- **Model.** RR1's fit as filed in `RR1_BACK_HALF.md`, for its play-start reference: the same outcome and the same eight covariates, including the two slopes on distance below and above the play's starting score, plus one new covariate, RECENT: the mean of outcome minus the chosen option's expected value over the previous three trials. RECENT and the two distance terms are standardised. Adding a covariate changes the fitted panel, and RR1's contract admits no new column, so this is a new small card with its own fixture and replay. It reuses RR1's roster and its 2,000 whole-person draws.
- **One primary.** The size of RECENT's coefficient minus the larger of the two distance slopes' sizes. Bar 0.05.
- **Fixture.** Planted: synthetic choices generated with a RECENT weight of 0.3 and distance weights of 0, and the reverse. The primary must return the planted sign and, within its interval, the planted size.
- **Limits.** A choice is not a feeling. On this task's own mood ratings the published result is that happiness is "[explained not by current task earnings, but by the combined influence of recent reward expectations and prediction errors](https://doi.org/10.1073/pnas.1407535111)". The mood cards stay held under their control requirement, so RR3 stays with choices. Wins raise both RECENT and distance from the start; file their correlation.
- **Tags.** `H15-T6`.
- **Ceiling.** 10,000 from MD.

### 3E. Two new public text sources (builders start these on day one)

#### RF1. Three reads in election comments (handoff test 3)

- **Why.** Round 15's proposal, awaiting ruling: liked, respected and trusted are three separate reads, with "kind" meaning character. The handoff: "Fit liked, respected and trusted as three separate reads and compare with two... If three wins: adopt the three reads. If not: fold seen as kind into Belonging." Requests for adminship are a rare record of a community stating, in words, how it sees a person, and then voting.
- **Source.** The Stanford file of every vote from 2003 to May 2013: 198,275 votes among 11,381 users, each with voter, candidate, vote, outcome, year, time and the comment's text ([SNAP](https://snap.stanford.edu/data/wiki-RfA.html)). 14 MB. File the licence note from its licence page at intake.
- **Markers,** frozen in the design commit; these are the starting lists.
  - RESPECT, for and against: experienced, competent, knowledgeable, capable, skilled, knows policy, good contributions; inexperienced, not enough experience, too few edits, lack of experience, clueless, doesn't understand policy.
  - TRUST, for and against: trust, trustworthy, honest, integrity, fair, sound judgment, good judgment, level-headed, responsible, mature; don't trust, untrustworthy, dishonest, poor judgment, immature, abuse the tools, power hungry, deceptive.
  - LIKING, for and against: friendly, nice, pleasant, likeable, good guy, pleasure to work with, cheerful; rude, abrasive, hostile, unpleasant, unfriendly, uncivil, arrogant.
- **Instrument check.** Each family must appear in at least 3% of comments. For each family a builder reads 100 random hits in a private file and the family is admitted at 80 or more correct; the owner reviews the tally and not the hits.
- **Unit.** An election with at least 20 comments. Marker rates come from the first third of its votes by time. The outcome is the support share among the remaining two thirds.
- **Models,** each a binomial model of the later votes (support against oppose, neutral left out) with year effects and the early support share: TWO-A (respect; trust plus liking). TWO-B (respect plus trust; liking). TWO-C (respect plus liking; trust). THREE (each alone).
- **One primary.** THREE's out-of-fold gain in binomial log loss per later vote, averaged over elections, over the best of the three two-read models; folds by candidate. Bar 0.002 nats. Candidate-cluster interval.
- **Secondary.** Which "against" family costs the most support per mention. Round 15: character "[is usually more important than warmth in impression formation](https://doi.org/10.1037/a0034726)", so TRUST should cost the most.
- **By construction.** Early and late voters see the same candidate, which is why the early tally is in every model. Adminship is an office of trust, so a lead for TRUST here may not travel. Who defers to whom is not in this source.
- **Fixture.** Twelve synthetic comments with hand counts; a planted three-read world where TWO-A must lose by a stated margin.
- **Tags.** `H15-T3`.
- **Ceiling.** 40,000.

#### CP1. Warmth is matched, standing is complemented (handoff test 4)

- **Why.** Round 15 cites the rule from pairs rated moment by moment: "[partners' affiliation behaviors were very strongly in phase, whereas their dominance behaviors were equally strongly out of phase](https://doi.org/10.1037/a0016232)". The handoff: "Within reply pairs, does politeness pull politeness and assertion pull deference? If yes: the engine can read relative standing from a pair. If no: complementarity is a face-to-face effect only."
- **Source.** ConvoKit's Wikipedia talk-pages corpus: 38,462 speakers, 391,294 utterances, 125,292 conversations, with `reply_to`, a timestamp, `is-admin` and `edit-count`; CC BY-SA 4.0 ([documentation](https://convokit.cornell.edu/documentation/wiki.html)).
- **Markers per 100 tokens,** frozen; starting lists:
  - WARMTH: thanks, thank you, appreciate, grateful, hi, hello, welcome, glad, great, nice, good work, good point, sorry, apologies.
  - DEFERENCE: perhaps, maybe, I think, I wonder, might, could you, would you, would it be, please, if you don't mind, correct me.
  - ASSERTION: a sentence that opens with a bare command from a fixed list (stop, read, see, look, do, don't, remove, fix, add, check, leave, quit, use, provide, cite, explain); you need to, you should, you must, you have to; obviously, clearly, the fact is, you are wrong.
- **Instrument check.** Each marker family must appear in at least 3% of utterances. A builder reads 100 random hits per family, and a family is admitted at 80 or more correct.
- **Rows.** A reply by B to a parent by A, with A not B and at least 10 tokens each. Quoted lines are stripped first.
- **Null.** Shuffle replies among the pairs of one conversation, 200 times. Every estimate is the observed standardised slope minus the shuffled mean. That removes what a page's topic and tone put in.
- **One primary.** (Parent's ASSERTION on reply's DEFERENCE) minus (parent's ASSERTION on reply's ASSERTION). Bar 0.02. Complementarity predicts above the bar.
- **Secondary.** WARMTH on WARMTH, which should be positive. The primary split by who is the admin: the pairs table has anger from the stronger side drawing fear and from the weaker side drawing anger back. The gap in `edit-count` as a graded difference.
- **Rival.** Accommodation: people converge in style, which predicts ASSERTION on ASSERTION above zero. The corpus was built for a study of exactly that on function words.
- **If it supports.** Export EX6 for ToMpathy: the pair table with marker counts and admin flags, no text.
- **Fixture.** Ten synthetic pairs with hand counts; a planted complementary world and a planted convergent one.
- **Tags.** `H15-T4`.
- **Ceiling.** 60,000.

#### SV1. A public drop and what follows (reserve; build only if a builder is free)

On the five Stack Exchange archives already verified, add the Votes and Comments tables. For each answer, the day of its first downvote; then what its author does in the next three days: edits the answer (repair), comments under it (contest), or posts nothing anywhere (withdraw), against her own answers that drew no downvote. Split by how unusual a downvote is for her. The one published result near it, on four news-comment sites, is that negative feedback made authors post more and worse ([Cheng et al. 2014](https://arxiv.org/abs/1405.1429), abstract), which is the opposite of withdrawal. Votes carry a day and no voter. Ceiling 60,000 under SV.

### 3F. The ISEAR block (conditional on R9)

If the source is present, verify its codebook at intake and map items by their wording. A card whose item is missing is unsupported. As the analyst recalls the questionnaire (unverified until intake): seven emotions including shame and guilt, about 7,600 reports, with items for how expected the event was, how long the feeling lasted, what the person judged they could do about it, and how they moved toward, away from or against others.

- **IN8,** as specified on 11 November.
- **IS2. What could be done picks the channel.** The coping item against the emotion. The table "Which channel fires" predicts anger with "could influence it", fear with "could escape", sadness with "powerless", shame with "acted as if nothing had happened". Primary: the mean log-odds of those four cells against independence. Bar 0.2. Respondent-cluster interval. This is the control question the back-half packet left waiting on a source, on a sample the theory's table was not built from.
- **IS3. Shame and guilt by the next move.** The movement item: guilt toward, shame away. Primary: the difference in the share moving away. Bar 0.05.
- **IS4. FEAR by time course.** Round 14: split fear reports by how long the feeling lasted before scoring anything, since "prompted fear reports mix the alarm with worry". Short against long, on the coping item. This is a first look at this sample and must be registered before the item tables are opened.

### 3G. Exports to ToMpathy (local disk only, amendment T's terms)

- **EX4 (carried).**
- **EX5. Questions and the answer the asker chose.** From the five verified Stack Exchange archives' Posts table: 2,000 questions, 400 per site, each with 3 to 8 answers, an accepted answer that is not the asker's own, and a body of 80 to 600 words. Rank rows by SHA-256 of `EX5|20261112|site|source_row` and keep the lowest. Fields: site, public question id, title and body as text with code blocks replaced by a marker and their length; for each answer its public id, body text, final score, order of posting and the accepted flag. No user fields. README with the CC BY-SA attribution addresses. Copy to ToMpathy's `.local/bench/EX5/` by EV4's procedure. Ceiling 20,000 from EX.
- **EX6.** Only if CP1 supports.

### 3H. Carried, in the background

RR2. The R1 reader work and GO1's language-model secondary. Chess scoring under amendment V, then CH2 to CH5 as scores arrive.

## 4. Review order and the two days

Three builders work in parallel from the first wake. Builder A: SG1, then CH8 to CH12. Builder B: RF1 and CP1 intakes, markers and instrument checks. Builder C: IN9's cue counts, IN11, IN12, LA5, RR3, EX5.

| Step | Review | Why here |
|---|---|---|
| 1 | LA3, LA4 | Built and fixtured two days ago |
| 2 | SG1 (the extended CH7 wrapper) with CH6 and CH7 | One traversal; the fixture above gives expected rows that no adapter produced |
| 3 | CH8, CH12 | Table cards on SG1 |
| 4 | IN9 (items first, cues second) | A configuration of the IN handler |
| 5 | TR1, RR3 | TR1's checks passed; RR3 reuses RR1's roster, fit and replay |
| 6 | CH9; CH10 after SG1.v; CH11 | Table cards on SG1 |
| 7 | LA5 | Rides LA's prepared tables |
| 8 | IN11, IN12 | After R7's columns |
| 9 | RF1, CP1 | As their intakes and instrument checks qualify |
| 10 | EX5, EX4; block 3F if the source is there | |

Steps 1 to 6 hold fourteen reviews. At the landing rate of 11 and 12 November (seven results, then three) that is two to five days, and two only if table cards review as fast as IN5 to IN7 did (three within about an hour of the back-half packet arriving). The list is long on purpose: the curator asked for two days with margin, and a queue that waits on review should never run out of work that is ready to review. Anything not landed by the cutoff is carried by name into the final curator packet as built, reviewed or neither.

## 5. When review is the bottleneck

Idle slots and idle builders take these, in order. None needs a new admission beyond amendment U.

1. **Chess scoring shards** (amendment V).
2. **The activation log** (amendment X).
3. **Texture on landed chess cards:** bullet and rapid; a 15 and a 60 minute session gap; rating bands; tournament against other games; the session ended by clock time in place of start gaps.
4. **Follow-ons allowed without a new packet.**
   - CH8 above the bar: rerun within stoppers and non-stoppers from CH12's GAIN, to see whether the forecast effect lives in one type.
   - CH8 inside the band: pool blitz with rapid once and report the pooled sensitivity.
   - CH10's time courses differ: add lags 5 to 8.
   - IN9 above the bar: report which five items carry it, and rerun on the validation readers' appraisals of the same texts.
   - CP1 above the bar: the same estimate within conversations that later contain a personal attack, if ConvoKit's labelled subset is at hand.
   - RF1 above the bar: by year, 2003 to 2007 against 2008 to 2013.
5. **RR2.**

## 6. The return

Keep `THEORY_RETURN.md` rolling. Add a Round 15 table with one row per handoff test, in the back-half table's columns:

| Handoff test | Card |
|---|---|
| 1. Unexpected against expected loss | CH8, CH9 |
| 2. Wins and losses moving the claim | CH10 |
| 3. Three reads against two | RF1 (Ghost B3 in constructed worlds) |
| 4. Warmth matched, standing complemented | CP1 |
| 5. Guilt against shame by sender | IN9's cue rows; IS3 if the source is there; SV1 if built |
| 6. Slope against level | RR3 |
| 7 to 10 | Ghost V29 |
| 11. Set point against channel strength | CH12, IN12, TR1 |
| 12. The kith index | no data here has closeness ratings; say so |
| Round 14, carried | CH11 (PLAY's trigger), LA5 (mockery), IN11 (rate against level), IS4 (FEAR by time course), IS2 (control picks the channel), LA3, LA4, CH7 |

"Pending" means uncomputed. A card that could not run says which gate stopped it.

## 7. Limits

- **A rating is not standing in a room.** CH8 to CH12 can show how people act around a public number with a forecast. They cannot show that the act is SHAME, RAGE or pride. The record uses those words only in the "why" line.
- **CH8 is confounded by state** in the same direction as its prediction. CH9's rematch share and CH8's falsification row are the answers on offer, and neither closes it.
- **Word lists measure words.** RF1, CP1 and IN9's cues stand or fall with their instrument checks, and a list that fails is reported as failed.
- **Prompted reports are recollections fitted to a word.** IN9, IN11 and IN12 inherit that.
- **Nothing here tests the kith index, LUST, or the hub.** The first has no data, the second has no card this week, and the third is in constructed worlds this week.
