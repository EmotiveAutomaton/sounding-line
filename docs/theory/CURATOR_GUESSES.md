# The curator's active guesses — extracted, separated from my analysis

**2026-08-05, at his instruction:**

> There's a lot of things that *you* think in there, and I specifically need to extract the things
> that *I* think that were added in — like the triangle, surface and depth guesses. Those are active
> guesses that haven't been properly addressed.

He also named why this file exists, which is a claim in its own right:

> One of the solutions to *"you fall into paths people have explored already"* is literally to write
> theory documents and then have you over-index on them.

**So this is both an index of open claims and a deliberate counterweight to the "Artificial
Hivemind" effect** — the documented tendency of language models toward intramodel repetition and
clustering around seed literature. If the seed literature is *his*, the clustering works for us.

---

## How to read this file

Every entry is **his claim, in his words where possible**, then its status, then **what would
actually test it**. My interpretation is confined to the last column, and where I have previously
been wrong about one of these it says so.

**Status vocabulary**

| | |
|---|---|
| **UNTESTED** | no instrument has ever been pointed at it |
| **INSTRUMENT DEAD** | tested, but what died was our measure, not the idea |
| **PARTLY** | evidence exists and is incomplete |
| **REFRAMED** | tested, and the result changed the shape of the claim |

---

## A · The frame

### A1 · Empathy is three coupled variational inference problems — **REFRAMED**

> Empathy is effectively a variational inference problem — **three separate variational inference
> problems being solved in parallel, and each one bootstraps the others.** The proximal goal, the
> process, the values/drives. **And I don't know if drives are values.**

**What happened.** Sim T-1 tested it interventionally. It is **not a triangle**: three of six edges
are exactly zero, goal is a *sink* already at ceiling (1.000), process is the *source* (+0.840 to
depth), and the edges are **additive, not superadditive** — so "bootstrapping" is not what was
measured.

**But his two directional predictions, recorded before the run, both held**: goal easiest to recover,
process most useful when supplied.

**And his own open question is still open.** The values vertex **does not exist** in the model:
H(values | goal) = 0, a deterministic coarsening. The simulation refused to invent one, which was
correct. *Are drives values?* has not been asked, because nothing yet can ask it.

**What would test it:** a model with a values factor that is not a coarsening of goal. That is a
build, not a run, and nobody has scoped it.

### A2 · Depth is a property of the writer **with respect to the domain** — **UNTESTED**

> It does not vary within an artifact unless the domain does.

**This is the sharpest definition of depth in the project**, because it makes depth a **relation**
rather than an attribute — and it came with its own falsifier attached: *depth moves where domain
moves.*

**Why it matters more than it looks.** `FINDINGS.md` concludes the binding constraint is that we have
never had a controlled human corpus. **A2 says why that is fatal rather than inconvenient**: a
relation cannot be measured by varying one side. Every measure that has died, died reading artifacts
alone.

**What would test it:** artifacts by one maker spanning two domains, one where they are expert and
one where they are not. The falsifier is directly runnable and has never been run.

### A3 · Surface and depth are two decision densities, split by what the decision targets — **PARTLY**

> Surface thickness kind of stayed the same throughout, I feel like.

**Evidence in favour, from the side:** sim S-6 found practised surface decays **6.5× faster** than
depth, and synthetic surface is **flat**. That is consistent but it is a simulation result about a
constructed emitter, not a measurement of the split on text.

**What would test it:** the two densities separated on real artifacts, which requires a measure for
each, and we have neither.

---

## B · His detectors — what he actually uses when reading

### B1 · The **variation** of the veneer — **UNTESTED. This is the big one.**

> When I've been talking about the veneer in my head, I've been thinking about the imagery and
> iconography.

Not surface *level* — surface **change**. An opening reaching for professional register and then
relaxing out of it. **The performance is what costs something, so the performance is what slips, and
the slip is where the maker shows.**

Scope limit he attached himself: *useless on published books, because editing sands the veneer flat.*

**Status: this is his primary detector and no instrument has ever been pointed at it.** That is,
flatly, the largest unexploited item in the project. Ten measures were built and not one of them
measured within-artifact variance of anything.

**What would test it:** any measure computed per-window, then its **variance across windows within an
artifact** rather than its mean. That is a one-line change to every measure we already have, and the
342 new features make it 342 candidates. **It has never been tried.**

> Note the collision worth checking: Gate 3's N13 failed because within-artifact sd was **0.808**
> against a between-half signal of **0.087**. We recorded that as instability. **B1 says it might have
> been the signal.**

### B2 · Reading enters at an **anomaly**, not at the artifact — **UNTESTED**

> The thing that most jumps out at me isn't mistakes but **unusual constructions, or odd decisions
> that I can't find an explanation for.**

And then it runs purpose→method **and** method→purpose. Entry point set by wherever he has partial
expertise. `bounded_v6` has a stage zero for this; it is locked and opt-in and has never been the
live path.

He also flagged his own discomfort: *"I hate that a lot of this is me picking out mistakes and typos,
which is also a trick for AI and it's not okay. But it is a way of extracting decisions."*

**What would test it:** does entering at the anomaly beat entering at the whole artifact, on the same
artifacts? A prompt variant, not new machinery.

### B3 · Confidence in a maker **moves while reading** — **UNTESTED**

> It starts questionable... 8 or 9 by the end.

**The trajectory carries what the endpoint does not.** Every reading we record is a final number.

**What would test it:** score windows sequentially and keep the trajectory. Related to B1 — both say
the *within-artifact* series is where the information is, and we have only ever kept means.

---

## C · Mechanism guesses

### C1 · Relative goal diversity — soul is a **variety of motivations** — **INSTRUMENT DEAD**

> When we talk about something having **soul**, what that means is a variety of motivations. And it
> tends to travel with expertise — because as processes are baked in with automaticity, you lose
> conscious access to them and **they start to be tied more to your drives.**

**What died was `purpose_breadth`, not the idea.** Sim T-2 showed posterior entropy tracks
**difficulty**, and at matched difficulty the excess from diversity is −0.013 to −0.025. The
simulation stated explicitly it **cannot** test whether practice *causes* drive-multiplicity.

**What would test it:** any measure of motivational variety that survives a **difficulty control**.
Neither of the two tried so far would have. This supplies the mechanism the framework otherwise
lacks, so it is worth a second instrument.

### C2 · Dense aesthetics **conceal** poor motivation beneath — **UNTESTED**

> I do think the density of decision-making is by necessity a little bit thinner on corporate art.
> **Aesthetics that are so dense that they're intended to conceal the poor motivation beneath it. A
> particularly dense top layer.**

**Never tested, and it is directly checkable.** It predicts a specific *inversion*: high surface
density with low depth density, concentrated in commercial work.

**And there is already a number pointing at it.** C3 found half B (commercial copy) sits **26% of the
way** from essays toward machine text. We read that as a register confound. **C2 says it may be the
phenomenon.**

**What would test it:** surface-density and depth-density measured separately on the same artifacts,
with commercial work as the predicted-inversion arm. Blocked on A3.

### C3 · The mechanistic-interpretability angle — **PARTLY, and half of it is dead**

> They have Panksepp's lower-order features near their sensory input channels and Barrett's emotional
> prediction in cortical networks further away... **human text should trigger MORE low-order
> affective activation relative to high-order.**

**Ruled out** as a human/machine discriminator: the gap keeps 99% of itself under sentence-shuffling
and tracks register (C3 control, p = 0.0033).

**Still open** on the ladder, where register is fixed by construction: rho = −0.275, **p = 0.0529**,
and it is the only order-dependent effect in the project. `corpora/ladder2/` is the held-out
replication, generating now.

### C4 · Leaked vs emblematic affect, and **the shield matches the leak** — **PARTLY**

> Leaked greater than emblematic doesn't even count as concealment. **The shield matches the leak** —
> the display gets *louder*.

I had this backwards and he corrected it. **Sim S-3 confirmed his direction**: amplifying the shield
makes concealment *more* detectable, not less. T-4 shrank the effect to a third of its advertised
size (S-3's threshold was fitted on labelled data) but the **direction held**, and it survives a
reader that is wrong about almost everything — including a 50% channel swap.

**The narrow part:** it fails at **25% concealment**. It detects heavy concealers only.

### C5 · LUST belongs in the list, because it shows in what an artifact **justifies** — **UNTESTED**

I dropped it, reproducing ANPS's convention. He overruled, and the reason is better than the
convention: **ANPS drops LUST because a questionnaire cannot reach it. An artifact has no such
limit.** Signature he gave: *the thing a reader politely glosses over — attention dwelling past what
the argument needs.*

**What would test it:** attention-dwell as a measurable quantity. Nothing built.

### C6 · Showing someone your writing is a kind of **intimacy** — **UNTESTED**

> If you know the person better, you can extract their proximal goal and their process more easily.

This is the values vertex acting as a **prior held before the artifact is seen**, rather than as
something recovered from it. Blocked on A1 — the vertex does not exist yet.

---

## D · Method claims he has made, and their track record

**He is 5 for 5 on methodology.** Recorded because it is decision-relevant: when he pushes back on a
method, the prior should be that he is right.

| | claim | outcome |
|---|---|---|
| **D1** | censor dates — a cue must *dominate*, symmetry is the wrong test | **right.** I argued and was wrong |
| **D2** | the rich-arm prompt leaks instruction-following | **right.** It said "name three things you decided NOT to cover" |
| **D3** | option D is not "years" | **right.** 2–3 days; pymdp was already installed next door |
| **D4** | the shuffle test is not correct | **right**, and worse than he guessed — it perturbs ~3× the signal |
| **D5** | near-significance means raise the power, not report a failure | **adopted as standing policy.** `corpora/ladder2/` |

### D6 · Stack the weak effects into a detector — **UNTESTED, with a warning**

Open. The warning is in `FINDINGS.md`: stacking effects that share a confound produces a **strong
confound**, and the AI-detection literature says a stylometric stack reaches **F1 ≈ 0.99** — so the
likely outcome is rediscovering a machine detector. **The ladder is the only thing that tells the
difference**, because a machine detector must see all five rungs as identical.

---

## What this file says to do next

Reading the statuses rather than the arguments, three things stand out and **none of them is
expensive**:

1. **B1 — within-artifact variance.** His primary detector, never measured, and a one-line change to
   every measure we own. With 342 new features that is 342 candidates, and Gate 3's "instability" may
   have been it all along.
2. **A2 — depth as a relation.** Its falsifier is directly runnable and would tell us whether the
   corpus problem is fatal or merely inconvenient.
3. **C2 — dense surface concealing thin depth.** Never tested, and C3's commercial-copy number is
   already sitting there pointing at it.
