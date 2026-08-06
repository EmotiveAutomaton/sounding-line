# The central disagreement — and the theory the literature audit did not sand off

**2026-08-05.** Written immediately after a literature audit found four of five core claims
substantially occupied. **Read this before engaging any external research.** It is the deliberate
counterweight: the framework arrives in dictated fragments while the literature arrives in confident
volume, and without a refresh the volume wins.

The curator's own diagnosis of the risk, and it is why this file exists:

> If you replace what I said outright with these citations, you replace my mapping in your own head.
> **This is one of the mechanisms through which AI sands down the process.**

---

## §1. The impossibility proofs assume unconstrained inference. Humans are not unconstrained. ★

Armstrong & Mindermann prove a policy cannot be uniquely decomposed into planner and reward, and
that this *"cannot be resolved by observing the agent's policy in enough environments."* The audit
reported this as fatal to the values programme. **It is not, and the counter-argument attacks the
premise rather than the proof.**

> Saying something isn't possible just means you haven't found the way to do it yet — **especially
> if the world is doing it. Humans do this. Therefore it must be able to be done.** The way that
> you're doing it is incorrect.

> **"Irrational agents" is incorrect about humans.** In a lot of ways we are *boundedly
> hyper-rational.* **It looks like irrationality to have fractal motivations.**

> The problem they are running into is an **inability to disassemble expertise from exploratory
> behaviour.**

### The decisive move: his three assumptions are exactly the three the proofs require

Single-episode goal inference works in cognitive science only given a bounded hypothesis space, a
known transition model, and an assumed rationality principle. The audit reported that none of the
three transfers to artifacts. **They do — they are already in this framework under different names.**

| what the proof needs | what he already assumes | his name for it |
|---|---|---|
| a bounded hypothesis space | **human-shaped goals** | convergent midbrains |
| a known transition model | **expertise** | *"the transition model is just expertise"* |
| a rationality / optimality principle | **near-optimality** | *"that's just MaxEnt"* |

> *"Oh my god, it's my three assumptions."*

**And the second identification is the one to build on:** *"the maker's competence is their
expertise."*

> **The two unknowns Armstrong & Mindermann prove are fatal are the same quantity in this framework
> — and it is a quantity we already claim is recoverable.** It is the technique layer.

**This is the project's central disagreement with the literature. It is not a hedge and it is not to
be narrowed.** Two impossibility results — archaeological *equifinality* and IRL *partial
identifiability* — are the same problem, and this is the same answer to both.

**The honest form of the claim:** the theorems hold. What is contested is that their conditions
describe a human reading a human artifact. That is an empirical question, not a mathematical one.

## §2. Emotion is a vertex humans enter through, and nobody is using it

> Humans cheat by having **convergent midbrains** that let us converge on similar views. **Emotion is
> going to be one of the common vertices people use to enter this equation**, and I don't feel like
> people are addressing that directly.

> **Panksepp is right, full stop.** Because he's right, that has to be reflected in human behaviour
> and thus in optimal expression of human activity.

**This is the answer to "0% prompt recovery from sampled text alone."** That result assumes no prior
over the emitter. A human reading a human has a very strong one — a shared affective architecture —
and that is the bootstrap. *"It's the human-shaped piece that's going to be the magic. I just
explicitly mean the weightings in our midbrain."*

**Consequence:** the low-order/high-order affective ratio is not one measure among many. It is the
operationalisation of the shared-prior bootstrap, which is a reason it keeps surviving controls that
kill everything else.

## §3. Re-reading recovers the tail of the distribution

> A human could study a single bit of text and extract **more and more goals from it over time**, in
> a layer of **decreasing confidence with increasing information**. That is what we do — literature
> studies exist for this. People reread the same book over and over for this purpose.

Against the finding that prompt information survives in the model's **distribution tails** rather
than in sampled text: **that is exactly what re-reading recovers.** Deep analysis adds *texture* to a
maker's motivations, and texture is the tail.

**Testable:** does repeated probing of one artifact, accumulating low-confidence attributions,
converge on something stable — and does that stable thing match what many artifacts by the same maker
give you? If so, **depth of reading substitutes partially for breadth of corpus**, which is a direct
answer to the diversity-of-conditions requirement.

## §4. The architecture, named

> Attention directs toward **policy space**. You use the **trajectory mapping — which is our
> expertise** — layered over a **weighted policy map, which is our outcomes**. From that we get our
> actions.

    expertise (trajectories)  ×  weighted policy map (values)  →  actions
    a goal = attention amplifying part of the policy map

First version of the framework that names what each layer **is** rather than what it does. He flags
it lands next to Friston.

## §5. Everything is an artifact, including biography ★

Bullot & Reber say appreciators process *causal and historical information about the artwork's
making*. He extends it further than they do:

> **Everything's an artifact. Even information about their life.** Any action they took that affected
> the world counts. Even if the curator is providing additional stimuli about the artist in addition
> to the painting in front of you, **it is indistinguishable.** You will use **epistemic foraging** to
> find more things out about the artist if you want to.

**This dissolves the artifact/context distinction.** Learning about the artist is not *context* for
the work — it is **more trajectories from the same maker**, which is exactly what §1's
diversity-of-conditions requirement asks for. The two claims meet here, and it means biographical
material is not a confound to be controlled but data to be included.

It also disposes of the "the person is not there" objection: *"you're responding to their sound waves
and it's the same maths."*

## §6. Aesthetics is the cheat, and AI broke it ★

> Aesthetics is one of the **easiest goals to judge**, because it is literally surface polish — so
> you can explicitly judge whether the maker succeeded at it, and implicitly the value of what you
> are seeing by **how much you want to look at it. It is a self-referring goal and you can cheat it
> pretty easily.**
>
> **It's also the piece that's misfiring on AI specifically. Previously it correlated with effort
> very highly. Now it does not. That's what's breaking.**

The sharpest available account of why generated text unsettles readers, and it is directly testable:
**the polish–effort correlation should be strong in human corpora and near zero in generated ones.**

Note this also reframes the effort heuristic (people rate identical artifacts higher when told more
effort went in, more so when quality is ambiguous). The audit offered it as an adversarial reading of
depth — a bias in the reader. **On this account it is not a bias, it is a normally-valid inference
that a new kind of artifact has broken.**

## §7. Burstiness and unmasking are goal variation, seen without the theory

> I'm not surprised that variation in surface polish is the main way people detect AI. **It's not
> burstiness. It's not unmasking. It is goal variation** — all of them varying in relative strength
> as you express yourself. People aren't seeing it for what it is.

**And a distinction I conflated and he separated:** intrinsic plagiarism detection finds *a different
author spliced in*. That is **not** one author's goals shifting across their own piece. The prior art
is less pre-emptive than the audit implied, and the two should not have been merged.

**A prediction he made before seeing the result:** constraints in a prompt swing machine-detector
accuracy **because constraints make the text look more human** — humans have diversity of motives.
The published paper presents this as instruction-following instability. On this account it is the
theory's prediction, and he called the direction unprompted.

## §8. Mistakes, and how the maker answered them

> One of the more interesting bits in art literature is **the importance of the mistake** — the
> mistake, and the way the author can be presumed to have responded to it, is one of the more useful
> pieces of information once you have observed it.

Connects to reading-enters-at-an-anomaly. **A mistake is an anomaly with a known cause**, so the
maker's response to it is a decision with its alternatives visible. Unexplored here.

## §9. Where the accumulated human tricks are kept

> Archaeology and the **Morellian method** will intrinsically have all of the thousand little tricks
> humans have learned to get better at this specific skill. **We need a high-resolution look at the
> vertices they enter at, and we need to recreate those in our data.**

Intent extraction **is a skill** — trainable, improvable, degradable — so meta-skills have congealed
around it in the disciplines that practise it hardest. **This is a different literature target from
the audit's:** not "who claimed this" but **"what do practitioners actually do."**

## §10. Predict, not identify — as a limit, not a concession

Dennett's intentional stance licenses prediction, not identification. That was offered as a mismatch
with an instrument whose output is "the maker's actual goal."

> **It's a question of limit.** We're doing a Taylor series approximation — increasing precision
> based on Bayesian updating. Eventually, hypothetically, the only way to do it fully would be to
> **hold someone else entirely in your mind.**

Identification is **the limit of prediction under accumulating evidence**, not a different act. That
is a statable position in the intentionalism debate and it answers Wimsatt & Beardsley without
conceding to them.

---

## What to do with a literature collision

The pattern across three audits, and it is not discouraging:

> Other people have **fragments** of this framework, and each misinterprets its fragment slightly
> because they do not have the rest of it. Being able to **predict another group's results while
> disagreeing with their interpretation** is the signature of holding a piece of the puzzle they do
> not.

So when a collision is found: **record it, state the difference, and keep the framework's version as
the working one.** The difference is usually the contribution. It is never a reason to retreat to the
narrow claim that survives someone else's theorem.
