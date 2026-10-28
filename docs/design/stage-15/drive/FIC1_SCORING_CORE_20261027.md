# FIC1 fixed-support scoring and reporting core

This is the next component of the commissioned FIC1 comparison, not a new
scientific card or a repair of a failed gate. It validates scoring arithmetic
on explicit constructed inputs only. It neither loads human features nor
claims that the still-unbuilt context reconstruction is valid. The existing
exact profile rebuild and gallery-only nuisance fit remain unchanged.

The scorer uses the existing B-only gallery scaling, missing-feature handling
and fractional tie credit. A declared gallery never shrinks between observed,
context and reassigned arms. Every required writer must appear in every score
map. An unsupported reference draw invalidates the entire fixed 1,000-draw
reference; no successful-only mean or probability is computed. Nonfinite or
out-of-range scores and duplicate writer declarations refuse.

The empirical one-sided probability uses the plus-one rule and includes ties.
The context contrast is formed by subtracting the two scores for each writer
before the 2,000-draw writer bootstrap. The gallery stays fixed. A variant
clears the numerical admission rule only when its permutation probability is
below 0.05 and its paired context interval is above zero. Equal arms must yield
exact zero and no admission; an inverse signal cannot pass the positive rule.
This numerical decision does not certify the provenance or construction of
either control. The complete consumer must separately require their validated
bindings and full calibration.

Genre comparisons pair the same declared writers. Retain the existing exact
two-sided McNemar diagnostic and its two-by-two table. Fractional ties make
that binary diagnostic unsupported, rather than inventing discordant counts;
the paired fractional accuracy difference remains available. No tie breaker
or second estimator is introduced.

Before any human score, freeze the length rule as follows. Use the raw profiles
at 500, 1,000, 2,000 and full words, with the same all-length, both-genre writer
roster prepared earlier. The full-length covariate-adjusted comparison remains
separate: changing adjustment across curve points would confound evidence
length with the transformation. For each genre and channel, report all four
accuracies, the paired full-minus-500 interval, and the linear slope across
the four ordered levels. Continue that channel's interpretation only if both
genres have strictly positive endpoint gain and positive slope. A flat curve,
including a ceiling tie, stops that instrument's length interpretation; an
unsupported roster is recorded as unsupported. This is an operational reading
of the packet's 'accuracy rises' condition, not an additional significance
claim. It is frozen before outcomes and does not waive either control gate.

Known-answer checks cover constant ties, identity fingerprints, fixed-gallery
support, exact zero, reverse direction, complete and incomplete banks, paired
genre arithmetic, fractional ties, rising/flat/falling and misleading hump
curves, order invariance, malformed inputs and immutable replay. The native
handler accepts only a marked constructed fixture and replays its complete
result in a fresh process. Corpus scoring is deliberately unavailable through
this handler until the full consumer and its controls are admitted.

LESSONS sections 3–5, CONTROLS sections 1–7, the play-frame theory row and its
afterword were reread for this component. The earlier timing pass charged
1,907.78125 CPU seconds including reserves. Reserve another 120 seconds for
construction and targeted checks, and cap native validation plus replay at
120 seconds, one numerical thread and 2 GiB projected RAM. These charges remain
inside the original 7,200 seconds. S4 permits one cumulative extension up to
14,400 seconds if the eventual complete measured forecast requires it; this
component does not invoke that extension or admit the full scientific run.

Remaining: pooled context reconstruction, independent-donor rotations and
nuisance refits, coherent reference banks, full-pipeline calibration, whole
design cost admission, and the separately gated AUTH primary. No source,
failed scientific gate, locked file or existing output is changed.
