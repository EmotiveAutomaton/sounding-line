# TD1: frozen implementation note

DESIGN CHECK: LESSONS 1a-1c and 2-5; CONTROLS 6-7.
Under the null the control must retain zero; under the specified alternative it
must recover the registered direction. Invalid controls or missing support stop
scientific interpretation. The inconclusive band includes every case not admitted
by a passing control and an explicit support or against rule.

Practical bars: 1% held-out error gain against, below 0.5% for the packet support rule; both signed plants and an error-gain interval accompany the original rule.

[Review amendments](REVIEW.md) and [source intake](DATA_INTAKE.md) bind this
implementation alongside the unchanged supplied specification below. All draws
use seed 20261106 unless the packet explicitly retains a prior frozen sample.
Scientific execution must pin a Git commit containing this note. This design
records planned work, not completed validation or results.

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
