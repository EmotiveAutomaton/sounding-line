# RUNTIME V6 VALIDATION 20261030

**Hypothesis.** Can supervision tolerate the atomic writer replacing its temporary file while still refusing actual storage and I/O faults?

**METHOD.** Exercise a deterministic disappearing-file race, normal missing-file refusals, permission denial, single-stat counting and retained temporary bytes. Then launch the actual v6 supervisor for native execution plus independent replay, and separately present an oversized output to its real cap handler.

**Found.** The isolated supervisor passes race and refusal checks, native replay and the unchanged storage cap; scientific code and limits remain unchanged.

All seven regression checks pass. The native positive rehearsal completes and freshly verifies; the negative rehearsal stops on the exact frozen byte-cap error and writes no completion. The first test invocation was blocked by its default temporary-directory permissions before any test body ran; that output and charge remain, followed by a successful fresh workspace-local invocation. No criterion was weakened.

The table lists operational validation only. Each row identifies a native rehearsal and its retained CPU charge; the cap refusal is the intended known answer.

| Rehearsal | Outcome | CPU seconds |
|---|---|---:|
| Atomic writer and fresh replay | Complete and verified | 1.4375 |
| Oversized output | Correctly refused | 2.0 |

Regression and native charges total 5.828125 CPU seconds before checkpoint-preparation bookkeeping. They are covered by a conservative 300-second reservation deducted from the existing shard allowance; unused reservation is not silently reclaimed. The v5 runtime remains immutable for the healthy workers.

**Means.** This validates an infrastructure repair only. All source checks, native containment, resource floors, CPU/wall/drain limits and full fresh scientific replay still apply. No new scientific claim or additional compute allocation follows.
