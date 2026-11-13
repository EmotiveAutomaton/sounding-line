# Exact legacy-reader retirement checker

Prospective implementation, November 13, 2026. This design is not an admission
or a committed-design claim. It implements only the first step of the owner's
reviewed static transition proposal. No runtime, policy, lease, old terminal or
live CH1 source is changed. No new-family PLAN or production retirement record
is created. RF/CP/IS/SV remain behind the existing transition gate.

## DESIGN CHECK

The case is a historically terminated accounting reader whose PID has since
been reused or is inaccessible. An exact audited terminal control-flow profile
can prove that this attempt cannot perform another accounting read without
querying that unrelated current PID. The check must reject an active, starting,
unclaimed, ambiguously failed or falsely labelled attempt. The source argument
is specific to the eleven pinned v8 control-flow files; constructed fixtures
cover actual-format COMPLETE, execute/verify PAUSED and fully accounted FAILED
records, ownership, reader versus native-exit distinctions and refusal cases.

The smaller route is no acceptance: unknown versions, absent historical launch
provenance, unresolved started operations, forced exits, unreadable evidence and
unreconciled leases remain held. There is no reduced evidentiary threshold and
no reinterpretation of a native access denial as absence. This is an operations
instrument, not a new scientific study or permission to alter the campaign.

## Scope and trusted inputs

`week5_reader_retirement_v1` is read-only and has no command-line certificate
writer, process query, signal, cleanup, launcher or accounting mutation. The
caller supplies an externally owner-reviewed authority path and its independently
pinned SHA-256. The authority names one exact attempt, repository, allowlisted
profile, operational metadata pins, started operations and authenticated current
successor lease pins. It also pins **recorded-at-launch** provenance binding the
actual command, owner identity, plan digest, launcher digest and time. The
checker does not manufacture that provenance from PLAN or capsule presence.
Unavailable authentic historical command evidence remains an owner gate.

An authority file is a trust input, not a self-authenticating certificate. Its
expected hash must come from the owner's reviewed admission context, never from
an untrusted attempt's assertion. Constructed authorities require an explicit
isolated-fixture mode and cannot pass the default production mode. This delivery
creates no production authority. Outputs always deny scientific-validation,
checkpoint-copy and campaign-transition admission; they report the narrower
reader-retirement finding and preserve terminal and Job CPU separately.

Only `week5-v8-post-reader-20261113` is implemented. The exact v8 runtime module,
launcher digest and eleven source hashes are frozen in the separate profile
module. Every source must match both the original PLAN pin and inert capsule
bytes. A `week5-v11` label in this v8 route is a refusal, not an exemption.
Other historical versions and currently compatible v11 readers need separately
reviewed classification; this checker alone cannot authorize the fleet transition.

## Evidence contract

The attempt is a direct child of the exact campaign directory. Its exclusive
claim, OWNER, monitor binding, admission and exactly one typed terminal must
authenticate and agree. Required JSON is bounded, rejects duplicate/nonfinite
values and traversals, and never follows reparse/symbolic paths. Source and
metadata bytes are authenticated again before return; top-level attempt and
both exact lease-bank inventories must remain unchanged. Enumeration failures
propagate as refusals, never empty inventories. The call is bounded to 256
reads, 2 MiB per file and 64 MiB total; exceeding those bounds refuses.

For each explicitly started operation, parent-child and worker native identities,
two-thread/no-GPU environment, child usage and complete Job usage are required.
The Job exit code must be known, with zero forced-termination margin. Terminal
CPU cannot undercount Job CPU; successful/paused cases must agree exactly within
1e-8 seconds, while a failed terminal retains any conservative excess. The
existing 30-second supervisor charge is reported separately, never added twice
or reset. A FAILED receipt requires `accounting_reconciliation_required=false`;
pre-child failures and forced-closure ambiguity are intentionally unsupported in
this first profile. COMPLETE also authenticates its operational manifest members
and verification; PAUSED authenticates the recorded checkpoint-manifest structure,
not participant/score files or copy compatibility.

No attempt-owned lease may remain in either bank. An occupied successor lease
must have a separately reviewed current hash and a different native birth and
attempt binding; it is read and preserved, never queried or removed. This does
not prove the successor is a compatible fleet reader. Later policy integration
must hold the common admission mutex, inventory every attempt, resolve actionable
unclaimed/starting writers and classify every other reader. The checker cannot
fence arbitrary old launchers that ignore the sole-owner protocol.

`inspect_post_reader` certifies only accounting-reader retirement. The separate
`inspect_observed_exit` route additionally requires externally authenticated
retained-handle observations for the exact owner and every recorded child, with
contained descendants closed, bound to the terminal and OWNER hashes. It does
not perform these observations, infer them from a terminal, or authorize copying.
Constructed handle records in the fixture prove schema behavior only.

## Exact source argument and excluded migration

- `week5_runtime_v8.py:60-62`: exclusive claim precedes all global reads; an
  attempt cannot simply reenter after terminal.
- `:85-121`: every operation is Windows-job-contained and exits its context.
- `:123-131`: PAUSED follows closed child context and returns.
- `:138-144`: COMPLETE follows the final global accounting read.
- `:146-160`: failure accounting and FAILED precede only exact lease release.
- `batch_runtime.py:56-60`: release reads/equality-checks/unlinks its own lease;
  it does not read the campaign plans.
- `batch_runtime_v8.py:118-131` and `native_job.py`: explicit native Job usage
  and containment closure; unknown exit/margin is not silently accepted here.
- `week5_launch_v8.py:29-63`: actual launched module, source capsule and monitor
  handshake. Capsule presence alone does not prove that invocation occurred.
- `week5_policy_v2.py:90-95`: an unclaimed new-family PLAN can break an old
  reader because family validation precedes zero charging.

CH1 remains running unchanged. This delivery neither requests its yield nor
implements v12 or resume changes. The previously identified sealed nested-yield
file versus generic copy-manifest mismatch remains an explicit later migration
gate. A reader-retirement finding does not repair that mismatch or replace
native-exit, full checkpoint, disk, cost or coverage checks.

## Constructed qualification, pending serial token

The focused suite has 24 checks: the four terminal/phase contracts; authenticated
semantic refusals; missing claim/owner/terminal; unknown profile; changed capsule;
old and authenticated successor leases; denied enumeration; inventory and
authority races; separate observed-exit evidence; default refusal of constructed
authority; complete fixture-handler/replay parity; pre-child and forced-exit
holds; conflicting terminals. Successful checks patch native lookup to raise and
compare all constructed evidence bytes before and after. Semantic negative
fixtures intentionally repin their invented authority to test more than hashes.

The fixture reads no real attempt or corpus. It copies the eleven pinned old
source files as inert bytes and never imports or executes them. An optional
future counted fixture adapter prepares a fresh constructed case and independent
replay; it is supplied as source only and is not launched by this request.
These checks do not reproduce an actual legacy-reader admission race or native
exit observation. That later native qualification and policy/launcher integration
remain separate owner gates.

Requested focused test bound: 180 wall seconds, 150 complete native Job CPU
seconds, two numerical threads; unchanged commit/RAM/disk floors. Use the owner's
serial token, a new workspace-local pytest basetemp and no cache provider. Pin
all candidate, fixture, test and exact-profile bytes before/after. No tests have
run at preparation. A passing suite is evidence for this checker only, not
admission to write RF/CP/IS/SV plans or issue production retirement certificates.
