# Current status

Updated September 29, 2026. Start here for current authority; historical execution
notes remain in the [operating archive](docs/archive/operations/README.md).

## Stage 13: admitted queue complete; final packet pending

September 29, 00:21 PDT: the queue exited normally at 00:04 PDT with **686 complete,
three retained failures and ten blocked cards**. No running, pending or runnable card remains.
All 180 extension producers and the full comparison are recorded. Complete consumer replay
passes across all 26 reports, with frozen models, calibration and source separation verified.
All 699 manifests and their source/input bindings pass; the 518 prior core cards are unchanged.
[Comparison and exit verification](results/phase_2_4_stage_13/EXTENSION_RESERVE_20260929.json).

Actual coordinator/worker absence and released dispatch/GPU locks verify. The checkpoint
helper retains a fresh heartbeat and its held lock. The sole watcher retains verified loaded
sources, fresh scanning and actual delivery of the three final notices. Only the exact exited
coordinator watch was retired; terminal paths and health due **September 29 at 01:30 PDT**
remain. Memory and disk headroom pass; AC processor maximum remains 90% with boost disabled.
Earlier notification failure and the native queue-inventory sandbox limitation remain recorded.

Gear 2 remains the authorized allocation; a drained queue grants no new work. The primary
Qwen admission and its bounded correction failed; correction allowances are exhausted and
nine dependent cards remain blocked. The literal-confidence failures leave one further
consumer blocked. The original memory-type contrast remains void (L455); its separately
corrected development consumer is recorded (L456), with unequal lengths, one component and
no reserve rerun. Full GPU tuning and its fixed core comparison are complete; the extension
contains no additional full-tuned comparison. Preserve those limits in the final packet.

Next work is final packet assembly, reporting core and extension separately with complete
comparisons, examples, costs and deficits. Finish **Friday October 2 at 05:00 PDT**;
the science cutoff remains Thursday at 21:00 PDT. No new research, retry or cloud use.
[Execution handoff](docs/design/stage-13/EXECUTION.md).

## Stage 12: final endpoint closed; scientific deficits retained

The submitted local queue drained September 25 at 02:45:13 PDT: 281 completed
jobs, 14 retained failures and 31 deferred jobs. The local allocation expired
September 25 at 20:50 PDT. Seven admitted narrow-history producer blocks and
their summary never launched; 1,248 calls remain unrun. The broad human-history
main, failed admissions and incomplete comparisons remain explicit.

The [final evidence packet](results/phase_2_4_stage_12/FINAL_PACKET_20260927.md)
is assembled following the September 27 reporting-start checkpoint.
[Retained-record verification](results/phase_2_4_stage_12/REPORTING_START_20260927.json)
passes. The original interim is preserved; Stage 13 results are kept separate.
The September 28 at 06:17 PDT final endpoint is now [reconciled](results/phase_2_4_stage_12/FINAL_ENDPOINT_20260928.json): retained records are unchanged, the helper exited normally and its exact watch is retired. Original-week reporting costs are reconciled; separate local costs are unchanged.
A drained queue is not a fully completed program, and no expired allocation restarts.

## Supervision and next action

The existing durable watcher retains independent four-hour queue-health checks,
immediate failure/exit notices and original week checkpoints. Do not reset its clock
for documentation work. Pending operational events require actual inspection and
write-through before ACK. Future Gear 1 authorization never restarts expired work.

Next action: assemble the final packet from complete recorded comparisons; preserve the independent health inspection due September 29 at 01:30 PDT. Qwen correction allowances are exhausted; its failed admission and missing primary-reader comparison remain in the final deficit record.

## Navigation

- [Documentation map](docs/README.md): authoritative records by purpose.
- [Study index](docs/design/README.md): pending, reporting, historical and reusable material.
- [Workspace layout](docs/WORKSPACE_LAYOUT.md): folder ownership, retention and filing rules.
- [State](docs/STATE.md), [queue](TODO.md), [findings](FINDINGS.md): complete retained ledgers.
