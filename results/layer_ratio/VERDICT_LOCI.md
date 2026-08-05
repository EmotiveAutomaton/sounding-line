# Layer ratio at the validated loci — my hypothesis was wrong, and something bigger showed up

**2026-08-05.** Same measure, layers split at the **bimodal loci** (0–2 and 22–29) instead of into
thirds.

---

## The ladder got WORSE, which was the thing I predicted would improve

| | thirds | **loci** |
|---|---|---|
| rung vs ratio | −0.339, p = 0.016 | **−0.275, p = 0.053** |
| shuffled | +0.121 | **−0.043** |
| vs word count | +0.284 | +0.347 |
| verdict | AMBIGUOUS | **AMBIGUOUS** |

**I argued the thirds split was diluting the signal with the dead middle. It was not.** The loci
split is weaker on the ladder and the p-value crosses 0.05 the wrong way. That reasoning was wrong
and the twenty minutes settled it.

*The shuffle control did get cleaner* — −0.043 against −0.339 intact. Still the only measure here
that needs word order.

---

## And the human/machine separation grew by an order of magnitude

| | thirds | **loci** |
|---|---|---|
| human | 2.0945 | **0.7142** |
| rich | 2.1194 (p = 0.09) | **0.9963 (p < 0.0001)** |
| averaged | 2.1742 | **1.0811 (p < 0.0001)** |
| thin | 2.1939 | **1.0866 (p < 0.0001)** |
| **human vs thin, relative** | **4.7%** | **52%** |

**Human text sits at 0.71 and every machine kind sits near 1.0.** All three now significant,
including `rich`, which was not before.

And the ordering holds and sharpens:

    human 0.71  <  rich 1.00  <  averaged 1.08  <  thin 1.09

`rich` — machine-written **with** a purpose and audience specified — is the machine kind closest to
human, and it is now separated from `thin` rather than sitting on top of it.

---

## THE CONTROL THIS IS MISSING, AND IT IS THE ONE THAT HAS KILLED NINE MEASURES

**Only the ladder was shuffled. The human/machine comparison was not.**

Human artifacts are real web pages; machine artifacts are generated prose on twelve topics. They
differ in register, topic, formatting and provenance all at once. **A 52% gap between two
populations that differ in everything is exactly the shape of a confound**, and the shuffle test on
*that* comparison has not been run.

**Nothing in the human/machine numbers above may be quoted until it has been.** The ladder's
shuffle result does not transfer — the ladder holds register and topic constant by construction and
the human/machine comparison holds nothing constant at all.

That check is the immediate next run and it is cheap.

---

## What stands regardless

**The ladder verdict is AMBIGUOUS on both splits** and the pre-registration says that licenses
nothing. Two splits, two ambiguous results, and the better-motivated split was the worse one.

**The measure still needs word order**, on the one comparison where it was tested. That remains the
only thing separating it from the nine measures that came before.
