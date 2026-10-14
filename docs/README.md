# Documentation - current authority, methods and history

**Current commission:** the [October week](design/stage-14/README.md) uses Stage 14.
The admitted local adapter ladder and approved Modal main are complete; remaining
local and API lanes are held at admission gates. Supervision remains healthy.
See [current status](../CURRENT_STATUS.md) for both gears, costs and Friday's final
packet. The September closure statements below remain historical.

**Navigation:** [all stages 2-14](design/README.md) · [program context](design/program/README.md) · [Gear 3 rounds](design/gear-3/README.md) · [applied October 14 theory errata](design/archive/THEORY_ERRATA_20261014_APPLIED.json).

**Start with [current status](../CURRENT_STATUS.md), [study authority](design/README.md) and [workspace layout](WORKSPACE_LAYOUT.md).** The admitted original and healing Stage 13 queues are drained, with the [final packet assembled](../results/phase_2_4_stage_13/FINAL_PACKET_20260930.md) and all retained completions verified. Reader admission and unavailable comparisons remain explicit deficits; the [October 1 endpoint](../results/phase_2_4_stage_13/FINAL_ENDPOINT_20261001.json) is reconciled and the exited helper watch retired; Stage 12 remains stopped with its [final evidence packet assembled](../results/phase_2_4_stage_12/FINAL_PACKET_20260927.md) and its [final endpoint reconciled](../results/phase_2_4_stage_12/FINAL_ENDPOINT_20260928.json); scientific deficits remain.

**The claims live in [`theory/`](theory/), organised by what we believe; the methods live in
[`../FINDINGS.md`](../FINDINGS.md), organised by when we ran them.** A result exists in both or
it is lost. Everything else here is material to hand an agent when it needs a particular kind of
context.

| folder / file | what is in it | when to reach for it |
|---|---|---|
| [`theory/`](theory/) | **the hypothesis store**: five files, one question each (inference targets / architecture / decision traces / reader heuristics / alignment), format spec in its README | after a context loss, when a result needs a home, before any edit inside it |
| [`TOOLS.md`](TOOLS.md) | current tools, models, testing environments and readiness limits; historical instrument ledger | before choosing or building an instrument, checking capabilities, or diagnosing readiness |
| [`method/`](method/) | **LESSONS (read before designing or building anything)**, CONTROLS, LITERATURE, DEVIATIONS, NEURAL_ANALOGUES; its README maps each file to its reach-for moment | designing a test, building a runner, doubting a control, claiming novelty |
| [`gates/`](gates/) | gate 0–3 material, curation batches, calibration | archaeology on an old gate |
| [`sim/`](sim/) | traffic with the Ghost Scale Simulation, both directions, newest first | anything about mechanism |
| [`design/`](design/) | current October program and errata in Stage 14, closed September contracts, reusable blueprints and indexed history | deciding what to build |
| [`archive/`](archive/) | superseded, nothing deleted | rarely |
| [`GEAR3_MODAL_WORKSPACE_GUIDE.md`](GEAR3_MODAL_WORKSPACE_GUIDE.md) | Modal workspace selection, usage limits, payment readiness and existing resources | before the bounded cloud pilot |
| [Midweek API implementation](design/stage-14/MIDWEEK_IMPLEMENTATION.md) | Paid-reader access, profile prerequisite, accounting and remaining admission holds | when checking the current API lane |
| `STATE.md` | agent orientation: hard constraints, the research program, the queue's state | first thing after a compaction, with FINDINGS and the theory folder |

**The working loop is a skill.** `.agents/skills/grind/SKILL.md` (`$grind`) holds the full
results-processing loop, harvest-first; `tools/theory_lint.py` enforces the theory folder's
mechanical format rules through a PostToolUse hook. First gear (`run_first_gear.sh`, part of
the machine, the GPU mostly the curator's) is the default engine; second gear
(`run_second_gear.sh`, everything, loaded about a day deep) only on his explicit call. The
gears replaced day/night as the standard on 2026-08-12.

**Primary records of runs are not here.** They are `results/*/VERDICT.md` and the per-run JSONs,
alongside the data.

**Codex operations:** [`CODEX_OPERATIONS.md`](CODEX_OPERATIONS.md) maps hooks, private
notifications, queue wakeups, verification, and rollback. `../AGENTS.md` is canonical.
