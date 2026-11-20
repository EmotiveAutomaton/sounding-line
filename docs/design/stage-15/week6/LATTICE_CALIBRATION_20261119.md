# LT1: prospective source-level calibration

Curator ruling, 19 November 2026. This amendment governs the lattice extension's
section 3.10. It is frozen before opening any new lattice row's results. The
packet's 44 predictions and every requested count remain intact. The already
seen ES1 interaction table is the packet's declared prior exposure; it is not a
new lattice result. Nothing here changes an individual study or its verdict.

The curator approved the following rule:

> Keep all 44 predictions and all counts. Label the coin-toss calculation
> descriptive. The combined set may be called passing only on a dependence-aware
> calibration, fixed before any lattice row is read.

## Primary

For each source, divide the number of decided rows on their predicted side by
that source's number of decided rows. An interval must exclude zero strictly to
be decided; touching zero is undecided. Invalid, unsupported and unrun rows keep
their dispositions and reasons but do not enter either count.

The primary statistic is the number of sources with a strictly greater than
one-half share on the predicted side. Its denominator is every source with at
least one decided row. A tied source therefore stays in the denominator without
a success. MIDUS waves two and three are one source; diary members 0057 and 0056
are separate sources. Use the exact upper fair-binomial tail over these source
votes and the declared 0.05 threshold. Zero eligible sources cannot pass.

All 44 rows must have a final disposition before a combined verdict is issued
at the campaign freeze. Preserve the raw decided/predicted counts and the
source-and-claim grouped counts and coin tails as descriptive calculations.
Multiple dependent rows never multiply a source's primary vote.

## Secondary, only from already computed diary draws

Where each source has an authenticated common whole-person draw bank, use its
existing 2,000 draws, with no new data pass and no refitting. Orient each column
by its frozen prediction, subtract that column's bootstrap mean, and retain the
entire vector of row effects together within each source. For each null vector,
translate the centred column's 2.5th-percentile offset by that vector's effect;
count a predicted-side decision when the translated lower limit exceeds zero.
Compare the observed number of predicted-side decisions with this reference.

Combine source count vectors using independent fixed permutations, seed
20261119, and report the plus-one Monte Carlo tail with 2,000 reference draws.
This operationalizes the requested sign reference by recentering the existing
joint draws, preserving their within-source dependence. It does not run an
additional model or claim that bootstrap rows are independent observations.
Missing or incompatible draw provenance cannot be repaired by fresh fits.

The secondary is optional. If it would cost more than one diary card's 20,000
CPU-second allowance, or the existing draws cannot support it, file the primary
alone and state the reason. It cannot rescue a failed primary.

## Required limits and validation

The source-level count still assumes independent sources and fair signs under
the null. The return must state that every row shares the rival it cannot rule
out: self-report in one sitting. Where a row uses conduct, preserve that
measurement distinction beside this required set-level warning.

DESIGN CHECK: LESSONS sections 3–5 read for this design. Null: duplicating perfectly
correlated rows within one source cannot create additional primary votes.
Alternative: six independently counted sources all favouring predictions have
an exact upper tail of 1/64. Exhaustive boundary checks cover zero decided rows,
ties, zero-touching intervals, negative predictions, invalid diagnostic intervals,
both MIDUS waves, and all 44 preserved dispositions. The shared-draw reference
must preserve perfectly correlated columns and must refuse missing provenance.
Constructed checks validate computation, not source independence or a human
mechanism. No new lattice results were read to choose this rule.
