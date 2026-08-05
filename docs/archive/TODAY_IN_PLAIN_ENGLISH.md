# What we did on 2026-08-04, in plain English

No codes. What was physically run, what came back, what it means.

---

## What actually happened, mechanically

| what | what it physically was |
|---|---|
| **Gate 3 finished** | A 9B model on the local GPU read 51 web pages, five times each, ~14 hours. |
| **We downloaded 34 books** | Austen, Dickens, Darwin, Twain — several works per author, from Project Gutenberg. 22 million characters. |
| **We had the model write 36 fake articles** | Three kinds, on the same topics, to serve as a "nobody made this" control. |
| **We loaded a small model raw** | 1.5B parameters, in PyTorch rather than through Ollama, to read its *internal activations* instead of its output. |
| **Everything else was statistics** | On text we already had. No new reading. |

---

## The tests, one line each

**Gate 3** — *does the instrument separate careful work from commercial filler?*
**Failed, and worse, it turned out it couldn't have succeeded.** The measure was a ratio of counts
whose denominator is usually near zero, so it has wild variance. The noise was nine times the
signal. The parent simulation independently showed the same statistic reports "17×" in a world
built so the true answer is zero.

**The books** — *does the way people use small words (the, of, but, I) carry anything?*
**Yes.** It identifies which author wrote a passage, and it even tells one author's different books
apart at 2× chance. But it turned out my statistic for this had been wrong for two days — it said
"no signal" on a task that is the most established result in the field. Fixed.

**The 36 fake articles** — *build a proper "nobody made this" control.*
Every previous control used **three** short artifacts written for a different purpose. Four separate
measures had been tested against those three. Now there are 36, length-matched.

**Density by compression** — *is a maker's work more "organised" than a machine's?*
**Ran twice, failed twice, for two different reasons.** First it was measuring word count. Then,
after length was controlled, it was measuring **vocabulary richness**. Both times it looked like a
real result first.

**The wall test** — *does a reading model behave differently when there's nobody behind the text?*
**Failed twice**, on two different models. The idea: a model reading about a person temporarily
"becomes" a bit like them, then returns to itself. So measure how far it moves. It didn't move
differently for human vs machine text.

**The refusal test** — *measure what the reader COULDN'T do instead of what it found.*
**Reported as uninformative**, because my pass condition would have passed by chance half the time.

**D-0b** — *do small words track a writer's emotional state, not just their identity?*
**Ambiguous.** 1.80× against a threshold of 2.0×. The effect is real (p = 0.005) and doesn't meet
the bar that was set in advance. The bar stands.

---

## The "rich arm", which is the thing worth keeping

The 36 fake articles come in three kinds:

| | what it is |
|---|---|
| **thin** | *"Write about mattresses."* Nothing specified. |
| **rich** | A long prompt: purpose, audience, "name three things you decided not to cover", "be direct about what you're uncertain about." |
| **averaged** | Generated, then rewritten twice to smooth it out. |

**All three are machine-written. That is the point.**

> A **machine detector** must call all three equally empty.
> An **intent detector** must rank `rich` above `thin`, because a person put more intent into it.

**This project has always claimed to be the second and has never had a way to check.** Now every
measure gets run against it, and a measure that treats `rich` and `thin` alike is disqualified
whatever else it does.

---

## Two controls that are now mandatory

**The shuffle test.** Randomise the word order and re-run. Vocabulary and length are preserved
exactly; all structure is destroyed. **A measure whose effect survives that is a vocabulary
statistic**, whatever it is called. This is what caught the density measure — and it caught it in
fifteen minutes instead of fourteen hours.

**The length correlation, computed before the verdict.** Not after.

---

## What actually survived today

**Function words carry real information.** They identify a website at 7.6× chance and tell one
author's books apart at 2×. Validated against tasks with known answers.

**`purpose_breadth` works** — the simulation proved it separates concentrated from diverse
motivation *at matched decision density*, which no real corpus could show.

**The affect directions inside a model are real** — 4× chance on held-out sentences, and **not
lexical**: bag-of-words on the same sentences scores exactly chance.

**And the apparatus for killing bad measures is now sharp.** Seven measures died today. The first
took fourteen hours to disqualify. The last took fifteen minutes.

---

## The honest summary

**No measure of intent survived today.** What survived is a control set that can tell an intent
measure from a machine detector, two mandatory confound checks, and a much faster way to find out
that something doesn't work.

That is a real day's progress and it is not the kind that feels like progress.
