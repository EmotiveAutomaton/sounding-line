# FIC1.h1 exact context-cache validation

Frozen before execution, October 29. This is Week 3 section 0.3 B(3)'s
separately labeled cheaper exact implementation at the parent's rank, within
the original FIC1 allocation. It changes no estimand, population, context rule,
control, reference count, nuisance fit, scoring rule or scientific gate.
Original modules and failed attempts remain retained and unmodified.

DESIGN CHECK: LESSONS sections 3–5, CONTROLS sections 1–7 and G220's section,
correction and afterword were reread. Under both prompt-only and planted-writer
construction, every cached context output must be byte-identical to canonical
JSON from the original implementation. Any difference fails engineering
admission; no numeric tolerance or selected-output comparison substitutes.
Missing support must stay missing. A speedup without parity is unusable.

Reuse the original arithmetic functions. A per-instance private data snapshot
binds all cached values. The cache key is the exact sorted donor-session list,
final-versus-typed mode and exact prefix quota. Cache at most 128 donor measures,
evicting least-recently-used entries. Cache original support and writer folds
once from that same snapshot. Reconstruct assigned observed profiles, literal
leave-writer-out profiles, all independent donor contexts and all nuisance fits
for every draw. Never skip context construction because a downstream consumer
currently ignores a returned field. Do not coalesce or reorder timing masses.

Targeted checks cover full canonical output equality, changed assignments,
cache eviction, unsupported donor prefixes, caller input/output mutation,
independent-instance isolation and refused role-crossing assignments. Compare
the original and cached implementations on both existing nine-writer raw-event
worlds, the identity and draws 0 through 31, then repeat draw 0 and identity.
Each native verification independently reconstructs those complete worlds and
both implementations in a fresh process. Retain full parity hashes and raw
timings, without scientific scores. Source and test bytes are pinned.

Charge 120 CPU seconds for construction, targeted tests and timing against the
previous cumulative 3,826.234375 seconds. Native execution plus fresh replay
has a 300-second component cap, admitted only if a measured forecast fits it.
One numerical thread, 3 GiB projected RAM, 128 MiB output. The original total
ceiling remains 7,200 CPU seconds; no S4 extension is invoked. An exhausted
component cap retains evidence and does not authorize an automatic retry.

This handler is constructed-only. Corpus parity, complete-corpus timing, full
scientific calibration and whole-study cost admission remain separate gates.
Passing these constructed checks alone does not authorize human identification
or AUTH. No claim of speedup is made until measurement completes.
