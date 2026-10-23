# GEN1: retain extraction across the combined wall bound

This is an engineering continuation of the
[frozen comparison](GEN1_COMPARISON_20261023.md), not a changed experiment.
The real feature source pass is slower than the constructed rehearsal. At
255.65 elapsed wall seconds it had reconstructed 326 of 990 matched sessions;
at about 466 seconds it had reconstructed 610. A full extraction plus fresh
replay therefore projects beyond its frozen 900-second combined cap. Do not
alter that live plan or source. Preserve its exact completed extraction if
the supervisor interrupts verification at the cap.

The continuation is admissible only after the original worker has exited,
with a recorded combined-wall TimeoutError during the verify phase, a complete
RESULT matching SUMMARY, all matched sessions/words retained, and every original
source/code pin and input binding intact. Any other failure, incomplete extraction
or original COMPLETE refuses continuation. Copy the six completed output files
byte-for-byte, then reconstruct every source and feature in a fresh native
verification process using the unchanged normalized-path extractor. No outcome
is computed in the feature component. Do not promote copied checkpoints before
this replay passes. A completed original component is never restarted.

Known-answer checks include byte-exact reuse/full replay and refusal of another
failure class, an interrupted execute phase, a previously completed component,
changed pins and incomplete rows. Complete native rehearsal precedes dispatch.

The original one-CPU-hour ceiling remains the conservative 1,800 wall seconds;
S4's single cumulative extension permits at most 3,600. All original attempts,
both replay phases and continuation time count. Retain the prior 279.617759
seconds, the 150-second build reservation, the 49.634831-second path failure,
and another 120-second conservative reservation for continuation validation.
That is 599.252590 seconds before the current attempt's actual cost. Only the
remaining cumulative allowance may be dispatched. A continuation may receive
at most 1,200 seconds and must reserve at least 60 for later comparison admission;
the statistical run is separately admitted from measured remaining allowance.

The brief's original scientific question, feature boundaries, controls, frozen
galleries, support, seeds, thresholds and final-packet policy do not change.
No new paid work, GPU start, hypothesis or family counter follows.
