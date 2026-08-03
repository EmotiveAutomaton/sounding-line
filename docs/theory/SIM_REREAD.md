# What the simulation says that this project is not doing

**Re-read 2026-08-03, while Gate 3 was running.** Source: `ghost-scale-sim` — the essay
(`docs/theory/Art_a_unifying_model.md`), `FINDINGS.md`, and this time **the model code itself**,
which had not been read before: `observer.py`, `creators.py`, `v6_model.py`, `v6/e36_process.py`,
`v9/minimal_models.py`, `v10/e55_intent_gate.py`, `docs/versions/v10-reader-as-defence/SPEC.md`.

Previous passes read the *findings*. This one read the *implementations*, and the implementations
carry constraints the findings do not state.

---

## §1. The missing control — N28 has no analogue here

This is the sharpest thing in the re-read and it bears directly on Gate 3.

E36's method-unlock result is only interpretable because of a null called **N28**:

> At mu = 1 there is no process to recover — every execution mode emits the goal signature exactly
> — so process recovery must sit at chance whatever the goal recovery is. **If it does not, the
> measure is reading goal information and is goal recovery renamed**, which is precisely the trap
> depth itself was built to avoid.

And the verdict file carries a kill switch:

> `NULL N28 FAILED. Process recovery is not at chance where there is no process, so the measure is
> reading goal information and every number above is uninterpretable.`

**Gate 3's card has N11, N12, N13. It has no N28-analogue.** There is no artifact class in the
Gate 3 corpus where unlock must be 1.0 by construction. Without one, a significant G3.1 cannot
distinguish *"unlock measures method recovery"* from *"unlock measures some property of purpose,
verbosity, or length that happens to differ between the halves."* G3.5 catches length only.

The card is locked and this cannot be added now. It is a **limitation to state in the Gate 3
report whatever the outcome**, and it is the first thing a successor design owes.

**It is checkable off-corpus.** The three generated artifacts are locked and already exist. They
are the closest available "no reconstructible maker" case. Running unlock on them touches neither
the Gate 3 corpus nor the card. If unlock on generated content comes out high, E36's warning
applies to this instrument directly.

---

## §2. The unlock statistic is not E36's statistic

| | E36 | Sounding Line |
|---|---|---|
| quantity | `process_error_reduction` — mean log P(true mode) minus log(1/n) | `decisions_after / decisions_before` |
| kind | signed information measure against ground truth | unbounded count ratio, no ground truth |
| value when nothing moves | exactly 0 | exactly 1.0 |
| effect found | "roughly doubles" after the goal settles | 1.28 vs 0.92 (pilot) |

The direction was inherited correctly. The **measure was not**, and E36's own file explains why
that matters — it rejected the count-style statistic explicitly:

> The first implementation used ACCURACY. That was wrong... accuracy measures "how often did this
> artifact happen to be in mode zero", which is not a chance-level statistic and came out at 0.15
> against a nominal 0.25 — **BELOW chance, which no amount of information could produce**... It is
> the fourth instance in this project of an instrument answering a nearby question.

**This is not a fixable oversight.** E36 has ground truth about the maker's execution chain;
Sounding Line reads real artifacts and has none. Error reduction is not computable here. But it
means the unlock number is a **weaker quantity** than the one the prediction was derived from, and
must not be quoted as though it were the same measure.

---

## §3. The theory has an axis this project does not measure — and C-22 is about it

The unifying model is explicitly **two** axes:

- **X — artfulness.** Decision density, including decisions compressed into automaticity.
- **Y — good/bad.** *"Whether the artist met the goal implied by the actions taken... you, the
  viewer, get to decide what their goal was... and you get to decide if they met it."*

Everything Sounding Line measures is X-ish. Under the flattened-intent hypothesis (C-22),
commercial work sits **high on Y** (it meets its single goal very well) and plausibly high on X
too. What separates it is neither axis.

The essay gestures at the missing dimension without formalising it, under **goal layering**:

> The question of whether the chair is art has to do with whether the creator just wanted to meet
> simple base requirements... **or whether they had complex goals of their own they were optimizing
> towards by layering interlocking decisions.**

That is C-22, in the source document, from before this project existed. It is not a new
hypothesis — it is an unformalised part of the original model, and `purpose_breadth` is the closest
thing anyone has built to it. **F-3 is a test of the theory's own unbuilt axis**, not a rescue.

---

## §4. The user's automaticity correction traces to source

The correction — *"high expertise should produce the same number of visible decisions"* — is the
essay's position, not a departure from it:

> Decisions are counted individually, **including subordinate and previously addressed solutions**.
> Every decision matters. / Automaticity is the caching of human struggle.

And `v6_model.py:self_report_accuracy` records the author's own correction to the working note:

> The working note said the subconscious holds the process goals. It holds the **PRACTISED** ones:
> recently acquired, poorly modelled skills are held consciously and can be reported, and it is the
> tightly compressed, heavily automatised structure that becomes inaccessible to its own author.

So E43 is: compression removes decisions from the *maker's report*, not from the *artifact*, and
the reader is unaffected. Any measure that reads expert work as having fewer decisions is measuring
the maker's self-account, which no artifact contains.

---

## §5. The architecture is matched to the wall, not to the A/B split

Version 9's minimal-model programme strips one structural commitment at a time:

> **All of them rest on one.** No surviving finding outlives replacing the maker-modelling reader
> with a surface classifier. Hierarchy and costly attention are free — no finding needs them. And
> **the wall is the only finding that needs the reader to hold a distribution** rather than a best
> guess, which is exactly right, because the finding *is* a claim about the shape of a posterior.

The probe holds a purpose posterior. Per MIN, that machinery is **required** for exactly one
finding — E37's wall, *legible and empty*, non-invertibility — and is surplus to every other. Gate 3
tests A-vs-B separation, which by MIN a surface classifier could do.

**The instrument is well-built for the thing it is not testing.**

---

## §6. E55 is the reframe, and the stop condition does not block it

Version 10's Reader 4 — the project's only constructive result:

> Absorption scaled by how well the maker was recovered. **No values anywhere.** ... it rejects what
> it cannot attribute a maker and a purpose to, and imposes no view about what anyone should want.
> **It also needs no social adoption, which was the entire practical objection to the Ghost Scale.**

Measured: cuts damage 23%, restores reading of genuine work 0.84 → 1.00, **costs nothing on a clean
corpus**, never reads the label, reproduces in 83% of random models. Against the same threat, a
surface-quality filter leaves a learner exactly as damaged as no filter (0.826 vs 0.827).

This is a different object from what Sounding Line currently is. Sounding Line is a **classifier of
artifacts**; Reader 4 is a **reader-side gate on absorption**. A gate does not need to separate
careful work from competent filler — it needs to refuse the non-invertible, which is §5's wall,
which is the one thing the architecture is right for.

**Gate 3's stop condition forbids rebuilding the measure and re-running on this corpus.** It does
not forbid a different claim requiring different evidence — and the card already says a successor
needs a corpus this project has not seen. E55's corpus is **grooming**, which is **C-14**, sourced
never. The sim's only constructive finding and this project's oldest unpaid debt are the same
corpus.

---

## §7. Two ceilings that were already known and are worth restating together

**E38.** A machine-matched reader scores 1.000 on machine content and 0.280 on human. The probe is
one. Half A is human content. This is a ceiling on G3.1, not a bug in it.

**E10 / E15.** Reader skill caps extraction, measured on a corpus with zero machine content
anywhere — and belief accuracy breaks down well before choice accuracy does. *"A rater's internal
picture rots while their picks stay right."* Which is the direct argument for C-20's second reader,
and for why agreement between the curator and the probe is not evidence either is right.

---

## §8. What this changes

Nothing about Gate 3. It is locked and running, and every item above either predates it or cannot
be applied to it.

What it changes is **what gets written afterwards**:

1. The Gate 3 report states the missing N28-analogue as a limitation, pass or fail.
2. Unlock is reported as a count ratio and never as E36's quantity.
3. Unlock on the three locked generated artifacts, as the nearest available no-maker control.
4. If G3.1 fails, the successor is **not** a fourth discriminator. It is E55's reader-side gate on
   a grooming corpus, aimed at the wall — the one finding the architecture is required for.
