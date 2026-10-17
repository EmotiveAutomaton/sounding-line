# Fixed Pythia precision diagnostic

DESIGN CHECK: LESSONS 3–5 reread October 16. NULL: direct and cached
teacher-forced losses disagree, or either becomes nonfinite; the reader stays
unadmitted. ALTERNATIVE: the higher-precision runtime agrees on every fixed
comparison. No threshold is relaxed and no scientific effect is selected.

Reader pilot v3 ended at Pythia 410M's first unconditional comparison. The
retained arrays have equal length and finite values but exceed the original
0.02 absolute token-loss tolerance. This identifies numerical disagreement,
not its cause. The completed Qwen runtime does not diagnose Pythia.

Run the same first frozen menu under all four pilot contexts, with the same
weights, tokenizer, attention implementation and inputs, once in float16 and
once in float32. Save every direct/cached array, GPU residency, actual dtype,
library version and attention implementation. Compare all eligible targets;
retain context overflow as unavailable. No input is selected by its output.
Float16 failure is an expected diagnostic outcome, not a reason to abort before
the paired float32 measurement. Nonfinite output or resource failure stops.

Both versions passing means the old failure did not reproduce. Float16 failing
and float32 passing supports a precision-specific remedy on this fixed menu.
Both failing leaves the cause unresolved; float32 alone failing also leaves
the higher-precision route unadmitted. Passing this diagnostic cannot admit
the full roster, larger Pythias, full-corpus scoring or a scientific claim.
Any successor needs a separately frozen full pilot and feasible memory plan.

One GPU lease, 6,500 MiB cold headroom, 1,024 MiB operating floor, 78 C ceiling,
40% allocator cap and full CUDA residency remain unchanged. Maximum compute
time is fifteen minutes, resource wait six hours. No paid calls or retries.
