# Current status

Updated September 27, 2026. Start here for current authority; historical execution
notes remain in the [operating archive](docs/archive/operations/README.md).

## Stage 13: running in Gear 1

The latest instruction approves all studies in **Gear 1**, finishing Friday
October 2 at **05:00 PDT**. New science stops before Thursday at 21:00 PDT,
reserving eight hours for replay/reporting. The frozen core has 514 cards: 503 CPU and 11 held GPU cards. One CPU worker runs at a time. Actual reader admissions, full capacity blocks and first production output replay. The 181-card extension is conditional on complete core results and whole-family time admission. Heavy GPU work is held. [Execution handoff](docs/design/stage-13/EXECUTION.md). [Review the plan](docs/design/stage-13/IMPLEMENTATION_PLAN.md) and the
[unchanged source](docs/design/stage-13/README.md).

## Stage 12: generation stopped; final report still owed

The submitted local queue drained September 25 at 02:45:13 PDT: 281 completed jobs,
14 retained failures and 31 deferred jobs, with zero scientific workers in the
September 27 at 15:19 PDT health inspection of Stage 12; Stage 13 now has its separate CPU worker. The local allocation expired
September 25 at 20:50 PDT. Seven admitted LP16 producer blocks and their summary
never launched: 1,248 calls remain unrun. Other failed admissions and incomplete
comparisons remain explicit. A drained queue is not a fully completed program.

The [interim packet](results/phase_2_4_stage_12/INTERIM_PACKET_20260925.md) and
[latest inspected health](results/phase_2_4_stage_13/HEALTH_20260927_1519.json)
preserve those dispositions. No Stage 12 restart or extension follows from Stage 13
planning. The original reporting checkpoint is September 27 at 18:17 PDT; the
**final packet is due September 28 at 06:17 PDT**.

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
