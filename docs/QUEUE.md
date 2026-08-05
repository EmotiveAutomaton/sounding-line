# The queue — what is left, in order, with what it costs

**2026-08-05.** Written to survive a compaction. Rates are measured from today's runs, not guessed:
**one probe loop ≈ 1.9 min · one generation ≈ 1.1 min · one activation read ≈ 0.3 s on GPU.**

---

## Running now

**Layer ratio, split by the validated loci.** The first version split layers into thirds; the
affect-direction accuracy is **bimodal** (a locus at 0–1, a dead middle, a second at 22–27), so
thirds average the dead middle into both terms. This uses the loci themselves. **~20 min.**

---

## Queued, in order

| # | test | what it needs | ETA | gated on |
|---|---|---|---|---|
| **1** | **Layer ratio at the loci** | running | 20 min | — |
| **2** | **Leaked-layer separation** | artifacts where maker STATE varies but SPECIFICATION does not | — | **the curator's readings** |
| **3** | `purpose_breadth`, early vs late books | 10 authors × 2 periods × k=3 = 60 loops | ~2 h | — |
| **4** | Triangle edges (5 unmeasured) | 10 artifacts × 5 edges × k=3 = 150 loops | ~5 h | sim T-1 would re-specify it |
| **5** | Layer ratio on a 7B | same design, larger model | ~1 h | only if #1 improves |

**#2 has no ETA because it is not compute-bound.** It is the only test that can separate the
leaked layer from the emblematic one, and it needs human-labelled maker states, which exist only in
`results/readings/`.

---

## The standing bar every measure must now clear

Nine measures died. Each control below is a grave with a name on it.

1. **Shuffle** — re-run on word-shuffled text. Survives = it is vocabulary. *Only the layer ratio has ever failed this in the right direction.*
2. **Length** — correlation with word count, computed before the verdict. Above 0.4 voids.
3. **The ladder** — rank five rungs of known increasing specification, content randomised.
4. **The rich arm** — rank machine-written-with-intent above machine-written-without, or be a machine detector.
5. **The no-maker set** — 36 artifacts, three kinds, length-matched.

---

## Assets that did not exist two days ago

| | |
|---|---|
| `corpora/ladder/` | 50 artifacts, five rungs, known monotone intent manipulation, randomised content |
| `corpora/nomaker/` | 36 artifacts, thin / rich / averaged |
| `corpora/store/` books | 34 works, 10 authors, several each — a per-maker baseline |
| `results/readings/` | 11 artifacts read aloud by a human, two sessions |
| the five controls above | the reason failures now take 15 minutes instead of 14 hours |

---

## Not queued, and why

**A new fetched corpus (C-14).** An acquisition decision, not a night of compute.
**More function-word work.** Ceiling is author identification; we are past it.
**Gate 4.** Needs #1 and the sim's T-1 to decide what it should even measure.
