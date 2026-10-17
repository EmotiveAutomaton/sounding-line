# Reader pilot numerical repair

DESIGN CHECK: LESSONS 3–5. Cache and direct teacher forcing must agree within
the original 0.02 absolute token-loss tolerance. Empty, unequal-length or
nonfinite arrays fail. No scientific effect is being selected.

The first pilot stopped on cold-load memory headroom between readers. The
second waits for that resource but stopped at the first Qwen cached/direct
comparison. Its exception establishes failure of the tolerance, but the old
worker did not retain the numeric discrepancy; its size and cause are unknown.

A separate third attempt tests a precision explanation: the same Qwen weights,
tokenizer and full input roster run in float32, with the original comparison
and tolerance unchanged. Each comparison's complete arrays and error are
retained before admission. Passing would establish agreement for the repaired
runtime, not retrospectively prove the cause of the float16 failure. A further
failure stops this attempt and requires diagnosis, not a tolerance change.

The completed Smol pilot is reused by exact input/source binding. Unrun Pythia
readers retain float16. Per-reader dtype is part of the runtime identity.
Common byte units, whole-context exclusion, full GPU residency, the 6,500 MiB
cold-load floor, 1,024 MiB operating floor and 40% allocator cap remain.
This finite pilot admits neither full-corpus scoring nor a scientific claim;
its measured throughput and exclusions must first inform that executable plan.
