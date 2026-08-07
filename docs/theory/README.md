# Theory — the hypothesis store

Every claim this project makes, with what we checked and what came back. **`FINDINGS.md` was the
claims index and is now the method archive** — how each test was run, looked up when a row here needs
its detail.

**After a compaction, re-read this whole folder.** The folder, not a named file; filenames go stale.

---

## Format — every section, every file

    1. HIS WORDS, as a blockquote
    2. WHAT IT SAYS -- mine, short
    3. HYPOTHESES, with status and evidence
    4. WHAT WOULD SETTLE THE OPEN ONES

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

**Identifiers are stable — never reused, never renumbered.**

## Files

| | |
|---|---|
| **[THE_TRIANGLE.md](THE_TRIANGLE.md)** | the core claim. Goal, process, drives — and what values are. Absorbs `VALUES.md` and the value-recovery half of `AGAINST_IMPOSSIBILITY.md` |
| **[THREE_LAYERS.md](THREE_LAYERS.md)** | the architecture. What a model reconstructs at each depth and where it fails. Absorbs `AFFECT_ARCHITECTURE.md` |
| **[POLISH_AND_DEPTH.md](POLISH_AND_DEPTH.md)** | two decision densities, split by what the decision targets. Absorbs `FLATTENED_INTENT.md` and `LEAKAGE.md` |
| **[HUMAN_HEURISTICS.md](HUMAN_HEURISTICS.md)** | how a person reads intent out of an artifact. He is the instrument; this describes it |
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
