# Record keeping for agent readers, 10 November 2026

*A recommendation from the theory thread for both research repositories. It is a brief for the registered workspace owner to apply. Claude doesn't edit the repositories. Nothing here deletes or renames an existing id, anchor or hash.*

## The problem in one paragraph

Results are recorded at the level of a run or a sub-check, and read at the level of a claim. So when one small record changes, the claim looks like it changed. In Sounding Line's Stage 15 ledger, 568 of 652 rows are infrastructure. Its findings file opens with operations entries, and its state file is 116,000 words. Ghost's V27 wrote 280 verdicts in two days. The curator no longer reads individual results. Agents do, and they need to find the few records that bear on a claim without reading the rest.

## Three kinds of record

| Kind | What it is | How many | Who reads it |
|---|---|---|---|
| **Claim** | A long-lived statement about people or about a method, with a standing and a history | tens | everyone, first |
| **Run** | One execution: a study, a control, a repair, a health check | thousands | only when a claim points to it |
| **Texture card** | A theory-facing note: what a variant suggests about a named line of the theory | hundreds | the theory thread |

Rules:
- A claim's standing changes only when a primary on people lands, or a constructed result replicates.
- A run never carries a verdict about a claim. It carries an estimate, its controls, and a pointer to the claim it bears on.
- A texture card never says "met" or "not met". It names the theory line it pokes and says what it suggests.
- A result that is fixed by construction is recorded as a scale report, not a verdict.

## Fields to add to every ledger row

The Stage 15 ledger already has `outcome`, `scope_qualifiers`, `supersedes` and `superseded_by`. Add:

- `claim_family`: the claim this row bears on, from a short fixed list.
- `bearing`: one of supports, narrows, against, uninformative.
- `population`: people, models, or constructed.
- `by_construction`: true or false.
- `theory_tags`: any of channel, set point, ladder, attention, reader, gate, kith, laughter.
- `record_kind`: claim, run, or texture.

A script can fill `population` and `record_kind` for old rows from fields that exist. The other four need one re-read pass (below).

## Files

- `SCOREBOARD.md`, generated from the ledger: one row per claim family, with its standing, the date it last changed, and links to the rows behind it. This is the file an agent reads first.
- `OPS_LOG.md`: operations entries move here. `FINDINGS.md` keeps science only, with a generated index at the top.
- `texture/`: one short file per card.
- `docs/START_HERE_FOR_AGENTS.md`, under 300 lines: reading order, where each kind of record lives, and five worked queries (for example, everything on people that bears on attention).

## Theory files

- `CURRENT.md`: today's tables only (channels, set points, ladder, open questions), regenerated from the theory thread's state file each round.
- `QUOTES.md`: every curator quote, verbatim, with its date, its tags, and a status of current or superseded. A superseded quote gets a dated pointer to what replaced it. No quote is deleted or reworded.
- The existing long files become the archive. Nothing in them is removed.

## The weekly re-read

Each week, one agent re-reads one old stage against `CURRENT.md` and writes a one-page card: what this result says about today's channels, set points and ladder, and what it can't say. The same pass fills `claim_family`, `bearing`, `by_construction` and `theory_tags` for that stage's rows. Twenty stages take twenty weeks at no extra compute.

## Texture lanes

A texture job starts from a line of `CURRENT.md` and ends with a card. Its packet states which line it pokes and what the next theory discussion would do differently for each way it could come out. If nothing would change, it isn't run.

## Order of work, cheapest first

1. Add `record_kind` and `population` by script.
2. Move operations entries to `OPS_LOG.md` and generate the findings index.
3. Generate `SCOREBOARD.md`.
4. Build `QUOTES.md` from the theory files.
5. Start the weekly re-read.
