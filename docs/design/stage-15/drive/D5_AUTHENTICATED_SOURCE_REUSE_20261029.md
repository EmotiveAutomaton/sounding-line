# D5.h1 v2: exact reuse at both completed producer boundaries

The first exact-reuse source paused at its unchanged cumulative cost guard.
Retain it, all partial outputs, source versions and charges. This cost version
also reuses the completed P2 timeline instead of recomputing that existing
producer for each D5 execution. PMAP and P2 are completed, authenticated sources;
their original inputs remain pinned, and their unit hashes must match.

## DESIGN CHECK

LESSONS sections 3–5 read for this build. NULL and ALTERNATIVE use the identical
retained source population and transform. Both complete source producers are
checked before D5 uses their fields; raw source hashes are still checked per
session. Every new D5 view is independently reconstructed in a fresh process.
No upstream completion, source hash, identity, span coverage, token equality or
immutable output check is removed. This is fresh D5 replay, not a new full raw
P2/PMAP reconstruction; the summary explicitly names both source reuses.

Before dispatch, require exact complete-payload parity for every saved session
from both stopped attempts, plus real producer integration and one fresh raw
timeline comparison. This tests reuse against the earlier replayed values.
The constructed full handler, reentry, mutation refusal and yield path remain.
No population, model, bin, matching rule, scientific gate or statistic changes.

Keep the same 3,600 cumulative CPU-second source probe, with all prior attempts
and test charges. Combined execution/replay cap is 2,400 CPU seconds; wall cap
4,500 seconds. The first-tenth forecast still covers both passes with the same
factor of two and can pause this version. No automatic retry is planned. If
this also fails admission, move to the next independent commissioned card.
Identification and its scientific controls remain separate, uncomputed work.
