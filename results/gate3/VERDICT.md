# Gate 3 — the primary failed, and it could not have succeeded

**Scored 2026-08-04 with `runners/score_gate3.py`, written before any artifact had been read,
against card `d373508e2373`.** 51 artifacts, k=5, both arms, local, sanitised and date-censored.
One dropped. ~14 hours.

---

## The numbers

| **G3.1 — method unlock, Half A vs Half B** | |
|---|---|
| Half A | mean **1.329**, sd 0.913, n = 28 |
| Half B | mean **1.242**, sd 0.573, n = 22 |
| difference | **+0.087**, 95% CI **[−0.338, +0.513]** |
| | Welch t = 0.413, **p = 0.68**, Cohen **d = 0.11** |
| | **FAIL** |

Direction is as predicted and the effect is indistinguishable from nothing. The pilot's d = 0.87
became d = 0.11.

**No length confound** (r = +0.266, p = 0.062). One artifact dropped — `b_a8a3e574`, which was
never text; see `ACCIDENT.md`.

---

## N13 failed, and the card says that outranks the p-value

> **N13.** Per-artifact unlock is stable enough to measure: within-artifact spread across k = 5 is
> smaller than the between-half difference. **If not, k must rise before any claim is made.**

| within-artifact sd | **0.808** |
|---|---|
| between-half difference | **0.087** |

**The noise is nine times the signal.** And the author's recorded prior, written before the run:

> The author expects N13 to be the tightest null... **if N13 fails the correct response is to raise
> k and re-run rather than to report G3.1 at any p-value.**

**So G3.1 is not reportable.** Not as a failure, not as anything. That is pre-registered and it is
not a convenient reading — it was written down when a null result would have been the comfortable
outcome.

---

## And raising k would not help, which the simulation established independently

`docs/SIM_RESULTS.md`, run in the parent repository **while this gate was still executing**, on the
same statistic with ground truth available:

| | |
|---|---|
| at mu = 1, where the construction guarantees nothing to unlock | count ratio reads **17.65**, interval [4.54, 37.43] — **fails N28** |
| correlation with `process_error_reduction`, the graded measure it stands in for | **r = 0.086** |
| rollouts where the denominator is zero | **378 to 467 of 467** |

> A statistic that never consults the truth reports a 17× "unlock" in a world built so that there
> is provably nothing to unlock.

**N13's failure is not sampling noise. It is that structure.** A ratio whose denominator is
frequently near zero has unbounded variance, and here the median within-artifact sd is 0.465 while
the maximum is **7.43**. More samples of an undefined quantity are more undefined.

---

## What may and may not be concluded

**The stop condition's conclusion is NOT licensed.** The card says:

> If G3.1 fails... then recoverable intent, as this project defines and measures it, is not more
> present in work made with care than in competent commercial work.

**That inference requires an instrument that could have detected the difference.** N13 says this one
could not, the simulation says why, and the card itself forbids reporting G3.1 when N13 fails.

**Gate 3 is uninterpretable, not negative.** Which is worse than a clean negative and more honest
than either alternative — it means fourteen hours of GPU produced a number nobody may use.

**What IS licensed:**

- **The measure is disqualified.** Not "did not reach significance" — *disqualified*, on a null it
  failed and on independent mechanism evidence. Method unlock as a count ratio does not carry a
  primary.
- **The corpus split is untested**, and remains so. Nothing here says whether Half A and Half B
  differ in recoverable intent.

---

## The secondaries, reported because the card says report them regardless

| | | |
|---|---|---|
| **G3.2** named-alternative rate | A 0.657, B 0.711, p = 0.35 | **REVERSED** — same direction as Gate 2. The unlock pass did not fix it. |
| **G3.3** boundedness ablation | bounded separates +0.087, free-form **+0.000** | **bounded better** — but on a disqualified statistic, so it establishes little. `ACCIDENT.md` is the stronger evidence and it was an accident. |
| **G3.4** machine-audience | A 0.069, B 0.090, p = 0.36 | as predicted, not significant |
| purpose agreement *(diagnostic)* | A 0.800, B 0.751, p = 0.39 | |

---

## C-22's predictions, logged mid-run before any result, now checked

Recorded in `docs/theory/FLATTENED_INTENT.md` on 2026-08-03, deliberately before Gate 3's numbers
existed, precisely so this could happen.

| | prediction | result | |
|---|---|---|---|
| **F-1** | Half B shows **higher** purpose agreement | A 0.800, B 0.751 | **FAILED** |
| **F-3** | Half B shows **lower** purpose breadth — *"the sharp one"* | A 0.324, B 0.361 | **FAILED** |
| **F-4** | Half B decision density **not** lower | A 3.166, B 3.552 | **HELD** |

**F-3 was the one that mattered and it failed, in the wrong direction.** The hypothesis document
called it *"the sharp one"* and said explicitly that a confirmation would not establish C-22
because the corpus had been read many times. A **disconfirmation** does not have that problem: the
prediction was directional, recorded, and it went the other way.

**Two caveats, both real, neither rescuing:**

- Nothing here is significant. p = 0.35 and 0.39. This is a failure to confirm rather than a
  confirmed reversal.
- The simulation found `purpose_breadth` **does** separate flattened from layered makers at matched
  density (−0.108, interval excluding zero) — and warned of a **floor effect on easy material**,
  which this corpus may be. So F-3 may have failed for the reason S-2 predicted rather than because
  C-22 is wrong.

**C-22 is not refuted. Its test on this corpus is not evidence for it, and F-3 went the wrong way.**

---

## What this costs and what survives

**Costs:** the primary measure, and the claim Gate 3 was built to test. The instrument does not
currently measure what the theory says it measures, and this run cannot say whether the theory is
right.

**Survives, and all of it independently of the failed measure:**

- **the wall as a positive signature** — the simulation's S-6: a maker with no budget produces a
  **flat** surface, not a thin one
- **`purpose_breadth`** — validated at the mechanism level at matched density, unconfounded with
  depth
- **the leaked layer is readable** — 0.899 against 0.250 chance, and the shield claim strengthens
  with amplification
- **boundedness has a failure mode that means something** — `valid=0/5` is information the
  free-form arm structurally cannot produce
- **the function-word channel** — 7.6× host identification on this corpus, 2.05× within-author
  across works
- **every reading the curator produced.** Eleven artifacts, two sessions, and not one of them has
  been invalidated by anything today.

The successor design in `docs/SUCCESSOR.md` was written before this number existed. Its first
requirement — a corpus this project has not seen — is unchanged, and its second is now specified by
mechanism: **score a graded log-probability against a baseline, not a count of recovered
decisions.**
