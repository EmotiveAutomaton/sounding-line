# D-0 — FAIL

**2026-08-03. 48/48 generations succeeded. Verdict as pre-registered.**

| | ratio | categories > 2.0 | threshold |
|---|---|---|---|
| all cells (4 purpose × 4 affect) | **0.78** | **0** | pass needs > 1.5 and ≥ 3 |
| purpose only | **0.09** | 0 | |
| affect only | **0.19** | 0 | |

**Function-word vectors do not separate artifacts written under specified maker states.**
The feature channel option D was going to invert is wrong as designed. D does not proceed.

Cost: about forty minutes, against the 2–3 days D would have taken.

---

## What it does not license, and the discipline point

The per-cell numbers contain a pattern, and it has to be reported without being used:

**first-person-singular rate, pooled across purposes**

| affect | I / 1,000 |
|---|---|
| rage | 13.8 |
| fear | 13.7 |
| care | 6.8 |
| seeking | 5.7 |

That is a 2× split in the single most documented function-word signal, in a direction that is not
absurd — self-reference rising with grievance and anxiety, falling with outward-directed care and
absorbed curiosity.

**And it did not pass, because within-group variance swamps it.** Even for `i` alone the
between/within ratio is 0.5. With k = 3 per cell, "weak channel" and "underpowered test" are not
distinguishable, and **noticing that after a failure is exactly the move this project forbids.**
The threshold was set before the run. It was not met. D does not proceed on a post-hoc look at a
pattern I went looking for after seeing the verdict.

What is legitimate: a **new** pre-registration, run separately.

> **D-0b.** Affect only, purpose held fixed, k = 10. 40 generations, ~30 minutes.
> Pass condition set before it runs, not inherited from D-0.

---

## The reading that is more interesting than the failure

D-0 asked whether **a language model instructed to adopt a state** produces state-separable
function words. It does not. There is a mechanistic account of why, and it is the project's own
distinction:

> The model has no **leaked** layer, because it has nothing unchosen. Every token it emits is
> selected. Told to be angry it writes angrier *content*; it has no involuntary production to bend.

Function words leak in humans because they are produced below deliberation. A system with no
below-deliberation has nothing to leak.

**Which makes D-0's failure a prediction about the contrast, not a dead end.** If human artifacts
show state-separable function-word profiles and machine artifacts do not, that difference is a
discriminator — and it is one built on *absence of involuntary production* rather than on any
surface quality, which is exactly the property E40 says a surface measure cannot have.

**This is a new hypothesis, not a rescue.** It needs human artifacts with known maker states, which
this project does not have and which C-14 has owed from the start. Recorded, not acted on.

---

## Kept

- 48 generations at `generations.json` — a small fixed-topic corpus with known specified states,
  reusable by anything that wants machine text with labels.
- one anomaly, unexplained: `persuade|care` ran 729 words against ~380 everywhere else.
