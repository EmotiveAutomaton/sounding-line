# Stage 12: one warm-start recovery of the first execution block

The first frozen execution block stopped after its first returned call at the
unchanged matched-throughput guard. Retained telemetry records 11.712 seconds
client wall time, including 8.873 seconds of model loading, against a 2.896-second
matched reference. The response, timings, failed terminal and all costs remain.
Later independent blocks continue; no original result is replaced.

DESIGN CHECK: LESSONS 3–5 and the original execution design read. Under either
scientific hypothesis the same timing guard applies. Cold model admission is
not warm throughput. The cause-specific recovery requires the exact model and
context already fully resident at launch, with the unchanged free buffer.
Missing residency refuses dispatch; it does not lower a threshold or select a
different model. This is the single permitted recovery of this history block.

After the current queue exits normally and its native ownership is released,
execute all fourteen original requests in a new attempt namespace. Retain the
same request digest, controls, parser, profile, seed, labels and source inputs.
No partial response is spliced into the recovery. The new whole attempt is the
selected comparison if complete, with both attempts and costs visible. A failed
recovery closes this unit as incomplete; no second automatic recovery.

The single card reserves 4,740 GPU-service seconds, 600 CPU seconds and 5,580
wall seconds. Whole-plan accounting includes the original submitted roster,
this additional reservation and the original protected reporting reserves.
No cloud spending, extra fit, application stop or source/scorer change is made.
Current-queue completion is an explicit dependency; dispatch also checks its
native identity, released GPU lock and exact resident-model evidence. The
existing terminal watcher supplies the next operator handoff.
