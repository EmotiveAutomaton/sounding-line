# The controls, against a real no-maker set — and a retraction

**2026-08-04.** 36 no-maker artifacts in three kinds, against 51 human artifacts, strictly
length-matched with permutation nulls.

---

## §1. What it looked like, for about fifteen minutes

Length-matched at exactly 1,000 words, short texts dropped, 2,000-permutation null:

| group | scale_gain | vs human | p |
|---|---|---|---|
| **human** | **0.3091** | | |
| rich | 0.2399 | −0.0692 | 0.0005 |
| thin | 0.2316 | −0.0775 | 0.0005 |
| averaged | 0.2268 | −0.0823 | 0.0005 |

**human > rich > thin > averaged**, and **rich vs thin at p = 0.0032**, replicated at a 1,200-word
threshold.

That ordering is the theory's, exactly. `rich` is machine-written **with a purpose and an audience
specified**, so it should carry the prompt-writer's intent and rank above `thin`. `averaged` is
generated then rewritten twice — *"the latent space is a graveyard of idiosyncrasies, ground down
into a frictionless paste"* — and it ranked lowest of all.

**A measure that ranks two machine-written sets differently by how much intent was put in is an
intent measure, not a machine detector.** I called it the most important result of the project.

---

## §2. It is type-token ratio

**The shuffle control.** Randomise the word order within every text: vocabulary is preserved
exactly, all structure is destroyed.

| | human−thin | rich−thin |
|---|---|---|
| intact | +0.0775 (p = 0.0005) | +0.0083 (p = 0.0032) |
| **word-shuffled** | **+0.0725 (p = 0.0005)** | **+0.0115 (p = 0.0032)** |

**The effect survives shuffling unchanged.** It is not reading order, structure, or hierarchy —
those were destroyed and it did not notice.

And directly:

> **`scale_gain` vs type-token ratio: rho = −0.879, p < 0.0001.**
>
> human TTR **0.470**, rich **0.571**, thin **0.606**.

The model repeats itself less than people do. Less repetition means less compressible, which lowers
`scale_gain`. **The whole result is lexical repetition wearing hierarchy's name.**

**Retracted.** §1 is not evidence about intent.

---

## §3. The part that is worse than the result

`results/density_VERDICT.md`, written **this morning**, after the first version of this measure died
to a length confound:

> The space of surface statistics on text is dominated by **length, register and vocabulary**.
> Anything computed from raw text will mostly measure those unless each is explicitly controlled.

I controlled length. I did not control vocabulary. **I wrote the warning and then walked into the
next item on my own list**, and the thing that caught it was a control I only designed because the
first failure had happened.

Seventh instrument. The confounds so far, in order: denominator instability, dimensionality,
sample size, scale mismatch, **length**, and now **vocabulary**.

---

## §4. So this becomes a standing requirement

> **The shuffle test.** Any measure computed on text must be run on word-shuffled text before it is
> believed. Shuffling preserves vocabulary and length exactly and destroys everything else.
>
> **A measure that survives shuffling is a vocabulary or length statistic**, whatever it is called
> and whatever theory motivated it.

It costs one line and it would have caught this in the first minute rather than the fifteenth. It
is now the second entry in the confound checklist, beside the length correlation that `run_wall.py`
already runs before its verdict.

---

## §5. What did survive, and it is not nothing

**Function words separate human from no-maker at 93.1%** (chance 50%), and separate `rich` from
`thin` at 83.3%. Those numbers are *also* vocabulary-flavoured — function-word rates are a
vocabulary statistic by construction — but that channel has an external validation the density
measure never had: **7.6× host identification and 2.05× within-author across works**, on tasks with
known answers.

**The `rich` arm is now the sharpest instrument in the project** and it was worth building for that
alone. It is machine-written with a purpose specified, so:

> Any measure that ranks `rich` with `thin` is a machine detector.
> Any measure that ranks `rich` toward human is doing what this project claims to do.

Every future measure gets run against it. That is the test that separates the two things this
project has always insisted are different, and until today there was no way to run it.
