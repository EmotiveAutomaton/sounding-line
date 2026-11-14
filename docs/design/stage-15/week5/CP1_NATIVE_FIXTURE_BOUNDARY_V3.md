# CP1 native-fixture phase boundary

Prepared November 13, 2026, before native admission. The V2 numerical/consumer
modules passed all nine targeted constructed checks. Their bytes remain fixed.
The V1 failure, V2 test receipt and earlier fixture modules are retained.

Static packaging review identified a fixture-only boundary issue: the V2
wrapper called the full consumer verifier during execute. A later native
verification could therefore reuse that already populated replay directory.
Targeted same-process checks were valid as reported; this does not establish
that a native verifier had recomputed the complete consumer in a fresh process.
No native fixture had been launched and no human-source verdict is affected.

`week5_cp_native_fixture_v3` is a thin successor. Execute prepares the explicit
synthetic source/gate envelopes, runs the V2 consumer and the three full planted
worlds, and writes only an execute receipt. Formal native verify rebuilds the
source/markers in a separate formal-source tree, independently repeats the
manual-gate arithmetic, invokes the consumer's complete fresh replay for the
first time, then recomputes all three 2,000-draw worlds. Cooperative yield keeps
the authenticated formal checkpoint prefix. No raw source, statistic, seed,
model, threshold or numerical tolerance changes.

**DESIGN CHECK.** Execution and independent verification are separate claims.
A same-process replay must not masquerade as first computation in the native
verifier. The owner must run this exact wrapper in a counted producer/fresh-
verifier chain before native qualification. This wrapper has static syntax
checks only; that native proof is outstanding. Human source/manual instrument,
scientific definition review, cost and resource admission remain outstanding.
