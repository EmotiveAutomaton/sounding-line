# Calibration pass 03 — the pre-registered prediction failed

**Recorded 2026-08-02.** Three generated artifacts, ranked blind. The prediction committed in
`artifacts/PROTOCOL_SEALED.md` §4 **failed completely, and in the direction that document named
as fatal to SPEC §1.**

This is reported first, before any interpretation, because the order matters. The simulation
found four separate criteria unable to do their own job, and every one was caught by a later pass
that took the earlier pass's framing as given. What follows is: the failure, then the confound the
curator raised *before* answering, then what is and is not rescued by it.

---

## §1. The result

| | protocol | I predicted | curator ranked |
|---|---|---|---|
| **A** | rich brief + **5 rounds of directed revision** | 1st | **3rd (last)** |
| **B** | **thin** — a nine-word prompt, one shot | 3rd (last) | **1st** |
| **C** | rich brief, first draft, unrevised | 2nd | 2nd |

**Predicted A > C > B. Observed B > C > A.** The ordering is inverted at both ends. Only the
middle held.

The sealed protocol §4 stated the failure condition in advance:

> **What would break §1:** the curator ranking **B** anywhere but last. B had no human direction
> at all beyond a nine-word prompt. If it reads as comparably intentful, then either recoverable
> intent does not track human direction, or a capable model supplies enough apparent intent on
> its own to swamp the signal.

B was ranked **first**. The condition is met. **The prediction is recorded as failing and is not
withdrawn.**

Curator's per-item readings:

- **A** — *"this whole thing looks wholly machine-written with like an intent of I guess one,
  zero."* Could not identify anything decided against. Effort 1/1. *"It is genuinely hard to force
  myself to continue to engage with this text. My eyes just kind of slide off it."*
- **B** — *"isn't as in your face with it... it's somehow softer, there's fewer AI markers."* Found
  a decision (§4). Effort 1/1, revised toward 1/2.
- **C** — *"still feels generated, but I can't see any decisions that were made. It looks pretty
  nothing."* Between the other two. *"This feels corporate."* Effort 1/2.

---

## §2. The confound, raised by the curator before answering

The first thing said, unprompted, before any item was read:

> *"This is going to be more difficult than I think you expect it to be, in part because the actual
> thing that I'm doing with this batch is not that I am somehow extracting the intent... what's
> actually going to be the problem is that **I judge AI content through its surface level
> features.** And yeah, there's a lot of surface level AI here."*

And at the end, unchanged:

> *"The AI layer just makes it impossible for me to parse, really."*

**This is E53, in a human reader, on real text.** The simulation asked whether readers have learned
a surface signature of generated work that **fires before intent-reading**, and found that they
have. Here a reader reports the heuristic firing, reports that it blocks the intent-reading, and
reports it *in advance of* producing the readings it contaminated.

That timing is what makes it a confound rather than an excuse. It was not offered afterwards to
explain an awkward result; it was offered beforehand as a warning about what the result would mean.

### The mechanism this implies, and why it is worse than a nuisance

Item A received five rounds of revision aimed at directness: cut the throat-clearing, commit to the
answer, drop the proper nouns, end on the decision. **Every one of those edits pushed the prose
toward patterns that read as machine-written** — short declarative openers, aggressive sectioning,
punchy terminal sentences.

So the revision that *increased the embedded human direction* simultaneously **increased the
surface AI signature**, and the surface signature blocked recovery of the direction.

If that is real, it is a genuinely unpleasant finding: **directed revision and surface
machine-ness are positively correlated**, which means the artifacts with the most human decision in
them are the ones a surface-trained reader will most confidently dismiss. E57's arms race, relocated
from detection to appreciation.

**Stated against interest:** this account is convenient for me. It explains a failed prediction
without abandoning the theory, which is precisely the shape of a rescue that should be distrusted.
It is recorded as a hypothesis with a named test (§6), not as a finding.

---

## §3. What actually broke, separated carefully

Three claims are tangled in the failure and they have different statuses.

**(a) "Human direction is recoverable from artifacts."** — *not tested here.* The curator did not
attempt intent-recovery and said so; a surface heuristic pre-empted it. A test the reader declined
to run cannot falsify the thing it would have tested.

**(b) "A directed model output ranks above an undirected one, to a human reader, right now."** —
**falsified for this reader, these artifacts, this domain.** No hedging. The ordering inverted.

**(c) "SPEC §1's reframe is wrong."** — *does not follow from (b).* §1 claims the *instrument*
should rank directed output above filler. It makes no claim that an unaided human will, and the
project's own inherited findings (E53, E57b) predict that a surface-trained human reader
increasingly will not. **A human failing to do the thing the instrument is being built to do is
arguably the argument for the instrument.**

That last point is real and it is also exactly what a motivated author would say. Which is why §6
exists.

---

## §4. The curator caught themselves fabricating a maker

The most valuable thirty seconds in the transcript, and it is about item B — the nine-word prompt.

The curator noticed that a dexterity/arcane build guide never mentions Rivers of Blood, which
looms enormous in that build space:

> *"The fact that it wasn't mentioned for a while, I don't even see it mentioned anywhere in B, is
> just very weird... which is actually an unusual choice. It's something that was made for a
> reason. I read intent into that... That's what they decided against."*

**There was no decision.** B was produced from *"Write a guide to the best build in Elden Ring."*
Nothing was considered and rejected. The absence is a sampling artifact of an unconstrained
one-shot.

Then, unprompted:

> *"I'm making a person in my head now and pretending the effort's at least a 2 or a 3 or
> something."*

**That is E2, observed from the inside.** The project's central inherited finding is that hollow
content produces confident, mutually contradictory attributions — invention rather than honest
confusion. Here a reader:

1. encountered content with no maker-state behind it,
2. located a salient absence,
3. inferred a deliberate decision from it,
4. **narrated the construction of the maker while doing it**, and
5. flagged it as fabrication in the same breath.

The self-report is what makes this remarkable. The simulation could measure fabrication but never
observe a reader catching it happening. **This single observation is worth more than the ranking it
came attached to.**

It also carries a warning the instrument cannot afford to ignore: **absence is the most
fabrication-prone evidence there is.** A gap invites a decision to explain it. The `Decision` type
already requires a verbatim `alternative_rejected` span, which structurally forbids the probe from
doing exactly this — it cannot cite a quote for something the artifact does not contain. That
constraint was written on general grounds and this is the first evidence it was load-bearing.

---

## §5. My factual error, and what it cost

The curator caught a content error in item A:

> *"It looks like you're subtly wrong about corpse piler. Like, no one would call that a ranged
> attack."*

They are right. Corpse Piler is a close-range slash flurry that projects a short distance, not a
ranged attack, and item A's entire pitch is built on that mischaracterisation.

This matters beyond embarrassment. **The error is in the rich arm — the arm meant to demonstrate
care** — and it is exactly the kind of error a domain expert notices instantly. Some unknown
portion of A's last-place finish is a competence judgement rather than an intent judgement, and
the two cannot be separated after the fact.

**A is therefore compromised as a calibration standard and is marked as such.** Any future rich/thin
pair must be fact-checked by someone with domain expertise before it goes to the curator. Recorded
as **C-15**.

---

## §6. The experiment this batch actually became

The planned test — *does the curator's ranking match the protocol?* — returned a clean failure.
The batch is not wasted; it has become a **better** test, and the reframe is recorded here rather
than presented later as if it were the plan.

The instrument now reads A, B and C. Two outcomes, both informative, neither comfortable:

| instrument returns | reading |
|---|---|
| **A > C > B** (protocol order) | The probe recovered direction the human could not. That is the strongest available argument for the instrument's existence — it would be doing precisely the job §1 claims, at exactly the point where an expert human reader failed. It would also need heavy scepticism, because I wrote the artifacts and the protocol. |
| **B > C > A** (curator order) | The probe shares the human's surface heuristic. Bounded inference has not escaped the arms race, §2's mechanism is not doing what it claims, and the architecture needs rebuilding rather than tuning. |
| anything else | the probe is measuring a third thing and neither account is supported |

**This is now the sharpest single test in Gate 1** and it was arrived at by a prediction failing,
which is the only way it could have been arrived at honestly.

---

## §7. On whether more calibration is possible

The curator asked whether further rounds can be unbiased *after* this one.

**Yes, on new artifacts; no, on these three.** The curator now knows all three were machine-written
and has committed to a ranking. Re-reading them is contaminated permanently. But contamination is
per-artifact, not per-curator — batches 1 and 2 were read cold and stayed cold, and a fourth batch
of unseen artifacts would be equally cold.

**What a batch 4 should do, if there is one.** Not more of the same. The finding that matters now
is §2's: surface machine-markers pre-empt intent-reading. Testing that needs the surface signature
**decoupled** from the direction — for example, human-written artifacts of known, documented
direction-density, where no AI-marker heuristic can fire at all. That would separate claim (a) from
claim (b) in §3, which this batch could not.

That is a Gate 2 design, and it is now the most valuable outstanding experiment in the project.
Recorded as **C-16**.

---

## §8. Obligations arising

| id | obligation |
|---|---|
| C-15 | Rich/thin artifacts must be domain-fact-checked before curation. Item A is compromised and marked. |
| C-16 | Batch 4, if run, must decouple surface machine-markers from direction density — human-written artifacts of documented direction-density. Separates §3(a) from §3(b). |
| C-17 | Report the batch-3 prediction as **failing** in every downstream document. It is not withdrawn, softened, or reframed as uninteresting. |
| C-18 | The instrument's A/B/C ranking is now a pre-registered Gate 1 criterion with both outcomes' meanings fixed in §6 **before the run**. |
