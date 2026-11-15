# Week 6 v2 budget-extension proposal

Prospective static proposal only, requested by the runtime owner November 15.
No runtime, test, calendar, budget registry or live plan changes; no numerical
checks or native job. The current v1 files and their pinned tests remain immutable.
Owner review is required before implementation or a new plan can use this route.

## Authority and the present gap

Standing S4 in `drive/WEEK_PACKET_20261018.md`, section 1, allows continuing and
logging a projection up to twice the original ceiling. Week5 `PACKET.md:73-80`,
amendment L, keeps that one doubling and amendment E's sample route; L(b) says
that beyond doubling, checkpointed work continues under the family ceiling when
a counted slot is idle. These are inherited operating provisions, not new
scientific estimands or permission to change an outcome gate. A later explicit
nonextendable card restriction would still prevail; owner review records authority.

The Week6 addendum keeps one original inclusive card allowance across carried
work, reference scopes, preparation, every attempt and replay. This proposal
preserves that original ceiling as the immutable accounting baseline. It makes
an authorized extension explicit rather than overwriting that baseline.

Current `week6_limits_v1.py:28-97` already preserves original identity/ceiling,
prior-campaign costs, cumulative preparation and receipt ancestry. Its immutable
revisions may increase preparation, but cannot change the original ceiling.
`week6_policy_v1.py:122-126` then always uses original ceiling minus cumulative
card charges. No current field expresses S4 or L(b). Merely writing a 40,000-second
ceiling into IN14's next budget row would correctly fail the present guard.

The Week5 v3 precedent is `week5_policy_v3.py:73-115`: all actual/failed work and
supervisor allowances count against family/campaign room; unclaimed reservations
cost zero, active work has its sampling envelope and unknown claimed work retains
its cap. Its remaining() has no new per-phase allocation. Week6 keeps those
rules and adds cumulative per-card accounting; v2 must preserve both parts.

## Minimal isolated files

Propose only four new runtime files: `week6_limits_v2.py`,
`week6_policy_v2.py`, `week6_runtime_v2.py`, and `week6_launch_v2.py`.
The limits/policy copies add the extension schema, mode selection and accounting
formula below. Runtime/launcher copies bind the v2 policy and explicit
`accounting_runtime=week6-v2`, record its admission mode and retain all existing
containment/accounting/byte/resource/monitor/drain behavior. No global monkeypatch.

Reuse unchanged `week6_child_v1.py` and `week6_resume_v1.py`. The child has no v1
accounting-runtime admission branch; it executes the pinned handler with the same
post-import two-thread guard. Resume already preserves module, inputs, family,
campaign, budget_key, scientific configuration and every predecessor pin. It can
copy a verified exited v1 checkpoint into a new v2 attempt while retaining old
runtime pins and adding v2 pins. No source/scientific module changes are required.
The running calendar imports immutable v1 clocks and remains untouched.

## Append-only receipt schema and explicit plan opt-in

Keep `_budgets/<key>-rNNNN.json`, existing revision numbering and hash ancestry.
Keep `key`, `family`, `ceiling_cpu_seconds` and `prior_campaign_cpu_seconds`
immutable. Keep `preparation_cpu_seconds` cumulative/nondecreasing and preserve
all prior evidence pins. Do not put original cost or preparation into a new zeroed
budget key. Existing rows with no extension field mean the original allowance.

A new reviewed revision may add `extension` with exactly:

- `mode`: `s4_double` or `lb_idle_family`;
- `authority_paths`: nonempty paths already pinned in the row's evidence_pins;
- `cost_evidence_paths`: nonempty pinned counted-probe/actual-charge records,
  reviewed by the owner as cost evidence; scientific outcomes do not size budgets;
- for L(b), `checkpoint_evidence_paths`: nonempty pinned existing design/fixture
  evidence that the handler supports sealed cooperative checkpoints and continuation.

The existing row-level owner_reviewed flag covers the whole decision. No new
curator permission step is inferred. Unknown/malformed modes or missing evidence
refuse. Allowed history is original -> s4_double -> lb_idle_family, with repeated
same-mode revisions permitted for cumulative preparation/evidence updates. No
backward transition, skipped doubling, arbitrary multiplier or repeated doubling.
The effective doubled allowance is always derived as 2*C from the ORIGINAL C;
it is never doubled from the last effective number. A planned checkpoint quantum
may straddle the 2*C boundary under a reviewed L(b) plan; there is no requirement
to waste the last fraction of a prior allowance before freezing a continuation.

Use the existing pinned plan `budget_receipt` as explicit opt-in. The allowance
mode comes from that exact bound revision, while latest cumulative preparation
still applies. A later extension row cannot silently promote an old plan. V1
readers can still validate the unchanged original fields and charge preparation;
they ignore extension fields and retain their original ceiling. V2 old/base-bound
plans also retain that ceiling. New v2 extension plans pin the chosen row and all
source/evidence closure. Immutable old plans are never rewritten or relaunched.

## Exact accounting and the idle condition

Let C be the original card ceiling, P its preserved prior-campaign card charge,
W the current Week6 card charge including the latest preparation total, every
claimed native attempt and each existing 30-second supervisor allowance. Let F
be remaining current Week6 family/campaign room from the unchanged charges().
Unclaimed reservations, nested diagnostic timing and old preparation revisions
are not charged again. The existing prior-campaign amount debits the cumulative
card allowance; it is not also rebooked as new Week6 family work.

    original room = max(0, min(C - P - W, F))
    S4 room       = max(0, min(2*C - P - W, F))
    L(b) room     = max(0, F)

L(b) removes only the nominal per-card stopping limit for that reviewed
continuation. Reports still show C, P+W, the one doubling and extension mode.
Family/campaign ceilings never increase. Each native plan still has finite
positive CPU/wall bounds; the launch cap is min(plan cap, admitted room minus
supervisor allowance). Missing child accounting still conservatively charges
the immutable attempt cap. Existing native whole-job accounting is unchanged.

Check L(b)'s idle condition at every new checkpoint quantum's dispatch, under the
same shared admission mutex used to claim its actual lease. Compute free counted
slots from the current eight-slot bank and active shared reservation; reject a
full bank, an unavailable eligible lease, or stale/unknown ownership as the
existing contract requires. Recheck after a stale review at actual claim. Record
mode, bound receipt hash, original/effective allowance, cumulative prior cost and
idle_slots_before_claim in ADMISSION.json alongside the claimed lease.

The slot remains valid for that finite checkpoint quantum. Other jobs filling
remaining slots do not revoke an already owned slot halfway through a calculation;
the next quantum must demonstrate idle capacity again. Do not invent an extra
requirement that every other queue be empty, and do not treat unclaimed budget
reservations as occupied CPU slots. Existing dispatch priority remains owner-run.
BK's original-lease restriction and shared reservations remain unchanged.

Runtime `available(plan, exclude=current_root)` still excludes the current
attempt before adding its exact charged/current-child CPU and supervisor allowance
in the existing guard. This prevents counting its heartbeat twice. Other running
attempts keep their current sampling envelopes. Final and failed receipts retain
exact ownership and charge reconciliation. No live extension raises a claimed
worker's frozen cap: pause/exit first, authenticate a new attempt, and preserve
checkpoint and all predecessor pins.

## Frozen prospective checks and rollout

The paired `WEEK6_BUDGET_V2_TEST_MATRIX.json` freezes 25 logical checks before code
changes: original and doubled arithmetic, once-only preparation, prior campaign
cost, immutable ancestry, exact plan opt-in, single doubling, every charged attempt,
family/campaign exhaustion, active/unknown accounting, same-attempt exclusion,
idle-slot races/shared reservation, immutable v1 behavior and native continuation.
No test has run; the matrix is a specification, not a passing fixture claim.

Proposed new selector: `tests/test_week6_budget_v2.py`; keep every pinned v1 test
unchanged. Reuse its constructed setup/contracts only as reference. Static diffs
must show unchanged clocks, caps, resource floors, accounting kernel, output guards,
thread limits, ownership, replay and scientific semantics. Unit checks precede a
small contained literal native complete and v1-pause/v2-resume case. Retain every
failure and resource receipt; no human source or corpus execution. The owner
reviews exact code and releases the serial slot before a bounded run.

After checks, a committed reviewed design and a new pinned launcher/runtime plan
are needed. Existing v1 plans/calendars keep their pins and behavior. Actual Week5
drain proof remains mandatory. No registry row, plan, source clock or cost is
changed merely by this proposal. A new accounting extension is logged in OPS_LOG
and the digest; it changes no scientific support gate or claim.
