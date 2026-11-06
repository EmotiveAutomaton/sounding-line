# TD2: frozen implementation note

DESIGN CHECK: LESSONS 1a-1c and 2-5; CONTROLS 6-7.
Under the null the control must retain zero; under the specified alternative it
must recover the registered direction. Invalid controls or missing support stop
scientific interpretation. The inconclusive band includes every case not admitted
by a passing control and an explicit support or against rule.

Practical bar: 0.01 training-standardized happiness units per SD of the residualized spread component; report both this standardized coefficient and the original coefficient.

[Review amendments](REVIEW.md) and [source intake](DATA_INTAKE.md) bind this
implementation alongside the unchanged supplied specification below. All draws
use seed 20261106 unless the packet explicitly retains a prior frozen sample.
Scientific execution must pin a Git commit containing this note. This design
records planned work, not completed validation or results.

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
