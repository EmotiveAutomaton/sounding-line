# W-1 — the wall is not visible as displacement, in a model that has no self to be displaced from

**2026-08-04.** Qwen2.5-1.5B, CPU, 20 Gate 3 artifacts against 3 generated, fixed 200-word windows,
late layers only.

| | |
|---|---|
| human | 0.2884, sd 0.0151, n = 20 |
| generated | 0.2932, sd 0.0085, n = 3 |
| difference | **−0.0049**, p = 0.53 — generated displaced *slightly more* |
| | **FAIL** |

**No length confound this time: rho = −0.205, p = 0.35.** The measure is clean. The answer is that
the reader does not move further from its resting state for a human maker than for machine content.

W-2's spread went the predicted way — generated sd 0.0085 against human 0.0151 — but on **n = 3**,
where a smaller spread is close to meaningless.

---

## The model was the wrong one, and that is my error rather than a rescue

The mechanism this test is built on, from the emotion-concepts paper:

> The model tracks emotions of story characters temporarily during narrative generation, **then
> returns to representing its assistant persona's emotional states afterwards.**

**That was measured on Claude Sonnet 4.5 — a large, instruction-tuned model with a strong assistant
persona.** "Falls back to its own persona" requires a persona to fall back to.

**Qwen2.5-1.5B is a base model.** It has no assistant persona. It was never trained to be anyone.
So the quantity W-1 measures — distance from the reader's own resting state — may not have a
referent in it at all, and a null is what you would expect whether or not the wall exists.

That is the same class of error as choosing layer 14 because it was `n_layers // 2`: **a parameter
picked for convenience, in a place where the choice was load-bearing.** Third time today.

---

## What is retested and what is not

**Retest:** the same design on an **instruction-tuned** model, which has the persona the mechanism
requires. Queued.

**Not rescued by this:** if the instruct model also returns a null, the reading is that displacement
from baseline is the wrong operationalisation — not that the model is too small again. One named
reason gets one retest.

**And n = 3 is the deeper problem.** Three generated artifacts cannot carry this whatever the model.
The no-maker side of every control in this project is three artifacts written for Gate 1, and that
is now the binding constraint on four separate measures. **Generating a proper no-maker set is
cheap and has never been done** — it is the smallest unblocked thing on the list.

---

## What the measure did establish

The confound discipline worked. `results/density_VERDICT.md` was a length measure that survived
twenty minutes; this one had the length check built into its pre-registration and came back clean
at rho = −0.205. **The instrument for deciding what is true is holding**, which is the only thing
that has held all day.
