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

**Status:** SUPPORTED · REJECTED · VOID (*could not answer its own question, which is not a negative
result*) · OPEN · CONTESTED (*the literature says the opposite; that difference is the contribution*) ·
INSTRUMENT DEAD (*our measure died, not the idea*).

**Source, because they are not equally strong:**

    (test)  real text, here. The strongest thing we have
    (sim)   the parent simulation. Weaker. Authoritative about a METHOD, suggestive about a MECHANISM
    (lit)   published work. READ if fetched and opened, SNIPPET if not

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

**Simulation results are harvested here too, marked `(sim)`.** They enter as hypotheses with weak
evidence, not findings. Slotting them in is how we stop treating a simulation artifact as a fact,
which has already happened once and cost two days.
