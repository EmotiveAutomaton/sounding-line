# P1 suggestion corpus: measured pilot and checkpointed execution

DESIGN CHECK: LESSONS 3-5 reread October 17. NULL: changed source, incomplete
coverage, invalid token alignment, nonfinite losses, numerical disagreement or
resource-floor loss refuses completion. ALTERNATIVE: the fixed exposed suggestion
roster is completely scored with explicit whole-context exclusions, recoverable
chunks and measured resource bounds. No hypothesis is selected by these checks.

The curator requested completion of all feasible commissioned work on October 17.
This is the suggestion component of P1, not the writer-typed/history component
or a completed downstream study. Preserve all original reader attempts and the
verified v6 memory implementation. Do not describe the finite pilot as a corpus run.

Use every menu in the frozen Phase 0 exposed roster: 1,399 sessions, 61 writers,
16,855 decisions. Pin original session sources, model/tokenizer bytes and runtime
versions. Read each session's original initial prompt; preserve menu order and
text, decision identity and all four existing context renderings. The target is
the complete displayed suggestion. Retain native per-token losses and offsets,
total and mean loss, UTF-8 byte normalization, and average-tie within-menu ranks.
Whole-context overflow is an explicit exclusion, never truncation. Reader-specific
recent-token contexts retain their original scope. No sealed confirmation data.

Pythia 410M/1B/1.4B use the verified float32 no-cache blocked projection. Qwen500
uses the prior float32 cached scorer; Smol360 uses the prior float16 cached scorer.
Keep the original model identities and numerical tolerance of 0.02. Repeated
original outputs are not recomputed to create apparent progress.

Before corpus dispatch, census all input token lengths and eligibility for each
reader/context. For each reader, select the deterministic first menu nearest each
quartile of eligible whole-context length, plus the longest eligible menu and
first overflow menu when present. Selection reads input support only, never losses
or writer outcomes. Score each selected complete menu in all four contexts. Check
the first eligible unconditional target against ordinary direct scoring. All
arrays, exclusions, elapsed times, allocation peaks and output bytes are retained.
The complete timing pilot receives independent validation and write-through before
the operator freezes any corpus plan. No automatic main dispatch.

The GPU allocator cap is 5888 MiB. Cold free memory must be at least 7424 MiB;
between unloaded models with the initialized CUDA context require 7168 MiB and
zero allocated/reserved bytes. Every candidate or cached menu has before/after
resource checks. Keep 1024 MiB free, 78 C maximum, 8 GiB RAM and commit headroom,
20 GiB disk, one CPU thread, below-normal priority and the exclusive project GPU
lease. Explicit process-local BLAS cleanup follows model deletion. No offload,
quantization, floor relaxation or stopping other applications. A resource loss
preserves checkpoints and fails the finite attempt; it never becomes a null.

The pilot has a two-hour resource-wait allowance, two hours of work and a four-hour
hard wall. Main allowance is computed after the pilot, with a threefold safety
factor using both input-token and scored-option rates, a ten-hour minimum and a
72-hour maximum. If the forecast exceeds that ceiling, do not launch the main
unchanged. Maximum main retained bytes: 32 GiB; estimate from actual compressed
pilot records before admission. Main checkpoints are one complete session per
reader, compressed losslessly with deterministic gzip metadata, hashed and read
back before registering completion. A reusable checkpoint validates its exact
input identity, source plan and entire score schema; unknown/partial files refuse.
Recovery requires inspected native exit and a separately reviewed attempt; no
automatic retry. Main completion requires every planned reader/session chunk,
every input accounted for and unchanged source bindings. Intermediate chunks are
not scientific findings or complete P1. Final produces and native identity must be
registered before work; immediate failures and the standing six-hour health cadence
remain. No paid calls, new studies, delegation or unattended publication.
