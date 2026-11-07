# Original-bank backlog admission

Week 5 packet section 3 assigns the BK queue to the original four slots as
they free. Runtime v5 instead prefers the additional bank for every family.
This successor corrects admission only; it does not change a scientific card,
resource floor, accounting limit, frozen source, checkpoint or live lease.

`week5_runtime_v6` searches slots 0–3 for family BK. Other admitted families
keep the v5 order: 4–7, then idle 0–3. An occupied original bank refuses a BK
start even if an additional slot is idle. The original admission mutex still
serializes both banks, policy admission still runs inside that mutex, and
exclusive creation still prevents an occupied lease from being replaced.

`week5_launch_v6` is the v5 launcher with only the runtime module changed.
The child, resume adapter, source closure, committed-design review, owner and
monitor handshake, output sealing, fresh replay, CPU accounting and release
behavior remain byte-equivalent. Old launchers, live jobs and leases remain
untouched. A valid stopped predecessor may resume through the new runtime
with all original pins retained and the new runtime/launcher pins added.

## DESIGN CHECK

- **Case and check:** a BK card must never take an additional-bank lease.
  Native constructed bank fixtures and targeted checks cover an idle bank,
  occupied original slots, completely occupied original bank with additional
  slots idle, other-family borrowing, failed resource admission, exact
  retained lease bytes and unchanged non-claim runtime code. Actual counted
  constructed execution separately verifies original-bank admission, fresh
  replay, sealed outputs, owner exit and lease release.
- **Smaller route:** if no original slot is free or resource admission fails,
  preserve the refusal and wait for authorized capacity. Never borrow an
  additional slot for BK, migrate a lease or stop an unrelated process.

This is an operational correction with no scientific result. The private
inspection records current BK lease placement and any historical mismatch;
it is not authority to alter a running job. Native validation is bounded to
constructed arithmetic, a 60 CPU-second ceiling, 0.25 GiB projected RAM,
two numerical threads and the existing no-GPU/no-paid policy.
