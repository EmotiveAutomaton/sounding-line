# Evidence navigation contract

The curator approved the [revised record-keeping plan](../design/program/RECORD_KEEPING_REVIEW_20261111.md)
on November 11, 2026: “go ahead to implement that revised version beginning with
the generated views over the preserved evidence. I agree with your recommendations.”
This is an additive transition. The legacy ledger, FINDINGS, immutable receipts,
theory files and existing stage filing requirements remain authoritative.

## Sources and generated views

- `MIGRATION_INVENTORY.json` is the frozen initial inventory: stable evidence IDs,
  bindings, detail locations, source hashes and identified writer entry points.
  Its old hashes describe the initial snapshot, not today's mutable source state.
- `ANNOTATIONS.json` is a versioned, reviewed overlay keyed by original evidence ID.
  Every reviewed entry pins substantive row content and its reviewed documents.
  The generator never overwrites the ledger's outcome, scope or estimates.
- `CLAIM_REGISTER.json` keeps individual claim identities, family groups, explicit
  standing and many-to-many evidence relationships. A run can bear differently on
  two claims. Review dates and standing-change dates are separate; unknown dates
  stay null. This pilot transcribes existing scoped interpretations, not new theory.
- `CONFIG.json` specifies quotation sources and five bounded query acceptance sets.
- `RECORDS.json`, `SCIENCE.md`, `OPERATIONS.md`, `UNCLASSIFIED.md`, `TEXTURES.md`,
  `texture/*.md`, `QUOTES.json`, `QUOTES.md`, `QUERIES.md`, `MANIFEST.json`, the root
  `SCOREBOARD.md` and `../START_HERE_FOR_AGENTS.md` are generated. Do not hand edit.

Run `.venv/Scripts/python.exe -X utf8 -B tools/record_views.py build`, then the
same command with `check`. Generation uses only local saved evidence; it does not
run scientific analyses, access raw participant records, dispatch jobs or change
wakes. It verifies the complete legacy source bindings and reviewed document pins,
rejects duplicate and dangling IDs, and fails if sources change during generation.
The manifest is written last; `check` refuses partial, missing or stale generations.
Readers must check freshness. A fresh timestamp alone is not validation.

## Classification and validity

`record_kind` (run, texture, claim, unknown) differs from `purpose` (primary,
probe, calibration, texture, operations, engineering_repair, unknown). An
infrastructure outcome is not enough to determine either scientific purpose or
population. Only the exact legacy operational-record shape automatically sets
kind=run, with its rule and source recorded; its other fields remain unreviewed.
Three exact, unambiguous human-substrate labels may populate people, with their
literal source and rule recorded. Other substrate text is not keyword-classified.

Population admits people, models, constructed, mixed, not_applicable and unknown.
Readout remains separate, and the original detailed scope is always retained.
Mixed-source calibration is not converted into either pure human or pure synthetic
evidence. Unknown is not false, uninformative, unsupported or a scientific null.
`by_construction` is true, false or unreviewed; a reviewed judgment requires a
reason. Synthetic data alone do not establish a construction guarantee.

Evidence validity is valid, limited, invalid or unknown. Link bearing is supports,
narrows, against, uninformative, context or unknown, scoped and explained per claim.
Controls and scientific outcomes keep their original labels. A failed calibration
can be valid evidence that an instrument is unqualified; it does not become human
evidence against the mechanism. Independent replay is not independent replication.

The scoreboard displays only reviewed standing. It never votes over counts,
promotes a claim after an operations entry or picks the newest result as truth.
An invalid or unknown basis immediately adds a warning against positive licensing.
A changed reviewed source blocks generation until re-review. Correct evidence
validity promptly; theoretical interpretation still follows the curator pass.

## Quotes and theory authority

QUOTES extracts currently filed blockquotes outside code fences, preserving exact
Markdown bytes and line/digest references. All attribution, dates, tags and
supersession are unreviewed until checked against context and filing receipts.
It is an inventory, not a declaration that each block is a current curator quote.
Original transcript verification is false unless separately established. Repairs
remain documented at their original sources. Removed quotes are not resurrected;
prior inventory revisions and source history remain in Git.

CURRENT is deferred because the supplied proposal names no exact, versioned,
curator-approved theory-thread state input. Existing theory files remain active.
Do not fabricate CURRENT from a guessed latest file or retire those theory files.
The [review queue](REVIEW_QUEUE.md) defines one bounded annotation pass using the
identified local theory revision, without a new timer, agent or experiment.

## Writers, transition and rollback

Every landing retains its full existing write-through and ACK policy. After the
last ledger, source or receipt update, run `build` and `check`. Private landing
helpers are inventoried but are not experiment inputs; their owner must include
the final refresh in the landing procedure. Existing producers and pinned live
runtimes are untouched. No watcher hook or background scan regenerates evidence.
The current Week 5 record helper marks navigation pending before filing; its
`finalize_views()` runs build/check at the final boundary. The same CLI commands
are available for older writers. A pending landing makes freshness checks and
queries refuse until the owner finishes filing. All older readers/writers still
need migration before any physical relocation.

Physical relocation is deferred. Before moving anything, migrate every writer and
reader with an explicit source map, compatibility anchors and a tested rollback.
Never move the archive first and allow an old helper to recreate it.
For this additive phase rollback consists of removing the navigation pointers and
stopping regeneration. Retain the overlay/register history; all original evidence
stays where it was. Do not reset unrelated work or change running jobs.

The query pilot is intentionally bounded. The unclassified view is part of every
search result's limitation, not a hidden backlog. Expand reviewed mappings only
after reading their original sources and recording the exact review basis.
