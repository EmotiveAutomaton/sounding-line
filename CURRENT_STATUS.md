# Current status

Updated September 27, 2026. Start here for current authority; historical execution
notes remain in the [operating archive](docs/archive/operations/README.md).

## Stage 13: running in Gear 1

The latest instruction approves all studies in **Gear 1**, finishing Friday
October 2 at **05:00 PDT**. New science stops before Thursday at 21:00 PDT,
reserving eight hours for replay/reporting. The frozen core has 514 cards: 503 CPU and 11 held GPU cards. One CPU worker runs at a time. Actual reader admissions, full capacity blocks and first production output replay. The 181-card extension is conditional on complete core results and whole-family time admission. Heavy GPU work is held. [Execution handoff](docs/design/stage-13/EXECUTION.md). [Review the plan](docs/design/stage-13/IMPLEMENTATION_PLAN.md) and the
[unchanged source](docs/design/stage-13/README.md).

## Stage 12: generation stopped; final packet assembled

The submitted local queue drained September 25 at 02:45:13 PDT: 281 completed
jobs, 14 retained failures and 31 deferred jobs. The local allocation expired
September 25 at 20:50 PDT. Seven admitted narrow-history producer blocks and
their summary never launched; 1,248 calls remain unrun. The broad human-history
main, failed admissions and incomplete comparisons remain explicit.

The [final evidence packet](results/phase_2_4_stage_12/FINAL_PACKET_20260927.md)
is assembled following the September 27 reporting-start checkpoint.
[Retained-record verification](results/phase_2_4_stage_12/REPORTING_START_20260927.json)
passes. The original interim is preserved; Stage 13 results are kept separate.
The final endpoint reconciliation remains **September 28 at 06:17 PDT**.
A drained queue is not a fully completed program, and no expired allocation restarts.

## Supervision and next action

The existing durable watcher retains independent four-hour queue-health checks,
immediate failure/exit notices and original week checkpoints. Do not reset its clock
for documentation work. Pending operational events require actual inspection and
write-through before ACK. Future Gear 1 authorization never restarts expired work.

Next action: land complete Stage 13 cells and inspect conditional continuation at the independent health checkpoints. Heavy training and sustained GPU inference stay
held under Gear 1; available capacity is not permission to change gears.

## Navigation

- [Documentation map](docs/README.md): authoritative records by purpose.
- [Study index](docs/design/README.md): pending, reporting, historical and reusable material.
- [Workspace layout](docs/WORKSPACE_LAYOUT.md): folder ownership, retention and filing rules.
- [State](docs/STATE.md), [queue](TODO.md), [findings](FINDINGS.md): complete retained ledgers.
