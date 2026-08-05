# LEXICAL — the word shuffle got the right answer for the wrong reason, and now we have it for the right one

**2026-08-05.** The replacement for `results/layer_ratio/VERDICT_CONTROL.md`'s retracted C1.
Pre-registration in the header of `runners/run_shuffle_sweep.py`, written before the run.

---

## §0. The positive control, run first, gating everything below

Burrows' Delta on author identification — a forty-year-old known answer, and **provably
permutation-invariant**, so no grain can legitimately move it.

    intact      68.9% vs 10.0% = 6.89x
    paragraph   68.9%  = 6.89x   ok - invariant
    sentence    68.9%  = 6.89x   ok - invariant
    phrase      68.9%  = 6.89x   ok - invariant
    word        68.9%  = 6.89x   ok - invariant

**Identical to the digit at every grain.** This validates the measure pipeline *and* the four
shuffling functions simultaneously, before any real number is computed. It is the check that would
have caught `separability()` four dependent results earlier, and it is now standing.

---

## §1. The sweep

Human (n = 30) against the no-maker set (n = 36), layer ratio, all four granularities:

| grain | human | machine | gap | p | vs intact |
|---|---|---|---|---|---|
| **intact** | 0.7142 | 1.0547 | **−0.3405** | 1.96e−15 | — |
| paragraph | 0.7125 | 1.0641 | −0.3517 | 1.26e−15 | **103%** |
| **sentence** ← verdict grain | 0.7178 | 1.0547 | **−0.3369** | 1.97e−14 | **99%** |
| phrase | 0.7545 | 1.1093 | −0.3549 | 1.26e−13 | 104% |
| word | 0.7887 | 1.2226 | −0.4338 | 5.83e−16 | **127%** |

> **LEXICAL.** The gap retains **99%** of itself when every sentence is reordered, and **103%** when
> paragraphs are. **The human/machine gap needs no discourse order whatsoever.**

---

## §2. The curve validates the retraction *and* reverses its practical effect

Both things are true and both should be said.

**The methodological point stands, and this measures it exactly.** The three grains that stay *in
distribution* agree tightly — **99%, 103%, 104%.** The word grain jumps to **127%**. That divergence
is the artefact `docs/method/CONTROLS.md` §3 predicted: word-shuffled text is out of distribution for
the reader, and the measurement moves to a different operating point rather than being ablated.
**The original "121% survival" was ~27 points of that artefact.** The word shuffle was not entitled
to its verdict.

**And the verdict it was not entitled to was correct anyway.** Three independent in-distribution
grains say the gap is fully lexical, and **C3 — a construction control that never used shuffling —
already named the mechanism**: commercial copy sits 26% of the way from essays toward machine,
p = 0.0033.

> **I retracted a conclusion and the re-run confirms it.** The retraction improved the reasoning, not
> the answer. That is worth recording plainly rather than dressed up: the honest gain here is a
> *method* that now produces defensible verdicts, and one measure's status clarified — **not** a
> result rescued.

## §3. What is now settled, and what is not

| | |
|---|---|
| **the layer ratio as a human/machine discriminator** | **DEAD.** No longer "unresolved." Four independent lines agree: three in-distribution grains plus C3. It must never be reported as one |
| **the layer ratio on the ladder** | **still live, and still the only order-dependent effect in the project.** Rung effect −0.275; paragraph and sentence shuffling leave it untouched; phrase-shuffling costs a full ladder span |
| **the two-component account** | **strengthened.** Where register is free, the measure is 100% lexical. Where register is fixed by construction, what remains needs *local* order. Both halves are now measured rather than argued |
| **the word shuffle** | retired for order-sensitive measures. Retained for permutation-invariant statistics, where §0 shows it is exact |
| **the sentence shuffle** | adopted. Stays grammatical, stays in distribution, destroys only the order a reader uses to follow an argument |

## §4. What would have falsified this

The gap collapsing under sentence-shuffling — which would have made this the first order-dependent
effect on *human* text and would have reopened the whole human/machine leg. It did not; it moved by
1%.

Or the positive control failing: if author ID had not returned ~7× identically at every grain, the
shuffling code would have been wrong and none of §1 would be readable.
