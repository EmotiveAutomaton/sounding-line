# LA paired-reader completion reentry

Status: prepared, unexecuted, not admitted. Source inspection found that the
frozen v3 LA scorer writes elapsed `COST.json` after reading a completed score
bank. A repeat execute after completion but before independent verification
therefore compares a different elapsed duration against the immutable original
receipt. This is the same accounting pattern as the repaired AT reentry; no
LA human scoring result or observed LA runtime failure is claimed.

## DESIGN CHECK

Reviewed lessons 3--5, 2026-11-07. The case is complete scoring followed by an
operating pause before verification. The check reenters exactly that completed
execute, preserves every numeric byte and the first cost receipt, then performs
fresh causal and masked forwards. Partial-act yield and continuation remain.

The smaller route is the already bounded constructed fixture. No successful
subset, numerical tolerance, model, source cohort or inference is substituted.
Production still needs complete primary AT2 selection, measured paired-model
peak memory and counted cost/pilot admission under the original LA ceiling.

`week5_la_pipeline_v4.score` runs the exact v3 function code object with a
private globals mapping. The only altered write is an already present, valid
completed cost receipt: it is checked and retained. This does not patch the
old module's globals or files. All other writes, model loading, context,
scoring, masks, refusal rules, array comparisons and resource-yield checks are
the original code. The predecessor code hash is required. Each invocation,
including yields, exceptions and repeated verification, adds its own immutable
cost record; native total accounting including startup remains authoritative.

The collector accepts only exact v3/v4 producer modules, authenticated plans,
required numerical source pins and pinned input files. The original float64
causal specification, original float32 masked computation, direct-forward
tolerances and one-percent unsupported allowance remain unchanged. Missing,
unknown or incompatible producers refuse. The resulting numeric projection
and summary are the original collector's output, with producer provenance in
a separate sidecar. Existing v3 attempts and sources stay immutable.

## Proposed counted proof

`week5_la_pipeline_v4_fixture` consumes only the completed constructed AT
collection fixture and its selected-reader receipt. It loads actual tiny
constructed causal and masked transformers, never pretrained human readers or
participant text. It exercises partial-act interruption, unchanged resume,
complete-execute interruption before verify, completed execute reentry and a
fresh paired numerical verification. An original v3 execution on identical
inputs must produce byte-identical act scores. A mixed exact v3/v4 bank must
equal the original all-v3 collection. Unknown producers, absent pins and
negative cost receipts are refused on constructed copies.

The outer counted runtime performs independent replay. Its nested completion
receipts are explicitly constructed dependency fixtures, not production
admissions. Proposed envelope: LA family, 600 CPU seconds, 900 wall seconds,
3 GiB projected peak, two numerical threads, CPU only. Owner review and a
committed design precede any start. No new fixture has been executed yet.
