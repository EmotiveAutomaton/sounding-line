# AT completed-score accounting recovery

The first guarded large precision control finished execution and then paused
before fresh verification because its declared memory admission margin was not
available. Its successor authenticated the complete score checkpoints but
failed when the original scorer attempted to write new elapsed times over the
first immutable `COST.json`. This is an execution/accounting defect. Preserve
the completed scores, original cost, guarded pause, failed continuation and all
charged CPU. No numerical tolerance, precision, population, context or forward
sample changes.

## DESIGN CHECK

**The case and its check.** A completed score batch may be reentered after the
verification child was refused before model loading. The scoring-v5 successor
executes the exact code object from frozen scoring-v4, interposing only its
completed-cost write. If a valid original cost exists, its bytes must remain
identical; reentry validates every sealed score, token identity, reconstruction,
index and summary exactly as before. The fresh verifier still runs the original
seeded two-percent uncached forward comparison at the unchanged 0.0001-nat gate.
Every invocation, including yield and exception, writes a separate private
process-cost receipt. Runtime accounting, including startup and every prior
attempt, remains authoritative; a historical cost is never substituted for the
new invocation's cost.

The known-answer fixture first runs the actual original-v4 handler on a tiny
constructed GPT-NeoX model. It completes all rows, then deliberately exercises
the unchanged native guard's insufficient-headroom refusal before verification.
A new attempt copies every immutable output, reenters execution with v5, and
independently verifies the original score bytes. The fixture requires the first
cost and all scoring outputs to remain byte-identical and both successor phase
costs to exist. Its inputs are literal constructed character-token rows; real
case inputs are prohibited. Constructed memory snapshots exercise guard control
flow and do not certify actual memory availability for the large model.

**The smaller route.** No sample or numerical relaxation. A failed original
cost schema, altered completed output, numerical mismatch or insufficient
native resource margin refuses. Large human-case verification waits for the
original margin and owner admission. The successor still loads the same model
once during execute reentry to perform its original token reconstruction checks;
it reuses the sealed forward scores and does not recompute them in that phase.
Fresh verification remains a separate model invocation.

`week5_at_precision_case_v2` substitutes only scoring-v5 in the frozen case
wrapper. `week5_at_precision_guard_v2` substitutes only that case in the frozen
guard body. The 26-GiB commit and 20-GiB available-RAM start thresholds, six-GiB
hard floors, seven-GiB cooperative trigger, sixty-second grace and exact owned
native identity remain unchanged. Original modules and all old receipts remain.

`week5_at_precision_resume_fixture` exposes the stable counted-fixture contract:
`inputs.failed_root` points to the explicitly constructed input bundle and
`config.mode` is `counted_resume`. The first verification intentionally yields.
Its authenticated continuation uses the ordinary unchanged resume contract,
then returns `verified: true` after complete fresh checking. A local copied
fixture proves only local behavior; an actual counted runtime chain must also
pass before owner admission of the large continuation.

The scientific numerical binding remains `AT-FP64-1`: same pinned float32
tensors converted exactly to float64 model computation, same float32 predictive
reductions, context and tokenizer. This accounting repair supplies no selected
reader or scientific result. Bank collectors and downstream admission must
explicitly recognize the successor producer before accepting its outputs.
