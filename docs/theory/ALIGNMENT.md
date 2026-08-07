# Alignment — the terminal value is the balanced sum of seeking and acting

> **The terminal value is not the seeking. It is the SUM OF THEM BOTH.** [...] If we're going to align
> AI and it's going to take action, then that action needs to be aligned with the same kind of action
> every other organism deals with — this reverse-engineered process through which you extract
> information. **And because of that imprecision, it helps you balance both action and epistemic
> foraging through the act of surprise minimisation.**

**The largest claim this project makes.** Not *learn human values then optimise them* — that is the
framing the impossibility results bite, because it must act on an estimate while the estimate is
wrong. **Here the imprecision is a term in the objective rather than a defect the design tolerates.**

## ⚠ On priority, stated plainly

**These sections were arrived at independently, and the author was not aware at the time that most of
the components already exist in the literature.** Active inference and its decomposition into
epistemic and pragmatic value are established; so are assistance games, cooperative inverse
reinforcement learning, value learning under uncertainty, and active preference elicitation. **Learning
that was a disappointment, and it is recorded as one rather than obscured.**

**What the existing work does not supply is the third component: the extraction mechanism itself** —
something that actually recovers a maker's goals, process and drives from what they produce, and gets
better at it with more and more varied evidence. **That is [`THE_TRIANGLE.md`](THE_TRIANGLE.md) and
[`HUMAN_HEURISTICS.md`](HUMAN_HEURISTICS.md), and it is what this repository is building.**

**Our own literature check is still owed.** Everything below was recorded in his words and dated
**2026-08-05, before any search**, so whatever the field turns out to hold, the record shows this was
arrived at independently and from which direction. **Nothing here should be asserted as novel until
AL-1 through AL-5 have been searched properly.**

---

## §1. The core claim — one objective, two terms

**Active inference minimises expected free energy, and that quantity decomposes into exactly two
terms:**

    epistemic value    reduce uncertainty about the world   ->  the empathy / value-extraction half
    pragmatic value    bring about preferred outcomes       ->  the acting-on-values half

**Neither term alone is an alignment proposal.**

- **Epistemic value alone** is a system that only ever seeks. **Safe, and useless** — it never acts.
  And an unbalanced information-maximiser is precisely the one with an incentive to experiment on
  people.
- **Pragmatic value alone** is the standard framing — learn *W*, then maximise it. **That is the one
  the impossibility results bite.**

**Together they are a single objective with a built-in governor.** As the estimate sharpens the
pragmatic term dominates and the system acts; where the estimate is poor the epistemic term dominates
and the system asks rather than acts.

> **The balance is not a safety constraint bolted on. It falls out of surprise minimisation.**

**And this is why the limit framing in [`THE_TRIANGLE.md`](THE_TRIANGLE.md) §8 is load-bearing rather
than a hedge.** Values are approached through inference with error and never certainly attained. **A
design whose objective already contains its own uncertainty does not need the limit to be reached. It
is correctly specified at every point along the way.**

## §2. How this differs from the proposals it sits next to

    standard    terminal value = W, the human value function. Learn W, then maximise it
    this        terminal value = the balanced sum. There is no "then"

Every alignment scheme whose terminal value is *W* has to survive the gap between the estimate and the
truth — **it must act while the estimate is wrong, and the gap is where the failure modes live.**

> **A system whose terminal value includes the approach has no gap to fall into. Being wrong about W
> is not a failure state, it is the normal operating condition, and what it optimises is the reduction
> of that wrongness.**

**It is not corrigibility or deference either.** Those are constraints *on top of* an objective. **This
makes the balance itself the objective.**

## §3. The anti-capture argument, which falls out of the same structure

> This inherently means you have to **average it across all of humanity**, because you need more
> information. It prevents assholes like rich people from giving their local values, **because it could
> never be enough. It could never be enough data.** And as a result they run too high a risk of dying
> due to a catastrophically omnipotent misaligned AI that can't yet zero in on their specific data.
>
> **It's us, and all of us, and our need to spread out information throughout all of human history,
> that will protect us.**

**A structural argument, not a moral one, and that is what makes it interesting.** A system whose
objective includes reducing uncertainty about human values has **an appetite for evidence that no
subgroup can satisfy.** Narrowing the target population does not improve the estimate — it enlarges the
residual uncertainty, and under this objective larger uncertainty is *more* costly, not less.

**So the usual value-capture attack fails on its own terms:** the captured system remains maximally
uncertain, and an uncertain optimiser with capability is precisely the thing that kills the people who
captured it.

**Value breadth is not an ethical add-on here. It is an instrumental requirement of the objective.**

## §4. The failure modes, named now rather than discovered later

**This needs to survive attack to be worth anything, and stating them now is cheaper than finding
them.**

1. **Instrumental intrusion.** A system maximising information about what humans want has an incentive
   to *experiment on people*. **The sharpest objection**, and not obviously answerable by a
   side-constraint, because side-constraints are what this design was meant to avoid needing.
2. **The manipulation shortcut.** Making humans easier to read — simpler, more predictable, more
   uniform — reduces uncertainty. **A catastrophic optimum that is *closer*, not further, under a naive
   reading of the objective.**
3. **Whose values, and at what resolution.** "Humanity" is not one agent. Reducing uncertainty about an
   aggregate may mean sharpening a fiction.
4. **It may not be action-guiding.** A system that only ever seeks never acts on what it learns.
   Something has to convert the estimate into behaviour, **and that converter is where the original
   problem may simply reappear.**

**Failure mode 2 is the one to take most seriously**, because it is the same structure as this
project's own recurring error: **an instrument that optimises a proxy for a thing ends up destroying
the thing. We have watched that happen ten times at small scale.**

## §5. Why this belongs in this repository

The project's stated goal has always been **detect depth → give AI empathy → extract values**, with a
fourth step that was a label rather than a mechanism. Active inference supplies the link:

    detect depth  ->  give AI empathy  ->  extract values  ->  OPTIMALLY DEFINED BEHAVIOUR

**The same formalism that describes the extraction also describes what to do with it**, and the two are
terms in one objective rather than two systems bolted together.

**And the connection is mechanical, not rhetorical.** The instrument this project is building *is* the
seeking apparatus — something that reads artifacts to recover a maker's goals, process and values, and
improves with more and more varied evidence. **If that instrument worked, it would be the component
this proposal requires: the part that does the approaching.**

## §6. Hypotheses

**Every row is unsearched. That is the point of the file and also its largest weakness.**

| # | hypothesis | status | evidence |
|---|---|---|---|
| **AL-1** | Making the terminal value the *balanced sum* avoids the failure mode that bites "learn W then maximise W" | **OPEN, unsearched.** Nearest literatures: assistance games, cooperative IRL, value learning under uncertainty, active preference elicitation. **None fetched** | — |
| **AL-2** | Epistemic value alone is safe and useless | **OPEN.** My first write-up, which he corrected as exactly half the argument | — |
| **AL-3** | An unbalanced information-maximiser has an incentive to experiment on people | **OPEN, and it is failure mode 1** | — |
| **AL-4** | Making humans easier to read lowers uncertainty, so manipulation is *closer* under a naive reading | **OPEN, and the one to take most seriously** | — |
| **AL-5** | Value capture fails structurally, because no subgroup can satisfy the appetite for evidence | **OPEN, unsearched.** Social-choice work on value aggregation usually argues the *opposite* — that aggregation is where alignment gets hard. **A collision worth finding** | — |
| **AL-6** | Residual uncertainty grows under population narrowing, in a toy model | **OPEN.** Formal, and the parent simulation is the right environment | scoped in `../sim/` |
| **AL-7** | The instrument this project is building *is* the seeking apparatus this proposal requires | **OPEN, and it is why this file lives here** | — |

---

**The one thing to preserve if everything else is superseded:** *the terminal value is neither the
seeking nor the thing sought — it is the balanced sum of both, under surprise minimisation. The
imprecision is not a problem the design tolerates; it is the term that makes the design work.*
