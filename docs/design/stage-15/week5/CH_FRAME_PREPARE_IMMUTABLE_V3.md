# Close the sampler preparation input-read path

Prospective minimal v3 correction. Preserve v1/v2 source files, their designs,
focused checks and the completed counted v2 qualification with its recorded cost.
No earlier result is overwritten or redescribed as if it exercised this repair.

## DESIGN CHECK

The v2 selector's immutable connection is correct but incomplete as a production
protection: `week5_ch_sample_bounded.prepare` opens the authenticated input frame
before invoking the selector. That ordinary SQLite connection can create WAL
or shared-memory sidecars even when the selector itself does not. The earlier
v2 checks observed the selector's open connection and complete-run endpoints;
they did not observe this separate preparation connection while it was open.

`week5_ch_backhalf_roster_v3` supplies the exact existing `prepare` checks and
return tuple with its input connection changed to v2's `completed_frame` helper.
That helper uses immutable read-only SQLite after refusing outstanding nonempty
WAL/rollback-journal data. Completion flags, salt hash, exact raw-month roster,
raw source hashes, selected rows, allocation counts and raw-record denominator
are unchanged. The sampler's output/scratch database remains writable.

The wrapper scopes only the sampler's `prepare` entry point and the existing
selector entry point to the current child invocation, restoring both on exit.
It does not monkeypatch SQLite globally or edit any earlier module. Its extra
configuration pin binds the new preparation adapter; the existing selector and
raw sampler implementation pins are retained. Both execute and fresh full raw
verification use the repaired route.

Constructed checks observe inventory and hashes after each SQL operation while
the actual preparation input connection is open, and after close. They compare
the complete tuple to the original prepare on a separate private oracle copy,
preserve original incomplete-frame and wrong-salt refusals, and reject a real
outstanding WAL before stale data can be read. The full three-month constructed
raw-source fixture observes both execute and verifier preparation connections,
checks original collector byte parity and preserves the frame directory.

All five constructed checks passed in 7.0 native Job CPU seconds and 7.418
seconds wall time. Exact tested source hashes were unchanged before/after the
run. The raw-reference case observed both preparation SQL statements during
execution and again during full verification, with source inventory equality
while each connection was open.

This is source-preservation engineering only. Original source selection, roster,
positions, missingness, row order, quotas, costs and scientific controls are
unchanged. No real completed frame, engine or corpus is opened by these checks.
The owner reviews this new pinned route and current resource/cost requirements
before production admission. The v2 counted qualification remains valid evidence
for its own implemented boundaries; it is not silently upgraded to v3 proof.
