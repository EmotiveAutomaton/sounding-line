# FR1.h1: preserve reused controls in the arm-label reference

25 October 2026. Pre-corpus control refinement, separately frozen.

FR1 permits the same single-dismissal control to be matched to several events
from one writer. Independent pair-level sign swaps would give those correlated
rows independent labels. The writer bootstrap already preserves the dependence;
the arm-label reference must preserve it too.

`week3_frames_analysis_cluster` changes only that reference: one sign per real
writer flips every paired occurrence together. The original raw sign-bank size
is still consumed, selecting the first draw belonging to each writer, so all
later full-profile fake assignments and paired bootstrap draws stay exactly
identical to the original seeded banks. The primary estimate and its interval,
the full-profile fake mean and the paired own-minus-fake interval are unchanged.
The 200-draw reference, descriptive probability and standing bias flag now use
the real writer as their exchangeable unit.

Original analysis files remain intact. This is an explicit `.h1` comparator
refinement, not a claim that the previous source failure produced a scientific
result. It shares the original FR1 3,600 CPU-second ceiling and its prior charges.

Three targeted checks establish exact preservation of primary/fake banks,
refusal to turn 100 repetitions from one writer into 100 independent labels,
scoped restoration after an error, and complete fresh-process constructed replay.
The full source requires the separately validated canonical-text recovery before
either source or statistical corpus dispatch. Owner native validation and
measured cost admission remain outstanding.
