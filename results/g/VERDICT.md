# G — the channel works, and the statistic did not

**2026-08-03.** 34 public-domain books, 10 authors, several works each, 22.2M characters.
Fetched via the same robots-honouring fetcher as everything else. No GPU.

---

## The headline

> **G-2 PASSES.** Function words separate **one author's different works** at 63.3% against 30.8%
> chance — **2.05×**, every one of ten authors above chance, against a permutation null of
> 31.0% (sd 1.7%).
>
> **The channel carries substantially more than identity.** There is capacity for state.

And underneath it, a correction that matters more:

> **The separability statistic I have used since D-0 is wrong.** It understated a known-good signal
> by enough to call it absent.

---

## §1. The statistic failed a task with a known answer

Author identification from function words is the most established result in stylometry. So it is
not a hypothesis — it is a calibration, and a measure that cannot do it is broken.

| at 2,000-word windows | result |
|---|---|
| **univariate separability** (mine, since D-0) | ratio **0.51** → *"no group information"* |
| **Burrows' Delta, nearest centroid**, leave-one-**work**-out | **52.4%** vs 10% chance → **5.2×** |

The information is in the **joint** distribution across categories. Averaging per-category
F-ratios discards exactly the structure that carries it.

**This is the fourth instance in this project's lineage of a criterion unable to do its own job,
and the first caught by testing the criterion against a task whose answer was already known.** That
check should have run before D-0, not after G-1 looked wrong.

`separability()` is retained as a per-category diagnostic — *which* categories move is still worth
knowing — but it decides nothing from here.

### What it invalidates

- **D-0's design**, already inconclusive on power, is now doubly so: wrong statistic *and* too
  little text.
- **G-1's calibration reading.** The rise with window length was real (0.22 → 1.38) but the
  absolute numbers meant nothing.
- **G-2's first reading**, which came back FAIL at median 0.38 and was wrong.

---

## §2. G-2, rerun properly

Leave-one-window-out, nearest centroid on z-normalised vectors, 2,000-word windows, 18 categories.
Identity is controlled by construction: every window inside a comparison is the same person.

| author | works | n | accuracy | chance | lift |
|---|---|---|---|---|---|
| twain | 4 | 80 | 80.0% | 25.0% | **3.20×** |
| wells | 4 | 76 | 72.4% | 25.0% | **2.89×** |
| dickens | 4 | 74 | 56.8% | 25.0% | 2.27× |
| melville | 3 | 47 | 72.3% | 33.3% | 2.17× |
| conan-doyle | 4 | 80 | 51.2% | 25.0% | 2.05× |
| wollstonecraft | 2 | 32 | 93.8% | 50.0% | 1.88× |
| darwin | 3 | 60 | 60.0% | 33.3% | 1.80× |
| stevenson | 3 | 52 | 59.6% | 33.3% | 1.79× |
| eliot | 3 | 60 | 51.7% | 33.3% | 1.55× |
| **austen** | 4 | 80 | 35.0% | 25.0% | **1.40×** |
| **mean** | | | **63.3%** | **30.8%** | **2.05×** |

**Permutation null** — work labels shuffled within each author, 20 draws: **31.0% (sd 1.7%)**.
Observed 63.3% is about nineteen standard deviations above it.

### The confound, and the honest bound

Different works differ in **topic, genre, narrator and period** as well as in anything
state-like. Function words are supposed to be topic-independent, so if the premise holds topic
should contribute little — but *should* is not evidence.

**Austen is the control and she is the weakest result.** Four novels, one genre, one narrator mode,
a fifteen-year span: the tightest available hold on everything except the writer's state. She comes
in at **1.40×** — real, well above the 31% null, and *half* the aggregate lift.

**Read that as the honest floor.** Some of the 2.05× is topic and genre. The within-genre residue
is smaller and still present.

---

## §3. What this licenses, and what it does not

**Licensed.** D-0b is worth running. The channel has capacity beyond identity, so a
state-separation question is no longer obviously hopeless.

**Not licensed.** Nothing about *affect*. These authors' states are unknown and unlabelled;
"different work" is not "different affect". G shows the channel has room. It does not show what
fills the room.

**Also not licensed:** any earlier number computed with `separability()`. That includes the
half-A/half-B leakage run in `results/leakage/`, which needs recomputing with `delta_classify`.

---

## §4. The corpus is the other output

34 works, 10 authors, 2–4 works each, 22.2M characters — and **it is the per-maker baseline
`measures/leakage.py` says the whole approach needs.** H is therefore partly done: the design
stylometry uses for baselines is several works by one author, and that now exists locally.
