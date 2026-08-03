# The leg of this project I had not seen

**Second research round, 2026-08-03**, at the curator's instruction after he read the first:

> Clearly there's a leg to this project that you aren't aware of and it's going to get real
> complicated... I'm not even sure what kind of framework we could leverage to even begin to
> implement such a thing. Oh, buddy. I guess I have been glossing over it myself.

He is right that I was glossing. The stated end goal is not an instrument:

> My personal end goal is to find a way to fully give AI human empathy, but not human emotions...
> empathy in this case is not some nebulous concept, it's specifically this process that I have
> defined. And it requires some kind of subordinate solution space that converges on these
> predictions of these interoceptive signals.

That is a research programme, and the literature has more to say about it than I expected.

---

## §1. The two layers are not a design choice. They are the field's central unresolved debate

The biggest finding of this round, and it was sitting in plain view.

**Panksepp** distinguishes three levels: **primary** (subcortical core affect, evolutionarily
conserved, pre-linguistic), **secondary** (learning), **tertiary** (cortical — thoughts *about*
emotion). **Barrett** calls only the tertiary level "emotion" and calls the rest "affect." Her
theory of constructed emotion says emotion categories are built from core affect plus conceptual
knowledge, and are not natural kinds.

The reconciliation position, stated in the literature:

> Basic emotion theories are theories of **emotion**, while the theory of constructed emotion is a
> theory of **feeling**.

Now put that against the curator's correction from an hour earlier, which was made with no
reference to any of this:

| his layer | the field's level |
|---|---|
| **leaked** — *"a layer that is TRUE... emotional leakage that can show up in your text"* | **Panksepp's primary process.** Core affect. Involuntary, conserved, pre-linguistic. |
| **emblematic** — *"a conscious social decision"* (his cite: Ekman) | **Barrett's tertiary.** Constructed emotion. Conceptual, culturally learned, categorical. |

**The two-layer model is the reconciliation.** It requires both theories to be true of different
things, which is exactly the position the reconciliation literature has converged on. That is not a
small thing to have arrived at from ten artifacts and a think-aloud.

It also means the two layers should **not** be assumed to share a value set — Barrett's whole point
is that constructed categories are culturally variable while core affect is not. `family_v3.yaml`
currently gives both layers the same eight values by YAML anchor. That is now a **named
simplification** rather than an unexamined default.

---

## §2. Which diagnoses the field's LUST problem, and the curator called it

He said, before any of this was searched:

> I think they were just catching the fact that leakage — they were assuming that leaked fear and
> performed fear are the same thing. I would be willing to bet that was an error on their part,
> and that's why lust is kind of bullshit in this framework, because **the easiest thing to catch
> is the performed section.**

**ANPS is a self-report questionnaire.** A questionnaire can only reach the tertiary level — it
asks a person to *report a category*. Under the two-layer account, LUST is the system least
available to tertiary report, for reasons that are social rather than neural.

So ANPS did not find LUST unmeasurable. It found LUST **unreportable at the layer a questionnaire
can reach**, and then dropped the value. That is a measurement-access artefact, and his objection
was structurally correct before he had the argument for it.

**Artifacts do not have that limitation.** They are not self-reports. This is now the clearest
statement of what Sounding Line could contribute that the existing instrument cannot.

---

## §3. "Emotions are predictions of interoceptive states" is the mainstream position, and it is formalised

He said it as an aside. It is Seth & Critchley's **emotion as interoceptive inference**, and
Barrett & Simmons' **theory of constructed emotion as an active inference account of interoception
and categorization**. Friston and colleagues have the active-interoceptive-inference version.

This matters practically rather than academically: it means the thing he wants to constrain the
solution space with **already has a formalism**, and it is the same formalism the Ghost Scale
theory already runs on. Active inference is not a second framework bolted on — the essay's
appreciation-as-IRL argument and interoceptive emotion are the same machinery pointed at the
outside and the inside.

---

## §4. The hard part, stated as the literature states it

The affective-computing literature draws exactly the line the curator drew:

> Emotional **recognition** does not equal emotional **understanding**; detection does not mean
> comprehension.

And its prescription is the problem:

> Computational modelling should follow neural mechanisms by **having an internal state similar to
> human emotion** and developing a mirror mechanism to understand others' emotions through its own
> experience.

That is his method, described from the other side:

> The mechanism I use to tell how the author felt is by **cycling through a few feelings and
> adjusting it a little bit until it fits** with what they said.

**Simulation Theory, computationally implemented.** It exists — there is a probabilistic
simulation model of affective facial expression processing that maps observed behaviour into the
mind-reader's own latent space. It is a small literature and it is about faces.

**And the probe has no internal state to simulate with.** That is the real objection to stage E,
and it is much deeper than "an LLM will confabulate a label."

---

## §5. The escape, and it is the one that fits "empathy without emotions"

The literature's prescription says the reader needs an internal state *like* emotion. The stated
goal is empathy **without** giving the machine emotions. Those look incompatible. I think they are
not, and the distinction is worth stating precisely:

> **You do not need interoceptive states. You need an interoceptive generative model.**

What simulation requires is the mapping *situation → predicted bodily state → emotion category*.
Running that mapping forward as a **prediction about someone else** does not require instantiating
the bodily state. It requires having the model of one.

A language model trained on human text plausibly has that mapping, because humans write the
mapping down constantly. It has no body and it has no interoception. **The open question is whether
the model without the substrate is sufficient for reading** — and that is testable, cheaply:

> **A-1.** If the probe can predict *which affect a human reader will attribute* to an artifact,
> without any internal state, the generative model is sufficient for the reading task and the
> substrate is not required. If it cannot, the substrate is load-bearing and this project needs an
> architecture it does not have.

Session 02's question 3 is the human side of that test. It was designed for a smaller purpose and
happens to be the right instrument for this one.

Worth being honest about the limit: the substrate may be unnecessary for *reading* and still
necessary for *caring*. Nothing here bears on the second, and the second is the harder half of the
stated goal.

---

## §6. The gap under the gap

There is a small, live literature on **interoceptive AI**: life-inspired interoceptive
architectures that factorise internal from external state variables, and interoception-inspired
regulatory architectures for artificial agents. There is a larger one on affective RL — empathy
reward functions, emotion-informed policy optimisation, emotional alignment as a constrained MDP.

**All of it is about an agent regulating itself.** None of it is about an agent *reading another
agent's affect by simulating it*.

So the position is:

| | exists | this project |
|---|---|---|
| primary-process affect systems | validated in behaviour | borrowed |
| affect from text | LIWC-class r≈0.4; supervised transformer r≈0.85, on projective narratives | neither |
| emotion as interoceptive inference | formalised | adopted |
| interoceptive architectures for AI | small, self-regulation only | not applicable |
| **simulation-based reading of another's affect from artifacts** | **nothing found** | **the claim** |

That last row is the leg he says I was not aware of. He is right. It is not a feature of family v3;
family v3 is a small sighting shot at it.

---

## §7. What changes in the build

**Immediately, from his answers.**

1. `none_legible` → renamed for what it describes. He chose option B and the reasoning is
   decisive: *"humans are excellent at concealing motives... I don't think humans do anything
   unless there's a reason."* The value describes **the reading**, not the maker.
2. The divergence framing was wrong and he corrected it: *"leaked greater than emblematic doesn't
   even count as concealment... if anything the emblematic would get larger. You perform louder to
   cover up. I get extra quiet if I'm extra angry. **The shield matches the leak.**"* Concealment is
   not absence of display — it is display *shaped against* the leak.
3. Lust's second signature is his, and it is better than mine: not
   justification-for-an-unasked-question but **the thing a reader politely glosses over**. *"Someone
   ends up talking about feet for a sentence too long and you're like, ooh, buddy."* An artifact
   where attention dwells past what the argument needs.
4. No additions to the eight. *"We shouldn't add anything, because that's kind of just where the
   literature is right now."* Correct, and §1 gives a second reason: the eight are the **primary**
   layer's vocabulary, and the tertiary layer's vocabulary is a separate question this project is
   not equipped to open.

**A new null, from §1.**

> **N-AFF-3 (layer separation).** `leaked` and `emblematic` must not come back as the same
> distribution. If their mean divergence across a corpus is near zero, the probe is answering one
> question twice and the two-layer model is unsupported by this instrument — whatever is true of
> people.

**And a predicted collapse direction, from §1 and the first review.**

N-AFF-2 says the eight values may collapse. §1 says **which layer will collapse first: `leaked`.**
Language encodes the tertiary layer — that is what the words *are* — while the primary layer
reaches text only through leakage. If one layer separates and the other does not, that is the
expected result rather than a failure of the design.

---

## Sources

- [Basic Emotions or Constructed Emotions: Insights From Taking an Evolutionary Perspective](https://journals.sagepub.com/doi/10.1177/17456916231205186)
- [Mapping emotions: basic emotions versus constructivism](https://www.mindscienceacademy.org/en/mapping-emotions-basic-emotions-vs-constructivism/)
- [Seth & Critchley, Extending predictive processing to the body: Emotion as interoceptive inference](https://www.cambridge.org/core/journals/behavioral-and-brain-sciences/article/abs/extending-predictive-processing-to-the-body-emotion-as-interoceptive-inference/A53E081B5EEBD7CF7658F3D484714AFE)
- [Seth, Interoceptive inference, emotion, and the embodied self](https://www.sciencedirect.com/science/article/pii/S1364661313002118)
- [Barrett, The theory of constructed emotion: an active inference account of interoception and categorization](https://academic.oup.com/scan/article/12/1/1/2823712)
- [Active interoceptive inference and the emotional brain](https://royalsocietypublishing.org/doi/10.1098/rstb.2016.0007)
- [Affective Facial Expression Processing via Simulation: A Probabilistic Model](https://arxiv.org/pdf/1411.0582)
- [Brain-Inspired Affective Empathy Computational Model](https://pmc.ncbi.nlm.nih.gov/articles/PMC9341284/)
- [Life-inspired Interoceptive Artificial Intelligence for Autonomous and Adaptive Agents](https://arxiv.org/abs/2309.05999)
- [Interoceptive machine framework: toward interoception-inspired regulatory architectures in AI](https://www.sciencedirect.com/science/article/pii/S1571064526000461)
- [Cross Fertilizing Empathy from Brain to Machine as a Value Alignment Strategy](https://arxiv.org/pdf/2312.07579)
- [Toward Artificial Empathy for Human-Centered Design: A Framework](https://arxiv.org/pdf/2303.10583)
