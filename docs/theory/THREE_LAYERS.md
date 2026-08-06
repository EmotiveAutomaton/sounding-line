# The trimodal architecture — what a language model is failing to model, and where

**2026-08-05.** The curator's response to a literature audit that recommended abandoning Panksepp as
a premise. **He rejected the recommendation and replaced the architecture instead**, and the
replacement makes sharper predictions than the thing it replaces.

**Timing worth recording:** he stated the trimodal prediction while working through the audit, and
says he had already rejected the bimodal profile in his head *before* reaching the section reporting
that nobody else finds bimodal. Not a controlled pre-registration, but it is on the record in the
order it was said.

---

## §1. The reframe that makes everything else follow

Everything below rests on one move, and it changes what the measure is *of*:

> When I say the model leaked involuntary affect, **I'm not assigning affect to the model.** It's
> that they're **trying to predict the human brain and failing to do so.** They're trying to have
> empathy and failing.

**A language model trained on human text is an attempt to model the process that produced it.** Its
architecture is not an emotional system; it is a *reconstruction* of one, built by prediction, and it
inherits the shape of what it is reconstructing — **including where the reconstruction is bad.**

That reframing does two things at once. It removes the embarrassing implication that we are claiming
a model has feelings. And it makes the **errors** the interesting part: where the model reconstructs
human affective structure badly, that is a measurable fingerprint of the structure itself.

## §2. Three layers, and what each is trying to reconstruct

| depth | what it reconstructs | why | quality of reconstruction |
|---|---|---|---|
| **early** | **valence and arousal** — the periaqueductal-gray-like assignment | the lowest-level, most universal, most consistent thing in the training signal | **good.** Easiest to capture |
| **middle** | **Pankseppian primitives** — the ancestral, baked-in affective systems | conserved across humans, so it is *there* in the data, but it is **pre-verbal and not directly expressed** | **bad, and noisily so.** The model struggles here |
| **late** | **goal direction and proximal purpose** — attentional focusing, polish, expertise | individual to the person | **chaotic.** Not a failure to model so much as a genuinely high-variance target |

**His words on the middle, which is the load-bearing claim:**

> The middle one we wouldn't be able to converge upon... that's the part of the human brain that is
> baked in a little bit, that is a little bit more ancestral. **And it's struggling to model that.**
> So it uses valence-arousal mixed with some goal direction to get most of the way there. **But this
> is where its error comes from.**

And the consequence he draws, which is the reason this belongs in a project about alignment:

> **The lack of Panksepp is where a lot of misalignment comes from, specifically. We have to give
> emotions in order to converge upon a more appropriate goal extraction.**

## §3. What this predicts, and it is falsifiable

**a. Trimodal, not bimodal.** Three loci with two troughs, not two loci with one dead middle. Our own
result found bimodal and no one else reports it; this says both may be reading a three-part structure
with the middle one *present but noisy*, which a two-way split would smear.

**b. The middle layer is high-activity and low-coherence.** Not silent — *noisy*. That is a
specific, checkable signature and it distinguishes this from "the middle does nothing."

**c. Polish lives late; leakage lives early.** Directly testable against the surface measures we
already have. If polish measures correlate with late-layer structure and leakage measures with
early-layer structure, the mapping holds.

**d. Cognitive expertise is late.** *"Nearly everything you get out of text would be late."* With a
caveat he added himself: motor expertise may be distributed, and he cannot speak to that from text.

**e. Why models never peak in the final layer.** The brain-alignment literature finds peak alignment
at middle depth, never at the end. His account: *"they can't get through the middle layer to get to
the final layer, so their final layer just kind of randomly optimises upon the noise of the middle
layer."* **A failure of the middle propagates as noise into the top.**

**f. On Anthropic reading the early layers as lexical.** He does not dispute the finding, he disputes
the interpretation:

> They're reading the valence and arousal layers and interpreting those as lexical, because there
> **is** a casual lexical mapping through the emotion wheel we all use. But what that emotion wheel
> is really doing is defining and elaborating higher-order predictions and controls **of** valence
> and arousal.

So "early layers encode token valence" and "early layers reconstruct a valence/arousal assignment"
are the same observation under two readings, and the emotion-word vocabulary is the *interface*
between them rather than the thing itself.

**g. A layer-count prediction, offered as a guess.** That the ratio of parameters across a model's
depth may echo the ratio of neuron counts across receptor / midbrain / neocortex — because the model
is trying to reconstruct that structure under a capacity constraint. **Speculative, and he flagged it
as such**, but it is checkable.

## §4. Where this leaves Panksepp — and a correction I have to make twice

The audit recommended dropping Panksepp as a load-bearing premise. **I passed that recommendation on
as a lead conclusion. He rejected it, and he was right to:**

> This is an example of you trying to sand away a very important load-bearing column of this piece.
> **Panksepp in general may not be precise, but the idea of midbrain-localised solutions is
> absolutely load-bearing. If you drop that, we have what everyone else has, which is the wrong
> part.** You did it again, and you did it as a foundational recommendation.

**"You did it again" is accurate and it is the second instance.** The first was Bullot & Reber. Both
times the mechanism was identical: a literature return arrived in volume and confident prose, and I
adopted its framing over the project's without testing between them. `CLAUDE.md` already forbids
this. It happened anyway, in the form of a recommendation rather than a rewrite, which is harder to
notice and therefore worse.

**The claim that is load-bearing is not the taxonomy.** It is **midbrain-localised affective
primitives of some kind**. Panksepp's seven systems are the best available guess at their shape, not
a commitment to their exact number. A data-driven decomposition returning six, or eight, would be
informative rather than fatal — *"if a PCA pops out an eigth, that makes the eigth really
interesting."*

**A literature review on Panksepp versus Barrett is running**, because this is load-bearing enough
to be worth resolving properly rather than adjudicating from memory. His prior, stated plainly:
Barrett *"only has part of the picture."*

## §5. The build, if the structure is not there naturally

> If this structure is not what happens in naturally occurring language models, **I wonder if we
> could force it** — make an empathic bot with lower-order valence and arousal, medium human-mapped
> Pankseppian structures, and higher-order predictions and controls on those that are free-floating
> and subject to rapid change.

**This is the constructive version of the whole framework**, and it converts a measurement project
into an architectural one. If the middle layer is where models fail to reconstruct human affective
structure, and if that failure is where misalignment comes from, then **supplying the missing middle
is an intervention rather than an observation.**

He suspects prior art exists. The running literature review is checking.

**And a question he raised and deliberately deferred:** whether such an architecture would need
something thalamus-like to gate between the layers. Recorded, not pursued.

---

## §6. What this retires

**The revision-wobble test was a false start, and he did not propose it.**

> The problem is that revisions from a human author are always going to carry **the same level of
> intent density across the board.**

His account of what would have been interesting instead: **AI revision**, where what you notice is
the moment the model's attentional mapping shifts away from your goal and you reach out to correct
it — *"allow me to pick you up with the largest pole of the tent in my distorted policy space."* He
predicts that would produce a vague unifying effect, and declines to claim even that.

**So the null we recorded stands, but its target was mis-specified.** It tested whether human
redrafting varies the veneer. On this account human redrafting should not vary it at all, which makes
the null unsurprising rather than informative.

**And one factual correction to my own writing.** I wrote that neurons in a brain are "plausibly
natural units", offered as the disanalogy that makes interpretability unlike an electrode. He
rejected it: *"that's grandmother-cell thinking and shit's vectorized."* He is right — population
coding is the mainstream view, and the disanalogy I reached for was weaker than the ones that
actually hold, which are the absence of a privileged basis in the residual stream and the fact that
interpretability scores fail to distinguish a trained model from a randomly initialised one.


---

## §7. Corrections and additions, 2026-08-05, after he read the above

### a. Goal direction is not only late — in humans it is everywhere, and mostly middle and late

> Goal direction comes from **all three** in humans. I would say middle and late are where you get
> most of it. **In AI I genuinely have no idea.** It might be a late affectation, but hard to say.

**Flagged as needing the literature rather than a guess.** The write-up above put goal direction
squarely in the late layer; that is his claim about *models*, tentatively, and not his claim about
people.

### b. The friction he wants logged: early-as-valence/arousal does not quite fit ★

**This is the load-bearing discomfort, recorded as discomfort rather than resolved:**

> The prediction that early valence/arousal is what we're mapping — **it doesn't quite fucking
> fit.** Because the input for humans is **sensory** data. That's kind of what a model gets when it
> is boiled down into vectors, **but it's not quite the same.**
>
> When I say you can't extract emotion words from valence and arousal **directly** — you can get
> kind of close. I might be over-hedging. I'm noting there's discomfort in the mapping where I don't
> feel as confident, and **it's absolutely load-bearing.**

**The mismatch is specific.** A human's early layers receive *sensory* input and assign valence to
it. A model's early layers receive *tokens* — already symbolic, already the output of somebody else's
whole stack. If the analogy holds it must be because token embeddings function as a sensory surface,
and that is an assumption, not an observation.

**Nothing downstream should treat this as settled.** It is the weakest joint in the architecture and
he named it himself before any test did.

### c. Late may be *more* coherent when the goal is clear

> You might also have more agreement in the late, **if the goal is clear.** What you get at the end
> is my guess. And the middle — yeah, it's convergent.

So the coherence prediction is conditional rather than flat: **late coherence should scale with how
clearly the goal is specified.** On the ladder that is a directly testable interaction — coherence at
late layers against rung — and it is now part of the depth sweep's output.

### d. On the seven — he goes further than the review does

> Panksepp specifically noted he grabbed **the easiest ones**, the human-level identifiable ones. **By
> definition he missed a ton**, because the brain operates in a vector space that is hard for us to
> intuitively understand. If you told me there were 27, I would believe you. **Some of them might not
> even have names. These primitives are the key, however many there are. I don't really care how many
> there are.**

**That is a stronger position than "the taxonomy is a design vocabulary."** It predicts that a
data-driven decomposition *should* return more components than seven, and that some will be
unnameable — which makes the 24-to-28-dimension results in the emotion literature evidence *for* the
framework rather than against it.

### e. Terminology: drives, not feelings — but he yields it

> Emotions and feelings is fine. I've done **emotions and drives**. She can claim the word emotion.
> But "feeling" is probably incorrect because it implies you don't feel emotion. **Drives feels like
> a better word.** But I'll use whatever the literature has — it's not big enough a matter to give up
> the advantage of aligning with research terminology.

**Recorded because it is a deliberate concession**, not an agreement. Use *emotion / feeling* in
anything outward-facing; **drives** is the internally accurate word.

### f. The alignment weakness he names himself, and the bootstrap that answers it

> It's a weakness to the alignment consequence, because **we have to provide that weighting
> somehow.** It has to be based on... something? But at the very least it seems like all it needs is
> a **bootstrap.** You don't need a ton — a little bit would be enough to start the shape, to kick it
> off in the right direction.

**This is the strongest available answer to "whose values, and who decides."** If the mid-level
primitives only need to be *seeded* rather than *specified*, the design does not require anyone to
write down the value set — which `docs/theory/VALUES.md` §4 establishes is impossible anyway. **The
bootstrap claim and the value-blindness claim fit together**, and neither was stated with the other
in mind.

### g. Attention as expertise-weighted policy, and the example that sharpens it

> Is this attention mapping onto the policy space **weighted by your expertise as a trajectory**?

And the case he uses to test it on himself:

> If I were forced to design a Nazi camp, part of my motivation would be not dying. But part would be
> **efficiency** — I could tap a need for efficiency to do this. **But I wouldn't be able to tap into
> the cruelty a Nazi designer would have. It just wouldn't be there for me to optimise.** I'd have to
> finagle with my own motivations to get that to happen.

**The claim underneath: you can only route attention onto drives you actually have.** Two makers
producing the same artifact under the same instruction will do it from different drives, and the
drives they *lack* constrain what they can produce and how. **That makes the absent drive as
informative as the present one** — and it is a mechanism for why an artifact can be recognisably
made-under-duress. Unexplored, and it needs a name.
