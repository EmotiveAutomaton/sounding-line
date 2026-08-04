# Leakage, recomputed with the statistic that works

**2026-08-03, after G showed the univariate separability measure was broken.** Every number in the
earlier run of this was computed with it and is void.

---

## The corrected results

**Burrows' Delta, nearest centroid, leave-one-out, on the Gate 3 corpus. No model, no GPU.**

| question | accuracy | chance | lift |
|---|---|---|---|
| **Half A vs Half B** | **84.3%** | 50.0% | **1.69×** |
| **which host produced this** (10 hosts, 25 artifacts) | **76.0%** | 10.0% | **7.60×** |

Half A recovered at 82.1%, Half B at 87.0% — balanced, so it is not one class swallowing the
other.

**The earlier reading of this file said the channel "DOES NOT separate — within-half variance
dominates", on a ratio of 0.27. That was the statistic failing, not the channel.**

---

## §1. The host result is the validation that matters

Function words identify *which website produced an artifact* at **7.6× chance** on 25 real web
pages of 1,500–3,500 words.

That is the channel working **on this corpus**, at these lengths, on modern web text — not only on
19th-century novels. It is the evidence that G's finding transfers, and it cost nothing.

---

## §2. The A/B result is a baseline Gate 3 now has to beat

**84.3% separation of the two halves, from a CPU measure with no language model in it.**

Gate 3 is spending eleven hours of GPU establishing whether a model-based measure separates those
same halves. **Whatever it returns is now measured against 84.3% from function-word counting.**

That is not a claim that the halves differ in *intent*. It is the opposite kind of claim, and the
confound is obvious and severe:

> Half A is personal essays and technical writing. Half B is commercial pages. **Those differ in
> register**, and register is exactly what function words encode alongside everything else. An 84%
> classifier here may be reading nothing but *blog post vs sales page*.

Which is precisely why it is a **baseline** rather than a result. A measure that claims to read
intent should beat one that reads register, or explain why it does not.

---

## §3. What is still not licensed

- **Nothing about affect.** These are not affect labels and the channel has never been mapped to
  the family's values.
- **Nothing about the halves' intent content.** See §2's confound.
- **Nothing per-artifact.** These are classification accuracies over a set. The per-artifact
  deviation numbers in `leakage.json` were computed against a corpus-mean baseline and remain the
  weaker version of the question — the per-maker baseline the books corpus now supplies is the
  right one and has not been applied here yet.
