# Suggestion throughput recovery: direct safety telemetry

DESIGN CHECK: LESSONS 3-5 read October 17. NULL: telemetry disagreement, source
drift, changed scores, inadequate memory or an excessive measured forecast refuses.
ALTERNATIVE: the same checks and scores complete faster with direct read-only
telemetry. No sampling cadence, precision, context, gate or ceiling changes.

The complete valid v3 pilot projects beyond the 72-hour main limit. Its repeated
GPU checks start a new command process for every candidate/menu boundary.
Replace only those invocations with direct fresh calls to the installed NVIDIA
NVML library. No telemetry caching, driver setting, model edit or new dependency.
Require one unambiguous device, pin the installed DLL and verify its identity
against the command at startup and after each model loads. API failures refuse.
Each candidate/menu retains exactly its previous before/after check points.
Free memory rounds down conservatively; every existing resource floor remains.

Validate memory units, invalid accounting, API errors, identity mismatch and
disagreement on known answers. Five bracketed live comparisons against the
existing command must agree within 16 MiB and 2 C (temporal comparison margins,
not safety-floor changes). The complete v4 pilot must independently replay all
checkpoints and match the same v3 selected native-token losses within 0.02 before
main preparation. All old inputs, selection, model weights, float32 precision,
contexts, packing, losses and deterministic checkpoints remain unchanged.

Charge all previous pilot/diagnostic lifetimes, including completed v3, against
the original two-hour work allowance. This is one bounded implementation timing
recovery, not a repeated search for a passing scientific result. Require full
write-through before main preparation. Main still needs the measured threefold
runtime forecast within 72 hours and output estimate within 32 GiB. Typed/history
and downstream comparisons remain separate. No paid calls or automatic main.

The telemetry ABI follows NVIDIA's primary documentation:
[device queries](https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html),
[memory structure](https://docs.nvidia.com/deploy/nvml-api/latest/api/structnvmlMemory__v2__t.html),
and [initialization/cleanup](https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlInitializationAndCleanup.html).
Windows memory values retain the operating system's accounting limitations;
agreement with the prior command does not make them continuous physical guarantees.
