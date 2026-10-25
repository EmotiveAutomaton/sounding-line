---
name: grind
description: THE GRIND NEVER STOPS — the standing loop for processing this project's queue, results, and reports. Invoke whenever landing results, checking the queue, writing findings through, or when the curator says "run the grind", "queue duties", "process the results", or "continue the grind". Loads the full step list so no step is skipped late in a session.
---

# The grind never stops

Run every step, in order, every time. A result that has not been through all of them has not
landed. Late sessions skip steps; this list exists so they don't.

## 0. Read the specs that bind this loop

- Re-read `docs/theory/README.md` (the format block) BEFORE any theory edit this pass.
- If the pass will touch FINDINGS, re-read its "How this file works" header.
- Check `AGENTS.md`'s top lines for standing constraints (freezes, temporary rules).

## 1. Harvest his words FIRST, before anything mechanical

- Re-read what he said this turn. Musings on things he read in the markdowns are candidate
  hypotheses, not chatter — he should never have to say "now design an experiment for that".
- For each candidate: think about what he might be suggesting; judge whether it is novel
  research; do any research inline unless he explicitly requests agents for this task.
- Then design a test that would prove, disprove, or provide evidence either way, and file it in
  `TODO.md` under an identifier, in the right phase. The studies' responses come back through
  this same loop.
- **Before the design is filed, read the matching sections of `docs/method/LESSONS.md`** (and
  `CONTROLS.md` if a control is involved). The lessons file exists so mistakes are made once;
  a design that repeats a receipted mistake is a defect even if it would have worked.
- If nothing was suggested, say so in the report ("no tests harvested this pass") so the step
  is visibly run, not silently skipped.

## Stage-specific precedence

Read the currently ratified brief before acting. Its ceiling, closure freeze, reporting mode,
and spending limits override older general defaults. Stage 8 landings write through internally;
one final curator packet is reported. A wake never authorizes a new gear, cloud spending,
research design, or interpreting per-artifact output from an unfinished cell.

## Six-hour health cadence (curator instruction, 2026-10-10)

The watcher now carries an explicitly authorized recurring six-hour queue-health
inspection alongside immediate transition alerts. This supersedes the prior
transition-only prohibition at that cadence and the older ETA scheduling defaults
below. Do not add separate ETA wakes. On a health event inspect native identities,
progress and output freshness, failures, locks, resource limits, eligible authorized
work and watcher delivery health. Document findings and perform authorized recovery
before ACK; its ACK automatically rearms six hours later. Ordinary activity and
unrelated ACKs do not postpone it. Preserve gear and study scope; intentional GPU
parking remains healthy when required by the active allocation. No new research is granted.

## 2. Queue state

- Read the active stage scheduler status and `results/queue_main.log`; confirm the loop
  process is alive (two-line lock, Windows PID), with process creation time checked.
- Run `python tools/codex_watch.py status`. A detached process alone cannot wake Codex.
  Keep final produces registered, delivery failures visible, and one owner session.
  After completing a landing, acknowledge its event with `codex_watch.py ack EVENT_ID`.
  The agent executes the scientific write-through; the watcher only delivers paths.
- **First gear and second gear are distinct settings** (renamed from day/night 2026-08-12).
  First gear (`run_first_gear.sh`, serial, part of the CPU, the GPU mostly his because games
  need it) is the DEFAULT whenever he is talking at all regularly, and the mode for when he
  wants the machine. Second gear (`run_second_gear.sh`, sharded, as much CPU and GPU as the
  work can take) only when he explicitly calls for it, **loaded with about a day's worth of
  analyses ahead of time, and with no time window: it runs until the queue is empty (his
  standing ruling, 2026-08-28)**. Never shift to second gear on inference; he calls the gear.
- If nothing is running and the queue has stages, find out why before anything else.

### Schedule the next useful check-in

- Before yielding with authorized work running, estimate the next point that needs an
  agent from live progress or existing rates. Wake conservatively early, usually about
  twenty percent before it; healthy long GPU work normally needs thirty-to-sixty-minute
  checks, not repeated few-minute turns. Shorter checks need an imminent intervention.
- Run `python tools/codex_watch.py schedule SECONDS --expected-seconds ESTIMATE --reason REASON`.
  Record and verify its due time, milestone and basis; report the next check-in. Re-estimate
  after inspection. Do not create a new forecast project just to set a wake.
- Routine completion notices accumulate until the check-in. Fully land every delivered
  result before ACK; notification batching never licenses partial write-through or interim
  scientific scores. Failures, pauses, interrupts and registered active-queue completion
  bypass the delay. Keep those terminal paths registered.
- Suppress redundant routine wakes while already active. Without a recorded estimate the
  watcher uses a thirty-minute routine cooldown; fixed liveness fallback follows recent
  owner attention. Waiting belongs to the service, not an occupied agent turn.

## 3. Gather landings

- Every results file newer than its last write-through is a landing. Check the stage list's
  produces paths, not just the log tail.
- A result that appeared in ANY form (log line, committed file, notification) gets its FULL
  write-through in the same pass. "Entry next pass" is the named leak.

## 4. Write each landing through, in this order

1. `FINDINGS.md`: full entry — hypothesis in plain language, METHOD sentence, captioned table,
   verdict, means. Add any quoted p-value to `runners/audit_multiplicity.py` and re-run it.
2. `docs/theory/`: the row in the table the result bears on, AND the afterword under that table
   revisited in the same edit. Instrument results go to `docs/TOOLS.md` (the instrument ledger
   section) instead.
3. `TODO.md`: close the row, file what the result opened, under the same identifier.
4. The chat report: hypothesis → method → found → means. Short forms in chat, full in FINDINGS.
   Caption every table. No variable names in prose. Never soften a null.
5. The curator roll-up, appended to the FINDINGS entry (never duplicated elsewhere): theory
   group · plain-language question · outcome class, exactly one of Strengthens | Narrows |
   Kills | Infrastructure · one-sentence result (≤1 number) · project meaning · next
   engineering obligation · public claim status · curator decision required (No, or Yes with
   one recommended answer) · detail pointer. Full spec: `docs/design/archive/PHASE_2_0_CONTEXT.md` §15.

## 5. Instruments and infrastructure

- A new or repaired tool gets its row in `docs/TOOLS.md` with its validation state.
- Any criterion that fired (or could not fire) gets recorded — that class is the project's
  recurring death.

## 6. Refill

- Keep the queue loaded to the gear: second gear carries about a day's worth of analyses ahead
  of time and runs until the queue is empty (no window), first gear four to eight hours of
  light stages. Produces-guarded stages only; underestimate runtimes by 2-3×.
- Phase order comes from the plan at the head of `TODO.md`; recreations pass only on exact
  published values.
- **Before building or extending any runner, re-read `docs/method/LESSONS.md` §3 to §5**
  (statistic, model arm, infra). New lessons land there in the same pass that earns them.
- **Every new prereg card or gate-bearing runner carries a DESIGN CHECK block in its header**
  (his ruling 2026-08-18, enforced by the design_lint hook): the LESSONS sections read for
  THIS design, and for every gate its expectation under the NULL, its expectation under the
  ALTERNATIVE, and the failure direction it guards; bands exhaustive. The two receipted
  deaths of this class: L73's silent band, L132's direction-blind shuffle gate.

## 7. Close

- Locks verified + `git status` deletion lines read before any commit (and NO git at all while
  a freeze line stands in `AGENTS.md`).
- The report leads with queue state and ends with what runs next.

## Standing amendments, 25 October

Ratified by the October 25 Week 3 packet and current handoff. These amendments
supersede the older retry/refill defaults; scientific write-through and final-packet
reporting remain mandatory. Source: `docs/design/stage-15/week3/PACKET.md`, section 0.3.

**A. Never idle.**
- Keep at least two ready cards per CPU slot.
- When the ready queue drops below that, building the next cards comes before routine events. Failures and triggers are acknowledged first.
- Sources, in order: this packet's tree, the follow-ups under C, section 6's backlog.
- Report idle slot-hours in every digest. Any idle hour while commissioned work remains is a defect, recorded in OPS_LOG with its cause.

**B. Healing passes run automatically.** This amends the 17 October packet's row 9 and errata rule 2's "exactly one retry" for engineering failures.
- **What heals.** An engineering failure: a crash, a code bug, a dependency or join error, a failed known-answer check (an instrument failure, not a result), or non-convergence that a repair leaving the estimand unchanged can fix (starting values, optimiser settings, iterations). A repair that changes the model is a `.h1` card (step 3).
- **What doesn't:**
  - an environmental interruption, as rule 2 defines it (a memory or temperature guard, an operating-system refusal, sleep, power loss or reboot, disk exhaustion): resume from validated checkpoints as rule 2 says, as often as the cause recurs. It uses up no healing attempt;
  - a data defect: S3's canonical successor;
  - a cost overrun: S4 first. If a cheaper exact implementation is then needed, register it under step 3;
  - a scientific gate that fails (a null, a negative, a pass rule not met): that is a result. Record it and route it under C; never heal it.
- **Steps:**
  1. Diagnose the cause. Record one line in OPS_LOG with its class: engineering or instrument.
  2. Repair and rerun, with inputs, comparators, seeds and contrast unchanged. Up to two healing attempts per card. Shared passes keep row 10's count: at most 2 attempts in all.
  3. If the repair has to change the design (a new estimator, a reduced grid, a cheaper exact implementation), register it as a new card with the suffix `.h1`, frozen before it runs, and dispatch it at the parent's rank.
  4. After two failed healing attempts, record the card as invalid with its reason, and dispatch the next.

**C. Follow-ups run automatically.** After each landing, register follow-ups from this menu, frozen before their outcomes, without waiting to be asked:

| Parent's state | Follow-ups registered at once (at most three) |
|---|---|
| Positive or marginal | (a) specification curve `.s`; (d) a mechanism probe `.m`, the smallest test that would say why; then (c) a second dataset `.r` where one is already in hand, otherwise (b) a second pipeline `.p` |
| Null | (e) an instrument check `.ic`: could this pipeline have seen the effect at the size that matters (a planted calibration, or a power curve over effect size)? Until (e) lands, the null is reported as "not detected; sensitivity untested", never as a negative |
| Unsupported (too few events to test) | None. Recorded apart from nulls, with the support count |
| Negative | (a), plus the reversal's mechanism probe `.m` |
| Invalid | B's healing passes |
| Anything the owner finds surprising | One exploratory card `.x`, labelled exploratory, registered only while the parent has fewer than three follow-ups |

- **Caps.**
  - Each follow-up is capped at half its parent's ceiling.
  - At most three follow-ups per parent per week, the exploratory card included.
  - **One generation only.** A follow-up registers no follow-ups of its own; its result goes to the digest.
  - **No locked holdout is spent automatically.** `.r` never reads a Tier 4 holdout (Padmakumar & He's logs, FX1's folds).
  - Follow-ups rank below this packet's cards, except that an instrument check `.ic` jumps ahead of any card that depends on the same instrument.
- **Suffixes.** `.s`, `.p` and `.r` keep their 17 October meanings. `.m`, `.ic` and `.x` are new. `.c` keeps its 17 October meaning (planted calibration in V4's worlds) and isn't used by this menu.
- **Rationale.** Each follow-up carries one line on why, written by the owner. The curator may veto at the digest; nothing waits for him.

**D. A claim ledger.** The workflow fix for corrections.
- **Start a Stage 15 claim ledger modelled on Stage 4's and 5's:** `results/phase_2_4_stage_15/CLAIM_LEDGER.json`, rendered as `CLAIMS.md`. Each row keeps their fields (`card`, `estimand`, `outcome`, `strongest_rival`, `scope`, `pursuit`, `warrant`, `public_wording`, `detail`, `at`) and adds:
  - **id:** the FINDINGS id where one exists (for example `S15-EV1-PAUSES-V1`), otherwise `S15-<card>-<n>`, so companion repositories can cite rows;
  - **estimate,** with its interval;
  - **control status:** passes, biased reference, invalid, untested;
  - **scope qualifiers:** corpus, population, real or constructed, descriptive or confirmatory;
  - **source file and line;**
  - **supersedes / superseded by;**
  - **correction class** when changed: arithmetic, data, instrument, control, scope, attribution, citation or wording.
- **Allowed verbs are fixed by status:**
  - passing controls → "supports";
  - biased or invalid controls → "descriptive only";
  - constructed → "in constructed worlds";
  - a null with untested sensitivity → "not detected";
  - too few events → "unsupported".
- **Anything sent to the curator** quotes claims by ledger id with their public wording. That covers digests, talk pages and returns to companion repositories. A paraphrase must cite the id.
- **Corrections come first in every digest,** with their class. A superseded row stays, marked.
- **Backfill** the ledger at handoff for every claim in the 17 October packet's section 1, the 18 October week packet's section 0 state bullets and this packet's section 1, and for EV1 to EV4, PMAP, GEN1, DR1, NP1, D24 and D30.
