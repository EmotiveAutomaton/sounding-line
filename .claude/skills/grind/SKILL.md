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
- Check `CLAUDE.md`'s top lines for standing constraints (freezes, temporary rules).

## 1. Harvest his words FIRST, before anything mechanical

- Re-read what he said this turn. Musings on things he read in the markdowns are candidate
  hypotheses, not chatter — he should never have to say "now design an experiment for that".
- For each candidate: think about what he might be suggesting; judge whether it is novel
  research; decide whether a background research agent is worth sending out first (spawn only
  with his standing rules in mind).
- Then design a test that would prove, disprove, or provide evidence either way, and file it in
  `TODO.md` under an identifier, in the right phase. The studies' responses come back through
  this same loop.
- **Before the design is filed, read the matching sections of `docs/method/LESSONS.md`** (and
  `CONTROLS.md` if a control is involved). The lessons file exists so mistakes are made once;
  a design that repeats a receipted mistake is a defect even if it would have worked.
- If nothing was suggested, say so in the report ("no tests harvested this pass") so the step
  is visibly run, not silently skipped.

## 2. Queue state

- `tail results/queue_main.log`; confirm the loop process is alive (two-line lock, winpid).
- **First gear and second gear are distinct settings** (renamed from day/night 2026-08-12).
  First gear (`run_first_gear.sh`, serial, part of the CPU, the GPU mostly his because games
  need it) is the DEFAULT whenever he is talking at all regularly, and the mode for when he
  wants the machine. Second gear (`run_second_gear.sh`, sharded, as much CPU and GPU as the
  work can take) only when he explicitly calls for it, **loaded with about a day's worth of
  analyses ahead of time**. Never shift to second gear on inference; he calls the gear.
- If nothing is running and the queue has stages, find out why before anything else.

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
   one recommended answer) · detail pointer. Full spec: `docs/design/PHASE_2_0_CONTEXT.md` §15.

## 5. Instruments and infrastructure

- A new or repaired tool gets its row in `docs/TOOLS.md` with its validation state.
- Any criterion that fired (or could not fire) gets recorded — that class is the project's
  recurring death.

## 6. Refill

- Keep the queue loaded to the gear: second gear carries about a day's worth of analyses ahead
  of time, first gear four to eight hours of light stages. Produces-guarded stages only;
  underestimate runtimes by 2-3×.
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
  a freeze line stands in `CLAUDE.md`).
- The report leads with queue state and ends with what runs next.
