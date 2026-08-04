# R-1 says PASS. The pass condition had a 50% false-positive rate.

**2026-08-04.** Reporting this as **UNINFORMATIVE** rather than banking the pass, because the
threshold I wrote could not do its own job — and I can show that arithmetically rather than
suspecting it.

---

## What came back

| component | human (n=50) | generated (n=3) | diff |
|---|---|---|---|
| unmoved | 0.020 | 0.333 | **+0.313** |
| unconcentrated | 0.340 | 0.368 | +0.028 |
| unnameable | 0.319 | 0.333 | +0.014 |
| **unconverged** | 0.222 | 0.133 | **−0.088** |
| **unattempted** | 0.088 | 0.000 | **−0.088** |

Three of five higher → my pre-registered PASS.

## Why that is worth nothing

> **P(≥3 of 5 components higher, by chance alone) = 50.0%**

I wrote a threshold with **a coin-flip false-positive rate** and no magnitude requirement. Any
five-component panel of noisy measures passes it half the time. This is the sixth instance in this
lineage of *a criterion unable to do its own job*, and the first one I have caught by computing its
false-positive rate **before** quoting the verdict rather than after.

And the substance is worse than the arithmetic:

- **two of the three "wins" are +0.014 and +0.028** — noise on n = 3;
- **the entire pass rests on `unmoved`**, which at 0.333 with n = 3 means **exactly one artifact**
  out of three had a posterior that settled on the first pass.

**One artifact is not a finding.**

---

## The two losses are more interesting than the win

**`unconverged` went the wrong way, and E38 predicts exactly that.** Independent readings of
generated content *agreed more* than readings of human content. The probe is a machine-matched
reader — 1.000 on machine content against 0.280 on human — so it finds its own family's output
easy and converges on it. **Disagreement-as-wall (E2's signature) is unavailable to a reader that
finds the wall legible.**

That is a real constraint on the whole refusal idea: two of its five components measure the
*probe's difficulty*, and the probe has systematically less difficulty with exactly the content the
theory says should be hardest.

**`unattempted` went the wrong way for the same reason.** The schema rejected zero generated
samples and 8.8% of human ones. Machine text is tidier, so it validates more cleanly.

---

## What survives

**R-3: refusal is not the broken measure in new clothes.** Against method unlock, on the same 50
artifacts:

| | rho | p |
|---|---|---|
| unnameable | −0.071 | 0.62 |
| unconcentrated | −0.120 | 0.41 |
| unconverged | −0.069 | 0.63 |

**Independent of the disqualified statistic**, which was worth checking and is the one clean result
here.

**R-2, exploratory, no prediction made:** Half B refuses marginally more on 3 of 5, all differences
under 0.05. Nothing.

---

## What has to change

**1 · The pass condition.** Component-counting is not a test. A real one needs a magnitude and a
null — the correct form is a permutation test over group labels on the whole five-vector, which
costs nothing and has a false-positive rate that is what it says it is.

**2 · n = 3 has to stop.** This is the fourth measure tested against the same three Gate 1
artifacts. `runners/make_nomaker_set.py` is queued and builds 36, length-matched, in three kinds.

**3 · Two components may have to go.** `unconverged` and `unattempted` measure the probe's
difficulty, and E38 says the probe's difficulty runs *backwards* to the theory's prediction. A
refusal panel whose components disagree with each other by construction is not one measure.

**The three that survive that cut — `unnameable`, `unconcentrated`, `unmoved` — are the ones about
what the reading could not SAY**, rather than what the probe found hard. That is the version worth
re-running against a real control set.
