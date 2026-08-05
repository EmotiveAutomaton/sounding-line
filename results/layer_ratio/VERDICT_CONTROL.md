# The 52% gap is vocabulary. The ladder signal is not. Both are true.

**2026-08-05.** Three controls on the human/machine layer-ratio result.

---

## C1 · Shuffle — the result dies

| | human | machine | gap |
|---|---|---|---|
| intact | 0.6965 | 1.0547 | **−0.3581** |
| **word-shuffled** | 0.7854 | 1.2197 | **−0.4343** |

> **Gap survival: 121%.** Shuffling made it **larger**.

Word-shuffling preserves vocabulary exactly and destroys all order. The human/machine separation
did not merely survive that — it grew. **It is vocabulary, and it is not subtle about it.**

**Tenth measure.** Retracted before it was quoted anywhere, which is the only thing to be said for
it, and the reason the control was run before the claim was made rather than after.

## C2 · Length — clean

rho = −0.274 against word count. Under the 0.4 void threshold. Not the problem this time.

## C3 · Register — and it says the same thing from a different direction

| | ratio |
|---|---|
| half A (essays, technical writing) | 0.6484 |
| **half B (commercial web copy)** | **0.7551** |
| machine | 1.0547 |

**Half B sits 26% of the way from Half A toward the machine kinds**, p = 0.0033.

Commercial copy is the human writing closest in *register* to generated prose, and it lands
proportionally closer to it on this measure. That is what a register effect looks like, arrived at
independently of the shuffle test, on data that was already in hand.

---

## The part that is not dead, and it matters

**The ladder is a different comparison and it behaves differently.**

| | intact | shuffled | survival |
|---|---|---|---|
| **human vs machine** | −0.358 | **−0.434** | **121%** |
| ladder (thirds) | −0.339 | +0.121 | ~0% |
| ladder (loci) | −0.275 | −0.043 | ~16% |

**The same measure, on the same model, with opposite results — and the difference is what the two
comparisons control.**

The ladder holds register, topic, format and generator **constant by construction**; only the
amount of specification varies. There, the effect **needs word order**. The human/machine
comparison holds **nothing** constant, and there the effect is entirely vocabulary.

> **The measure has a small non-lexical component and a large lexical one.** When confounds are
> controlled, only the small one remains. When they are free, the large one swamps it.

That is a coherent account rather than a rescue, and it makes a prediction: **any comparison that
does not control register will produce a large vocabulary effect on this measure**, and any that
does will produce something near the ladder's −0.3.

---

## Consequences

**The 7B run skips itself.** `run_queue_today.sh` gates it on `survival < 0.5`. A larger model
would measure the same confound more expensively.

**The ladder result stands where it was: AMBIGUOUS**, on two splits, at −0.275 and −0.339. It is
still the only thing here that has ever needed word order.

**And the ladder is now the only comparison worth running this measure on**, because it is the only
one that controls what has to be controlled. That is a real narrowing: the measure is not a
human/machine discriminator and should never be reported as one.
