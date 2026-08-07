# Theory — the hypothesis store

Every claim this project makes, with what we checked and what came back. **`FINDINGS.md` was the
claims index and is now the method archive** — how each test was run, looked up when a row here needs
its detail.

**After a compaction, re-read this whole folder.** The folder, not a named file; filenames go stale.

---

## Format — every section, every file

    TOP OF FILE   a blockquote stating the theory in his words, then two or three lines of what
                  it claims. A visitor should get the shape from the first screen
    EACH SECTION  1. the date it was said
                  2. HIS WORDS, as a blockquote
                  3. WHAT IT SAYS -- mine, short
                  4. HYPOTHESES, with status and evidence

**Sections run in decreasing load-bearing order** — the core claim first, then whatever explains the
theory most naturally. Not the order things were written in.

**Tests go in `TODO.md`, not here.** This folder holds *results*. The exception is a test that cannot
be run yet, which stays as an OPEN row with the blocker named.

**Blockquotes are the curator's words only** — not superseded claims, not literature, not emphasis.
Superseded material takes a bold **Superseded —** prefix and stays in the section it belongs to.
**Corrections are folded in, never appended.**

**Status:** SUPPORTED · REJECTED · VOID (*could not answer its own question — not a negative result*) ·
OPEN · CONTESTED (*the literature says the opposite; that difference is the contribution*) ·
INSTRUMENT DEAD (*our measure died, not the idea*).

**Source, because they are not equally strong:**

    (test)  real text, here. The strongest thing we have
    (sim)   the parent simulation. Weaker. Authoritative about a METHOD, suggestive about a MECHANISM
    (lit)   published work. READ if fetched and opened, SNIPPET if not

**A hypothesis with a history gets one indented timeline line.** Contradiction without a timeline is
not acceptable.

**A disconfirmed thing gets one line and no elaboration.** State what was checked and what came back,
and stop. **Nobody is going to ask a follow-up about a dead idea**, so auxiliary detail about it is
pure cost — it buries the live claims around it. The reasoning that produced a *useful* measurement is
worth keeping even when its conclusion was wrong; the reasoning behind a claim that simply failed is
not.

**Under every hypothesis table, a short paragraph saying what those results add up to.** Not how many
were run. **A first pass at combining them into a claim**, so the section has a conclusion and not
just a ledger.

**Identifiers are stable — never reused, never renumbered.**

## Files

| | |
|---|---|
| **[THE_TRIANGLE.md](THE_TRIANGLE.md)** | **the empathy triangle** — intent extraction as a triple inference over goal, process and drives. The core claim; everything else is downstream. Also holds what values are, and the disagreement with the impossibility literature |
| **[THREE_LAYERS.md](THREE_LAYERS.md)** | the affective architecture a model is trying to reconstruct, and where the reconstruction fails. **Carries the project's largest live worry: whether the structure is there at all** |
| **[POLISH_AND_DEPTH.md](POLISH_AND_DEPTH.md)** | two decision densities, split by what the decision targets. Absorbs `FLATTENED_INTENT.md` and `LEAKAGE.md` |
| **[HUMAN_HEURISTICS.md](HUMAN_HEURISTICS.md)** | the tricks a person uses when the maker is absent. **Candidate feature-extracting amplifiers**, not a method we expect to depend on |
| **[ALIGNMENT.md](ALIGNMENT.md)** | the terminal value as the balanced sum of seeking and acting. The one claim that does not depend on the rest |
| **[essays/](essays/)** | the two personal essays, kept as the rawest form of the intent |

## Elsewhere

| | |
|---|---|
| [`../../FINDINGS.md`](../../FINDINGS.md) | the method archive |
| [`../method/`](../method/) | what a control licenses, the ledger, deviations, literature reviews |
| [`../sim/`](../sim/) | simulation traffic, both directions. Newest first |
| [`../archive/`](../archive/) | superseded. Nothing deleted, only moved |

## His methodology record — 5 for 5

**Cited by `CLAUDE.md` as a prior: when he pushes back on a method, assume he is right until shown
otherwise.**

| | claim | outcome |
|---|---|---|
| **D1** | censor dates — a cue must *dominate*; symmetry is the wrong test | **right.** I argued and was wrong |
| **D2** | the rich-arm prompt leaks instruction-following | **right.** It said "name three things you decided NOT to cover" |
| **D3** | option D is not "years" | **right.** 2–3 days; `pymdp` was already installed next door |
| **D4** | the shuffle test is not correct | **right**, and worse than he guessed — it perturbs ~3× the signal |
| **D5** | near-significance means raise the power, not report a failure | **adopted as standing policy** |

## The maintenance rule

**A result goes in the hypothesis table of the section it bears on, in the same pass as
`FINDINGS.md`.** Findings is organised by *when we ran it*; this folder by *what we believe*. A result
recorded only in findings gets lost.

**Simulation results are harvested here too, marked `(sim)`** — hypotheses with weak evidence, not
findings. Slotting them in is how we stop treating a simulation artifact as a fact, which has already
happened once and cost two days.
