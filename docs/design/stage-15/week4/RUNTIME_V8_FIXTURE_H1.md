# Runtime v8 native writer-contention fixture

The first native stress fixture exited after Windows denied replacement of its
PID-named progress file during aggressive concurrent scanning. Original receipts
and stderr remain; its 0.890625 CPU seconds count against the original runtime
validation allowance. The supervisor labels the child exit engineering; direct
stderr identifies a Windows sharing refusal in the auxiliary telemetry writer.

The new fixture retries only that writer's PermissionError, at most fifty calls
with ten milliseconds between retries. It preserves every value, both actual
temporary formats, concurrent scanning, exact byte totals and native cap refusal.
Permanent denial and other I/O errors still fail; three separate tests cover these
paths. The earlier seventeen scanner checks remain unchanged and pinned.

This bounded writer retry is confined to the constructed fixture. It does not
modify the pinned human-source runner or its shared progress writer, and does not
claim that their possible Windows sharing refusals are repaired. Any later source
continuation needs a separately pinned writer successor and full validation in
addition to the existing cost hold. No source replay is admitted now.

Both native fixture attempts and the byte-cap refusal share the original 120
CPU-second validation allowance. The existing additional twenty-second reserve
covers both targeted test sets and preparation; it is not refunded. The case and
its check remain both writers plus fail-closed accounting; the smaller route is
the bounded constructed fixture only. No new scientific scope or spending.
