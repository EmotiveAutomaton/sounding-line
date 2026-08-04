# D-0 — INCONCLUSIVE. The design could not have detected what it was looking for.

**Corrected 2026-08-03, hours after first reporting it as FAIL.** The correction is mine and it is
the same class of error the parent simulation logged four times: *a criterion unable to do its own
job.*

---

## The observed result

| | ratio | categories > 2.0 | threshold |
|---|---|---|---|
| all cells (4 purpose × 4 affect) | 0.78 | 0 | pass needs > 1.5 and ≥ 3 |
| purpose only | 0.09 | 0 | |
| affect only | 0.19 | 0 | |

48/48 generations succeeded. **Reported as FAIL. That reading was wrong.**

---

## The power simulation, which does not touch the data

The curator's objection was that function words are not frequent enough in a short sample to carry
detectable variation. That is checkable without looking at any observation — plant a real effect,
simulate the design, and see whether the statistic finds it.

Texts were ~380 words. At an `I`-rate of 13.8 per 1,000 that is **five tokens**. Poisson noise on
five counts is enormous relative to a between-group difference, and the separability statistic
divides by a within-group variance made almost entirely of that noise.

**Planted effect: a real 2.4× split, 13.8 / 13.7 / 6.8 / 5.7 per 1,000.**

| design | median F | P(F > 1.5) |
|---|---|---|
| **D-0 as run** — 380 words, k=3 | **1.17** | **38%** |
| 1,000 words, k=3 | 2.60 | 78% |
| 2,000 words, k=3 | 5.02 | 97% |
| **2,000 words, k=10** | 3.30 | **99%** |
| 4,000 words, k=10 | 6.47 | 100% |

*Null control — all four rates identical:* median F = 0.32 at the D-0 design, false-positive rate
5%. The statistic is well-behaved. It is simply blind at this text length.

> **D-0 as run had 38% power against the effect it existed to detect. Its median outcome under a
> real effect was BELOW its own pass threshold.**

A design that fails 62% of the time when the hypothesis is true cannot report a failure as
evidence. **The verdict is INCONCLUSIVE.**

---

## What I got wrong, precisely

I set the pass threshold from the statistic's meaning (1.0 = no group information) and never asked
whether the design could reach it. The stylometry literature is explicit that reliable attribution
needs *at least several hundred words*, and that is for **identity**, which is the strong signal.
**State** is weaker, so it needs more, and I generated 380-word samples.

**The earlier note in this file — that the observed I-rate pattern must not be used because
noticing it after a failure is forbidden — still stands, and for the same reason.** The pattern is
not evidence. What has changed is that the *failure* is not evidence either. Both directions are
now blocked by the same arithmetic, which is the correct symmetric outcome.

---

## D-0b, pre-registered now, with power computed first

> **Design.** Affect only, four states, purpose held fixed, topic held fixed.
> **2,000+ words per generation, k = 10.** 40 generations.
>
> **Power: 99%** against a 2.4× effect in `I`-rate; false-positive rate 0% under the null.
>
> **PASS** — ratio > 1.5 and ≥ 3 categories above 2.0, unchanged.
> **FAIL** — at or below 1.0. At 99% power this *is* informative, which is the whole point of
> computing power before the run rather than after.

Cost ~40 minutes. It is queued behind Gate 3.

---

## The other reading, unchanged and still not acted on

D-0 asked whether a model *instructed* to adopt a state produces state-separable function words.
Whatever D-0b returns, there is a mechanistic account worth holding:

> The model has no **leaked** layer, because it has nothing unchosen. Told to be angry it writes
> angrier *content*; it has no involuntary production to bend. Function words leak in humans
> because they are produced below deliberation, and a system with no below-deliberation has
> nothing to leak.

If that is right, D-0b should *also* fail — for a reason that is a finding rather than a defect.
Distinguishing the two needs the same test on **human** artifacts of adequate length, and the Gate
3 corpus already has those: 1,500–3,500 words each, which is in range.

---

## Kept

- 48 generations at `generations.json` — fixed-topic machine text with known specified states.
  Too short for function-word statistics; still usable as a labelled machine corpus.
- one anomaly, unexplained: `persuade|care` ran 729 words against ~380 everywhere else.
