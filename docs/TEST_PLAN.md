# Every test worth running, given the triangle

**2026-08-05.** Written after the curator's three thoughts, which reorganised what the project is
measuring. Ordered by *what could change a conclusion*, with the confounds each must survive.

**Every test on this list is a demo on real data or on generated data with a known manipulation.**
None is a model of the mechanism — those go to the parent simulation, listed separately at the end.

---

## §0. The three controls every test must now pass

Written first because seven measures have died to exactly these, in this order.

| | |
|---|---|
| **shuffle** | Re-run on word-shuffled text. Vocabulary and length preserved, all structure destroyed. A surviving effect **is** a vocabulary statistic. |
| **length** | Correlation with word count, computed **before** the verdict. Above 0.5 voids it. |
| **the rich arm** | Does the measure rank machine-written-with-intent above machine-written-without? A measure that treats them alike is a machine detector. |

---

## §1. The intent ladder — running now

**The rich-arm result, done properly.** Five rungs, 0 / 1 / 3 / 6 / 10 randomly-drawn specifications
per prompt, content randomised, length the only systematic variable, and **no specification names a
decision, alternative or uncertainty** — which is the flaw that made the first version possibly
measure instruction-following.

Tests **monotonicity**, which is far harder to produce accidentally than a two-group split. Any
measure can separate two groups by luck; ranking five in order with randomised content cannot.

Pass: rho > 0.4 against rung, p < 0.01, surviving the shuffle control.

---

## §2. The layer ratio — the curator's, and the highest-value untried thing

> Human text should trigger **more low-order affective activation relative to high-order** than
> machine text does.

**Why it is structurally different from everything that has failed:** it is a **ratio between two
layers of the same reader on the same text.** Length, register and vocabulary act on both layers
and largely cancel. Those three confounds killed five measures.

The pieces exist. `results/b/VERDICT.md` found affect directions real at 4× chance, **not lexical**
(bag-of-words scores exactly chance on the same sentences), and **bimodally distributed across
depth** — an early locus, a dead middle, a late locus. That is the structure this needs.

Run on: Gate 3's 51 artifacts, the 36 no-maker artifacts, and the ladder. Three populations, one
measure, and the ladder gives it a monotone target rather than a binary one.

---

## §3. The five unmeasured edges of the triangle

`docs/theory/THE_TRIANGLE.md`. Goal, process and values each bootstrap the others — six directed
edges, and **E36 measured one.** Gate 3 built its whole primary on that single edge.

The design is the same each time: **supply prior information at one vertex, measure recovery at
another**, against a control that gets no prior.

| supply | measure | status |
|---|---|---|
| the goal | process recovery | E36 — the only one done |
| **the values** | **process recovery** | unclaimed |
| **the values** | **goal recovery** | unclaimed |
| **the process** | **goal recovery** | unclaimed |
| **the process** | **values recovery** | unclaimed |
| **the goal** | **values recovery** | unclaimed |

Cheap: the probe already takes a supplied purpose at stage B. Supplying a *value* or a *process*
instead is a prompt variant, not new machinery. **Five tests, one afternoon of GPU, and nobody in
the literature has run any of them.**

---

## §4. Goal diversity against expertise

The curator's mechanism: practice → automaticity → the decision leaves deliberate control → it is
made by **drives** instead. So an expert's artifact carries more motivational variety without the
expert choosing it.

**Two predictions using quantities that already exist:**

1. `purpose_breadth` **rises** with maker expertise
2. `purpose_agreement` **stays flat** — the goal is still one goal; it is the sources feeding it
   that multiply

The second is what makes it a real test rather than a restatement, because "expertise makes things
more complicated" would move both.

**Corpus:** the 34 public-domain books already have an expertise proxy — early works against late
works by the same author. Within-author, so identity is controlled by construction.

---

## §5. The wall, third attempt — and its last

Displacement-from-baseline failed twice. **The layer ratio (§2) is a different quantity** and gets
one attempt at the same question. If it fails, the wall is not measurable in a reader's activations
by anything this project can build, and that should be written down rather than retried.

---

## §6. The human side, which nothing can substitute for

**The reading sessions are the only source of human-labelled maker states.** Two sessions,
eleven artifacts, and the protocol now asks the right questions.

The measurements that need them:

- **A-1** — can a model with no interior predict what affect a human attributes? Needs the curator's
  affect labels against the probe's.
- **the veneer-variation claim** — his primary detector, and no instrument has been pointed at it.
- **the contrast test for D-0b** — function words tracking state in *humans*, which is the thing
  D-0b could not address.

**C-20 stands.** One reader cannot bound their own cap, and everything here rests on one.

---

## §7. What should go to the simulation instead

Sent as `FOR_GHOST_SCALE_SIM_2.md`. These are mechanism questions, and a mechanism question run on
real text is a question run without ground truth.

| | |
|---|---|
| **T-1** | Do the triangle's six edges actually bootstrap each other, and are they symmetric? |
| **T-2** | Does goal diversity rise with automaticity, holding decision count fixed? |
| **T-3** | Is a count of recovered decisions ever recoverable, or is the graded measure always required? |
| **T-4** | Does the leaked/emblematic divergence survive when the reader is itself uncertain? |

---

## §8. Not doing, and why

**More function-word work.** Its ceiling is author identification and we are past it.

**Anything on the Gate 3 corpus as a primary.** It has been read many times; it is a diagnostic
corpus now.

**A new fetched corpus.** C-14 is owed, but it is an acquisition decision rather than a night of
compute, and every test above runs on what exists.
