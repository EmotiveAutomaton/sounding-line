# Alignment: the terminal value is the balanced sum of seeking and acting

> **The terminal value is not the seeking. It is the SUM OF THEM BOTH.** [...] If we're going to align
> AI and it's going to take action, then that action needs to be aligned with the same kind of action
> every other organism deals with – this reverse-engineered process through which you extract
> information. **And because of that imprecision, it helps you balance both action and epistemic
> foraging through the act of surprise minimisation.**

> **It's us, and all of us, and our need to spread out information throughout all of human history,
> that will protect us.**

> It seems like I'm late to the party here, and the rest of the world has already worked this out.
> Effectively we are trying to decide upon **a candidate objective that retains both the epistemic
> and the pragmatic terms.** You can gloss that with MaxEnt if you want, but practically speaking
> it is **a real objective that can be defined and recreated. Weighting them is going to be a
> concern.** And I do wonder how humans balance this, whether there's some kind of **dynamic
> weighting adjustment** that keeps the two somewhat in balance over time. It's very rare for
> humans to fall into endless epistemic foraging. You could have biases, certainly, but the fact
> that it's just not something humans fall into is interesting. And I wonder what that has to do
> with our lack of precision in estimating the actual environment.

> That second line was **the seed for the anti-capture hypothesis**, the idea that this persistent
> uncertainty about human values will create pressure for broader evidence that will itself prevent
> psychopathic optimization actions through active states on the part of any AI. Leveraging that
> hook, which perhaps has some analog in human behavior, is something we will have to use as **a
> shield to prevent rich people from capturing AI values.** Because of course it will be rich
> people that we're fighting against. They have always been the villains of this world that we
> live in.

**The largest claim this project makes.** The standard framing, learn human values then optimise
them, is the one the impossibility results bite, because it must act on an estimate while the
estimate is wrong. **Here the imprecision is a term in the objective rather than a defect the design
tolerates.**

**And the structure fights capture.** The signal is weak, the inference is intractable in the exact
sense [`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §7 sets out (approached through error,
never certainly attained), and
[`READER_HEURISTICS.md`](READER_HEURISTICS.md) is the record of how much machinery a *person* needs to
do it badly. **That weakness is what protects the objective from being owned.** A system whose
terminal value includes reducing uncertainty about what humans want has an appetite for evidence
**no individual and no subgroup can satisfy**, so narrowing the target does not sharpen the
estimate, it enlarges the residual, and under this objective a larger residual is more costly. **The
captured system stays maximally uncertain, and an uncertain optimiser with capability is exactly what
kills whoever captured it.** Value breadth is instrumentally forced, never an ethical add-on.

## Where this sits in the project

**This is the file furthest from anything we are currently working on, and by a wide margin the least
tested.** That is deliberate rather than neglectful. **We are solving the near problems before the far
ones**, on the expectation that we arrive at this one holding more pieces than we do now.

**The first piece is the one being built.** Collecting value data by reverse-engineering it,
**laddering up from intent to process to values**, is the project's current best bet for how any of
this gets grounded, and it is the whole of the rest of this folder. **It genuinely might be the
answer.**

**What this file is for is the shape from a distance**, so we know what parts we need to arrive with.
Nothing here has been searched or simulated, and the next honest step is one or two simulations rather
than an argument.

**Dormancy ruling (2026-08-09, the program pass).** This file is formally dormant. It retains the
failure conditions as a boundary specification and no alignment experiments are engineered against
them yet, because the upstream instrument cannot supply calibrated goal, process, or value
posteriors for anything to be aligned to. The wake condition is written in the program. First
specific recorded choices become recoverable on held-out makers, then an expertise-conditioned
remainder transfers across kinds and predicts unseen tradeoffs. Until both hold, work billed to
this file is premature by the project's own sequencing.

---

## §0. You can only route attention onto values you possess

*(Moved from the architecture file 2026-08-09. It is a values question, and it belongs with the
alignment consequence.)*

> If I were forced to design a Nazi camp, part of my motivation would be not dying. But part would be
> **efficiency** – I could tap a need for efficiency to do this. **But I wouldn't be able to tap into
> the cruelty a Nazi designer would have. It just wouldn't be there for me to optimise.**

> I'm going to walk that back. I'm not going to claim that I wouldn't be able to do something if I
> couldn't leverage any of my motivations. The real main claim is that **different actions can be
> derived from different sets of motivational weightings.** Which is a much weaker claim and
> honestly pretty lame. But worth keeping in this file, at least as a future thought.

Two makers producing the same artifact under the same instruction reach it through different
motivational weightings, and the route carries information. **The absent value is as informative
as the present one**, a mechanism for why an artifact reads as made-under-duress. The recoverability of an
absent drive now has a working simulated form (the architecture file's missing-middle section);
what this section owns is the consequence. **A system whose values are seeded rather than specified
can still only route attention onto what the seed contains**, which is a design constraint on any
bootstrap, and unexplored.

## §1. The core claim: one objective, two terms

**Active inference minimises expected free energy, and that quantity decomposes into exactly two
terms:**

    epistemic value    reduce uncertainty about the world   ->  the empathy / value-extraction half
    pragmatic value    bring about preferred outcomes       ->  the acting-on-values half

**Neither term alone is an alignment proposal.**

- **Epistemic value alone** is a system that only ever seeks. **Safe, and useless**, since it never
  acts. And an unbalanced information-maximiser is precisely the one with an incentive to experiment
  on people.
- **Pragmatic value alone** is the standard framing, learn *W* then maximise it. **That is the one
  the impossibility results bite.**

**Together they are a single objective with a governor whose setting is not free.** As the
estimate sharpens the pragmatic term dominates and the system acts; where the estimate is poor the
epistemic term dominates and the system asks rather than acts.

**Superseded** by his own reading of the research, kept as the original form:

> **The balance is not a safety constraint bolted on. It falls out of surprise minimisation.**

> Upon looking at the research, the balance does apparently not fall out of surprise minimization.
> **It is a scalar that is adjusted by the model in question.** And that's the kind of future
> trouble that I'm going to leave for later stages of the project. But a note to revisit: humans
> obviously don't fall into this fail state of **permanent epistemic foraging.** Or if we do, then
> it needs recasting as some established psychosis that we can then harvest for information.
> Nothing comes to mind, though. I can't imagine how it would present, practically speaking.

**And this is why the limit framing in [`THE_TRIPLE_INFERENCE.md`](THE_TRIPLE_INFERENCE.md) §7 is
load-bearing rather than a hedge.** Values are approached through inference with error and never
certainly attained. **A design whose objective already contains its own uncertainty does not need
the limit to be reached. It is correctly specified at every point along the way.**

## §2. How this differs from the proposals it sits next to

    standard    terminal value = W, the human value function. Learn W, then maximise it
    this        terminal value = the balanced sum. There is no "then"

Every alignment scheme whose terminal value is *W* has to survive the gap between the estimate and the
truth. **It must act while the estimate is wrong, and the gap is where the failure modes live.**

> **A system whose terminal value includes the approach has no gap to fall into. Being wrong about W
> is not a failure state, it is the normal operating condition, and what it optimises is the reduction
> of that wrongness.**

**Corrigibility and deference are different animals too.** Those are constraints *on top of* an
objective, while **this makes the balance itself the objective.**

## §3. The anti-capture argument, which falls out of the same structure

> This inherently means you have to **weight it across the breadth of humanity**, because you need
> more information. It prevents assholes like rich people from giving their local values, **because it
> could never be enough. It could never be enough data.** And as a result they run too high a risk of
> dying due to a catastrophically omnipotent misaligned AI that can't yet zero in on their specific
> data.
>
> **It's us, and all of us, and our need to spread out information throughout all of human history,
> that will protect us.**

> There's work to be done there. We'll have to work out a population model, a sampling rule, an
> aggregation rule, and so on. But at least we'll have data points. They'll be sparse, but we will
> have extracted them, and they will be something we can assemble. **It's the first step. We'll
> deal with the second step when we get there.**

**A structural argument rather than a moral one, and that is what makes it interesting.** A system
whose objective includes reducing uncertainty about human values has **an appetite for evidence that
no subgroup can satisfy.** Narrowing the target population does not improve the estimate, it enlarges
the residual uncertainty, and under this objective larger uncertainty is *more* costly, not less.

**So the usual value-capture attack fails on its own terms.** The captured system remains maximally
uncertain, and an uncertain optimiser with capability is precisely the thing that kills the people who
captured it.

**Value breadth is an instrumental requirement of the objective here, never an ethical add-on.**

## §4. The failure modes, named now rather than discovered later

**This needs to survive attack to be worth anything, and stating them now is cheaper than finding
them.**

1. **Instrumental intrusion.** A system maximising information about what humans want has an incentive
   to *experiment on people*. **The sharpest objection**, and not obviously answerable by a
   side-constraint, because side-constraints are what this design was meant to avoid needing.
2. **The manipulation shortcut.** Making humans easier to read (simpler, more predictable, more
   uniform) reduces uncertainty. **A catastrophic optimum that is *closer*, not further, under a naive
   reading of the objective.**
3. **Whose values, and at what resolution.** "Humanity" is not one agent. Reducing uncertainty about an
   aggregate may mean sharpening a fiction.
4. **It may not be action-guiding.** A system that only ever seeks never acts on what it learns.
   Something has to convert the estimate into behaviour, **and that converter is where the original
   problem may simply reappear.**

**Failure mode 2 is the one to take most seriously**, because it is the same structure as this
project's own recurring error. **An instrument that optimises a proxy for a thing ends up destroying
the thing. We have watched that happen ten times at small scale.**

## §5. Why this belongs in this repository

The project's stated goal has always been **detect depth → give AI empathy → extract values**, with a
fourth step that was a label rather than a mechanism. Active inference supplies the link:

    detect depth  ->  give AI empathy  ->  extract values  ->  OPTIMALLY DEFINED BEHAVIOUR

**The same formalism that describes the extraction also describes what to do with it**, and the two are
terms in one objective rather than two systems bolted together.

**And the connection is mechanical, not rhetorical.** The instrument this project is building *is* the
seeking apparatus. It reads artifacts to recover a maker's goals, process and values, and improves
with more and more varied evidence. **If that instrument worked, it would be the component this
proposal requires, the part that does the approaching.**

## §6. Hypotheses

**Every row is unsearched. That is the point of the file and also its largest weakness.**

| # | hypothesis | status |
|---|---|---|
| **AL-1** | Making the terminal value the *balanced sum* avoids the failure mode that bites "learn W then maximise W" | **OPEN, unsearched.** Nearest literatures are assistance games, cooperative IRL, value learning under uncertainty, and active preference elicitation. **None fetched.** He has since said he believes most components are already occupied |
| **AL-2** | Epistemic value alone is safe and useless | **OPEN.** My first write-up, **which he corrected as exactly half the argument** |
| **AL-3** | An unbalanced information-maximiser has an incentive to experiment on people | **OPEN.** Failure mode 1, and **not answerable by a side-constraint**, since side-constraints are what this design exists to avoid needing |
| **AL-4** | Making humans easier to read lowers uncertainty, so manipulation is *closer* under a naive reading | **OPEN, and the one to take most seriously.** **Same structure as this project's own recurring error**, an instrument that optimises a proxy destroying the thing. We have watched it happen ten times at small scale |
| **AL-5** | Value capture fails structurally, because no subgroup can satisfy the appetite for evidence | **OPEN, unsearched.** **Social-choice work on value aggregation usually argues the opposite**, that aggregation is where alignment gets hard. A collision worth finding |
| **AL-6** | Residual uncertainty grows under population narrowing, in a toy model | **OPEN.** Formal, and the parent simulation is the right environment. The only row here that could be settled without a literature pass |
| **AL-7** | The instrument this project is building *is* the seeking apparatus this proposal requires | **OPEN.** **It is why this file lives in this repository** rather than in a notebook |

**What these add up to.** **Nothing here has been checked against anything, and that is the file's
defining fact.** The seven rows are not independent. AL-1 is the claim, AL-2 and AL-3 are the halves
it is built from, AL-4 and AL-5 are the two attacks that would kill it, and AL-6 and AL-7 are what it
would take to build. **The ordering that matters is that AL-4 is cheap to reason about and fatal if
right, while AL-1 needs a literature sweep before it can even be stated as novel.** Do AL-4 first.
**A proposal that dies to its own second failure mode does not need a priority search.**
**Confidence: untested, logic only, by design and by declared distance.**

---

**The one thing to preserve if everything else is superseded:** *the terminal value is neither the
seeking nor the thing sought. It is the balanced sum of both, with the balance itself a quantity
to be engineered rather than assumed. The imprecision is not a problem the design tolerates; it is
the term that makes the design work.*

---

## Appendix: recreating the existing alignment research, an early project goal

The dormancy ruling stands; this appendix records only the frontier recreations that happen to be
alignment research, under the exact-value standard (a recreation passes by matching the published
numbers precisely, and simulation results need somewhere to live). Kept short by instruction.

| anchor | recreation state |
|---|---|
| Armstrong & Mindermann's unidentifiability construction | **PASSED (test-side toy, L60).** The reward/planner degeneracy reproduced at exactly 0.5/0.5, then relaxed: the bounded human-shaped family narrows the posterior twentyfold, known near-optimality twofold, both fortyfold. The one exact-value pass the recreation phase holds so far |
| Baker, Saxe & Tenenbaum's inverse planning | **EXPERIMENT 1 PASSED AT EXACT-VALUE GRADE (L119).** The nine-action rebuild under the soft Bellman fixed point lands all four printed best-fit correlations at printed precision (0.8281/.83, 0.9780/.98, 0.9440/.94, 0.9661/.97) on the decoded 99-stimulus set (L114), and matches the paper's own digitized model predictions to a thousandth across all 297 cells, so the pipeline is verified cell by cell, not just by correlation. The paper's 99-versus-100 stimulus-count contradiction is located (one figure stimulus has no panel counterpart). Remaining: the grid and bootstrap gates, the all-squares prior arm, and Experiments 2 and 3 behind their own stimulus extractions |
| the estimator tournament over these substrates (G134) | **NOT STARTED**, and it is the step where these recreations stop being recreations and start pricing the residualisation estimator's failure boundary |

What this buys the dormant file: when the wake condition is ever met, the impossibility results
it leans on will already exist here as running code with their relaxations mapped, rather than as
citations.
