# CH1 cooperative filler successor

This operational successor retains [CH_PIPELINE](CH_PIPELINE.md) and
[CH_ANALYSIS](CH_ANALYSIS.md), the exact source roster, Stockfish 19, fixed
node limits, one thread and 64 MB per engine, and all numerical acceptance.
The original source, scorer and native receipts remain immutable. No human
positions may run before the complete source census and frozen sample verify.

## DESIGN CHECK

LESSONS 3–5 apply: authenticate the producer/consumer boundary, distinguish
partial counts from complete populations, preserve saved bytes, and exercise
actual native pause and continuation. Under both null and alternative inputs,
owner yield must retain a consecutive score prefix; missing, changed, duplicate
or extra records must refuse. A copied verification prefix earns no independent
replay credit. Single-legal-move and unique-mate boards retain their exact known
answers. No gate depends on a human association or its sign.

## Execution and verification

`week5_ch_engine_bounded` uses the unchanged scorer's method through a subclass
whose only change is a 20-second engine transport timeout. A position has at
most two fixed-node searches, leaving the supervisor's 60-second cooperative
grace available when an engine becomes unresponsive. Such a timeout retains an
interruption; it never substitutes a shallower score. Two single-thread engines
serve both execution and independent fresh-process verification.

Each batch binds a disjoint roster interval of at most 1,024 positions. At most
600 wall seconds of new scoring start before sealing an ordinary filler batch;
the supervisor enforces 1,800 combined wall seconds, including complete replay.
The packet's 2,500,000 CPU-second family ceiling accounts for every attempt.
The first actual source batches supply measured cost; a constructed fixture
cannot admit the full 400,000-position cost. The sample itself remains unchanged
when a batch seals early; the next disjoint batch begins at its recorded offset.

An owner yield or position quantum returns `yielded` with a preserved prefix.
A new attempt may copy only the runtime's authenticated complete checkpoint
manifest. Both handlers check owner requests between every pair of positions.
An exactly copied predecessor request is retained and recognized as historical
by `RESUMED_FROM.json`; any different request interrupts. Completed scores are
never replaced. The resumed execute handler recognizes its sealed batch, while
verification recomputes every score from ordinal zero in fresh engines.

The native fixture must cover a counted partial pause and complete continuation,
the actual child and monitor interfaces, strict fresh replay, unchanged original
bytes, an owner pause during verification, late changed requests, and damaged
input/score refusal. The existing collection consumer still requires the whole
frozen population exactly once. A separate planner adapter accepts this
successor's authenticated completed batches without weakening original checks.

## Cost and scope

The short constructed integration proof is capped at 300 CPU seconds per
attempt and charged to CH. Production batches retain the combined 1,800-second
wall bound and no more than two numerical threads. No GPU, model service,
network transfer, paid call, scientific estimator or public claim is introduced.
If a batch cannot fit, preserve its checkpoint and use a smaller operational
position quantum under the same frozen interval and family accounting.
