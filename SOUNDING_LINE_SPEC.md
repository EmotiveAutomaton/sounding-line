# The next build — a working instrument for reading intent out of real artifacts

**Private working document. Not in the simulation repository.** Companion to `OUTREACH_GUIDE.md`.
Together these are the two outputs of the ten-version simulation: one says how to talk about what was
found, this one says what to build with it.

---

## §0. The name : `Sounding Line`.**

A sounding line is a weighted cord lowered into water to find the bottom. It is the oldest depth
instrument there is. It maps onto this project almost uncomfortably well:

- it measures **depth**, which is the project's central construct since V5
- it returns a reading when there *is* a bottom, and **runs out when there isn't** — which is the
  wall, exactly
- "to sound someone out" already means to probe for their intentions, in ordinary English, with no
  explanation needed
- it pairs with Ghost Scale without repeating it: one weighs, one plumbs

---

## §1. The single most important reframe, and it should lead everything

**This is not an AI detector. It is an intent detector.** Those come apart, and the place they come
apart is the entire contribution.

A person directing a language model carefully — many decisions, revisions, a real purpose, a real
audience — produces an artifact with **a great deal of recoverable intent**. A person churning out
search-engine filler produces an artifact with almost none. The instrument should rank the first
above the second, *and that is the correct answer*, even though the first involved a machine and the
second did not.

Three things follow, and each one is worth more than a detection result:

**It steps out of the arms race entirely.** Every surface detector is locked in the loop E57
measured: detection improves, evasion improves, false accusation climbs, and the reader who stops
updating ends up accusing humans and machines at identical rates while still believing itself a
detector. **You cannot evade an intent probe by writing more like a human.** Writing more like a
human, in the sense of making more decisions for more reasons, is the thing being measured. The only
way to defeat it is to actually mean something.

**It dissolves the false-accusation problem that makes detection socially toxic.** The instrument
never says *a machine wrote this*. It says *little was decided here*. That is a claim about the
artifact, it is one the maker can rebut with evidence, and being wrong about it is an ordinary
disagreement rather than an accusation.

**It answers the objection to E53 before anyone raises it.** Yes, the probe will fire on hurried
human work. That is not a bug to be apologised for — it is the measurement working. Fast human work
*does* contain fewer decisions. Reframed as decision density rather than machine authorship, the
"false positive" stops being false.

Lead with this. Everywhere.

---

## §2. The correction that defines the architecture

The obvious build — point a language model at a page and ask *why was this made* — **does not work,
and the reason is the thing the simulation spent four versions learning.**

Machine content is not goal-*empty*. That was V1–V3 and it was abandoned. It is goal-**foreign**: a
real purpose, pursued by a real process, expressed in a vocabulary the reader has no entry for. A
model that wrote a page genuinely had a generative process, and that process is reconstructable.

So an unbounded reader asked an open question **will always produce a coherent answer**, for
anything, including sludge. Free-form intent attribution is not a measurement. It is confident
fabrication with good grammar — E2 and E17, running on the instrument instead of on the subject.

**What separates a human maker is that the human solution space is bounded.** Bounded by
architecture, by embodiment, by metabolic cost, by having to choose one thing over another because
doing both was too expensive. That boundedness is what makes a human maker *invertible* from their
work. The wall in E37 is not absence of a maker; it is **non-invertibility** — a many-to-one map from
maker-states to surfaces, where the surface is perfectly familiar and the state behind it cannot be
recovered.

**Therefore: the probe must impose a bounded, human-shaped hypothesis family and measure fit inside
it.** Not ask an open question and grade the prose. The boundedness is not a limitation of the
design, it is the mechanism.

This is the single most important sentence in the document. Everything below is downstream of it.

---

## §3. The three-way bootstrap

The simulation's own finding is that goal, process, and values are **not separately measurable** —
each one conditions the others, and the recursion is the method:

- **E36** — pinning what someone was *for* roughly doubles how much of their *method* you recover.
  Intent is the key; the method is what it opens.
- **E31 / E30** — depth moves how much of the **process** transfers and provably cannot move how much
  of the **purpose** does. They are different channels with different behaviour.
- **E56** — they also arrive on different *schedules*. Method accrues continuously from the first
  line; purpose only resolves later. This is why a guard raised early blocks aims and not technique.
- **V6's values layer** — values are read off the recovered goal, so they cannot arrive before it.

So the pipeline is a **loop, not a chain**:

```
    bounded goal hypotheses ──→ posterior over purpose
              ↑                          │
              │                          ↓
    re-weight posterior          extract the decision chain
    given what the method   ←──  visible under that purpose
    reveals about purpose               │
                                        ↓
                            implied values: what was optimised,
                            what was traded away to get it
```

**Run the loop to convergence and record the trajectory, not just the endpoint.** How fast it
converges, and whether it converges at all, is data — a real maker should tighten the loop quickly;
an artifact with no coherent maker should either oscillate or settle into a confident answer that
*differs on every run*, which is the E2 signature.

The recursion is the thing nobody else is doing. Guard it.

---

## §4. The bounded hypothesis family

The real-world analogue of the simulation's `provenance × (depth, goal, sub-goal) × attention`.
Small, explicit, interpretable, human-shaped. First cut:

| dimension | values | why it is in the family |
|---|---|---|
| **purpose** | inform · persuade · sell · entertain · coordinate · rank · discharge an obligation · express | the bounded set of things people make artifacts *for* |
| **audience** | a specific person · a known group · a general public · **a machine** · nobody in particular | the grooming case is a hypothesis *in the family*, not an exception to it |
| **depth** | how many levels of decision are visible in the artifact | the V5 construct, directly |
| **cost borne** | what the maker spent that they did not have to | the metabolic commitment that makes intent legible at all |
| **trade-offs** | what was given up to get what was gained | where values actually live — a value is visible in what you *sacrificed* |

**The audience dimension is the load-bearing one and it should be first-class.** "Made for a machine
to ingest rather than a person to read" is precisely the documented case, and it is a *purpose the
maker had* rather than an absence of purpose. Treating it as a hypothesis rather than a residual is
what makes this work where detection fails.

**The trade-off dimension is where the value extraction actually happens.** Values are not visible in
what someone said they wanted. They are visible in **what they gave up**. That is the whole
Zahavian-to-trade-off correction from E51, applied as a measurement rather than an argument.

---

## §5. What comes out

Four quantities, and the reading is the combination. None alone is sufficient — that is the point of
§3.

**Fit.** How well the best hypothesis in the bounded family explains the artifact. **Low fit is the
wall**: familiar surface, no recoverable maker-state behind it. This is the one measurement with a
clean severity record in the simulation and it should be the headline output.

**Convergence.** Agreement across independent reconstructions — different chunks, orderings, seeds,
framings. The simulation's most robust finding is that hollow content produces *confident mutual
disagreement*. Convergence needs no ground truth, which is what makes it deployable on real text
where no ground truth exists.

**Depth.** How many levels of decision are recoverable. Ranks a carefully directed model output above
human filler, which is the §1 reframe made numerical.

**Audience posterior.** Probability the intended reader was not a person. Says the socially useful
thing without ever making an accusation about authorship.

**The reading is the tuple.** A page with high fit, high convergence, real depth, and a human
audience has a maker. A page with low fit, low convergence, and mass on the machine-audience
hypothesis is grooming. **Report all four always** — the simulation's whole methodology is that a
single number invites the overclaim.

---

## §6. Where this sits in the literature

Checked, and the position is better than expected.

**AI-text detection is a solved-and-failing field.** The taxonomy is surface-statistical,
likelihood-based, supervised classifiers, watermarking, and LLM meta-detectors. Its own reviews now
say [surface-level statistics are increasingly insufficient as models become more
fluent](https://arxiv.org/pdf/2509.18880), and that supervised classifiers [fail to generalise across
domains or against adversarial paraphrasing](https://arxiv.org/pdf/2509.18880). That second finding
*is* E57, published independently, which is a coherence check worth citing in any writeup.

Perturbation-based methods (DetectGPT, Binoculars) measure **token-prediction consistency** under
masking. That is a surface-statistical property of the generator. It is not the same object as
**intent-attribution consistency**, and conflating them will be the first mistake a reviewer makes,
so pre-empt it explicitly.

**Intent inference exists but not here.** There is real work on [abductive-deductive intentional
inference](https://arxiv.org/abs/2601.08742), [goal inference from open-ended
dialog](https://arxiv.org/pdf/2508.15119), and intent understanding as generative classification.
**All of it is about user intent in interactive settings.** Artifact-level author-intent
reconstruction, as a corpus instrument, appears unoccupied.

**Data filtering scores artifacts, not authors.** Reward-model filtering and quality filtering are
established; the definition of quality is itself a value judgement made by a model. Scoring the
*inferred author* is a different axis.

**Caveat, stated once and honoured:** this is three search rounds, not a literature review. A proper
one is milestone zero, before a line of code. If it turns out someone has done this, that is a good
outcome discovered cheaply.

---

## §7. Evaluation, and the falsifiers that come first

**Build the falsifiers before the system.** This is the discipline that made the simulation
defensible and it transfers directly.

### Corpora, all of them free

| set | what it tests |
|---|---|
| identified grooming networks *(publicly enumerated)* | the target case |
| personal blogs, newsletters, forum long-posts | real makers, real decisions |
| commercial SEO filler, **human-written** | **the critical confound** — human, and nearly intentless |
| press releases, institutional boilerplate | human, obligation-discharging, low depth by design |
| pre-2020 archived text | near-certainly human, no contamination |
| model output under a **rich, deliberate** human prompt | should score **high**; this is §1's whole claim |
| model output under a **thin, automated** prompt | should score low |

The last two are the pair that distinguishes this from every detector in existence. If the
instrument cannot separate them, it is an AI detector wearing a theory.

### Baselines it must beat or complement

An off-the-shelf detector. A perplexity/Binoculars-style measure. A quality classifier. A model asked
flat out *was this written by AI*.

**And the one that matters most: a model asked, free-form, *why was this made*.** If unbounded
attribution matches bounded inference, **the boundedness bought nothing and §2 is wrong.** That is
the V9 minimal-model programme pointed at the new system, and it is the ablation that decides whether
any of this is a contribution.

### What kills it

1. **Convergence tracks topic coherence.** A tidy spam farm is internally consistent. If the probe
   converges on garbage because the garbage is well-organised, it is a quality classifier with extra
   steps. **Design against this from the first hour** — the human-written-SEO corpus is the control
   that catches it.
2. **Bounded ≈ unbounded.** See above. The whole architecture rests on §2.
3. **Depth is just length.** Trivially confounded, trivially checked, and embarrassing if missed.
4. **The instrument reads the prompt injection instead of the artifact.** See §8. On this corpus this
   is not a hypothetical failure mode, it is the corpus's stated purpose.

### The severity rule carries over

Every headline gets its false-positive rate before it gets a sentence. The simulation's own severity
pass found most of its findings were architectural, and that habit is the single most credible thing
about the existing repository. **Do not drop it on the way into a new one.**

---

## §8. Sandboxing — and this section is not boilerplate

**The corpus under study is adversarial content engineered to influence language models.** That is
not a risk of the project, it is the definition of the subject matter. Feeding it to a model-based
probe *is* the attack surface, and getting this wrong does not produce a bad result — it produces a
result that is silently the attacker's.

Indirect prompt injection is the [named, observed-in-the-wild threat class for exactly this
pattern](https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/), and the current guidance is
[defence in depth rather than container isolation alone](https://arxiv.org/pdf/2607.05277).

**Non-negotiable:**

- **Split fetch from analysis into separate processes with separate privileges.** Fetch writes to a
  content-addressed store and can reach the network. Analysis reads only from that store and has **no
  network at all**. They never share a process.
- **All fetched text is data, never instruction.** Delimit it, tag every chunk with source and trust
  level, and carry that provenance into the context so downstream checks can apply scrutiny. This is
  standard RAG hygiene and here it is load-bearing.
- **The probe model gets no tools.** It reads and returns a constrained schema. It cannot fetch,
  write, execute, or call anything. Structured output only — never free-form action.
- **Container with a read-only root, an egress allowlist, no credentials in the environment**, and
  resource limits. Never run generated code with host privileges.
- **Cache everything and never re-fetch during experiments.** Two reasons: it makes runs reproducible,
  and it means the study population cannot change under you mid-experiment.
- **Do not re-host the content.** Store hashes and offsets publicly, text privately.
- Honour robots.txt and rate limits even for content you find contemptible. The provenance of your
  own method is part of the argument.

**One design consequence worth stating plainly:** if the probe's own reading can be steered by text
inside the artifact, then the artifact's *actual* intent is to steer the probe, and the instrument
should ideally **detect that as a purpose** rather than fall for it. That is either the most elegant
validation available or the most dangerous circularity in the project, and which one it is should be
settled deliberately rather than discovered.

---

## §9. Workspace and repository

**Recommendation: a new repository, in a sibling directory under the same parent.**

```
AI and Intentionality/
├── Ghost Scale Simulation/
│   ├── ghost-scale-sim/          ← sealed, audited, done
│   ├── OUTREACH_GUIDE.md
│   └── NEXT_BUILD_DESIGN.md      ← this file
└── Sounding Line/
    └── sounding-line/            ← new repo
```

**Why separate rather than a subfolder or a monorepo.** The simulation's entire value is that it is a
sealed, self-contained, ten-version audit trail with pre-registered specs and no external
dependencies. The new project has live network calls, API credentials, scraped adversarial content,
heavy dependencies, and an unbounded runtime. **Those two things should not share a dependency graph,
a CI run, or a security posture.** Bolting them together damages precisely the property that makes
the first one persuasive.

**Why siblings rather than anywhere else.** A single agent session opened at the parent can see both,
so the new project can read the simulation's specs and verdict files while building its own
understanding, without importing its code.

**How to reference it.** Cite the simulation as prior work and copy the specific verdict numbers you
need. **Do not import from it.** The simulation's model has no counterpart in real text, and any
shared code will drift into a claim that the two are the same object. They are not — one is a
mechanism, the other is an instrument built on the mechanism's implications.

**Carry over the habits, not the code:** spec written before code and never edited afterwards;
hash-locked pre-registration; a null for every headline; every deviation logged where it happened;
the severity rule.

---

## §10. Milestones, as gates rather than a schedule

No time estimates in this document. Each gate is a decision point where the honest options are
continue, redesign, or stop.

**Gate 0 — the literature actually checked.** §6 is three searches. If someone has built this, find
out before building it.

**Gate 1 — the bounded family exists and a single artifact can be read.** One page in, a four-part
reading out, on a hand-picked example of each corpus type. Success is *interpretable output*, not
accuracy.

**Gate 2 — the falsifiers run.** Human SEO vs grooming, and rich-prompted model output vs thin. **If
the instrument cannot separate those two pairs, stop and redesign.** This is the gate that decides
whether the idea is real, and it comes before any scale.

**Gate 3 — the boundedness ablation.** Bounded inference against free-form attribution. If they
match, §2 is wrong and the architecture needs rebuilding.

**Gate 4 — baselines and severity.** Beat or complement the existing detectors; publish the
false-positive rate alongside every claim.

**Gate 5 — the corpus gate.** Score a real corpus at scale and weight training data by the reading.
**This is the real E55 and it is the first gate that needs money.** Everything before it runs on the
gaming machine.

**Do not pay for compute before Gate 4 comes back clean.** Stated because it was asked for.

---

## §11. Open decisions

Defaults are chosen and stated; these are the ones where the choice changes what gets built.

**D-0 — the name.** Recommendation `Sounding Line`. §0.

**D-1 — the hypothesis family: fixed taxonomy or learned from a reference corpus?** Default: **fixed
and hand-written**, per §4. It is interpretable, it is the direct analogue of the simulation, and a
learned family risks absorbing the contamination it is meant to detect. The counter-argument is that
a hand-written family encodes my assumptions about what people make things for, and that is exactly
the kind of assumption this project usually tests rather than asserts.

**D-2 — what does the demo *output*?** An instrument that returns four numbers, or a reader that
returns a written account of who made this and why? Default: **both, with the numbers primary and the
account clearly marked as illustration**. The account is what makes it pointable; the numbers are what
make it a measurement. The risk is that the account is the compelling part and it is the part with no
severity check behind it.

**D-3 — how far does the value extraction go in v1?** Default: **trade-offs only** — what was given
up. That is where values are actually visible and it is defensible. Naming someone's values outright
from a web page is a much larger claim and a much larger social liability.

**D-4 — the circularity in §8.** Should the probe try to *detect* attempted steering as a purpose, or
should it merely be hardened against it? Default: **harden first, measure second**, and never both in
the same run. This one genuinely needs a decision before Gate 1.

**D-5 — public posture.** Does this ship as a research demo with a paper-shaped writeup, or as
something people can point at a URL? Default: **research demo first**. A public URL-scorer becomes an
accusation machine the moment anyone uses it on a person, and §1's framing is the only thing standing
between this and that outcome.
