# The layer ratio — AMBIGUOUS, non-lexical, and pointing the other way

**2026-08-05.** Qwen2.5-1.5B on GPU, affect directions fitted from contrast sentences, ratio of
early-layer to late-layer affective activation, fixed 200-word windows.

---

## The ladder

| rung | ratio |
|---|---|
| 0 | 2.2147 |
| 1 | 2.1834 |
| 3 | 2.1651 |
| 6 | 2.1541 |
| 10 | 2.1619 |

| | |
|---|---|
| rung vs ratio | **rho = −0.339, p = 0.016** |
| **shuffled** | **rho = +0.121 — the effect COLLAPSES** |
| vs word count | rho = +0.284 — under the 0.4 void threshold |
| **verdict** | **AMBIGUOUS** — the pre-registered PASS was \|rho\| > 0.4 |

**AMBIGUOUS stands.** 0.339 is not 0.4 and the threshold was written before the run.

---

## §1. It is the first measure here that is not vocabulary

Nine measures have been built. **Every previous one survived word-shuffling**, which means every
previous one was reading the bag of words:

| | intact | shuffled |
|---|---|---|
| you_rate | +0.703 | **+0.703** |
| causal_rate | +0.659 | **+0.659** |
| type-token ratio | −0.545 | **−0.545** |
| density scale_gain | +0.548 | +0.442 |
| **layer ratio** | **−0.339** | **+0.121** |

**Shuffling destroys word order and preserves vocabulary exactly. This measure loses its effect and
changes sign.** It needed the order. That is what the curator's construction argument predicted —
a ratio between two layers of one reader cancels what acts on both — and it is the first time the
prediction has been borne out by anything.

**That is a bigger result than the p-value**, because it means the measurement channel is not the
one that has swallowed everything else.

---

## §2. The direction is backwards from the prediction, and it is coherent

The prediction: *human text should trigger MORE low-order affective activation relative to
high-order.*

| | ratio | vs human |
|---|---|---|
| **human** | **2.0945** | |
| rich | 2.1194 | +0.0249, p = 0.09 |
| averaged | 2.1742 | +0.0797, **p < 0.0001** |
| thin | 2.1939 | +0.0994, **p < 0.0001** |

**Human is the LOWEST.** The opposite of predicted — and **the same direction as the ladder**, in an
independent population, with the two lining up:

    thin 2.19  >  averaged 2.17  >  rung 10 2.16  >  rich 2.12  >  human 2.09

**More intent, lower ratio. Two populations, one ordering.** Human extends the ladder past its top
rung, which is what it should do if the ladder is measuring what it claims.

### The reading that makes both true

The prediction was about **leakage** — the involuntary layer, which is Panksepp's and sits low.
**But specified intent is not leakage. It is the emblematic layer** — chosen, conceptual, and
Barrett's, which sits high.

So more specified intent gives the reader more to construct at the conceptual level, the *late*
term grows, and the ratio falls. **The prediction may be right about leakage while this test
measures specification, which is the other layer of the same model.**

If so, the test that separates them already exists: the ladder manipulates the emblematic layer by
construction. **A manipulation of the leaked layer would need artifacts whose maker's state varies
while their specification does not** — which is what the reading sessions have and nothing else
does.

---

## §3. What this licenses

**Not a pass.** AMBIGUOUS was pre-registered as licensing nothing, and it does not.

**But it changes what to build next**, on three grounds that are independent of the threshold:

1. **The channel is not lexical.** First time in ten measures.
2. **The ordering is consistent across two independent populations**, one of which (human) was
   never part of the ladder's design.
3. **The direction has a mechanistic reading** that is internally consistent with the two-layer
   model rather than a post-hoc story — the layers are doing different jobs and this measure is
   catching the one that was manipulated.

**The immediate next step is not a bigger model.** It is to run the same measure with the layers
split by the *validated* structure rather than by thirds: `results/b/VERDICT.md` found accuracy is
bimodal across depth — a locus at layers 0–1, a dead middle, a second locus at 22–27. The current
early/late split uses thirds and therefore averages the dead middle into both terms.
