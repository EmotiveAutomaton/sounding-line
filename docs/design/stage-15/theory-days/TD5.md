# TD5: frozen implementation note

DESIGN CHECK: LESSONS 1a-1c and 2-5; CONTROLS 6-7.
Under the null the control must retain zero; under the specified alternative it
must recover the registered direction. Invalid controls or missing support stop
scientific interpretation. The inconclusive band includes every case not admitted
by a passing control and an explicit support or against rule.

Practical bar: 0.1 lift units in either direction. Retain the original fixed-competitor interval and add maximum-reselected uncertainty; no unsupported pair is a zero competitor.

[Review amendments](REVIEW.md) and [source intake](DATA_INTAKE.md) bind this
implementation alongside the unchanged supplied specification below. All draws
use seed 20261106 unless the packet explicitly retains a prior frozen sample.
Scientific execution must pin a Git commit containing this note. This design
records planned work, not completed validation or results.

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
