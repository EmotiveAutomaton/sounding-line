# Reader recovery with a bounded memory footprint

DESIGN CHECK: LESSONS 3-5 reread October 17. NULL: altered token alignment,
nonfinite values, numerical disagreement, partial CUDA parameter residency,
allocation exhaustion or safety-floor loss stops the complete attempt.
ALTERNATIVE: the unchanged float32 reader ladder finishes with equivalent
losses inside a smaller measured memory envelope. This validates an apparatus;
it neither selects a scientific effect nor automatically launches the corpus.

The curator authorized a small implementation adjustment on October 17 so the
study can coexist with other work. Preserve v4 and its resource-deadline failure.
Do not lower v4's gate or promote its partial ladder to a completed pilot.

The new Pythia path recomputes each candidate's whole prefix without a KV cache
and projects final hidden states to vocabulary logits in blocks of 32 target
positions. This removes persistent prefix/branch cache copies and full-prefix
logits at the cost of repeated computation. Exact models, tokenizer bytes,
float32 weights/operations, all contexts, the 2048-token window, eligibility,
target token losses and byte-normalized denominators remain unchanged.
No quantization, token truncation or CPU/system-memory offload is introduced.

Validate the real scoring function on a small randomly initialized GPTNeoX
against ordinary direct scoring, a zero-weight uniform-probability answer,
the full window and deliberate nonfinite inputs. Then on both completed Pythia
410M and 1B pilots, compare every eligible token with the saved v4 cached scores
and retain both arrays. The maximum absolute token-loss tolerance remains 0.02.
Reused Smol and Qwen files stay byte-identical, including their disclosed missing
contemporaneous runtime-version provenance. Verify all v4 source/input pins and
the previously recorded retained-output manifest before copying any output.

Only after both real-model equivalence passes may Pythia 1.4B run. Check its
first unchanged menu in all four contexts against ordinary full direct scoring,
under the same 0.02 tolerance. Run one deterministic 2048-token synthetic memory
probe first, with the final 32 tokens scored. This checks the actual maximum
window on the new runtime, not a scientific result. Complete all 11 original
menus and retain throughput, numerical checks, eligibility and allocation data.

The GPU allocator is capped at 5888 MiB (5.75 GiB). Before creating the CUDA
context require 7424 MiB free: cap plus the unchanged 1024 MiB operating buffer
plus 512 MiB for non-allocator/context overhead. Between fully unloaded models
with the process's existing CUDA context, require 7168 MiB free and zero live
allocator bytes: the same cap and buffer plus 256 MiB additional overhead.
The initial context allowance is not charged twice. This is a new budget for
a different implementation; feasibility must be measured rather than assumed.
Keep the 78 C ceiling, host RAM/commit/disk floors and exclusive project GPU
lease. Check memory before/after each candidate and direct reference. An OOM or
loss of the operating floor fails and releases this worker's resources; no
automatic retry, different precision or admission-margin relaxation follows.

One finite worker, two hours maximum resource waiting and one hour computation,
three hours hard wall limit. One CPU thread, below-normal process priority;
yield briefly between candidates. Other projects and ordinary applications
retain their processes. Terminal and native-disappearance supervision must be
registered before model work. Full internal write-through precedes completion
ACK. A later full pass needs its own throughput-sized plan and checkpoints.
