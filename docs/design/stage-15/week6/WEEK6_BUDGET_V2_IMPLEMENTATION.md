# Week 6 explicit budget extensions, v2 candidate

Owner-authorized implementation of the frozen [proposal](WEEK6_BUDGET_V2_PROPOSAL.md)
and [25-case specification](WEEK6_BUDGET_V2_TEST_MATRIX.json). This is an untested
review candidate. It creates no live budget revision, scientific plan, admission,
calendar change or research run. Original v1 files and previous receipts stay intact.

## Production scope

Four new modules implement the route: `week6_limits_v2`, `week6_policy_v2`,
`week6_runtime_v2`, and `week6_launch_v2`. The original native kernel, containment,
child and checkpoint adapter are reused without edits. The launcher requires
`accounting_runtime=week6-v2` and pins its source closure. The live v1 calendar
continues to import the original clocks.

The limits module validates the exact extension schema and the sequence
original -> S4 doubling -> L(b) idle-slot continuation. Same-mode revisions may
add cumulative preparation or evidence. An extension cannot start the history,
skip S4, move backwards, supply a multiplier, drop prior evidence, decrease
preparation or change original identity, family, ceiling or prior-campaign cost.
Doubling is derived once from the original ceiling and must remain finite.

The exact receipt pinned by the plan determines its allowance mode. The latest
valid revision determines cumulative preparation. A base-bound plan stays at its
original allowance after either extension; an S4-bound plan stays doubled after
L(b). V1 readers ignore the additional extension object and still enforce the
original ceiling. Tests B04, B05 and B21 directly check those separate cases.

Original mode subtracts prior-campaign cost and all current card charges from C;
S4 uses 2*C; L(b) uses remaining family/campaign room. `charges()` and `remaining()`
are AST-identical to v1. Preparation is added before the native-attempt loop, so
excluding a running attempt never excludes preparation. Claimed attempts retain
their existing 30-second supervisor charge. Prior campaigns debit the card once
and are not rebooked as current family work. The runtime adds its own measured
child use and supervisor once against room excluding that same native attempt.

`claim()` retains the existing shared mutex and exclusive lease creation. The
admission call inside that mutex checks actual occupancy and the shared
reservation. It records free counted capacity before the lease is created. BK
still claims only its original bank. The existing owned quantum is not revoked
merely because other leases later fill; a new quantum must pass admission again.
The immutable finite plan cap never increases in place.

ADMISSION records bound mode, receipt/hash/revision, original/effective allowance,
prior-campaign cost, current card charge, cumulative card/preparation charges and
idle slots before claim. L(b)'s effective card ceiling is JSON null, meaning that
the finite family/campaign allowance governs; the original C remains explicit.

The new-family compatibility check recognizes both v1 and v2 as readers of the
same family namespace. Other legacy readers still require terminal/native-owner
reconciliation. V1 itself is untouched and may conservatively delay one of its
new-family starts while a v2 attempt is live; no old reader is silently upgraded.

## Static preservation proof

The private `WEEK6_BUDGET_V2_STATIC_PROOF.json` lists exact old/new hashes and AST
function comparisons. The entire execution loop and failure charging are
unchanged. The claim function changes only its reported runtime identity; the
launcher changes only its version bindings. Policy clocks, campaign/family caps,
slot paths, retry behavior, active-use envelope, resource floors, thread limits,
ownership checks, native accounting, output-byte guards and full fresh replay
remain inherited. Actual Week5 drain evidence is still mandatory.

The limits changes are `extension_mode`, budget ancestry validation and exact
bound-mode reporting. Policy changes are allowance arithmetic, explicit v2
identity, the compatible-reader set and additional admission metadata. No
scientific handler, input, estimator, uncertainty rule, outcome gate or wake
policy changes. Static equality is evidence of narrow scope, not a test result.

## Frozen verification candidate

`tests/test_week6_budget_v2.py` defines exactly 25 tests, B01-B25, matching the
unchanged matrix. Pure controls use temporary registries and empty or temporary
lease namespaces. They cover every accounting defect and race named in the
matrix, including cumulative preparation during current-attempt exclusion.

B23 runs literal execute and independent verify in real native processes. B24
runs an actual v1 supervisor to a verified exited pause, then a distinct v2
supervisor to completion with unchanged payload and predecessor pins. A new
literal-only test fixture, `week6_budget_fixture_v2.py`, checkpoints [2, 3, 5]
under the adapter's already-approved `max_new_draws` operational field. One item
pauses; the remaining two complete; independent replay must sum to ten. This
fixture is additional test support, not a fifth production runtime module.

The native helper substitutes only temporary campaign/slot roots and a
constructed admission clock. Its child wrapper sets the temporary root for the
unchanged resume adapter before running the unchanged child module. Resource
guards and native containment remain real. Each supervisor exits before its
successor starts; tests assert exact operation CPU sums, fresh child identities,
thread caps, released leases and preserved predecessor bytes. No research
sources, live slots, watcher configuration or live registry are touched.

The proposed whole-selector harness is private
`.agent-state/week6-builder-b/week6_budget_v2_test_run.py`. It binds the complete
pytest process tree to a native kill-on-close job, uses two numerical threads,
retains source/output pins and whole-job CPU/commit/RSS/exit receipts, and imposes
180 seconds on the complete owned tree. It uses a unique workspace basetemp and
`-p no:cacheprovider`. Estimated cost is 15-40 seconds wall and under 30 CPU
seconds; this is a forecast, not measured evidence. The containment deadline is
the bound, and every actual failed or completed attempt remains chargeable.

Runtime-owner review of exact bytes and explicit serial-slot release remain
required before testing. Passing these controls would qualify this accounting
route, not admit any scientific card or grant a live extension. A later reviewed,
pinned, append-only receipt and new immutable plan are required for each opt-in.
