# docs/ — working material, filed by topic

**The claims live in [`theory/`](theory/), organised by what we believe; the methods live in
[`../FINDINGS.md`](../FINDINGS.md), organised by when we ran them.** A result exists in both or
it is lost. Everything else here is material to hand an agent when it needs a particular kind of
context.

| folder / file | what is in it | when to reach for it |
|---|---|---|
| [`theory/`](theory/) | **the hypothesis store**: five files, one question each (inference targets / architecture / decision traces / reader heuristics / alignment), format spec in its README | after a context loss, when a result needs a home, before any edit inside it |
| [`TOOLS.md`](TOOLS.md) | installed libraries AND the built-here instrument ledger with validation states | before building an instrument, or when one misbehaves |
| [`method/`](method/) | **LESSONS (read before designing or building anything)**, CONTROLS, LITERATURE, DEVIATIONS, NEURAL_ANALOGUES; its README maps each file to its reach-for moment | designing a test, building a runner, doubting a control, claiming novelty |
| [`gates/`](gates/) | gate 0–3 material, curation batches, calibration | archaeology on an old gate |
| [`sim/`](sim/) | traffic with the Ghost Scale Simulation, both directions, newest first | anything about mechanism |
| [`design/`](design/) | SUCCESSOR, QUEUE, ENGINEERING_LOOP, DWELL_CORPUS; its README states the split from method (method binds every test, design briefs one build) and maps each file to its build | deciding what to build |
| [`archive/`](archive/) | superseded, nothing deleted | rarely |
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
