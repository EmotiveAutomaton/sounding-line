# What a control licenses — and what the shuffle test does not

**2026-08-05, at the curator's challenge.** Written after ten measures had been killed, six of them
by the shuffle test, and he asked whether the shuffle test is itself a confound.

> I actually don't think the shuffle test is going to be correct... shuffling inherently is a whole
> bunch of decisions, just by definition. But obviously randomness can't be the thing that we're
> detecting, because randomness is kind of the part of the problem and it's everywhere right now.

**He is right that something is wrong, and the specific wrong thing is worse than he guessed.** It
is not that shuffling adds decisions. It is that the shuffle test has been asked two different
questions and is only entitled to answer one of them.

---

## §1. What the shuffle test actually proves

Take a text, permute its words, re-measure.

> If `measure(intact) ≈ measure(shuffled)`, the measure is a function of the **word multiset** and
> almost nothing else.

For a **statistic computed directly from the text** — a function-word rate, a type-token ratio, a
count — this is not an empirical finding. It is close to a tautology, and it is airtight. A
permutation preserves the multiset exactly, so any statistic defined on the multiset is provably
invariant. If it moves, it wasn't. If it doesn't, it was.

**That is the whole of the shuffle test's authority, and it is real.** Nothing below takes it back
for the six lexical measures it killed. Those deaths stand.

---

## §2. The premise underneath it was never checked, and it is wrong

The project has treated the verdict `VOCAB` as automatically disqualifying. Look at why we thought
that, because the reasoning was never written down:

    a measure is "vocabulary" → it reads register, topic, genre → confound → dead

The middle step is an assumption. **Vocabulary is not one thing.** It is at least two:

| | | verdict should be |
|---|---|---|
| **register / topic / genre** | the artifact is a recipe, a legal notice, ad copy. Words follow from the category, not the maker. | **dead — this is the confound** |
| **word choice** | this maker, in this situation, reached for *this* word and not the near-synonym | **not dead. This is a decision channel.** |

**Word choice is where decisions live.** The entire theory of this project says a maker leaves marks
by choosing; choosing a word is choosing. A statistic that reads word choice and nothing else could
be a perfectly good intent detector, and the shuffle test would call it `VOCAB` and kill it.

So the shuffle test is a **proxy** for the confound we care about, and it is a proxy that
over-fires. It catches the thing we want dead *and* the thing we want.

**The non-proxy version already exists and we already run it.** Hold register, topic, format and
generator constant *by construction* and the confound cannot enter — there is nothing for it to vary
along. That is exactly what the ladder does, and it is what C3 did when it found commercial copy
sitting 26% of the way from essays toward machine text. **Construction beats ablation.** Where the
two disagree, construction wins, because it removes the confound instead of trying to subtract it.

---

## §3. Where the shuffle test is not merely a bad proxy but invalid

For a **model-internal measure** — anything read out of a reader's activations — shuffling is not an
ablation at all.

A permuted text is not "the same text minus order." It is **word salad**: ungrammatical,
out-of-distribution for any language model, and unlike anything in the corpus the reader's
directions were fitted on. Feeding it to the model does not subtract order from the measurement. It
moves the measurement to a different operating point, and then we compare across the two points as
though they were commensurable.

**The layer-ratio data says this happened.** Both arms moved *upward* under shuffling:

| | intact | shuffled | change |
|---|---|---|---|
| human | 0.6965 | 0.7854 | **+12.8%** |
| machine | 1.0547 | 1.2197 | **+15.6%** |

A clean ablation has no reason to inflate both arms by a common ~14%. That common-mode shift is the
model responding to nonsense — low-order layers keep doing lexical work while high-order layers have
nothing left to predict, which is precisely the ratio going up. And once you notice the shift, the
"121% survival" dissolves: **in proportional terms the gap barely changed at all** (−0.409 of the
mean intact, −0.433 of the mean shuffled). The gap was carried along by the shift, not tested by it.

> **Retraction.** `results/layer_ratio/VERDICT_CONTROL.md` concluded the layer ratio "is a
> vocabulary statistic." **That conclusion is withdrawn** — the shuffle test was not entitled to make
> it about a model-internal measure.
>
> **What survives is C3**, which is a construction control and never depended on shuffling: half B
> (commercial copy) sits 26% of the way from half A toward machine, p = 0.0033. The gap tracks
> register. So the layer ratio **is still not a human/machine discriminator** and still must never be
> reported as one. That verdict is unchanged; only its reason is.

Two of the ten dead measures were model-internal and were killed partly on shuffle evidence. They go
back to **unresolved**, not to alive. See `docs/LEDGER.md`.

> ### Follow-up, same day — the sweep ran, and it settles this
>
> `results/shuffle_sweep/VERDICT.md` measured the human/machine gap at all four grains:
>
> | | paragraph | **sentence** | phrase | word |
> |---|---|---|---|---|
> | gap retained | 103% | **99%** | 104% | **127%** |
>
> **The three in-distribution grains agree to within five points; the word grain diverges by 27.**
> That is the argument of this section turned into a measurement — the word shuffle's inflation is
> real and quantified.
>
> **And the conclusion it was not entitled to was correct anyway.** The gap needs no discourse order
> at all, so the layer ratio is **settled dead** as a human/machine discriminator rather than
> unresolved. The retraction improved the reasoning, not the answer. The other model-internal measure
> remains unresolved.
>
> Both replacements are now in service: **sentence shuffle** as the order test, and a **positive
> control** (Delta author ID, 6.89× identical at all four grains) gating the harness.

---

## §4. The randomness worry, in the form that survives

The curator's own framing — *shuffling is a whole bunch of decisions* — does not hold as stated. A
seeded permutation is maximum-entropy and goal-free; there is no maker and nothing is being pursued.
It is not decision-dense, it is decision-*free*.

**But the version one step over is a serious threat, and it threatens a whole class of designs:**

> A reader cannot tell "many decisions" from "unpredictable" without a model of what the decisions
> were *for*. Any measure whose implicit definition of intent is *departure from expectation* will
> score **noise as maximally intentional**.

This is N28 with the sign flipped. N28 asks whether a measure moves where there is nothing to
measure. This asks whether a measure **peaks** where there is nothing to measure — which is worse,
because the no-maker controls are quiet artifacts and would never catch it.

And it is not hypothetical. Every surviving candidate is at risk: `purpose_breadth` is a posterior
entropy, and a reader shown word salad should be maximally uncertain, i.e. maximally "broad."

### The control this implies — and it is better than the thing it replaces

**Rung −1: put the shuffled text on the ladder as a sixth rung, below rung 0.**

    a good measure ranks:   shuffled  ≤  rung 0  <  rung 1  <  ...  <  rung 10
    a bad measure ranks:    rung 10   <  shuffled

**If word salad scores above the most-specified rung, the measure is reading unpredictability and is
dead — regardless of what its rho against rung was.** That is a sharper, cheaper, more decisive test
than asking whether an effect "survives shuffling," and it uses the same shuffled texts we already
generate. It reuses the ablation as a **calibration point** rather than as a subtraction, which is
the only role the ablation is actually valid for.

---

## §5. Replacements, for when an order-sensitivity test is genuinely wanted

Full-word shuffling is the most violent possible perturbation. When the question is *does this
measure need structure*, ask it at a granularity that stays in distribution:

| | what it destroys | what it keeps | good for |
|---|---|---|---|
| **paragraph shuffle** | argument order | everything else | document-level structure |
| **sentence shuffle** | discourse flow | grammar, local coherence, register | **model-internal measures — this is the one to use** |
| **phrase shuffle (5-word windows)** | syntax | local co-occurrence | syntactic dependence |
| **full word shuffle** | everything | the multiset | **lexical statistics only** |

Run all four and you get a **curve instead of a verdict** — the granularity at which a measure lives.
That is strictly more information than a binary survival number, costs one extra pass, and would have
told us months of what we learned one measure at a time.

---

## §6. The hierarchy, stated once

Every future control declares which of these it is, because they license different claims.

1. **Construction** — vary one thing, hold the rest fixed by building the corpus that way.
   *The ladder, C3, within-author splits.* **Strongest. Removes the confound.**
2. **Matched comparison** — find pairs that already differ on one axis.
   *Early vs late works by one author.* Strong, but matching is never perfect.
3. **Null population** — measure where the quantity is absent.
   *N28, the no-maker corpus.* Catches measures that move on nothing.
4. **Ceiling population** — measure where the quantity is absent but the *surface* is extreme.
   *Rung −1, shuffled text.* **New. Catches measures that peak on nothing.**
5. **Ablation** — destroy a property of the input and re-measure.
   *The shuffle test.* **Weakest, and valid only when the ablated input stays in the measure's
   domain.* For text statistics: valid. For model readouts: not.

**A measure dies to a level-1 or level-2 control. A measure is only ever made *suspect* by level 5.**

---

## §7. What this costs us

Honesty about the bill. Softening the shuffle test does **not** revive the corpus of dead measures —
six of them were lexical statistics where the shuffle test is exact, and `scale_gain` was type-token
ratio no matter how you control it. The ceiling on function words is still author identification.

What it changes is smaller and specific: **two model-internal measures were retired on invalid
evidence and are now open questions**, the ladder is confirmed as the only comparison that has ever
been properly controlled, and there is one new control that is better than the one being demoted.

**The instrument did not get better today. The method did.**
