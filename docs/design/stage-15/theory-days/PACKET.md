# Sounding Line, Stage 15 theory days: testing the curator's channel theory on public data

*Spec sheet for the Sounding Line agent, dated 6 November 2026. Handing it over approves everything in it. CPU only; no paid calls. These theory days are new science cards, separate from the 6 November Theory Day record check (OPS-S15-W4-THEORY-DAY-RECORD-CHECK-20261106).*

The curator's theory treats Panksepp's emotion systems as pre-solved functions whose triggers are slopes along set points. These cards test the parts of that theory that public data can reach, each against a named rival. Every card states in advance three outcomes: what supports the claim, what counts against it, and what is inconclusive. The claims are labelled as in the curator's theory state of 4 November:
- **C2:** graded strength and word scales.
- **C3:** triggers are slopes, not levels, attenuated by uncertainty.
- **C4:** security is defended from below and spent from above.
- **C10:** DISGUST shuts intake and stops modelling the other.
- **C5** (backlog): identity is terminal; nothing trades for it.
- **C6** (backlog): effect is effort times power.

## 0. Window, rules and resources

- **Window.**
  - Opens at handoff. No new starts 36 hours after handoff; drain at 48 hours.
  - If handed over before week 4's freeze (Sunday 8 November, 20:00 PST), these cards have first claim on idle counted slots, and week 4's queue keeps the rest. This window outlives week 4's freeze and drain: week 4's start freeze doesn't bind these cards, and `transition_only` stays cleared until this window drains.
  - If handed over after week 4's freeze, week 4's start freeze doesn't bind these cards either: clear `transition_only` at handoff if it is set, and if week 4's drain (22:00 PST) falls inside this window, leave it cleared.
  - Restore `transition_only: true` at this window's drain.
- **Paths.**
  - Designs and this packet: `docs/design/stage-15/theory-days/` (this file as `PACKET.md`).
  - Results: `results/phase_2_4_stage_15/THEORY_DAYS/`.
  - Ledger rows carry the prefix `S15-TD`.
- **Rules in force.**
  - Week 4's rules apply where relevant: amendments E to H, with G's texture lane running only after the backlog and inside the 15 CPU-hour budget; for TD7, section 0.5's CoAuthor defaults (canonical choices, writer-cluster intervals, the pinned encoder), V4's examined-dismissal definition (section 2.4) and S4(b)'s hover rule (section 2.2).
  - Each card's design note, with its primary, practical bar and three-way outcome rule, is committed before any outcome is computed.
  - Amendment F's design pre-mortem applies to every card: state the case, the check, and anything true by construction. A card whose data can't produce its case is recorded "design cannot test", with the counts, and the agent moves on.
- **Data handling.**
  - Every new source goes through `DATA_INTAKE.md`. Raw files stay in the private raw area.
  - Never commit raw text, rater, author or participant identifiers, or lexicon entries; commit hashes and aggregates only.
  - GoEmotions' author field is never read.
- **Compute.**
  - Gear 2, CPU only. The card ceilings below total 12.6 CPU-hours (6.6 for TD1 to TD7, 6 for the backlog); with the intakes, the window's budget is 15.
  - A card whose probe projects past twice its ceiling takes amendment E's sample route.
- **Seeds.** 20261106 for every new draw, split and bootstrap, including amendment E samples drawn here: whole participants for TD1 to TD3 (floor 10,000) and whole writers for TD7 (floor 20). TD4 to TD6 have no sample route. TD7's existing frozen 25-writer sample keeps its seed, 20261102.

## 1. Intakes, first and in this order

A source whose licence forbids research use makes the cards that need it "unsupported at source".

**I1. Rutledge's Great Brain Experiment happiness data.**
- **Source:** Dryad, https://doi.org/10.5061/dryad.prr4xgxkk (Dryad publishes data under CC0).
- **Contents:** 47,067 participants, 91,058 plays, about 2.7 million choices and 1.1 million happiness ratings, as MATLAB structures with a README and a script.
- **Intake steps:**
  - Download it and record its hash.
  - From the README and the script, record the per-trial fields: trial type (gain, loss, mixed); the certain amount; the gamble's two outcomes; the choice; the outcome; the running total; each happiness rating and the trial it follows; play and participant ids; time, if present.
  - Record whether each play starts at a fixed total.
- **Case check:** at least 10,000 participants whose first play has all 12 ratings.
- **If it fails:** a missing field makes the cards that need it "unsupported at source".

**I2. GoEmotions, raw configuration.**
- **Source:** Hugging Face, `google-research-datasets/go_emotions`, config `raw` (Apache-2.0). It has 211,225 rows, one per comment and rater, over 58,011 comments and 82 raters. The fields are the text, `id` (the comment, which groups its raters), `author`, `subreddit`, `link_id`, `parent_id`, `created_utc`, `rater_id`, `example_very_unclear`, and 28 label columns (27 emotions plus neutral). Each comment had 3 raters, plus 2 more when the first 3 shared no label (Demszky et al. 2020); raters could pick several labels.
- **Intake steps:** drop rows flagged `example_very_unclear`.

**I3. NRC Emotion Intensity Lexicon and NRC VAD Lexicon.**
- **Source:** https://saifmohammad.com/WebPages/AffectIntensity.htm and https://saifmohammad.com/WebPages/nrc-vad.html.
- **Licence:** free for non-commercial research; no redistribution. The files stay out of git.

## 2. Cards

### TD1. Do levels add feeling beyond momentum? (C3)

- **Claim tested.** Momentary feeling follows recent changes, not the level reached.
- **Rivals.**
  1. Level matters.
  2. Time on task matters at zero change (Jangraw et al. 2023's mood drift).
  3. Momentum only (C3).
- **Model.**
  - Rutledge et al. 2014's momentary happiness model. Happiness is a weighted sum of discounted past certain rewards, gambles' expected values, and reward prediction errors, sharing one forgetting factor.
  - First reproduce a known answer: Rutledge et al. 2014's smartphone result, fitted per participant in 92 subsets of 200 consecutive participants, that certain-reward, expected-value and prediction-error weights were positive in all 92 subsets and expected-value weights below prediction-error weights in all but one. If the README documents the bundled MATLAB script's own outputs, match those too. Record whether each matched, and the tolerances.
- **Arms.**
  - **M0:** the reproduced model plus time on task (trial index).
  - **M1:** M0 plus the level, meaning points accumulated in the play so far with no forgetting. Equivalently, a second component with forgetting factor 1.
- **Fitting.**
  - First plays only. The app invited players to play again to beat their score, and Jangraw et al. 2023 kept first plays only because that changes motivation; a level could matter in a record chase for that reason alone.
  - Train on each first play's first 10 ratings and test on its last 2, Jangraw et al.'s split.
  - Pooled arm (primary): happiness standardised within participant on her training ratings, one shared forgetting factor chosen on a grid from 0.05 to 0.9, common weights, and participant intercepts.
  - Per participant, as Rutledge et al. 2014 fitted, reported beside it, with ridge penalties tuned on a 5,000-participant exploratory split that is then set aside, as Jangraw et al. did. Unpenalised, one more free parameter on 10 training ratings costs far more held-out error than the 1% bar.
- **Primary.**
  - Relative change in held-out mean squared error from M0 to M1 in the pooled arm.
  - The pooled level weight, with a 2,000-resample participant bootstrap interval; the median per-participant weight beside it.
- **Positive controls.**
  - Pooled arm: plant a level effect. Add to each standardised rating a common weight times her level, with the sign of M1's fitted level weight and its size set so the planted term's within-participant variance over training ratings is 2% of M0's training residual variance, and refit M0 and M1. If M1 then lowers held-out error by less than 1%, record "design cannot test" for the level contrast. A constructed check of this design gave 1.8%.
  - Per-participant arm: time, the reproduced model against M0; Jangraw et al. found a 3.3% gain (0.336 to 0.325) on this split. Record the gain. Time can't control the pooled arm: its mean weight is small next to its spread across people (−0.128 ± 0.007 %mood per minute, mean ± SE over 21,896 people, so an SD near 1), and one common time weight barely lowers held-out error.
- **Outcomes.**
  - **Against C3:** M1 lowers held-out error by at least 1%, and the level weight's interval excludes zero (a level effect of either sign contradicts C3).
  - **Supports C3:** the improvement is under 0.5%, and the interval includes zero.
  - **Inconclusive:** anything else.
- **Reported beside it:** the time weight in M0, refitted with time in minutes (where the intake records trial times) and happiness in percent of the scale, as a check against Jangraw's published −0.128% per minute; and whether the level term's effect grows late in a play.
- **Pre-mortem.**
  - Within a play of about 30 trials, the level and the discounted sums are correlated. Identification comes from the forgetting-factor contrast and from variation across participants, which the pooled arm's common weights use.
  - Report the multiple correlation of the level with M0's other regressors (the three discounted sums at the pooled forgetting factor, and time), within participant and pooled over training ratings. The planted-level control, not this correlation, decides whether the design can test the level. Per participant, over 12 ratings, the same correlation runs above 0.9 for most people even when the pooled arm identifies the level (a constructed check gave 0.47 pooled, and above 0.9 for 54% of participants), so report the per-participant version for the per-participant arm only.
  - M1 keeps M0's forgetting factor, and per-participant fits above 0.9 are excluded from the level contrast and counted. At a forgetting factor of 1 the level equals the sum of the three discounted sums, so its weight isn't identified.
- **Ceiling:** 2 CPU-hours, shared with TD2.

### TD2. Does uncertainty attenuate the trigger? (C3's gate)

- **Claim tested.** "Sufficiently certain futures" trigger more than uncertain ones of the same value.
- **Model.** M0, plus two discounted components with the same forgetting factor: each chosen gamble's expected value multiplied by its spread (the distance between its two outcomes, standardised), and each chosen gamble's expected value multiplied by its own absolute value, a curvature control. In gain and loss trials one outcome is nothing, so there the spread is a fixed multiple of the absolute expected value; without the control the spread term is a curvature term, and diminishing sensitivity alone makes its weight negative. With the control, mixed gambles identify the spread weight. Fitted on first plays in TD1's two arms.
- **Primary.** The pooled arm's weight on the spread component, with a 2,000-resample participant-bootstrap interval; the median per-participant weight beside it. A negative weight means a wider gamble's expected value counts for less, toward zero, for gains and losses alike, while the effective expected-value weight stays positive; report the share of chosen gambles for which it turns negative.
- **Outcomes.**
  - **Supports the gate:** the interval lies below zero and the weight's size passes the design note's practical bar.
  - **Against:** the interval lies at or above zero.
  - **Inconclusive:** anything else.
- **Reported beside it:** per point, the certain-reward weight minus the expected-value weight. A positive difference is weaker evidence than the primary: a certain reward is received at once, while a gamble's value is only anticipated, so timing differs as well as certainty.
- **Case check.** Spread must vary at a fixed expected value, which only mixed gambles allow: at least 10,000 participants with 5 or more chosen mixed gambles in their first play, and a pooled correlation between spread and absolute expected value among chosen mixed gambles below 0.9.

### TD3. Is security defended from below and spent from above? (C4)

- **Claim tested.** Below a security set point, people defend it and take less risk; above it, they spend surplus and take more.
- **Rivals.**
  - Prospect theory's break-even effect predicts *more* risk-seeking when behind, when a gamble could restore the start (Thaler & Johnson 1990).
  - The house-money effect predicts more risk when ahead.
- **Model.** Logistic regression of choosing the gamble, with:
  - participant intercepts;
  - trial type;
  - the gamble's expected value minus the certain amount;
  - standing (points above or below the play's starting total), with separate slopes below and above zero;
  - the number of gambles she has taken so far in the play, the trial index, and the discounted sum of her recent outcomes at TD1's forgetting factor. Gambles spread standing both ways, so a risk propensity that persists within a play otherwise makes risk rise with distance from the start on both sides; the recent-outcome term keeps momentum from being credited to standing.
- **Plays.** First plays are primary. Repeat plays are reported beside them, with her best earlier score as a second reference point, since the app invited players to beat their score.
- **Primary.** The slope below zero. C4 predicts it's positive: risk falls the further behind she is.
- **Outcomes.**
  - **Against C4:** the slope below zero is negative, its participant-clustered 95% interval lies below zero, and its size passes the design note's practical bar. Report it separately for trials where she is behind, the gamble's better outcome would bring her back to the start, and the certain option would not.
  - **Supports:** the interval lies above zero and the slope's size passes the practical bar.
  - **Inconclusive:** anything else.
- **Reported beside it:** the slope above zero. A positive slope there is predicted by both C4 and house money, so it's weak support.
- **Pre-mortem.** A game total is a weak stand-in for security. Its value here is the "against" outcome. Within-play intercepts with regressors built from her earlier choices bias the slopes a little (a constructed null gave +0.5 points of probability per 100 points below zero, interval above zero). Before outcomes, fit the model to 20 sets of choices simulated from the fitted model with both standing slopes set to zero, on each participant's own trial sequence. The practical bar is at least twice the mean absolute slope those nulls give plus three times their standard deviation: a constructed check found real-data null slopes up to about 1.6 times the simulated nulls' mean, so a bar just above the null slopes let a world with no standing effect read as "supports".
- **Case check.** At least 10,000 participants with first-play choices on both sides of zero, and at least 10,000 choices where the gamble could restore the start.
- **Ceiling:** 1 CPU-hour.

### TD4. Are the word scales single scales? (C2)

- **Words.** The curator's scales, weak to strong:
  - FEAR: uneasy, worried, anxious, scared, terrified.
  - RAGE: annoyed, frustrated, mad, angry, furious, rage.
  - SEEKING: interested, curious, eager, enthusiastic, excited.
  - PANIC/GRIEF: sad, lonely, grief, anguish, heartbroken.
  - CARE: tender, fond, protective, devoted, love.
  - PLAY: amused, silly, giddy, playful, hilarious, hysterical.
  - LUST: desire, passionate, lust, aroused.
  - DISGUST: dislike, yucky, disgusted, gross, loathe.
- **Mapping to intensity columns.**
  - RAGE to anger, FEAR to fear, PANIC/GRIEF to sadness, DISGUST to disgust.
  - SEEKING to anticipation, with joy beside it.
  - PLAY to joy; CARE to trust, with joy beside it.
  - LUST has no column, so it gets VAD only.
- **Coverage first.** Use NRC Emotion Intensity Lexicon v1 and NRC VAD v2.1. Report which words each lexicon holds. A word is covered for intensity only where it has a score in its scale's mapped column, since the intensity lexicon scores a word only for emotions it is associated with. A scale with fewer than 4 covered words is "not covered" for that lexicon. Adjacent pairs are neighbours in the curator's order among covered words; LUST's order is checked on VAD arousal.
- **Primary, per covered scale.**
  - The number of adjacent pairs that are out of order on the mapped intensity, with Spearman's correlation.
  - In VAD, the off-line ratio: the residual standard deviation of dominance after a straight-line fit on the mapped intensity (on arousal for LUST), divided by the standard deviation of arousal. Words on one line score near 0 whatever the line's slope, so the ratio reads a second dimension, not the scale's direction.
- **Outcomes, per scale.**
  - **Against:** more than one adjacent inversion, or an off-line ratio above 1.
  - **Supports:** no inversions and a ratio below 0.5.
  - **Inconclusive:** anything else.
- **Scope.** These are word norms. A positive result shows how people rate words, not that a channel fires in grades.
- **Ceiling:** 0.1 CPU-hour.

### TD5. Do raters' disagreements stay inside a channel? (C2)

- **Units.** Comments with 3 or more raters, and every pair of raters on each comment.
- **Channel assignment**, fixed before outcomes:
  - RAGE: anger, annoyance.
  - FEAR: fear, nervousness.
  - PANIC/GRIEF: grief, sadness.
  - PLAY: amusement, joy.
  - SEEKING: curiosity, excitement.
  - CARE: caring, love.
  - LUST: desire.
  - DISGUST: disgust.
  - Every other category is unassigned (a mix).
- **Measure.** Over ordered pairs of distinct raters (i, j) on the same comment, count disagreements on X and Y: i's labels hold X but not Y, and j's hold Y but not X. The expected count is the number of ordered pairs times P(a rating holds X but not Y) times P(a rating holds Y but not X), from all clear ratings in the unit. The lift is observed over expected. Agreements and one rater's own multiple labels never count.
- **Primary.** For each of the six within-channel pairs (anger and annoyance, fear and nervousness, grief and sadness, amusement and joy, curiosity and excitement, caring and love): its lift minus the highest lift between either member and any category in another channel whose expected count is at least 50, the competitor chosen on the full data and held fixed across draws. Give a 2,000-draw comment-bootstrap interval. A pair wins if its interval lies above zero and the difference passes the design note's practical bar; it loses if its interval lies below zero and the difference passes the bar.
- **Outcomes.**
  - **Against C2:** 3 or more of the 6 pairs lose.
  - **Supports:** all 6 win.
  - **Inconclusive:** anything else.
- **Reported separately:** the same comparison against unassigned categories (for example annoyance against disapproval, sadness against disappointment). The theory reads those as mixes, so losing to one is ambiguous.
- **Also reported:** the primary within comments with exactly 3 raters, since a comment got 2 more raters only when its first 3 shared no label.
- **Ceiling:** 0.5 CPU-hour, shared with TD6.

### TD6. Does disgust come with less talk of minds? (C10)

- **Rivals.** C10 predicts that disgust stops modelling the other, so less attribution of mental states. Giner-Sorolla & Chapman 2017 predict the same or more, because disgust follows an inferred desire to harm.
- **Units.**
  - A comment is "disgust" if at least 2 raters label it disgust and none labels it anger.
  - It is "anger" if at least 2 label it anger and none labels it disgust.
  - Both groups are matched 1:1 without replacement, exactly on subreddit and on decile of whitespace-token length (deciles over the two groups pooled), in seeded random order within each stratum; unmatched comments are dropped and counted.
- **Case check.** At least 300 comments in each group after matching. If not, relax to at least 1 rater with no rater giving the other label, and record the relaxation. On the raw data the 2-rater rule leaves 732 disgust and 1,485 anger comments and about 200 matched pairs, so expect the relaxation (about 1,440 pairs).
- **Resolution.** The pattern fires about 0.2 times per 100 tokens (median comment 12 tokens): with the frozen pattern, a check found 17 hits across both strict matched groups and 73 across both relaxed ones, with 95% intervals 119 and 88 percentage points wide. Either decisive outcome needs a difference of roughly 40% or more; smaller ones come out inconclusive. Report the hit counts.
- **Measure.** Mental-state attributions to others per 100 tokens:
  - A third-person subject (he, she, they, people, someone, everyone, or the [NAME] mask) followed within 3 tokens by one of these verb forms: think, thinks, thought, thinking; believe, believes, believed, believing; want, wants, wanted, wanting; mean, means, meant; intend, intends, intended, intending; know, knows, knew, known, knowing; feel, feels, felt, feeling; care, cares, cared, caring; try, tries, tried, trying; wish, wishes, wished, wishing; expect, expects, expected, expecting. Tokens are lowercase runs of letters, with the [NAME] mask as one token, so contractions split at the apostrophe; the rate per 100 tokens uses the same tokens.
  - The pattern list is frozen before outcomes.
- **Primary.** The rate in disgust comments minus the rate in anger comments, relative to the anger rate, with a bootstrap interval stratified by subreddit.
- **Outcomes.**
  - **Supports C10:** the interval lies below −10%.
  - **Against:** the interval lies above −10%.
  - **Inconclusive:** anything else.
- **Reported beside it:** the same contrast among comments whose target is a person (a third-person pronoun present). Disgust at food or bodies would lower mind-talk for reasons unrelated to a closed model.

### TD7. After rejecting an offer she has examined, does she stop weighing the source? (C10's function, on our records)

This tests the function the curator assigns to DISGUST, not the channel itself.
- **Data.** CoAuthor's canonical menus with option features and her state, from `runners/drive/cards/`: `week4_t4_menus_v2.py` (handling, open and resolution times), `week4_t4_history.py`, `week4_t4_encoding.py` and `week4_t4_inputs.py`; suggestion-hover events from `week4_s4_menu_source.py` (an opening or reopening snapshot is not a hover).
- **Model code.** `week4_t4_kernel_h1.py` and `week4_t4_choice.py` accept exactly five option features and two state terms, so the arm terms need a new versioned kernel. Check it against `week4_t4_choice.py` with the arm terms at zero, and against finite differences on the new terms, before any human fit.
- **Arms**, within writer:
  - after an examined dismissal: her upper tercile of open time (terciles over all her opened menus), or a suggestion-hover event while the menu was open;
  - after an examined acceptance, matched on open-time tercile and session-time decile;
  - fast dismissals reported separately.
- **Primary.** Over her next 3 opened menus with a canonical choice in the same session (ignored menus skipped; a menu inside two windows goes to the earlier event): how sensitive her choices are to option fit. One pooled conditional logit on these menus holds T4's five option features, writer-specific dismissal constants, and three arm terms (examined dismissal against examined acceptance): times cosine to her own history, times fit to the preceding sentence, and times the dismissal alternative. The primary is the mean of the two feature-by-arm coefficients, with features standardised on these menus, and a 2,000-resample writer-cluster interval; each coefficient is reported beside it. The controls enter as interactions with the dismissal alternative and with both fit features.
  - C10's function predicts flatter sensitivity after examined dismissals.
  - The rival, value learning, predicts a higher dismissal constant with sensitivity unchanged.
- **Outcomes.**
  - **Supports:** the primary's interval lies below zero.
  - **Against:** the interval lies at or above zero while the arm's dismissal term has an interval above zero.
  - **Inconclusive:** anything else.
- **Controls.** Characters typed between menus; time since the event; session-time decile.
- **Case check (amendment F).** At least 20 writers, each with at least 10 examined dismissals and 10 matched acceptances followed by 3 qualifying menus, as the primary defines them.
- **Pre-mortem.** Regression to the mean on open time (handled by matching); fatigue; general disengagement, which this design can't tell from closing a model. 14,285 of 16,855 opened menus carry a suggestion-hover event (S4(b)'s census), so the hover clause may make most dismissals examined: report how many qualify by each clause, and the primary with the open-time clause alone. After an acceptance the preceding sentence can be the accepted offer, which shifts the fit-to-sentence feature by arm: report each arm's share of post-event menus whose preceding sentence is writer-typed (R2's tags), and the primary on those menus.
- **Ceiling:** 3 CPU-hours. Past twice that, use the frozen 25-writer sample.

## 3. Backlog, in order, each after a licence check

If a licence fails, record "unsupported at source" and move on. Each backlog card's design note fixes its practical bar and three-way rule (supports, against, inconclusive) before outcomes, as section 0 requires; the outcome lines below give only the direction. B1 tests Claude's candidate interest set point, not a claim of the curator's.

**B1. Mood drift and an interest set point.**
- **Data:** Jangraw et al. 2023's online cohorts. Data at https://osf.io/km69z/ (no data licence stated in the paper or the code README; check the OSF page); code at https://github.com/djangraw/MoodDrift, a US Government public-domain work per its LICENSE file.
- **Test:** estimate the drift slope by condition (rest, visuomotor task, random gambling).
- **Outcomes:** an interest set point predicts steeper drift with less learnable input. Equal drift across conditions counts against it.
- **Ceiling:** 1 CPU-hour.

**B2. Choosers who never trade (C5).**
- **Data:** the Moral Machine responses, https://osf.io/3hvt2/. Confirm the licence and file layout.
- **Test:** among users who saw at least 3 scenarios on a dimension, find the share who chose the same side of that dimension every time. Each 13-dilemma session holds two dilemmas per dimension plus one random one (Awad et al. 2018, Methods), so 3 or more on a dimension takes a returning user: count them first as the case check. Compare against a coin-flipper's chance of 2 × 0.5^n for n scenarios (25% at 3), and against mundane dimensions (gender, fitness).
- **Outcomes:** never-trading rates on mundane dimensions that match those on species or intervention count against reading such refusals as identity.
- **Ceiling:** 2 CPU-hours.

**B3. Does winning standing satiate? (C4's "no ceiling")**
- **Data:** DomArchive (Strauss et al. 2022). Confirm the data licence.
- **Test:** use only datasets kept as time-ordered edgelists that say who acted on whom; 418 of DomArchive's 436 datasets are win-loss matrices with no order. Compute ranks (Elo) on each group's first half of interactions, then regress the aggression each individual initiates per partner in the second half on her first-half margin over the next rank. Ranks and outcomes taken from the same interactions would tie margin to wins by construction. Case check: at least 10 groups qualify, or record "design cannot test".
- **Outcomes:** "no ceiling" predicts no fall with margin. A fall counts against it.
- **Ceiling:** 1 CPU-hour.

**B4. Effort times skill (C6).**
- **Data:** a 1% random sample of one named month of the Lichess database (CC0), https://database.lichess.org/, keeping games with both engine evaluations and clock annotations. The design note names the month after a probe shows that streaming its compressed file for the sample fits the ceiling.
- **Test:** model each move's quality (minus its centipawn loss, so higher is better) on rating, log of time spent, and their product, controlling for game phase and position difficulty. Use low clock time as the forcing instrument for log time and for its product with rating.
- **Outcomes:** a product term at or below zero counts against effect = effort × power.
- **Ceiling:** 2 CPU-hours.

## 4. Dispatch

1. I1, I2 and I3.
2. TD4 (minutes).
3. TD5 and TD6.
4. TD1 and TD2.
5. TD3.
6. TD7.
7. The backlog, in order, while slots are free.

## 5. Reporting

- **Digest** at drain: `results/phase_2_4_stage_15/THEORY_DAYS/DIGEST.md`, beside the results, as week 4's digests sit in `results/phase_2_4_stage_15/DRIVE/`. For each card, give:
  - its outcome (supports, against, inconclusive, design cannot test, or unsupported at source);
  - the primary with its interval;
  - the case-check counts;
  - the commit of the design note.
- **Intake records** for I1 to I3 and any backlog source.
- **No cross-repository delivery.** These results go to the curator's theory thread.

## 6. Pre-mortem

- **The Rutledge data's fields may differ from the paper's.** The intake check comes first, and TD1 to TD3 depend on it.
- **The mapping from everyday emotion categories to channels is loose.** An "against" in TD4 to TD6 may be a mapping failure, so report coverage and the unassigned comparisons.
- **With over a million ratings, tiny effects pass significance tests.** That's why the practical bars are fixed in the design notes before outcomes.
- **The lexicon licence forbids redistribution.** Commit statistics only.

## 7. Triggers to the curator

1. A paid call would be needed. None is planned.
2. Privacy: an identifier or raw text would leave the repository.
3. An outage longer than 12 hours.

## Sources

- Rutledge, Skandali, Dayan & Dolan 2014, a computational and neural model of momentary subjective well-being, *PNAS*: https://doi.org/10.1073/pnas.1407535111.
- Rutledge, the Great Brain Experiment risky-decision and happiness data, Dryad: https://doi.org/10.5061/dryad.prr4xgxkk.
- Jangraw et al. 2023, mood drift over time, *Nature Human Behaviour*: https://doi.org/10.1038/s41562-023-01519-7.
- Thaler & Johnson 1990, gambling with the house money and trying to break even, *Management Science* 36:643-660.
- Demszky et al. 2020, GoEmotions, ACL: https://aclanthology.org/2020.acl-main.372; data: https://huggingface.co/datasets/google-research-datasets/go_emotions.
- Mohammad 2018, word affect intensities (LREC): https://arxiv.org/abs/1704.08798; lexicons at saifmohammad.com.
- Giner-Sorolla & Chapman 2017, beyond purity, *Psychological Science*: https://doi.org/10.1177/0956797616673193.
- Awad et al. 2018, the Moral Machine experiment, *Nature* 563:59-64.
- Strauss et al. 2022, DomArchive, *Philosophical Transactions of the Royal Society B*.
