# WATCH ACK FIX 20261101

**Hypothesis.** Can a completion remain acknowledged when the transport returns after the owner has already recorded it?

**METHOD.** Reproduce late success, retryable failure, uncertain delivery, exhausted attempts, cancellation and restart against disposable outboxes. Verify that acknowledgment timestamps, queue receipts and error evidence survive, already processed rows cannot be selected again, and duplicate acknowledgment cannot move the independent health deadline. Run the existing transition and health checks, then perform a controlled watcher-only reload with an exact native identity and preserved event snapshot.

**Found.** The watcher preserves completed acknowledgments across late delivery and cancellation; the tested repair is loaded with event history and the health deadline unchanged.

The table reports operational checks, not scientific outcomes.

| Check | Evidence |
|---|---|
| Original interleavings | Eight expected regression failures; one retry-limit check passed |
| Repaired targeted suite | All seventy checks passed |
| Persistent event records | All 2,807 unchanged across reload |
| Pending unacknowledged events | None |
| Calendar and health deadline | Unchanged |
| Research workers | None; Gear 2 has drained |
| Ready buffer | Zero of eight required cards |

The pending selector and claim/cancellation/restart updates now exclude acknowledged rows. Late transport settlement retains the transport receipt or error but preserves the acknowledgment state. No historical event is normalized, deleted or fabricated; the previously reconciled legacy label remains preserved. The new native watcher advertises the verified source digest and has a fresh scan. These tests use no real message transport. A future naturally occurring late-delivery race has not yet been observed on the new service, so live source adoption and fixture correctness remain distinct from that observation.

The complete D5 instrument landing and its event acknowledgment remain recorded under OPS-S15-W3-D5-IDENTICAL-CORPUS. The current D5 queue row now reflects its completed numerical work and retained cost balance. Scientific calibration and human scoring are not admitted by this maintenance result. The four research slots are unused because the ready buffer is unfinished and remaining D5 calibration needs cost admission; this is a capacity defect, not an intentional gear pause. Exact nonoverlapping research-slot intervals since the D5 launch are retained in the receipt. They do not measure total processor utilization and must not be added to overlapping historical snapshots.

**Means.** Delivery bookkeeping no longer reopens processed work in the tested interleavings. No scientific runner, calibration rule, CPU ceiling, GPU parking rule or paid-work closure changes. No tests were harvested from the operational wake. New scientific results still require their own full write-through before acknowledgment. Current records remain local; no publication occurs.
