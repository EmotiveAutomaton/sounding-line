# V4.c atomic telemetry monitor recovery

DESIGN CHECK: LESSONS sections 3–5 reread on October 30 before this repair.
Under either scientific null or alternative, a vanished atomic JSON temporary
file is not a missing result. Missing ordinary artifacts, permission errors,
resource shortages, changed pins and exceeded byte/CPU limits still refuse.

Shard zero stopped because the v5 output-size monitor called `is_file()` and
then `stat()` on a temporary progress file that had been atomically replaced
between those calls. The parent exception closed its contained worker. The
failed attempt, stderr, job accounting and checkpoint bytes remain preserved.
This is engineering healing attempt one, with no changed scientific estimand.

A separate v6 supervisor uses one `stat()` per enumerated path. Only a missing
name matching the existing writer's `.json.<32 lowercase hex digits>.tmp`
format is tolerated. Every existing regular file, including temporary files,
counts toward the original cap. Deterministic race/refusal tests and actual
native execute/verify and cap-refusal rehearsals precede recovery dispatch.
The first test invocation could not access its default temporary directory;
that environment failure is retained, followed by a fresh workspace-local run.

Resume in a new root from authenticated reference/seal pairs and their exact
binding. Copy the original model and observed-statistic records unchanged;
the original consumer reconstructs and compares these on entry. Unsealed
partial files are retained only in the old root and recomputed. Seeds, inputs,
model, statistic, original gates, 110 outer worlds, 199 references per world,
and fresh complete independent replay remain exactly unchanged.

The failed attempt's 944.8125 CPU seconds remain charged. A conservative
300 CPU-second repair reservation covers the bounded native rehearsals,
regression tests and operational preparation; measured costs are retained
separately and must fit this reservation. Deduct both amounts from shard
zero's original 174598 CPU-second reservation. No other shard reservation,
collector reservation, global ceiling, margin, stage boundary or gear changes.
Unused repair reservation is not automatically returned to execution.

Three healthy v5 workers continue on immutable original sources and retain
failure monitoring. Their runtime exposure is recorded; no healthy worker is
restarted to refresh a report or clock. If another fails, inspect its actual
cause and charge before any separately recorded recovery. The collector must
use the explicitly reconciled roots and include all failed-attempt and repair
charges before admission. No partial scientific verdict is licensed.
