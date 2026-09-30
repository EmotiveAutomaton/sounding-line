# Current status

Updated September 29, 2026. Start here for current authority; historical execution
notes remain in the [operating archive](docs/archive/operations/README.md).

## Stage 13: detector and memory healing complete; reader resource-held

The latest user request authorizes a thorough audit and healing where needed. The full retained-file audit passes, including completed output bindings and applicable saved-score replay. The original active queue drained normally: 686 complete, three failed and ten blocked cards. That audit identified the failed reader admission, original void memory contrast and missing strong detector comparison on the extension as the reasons for the separate healing pass below.

The frozen 33-card healing queue passed its setup checks and has now exited normally with 22 complete and 11 pending cards. Its three corrective families are: a named-category reader interface, information-matched memory conditions, and the frozen strong detector plus paired uncertainty. Original data, outputs, thresholds and failures are retained. The conditional Terra research-planning branch is not active because healing is necessary. [Audit receipt](results/phase_2_4_stage_13/VALIDITY_20260929.json) and [healing design](docs/design/stage-13/HEALING_20260929.md).

Finish **Thursday October 1 at 06:00 PDT**, the operator's stated assumption pending optional time preference. Science cutoff is **Wednesday September 30 at 22:00 PDT**, preserving eight hours for reporting. Existing Gear 2 continues: six single-thread CPU workers and one GPU, below-normal priority, AC maximum 90%, boost disabled. No paid compute. The exact old checkpoint helper has been retired and its Thursday successor verified; old receipts retain the original Friday schedule. The complete strong-detector comparison (L459) and all seventeen memory producers plus their complete consumer (L460) have passed full replay and internal write-through. Qwen admission remains held for actual GPU headroom; its ten descendants are gated. No workers or new failures remain. The exited coordinator watch is retired; the Thursday helper and sole watcher remain verified. Larger families pass measured capacity gates before release. [Live rollout and health inspection](results/phase_2_4_stage_13/HEALING_ROLLOUT_20260929.json).

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

The September 29 22:08 PDT health inspection verified the continued resource hold, intact records and healthy supervision, with no new failure or recovery. [Inspection](results/phase_2_4_stage_13/HEALTH_20260929_2208_PUBLIC.json) and [next-health ACK](results/phase_2_4_stage_13/HEALTH_20260929_2208_ACK_PUBLIC.json).

Next action: reassess actual GPU headroom at the next independent four-hour health event; resume the frozen reader work under a fresh queue identity only if its resource, admission and capacity gates permit. Retain the Thursday endpoint and all scientific deficits. [Complete memory and queue closure receipt](results/phase_2_4_stage_13/HEALING_MEMORY_COMPLETE_20260929_PUBLIC.json).

## Navigation

- [Documentation map](docs/README.md): authoritative records by purpose.
- [Study index](docs/design/README.md): pending, reporting, historical and reusable material.
- [Workspace layout](docs/WORKSPACE_LAYOUT.md): folder ownership, retention and filing rules.
- [State](docs/STATE.md), [queue](TODO.md), [findings](FINDINGS.md): complete retained ledgers.
