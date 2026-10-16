# Workspace and documentation map

Start with [current status](../CURRENT_STATUS.md) for authority and the next action,
then the [stage index](design/README.md) for the right design folder. **Stage 15 is
current; Stages 14 and 13 are closed with final packets.**

## Repository map

| Need | Read here |
|---|---|
| Startup and operating constraints | [AGENTS](../AGENTS.md), [STATE](STATE.md), [TODO](../TODO.md), [operations](CODEX_OPERATIONS.md) |
| Any stage's plans, sources and evidence | [Design index](design/README.md): one visible folder per stage, 2 through 15 |
| Current campaign | [Stage 15](design/stage-15/README.md); finite queues drained, remaining validation and scientific admission gates explicit |
| Closed October campaign | [Stage 14](design/stage-14/README.md) |
| Closed September campaigns | [Stage 13](design/stage-13/README.md), [Stage 12](design/stage-12/README.md) |
| Cloud rounds across stages | [Gear 3 campaign index](design/gear-3/README.md) |
| Program-wide context | [Program shelf](design/program/README.md) |
| Claims and curator framing | [Theory](theory/README.md); October 14 errata applied |
| Methods and capabilities | [Method shelf](method/README.md), [TOOLS](TOOLS.md) |
| Complete method/results record | [FINDINGS](../FINDINGS.md), `results/` and immutable receipts |
| Original briefs and errata | [Design archive](design/archive/README.md), [supplied-source archive](archive/study-specs/README.md) |
| Retired operational summaries | [Operating archive](archive/operations/README.md) |

The top of each live entry point describes current authority; dated history below
it remains history. Prefer links to CURRENT_STATUS over duplicating volatile queue
counts and forecasts. Result closure, valid evidence and complete study scope are
different facts.

## Stable paths and filing

New briefs belong once in their stage folder, with source hash and status in its
README. Theory errata belong in the source archive with an application receipt;
current claims belong in theory. Keep supplied sources byte-identical.
Each stage folder stays visible after closure and links to its preserved archive.

Stage 12's linked originals, three older frozen design paths and the engineering
loop remain at established paths for bound consumers or preserved source links.
They are indexed exceptions, not pending filing. Keep the locked specification,
preregistrations, raw capsules, cards and result receipts in place. The
[October 14 relocation ledger](archive/operations/DOCUMENT_RELOCATIONS_20261014.json)
records document moves and mechanical link repairs; no scientific evidence was
retired by organizing the shelves.

## Workspace outside Git

| Location | Role |
|---|---|
| `sounding-line/` | Main repository and active operating checkout |
| `reference/` | Separate research checkouts; do not edit during ordinary work |
| `.worktrees/gear3-round1/` | Inactive historical worktree; branch and evidence retained |
| `.workspace/assessments/` | Private workspace assessment and incoming-source preservation |
| `.agents/`, `.codex/`, `.claude/` | Existing local instruction/runtime surfaces |

Raw text, local models and operational evidence remain in their existing ignored
paths. The independent health cadence is six hours; a documentation pass does not
reset it or authorize new work.
