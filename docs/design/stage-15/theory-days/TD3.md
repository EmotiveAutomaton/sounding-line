# TD3: frozen implementation note

DESIGN CHECK: LESSONS 1a-1c and 2-5; CONTROLS 6-7.
Under the null the control must retain zero; under the specified alternative it
must recover the registered direction. Invalid controls or missing support stop
scientific interpretation. The inconclusive band includes every case not admitted
by a passing control and an explicit support or against rule.

Practical bar: max(0.01 log-odds per training SD of standing, two null mean absolute slopes plus three null SDs). Null trajectories must update all choice-dependent histories.

[Review amendments](REVIEW.md) and [source intake](DATA_INTAKE.md) bind this
implementation alongside the unchanged supplied specification below. All draws
use seed 20261106 unless the packet explicitly retains a prior frozen sample.
Scientific execution must pin a Git commit containing this note. This design
records planned work, not completed validation or results.

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
