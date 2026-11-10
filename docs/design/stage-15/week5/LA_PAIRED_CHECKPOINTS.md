# LA paired producer with masked checkpoints

Prepared November 8, 2026. This separate producer integrates the existing
within-act masked checkpoint primitive into the original paired language-act
reader. Prior producers, collectors, source preparation, admission scaffolds
and receipts remain unchanged. This document is a proposed engineering design;
its prepared fixtures have not executed.

## DESIGN CHECK

LESSONS 3–5 apply. The failure being prevented is losing a long act's partial
masked execution or independent replay at a cooperative resource boundary.
The constructed check compares the original paired producer with the successor
on identical inputs/configuration, including the original unsupported-history
case. It interrupts after a single original eight-position tensor batch,
retains the causal checkpoint, finishes both masked arms and separately
recomputes every masked batch. Changed source/model/checkpoint bindings,
missing selection, unknown options and missing guarding must refuse. Original
causal tolerance remains 1e-4 nats and masked vector tolerance remains 1e-5.
No scientific row, label, token position, model candidate or numerical gate is
dropped. Original LA1/LA2 definitions and the one-percent collection allowance
remain unchanged.

## Producer and original operations

`week5_la_pipeline_v5` authenticates completed primary AT2 selection and the
exact causal/masked manifests before loading. It calls the original causal
scorer at context 1024 in the frozen AT-FP64-1 specification. The existing
`week5_la_mask_checkpoints` primitive calls the unchanged original masked
kernel with float32 parameters, context 512 and batches of eight mask
positions. Original act values, INDEX and SUMMARY schemas/bindings are
preserved. Additional checkpoint and producer provenance is separate.

Each act has independent execute and verify causal receipts. A resumed act
warms the original prefix cache and checks the saved causal value by the
original fresh-forward check before retaining it. Masked execution and replay
use distinct sealed prefixes. Dedicated masked-yield exceptions become paused
results, never unsupported observations. Only the original explicit support
errors can be recorded as unsupported. Completed independent act replay has
its own seal binding the original act and every immutable within-act file;
resume can skip that already verified act only if those bytes still match.
An original unsupported act has no completed masked RESULT: independent replay
repeats the original refusal path instead of demanding an invented result.
The constructed empty-history act specifically exercises this distinction.

The default invocation quantum is 32 new mask batches or 600 wall seconds,
including cold loading and causal work; options permit at most 128 batches and
1200 seconds. The complete configuration remains part of the original
scientific input binding and must stay identical across continuation. A
checkpoint after the final tensor batch may still pause before reduction;
the next invocation authenticates its prefix and completes the reduction.
The first completed COST receipt is retained, and all invocation costs,
including failures, partial execute, partial verify and repeated cold loads,
remain additive evidence. Native accounting including startup is authoritative.

## Existing native guard integration

`week5_la_scoring_guard_v1` invokes the existing
`week5_at_precision_guard.run` code through a private function namespace.
Its exact native identity, polling, seven-GiB request thresholds, six-GiB hard
floors and sixty-second cooperative grace are unchanged. Only per-invocation
guard-receipt destinations are namespaced so repeated constructed calls in one
process cannot overwrite each other. No global module is patched.

Before each individual model load, the adapter additionally applies that same
original admission predicate: at least 26 GiB of system commit headroom and
20 GiB of available RAM. The second check occurs with the causal reader
resident. A refusal preserves its actual identity and snapshot, writes a
cooperative request and prevents the next load. The unguarded producer refuses
to load either model without this hook. The guard does not infer a paired peak
from isolated AT weight size or measurements and does not establish a safe
forward latency by itself. Hard termination retains its evidence and cannot
be relabelled a valid checkpoint.

## Prepared qualification sequence

1. `week5_la_pipeline_v5_fixture` requires the actual completed constructed
   AT-collection-v4 and LA-v4 idempotence proofs. Actual tiny causal float64
   and masked float32 models exercise original-output equality, within-act
   execute/replay pauses, a local copied partial checkpoint, completed COST
   reentry and input/checkpoint/unguarded/collector refusals. Before-load and
   between-load controls use explicitly synthetic headroom; they are not
   paired pretrained memory measurements. Every outer native verification uses
   a new execute-only checkpoint copy and recomputes all masked batches.
2. `week5_la_paired_chain_fixture` consumes the first fixture only after its
   real native COMPLETE and fresh verification. One act has two total masked
   batches and a fixed two-new-batch quantum. Attempt A must pause execution;
   B must preserve the runtime-authenticated copy, finish execution and pause
   independent verification; C must preserve both prefixes and finish fresh
   verification. The owner must use actual stopped identities, all-attempt
   accounting and the reviewed runtime continuation adapter. Neither local
   copied directories nor these prospective templates assert a native chain.

For review, each bounded constructed attempt proposes ceilings of 600 CPU
seconds, 900 wall seconds, 3 GiB and two numerical threads. These are unmeasured
qualification ceilings, not forecasts. All fixtures remain unexecuted here;
no test, model/source execution, native start, commit or ACK was performed.

## Remaining admission gates

The existing collector deliberately rejects the new producer identity. An
explicit, reviewed collector successor must authenticate this exact guarded
producer, all numerical/input pins and completed execute/replay provenance
before any mixed or full score bank is accepted. The original bounded-source
and selected-reader admission scaffolds likewise do not accept this identity.
Those successor integrations are still pending, not silently waived.

Human admission additionally requires the corrected complete ten-reader AT2
bank and its admissible selected reader, fully qualified bounded LA source
preparation, the native original-output and A/B/C proofs, and actual paired
resource/cost measurements. Unknown quantities include two simultaneous model
peaks, transient cold-load commit, each causal and eight-mask forward latency,
source/checkpoint authentication latency, complete independent replay cost,
and remaining full-bank/whole-meeting pilot cost. The original largest AT
fresh-verifier hold and owner memory gates are not cleared by this integration.
The measured first-five-percent route and original card/family ceilings remain
mandatory; no forecast or smaller population is invented.
