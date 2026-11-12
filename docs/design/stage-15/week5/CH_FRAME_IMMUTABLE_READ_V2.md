# Preserve the completed chess frame during roster selection

Prospective isolated engineering correction, November 11, 2026. The completed
three-month merge and original v1 roster/fixture remain immutable. No source
selection, player quota, tie rule, ordering, eligible-game threshold, score or
resampling control changes. Production admission remains with the owner.

## DESIGN CHECK

An ordinary SQLite `mode=ro` connection can create WAL/shared-memory sidecars.
The previously recorded merge-inspection incident demonstrates why a read query
must not be assumed to preserve the authenticated source directory. The v2
selector uses `mode=ro&immutable=1` only for an explicitly completed and
checkpointed source frame. It first refuses any nonempty WAL or rollback journal;
it must not silently ignore uncheckpointed source updates. The unchanged
selector then requires exactly the three complete April/May/June checkpoint
flags. Runtime source hashes, complete producer/replay receipts and no live
producer remain owner admission requirements.

The temporary candidate database and largest-remainder allocation are unchanged.
Every selected row, count, source priority and final player order must equal v1
on the same complete frame. The isolated fixture uses immutable access for its
independent small-frame oracle too, and snapshots the full source-frame directory
before selection, raw sampling and replay. It refuses changed bytes or extra
sidecars after those operations.

Constructed checks cover a clean checkpointed WAL-mode source, exact original
selection equality on a private oracle copy, missing/incomplete month flags,
an actual outstanding WAL transaction, and the complete original raw PGN
collector versus the bounded sampler with all three months. No human source,
engine, model or destination copy is needed. A focused pass is not production
admission or a new native source qualification by itself; it supplies the
owner's requested source-preservation and reference-parity evidence.

All five focused checks passed, consuming 7.046875 native Job CPU seconds and
7.735 seconds wall time. Source inventory/byte equality was checked while the
immutable connection was open as well as after closing it. The tested code
pins and the complete constructed parser/reference receipt are retained in the
private owner review. No real completed frame was opened by this qualification.

`week5_ch_backhalf_roster_v2` and `week5_ch_backhalf_fixture_v2` are separate
successors. Earlier manifest hashes remain retained. A future plan must pin this
new selector and fixture and the original scientific/raw-source definitions,
with the same complete-source dependencies, cost accounting and resource floors.
