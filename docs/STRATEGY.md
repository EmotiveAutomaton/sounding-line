# Lay of the land, after re-reading the theory

Written 2026-08-03 after going back through `docs/theory/Art_a_unifying_model.md` and the V6
results. Three things changed, one of them large.

---

## §1. The correction I owe on "post-hoc"

The curator is right and I was wrong to label the unlock measure post-hoc.

E36 is not a pattern found in data. It is a **derivation from the model** — depth is *constructed*
so that purpose is equally readable at every level, therefore purpose cannot move with intent
density, therefore the effect must live in method. That derivation exists independently of any
result, in a different codebase, before this project began.

**Testing a theory's prediction is not post-hoc analysis, whatever prompted you to get round to
it.** The honest residual is narrow: *which* theory-prediction I chose to test was prompted by a
failure. Since the theory has few predictions and this is a central one, that residual is small.
The `EXPLORATORY` label stays on the *sample size*, which is genuinely inadequate, and comes off
the *provenance*, which was fine.

---

## §2. CORRECTED — compression hides decisions from the MAKER, not from the reader

> **Correction, 2026-08-03, from the curator.** The section below originally argued that expertise
> compresses decisions out of the artifact, so expert work shows fewer visible decisions. **That is
> wrong, and the sentence I built it on says so if quoted in full.**
>
> E43: *"Practice compresses decisions, and compression is what makes a decision unavailable for
> report — **while the reader is unaffected.**"* I quoted the first half. The dropped clause states
> that compression affects the maker's self-report, not the reader's recovery.
>
> E33 confirms it from the other side: *a reader can know a maker better than the maker knows
> themselves, and the margin grows as the maker's self-account degrades.* That is the curator's
> "reading your own books teaches you about yourself" — the artifact keeps the decisions; the maker
> loses the report.
>
> **The theory's actual explanation is line 233:** *"It is the language of expertise that unlocks
> the ability to observe the hierarchies of decisions in others."* The decisions are all present in
> the artifact. The READER needs matching expertise to see them. That is E10 and E38, already
> established, and not a new mechanism.
>
> **Consequence for unlock:** it does not measure decompression of the artifact. It measures how
> much the reader's own decoder improves once the goal is pinned — E36's "intent is the key; the
> method is what it opens." The measure survives; the explanation I gave for it did not.
>
> Also tried and recorded as not working: holding the process constant to infer the goal. E36's
> between-reader test failed at 0.047 against a required 0.15 — method is legible *given* purpose,
> and purpose is not recoverable *given* method. The dependency is one-way.

### The original argument, retained as an error record

This is the one that reframes everything, and it is stated plainly in the essay.

> **Expertise just means having made lots of similar decisions yourself** — building out your own
> hierarchy of action through automaticity. *(line 233)*

> These layers add such a compression of decisions to every moment that the child, who has built up
> no automaticity, cannot match the density of artfulness... **baked-in hierarchical compression.
> Decisions are counted individually, including subordinate and previously addressed solutions.**
> *(lines 87–89)*

> **Simplicity without a dense underlying decision tree is just empty data; simplicity born from
> extreme compression is a masterpiece.** *(line 204)*

And the simulation measured the consequence, in E43:

> Does the maker lose access to their own reasons as the work deepens? **Yes.** Practice compresses
> decisions, and **compression is what makes a decision unavailable for report.**

**So high expertise produces MORE total decisions and FEWER visible ones.** Automaticity is
compression; compression is what removes a decision from the surface.

**The instrument counts visible decisions. The theory says visibility is inversely related to
expertise.** That is not a bug in a measure — it is the measure being pointed at the reciprocal of
its target, and it explains Gate 2's reversal exactly:

| artifact | expertise | visible alternatives | what the theory predicts |
|---|---|---|---|
| LocalThunk building his own game | very high | **0.00** | compressed away |
| plumber service-area template | none | **0.67** | nothing compressed; genre moves obvious |

It also explains the curator's own template observation (C-13). A template *is* compressed prior
decisions — made once, elsewhere, reused. The curator noticed the phenomenon in the wild before the
instrument did.

**And it explains why unlock works.** Unlock measures how much *more* becomes visible once the
purpose is supplied. That is **decompression**. A deep hierarchy needs the key to unpack; a flat
artifact has nothing to unpack and unlocks at ~1.0 or below. Unlock is not a lucky proxy — it is
the theoretically correct construct, and decision-counting never was.

---

## §3. Sample size — the actual numbers

From the Gate 2 unlock run:

| group | n | mean | sd |
|---|---|---|---|
| row 2 real makers | 4 | 1.283 | 0.512 |
| row 3 commercial filler | 3 | 0.917 | 0.220 |

Pooled sd **0.420**, effect **0.367**, **Cohen's d = 0.87** — a large effect, measured on seven
artifacts.

| power | n per group | total artifacts |
|---|---|---|
| 80% | **21** | **42** |
| 90% | **28** | **56** |

**42 artifacts settles it at conventional power.** That is a sourcing problem, not a curation
problem, and sourcing is mine.

Two levers would cut the requirement further, and both are free:

- **Raise k.** Per-artifact unlock at k=3 carries real sampling noise; k=7 would shrink
  within-artifact variance and therefore the pooled sd.
- **Exclude or separate the trivially-1.0 cases.** Where the posterior settles on the first pass,
  before and after use the same purpose and unlock is 1.0 by construction. Those artifacts are
  noise in the comparison, not signal.

---

## §4. What the curator actually needs to do

**Not read 42 artifacts.** The calibration passes already did their job: they found the missing
dimension (`effort`), split it in two, caught the surface-marker confound, and produced the
template observation. That work is done.

What is worth their time is **a much smaller, targeted read**: 8–10 artifacts chosen to span the
unlock range — a few the instrument scores high, a few low, a few at exactly 1.0 — read blind, to
check whether a human agrees with the instrument *where the instrument is confident*. That is an
hour, not a day, and it tests the thing that matters: whether unlock tracks something a person
recognises.

Everything else — sourcing 42 artifacts, running them, scoring them — is mine.

---

## §5. The plan

1. **Source ~45 artifacts**, ~21 per row, honouring robots.txt. The seven blocked at Gate 2 are
   permanently unavailable, so this needs breadth: personal blogs, technical postmortems, forum
   long-posts, craft writing for row 2; template local-service pages, brand content marketing,
   affiliate listicles, aggregator pages for row 3.
2. **Pre-register Gate 3** with unlock as the primary discriminator, a stated threshold, a stated
   null, and the trivially-1.0 handling decided *before* the run.
3. **Run local at k=5**, all artifacts, both arms.
4. **Curator reads 8–10 blind** to check the instrument against a human where it is confident.
5. **API arm once**, as the pre-registered replication, only if step 3 separates.

---

## §6. The honest position

Gate 2's verdict stands: the falsifiers failed on purpose-based measures.

What has changed is that **the failure is now explained by the theory rather than in spite of
it.** Three independent mechanisms — E36 (purpose is flat by construction), E38 (a machine-matched
reader loses human work), and compression-hides-expertise — all predict the exact failure observed,
and all three were established before this project ran a line of code.

That is not a rescue. It is the difference between *"the instrument does not work"* and *"the
instrument was built against three documented findings in its own foundation."* The second is
fixable and the fix is specified. The first would not be.

**The construct has still never been tested at adequate power on the right quantity.** Forty-two
artifacts and a pre-registration would be the first time.
