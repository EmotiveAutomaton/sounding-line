# Five-reader pilot with diagnosed precision repair

DESIGN CHECK: LESSONS 3–5 reread October 16. NULL: numerical disagreement,
unknown source identity, nonfinite output, partial residency or memory-floor
loss stops admission. ALTERNATIVE: all five exact reader runtimes finish the
fixed menu/context roster and satisfy the original 0.02 token-loss check.
Neither outcome selects a scientific effect or grants full-corpus admission.

The complete paired Pythia 410M diagnostic uses the identical fixed menu in
four contexts, once at each precision, with the same SDPA attention runtime.
Float16 disagrees by up to 0.129802; float32 agrees within 0.000351. This supports
a precision-specific remedy on these inputs, not a claim about every reader.
Retain the original failed pilots and both diagnostic attempts unchanged.

This successor runs all three Pythias in float32 on the unchanged 11-menu pilot
roster. Reuse completed Smol and float32 Qwen outputs from v3 only after exact
input, source and output binding checks. These reused outputs did not freeze
package versions contemporaneously; do not retrofit that claim. Record and
freeze versions for all new executions. The numerical comparison remains the
first menu under every context, with all direct/cached arrays retained; complete
pilot throughput and overflow counts remain necessary before full scoring.

Float32 increases weight memory. Pythia 410M and 1B retain the 6,500 MiB cold
headroom and 40% allocator cap. The 1.4B arm requires 8,500 MiB free before load
and caps allocation at 58% of this 12 GB device, providing space for its roughly
5.3 GiB of weights and bounded workspace. All arms retain the 1,024 MiB observed
operating floor, 78 C ceiling and full GPU residency. No CPU/system-memory
offload is permitted. Check actual parameter dtype/residency and free memory
after loading and calls. Headroom waits are bounded and never reclaim another
project's workers. Changing the memory reservation is not changing the
numerical acceptance threshold.

The finite worker has six hours of bounded resource waiting and four hours
of computation; time between fully unloaded models waiting for cold headroom
does not consume computation allowance. A hard overall limit remains. No
provider call, paid reservation, implicit retry or full-corpus dispatch.
