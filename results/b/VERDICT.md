# B′ — the directions are real; the artifact readings are not

**2026-08-03.** Qwen2.5-1.5B, CPU, 29 layers, eight concepts, four fitting sentences and two
held-out per concept.

---

## B′-1 · PASS, with three caveats stated

**50.0% held-out classification against 12.5% chance — 4.00×**, at layer 1, standardised.
Binomial p = 3.0e-4 single test, **8.7e-3 corrected for the 29 layers searched**.

**Not lexical.** Bag-of-words centroids on the identical held-out sentences: **12.5%, exactly
chance.** The activations carry something the vocabulary does not.

**Caveats, all of which bear on how much to believe it:**
1. **n = 16.** Two held-out sentences per concept.
2. **The layer was chosen post hoc** across every layer. The corrected p is the one to quote.
3. **Per-concept accuracy is very uneven** — `fear` 100%, `none_recoverable` 100%, four at 50%,
   and **`grief` and `lust` at 0%.** Two of eight concepts are not detected at all.

### What the first run got wrong, and it was all mine

| | |
|---|---|
| **arbitrary layer** | I used `n_layers // 2` = 14. It is the **worst layer in the model** — 18.8% raw. |
| **no standardisation** | Raw cosine follows the known high-magnitude "rogue" dimensions instead of the concept. Every concept collapsed onto `none_recoverable`: 12.5%, chance exactly. |
| **the runner stopped on FAIL** | before printing the layer sweep — the one diagnostic a failure needs. Same shape as the D-0 mistake: I keep building the verdict path and not the *why* path. |

Standardising and sweeping: **12.5% → 50.0%**, same sentences, same model.

---

## B′-2 · Weak. The layer structure exists but barely moves

Early/late affective activation ratio on the contrast sentences: **1.15 to 1.75**, varying by
concept. Not 1.0, so the layers are not doing identical jobs — but small, and on sixteen sentences.

Accuracy across depth is **bimodal**: high at layers 0–1, a dip through the middle, a second rise
at 22–27. Two loci rather than a gradient, which is closer to the low-order/high-order split than a
monotone story would be. **But layer 0 is the embedding layer**, so the early peak is likely
near-lexical whatever the bag-of-words control says, and the late peak at 22–27 is the one far
enough from vocabulary to be worth trusting.

---

## B′-3 · FAIL. And the failure is diagnostic

Eight Gate 3 artifacts:

| | |
|---|---|
| **peak concept** | **`lust` on all eight.** Every artifact, both halves. |
| **early/late ratio** | 1.98 – 2.17. Half A mean 2.01, half B mean 2.12. |

**`lust` scored 0% in validation.** A direction that cannot identify its own held-out sentences
winning on every real artifact is not a reading — it is the direction picking up something generic.
And the ratio has almost no variance across eight artifacts of two supposedly different kinds,
which is what a measure looks like when it is reporting a property of *the input format* rather
than of the input.

### The likely cause, and it is the same mistake a third time

**Directions were fitted on ~12-word sentences and applied to 4,000-character artifacts.**
A mean-pooled activation over 512 tokens is a different object from one over 15 tokens — different
norm, different composition, different everything. The projection is dominated by that shift.

That is the third instance today of *the instrument not matching the object*:

| | mismatch |
|---|---|
| **D-0** | statistic assumed a stable per-sample rate; 380-word samples gave five tokens |
| **G** | univariate statistic on a signal that lives in the joint distribution |
| **B′-3** | directions fitted on sentences, applied to documents |

---

## What would fix it

**Fit the directions on passages of the same length as the artifacts.** That needs affect-labelled
text of 2,000+ words per concept — which is exactly what **D-0b** needs, and exactly what the
project does not have.

Cheaper interim, and worth trying first: **window the artifact** into sentence-length spans, project
each, and aggregate. That keeps fitting and application on the same scale without needing any new
labelled text, and it turns the reading into a *per-span* quantity — which is what the emotion-
concepts paper says these representations natively are (*"local... tracking the operative emotion
concept at a given token position"*). I built the document-level version when the paper had already
said the representations are local.

**Nothing from B′-3 should be quoted.** B′-1 stands.
