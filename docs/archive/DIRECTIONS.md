# Directions forward

**2026-08-03.** After D-0 came back inconclusive and the emotion-concepts paper turned out to
answer more than it was asked.

---

## §1. What the paper actually gives us

*Emotion Concepts and their Function in a Large Language Model* (Anthropic, arXiv 2604.07729).
Four findings, and three of them are load-bearing here.

**a. The method is a recipe we can run.** 171 emotion concept words → have the model generate
stories depicting each → extract the characteristic activation vector per concept → validate by
checking it fires on semantically matched passages. Nothing exotic. It is a labelling procedure and
a mean.

**b. The representations are LOCAL — per token position, tracking the operative emotion of the
current context.** Not a persistent mood. That is exactly the granularity an artifact reading
needs: *what is the emotional content at this point in this text*, which is a per-span quantity,
which is what evidence spans already are.

**c. The model holds a CHARACTER's emotion separately from its own, then returns to its persona.**
It already does the thing this project needs — represent *someone else's* state while reading about
them, distinct from its own.

**d. And the one that changes the design:**

> *Desperation drove the model to take unethical actions* **even without obvious emotional
> language markers in outputs.**

**The internal representation carried an affect the surface did not.** That is leakage with no
lexical trace — and it is a direct statement that any text-surface measure, function words
included, will miss some of what is there. It is the strongest evidence yet that the leaked layer
is real and that reading it from the outside is the wrong side of the problem.

---

## §2. B′ — read the activations while the model READS

Not "steer the model." Feed it an artifact and record which emotion vectors fire, where.

- **method exists** (§1a), **granularity matches** (§1b), **and it is already the other-person
  case** (§1c)
- **no sparse counting.** D-0 died on five-token categories in a 380-word sample. Activations are
  dense and continuous; the failure mode that killed D-0 cannot occur.
- **two readouts, and the second is the curator's:**
  1. *which* emotion concepts fire, per span → the affect reading
  2. **the ratio of low-order to high-order affective activation.** Early layers carry
     valence/arousal — core affect, Panksepp. Later layers carry conceptual/predictive structure —
     Barrett. **That ratio is the leaked/emblematic split, measured mechanistically in the reader
     rather than inferred from the text.**

Cost: `torch` + `transformers`, a local 9B with `output_hidden_states`, an afternoon.
Open question: whether a 9B open model has the structure Sonnet 4.5 has. The interpretability
literature says emotion directions appear in small models too, so probably — but that is the first
thing to check, and it is cheap.

---

## §3. E — the wall, measured inside the reader

**This is the strongest new idea here and it follows directly from §1c.**

The model instantiates a separate representation for a character's emotional state, then drops it.
So:

> **When it reads an artifact with a recoverable maker, does it instantiate a distinct maker-state?
> When it reads the wall — legible and empty — does it fail to, and fall back to its own persona?**

That is E37 turned from a claim about artifacts into a measurable event inside the reader.
Non-invertibility stops being *"the posterior is diffuse"* and becomes *"the reader could not
build a separate agent to attribute this to."*

It is also the one measure here that needs no ground truth about the maker, no corpus labels, and
no human agreement. **And it is exactly what MIN says this architecture is uniquely required for** —
the wall is the only finding in the parent simulation that needs a reader holding a distribution
rather than a best guess.

Pre-registrable now: machine-generated artifacts should show *lower* separate-agent instantiation
than human ones, and the control is the same three locked generated artifacts that broke unlock.

---

## §4. F — steer the reader, not the text

Desperation steering changed behaviour without surface markers. So steering should change
*reading* too.

> Read one artifact under several steered reader-states. **Does what the reader recovers depend on
> the reader's affect?**

That is E10 — *reader skill caps extraction* — made manipulable instead of merely observed. And it
is the cleanest available test of the project's founding claim that a reading is a joint property
of artifact and reader, not a property of the artifact.

It has a sharp negative form: if steering the reader changes the reading a lot, then **every number
this project has ever produced is a reading by one particular reader-state**, and that belongs in
`may_not_claim`.

---

## §5. G — scale up before scaling down

The curator's point, and it reframes D-0's failure as a corpus problem rather than a channel one:

> It might have always been true that we needed to start on whole books and then scale down to
> articles.

Function-word statistics are volume-hungry. 380 words gives ~5 tokens in a category and no power.
A 3,000-word essay gives ~40. **A book gives 4,000.** Everything that was undetectable becomes
trivially detectable, and the measurement can then be *calibrated downward* until it breaks — which
tells you the actual resolution limit instead of guessing it.

Public-domain books are free, plentiful, long, and come with known authors — **which also solves
the per-maker baseline problem A actually needs.** Multiple works per author, decades apart,
different topics: that is the design stylometry uses, and it is available for the cost of a
download.

**This is probably the cheapest real progress on the list.**

*Noted for much later, not now:* decision density is highest in visual and auditory media, and text
is the tractable starting point rather than the interesting endpoint.

---

## §6. H — per-maker baselines from archives

A's actual blocker is that a corpus-mean baseline answers *"unusual for this collection"* when the
question is *"unusual for this person."*

Many of the Half A makers have archives — dozens of posts, one author, one register. Fetching
10–20 per maker turns every deviation into a within-maker deviation. **This is a fetch job, not
research**, and the fetcher already exists and honours robots.txt.

Combines with §5: books for the long-form calibration, archives for the per-maker baseline.

---

## §7. Ranked

| | what | cost | why it ranks here |
|---|---|---|---|
| **G** | public-domain books, long-form calibration | hours | fixes D-0's real problem and H's at once; free |
| **E** | the wall, measured inside the reader | needs B′ | strongest new claim, needs no labels |
| **B′** | activation readout while reading | an afternoon | enables E and F; validated method |
| **H** | per-maker baselines from archives | hours of fetching | what A needs to mean anything |
| **F** | steer the reader | needs B′ | can invalidate every number here, so worth knowing |
| **D-0b** | the powered rerun | 40 min | already queued |

**G and H need no GPU and no new dependency.** They can run beside Gate 3 tonight.

---

## §8. The thing to hold onto

D-0 was inconclusive because the sample was too small to see anything. §1d says the paper found
affect that *had no surface trace at all*. Those are the same lesson from two directions:

> **The outside of the text may not be where this is measurable.** Everything the project has built
> reads the artifact. The two most promising directions here read the *reader*.
