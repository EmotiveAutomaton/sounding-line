# What the simulation returned, and what it costs Gate 3

**2026-08-03.** Six questions sent, six answered — S-4 and S-5 merged, for a reason that is itself
part of the answer. Full report: `../../FROM_GHOST_SCALE_SIM.md`.

**Mechanism only.** Nothing here says anything about real artifacts and none of it should be quoted
as if it did. What it can do is tell you whether a statistic behaves, in a world where the truth is
known — which is the one thing no corpus can do.

---

## S-1 · Gate 3's primary is broken. This is the headline and it arrived before the run finished.

| statistic | mean at mu = 1, where there is provably nothing to unlock | verdict |
|---|---|---|
| `process_error_reduction` (E36's) | −0.022, inside tolerance | reads zero, correctly |
| **concentration ratio** (threshold-free) | **17.65**, interval [4.54, 37.43] | **FAILS N28** |
| resolved-count ratio @ 0.90 | 0.11 | FAILS N28 |

> **A statistic that never consults the truth reports a 17× "unlock" in a world built so that there
> is provably nothing to unlock.**

And it does not track what it stands in for: **r = 0.086** with `process_error_reduction` across
rollouts. **Effectively uncorrelated. The primary does not inherit E36's support.** It has to earn
its own, and on this evidence it cannot.

And it is usually undefined: at any threshold strict enough to mean *a decision was recovered*,
**378 to 467 of 467 rollouts have a zero denominator.**

### Why, and this is the part that generalises

> This reader's belief about the maker's execution mode is **diffuse the entire way through**.
> Median sub-goal posterior entropy sits at 96.5% of maximum and never drops below 75% in 288 steps.
> Process recovery is a small log-probability edge over a broad posterior, never a confident
> identification.
>
> **The quantity is real and the counting is what breaks it.**

If the probe emits discrete "recovered decisions", it is thresholding something that never crosses
a threshold. A graded measure against a baseline survives where a count does not.

### What this means for tonight

Gate 3 finishes around 05:30. **Its primary is a count ratio.** Sounding Line's own control already
showed machine artifacts unlocking at 1.111 against commercial work at 0.917; the sim now explains
that as a ratio computed on a small unstable denominator rather than a difference between artifacts.

**The result should be scored with the locked script and then reported with this in front of it.**
Not suppressed — the card is locked and the number is the number — but a p-value on a statistic
that reports 17× where nothing exists is not evidence about intent.

**The fix is named by the mechanism**: score a graded log-probability against a baseline instead of
counting recovered decisions. That is a successor measure, on a corpus this project has not seen.

---

## S-2 · `purpose_breadth` works, at matched density. C-22 survives its first real test.

Same positions, same depth, same number of execution decisions — only the concentration of the goal
mixture differs.

| | flattened | layered | |
|---|---|---|---|
| **purpose_breadth** | **0.450** | **0.558** | **−0.108, interval excludes zero** |
| goal accuracy *(trap: must not fall)* | 0.858 | 0.792 | +0.067, n.s. |
| process recovery *(trap: must not fall)* | −0.012 | −0.007 | −0.005, n.s. |

**Neither trap fired.** Accuracy went slightly *up* — which is what the curator predicted, because a
flattened maker is easier to read, not harder. Process recovery held, so "flattened" has not
quietly become "shallower".

**The construct is not confounded with depth**, and no real corpus could have shown that, because
no real corpus can hold density constant.

**Warning attached:** on transparent material with a long look, entropy collapses to ~1e-10 in both
arms and the test measures nothing. **Expect the same floor effect** if `purpose_breadth` is
computed on easy artifacts.

---

## S-3 · The leaked layer is readable, and the shield claim holds

**State recoverable from the leak alone: 0.899 against 0.250 chance.** The layer is readable in
principle — not a dead end.

**Divergence identifies concealment** at every amplification, interval excluding zero throughout.

And the curator's counter-intuitive correction survives contact with a mechanism:

| shield amplification | detector accuracy |
|---|---|
| 1× | 0.845 |
| 4× | 0.897 |
| **8×** | **0.963** |

> **Performing louder to cover up makes concealment more detectable, not less.** The shield is a
> readout of the thing it opposes, and amplifying it sharpens the readout.

*"The shield matches the leak"* was his correction to my first framing. It is now a mechanism.

---

## S-4 / S-5 · Merged. The reorder cannot change the answer, only the price.

Exact inference over the full joint is order-independent, so **no reordering can change the final
posterior** — confirmed empirically at exactly **0.000** difference over 540 paired rollouts.

**So the answerable question is cost, and there is a real effect:**

| arm | steps to settle | |
|---|---|---|
| forward | 9.06 | |
| anomaly-first | 8.63 | **−0.43, interval excludes zero** |
| reverse (method-first) | 8.49 | **−0.56, interval excludes zero** |

**Both reach the same answer sooner.** Under a reader that pays per look and can disengage, cheaper
*is* better — so the anomaly entry point is **a real efficiency and not a better inference.**

That is sharper and more defensible than what this project has been claiming. It also means
**S-4 does not refute the purpose-first loop**: the loop is right about where it ends up and merely
not optimal about how it gets there.

*Caveat carried over: half a step out of nine. A 5% saving, not a redesign.*

---

## S-6 · All three surface predictions hold, and the third is the one worth having

| creator | surface slope | content slope | |
|---|---|---|---|
| **practised** | **−0.0370** | −0.0057 | surface decays **6.5× faster** |
| novice | −0.0281 | −0.0299 | **both** decay |
| **synthetic** | **−0.0000** | −0.0000 | **surface does not move** |

> **The machine signature is not thin depth. It is a surface that does not move.**

A positive signature rather than an absence, which is worth more than any absence can be — every
detector already looks for absences.

**The honest caveat, from the sim itself:** the construction *builds in* the asymmetry it measures.
Content is cached and surface is not, by fiat. It is a consistency check on the theory's arithmetic,
not evidence that practice works this way in people. What it genuinely earns is the **direction of
the third prediction**, which does not follow trivially — a budgetless creator comes out *flat*
rather than merely *high*, and flat is testable.

**And it now collides with a reading-session finding.** The curator: *"when I've been talking about
the veneer in my head, I've been thinking about the imagery and iconography."* The sim's "surface"
is attention-density. Plain text has almost none. **S-6's prediction may not be testable on text at
all** until attention-density and register are separated.

---

## Score

| | |
|---|---|
| **S-1** | **the primary is broken.** Fails N28 at 17×, uncorrelated with the graded measure, undefined in 81–100% of cases. |
| **S-2** | `purpose_breadth` works and is not confounded with depth. C-22's first real support. |
| **S-3** | the leaked layer is readable; the shield claim holds and strengthens with amplification. |
| **S-4/5** | the anomaly entry is a **cost** win, not an accuracy win. Purpose-first is not refuted. |
| **S-6** | surface decay holds; the machine signature is a **flat** surface; partly built-in. |

Four of five sharpen claims the project already held. The fifth removes the one it was about to
report.
