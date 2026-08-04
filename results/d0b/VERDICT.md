# D-0b — AMBIGUOUS by the letter, and the effect is real

**2026-08-04.** 4 affects, purpose and topic fixed, k = 10, 40/40 generations usable, mean 1,420
words. Burrows' Delta with a nearest centroid, leave-one-out.

| | |
|---|---|
| accuracy | **45.0%** against 25% chance = **1.80×** |
| pre-registered PASS | > 2.0× |
| **verdict** | **AMBIGUOUS** — as written, and it stands |

**And the effect is real:** 18 of 40, **binomial p = 0.0047**, 2.92 sd above chance.

That is the honest shape of it. **A significant effect that does not meet a threshold set in
advance is not a pass**, and moving the threshold now is the exact move this project exists not to
make. But reporting "AMBIGUOUS" without the p-value would understate it in the other direction.

Per-affect: care 60%, seeking 50%, rage 40%, fear 30%.

---

## The design missed its own specification

**Target was 2,000+ words. The generations came in at 1,420.** The model would not write that long
however the instruction was phrased.

Power at the length actually achieved, against D-0's observed rates:

| | |
|---|---|
| 2,000 words, k = 10 — **assumed** | **100%** |
| 1,420 words, k = 10 — **achieved** | **91%** |

So the run was still well powered, and 91% is not the explanation for a 1.80× rather than a 2.0×.
Recorded because the pre-registration named a length and the run did not hit it, which is a
deviation whether or not it mattered.

---

## The part that is a genuine replication

D-0's per-affect `I`-rate pattern was noticed **after** that run failed, and was explicitly ruled
out of use at the time: *"noticing that after a failure is exactly the move this project forbids."*

It has now replicated on independent data, at 3.7× the length, with k = 10:

| affect | D-0 (k=3, 380w) | D-0b (k=10, 1420w) |
|---|---|---|
| rage | 13.8 | 20.6 |
| fear | 13.7 | 17.9 |
| care | 6.8 | 16.0 |
| seeking | 5.7 | 14.3 |

**The ordering replicated exactly** — rage > fear > care > seeking, self-reference rising with
grievance and anxiety, falling with outward-directed care and absorbed curiosity.

**This is the correct way for a post-hoc observation to become evidence**: forbidden when it was
found, held, and then tested on new data. It is the only thing in two days that has made that
transition.

**But the magnitude collapsed**, from a 2.4× spread to 1.44×. At longer length every affect's
`I`-rate rose and the gaps compressed. Whatever the effect is, it is **weaker in long-form than the
short-form accident suggested** — which is the opposite of what the length argument predicted, and
is the most interesting unexplained thing here.

---

## What it licenses

**Function words carry *something* about specified maker state in generated text.** p = 0.0047 on
independent data. That is more than D-0 could say and less than the threshold demanded.

**It does not license option D.** The pre-registration said AMBIGUOUS licenses nothing, and it
does not.

**And it says nothing about humans.** E38's generative analogue stands: a model's own emissions may
be more separable than a person's. The contrast test needs human artifacts of adequate length with
known-ish states, which the reading sessions are the only source of.
