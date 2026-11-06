# AUTH source: prospective full-run allocation

This records an allocation revision before the first full source run. The original
[source design](AUTH_SOURCE.md), native validation, timing attempt and its cost
shortfall remain unchanged. No source algorithm, cohort, provenance rule, seed,
word limit, expected output or scientific gate changes. No paid call is admitted.

DESIGN CHECK: LESSONS sections 2–5 read for this build. Under either null or
alternative, exact completed output and fresh replay must agree; any disagreement
refuses completion. This is cost admission only, with no scientific outcome.

The completed timing task costs 24.15625 CPU seconds including fresh verification.
Scaling the whole task by 990/99 and then doubling gives 483.125 CPU seconds for
full execution and replay. This is larger than the execution-only fourfold
projection of 438.75 seconds. Use the larger bound. The old 300-second combined
timing/full slice cannot admit this forecast, and that shortfall is recorded.

Allocate a 500-second component cap to the unchanged full task, from unspent
FIC1 CPU time. This is not a ceiling extension: the original shared 7,200 seconds
remain enforced. Carry all previous charges: 4,013.4375 historical seconds,
120 reserved for this source build/tests, 0.546875 native validation, and
24.15625 timing. Reserve another 30 for this allocation's validation, giving
4,188.140625 charged/reserved before full execution. Retain 600 additional
seconds for later AUTH construction and calibration. The admitted sum is
5,288.140625, leaving 1,911.859375 seconds within the original allocation.

**The case and its check.** Full preparation keeps all original 990 sessions from
24 writers and authenticates both completed sources, full documents and identity
metadata. Every candidate and summary receives fresh-process independent replay.
The whole timing task—not selected fast rows—determines the forecast.

**The smaller route.** No reduced paid cohort or weaker source check. If this
bounded full task cannot complete, preserve all outputs and stop at its component
cap for explicit recorded diagnosis. No automatic cap increase is implied.

One counted CPU slot, one numerical thread, 2 GiB projected memory, 128 MiB output,
1,500-second wall safety cap and existing terminal monitoring. Pair allocation,
known-answer authorship discrimination and paid admission remain separate gates.
