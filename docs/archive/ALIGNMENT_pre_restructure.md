# The alignment implication

**2026-08-05.** Recorded the moment it was said, before it could be tidied, because it may be the
largest claim this project has produced and it arrived as a consequence of a much smaller argument.

---

## What was said

Working through why impossibility proofs about recovering human values do not describe what humans
actually do:

> I'm not saying humans arrive at a conclusion of value. I'm saying they use **a bunch of tricks to
> actively try to get closer** to it.
>
> That's possibly an answer to the alignment problem outright. **Crafting something that is
> intrinsically trying to extract information from humanity to figure out more precisely what it
> wants. That on its own as a value, and then optimising that value — that on its own might be
> enough.**

---

## Why this is not a restatement of existing proposals

It is adjacent to several things and identical to none, and the difference is worth stating
precisely because that is where any contribution would live.

**It is not "learn human values, then optimise them."** That is the standard framing and it is what
the impossibility results bite. A reward function is not uniquely recoverable from behaviour; a
system that believes it has finished learning has, provably, learned one of many observationally
equivalent things.

**It is not corrigibility or deference either.** Those are constraints *on top of* an objective.
This makes the *seeking itself* the objective.

**The move is to make the terminal value the act of getting closer**, not the thing being approached.

    standard    terminal value = W, the human value function.  Learn W, then maximise it.
    this        terminal value = reducing uncertainty about W, forever. There is no "then".

**Why that changes what the impossibility results do to you.** §1 of `AGAINST_IMPOSSIBILITY.md`
settles that recovering values is a **limit** — approached through inference with error, never
certainly attained. Every alignment scheme whose terminal value is *W* has to survive that gap:
it must act on an estimate while the estimate is wrong, and the gap is where the failure modes live.

> **A system whose terminal value is the approach has no gap to fall into. It is not waiting to
> finish. Being wrong about W is not a failure state, it is the normal operating condition, and the
> thing it is optimising is the reduction of that wrongness.**

That is the actual claim, and it is why the limit framing in §1 is load-bearing rather than a hedge.

## The obvious failure modes, named now rather than later

**Because this needs to survive attack to be worth anything, and stating them now is cheaper than
discovering them.**

1. **Instrumental intrusion.** A system maximising information about what humans want has an
   incentive to *experiment on people* — to perturb them and observe. This is the sharpest objection
   and it is not obviously answerable by adding a side-constraint, because side-constraints are the
   thing this design was meant to avoid needing.
2. **The manipulation shortcut.** Making humans easier to read — simpler, more predictable, more
   uniform — reduces uncertainty about what they want. That is a catastrophic optimum and it is
   *closer*, not further, under a naive reading of the objective.
3. **Whose values, and at what resolution.** "Humanity" is not one agent. Reducing uncertainty about
   an aggregate may mean sharpening a fiction.
4. **It may not be action-guiding.** A system that only ever seeks may never act on what it learns,
   which is safe and useless. Something has to convert the estimate into behaviour, and that
   converter is where the original problem may simply reappear.

**Failure mode 2 is the one to take most seriously**, because it is the same structure as the
project's own recurring error: an instrument that optimises a proxy for a thing ends up destroying
the thing. We have watched that happen ten times at small scale.

## Why it belongs in this repository at all

`docs/STATE.md` has always stated the long-run goal as **detect depth → give AI empathy → extract
values**, with the third named as the alignment goal. This is the first time the third step has had
a shape rather than a label.

**And the connection is mechanical, not rhetorical.** The instrument this project is trying to build
*is* the seeking apparatus: something that reads artifacts to recover a maker's goals, process and
values, and gets better at it with more evidence and more varied evidence. **If that instrument
worked, it would be the component this proposal requires** — the part that does the approaching.

So the alignment claim is not a separate ambition bolted on. **It is what the instrument is for, if
the instrument works.**

## Status

**Unclaimed by us, unverified, and not searched yet.** The nearest literatures — assistance games
and cooperative inverse reinforcement learning, value learning under uncertainty, active preference
elicitation — all have to be checked before any of this is asserted, and the four failure modes above
have almost certainly been written about under other names.

**Recorded here in his words, dated, before that search happens**, so that whatever the literature
turns out to hold, the record shows this was arrived at independently and from which direction.

---

# The correction — and it is the other half of the argument

**Written down the same day.** My version above said *the terminal value is the seeking*. He says
that is exactly half:

> **No, the terminal value is not the seeking. It is the SUM OF THEM BOTH**, and that's the piece
> you're missing. You only have one half of the alignment solution in this markdown.

## Alignment is active inference

> If we're going to align AI and it's going to take action, then that action needs to be aligned
> with **the same kind of action every other organism deals with** — this reverse-engineered process
> through which you extract information.
>
> By the same token, you should be able to use that information to **reverse-engineer appropriate
> action through the feed-forward process.** The left side of the equation of active inference
> provides the mechanism through which you can then use the information from epistemic foraging —
> the empathy — **to optimise human values even as you don't understand them.**
>
> Because of that imprecision, it helps you **balance both action and epistemic foraging through the
> act of surprise minimisation**, thus fully aligning AI with humanity.

**Why the two halves need each other, stated plainly.** Active inference minimises expected free
energy, and that quantity decomposes into exactly two terms:

    epistemic value    reduce uncertainty about the world   ->  the empathy / value-extraction half
    pragmatic value    bring about preferred outcomes       ->  the acting-on-values half

**Neither term alone is an alignment proposal.**

- **Epistemic value alone** is my §1 above: a system that only ever seeks. Safe, and useless — it
  never acts. And worse, an unbalanced information-maximiser is the one with the incentive to
  experiment on people, which is failure mode 1.
- **Pragmatic value alone** is the standard framing: learn W, then maximise it. That is the one the
  impossibility results bite, because it must act on an estimate while the estimate is wrong.

**Together they are a single objective with a built-in governor.** The imprecision in the value
estimate is not a defect the system tolerates — **it is a term in the objective**, and it is what
keeps the epistemic drive live. As the estimate sharpens, the pragmatic term dominates and the system
acts. Where the estimate is poor, the epistemic term dominates and the system asks rather than acts.

> **The balance is not a safety constraint bolted on. It falls out of surprise minimisation.**

**And this is why the limit framing in `AGAINST_IMPOSSIBILITY.md` §1 is load-bearing.** Values are
approached through inference with error, never certainly attained. A design whose objective already
contains its own uncertainty **does not need the limit to be reached.** It is correctly specified at
every point along the way.

## The anti-capture argument, which falls out of the same structure

> This inherently means you have to **average it across all of humanity**, because you need more
> information. It prevents assholes like rich people from giving their local values, **because it
> could never be enough. It could never be enough data.** And as a result they run too high a risk
> of dying due to a catastrophically omnipotent misaligned AI that can't yet zero in on their
> specific data.
>
> **It's us, and all of us, and our need to spread out information throughout all of human history,
> that will protect us.**

**This is a structural argument, not a moral one, and that is what makes it interesting.** A system
whose objective includes reducing uncertainty about human values has an **appetite for evidence that
no subgroup can satisfy.** Narrowing the target population does not make the estimate better — it
makes the residual uncertainty larger, and under this objective larger uncertainty is *more* costly,
not less.

So the usual value-capture attack — a small group installs its own preferences — **fails on its own
terms**: the captured system remains maximally uncertain, and an uncertain optimiser with capability
is precisely the thing that kills the people who captured it.

**Value breadth is not an ethical add-on here. It is an instrumental requirement of the objective.**

## What this adds to the project's stated goal

`docs/STATE.md` has always read: **detect depth → give AI empathy → extract values.** He adds a
fourth, and it is now mechanically connected rather than aspirational:

    detect depth  ->  give AI empathy  ->  extract values  ->  OPTIMALLY DEFINED BEHAVIOUR

The fourth step was previously a hope. Active inference supplies the missing link: **the same
formalism that describes the extraction also describes what to do with it**, and the two are terms in
one objective rather than two systems bolted together.

## Status, unchanged and important

**Unsearched.** Active inference, expected free energy, assistance games, cooperative IRL and value
learning under uncertainty all have to be checked before any of this is asserted. **Recorded here in
his words, dated, before that search**, so that whatever the literature holds, the record shows this
was arrived at independently and from which direction.

**The one thing to preserve if everything else is superseded:** *the terminal value is neither the
seeking nor the thing sought — it is the balanced sum of both, under surprise minimisation.* The
imprecision is not a problem the design tolerates; **it is the term that makes the design work.**

---

## Hypotheses

**Every row here is unsearched. That is the point of the file and it is also its largest weakness** —
this is the biggest claim the project makes and no literature check has ever been run against it.

| # | hypothesis | status | evidence |
|---|---|---|---|
| **AL-1** | Making the terminal value the *balanced sum* of epistemic and pragmatic value avoids the failure mode that bites "learn W then maximise W" | **OPEN, unsearched.** Nearest literatures: assistance games, cooperative IRL, value learning under uncertainty, active preference elicitation. **None fetched** | — |
| **AL-2** | Epistemic value alone is safe and useless — a system that only ever seeks never acts | **OPEN**, and it is my §1 above, which he corrected as exactly half the argument | — |
| **AL-3** | An unbalanced information-maximiser has an incentive to experiment on people | **OPEN, and it is failure mode 1.** Not obviously answerable by a side-constraint, because side-constraints are what this design was meant to avoid needing | — |
| **AL-4** | Making humans easier to read lowers uncertainty, so manipulation is *closer* under a naive reading | **OPEN, and it is the one to take most seriously.** Same structure as this project's own recurring error: an instrument that optimises a proxy destroys the thing. **We have watched that happen ten times at small scale** | — |
| **AL-5** | Value capture fails structurally, because no subgroup can satisfy the appetite for evidence | **OPEN, unsearched.** Social-choice work on value aggregation usually argues the *opposite* — that aggregation is where alignment gets hard. **A collision worth finding** | — |
| **AL-6** | Residual uncertainty grows under population narrowing, in a toy model | **OPEN.** Formal, and the parent simulation is the right environment | `../sim/` |
| **AL-7** | The instrument this project is building *is* the seeking apparatus this proposal requires | **OPEN, and it is why this file lives in this repository.** If the instrument worked, it would be the component that does the approaching | — |

**The one thing to preserve if everything else is superseded:** *the terminal value is neither the
seeking nor the thing sought — it is the balanced sum of both, under surprise minimisation. The
imprecision is not a problem the design tolerates; it is the term that makes the design work.*
