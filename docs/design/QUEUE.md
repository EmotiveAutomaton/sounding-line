# The queue — what is left, in order, with what it costs

**2026-08-05, rewritten after the second simulation batch returned.** Rates are measured from real
runs, not guessed: **one probe loop ≈ 1.9 min · one generation ≈ 1.1 min · one activation read
≈ 0.3 s on GPU.**

Everything from the previous queue has either run or been cancelled. See §3.

---

## §1. Nothing is running

The GPU is idle. `run_queue_today.sh` reported `QUEUE DONE`.

---

## §2. Queued, in order

| # | test | what it does | ETA | gated on |
|---|---|---|---|---|
| **1** | **Rung −1 — the ceiling control** | put shuffled text on the ladder below rung 0. A measure that scores word salad **above** rung 10 is reading unpredictability and is dead whatever its rho was | **~25 min** | — |
| **2** | **Shuffle granularity sweep** | replace the binary shuffle test with a curve: paragraph / sentence / phrase / word. Tells us **at what scale** a measure lives instead of yes-no | ~40 min | — |
| **3** | **Layer ratio, re-adjudicated** | it went back to *unresolved*, not dead. Re-run against the ladder only, with #1 and #2 as its controls | ~30 min | #1, #2 |
| **4** | **The dwell corpus** | T-3's regime: artifacts whose makers hold **one sub-goal for long stretches**. Sustained arguments, single-session drafts, technical postmortems. Decision-counting is well-defined there and nowhere else | acquisition, not compute | a sourcing decision |
| **5** | **Leaked-layer separation** | artifacts where maker STATE varies and SPECIFICATION does not | — | **the curator's readings** |
| **6** | Triangle edges on real text | **re-specified by T-1** — it is not a triangle, and T-5 says process-side offers no instrument advantage. Reduced from 5 edges to the 2 live ones | ~2 h | was ~5 h |

**#1 and #2 are both cheap, both methodological, and both would have caught errors we made.**
That is why they are ahead of anything that could produce a positive result.

---

## §3. Cancelled, with reasons

| | why |
|---|---|
| ~~`purpose_breadth`, early vs late books~~ | **its measure is dead.** Sim T-2: `purpose_breadth` is confounded with difficulty — at matched difficulty, excess breadth from diversity is **−0.013 to −0.025**. Running it would produce a difficulty gradient and we would read it as expertise |
| ~~Layer ratio on a 7B~~ | gated on `survival < 0.5`; the gate fired correctly and it skipped itself. Now moot — the survival number it gated on has been retracted |
| ~~Rebuild the probe around the process posterior~~ | **T-5.** T-1 found process is the source and goal a sink, which looked like it demanded a rewrite. T-5 scored both as detectors and it is a **tie** (median +0.015 / −0.002). The asymmetry has no instrument consequence |

---

## §4. The standing bar — revised

Ten measures died. Each control is a grave with a name on it. **Ordered by what it licenses now,
not by how often it fires** — see [`method/CONTROLS.md`](../method/CONTROLS.md).

1. **Construction** — hold register, topic, format, generator fixed by *building* the corpus that
   way. The ladder. C3. **This is the only control that has never been wrong.**
2. **Matched comparison** — within-author, within-maker.
3. **Length** — correlation with word count, computed *before* the verdict. Above 0.4 voids.
4. **No-maker (N28)** — does it move where there is nothing to measure?
5. **Rung −1** — does it *peak* where there is nothing to measure? **New, and unbuilt.**
6. **Shuffle** — **valid for text statistics only.** It is not entitled to a verdict on anything read
   out of a model's activations, and it gave one anyway; that has been retracted.
7. **Power, computed first** — added after D-0 ran at 38%.

---

## §5. Assets

| | |
|---|---|
| `corpora/ladder/` | 50 artifacts, five rungs, known monotone intent manipulation, randomised content. **The only properly controlled comparison in the project** |
| `corpora/nomaker/` | 36 artifacts, thin / rich / averaged |
| `corpora/store/` books | 34 works, 10 authors, several each — a per-maker baseline |
| `results/readings/` | 11 artifacts read aloud by a human, two sessions |
| the seven controls above | failures now take 15 minutes instead of 14 hours |

---

## §6. Not queued, and why

**More function-word work** — ceiling is author identification and we are past it.
**A new fetched corpus (C-14)** — an acquisition decision, not a night of compute. But see #4:
T-3 has now specified what a *useful* new corpus would look like, which C-14 never had.
**Gate 4** — still needs to know what it should measure. Two of four survivors died today.

---

## §7. Curator-side

| | |
|---|---|
| artifacts 6–10, session 02 | the only source of human-labelled maker states |
| **C-20 — a second reader** | even n = 2 on 3–4 artifacts, answering Q1 and Q3. One reader cannot bound their own cap (E10) |
