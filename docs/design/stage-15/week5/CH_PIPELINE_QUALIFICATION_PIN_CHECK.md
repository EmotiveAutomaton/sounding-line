# CH qualification driver: immutable pin-check successor

This addendum keeps the full procedure, ten-stage order, bounds and controls in
[CH_PIPELINE_QUALIFICATION](CH_PIPELINE_QUALIFICATION.md). Use the separately named
`runners.drive.week5_ch_pipeline_qualification_v2` controller. The v1 controller,
constructed pause wrapper, delivered adapters and all prior notes remain intact.
No v1 command, test or counted native attempt was executed.

**DESIGN CHECK.** Static review found a driver-only integrity defect before
execution: v1 checked the delivered source pins, then could replace an existing
pin with a later closure-file hash. A concurrent change between those reads
could therefore become the new expected value. It must instead refuse.

V2 checks the delivered manifest and the preserved v1 preparation's source pins,
rejects any overlap with a different expected digest, and rejects any differing
digest while adding the source closure. It rechecks the complete set immediately
before freezing setup. Later reference-output pins likewise may not overwrite a
different frozen pin, and their resolved paths must remain inside the complete
reference attempt. Both qualification notes and the original delivered adapter
note must match the reviewed commit. The preserved v1 sources are also pinned as
evidence, without becoming the executable controller.

The actual native plans, complete checkpoint copying, observed pilot fractions,
original-output parity, source-zero independent replay, watcher/native/lease
inspection and cost accounting are unchanged. Inspection of a pending stage says
that this inspection started no job; it does not imply that a previously launched
worker is absent. No scientific field, source, support rule, ceiling or gate is
relaxed. This is an unexecuted static correction, not a claimed passing fixture
or a consumed native retry.

The owner must review this successor before any command that starts a counted
stage. No tests, native starts, commits, acknowledgement or scientific admission
have occurred in this preparation.
