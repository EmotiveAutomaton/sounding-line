# How to extract leakage from an artifact

**Round 3, 2026-08-03.** Short by request.

---

## §1. Leakage has a textual operationalisation, and it is 60 years old

**Function words.** Pronouns, articles, prepositions, conjunctions, auxiliaries.

- Produced **non-consciously**, topic-independent, stable across an author's corpus.
- <0.1% of vocabulary, ~**60% of words used**.
- **Very hard to fake.** This is why authorship attribution works at all.
- Track **psychological state**, not just identity: `I`-frequency predicts depression *better than
  negative-emotion words do*. Liars use fewer first-person singulars and fewer exclusives
  (`but`, `except`).

Content words are the deliberate layer. Function words are not.

> **leaked ≈ function-word distribution. emblematic ≈ content-word choice.**

That is computable today, on the corpus we have, without asking a model for a label.

**And it says stage E is measuring the wrong layer.** Asking an LLM *"what stance is performed"*
returns a content-word judgement. Stage E is an emblematic instrument by construction, on both of
its outputs. The leaked layer needs a different kind of measurement, not a differently-worded
prompt.

---

## §2. Your automaticity intuition is the mechanism stylometry runs on

You said leakage shows up as *automaticity bending* — the word choice the author never noticed
making. That is exactly the assumption behind function-word attribution: **style is unconscious, so
it survives intent.**

Two distinct signatures fall out, and they are not the same measurement:

| | what it is | measurable as |
|---|---|---|
| **function-word drift** | the automaticity bending | deviation from the author's own baseline, or from register norms |
| **attention dwell** — your feet example | content-side, not style | text spent on something past what the argument needs |

The first needs a baseline (multiple artifacts by one maker, or a register model). The second needs
a model of argumentative need. **Neither needs an LLM to introspect.**

---

## §3. Production-level leakage, from the deception literature

Text length, fluency, **revisions, repetitions, reformulations**, cognitive-load signatures —
reduced concrete detail, oversimplification, generalisation. These leak *despite* the writer
managing the narrative.

Caveat, and it is recent: a 2025 cross-linguistic study argues the limits of deception detection
from text are real and structural. Take the features, not the promise.

---

## §4. The internal state already exists. You do not need to build a limbic system

This is the finding I did not expect.

Mechanistic interpretability work on LLMs, 2025:

- **171 linear directions** in activation space corresponding to emotion concepts, with
  **causal** effect on behaviour.
- The geometry **mirrors human psychology** — principal components align to **valence and arousal**.
- Circuit-based modulation induces target emotions at 99.65% accuracy.
- Mid-layer attention heads carry the emotion decision.

Valence-and-arousal is **core affect** — the dimensional substrate, Panksepp's side of the
argument — **not** constructed categories.

> **The model's activations are closer to the leaked layer than its outputs are.**
> Its text is emblematic. Its internals are dimensional.

So the simulation literature's demand — *the reader must have an internal state like emotion* — is
already satisfied, unbidden. The instrument is not "wrap an MCP limbic system." It is **read the
one that is already in there** instead of asking the model to describe it.

That is also the cleanest form of *empathy without emotions*: the model has a representational
geometry of affect, and no interoception. Exactly the split argued in `AFFECT_ARCHITECTURE.md` §5,
now with an empirical instantiation rather than an argument.

---

## §5. The formal frame, named

**Bayesian Theory of Mind / inverse planning** (Baker, Saxe, Tenenbaum). Build a generative model
of how mental states cause actions; invert it with Bayes. There is a paper literally titled
*Theory of mind as inverse reinforcement learning*.

That is the essay's appreciation-as-IRL, already formalised, already implemented for spatial
agents. Sounding Line's version is the same inversion over **artifacts** instead of trajectories.
Nothing here needs inventing — it needs porting to a domain nobody has ported it to.

---

## §6. Options, costed

You asked what our actual options are. Four, and they are not exclusive.

**A · Function-word leakage.** Compute the leaked layer from function-word distributions instead
of from a prompt. Cheap, runs on the existing corpus, no GPU, 60 years of validation behind it.
**Needs a baseline** — either several artifacts per maker, or a register model. *This is the one I
would do first.*

**B · Activation readout.** Probe the local model's mid-layer activations for the valence/arousal
directions while it reads an artifact, instead of asking it for an affect label. Medium cost,
needs a hook into Ollama we do not have, and it turns the probe into a measuring instrument rather
than a respondent. **Highest ceiling of the four.**

**C · Keep stage E, scoped honestly.** It is an emblematic instrument. Run it, call it emblematic,
and stop claiming it reaches the leaked layer. Nearly free — it is already built. Combines with A
to give the two layers by two *different methods*, which is stronger than one method twice and
makes N-AFF-3 a real test rather than a formality.

**D · Full inverse-planning port.** Generative model of maker→artifact, inverted. This is the
research programme, not a build. Years, not weeks.

**A + C is the next move.** It gives both layers, by independent methods, on data we already have,
without touching Gate 3.

---

## §7. The thing to keep in view

> The goal of Sounding Line is just to be able to measure depth. It's just that.

Depth is *decisions recoverable*. §1 says a whole class of decisions — the automatic ones, the
compressed ones, the ones the maker never noticed making — has a measurement channel this project
has not used. **That is not scope creep into the empathy project. That is the depth measurement,
done properly.** The essay already said the automatised decisions count; nothing here has ever
counted them.

---

## Sources

- [The Psychological Functions of Function Words](https://www.researchgate.net/publication/237378690_The_Psychological_Functions_of_Function_Words)
- [Function Words in Authorship Attribution: From Black Magic to Theory?](https://aclanthology.org/W14-0908.pdf)
- [The Secret Language Code — Pennebaker](https://www.scientificamerican.com/article/the-secret-language-code/)
- [The Linguistics of Analysing Deception in Written Texts](https://www.cambridge.org/core/elements/abs/linguistics-of-analysing-deception-in-written-texts/C257606CC51F70AAED702FBBDE7C41EC)
- [What if Deception Cannot be Detected? Limits of deception detection from text](https://arxiv.org/pdf/2505.13147)
- [Do LLMs "Feel"? Emotion Circuits Discovery and Control](https://arxiv.org/pdf/2510.11328)
- [Where Do Models Find Happiness? Emotion Vectors in Open-Source LLMs](https://arxiv.org/pdf/2606.26987)
- [Mechanistic Interpretability of Emotion Inference in LLMs](https://aclanthology.org/2025.findings-acl.679.pdf)
- [Baker, Saxe & Tenenbaum, Bayesian Theory of Mind](https://web.mit.edu/9.s915/www/classes/theoryOfMind.pdf)
- [Theory of mind as inverse reinforcement learning](https://www.sciencedirect.com/science/article/abs/pii/S2352154618302055)
- [Gallese, Embodied simulation: from mirror neuron systems to interpersonal relations](https://onlinelibrary.wiley.com/doi/abs/10.1002/9780470030585.ch2)
