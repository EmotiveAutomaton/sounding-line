# Codex operations

## Current waiting policy, 2026-09-19

The owner now requests a queue-health inspection every four hours. Private
`health_interval_seconds: 14400` enables an independent persistent `health_schedule`
in watcher status, alongside `transition_only: true` for immediate transitions.
This explicitly supersedes the prior prohibition on periodic health wakes; older
ETA scheduling instructions remain historical. Do not add extra ETA wakes.

The next health event is due on the first service scan at or after its deadline
(60-second scan cadence). Ordinary hooks and unrelated ACKs do not defer it.
Its own documented ACK rearms four hours later; duplicate ACKs do not reset it.
One pending event, active-owner deferral, cancellation and uncertain-send refusal
remain. A sleeping/offline host or unresolved delivery can delay inspection.
The event instructs the operator to inspect identities, progress/output freshness,
failures, locks, resources, eligible authorized work and watcher delivery. Document
and recover within existing authority before ACK. A Gear 1 pause never authorizes
restarting parked GPU inference. No scientific deadline or budget resets.

All 122 watcher/runtime checks and 21 locks pass. Live watcher source adoption and
its first deadline verify; future idle delivery of the new event is unobserved.
Receipt: ../results/phase_2_4_stage_11_2/HEALTH_CADENCE.json. For rollback, cancel and
wait for watcher exit, restore the previous watcher source/configuration retained
in .agent-state/health-watch-20260919/, then resume under the same owner. Preserve
the outbox, scientific processes and original checkpoint schedule.

## Prior transition-only policy, 2026-09-12

September 19 terminal-schema repair (OPS-S11.2-I5): process supervision now
recognizes existing terminal statuses in uppercase or lowercase, while refusing
malformed or unfinished states. The prior admission disappearance alert was false
and remains retained beside its actual completion. All 109 watcher checks pass;
only the watcher was reloaded, with the same owner, outbox and scientific native
identities preserved. Loaded source and fresh scanning verify; later idle delivery
is a separate observation. [Receipt](../results/phase_2_4_stage_11_2/MONITOR_REPAIR.json).

The curator replaced routine ETA/liveness wakes with transition-only operation.
Private watcher configuration sets `transition_only: true`; explicit deadline
plans and elapsed-time fallback cannot create events in that mode. Successful
terminal produces, failures and predefined checkpoints still notify the owner.
`process_watches` binds native PID, creation time, executable and terminal paths;
disappearance or PID reuse without a final produce writes one monitor failure.
Inaccessible identity is a monitoring fault, never a claim of process death.
The service polls cheaply; healthy observations never invoke an agent.

Record native identities and expected outputs before ending a turn. No Stop
hook, recursive queue rule or remaining-work condition may extend it merely
because a simulation is running. Existing timer-based instructions below are
historical and superseded. No scientific process is restarted for monitoring.

Delayed notices can already have a full landing and a local ACK before their native
message reaches the owner. Reconcile that original landing and record actual delivery
separately. The installed experimental protocol exposes `thread/queue/list` and
`thread/queue/delete`; the CLI queue command has no cancellation flag. The September
13 inspection could not reach the local control socket (Windows error 10050), so no
native messages were listed or removed. The local watcher continues transition
detection, but this check does not establish future message transport. Preserve
uninspected notifications; do not restart science or add timer wakes to retry queue
cleanup. [Inspection](../results/maintenance_20260912/QUEUE_BACKLOG_INSPECTION.json).

The subsequent bounded native API helper successfully listed the existing owner
queue without a proxy socket, verified the one pending submission against its two
already completed landings, removed exactly that submission and confirmed an empty
inventory. It started no thread or model turn and restarted no existing process.
Use the installed native API for such bounded owner-only inspection; retain the
original failure. Queue cleanup does not establish future CLI delivery. [Retirement
receipt](../results/maintenance_20260912/QUEUE_BACKLOG_RETIREMENT.json).

The September 13 history completion exhausted five CLI attempts and left science idle. The watcher now uses `queue_transport: native-api` through `tools/codex_queue_api.py`: a bounded native helper lists and adds only the existing owner queue. A stable event-batch identity permits reconciliation without duplicating a pending message. Missing or ambiguous receipts become `unknown`, requiring inspection; no backend fallback or blind retry occurs. Private helper stderr is retained. Actual API acceptance, list, deduplication and exact retirement pass, as do 96 affected checks. The watcher records the loaded transport source hash. The completed earlier-draft four-job chain subsequently reached the owner after its final response on the first attempt. Its persisted delivery record and full producer inspection verify actual idle delivery separately. [Delivery receipt](../results/maintenance_20260912/NATIVE_QUEUE_IDLE_DELIVERY.json). [Receipt](../results/maintenance_20260912/NATIVE_QUEUE_TRANSPORT.json).

The curator authorized the full Claude/Fable to Codex/GPT transition on 2026-09-05.
`AGENTS.md` is the canonical contract; `.agents/skills/grind/SKILL.md` is its operational
skill. `CLAUDE.md` is a compatibility pointer, and the original contract is archived.
The coding model is the user's configured `gpt-6-astra` at `xhigh` effort. Scientific
models, Anthropic reference arms, frozen adapters, research locks, and spending rules
are independent of the coding operator and were not migrated to different models.

## Shared approval defaults (2026-09-06)

The user-level Codex configuration now selects `workspace-write`, `on-request`, and
`approvals_reviewer = "auto_review"`. Eligible escalation goes to the native reviewer;
the project hook never grants blanket permission to leave the sandbox. Existing
research locks, ownership, and spending constraints remain in force. The user-level
AGENTS.md points to the active shared behavior/security contract on this workstation.
Project instructions remain authoritative for this research program.

PermissionRequest no longer emits a human-input notification; explicit question
tools still do. Completion notifications are unchanged. Network access stays off
by default because the optional destination-filtering candidate did not pass the
installed CLI's compatibility checks. Required access uses automatic review.
An existing Full Access session must adopt the new permission mode in the client;
saved settings alone do not prove that an already-running session changed.

The latest reconciliation verified the saved defaults at both Sounding Line entry points
and the installed shared command-rule hash. The supported client permission menu was set
to **Approve for me**. In this installed extension that preset uses the native automatic
reviewer (`guardian_subagent`, accepted alongside `auto_review`) with a workspace sandbox
and network access off. Effective adoption is now verified from the native rollout's
fresh turn context at 2026-09-06 15:41:34 UTC: `on-request`, `auto_review`,
`workspace-write`, and `network_access: false`. The managed filesystem profile permits
the enclosing SoundingLine workspace and temporary directories, with the runtime's
protected metadata exclusions. This is not an OS write prohibition on `reference/`;
the separate project instruction forbidding reference edits still applies.

Actual `UserPromptSubmit`, `PreToolUse` and `PostToolUse` audit rows name this new turn.
The earlier successful targeted window reload already established native startup-hook
execution. The final permission-reload helper did not invoke its command: it stopped
when the command-palette match was not unique, but its queued continuation succeeded.
The new turn adopted the supported client permission selection without another reload;
do not describe the failed second invocation as a successful reload. No further restart
is needed for the verified settings. Local `.agent-state/permission-adoption-evidence.json`
contains the native turn context and audit rows; the earlier configuration and reload
receipts remain separate historical evidence.

## Reading continuity (curator-approved 2026-09-06)

AGENTS.md and the theory index now allow the complete initial theory read to span context
windows. Compaction resumes the first unread portion; it does not restart the entire folder.
Source changes invalidate the affected read progress. Every recovery still reloads the
shared/project instructions, current STATE/TODO/FINDINGS and theory index; scientific work
also reloads relevant sections and correction history. The local progress record is
`.agent-state/theory-read-progress.json`. It records reading, not scientific acceptance.

The updated reminder actually executed through PostCompact in the registered owner; the
SQLite audit and `.agent-state/recovery-rule-native-receipt.json` record the observation.
Both entry points still discover nine trusted hooks. The focused runtime suite passes
59 tests after the reminder change. This rule grants no additional execution authority.

## Workspace and ownership

The selected project folder contains `sounding-line/` (the Git repository) and
`reference/` (separate research checkouts). The enclosing `AGENTS.md` routes into this
repository. Run `./start_codex.ps1` or open the enclosing project in Codex. Native discovery
showed that these are distinct configuration roots: installation writes a hook set at
each root and an enclosing skill pointer. Each entry point discovers one set and one
grind skill. Do not also install user-level copies: Codex merges matching hook sources.
Generated hook paths are machine-local and ignored by Git; rerun setup after relocation.

`tools/codex_watch.py status` reports the sole owner thread, watcher heartbeat, pending
events, hook receipts, and notification failures. The owner ID is local state, not a
committed session identifier. Starting another session does not seize ownership.

The migration baseline is `.agent-state/baseline.json`: revision, existing dirty files,
Windows process ownership, run contract, adapter registry, and configuration hashes.
It is not a portable backup of model weights. Preserve ignored adapters, the model cache,
the existing virtual environment, and sibling references when moving machines.

`docs/STATE.md` is the current research handoff, including closure and the newly supplied
maintenance errata. This runbook records environment mechanics, not scientific warrant.
An old scheduler-status snapshot showing a running closure cell is not evidence of liveness.

## Hook mapping

Each row maps an old operating behavior to its Codex implementation and its limit.

| Behavior | Codex implementation | Boundary |
|---|---|---|
| Edit-time theory and design checks | `PostToolUse` calls `tools/codex_hooks.py`, then the existing linters | Parses `apply_patch` add/update/move/delete paths; shell calls scan Git changes. Bad payloads and Git failures cannot report a clean check. Post hooks provide corrective feedback after the write. |
| Command policy | `PreToolUse`, `tools/codex_policy.py` | Destructive disk/shutdown commands are denied; simple static reads are allowed inside the sandbox; everything else uses native approval. Explicit escalation is never auto-approved by this script. |
| Completion notification | `Stop`, `tools/codex_notify.py` | Uses `last_assistant_message`, never Claude transcript parsing. Keeps the existing ntfy topics, acknowledgment priority, and short snippet. |
| Needs-input notification | Pre-hooks on explicit user-input tools | Codex has no equivalent `Notification` event. Per shared Agent Core policy, automatic approval reviews do not page the curator; manual approval UI is the client's responsibility. |
| Startup and context recovery | `SessionStart`, `PostCompact`, `UserPromptSubmit` | Reload reminders identify canonical documents, current ownership, and pending landings. They do not claim that the agent has read those files. |
| Detached queue completion | `tools/codex_watch.py` plus `codex queue` | Durable final-produce events target one existing conversation; queue acceptance and completed write-through are separately recorded. |

The old classifier allowed arbitrary interpreter scripts, Git publication, and relative
recursive deletion based on command text. Those broad allowances are not transferred into
Codex escalation permissions. Ordinary authorized workspace work uses the native sandbox;
network, external writes, and other escalations use the platform's approval mechanism.
The original migration left that reviewer manual; the 2026-09-06 shared harness update
selects native automatic review while preserving the sandbox and project restrictions.

Notifications use `~/.codex/sounding-line/bus.conf`, copied locally from the existing
private configuration. Never commit or print that file. A failed POST is recorded as
failed or uncertain without printing credentials. Repeated delivery of the same hook
event is deduplicated; uncertain network writes are not retried blindly.

The original user-level Claude hooks remain available for other workspaces and rollback.
The retired project-local hook configuration is archived at
`archive/agent-runtime/settings.claude.json`; `.claude/settings.json` retains permissions
but no longer registers the old project hooks.
Do not run a Claude operator concurrently with the registered Codex owner here.

## Installation and exact hook trust

From the repository root, using the installed Codex executable and existing Python:

```powershell
python -B tools/codex_setup.py prepare --thread YOUR_EXISTING_CODEX_THREAD_UUID
# Inspect .agent-state/install-plan.json and the referenced scripts.
python -B tools/codex_setup.py install
```

Installation writes the reviewed project definitions, private notification configuration,
and a hidden Windows logon watcher. It preserves exact prior bytes and an installation
receipt for rollback. User-home and project `.codex` writes may require sandbox approval.
No models or dependencies are installed and no research engine is launched.

Codex separately requires review and trust of each exact hook definition. In the CLI,
use `/hooks`. For this explicitly authorized transition, `tools/codex_control.py
trust-reviewed` uses Codex's configuration API to record only the current native hashes
of the reviewed Sounding Line definitions. It verifies source hashes against the prepared
plan, requires complete discovery, preserves a private configuration backup, and checks
that Codex subsequently reports the definitions as trusted. No bypass flag is used.
`codex_control.py inspect` reports discovery and trust without changing configuration.
Resume the project conversation after changes so its configuration is reloaded.

The installed Windows CLI accepts `codex queue`, but its managed-daemon lifecycle command
is Unix-only. Do not install a Unix daemon recipe on this machine. A successful queue
receipt proves acceptance, not that an idle IDE session resumed. Require an actual wake
acknowledgment before describing unattended operation as verified.

## Watching and landing results

```powershell
python -B tools/codex_watch.py bind YOUR_EXISTING_CODEX_THREAD_UUID
python -B tools/codex_watch.py register-queue
python -B tools/codex_watch.py baseline --since BASELINE_EPOCH
python -B tools/codex_watch.py scan
powershell -NoProfile -File tools/start_codex_watch.ps1
python -B tools/codex_watch.py status
```

Baseline only once, after reconciling existing records. During a migration, use the
original baseline time: later produces must remain pending. The watcher does not read
per-artifact cases or oracle state. It watches stage manifests' declared produces,
the reviewed general-queue inventory, final packets, and interrupts, with an eight-hour
liveness fallback. Unchanged files use stat checks; changed files are hashed in chunks.

The general-queue inventory is generated explicitly after reviewing the queue code:
`register-queue` reads the constructed stage list without running its `main`. The waiting
service never imports that runner. A changed queue source requires re-registration,
so composed and generated produces cannot silently disappear from monitoring. The
existing always-run multiplicity audit is watched at its actual `results/multiplicity.json`.

To add another final produce, run `python tools/codex_watch.py register results/PATH`.
For a new stage, add its manifest to `.agent-state/watch.json`; the service reloads this
configuration each scan. These are monitoring operations, not research-stage creation.
Study-to-runner-to-queue translation remains manual and agent-owned.

The SQLite outbox persists across crashes. One kernel-held lock prevents two watchers.
An accepted message remains `queued` until the operating agent completes the full grind
write-through and runs `python tools/codex_watch.py ack EVENT_ID`. One outstanding batch
prevents repeated notifications to a disconnected conversation. New produces accumulate.
Explicit failures retry with backoff at most five times. A timeout, crash during send,
or zero exit without a queue receipt becomes `unknown` and requires queue reconciliation;
there is no unsupported claim of exactly-once transport across a crash.

`python tools/codex_watch.py cancel` cancels future sends, including a check immediately
before dispatch. To retry a reconciled failed or unknown event, use `retry EVENT_ID`.
To hand off: cancel, reconcile old queued messages, then run
`handoff NEW_THREAD_UUID --previous OLD_THREAD_UUID`, followed by
`powershell -NoProfile -File tools/start_codex_watch.ps1 -Resume`.
The logon helper honors cancellation and does not silently resume a cancelled watcher.
An explicit resume waits for the previous helper to release its kernel lock before
clearing cancellation. A timeout leaves cancellation in place.

## Estimated check-ins and grouped notifications (2026-09-11)

Before yielding while work runs, estimate the next point needing inspection from current
progress or existing measured rates. Set a conservatively early check-in, normally with
about twenty percent margin. For healthy long GPU work, thirty-to-sixty-minute checks are
usually enough; use a shorter interval only for an imminent intervention.

```powershell
python -B tools/codex_watch.py schedule 3600 --expected-seconds 4500 --reason "Check the running job before estimated completion"
python -B tools/codex_watch.py status
```

The first value is seconds until the check-in; expected-seconds is seconds until the
estimated milestone. The owner-scoped plan persists in the operational database and is
visible as `wake_plan` in status. The watcher emits one deadline event when due, even if no
file changes. Document the inspection before ACK, then replace the plan for the next useful
milestone. A pending deadline cannot be silently replaced. Allowed plans span one minute
to eight hours; those bounds are validation limits, not recommended polling intervals.

The watcher still scans cheaply once per minute, without invoking a model. Successful
produces remain in the outbox until the planned check-in and are delivered together.
Failures, pauses, interrupts and exact paths listed in private `urgent_paths` bypass the
delay; register the active queue's terminal COMPLETE path there. Each delivered result
still needs its full write-through. This changes notification timing, not scientific
acceptance, source locks, gear, spending, or the one-outstanding-batch ownership rule.

Routine delivery is suppressed while the owner has a fresh active hook. An active marker
older than fifteen minutes permits recovery if hooks stopped arriving. Without a plan,
routine notices wait at least thirty minutes after recent owner activity, acknowledgment
or delivery; the eight-hour fallback likewise accounts for recent attention. Queue errors
and ambiguous sends retain their previous retry/reconciliation behavior. `delivery_decision`
in status records the last decision taken by the actual service.

Validation: all 79 targeted scheduling and existing runtime checks pass, including grouped
successes, one-shot persisted deadlines, urgent backlog priority, active-owner suppression,
stale-owner recovery, fallback reset and invalid-plan refusal. The same-owner hidden watcher
restart loaded the new source and resumed scanning while the scientific worker and all 380
frozen sources remained unchanged. The first scheduled deadline reached this owner after
its preceding final response, confirmed at 16:04 UTC on September 11. Its event was created
seven seconds after the planned deadline and queued six seconds later; queue acceptance
and actual owner delivery are separately recorded. The same worker continued progressing
under retained cooling limits. Receipt: `FIRST_DELIVERY_INSPECTION.json` in the folder below.
Private prior source/config/rule copies and installation receipts are retained under
`.agent-state/wake-pacing-20260911/`. Rollback restores the previous watcher/config only after
its kernel lock is released, retaining the event database and scientific workers.

## Verification

```powershell
$py = '.\.venv\Scripts\python.exe'
& $py -B tools/verify_locks.py
& $py -B tools/theory_lint.py --all
& $py -B tools/design_lint.py --changed
& $py -B -m pytest -q -o addopts= -p no:cacheprovider --tb=short
& $py -B tools/test_s7.py
& $py -B tests/test_stage8_guards.py
```

The last two are standalone guard programs; pytest discovery does not execute them.
They use temporary roots and fake model servers. The lock perturbation test now uses
a temporary copy and never writes a live locked artifact. On this machine pytest's
existing user temp directory is inaccessible inside the Codex sandbox; rerun through
the normal approval path if it fails there. Do not rebuild the live virtual environment.

For live acceptance, confirm `/hooks` discovery/trust, a recorded real hook firing,
ntfy POST acceptance with the Codex title, one wake into an idle existing thread, and
the event acknowledgment after its write-through. Fixture tests alone cannot prove
the IDE's idle behavior or the physical watch's notification display.

Installation acceptance recorded on 2026-09-06 (operational evidence, not research results):

| Check | Observed result |
|---|---|
| Full pytest suite | 160 passed; includes failure cases, ownership, retries, deduplication, linter payloads, and rollback |
| Standalone isolation guards | Stage 7: 30/30; Stage 8: 22/22 |
| Research locks and documentation linters | All 21 locks hold; theory and changed-design checks pass |
| Native discovery at both workspace entry points | Nine trusted hooks and exactly one enabled grind skill each; no discovery errors |
| Existing notification bus | Accepted both labeled completion and input test messages; physical display unobserved |
| Live watcher restart | New process, current source hashes, fresh heartbeat, seven pending events preserved with identical queue IDs and attempt counts |
| Idle conversation wake | Passed: the migration probe resumed the existing conversation after its final response; the native queue no longer contains the probe |
| Native hook execution in the operating conversation | Passed after targeted window reload: actual SessionStart, UserPromptSubmit, PreToolUse and PostToolUse audit entries in the registered owner, with startup context delivered by Codex |

Machine-local receipts are in `.agent-state/`: `hooks-discovery.json`,
`skills-discovery.json`, `notification-check.json`, `restart-check.json`,
`hook-trust-receipt.json`, and `install-receipt.json`. `native-hook-check.json` records
that creating an empty ephemeral thread without a model turn did not fire a hook;
it is not a passing native execution check. The watcher reports `delivered_at` when
its prompt reaches the owner; `acknowledged` remains reserved for completed write-through.
`wake-probe-receipt.json` records the actual conversation acknowledgement and the remaining
native queue. This receipt was recorded by the agent, not fabricated as a hook event.
The research landing batch subsequently reached the owner and left the native queue.
`landing-delivery-receipt.json` records its seven matching hashes, readable file formats,
fresh watcher heartbeat, and absence of native hook audit entries at that earlier inspection.
Its final-produce events remained unacknowledged until the subsequent full write-through
and corrected-packet delivery in L371/L372; all seven are now acknowledged. Checking final-file metadata does
not convert a final-produce event into a liveness-only event.

If a queued turn arrives but the hook audit remains empty, do not declare native execution
verified. Reload the VS Code window (`Developer: Reload Window`), reopen the same conversation,
and inspect `codex_watch.py status` after its first tool call. Fresh helper discovery has
already reported trusted definitions; it does not prove that an older loaded session has
adopted them. The targeted reload completed this installation's native execution check;
`window-reload-receipt.json` and `native-execution-receipt.json` preserve its evidence.

## Errata administrative cutover (2026-09-06)

The maintenance source patch is installed from isolated branch
`codex/maintenance-errata-20260906`, revision `31c0e2ded4c81d75d895994c54a4826449e49687`,
on the original base `7384809b00760f984120f8c8a59d16f6e84768df`. Installation copied only
the eleven reviewed Stage 8 source/test files after checking their original hashes,
lock membership and absence of a production scheduler/engine consumer. The main checkout
retains its unrelated migration and research edits. No scientific process was restarted.

The combined checkout passes 161 pytest tests; its maintenance wrapper runs 27 adversarial
cases in a separate interpreter and temporary roots. The installed Stage 8 standalone guard
passes 22/22. All 21 locks and both documentation linters pass. Exact maintenance command:

```powershell
./.venv/Scripts/python.exe -B -m pytest -q -o addopts= -p no:cacheprovider tests/test_stage8_maintenance.py
```

The read-only snapshot is `.agent-state/errata-evidence/`; its 246 files match the original
evidence. `.agent-state/errata-derived/COVERAGE.json` is the dated administrative correction,
with validator/source/input hashes and explicit superseded manifest declarations. It does
not replace `results/phase_2_4_stage_8/CURATOR_PACKET_FINAL.md` or complete scientific
write-through. `source-receipt.json` beside it records old/new source hashes, installation
boundary and revision. `source-before/` preserves pre-installation source bytes.

S4/S5 interpretation and repair lineage, D1-D5 owner corrections and the final scientific
write-through are complete in OPS-ERRATA-2 and L371/L372. The root errata is retired to
archive/maintenance/; matched-information scientific reruns and curator processing remain open. The complete imported server/library closure remains a provenance limit;
new copied-capsule receipts must not be described as solving that broader problem.

For maintenance rollback, compare installed bytes with `source-receipt.json` before restoring
only the recorded source files from `source-before/`; remove a newly added file only if its
current hash still matches this installation. Preserve all evidence, receipts and newer edits.
Label derived corrections superseded rather than deleting them. This source rollback does
not require rolling back the Codex runtime.

## Rollback

Cancel the watcher first. `python tools/codex_setup.py rollback` restores the exact
external configuration bytes recorded in `.agent-state/install-receipt.json` and removes
only files this installation created. It refuses to overwrite later edits. The receipt
and private backups remain available. Research processes, adapters, and results are
never rollback targets.
Native project and exact-hook trust records are retained in user configuration; once
the installed definitions are removed, those records cannot execute these hooks.

Repository originals are in `.agent-state/baseline/` and the retired canonical contract
is also in `docs/archive/agent-runtime/`. Restore only reviewed migration files if a
repository rollback is needed. Never reset the whole working tree: the experiment wrote
results and deleted transient capsules while the migration was in progress.

Official runtime contracts were checked against
[Codex hooks](https://learn.chatgpt.com/docs/hooks) and the installed CLI's generated
protocol. Local acceptance evidence takes precedence over assuming feature parity.

## Completed repair workload and release check (2026-09-06)

The curator explicitly authorized necessary repair runs and gear two. Three finite jobs
ran under `run_second_gear.sh 0 2` and the queue drained at 08:17:15 PDT: actual readout
dependency/amendment inventory, deterministic all-option fixtures, and a local fixed-input
model precision check. No downloads, training or paid calls occurred. Results and source
hashes are in `results/maintenance_20260906/`; none rewrites closed-stage measurements.
The queue's initial transient status-write failure recovered on the next pass. After drain,
`runners/queue_status.py` installed atomic unique-temp replacement with bounded sharing-error
retries and tests preserving the last readable record. The orphan sweep now matches a
resolved repository path boundary and rechecks process creation time before any tree action.

After changing queue source, explicitly run `python tools/codex_watch.py register-queue`:
the watcher correctly pauses a stale inventory. Registration after review restores scanning;
it does not run a job. No pending eligible job remains after this repair workload. Seven
original final produces and three maintenance produces may be acknowledged only after the
completed owner write-through and final-packet delivery; use the current watcher status.
The runtime permission adoption check remains separate from this completed workload.

Release verification: **167 pytest tests**, Stage 7 **30/30**, Stage 8 **22/22**, all **21 locks**, and both documentation linters pass. All 246 preserved snapshot files still match their original stage bytes. The seven original final events and three maintenance events were acknowledged only after full write-through and corrected-packet delivery; the watcher reports no pending events, error or notification failure.

## Hidden delivery child, 2026-09-07

The watcher delivery subprocess now sets the Windows no-console creation flag.
Ten existing delivery/recovery checks pass, and a live sole-watcher restart verifies
the new source hash and heartbeat with the scientific queue unchanged. The current
machine's PowerShell execution policy refused the scripted restart. Recovery waited
for the cancelled watcher's kernel lock to release and launched the same existing
Python entrypoint directly with `Start-Process -WindowStyle Hidden`; no execution
policy was changed. The inherited capsule launcher is a separate outstanding flash
candidate and remains unchanged while the scientific source closure is frozen.
Receipt: `results/phase_2_4_stage_9/pilot/HIDDEN_WATCH_RESTART_20260907.json`.

The Stage 9 capsule launcher now also uses the hidden-process flag; the installed
stack passes 324 tests and 21 locks. The first quiet watcher restart was live but
later delivery failed. A reviewed normal-user restart of the identical entrypoint
restored acceptance of an actual human-pipeline completion notification, with the
same owner, source and live research queues preserved. The sandboxed CLI version
check emitted a home-directory warning; the normal-user check did not. Retain this
distinction between a live watcher and working transport. No execution or security
policy changed. Receipt: `results/phase_2_4_stage_9/pilot/WATCH_RESTORATION_20260907.json`.

The restored watcher subsequently delivered an actual operational completion message
to this owner after its final response. The historical branch produce and prior full
landing were reconciled before acknowledgement; no job was restarted. This verifies
post-restoration idle-owner delivery, without claiming prompt delivery of every event
or physical absence of visible flashes. Receipt:
`results/phase_2_4_stage_9/pilot/OWNER_IDLE_DELIVERY_OBSERVED_20260907.json`.


## Extension replacement during Stage 9 recovery, 2026-09-10

The existing watcher remained alive after its configured extension-version executable was removed by an update. Delivery failed with FileNotFoundError. The ignored local executable path was refreshed to the installed Codex CLI 0.153.4 after checking its version and queue help. The same watcher reloaded the configuration and queued the actual launch receipt successfully; no restart, source edit, policy change or scientific-worker interruption was needed. The actual launch wake subsequently reached the operating conversation after its final response. Its unchanged bytes and prior landing were reconciled before re-acknowledgement on September 10 at 15:14 UTC inspection. This proves observed post-repair conversation delivery; no native delivery-hook row was recorded for this already-acknowledged event, so native hook evidence is not inferred. Private repair/transport evidence is under `.agent-state/recovery-wake-launcher/`. When this error recurs, check that the configured binary still exists before retrying or restarting services.
