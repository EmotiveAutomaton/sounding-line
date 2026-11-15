# Owner-reviewed remaining-reader queue design

Prepared implementation; native qualification remains pending. The owner selects a 32,000 CPU-second total envelope (31,970 outer plus 30 supervisor), based on measured complete-chunk and interruption costs. This supersedes the provisional 230,400 ceiling in the preserved builder design below. Actual remaining allowance and the original freeze/drain may further reduce it. No production start precedes qualification.

# Original m00 pilot, bounded queue v1

DESIGN CHECK — LESSONS §3–§5 read in full for this build. Under either a null
or alternative downstream association, all source, model, precision, checkpoint,
native identity, cost and fresh-forward gates are identical. Complete verified
chunks advance; resource or quantum requests yield; changed, ambiguous,
unverified or numerically invalid evidence fails. No gate has an unreported
band. This infrastructure produces no association or scientific verdict.

## Frozen scope and case

The original first reader is `openai-community/gpt2-medium`, model ordinal 0.
The original proposal hash is
`c5d3380c0bfad4ea6b97dc5700115a820da4efe27ffb902165cc9aa4d574334e`;
the ten-reader roster hash is
`cdb90059a1439205dff7feba1517dc7fb990a57718e1e7996d431730f99a05fb`.
This proposal retains all 165 original pilot ordinals and 27,007 original
words. The parent reports ordinal 132 COMPLETE and its native owner exited;
therefore the proposed new queue is ordinals 133–164, in order. The final owner
prefix audit still must bind every completed predecessor before admission.

The case is a long, unchanged reader pilot whose repeated single-chunk
preparation needlessly authenticates the entire historical prefix. The check
is exact equality to the original proposal plus a complete, deduplicated
historical hash manifest, followed by independently verified native chunks.
The smaller route is an authenticated checkpointed continuation of these same
ordinals; it is never a reduced sample or another reader.

## Native execution and checkpoints

One reviewed outer runtime owns one shared counted CPU slot. Inside it, each
chunk uses the existing `week5_child_v7` in a fresh Windows contained process
for execution, then a different fresh contained process for verification.
Children claim no additional slot. Nested Job containment and actual launcher
accounting must pass the new native fixture before production admission.

Each child invokes the unchanged `week5_at_scoring_guard_v1`, which retains
`week5_at_scoring_v5`/v4, the original float32 weights promoted to float64,
float32 log-softmax/entropy reduction, final-text context of 1,024 tokens,
the original seeded 2% fresh forwards and the 1e-4-nat tolerance. The original
eight-row score blocks and receipts remain the resumable unit. The scorer's
900-second execution quantum is unchanged. No numerical implementation,
reader selection, input order or analysis code is changed.

Execution plus verification of one chunk is bounded by 1,700 wall seconds and
7,200 native CPU seconds. Cooperative wall requests begin 60 seconds before
the boundary; the exact owned nested job closes on expiry. Thus an abrupt stop
cannot lose an uncheckpointed phase spanning more than 30 minutes. Hard exits
or interrupted incomplete seals remain failures requiring owner recovery from
authenticated earlier checkpoints; they are never automatically marked paused
or complete. Soft pauses preserve both attempt and score seals. A continuation
creates a fresh internal attempt, copies only authenticated score outputs and
preserves all predecessor evidence and costs. A verify pause may require a
cheap unchanged execution reentry and a fresh complete verify; all repetition
is charged.

The memory guard is unchanged: start at least 26 GiB Windows commit headroom
and 20 GiB available RAM; request a yield below 7 GiB of either; terminate the
owned scorer below 6 GiB or after the original 60-second grace. These are
admission floors, not measured peak memory. Each child records actual thread
pools, native PID/creation identity, output hashes, original guard receipt,
phase usage and successful native exit. Maximum numerical threads stay two;
GPU, Ollama, paid calls and network collection stay off.

`CHUNK_COMPLETE.json` is an internal checkpoint, not a standalone research
terminal. It seals the complete executed-and-verified chunk. There are no
watcher registrations or write-throughs for intermediate chunks. The outer
queue terminal receives the complete internal landing under amendment N.

## Bounds and costs

The proposed queue envelope is at most 43,200 wall seconds, 230,400 child CPU
seconds (32 × the unchanged 7,200-second chunk envelope), projected peak RAM
20 GiB, and 1 GiB retained output. These are explicit conservative caps, not a
full-run timing forecast. Before launch the owner binds the smaller remaining
AT/campaign allowance, all predecessor and preparation charges, and the actual
campaign clock. The original AT ceiling remains 750,000 CPU seconds and the
campaign ceiling 6,000,000; no sub-allocation or reservation blocks an otherwise
eligible start. The outer runtime is authoritative for all descendant and
exited-process CPU, including hashing, reconstruction, repeated phases,
failures and verification. Per-chunk Job CPU is diagnostic, never added again
to the outer total. The usual outer supervisor charge remains separate.

At most six of the eight shared slots may hold long queues. Existing reservations
and companion ownership remain untouched. This candidate neither launches
outside Week 5's freeze/drain nor transfers work or charges to Week 6. If the
clock has closed, a separately reviewed carry-forward must bind the existing
original ceiling, all charges, runtime and actual Week 5 drain.

Output bytes are checked periodically and after every native exit, pause and
queue verification. A fast write-and-exit cannot evade the terminal cap.

## Prefix verification and source compatibility

The owner's existing full-prefix preparer runs once for ordinal 133. A review
receipt binds the exact request and proposal hashes. The nonlaunching freezer
collects all completed outputs, original native terminals, checkpoint ancestors
and normalized immutable dependencies into one deduplicated hash map. It
retains the exact already reviewed policy archive migration. Queue execution
authenticates that map once per invocation before new scoring. Per-chunk child
plans contain their own row file, model manifest, static scorer/child closure
and retained qualification dependencies; they omit historical prefix roots.
The full old prefix is not rehashed per chunk.

The queue's fresh outer verify audits every new chunk's complete outputs,
native execute/verify pair and original fresh-forward proof. It does not load
the model again after those complete separate-process verifications. It uses
the immutable prefix authentication receipt and pinned prefix identity. An
authenticated resume repeats the historical check once at entry, then skips
already verified new chunks.

No participant rows, scores or compressed source text were decoded in this
build. The original pinned row files and model manifest are consumed only by
the future admitted original scorer. Collection-catalog presence grants no
source or model admission.

## Collector compatibility and admission limits

The existing `week5_at_admission_prepare_v3.measured_chunk` and pilot envelope
expect one top-level `COMPLETE.json` per chunk. The new nested checkpoints must
not be passed to those functions or dressed up as independent top-level jobs.
The existing scientific collector is also not silently relaxed. Before any
downstream bank or association, the owner must admit a versioned collector
adapter that reads the outer queue COMPLETE/PLAN/VERIFIED seals, validates every
nested chunk, combines the original prefix and new exact ordinals into 0–164,
and charges each outer attempt only once. It must reject gaps, duplicates,
partial queues, altered inputs, changed precision/context/revision, missing
fresh forwards and missing native usage. This delivery prepares scoring only;
no complete ten-reader bank or AT2 analysis is admitted by its completion.

## Qualification before production

The test source is provided but unrun. Required counted qualification:

1. Targeted manifest/integrity fixtures, including exact scope acceptance and
   changed roster, precision, context, reader, guard, caps and prefix refusal.
2. Native constructed queue through the actual outer launcher, original child
   wrapper, original guarded FP64 kernel and nested Job containment. All model
   weights and texts are constructed; synthetic memory snapshots are labelled.
3. Two serial chunks with distinct fresh execute/verify identities, whole
   output seals and original fresh forwards; native pause/copy/resume with
   predecessor bytes unchanged; changed sealed-score refusal.
4. Actual fast-exit output-cap and hard-deadline refusal, with all failed native
   costs retained and exact owned process absence established.
5. Owner comparison of outer all-descendant Job usage against the sum of all
   nested usage (including failed and repeated phases), plus real launcher
   admission/ceiling/clock/slot behavior. A direct module test alone does not
   qualify production launcher wiring.

Proposed qualification envelope: one counted slot, two numerical threads,
2,000 inclusive CPU seconds, 3,600 wall seconds, 4 GiB projected RAM and 512 MiB
output, charged to AT. This proposal is not a booked allowance or permission to
run. No fixture passed is claimed until actual complete native receipts exist.


# Complete m00 pilot collection and native qualification addendum

DESIGN CHECK — LESSONS §3–§5 read for this implementation. Null and alternative
downstream results have identical admission and integrity rules. Exactly all
165 original ordinals and 27,007 original word rows pass the scope gate;
missing, duplicate, reordered or extra work refuses. The original model,
revision, final context, 1,024-token context length, FP64 numerical contract,
memory limits and seeded fresh-forward checks must all agree. No association
is calculated by this adapter.

## Preserved first delivery and correction

The earlier `at-queue-v1/DELIVERY.json`, hash
`81ecfe713b4549672cb23477ce4a4281cd8a5efc2c0687fccb4e7d28fd993148`,
remains unchanged. Its static review incorrectly said the original score
SUMMARY omitted `context_length`; the original source and actual chunk132
summary contain that field. The correction restores the explicit 1,024 check
and adds an actual changed-summary refusal to the constructed native fixture.

The forced-stop correction records the complete owned Windows identity before
polling, preserves it in the forced-stop record, closes the contained Job, then
requires an actual native inspection showing that exact identity is no longer
live. Unknown inspection fails. The fixture cannot pass just because its child
did not write an optional marker. A fast-output case requires the exact cap
error plus a successful actual child return and exit; a deadline case requires
the exact deadline error, matching owned identity and closure proof. A child
import error or unrelated exception cannot pass either case.

The guard's psutil timestamp is compared with Windows FILETIME after subtracting
the epoch as an integer, before floating-point division. This avoids cancellation
from first converting the much larger absolute FILETIME value. The existing
2e-6-second tolerance is retained, not widened. The native fixture will record
every actual conversion delta; none has yet been measured by this builder.

The private freezer now refuses pre-mortems unless they use the actual
launcher's `case_and_check` and `smaller_route` keys. These are compatibility
corrections, not scientific changes.

## Actual counted qualification harness

`qualify_at_queue_v1.py` has separate `prepare`, `launch` and `inspect` actions.
The builder has run none. The owner must first install reviewed source copies
and the targeted test under `tests/test_week5_at_queue_v1.py`, commit the design,
and supply the exact complete original guard/child bootstrap receipt. The
plan states that the old bootstrap passed and the new queue is the subject of
qualification; it does not describe the new queue as already qualified.

The harness calls `week5_launch_v10.freeze_plan` and `launch`, preserving real
clock, shared slot, remaining family/campaign allowance, watcher handshake,
source-capsule and native monitoring behavior. It uses one counted AT slot,
2,000 child CPU seconds, 3,600 wall seconds, two numerical threads, 4 GiB
projected RAM and 512 MiB output. The ordinary 30-second supervisor allowance
also remains charged. An existing outer fixture is not launched again.

Both outer execution and verification run the targeted checks in that counted
process and then independently construct and execute the native queue fixture.
Actual native cases cover serial execution and fresh verification, a sealed
pause and fresh copy/resume, altered score and context refusal, fast-output
overflow, hard deadline closure and retained costs. The harness final inspection
authenticates the outer COMPLETE/PLAN/VERIFIED outputs and exited owner, requires
all named native cases and known closures, deduplicates copied receipt identities,
and checks that each outer phase's native Job CPU contains every nested measured
phase, including stopped and resumed work. Conservative inner termination
margins are recorded separately from measured inner CPU; outer accounting is
authoritative and is never increased by adding nested CPU again.

This fixture uses actual tiny constructed FP64 models and labelled synthetic
memory snapshots. It cannot replace the original production memory admission
or justify a different reader. The owner must review every receipt before binding
production qualification into a new queue manifest. The earliest production
ordinal remains 133, and campaign clocks are not extended by this delivery.

## Additive collector adapter

The original collectors and source producer remain unchanged. The new
`week5_at_queue_collect_v1` accepts a pinned complete outer queue plus the
original qualified pilot source. It authenticates the queue COMPLETE, PLAN,
fresh verification, actual exited owner and all descendant usage. It verifies
the deduplicated original prefix once, then maps historical top-level chunks
0–132 and nested queue checkpoints 133–164 into exactly the original order.
It never constructs top-level COMPLETE files for nested chunks.

Each ordinal retains its original row-file hash and model-manifest hash,
original core/guard pins, exact model revision and numerical specification,
actual two-thread environment, native execute/verify identities, original
memory-start thresholds and guard limits, successful native usage and original
2% fresh-forward count/error. New nested phases additionally require owned,
exit and known-closed records. One native phase cannot authenticate two chunks.

The collector recomputes the original `score_binding` from the unchanged row
list and model manifest, checks INDEX order against original row keys, verifies
each sealed eight-row score block and its index slot, and rejects duplicated
word rows across chunks. The actual original scoring and fresh replay provide
tokenizer/forward certification; no model is loaded by collection and no
different numerical implementation is substituted.

Only after all 165 ordinals and 27,007 rows pass does it emit a private pilot
catalog, source/score index and complete m00 measured envelope. Historical
native chains and each outer queue attempt are charged once. Copied nested
diagnostic usages do not become new charges. The original all-AT failure
inventory remains separately pinned and charged, including failures outside
successful checkpoint ancestry.

Output is `complete_original_m00_pilot=true`, `whole_ten_reader_bank_ready=false`,
`scientific_admission=false`, `association_computed=false`. A missing or paused
queue emits no complete pilot artifact. This is one reader's source/scoring
catalog, not the complete ten-reader bank or permission to select the best
reader. A downstream fit must separately admit its full declared bank and
controls through the existing scientific rules.

## Collector fixture and remaining qualification

The separate collector fixture consumes only the complete actual constructed
queue fixture. It rejects a real model manifest, validates both native scored
chunks with the production helpers, and checks source/word bindings and exact
native proofs. Scratch copies test changed context, revision, precision, core
pins, word order, missing fresh forwards and wrong native identity. Metadata
controls exercise the original165/27007 boundary and explicitly refuse the
two-chunk fixture as an incomplete pilot. No native receipt is fabricated.

Its proposed counted envelope is 300 CPU seconds, 600 wall seconds, two
threads, 2 GiB RAM and 128 MiB output, plus the ordinary supervisor charge.
It depends on the completed queue qualification and reviewed adapter design.
All these tests are unrun. The final full original-pilot catalog and independent
replay run only after the real original queue is complete and the owner admits
the consumer. No human row was decoded in preparing this delivery.
