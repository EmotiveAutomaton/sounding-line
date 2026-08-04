# The explored-paths problem, and a check that fixes it

**The curator's criticism, 2026-08-04:** *"You tend to fall into paths that people have explored
already."* Correct, repeatedly, and it needs a mechanism rather than an intention.

---

## §1. Why it happens, precisely

I reach for validated techniques because they are validated. **A validated technique comes with a
validated ceiling**, and importing the technique imports the ceiling.

| what I reached for | age | its ceiling |
|---|---|---|
| function words / stylometry | 60 yrs | **author identification.** That is what it does. It has never reliably done state. |
| Burrows' Delta | 30 yrs | distance between authors |
| LIWC categories | 30 yrs | correlations with self-report, r ≈ 0.3 |
| concept-vector extraction | 5 yrs | concept presence |
| accuracy-against-chance | 100 yrs | that a difference exists |

Every one of those worked *as designed* and none could reach the question. The failure was not
execution. **It was choosing instruments whose known limit sits below the question.**

---

## §2. The check, run before adopting any technique

Three questions. All three must pass.

> **1 · What is this technique's ceiling, and is our question below it?**
> If the field has spent thirty years and got author identification, we will get author
> identification. Name the ceiling out loud before adopting.
>
> **2 · What do we have that the people who built this technique did not?**
> If the answer is nothing, we are reproducing their work and will reproduce their limit.
>
> **3 · Which of our assets does this use?**
> If it uses none, it is borrowed capability, not leverage.

---

## §3. What we actually have that nobody else does

This is the part worth keeping in view, because it is the answer to question 2 every time.

| asset | who else has it |
|---|---|
| **A worked theory of intent as compressed decision-making**, with an equation and a lineage | one person |
| **A simulation of the mechanism with ground truth**, four audit passes, 57 experiments | one project |
| **Model internals** — mechanistic interpretability is public now | anyone, but almost nobody has it *plus* a theory that says what to look for |
| **A curator who reads at high resolution and narrates it** | vanishingly rare; think-aloud protocols are expensive |
| **Four untested forward predictions the literature has never asked** | nobody, by definition |

**The last row is the one to mine.** From `ghost-scale-sim/EVIDENCE.md`, a retrospective literature
check that found four rows where *nobody has asked the question*:

- **E4** — the no-label baseline. The literature almost always supplies a label.
- **E30 · E31** — *"nobody appears to have separated method-uptake from purpose-uptake in an
  art-perception paradigm."*
- **E36** — *"the temporal ordering claim inside one exposure is not something the literature has
  tried to measure."* Called **the sharpest forward prediction** there.
- **E49** — artfulness as *density*: hierarchy per unit of observable extent. Compression measures
  are established; **the bimodality prediction is not tested anywhere.**

**Those four are the territory.** Any test that lands in one of them is automatically not a
well-explored path, because the check that went looking found nothing there.

---

## §4. The stockpile of entropy, and how to use it

The curator: *"we have a stockpile of entropy in the ghost scale sim repository — most notably the
theory documents, but also in the tests themselves."*

The way to use it is not to re-read it hoping for inspiration. It is to **ask the check's question
2 against it**: what does the simulation know that the field does not?

`EVIDENCE.md` answers that directly and I had forgotten it existed. It is a retrospective
literature check, one row per experiment, marking agreements, disagreements, and **absences**. The
absences are a map of unclaimed ground, already surveyed.

**Standing instruction to myself: when the next instrument is being chosen, open `EVIDENCE.md`
first and check whether the question is in an unclaimed row.** If it is, that is the one to build.
If it is not, run §2's three questions and expect to fail them.

---

## §5. Applied right now: what this rules in

Running §2 against what is queued:

| | ceiling | our asset | verdict |
|---|---|---|---|
| more function-word work | author ID — **below our question** | none we uniquely have | **stop** |
| activation reading (B′) | concept presence in a model | internals **+ a theory saying what to look for** | **continue** — question 3 passes strongly |
| the wall inside the reader | *no ceiling — unbuilt* | theory + internals + E37 | **continue** |
| refusal as a measure | *no ceiling — unbuilt* | the schema's failure modes are ours | **continue** |
| **multi-scale compression** | compression-aesthetics is established, **but E49's bimodality is unasked** | the theory says *density*, which specifies what to compress and at what scales | **build** — lands in an unclaimed row |

The last one is new and comes directly from this file's own procedure, which is the first evidence
that the procedure does anything.
