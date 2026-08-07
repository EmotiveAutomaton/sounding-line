# Reading — what he actually does when he reads an artifact

**The thread that had no file.** These claims have been scattered across `CURATOR_GUESSES.md` and
`FINDINGS.md` entries since the beginning. They are one perspective and they belong together: **the
curator is the only working instrument this project has, and this is the description of it.**

Fifteen artifacts, two sessions, sixteen readings, one reader. **Those readings have outperformed
every measure we have built.**

---

## §1. The primary detector is the *variation* of the polish, not its level

> When I've been talking about the veneer in my head, I've been thinking about the imagery and
> iconography.

Not surface level — surface **change**. An opening reaching for professional register and then
relaxing out of it. **The performance is what costs something, so the performance is what slips, and
the slip is where the maker shows.**

His own scope limit: **useless on published books**, because editing sands the polish flat.

**Terminology, his correction:** *polish*, not *veneer*. And under the theory polish is just
**aesthetics**.

### Where the evidence stands, and it is negative

**Tested twice. The informative test found nothing.**

| corpus | features surviving correction |
|---|---|
| machine text, 150 artifacts | 1 and 0 — **and uninformative**, because a machine has no performance to slip |
| **human text**, 86 authors, maker/prompt/topic/register all fixed | **0 of 313 for the wobble, against 12 for the plain average** |

**That second one is the corpus the hypothesis needed and it came back empty.**

**What it does not settle.** The claim is about a performance under *cost*, and redrafting an
assignment three times may not vary the polish at all. **The honest remaining version needs artifacts
of different KINDS by one maker** — which is the same diversity-of-conditions requirement every other
thread arrives at.

### And the field got here first, on the measurement

This file previously recorded within-document variance as unclaimed ground. **That was false and it
was load-bearing.** GPTZero's *burstiness* is literally the standard deviation of per-sentence
perplexity. Koppel's *unmasking* is 22 years old. PAN has run a shared task on it since 2018, with a
topic-controlled bar of **0.830**. A 2025 study of hidden states as author representations found
**document-level mean pooling best**, which is evidence against the variance idea at the
representation level too.

**What is not pre-empted:** within-artifact variance of **probe activations** rather than of
perplexity or surface style. Nobody found doing that.

**His reading of what the field is measuring, and it is a claim not a complaint:**

> It's not burstiness. It's not unmasking. **It is goal variation** — all of them varying in relative
> strength as you express yourself. People aren't seeing it for what it is.

**One distinction I collapsed and he separated:** intrinsic plagiarism detection finds *a different
author spliced in*. That is **not** one author's goals shifting across their own piece.

## §2. Reading enters at an anomaly, never at the artifact

> The thing that most jumps out at me isn't mistakes but **unusual constructions, or odd decisions
> that I can't find an explanation for.**

Then it runs purpose→method **and** method→purpose, with the entry point set by wherever he has
partial expertise.

**His own discomfort, recorded because he raised it:** *"I hate that a lot of this is me picking out
mistakes and typos, which is also a trick for AI and it's not okay. But it is a way of extracting
decisions."*

**Status: never tested.** `bounded_v6` has a stage zero for it; it is locked, opt-in, and has never
been the live path. **The test is a prompt variant, not new machinery** — does entering at the anomaly
beat entering at the whole artifact, on the same artifacts? One of the cheapest untried things here.

**And the mechanism, which connects this to §5:** a **mistake** is an anomaly with a *known cause*, so
the maker's response to it is a decision with its alternatives visible. *"The importance of the
mistake — the mistake, and the way the author can be presumed to have responded to it, is one of the
more useful pieces of information once you have observed it."*

## §3. Confidence in a maker moves while reading

> It starts questionable... 8 or 9 by the end.

**The trajectory carries what the endpoint does not.** Every reading this project records is a final
number. **Status: never tested**, and the fix is to score windows sequentially and keep the series.

**Related to §1 by more than coincidence** — both say the within-artifact *series* is where the
information is, and we have only ever kept means.

## §4. Depth is a property of the writer **with respect to the domain**

> It does not vary within an artifact unless the domain does.

**This is the sharpest definition in the project**, because it makes depth a **relation** rather than
an attribute — and it arrived with its own falsifier attached: *depth moves where domain moves.*

**Why it matters more than it looks.** `FINDINGS.md` concludes the binding constraint is that we have
never had a controlled human corpus. **This says why that is fatal rather than inconvenient: a
relation cannot be measured by varying one side.** Every measure that has died, died reading artifacts
alone.

**The test is directly runnable and has never been run** — artifacts by one maker spanning two
domains, one where they are expert and one where they are not.

## §5. Process is hierarchical, and you can enter the decode at any level

> Walking up to an unknown oil painting, you can engage with it on the level of **metaphor** — why did
> the author craft what they did. On the level of **technique**, like perspective. On the level of
> **mechanics** — how did they move their hand as they painted.
>
> **You can use any piece of knowledge about any of those three channels to begin the decoding.**

**Vocabulary decision: mechanics / technique / metaphor stands.** Panofsky was the wrong citation and
he rejected it correctly — those levels are about *what an image depicts*, not *how a thing was made*.
**Dennett's three stances is the right citation and not the terminology**; Marr, Newell and Pylyshyn
land independently on the same three-level structure, which is a result about the shape of the problem
rather than a coincidence of naming.

One caveat worth holding: **"metaphor" is narrower than the top layer needs** — the intentional stance
covers *purpose*, not only *meaning*, and this project's top layer has to carry goal.

**Still open, and he flagged it:** whether the layers are really three or arbitrarily subdividable.
Nobody in that convergence argues three is forced; they argue three is *useful*.

### This is where we collide with the literature, and the collision is the contribution

**Bullot & Reber assert a strict ordering** — the design stance is *"requisite for"* artistic
understanding. **That directly contradicts enter-at-any-layer-and-ratchet**, and the open peer
commentary attacked precisely the relations among their modes.

**And their framework is weakly supported.** Chmiel & Schubert tested its core prediction across 34
experiments in 23 publications: **26% support, 18% inconclusive, 56% no support.** An occupied lot
with a shaky building on it.

**The formal match we have never looked at is Rasmussen's abstraction hierarchy** — five levels with
explicit means-ends links, built for diagnosis **from any level**, forty years of use.

**The test, and it is the missing direction in the whole edge programme:** supply **mechanics-level**
information — cadence, clause habits, punctuation practice — rather than a stated purpose, and measure
goal recovery. **Every edge tested so far has supplied a goal or a process. None has ever supplied a
mechanic.**

## §6. Interest is unexplained decisions — which makes the reader an instrument

> Interest comes from finding decisions that you can't attribute meaning to, which implies there's
> more meaning you don't fully understand — either a **process** you aren't aware of, or an **extra
> motivation** you aren't aware of.
>
> **Artfulness is making a lot of unexplained decisions. Aesthetics is the appearance of having made
> unexplained decisions but for a reason, in an ordered sense.**

**This connects §2's anomaly-entry to a mechanism.** And it makes *interest* a proxy for
**unrecovered decisions**, which is the quantity this whole project is trying to measure.

> **If interest is what a reader feels when decisions are present but unattributed, then
> reader-reported interest is an instrument — and it is one we can ask a human for directly.**

**Interest ratings on his fifteen read artifacts are owed and would be the cheapest real test here.**

**A correction that matters, because I got it wrong once.** I offered **Berlyne's collative
variables** as live support. Reading the source rather than the snippet: *"Berlyne's arousal theory of
aesthetic appreciation has been mostly abandoned"* on mixed empirical results. **The vocabulary
survives; the mechanism does not, and this claim should not lean on it.** The live descendants are the
processing-fluency accounts, which sit at the *opposite* pole — pleasure from ease. That tension is
the field's live debate.

**His "ordered but unexplained" is close to effective complexity** — structure that is neither random
nor trivially regular. That is a real, formalisable quantity and it is the better formal target.

**And his own open question, which E4 arguably answers:** is there anything in art theory separating
aesthetics that *indicate* deeper understanding from **performative** aesthetics? Under §6,
performative polish would be **ordered without being unexplained.**

## §7. Aesthetics was the cheat, and AI broke it

> Aesthetics is one of the **easiest goals to judge**, because it is literally surface polish — you
> can explicitly judge whether the maker succeeded, and implicitly judge the value of what you are
> seeing by **how much you want to look at it. It is a self-referring goal and you can cheat it pretty
> easily.**
>
> **It's also the piece that's misfiring on AI specifically. Previously it correlated with effort very
> highly. Now it does not. That's what's breaking.**

**The sharpest available account of why generated text unsettles readers**, and it is directly
testable: **the polish–effort correlation should be strong in human corpora and near zero in generated
ones.** Corpora we already hold. Never run.

**It also reframes the effort heuristic.** People rate identical artifacts higher when told more
effort went in, more so when quality is ambiguous. The literature audit offered that as an adversarial
reading of depth — a bias in the reader. **On his account it is not a bias. It is a normally-valid
inference that a new kind of artifact has broken.**

---

## What this file says to do next

**Three of these are cheap and none has been run:**

1. **Entering at the anomaly** (§2) — a prompt variant.
2. **Depth across two domains by one maker** (§4) — the falsifier for the sharpest definition here.
3. **Polish against effort, human versus generated** (§7) — corpora already held.

And one that costs an hour of his time and would be worth more than any of them: **interest ratings**
(§6), because reader-reported interest is the only instrument in this project that has ever beaten the
measures.
