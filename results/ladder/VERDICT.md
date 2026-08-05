# The intent ladder — FAIL, and it explains yesterday's best result

**2026-08-05.** 50 artifacts, five rungs of 0 / 1 / 3 / 6 / 10 randomly-drawn prompt
specifications, content randomised, no specification naming a decision or an omission.

---

## Two independent grounds for failure

### 1 · VOID on length, by a hair, and the hair counts

| rung | median output |
|---|---|
| 0 | 1,398 |
| 1 | 1,440 |
| 3 | 1,432 |
| 6 | 1,454 |
| 10 | 1,456 |

**rung vs output length: rho = +0.403, p = 0.0037.** The pre-registration voids at above 0.40.

It is 0.403. The absolute difference is 4% — 1,398 words against 1,456 — and I do not get to say
"but it is only 4%" after writing the threshold down. **Voided.**

### 2 · Every measure that tracks the rungs is vocabulary

| measure | rho vs rung | **rho after word-shuffling** | |
|---|---|---|---|
| you_rate | **+0.703** | **+0.703** | identical |
| causal_rate | +0.659 | +0.659 | identical |
| density_scale_gain | +0.548 | +0.442 | mostly survives |
| type_token_ratio | −0.545 | −0.545 | identical |
| insight_rate | +0.457 | +0.457 | identical |
| i_rate | +0.407 | +0.407 | identical |

**Shuffling destroys every trace of order and changes almost nothing.** The strongest signal,
`you_rate` at 0.703, is the model addressing a reader more often because the specifications mention
readers. That is prompt vocabulary leaking into output vocabulary.

Five-way rung classification from the whole function-word vector: 32% against 20% chance.
Ends only, rung ≤1 against rung ≥6: **85%** — and it is the same vocabulary signal, sharper.

---

## What this retires

**Yesterday's rich-arm result is now explained.** `rich` ranked above `thin` on density at
p = 0.0032, in the theory's exact ordering, and I called it the most important result of the
project before the shuffle test killed it. **The ladder says what it was:** longer prompts change
the model's word choices, and every measure available was reading that.

The curator called for this rerun because the first design was not robust enough. It was not, and
the rerun is what settled it rather than leaving it as a suspicion.

---

## What it does NOT say

**It does not say added specification fails to add recoverable intent.** It says something
narrower and more useful:

> **Every measure this project currently has is lexical, and lexical measures cannot tell added
> intent from added vocabulary.**

Which is the argument for the one untried measure. The **layer ratio** — low-order against
high-order affective activation in a reading model — is a ratio *within one reader on one text*, so
prompt vocabulary acts on both terms and cancels. It is the only proposed measure whose
construction is immune to the thing that just killed this one.

---

## The corpus is the output

**50 artifacts with a known, monotone, randomised-content intent manipulation.** Nothing like it
existed yesterday.

Every future measure gets run against it, and the bar is now explicit and hard:

> **Rank the five rungs in order, and lose the effect when the words are shuffled.**

A measure that does both is reading something other than vocabulary. Nothing has yet.
