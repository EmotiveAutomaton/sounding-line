# docs/design — blueprints and build rationale, read when picking up the build

The split from `../method/`, since the two invite confusion: **method binds, design briefs.**
A method file is normative for every test, every day, trigger-indexed and read before designing
or building anything (its README maps the moments). A design file is the blueprint and rationale
for one thing we intend to build, dormant until that build is scheduled, and then it is the
brief. Merging them would put binding procedure and dormant blueprints in one index and dilute
the trigger discipline, which is why they stay two folders (the call made 2026-08-14, at the
curator's prompt).

| file | reach for it when |
|---|---|
| [`PHASE_2_0_CONTEXT.md`](PHASE_2_0_CONTEXT.md) | **the governing brief for Phase 2.0**, the curator's handoff (2026-08-16, snapshot 1d38130): mission, locked design decisions, sub-goals 2.0A to 2.0H, benchmark and evaluation contracts, claims policy, curator abstraction boundary. Read before any Phase 2.0 design or build decision; the live sub-goal map lives in `TODO.md`. Archived here from the repo top level per its own §17 routing |
| [`EVAL_CONTRACT_2_0.md`](EVAL_CONTRACT_2_0.md) | **G152, the Phase 2.0 evaluation contract, DRAFT pending the curator's freeze**: binary-label policy, regime taxonomy, metrics, split logic, baseline-selection rule, hard slices, claim language per outcome. Once frozen it joins the hash-lock discipline and no result can change it |
| [`BENCHMARK_2_0.md`](BENCHMARK_2_0.md) | **G153, the crossed provenance-decision benchmark blueprint**: cell structure, shortcut-breaking counterexamples, sources, dose decomposition, build order. Normative contracts stay in the brief §11 and the evaluation contract; this is the construction plan. Data acquisition blocked on the generator-budget and licensing rulings |
| [`DWELL_CORPUS.md`](DWELL_CORPUS.md) | sourcing or scoping the dwell corpus. Sim T-3 named the regime where decision-counting is a well-defined event; this is the first corpus request in the project with a reason attached rather than a vibe. Still a sourcing decision |
| [`ENGINEERING_LOOP.md`](ENGINEERING_LOOP.md) | choosing tooling or framing for the build side. The curator's engineering-loops reframe, in his words: this project is not only establishing claims, it is trying to make something. Quote discipline applies; his blockquote is untouchable |
| [`QUEUE.md`](QUEUE.md) | never for the live queue. The live queue is `TODO.md` plus `runners/run_queue.py`; this is the 2026-08-05 snapshot, superseded with a banner, kept whole for its measured rates and its ordering rationale |
| [`SUCCESSOR.md`](SUCCESSOR.md) | designing any successor to a gate instrument. Written before Gate 3's result was seen, deliberately: a successor designed after a number is a successor designed to explain that number. That discipline is the file's standing value |

Maintenance: a design file lands when a build is specified ahead of its schedule slot. It is
superseded in place with a banner, never deleted, when the build lands or the live document
moves elsewhere. Results never live here; they go to `FINDINGS.md` and the theory store.
