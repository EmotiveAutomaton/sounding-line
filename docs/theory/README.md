# Theory: the hypothesis store

Every claim this project makes, with what we checked and what came back. **`FINDINGS.md` was the
claims index and is now the method archive.** It holds how each test was run, looked up when a row
here needs its detail.

**Complete the initial read of this whole folder, newest first, before research or scientific
interpretation.** Under the curator-approved continuity rule in `../../AGENTS.md` (2026-09-06),
this read may span context windows. Record source hashes and the last fully read portion;
after compaction resume the first unread portion and re-read changed sources. Reload this
index and the current operating records after compaction. Before research, literature
comparison or theory edits, re-read the relevant sections, afterwords, correction history
and this README. Hashes, summaries and truncated output do not establish that text was read.

---

## Format: every section, every file

    TOP OF FILE   a blockquote stating the theory in his words, then two or three lines of what
                  it claims. A visitor should get the shape from the first screen
    EACH SECTION  1. the date it was said
                  2. HIS WORDS, as a blockquote
                  3. WHAT IT SAYS -- mine, short
                  4. HYPOTHESES, with status and evidence

**Sections run in decreasing load-bearing order.** The core claim first, then whatever explains the
theory most naturally. Not the order things were written in.

**Tests go in `TODO.md`, not here.** This folder holds *results*. The exception is a test that cannot
be run yet, which stays as an OPEN row with the blocker named.

**Blockquotes are the curator's words only.** Not superseded claims, not literature, not emphasis.
Superseded material takes a bold **Superseded** prefix and stays in the section it belongs to.
**Corrections are folded in, never appended.** Two rulings from the 2026-08-10 quote pass: the
curator may supply direct edits to his own quote blocks without restating them, and when he
directs outright removal of a quote, remove it; the git history is the record then.

**Spoken-source quotations (curator instruction, 2026-09-07).** Retain small excerpts
only when they contribute to the theory. Repair clear transcription errors to recover
the words the curator probably spoke; preserve his uncertainty, repetitions, unusual
phrasing, and tiredness rather than polishing his thought. Never turn a stronger analyst
reconstruction into a curator quotation. Mark substantive lexical repairs individually
and retain their source wording in the handoff. If the intended words remain uncertain,
use an explicitly labelled analyst paraphrase outside the quote block or leave the
passage out. Separate noncontiguous excerpts or mark an omission. Record the source
walkthrough and distinguish its date from the date the quotation is filed. Identify
retired or changed older quotes in the curator-facing errata.

**Status:** SUPPORTED · REJECTED · VOID (*could not answer its own question, which is not a negative
result*) · OPEN · CONTESTED (*the literature says the opposite; that difference is the contribution*) ·
INSTRUMENT DEAD (*our measure died, not the idea*).

**Source and scope must both be stated:**

    (test)  a measurement made in this project
    (sim)   a result from the parent simulation
    (lit)   published work; READ for the inspected source, SNIPPET otherwise

A result-bearing row also identifies its substrate: human artifact or process record,
model-generated text, or a constructed world. State whether the readout is a human,
a model, or an exact program wherever that changes the claim. A `(test)` tag does not
turn a constructed-world result into human evidence. Simulation can validate a method
under its assumptions; correspondence to a human mechanism is a separate question.
Evidence strength depends on the target, construction, controls, and replication rather
than on the source tag alone. Apply this clarification to changed rows now; retain
existing identifiers and provenance while bringing other rows into compliance during
their next substantive maintenance.

**A hypothesis with a history gets one indented timeline line.** Contradiction without a timeline is
not acceptable.

**A disconfirmed thing gets one line and no elaboration.** State what was checked and what came back,
and stop. **Nobody is going to ask a follow-up about a dead idea**, so auxiliary detail about it is
pure cost that buries the live claims around it. The reasoning that produced a *useful* measurement is
worth keeping even when its conclusion was wrong; the reasoning behind a claim that simply failed is
not.

**Under every hypothesis table, a short paragraph saying what those results add up to.** Not how many
were run. **A first pass at combining them into a claim**, weighing the relative strength of the
evidence, what follows logically, and what cannot all be true at once, so the section has a
conclusion and not just a ledger.

**Whenever a table changes in any way, the paragraph under it is revisited in the same edit.** A new
row can change what the set implies even when it changes nothing else. **A stale conclusion under a
fresh table is worse than no conclusion**, because it reads as current.

**The paragraph is read BEFORE the table, not after.** A reader lands on the conclusion first and
climbs up only if they want the detail, so it must stand alone. Plain words, the current state as
one interpretation, **no dated update-narrative** ("extended 08-09…" is a changelog, not a
conclusion; the folded-in rule applies to these paragraphs hardest of all), and identifiers only in
parentheses after the plain-language claim they tag, never as the subject of a sentence.

**Every paragraph ends with a fixed-vocabulary confidence line**, so validity is read at a glance
instead of re-derived per claim:

    Confidence: untested, logic only.
    Confidence: one bad test away.           a single run or family, or controls still outstanding
    Confidence: replicated and controlled.   multiple corpora or families, survived the audit;
                                             reversing it needs a NEW kind of fault, not a subtle one
    Confidence: instrument-dead.             the measure failed, so this says nothing either way

A mixed table joins two of these with a semicolon, each tied in plain words to the half it rates.

**Identifiers are stable. Never reused, never renumbered.**

**A result-bearing row cites its FINDINGS entry inline** — `(test, L53)` — so the row-to-entry
mapping stays greppable in both directions.

**The mechanical half of this spec is enforced in code.** `tools/theory_lint.py` runs after
every edit to this folder (a PostToolUse hook) and flags a missing afterword, a wrong Confidence
vocabulary, or a dash in prose for same-turn correction. The judgment-shaped rules above are not
mechanically checkable and still bind by being read — re-read this block before each batch of
edits here.

## Files

| | |
|---|---|
| **[THE_TRIPLE_INFERENCE.md](THE_TRIPLE_INFERENCE.md)** | **What is inferred?** The inference targets, their dependencies, value identifiability, and convergence. The core claim; everything else is downstream |
| **[THREE_COGNITIVE_LAYERS.md](THREE_COGNITIVE_LAYERS.md)** | **What human/model architecture might support the inference?** Carries the missing-middle prediction and the build gates |
| **[DECISION_TRACES.md](DECISION_TRACES.md)** | **What observable traces do the maker's decisions leave, and how are they measured?** Target × control × terminal topology. *(Renamed from `POLISH_AND_DEPTH.md` 2026-08-09)* |
| **[READER_HEURISTICS.md](READER_HEURISTICS.md)** | **How does a bounded reader find, combine, and calibrate those traces?** Priors, entry cues, traversal, updating, stopping, calibration, held as candidate feature-extracting amplifiers. *(Renamed from `HUMAN_HEURISTICS.md` 2026-08-09)* |
| **[ALIGNMENT.md](ALIGNMENT.md)** | **What objective should govern a system after it can read them?** The balanced sum of seeking and acting, the one claim that does not depend on the rest |
| **[essays/](essays/)** | the two personal essays, kept as the rawest form of the intent |

## Approved wording and source history

The October 18 twelve-position walkthrough is applied in the existing sections of
the three affected theory files. Its [supplied filing](../design/archive/SOUNDING_LINE_THEORY_FILING_2026-10-18.md)
and [application receipt](../design/archive/THEORY_FILING_20261018_APPLIED.json)
preserve quotation repairs, identifiers G203–G225 and source limitations. The
filing distinguishes communal fluency, acceptance lean, production stability,
shared expertise, habit and flow, model letdowns, separate choices, overlaying
corrections, fear/expertise aliases, play, sacrifice and the person entry.
Ghost N4d/N9/N8 are now imported with their constructed-world and discovery
limits; they do not establish human mechanisms. Completed local canonical
comparisons and control failures are integrated. Most linked full texts were
inaccessible or uninspected, so their vocabulary remains an attributed analyst
summary; READ marks inspected abstracts only. No exhaustive novelty search is
claimed. Earlier sources below retain their own dates and reading status.


The October 17 curator errata is applied across four theory files and this README. Its
[original text, quotations and repair ledger](../design/archive/SOUNDING_LINE_THEORY_ERRATA_2026-10-17.md)
and [application receipt](../design/archive/THEORY_ERRATA_20261017_APPLIED.json) preserve the exact
source, anchor checks, stable identifiers and before/after hashes. It files the curator's three
walkthroughs of that day. The triple inference is held as one joint inference with three entries,
function, person and process (G198); a value is a decision the maker still endorses (G199);
deliberate processing builds automatic routines, and one-shot aversive experience acts as broad
expertise (G200, G201); language models may lack the corrector, on his hedged reading (G202); goals
emerge, overlay and are topped by the last pass; attention allocates trust; aesthetics is one scale
of resolution speed on the curator's account; and pervasiveness locates a choice in its maker, with
automaticity a separate check. The curator asked that the files use the research literature's own
terms and teach them in place. His quotations keep System 1 and System 2, and the prose uses Type 1
and Type 2 processing, the current terms. Every position filed is OPEN. Ghost V23 results, N4b and
N4c included, are not imported by this errata and await curator uptake.

The October 16 curator errata is applied across the five theory files. Its
[original text, quotations and repair ledger](../design/archive/SOUNDING_LINE_THEORY_ERRATA_2026-10-16.md)
and [46-edit application receipt](../design/archive/THEORY_ERRATA_20261016_APPLIED.json)
preserve the exact source, anchor checks, stable identifiers and before/after
hashes. The vocabulary now separates needs (set points), deviations, inherited
drives and learned values. Learned ends, reader convergence, attention sources,
decision-level authorship and the aesthetic distinctions retain their stated
curator/analyst attribution and open empirical status. The newer saved-forecast
result in the reader dashboard is retained. Supplied literature reading labels
remain attributed handoff evidence, not a new review by the filing operator.
Ghost V22 and N4b outcomes are not imported by this errata. The source preserves
the superseded quote and its reading rule; G188 is withdrawn in favor of G191.

The October 14 curator errata is applied across the five theory files. Its
[original text and quotation-repair ledger](../design/archive/SOUNDING_LINE_THEORY_ERRATA_2026-10-14.md)
and [application receipt](../design/archive/THEORY_ERRATA_20261014_APPLIED.json)
preserve the source, exact edits, fresh identifiers and before/after hashes.
The supplied literature reading labels are retained as attributed handoff evidence;
this filing pass did not conduct a new literature review. Ghost V22 results remain
awaiting curator uptake. Earlier quotes remain in place under the new reading rules.

## Elsewhere

| | |
|---|---|
| [`../../FINDINGS.md`](../../FINDINGS.md) | the method archive |
| [`../method/`](../method/) | what a control licenses, the ledger, deviations, literature reviews |
| [`../sim/`](../sim/) | simulation traffic, both directions. Newest first |
| [`../archive/`](../archive/) | superseded. Nothing deleted, only moved |
| [the simulation's theory store](https://github.com/EmotiveAutomaton/ghost-scale-sim/blob/main/docs/theory/READING_INTENT.md) | **the most live representation of the author's theory (art, empathy, values, and AI) in an accurately tested, applied form.** Every claim of the ghost-scale model under its umbrella hypothesis, each row carrying a committed-verdict status; the surrounding [theory folder](https://github.com/EmotiveAutomaton/ghost-scale-sim/tree/main/docs/theory) holds the essays and the code-to-theory crosswalk. What this folder states as claims, that one runs as a model |

## His methodology record: 5 for 5

**Cited by `AGENTS.md` as a prior: when he pushes back on a method, assume he is right until shown
otherwise.**

| | claim | outcome |
|---|---|---|
| **D1** | censor dates, because a cue must *dominate*; symmetry is the wrong test | **right.** I argued and was wrong |
| **D2** | the rich-arm prompt leaks instruction-following | **right.** It said "name three things you decided NOT to cover" |
| **D3** | option D is not "years" | **right.** 2 to 3 days; `pymdp` was already installed next door |
| **D4** | the shuffle test is not correct | **right**, and worse than he guessed; it perturbs ~3× the signal |
| **D5** | near-significance means raise the power, not report a failure | **adopted as standing policy** |

## The maintenance rule

**A result goes in the hypothesis table of the section it bears on, in the same pass as
`FINDINGS.md`.** Findings is organised by *when we ran it*; this folder by *what we believe*. A result
recorded only in findings gets lost.

**Simulation results are harvested here too, marked `(sim)`**, with the constructed
substrate and reader identified. Judge their strength for the claim actually tested. A
controlled result may establish a property of its declared world; the corresponding human
claim remains a separate hypothesis unless independently tested. Preserve the source,
assumptions, and claim boundary when carrying either into the relevant section.
