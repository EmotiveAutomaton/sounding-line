# TD6: frozen implementation note

DESIGN CHECK: LESSONS 1a-1c and 2-5; CONTROLS 6-7.
Under the null the control must retain zero; under the specified alternative it
must recover the registered direction. Invalid controls or missing support stop
scientific interpretation. The inconclusive band includes every case not admitted
by a passing control and an explicit support or against rule.

Practical bar: the supplied 10% relative reduction. A zero anger denominator is undefined. Resample matched pairs within subreddit.

[Review amendments](REVIEW.md) and [source intake](DATA_INTAKE.md) bind this
implementation alongside the unchanged supplied specification below. All draws
use seed 20261106 unless the packet explicitly retains a prior frozen sample.
Scientific execution must pin a Git commit containing this note. This design
records planned work, not completed validation or results.

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
