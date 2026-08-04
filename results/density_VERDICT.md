# E49 density by compression — a length measure wearing a theory's clothes

**2026-08-04. Built, run, and disqualified inside twenty minutes**, because the confound check ran
before the result was written up rather than after.

---

## What it looked like

| | |
|---|---|
| E49's untested bimodality prediction | **BC = 0.642 and 0.745** against a 0.556 threshold — **bimodal**, on both quantities |
| the no-maker control | generated `scale_gain` **0.201** against human **0.323** — 38% lower, the right direction |
| half A vs half B | 0.323 vs 0.323, p = 0.996 |

Two of those looked like the best result of the day.

## What it was

| | |
|---|---|
| **`scale_gain` vs word count** | **rho = +0.877, p < 0.0001** |
| length-matched at 562 words | human **0.200**, generated **0.201** — **identical** |
| the "two modes" | low: median **1,109** words. high: median **4,865** words. Halves split evenly across both. |

**`scale_gain` is a word-count proxy.** The bimodality is in the *length distribution* of the
corpus. The no-maker signal was that the three generated artifacts are ~560 words against a human
median of 2,914.

Mechanically obvious in hindsight: when a text is too short to fill the largest window, the measure
falls back to a smaller scale, so short texts *cannot* show a large gain.

---

## The pattern, now unmistakable

Fifth instrument, fifth instance of **the instrument measuring a property of the input that is not
the thing wanted**:

| | it measured |
|---|---|
| method unlock | denominator instability |
| my separability statistic | one dimension of a joint signal |
| D-0 | five tokens of Poisson noise |
| document-level activation reading | the difference between a sentence and a document |
| **density by compression** | **word count** |

**The space of surface statistics on text is dominated by length, register and vocabulary.**
Anything computed from raw text will mostly measure those unless each is explicitly controlled —
and I have now demonstrated that five times at increasing cost.

**This is the strongest argument yet for reading the reader rather than the text**, which is where
the theory said the leverage was and where the only two positive results have come from.

---

## What would rescue it

Not much, and not soon. The measure needs a fixed token budget across scales so that length cannot
enter, and it needs comparison sets matched on length. That is buildable, but with the A/B
separation at p = 0.996 *before* the confound is removed, there is no signal underneath waiting to
be uncovered.

**E49's bimodality prediction remains untested.** This did not test it.
