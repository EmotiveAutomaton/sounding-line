# Bounded LA1 source preparation

Prepared November 8, 2026. This immutable engineering successor implements the
source-preparation gap identified in [human-bank admission](LA_HUMAN_BANK_ADMISSION.md).
It has not been executed or tested. Owner design review, local commit, counted
native qualification and measured real-source resource/cost admission remain.
No source projection, model inference, selection or scientific analysis was
started during its construction.

## DESIGN CHECK

The case is an interrupted source projection that otherwise repeats all prior
contexts before reaching new work. The check compares every output byte against
the original full preparation, including eight-act blocks spanning meetings,
support counters, stable tied ordering, contexts and final summary. Source,
configuration, checkpoint, cursor and completed-block changes must refuse.
No outcome or model score chooses a checkpoint or changes the source population.

The smaller route remains the existing separately measured whole-meeting route.
This successor does not select meetings, shorten context, change the laughter
window or supply a reader. Below-floor scientific handling is unchanged.
First-five-percent and any cost-triggered sample still require a measured,
prospectively frozen scope; no count or forecast is invented here.

## Exact interface and semantics

`week5_la_prepare_v1.execute/verify` accepts only `source_root`. The source must
have a complete independently verified receipt, and all of its sealed outputs
are checked. The original LA label helper and preparation v3/v4 code hashes
are frozen. Only LA1's already declared corpora, history lengths, windows,
vocal-label scope and laughter ownership are accepted. There is no selected
reader or model manifest input. The existing scored collector can consume the
same prepared output schema after qualification; its own admission stays closed.

Meeting groups retain original source order, then invoke the unchanged label
helper. Sorting meetings and using its original stable within-meeting sort
gives the original global order, including tied onsets and speakers. Only
earlier acts whose end is no later than the current start supply talk history.
All completed prior talk remains available to the later causal tokenizer; the
previous three/five/ten completed acts supply the unchanged masked input.
No future act, annotation marker, model output or other meeting is introduced.

Eight-act blocks keep the original global boundaries across meetings. A
checkpoint can retain zero to seven pending rows, the source cursor, support
counters and the entire ordered block index. Source row files, `BATCHES.json`
and `SUMMARY.json` must be byte-identical to the old implementation. Extra
checkpoint, binding, progress and invocation-cost files are provenance only.

## Checkpoints and limits

Checkpoints are immutable gzip state files with separate chained seals. Each
seal binds its state hash, predecessor seal, source completion, original code
and semantic configuration. A resume validates the chain and all retained
source blocks, reconstructs the current meeting from original data, and starts
at its saved position. Pending rows cross the next block boundary unchanged.
A file written before its seal may only be adopted after fresh reconstruction
equals it; no interrupted evidence is deleted or repaired in place.

Execute and independent verification have separate cursor chains. Verification
rebuilds labels and rows from the actual source and compares every act block,
index and summary; it does not use produced model scores or accept an execute
cursor as a verified cursor. A continued verifier can reuse only its own sealed,
unchanged previously replayed prefix. Complete execute reentry preserves the
original bank. Each invocation retains its process cost; native all-attempt
accounting remains authoritative.

The default quantum is 32 newly completed blocks or 600 wall seconds, checked
before each next act and between source phases. A resource request is honored
at those boundaries. The wall quantum may be changed only under the existing
runtime's permitted operational-key rule; `max_new_blocks` is kept identical
across native continuations because the current resume adapter does not list
it as a changeable operational key. Neither parameter alters source semantics.

Authentication of an individual file, gzip decoding, grouping the source and
construction of one meeting's labels are atomic units. Their real duration,
peak memory and checkpoint-chain authentication overhead are unmeasured. The
new quantum is not evidence that those units satisfy a native resource grace
period. Measure them inside the first counted source qualification; refuse or
develop another exact successor if they exceed the reviewed envelope. No
resource floor or native supervisor rule is relaxed by this implementation.

## Prepared proof and native boundary

`week5_la_prepare_v1_fixture` constructs three populated meetings and one empty
metadata meeting across both corpora, literal spoken “laugh”, stripped marks,
vocal/comment outcomes, overlapping acts and stable-sort ties. It prepares
the primary and all declared source variants, plus the already supported
vocal/comment label variant. The actual old full handler and bounded handler
must produce identical complete output bytes. Outer native verification
independently replays both handlers, including their source support.

Additional controls force a before-load yield, an interruption with pending
rows, a copied partial checkpoint, completed execute reentry, and refusal of
changed source/batch/checkpoint/cursor/configuration, an unexpected batch or
an added reader input. These are expressly local constructed checkpoint-copy
controls; they do not impersonate an exited native owner. The owner must also
review a counted pause/copy/resume sequence through the existing native resume
adapter before claiming native continuation readiness.

Suggested constructed proof cap for review: 600 CPU seconds, 900 wall seconds,
3 GiB projected peak and two numerical threads. These are unmeasured caps,
not forecasts or a human-source memory admission. The proof is prepared only;
no tests, source execution, native starts, commits or acknowledgments occurred.
