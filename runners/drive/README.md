# October 16 drive runners

This namespace implements the [new commission](../../docs/design/stage-15/drive/README.md)
without changing completed attempts. Public summaries belong in
`results/phase_2_4_stage_15/DRIVE`; raw text, identifiers, plans, predictions and
provider responses remain in ignored `raw/drive-*` folders.

Every worker freezes code/input hashes, claims an attempt once, records its
actual Windows PID and creation time, and verifies monitor registration before
work. Resource checks require 8 GiB each of available RAM and system commit,
and 20 GiB disk. A failure retains evidence and requires a separate attempt;
completed output is verified rather than rerun. Unknown provider calls retain
reservations. No unattended publication or automatic research expansion.

The card registry is a dependency map, not a claim that all runners exist.
Only tested executable plans may enter the native queue. See the drive design
README for authority and the current operational handoff for launch identities.

`reader_pilot_v6` completed the finite memory-recovery validation; all fixed
outputs, numerical gates, source hashes, native exit and released lease verify.
Its no-cache float32 scorer clears only its own BLAS workspace between models.
Do not rerun this completed pilot. `suggestion_pilot` now runs a finite
whole-input census and five-reader timing pilot. `suggestion_main` is built
but refuses preparation until that pilot is independently landed and its
measured bounds pass. Both use `suggestion_corpus`, thirteen passing targeted
checks, hashed per-session gzip checkpoints and native monitoring. This is
only the suggestion component; typed sentences/history remain unbuilt.
The original v5 cleanup failure remains preserved.
`v1_phase0_v3` completed the full 150-world calibration;
its evidence, native exit and released CPU lease are verified.
`reader_pilot_v4` ended at its finite resource-wait deadline before the largest
model loaded. Its native worker and launcher exited, GPU lease is released and
completed outputs are retained. The separate v6 recovery has an explicitly
reduced memory footprint and tested cleanup. Full reader scoring remains held.
The completed calibration retains its frozen plan and terminal evidence. No runner executes
all 31 cards.

`v1_phase0_v2` ended at its byte cap; its failure, source bindings and native
exit are recorded. `v1_phase0_v3` completed lossless recovery and the remaining
fits; the full grid and saved statistics independently reconcile. The [recovery contract](../../docs/design/stage-15/drive/V1_PHASE0_V3.md)
retains the grid, caps and original evidence. Do not start a duplicate worker.

Completed `content_features_v2` and `v2` representations/decomposition are
verified and fully recorded. No predictive fit or full reader pass is implied.

Completed `foundation`, `wiki_reference` and `cloud_v2` outputs are immutable;
original failed versions remain. Do not rerun or edit a live plan's imported
source. Read the [execution index](../../results/phase_2_4_stage_15/DRIVE/INDEX.md)
before dispatch; prepare/run commands refuse an existing attempt identity.
