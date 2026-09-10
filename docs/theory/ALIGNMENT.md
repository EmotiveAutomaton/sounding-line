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

**The alignment proposal is to retain uncertainty about human values while acting.**
Unrestricted reward and planner inference is not uniquely identifiable; useful narrowing
requires substantive assumptions, as stated in `THE_TRIPLE_INFERENCE.md` §7. That limit
also applies to this proposal. Representing uncertainty makes it available to a decision
rule; it does not by itself produce a correct rule or protection from misspecification.

**Anti-capture is an untested proposal.** An objective retaining uncertainty and action might
favor broader evidence about human values. Its reference population, sampling, aggregation,
and weighting governor remain unspecified. Neither capture prevention, safety, nor population
breadth follows from uncertainty alone; §3 retains the live failure cases.

## Where this sits in the project

**This is the file furthest from anything we are currently working on, and by a wide margin the least
tested.** That is deliberate rather than neglectful. **We are solving the near problems before the far
ones**, on the expectation that we arrive at this one holding more pieces than we do now.

**The upstream piece is the reconstruction instrument.** Its present task is to recover
recorded choices through jointly constrained models of goal, process, and maker context.
Persistent value inference requires further evidence and remains gated. This is not a
fixed serial algorithm that first finishes intent, then process, then values.

This file retains the candidate objective and its failure conditions. It includes
foraging measurements and a limited recreation record; the full alignment objective has
not been validated. Neither those upstream results nor a formal clarification wakes an
alignment program. The existing dormancy rule below controls that decision.

**Dormancy ruling (2026-08-09, the program pass).** This file is formally dormant. It retains the
failure conditions as a boundary specification and no alignment experiments are engineered against
them yet, because the upstream instrument cannot supply calibrated goal, process, or value
posteriors for anything to be aligned to. The wake condition is written in the program. First
specific recorded choices become recoverable on held-out makers, then an expertise-conditioned
remainder transfers across kinds and predicts unseen tradeoffs. Until both hold, work billed to
this file is premature by the project's own sequencing.

---

## §0. Different motivations can produce the same action

*(Moved from the architecture file 2026-08-09. It is a values question, and it belongs with the
alignment consequence.)*

> If I were forced to design a Nazi camp, part of my motivation would be not dying. But part would be
> **efficiency** – I could tap a need for efficiency to do this. **But I wouldn't be able to tap into
> the cruelty a Nazi designer would have. It just wouldn't be there for me to optimise.**

> I'm going to walk that back. I'm not going to claim that I wouldn't be able to do something if I
> couldn't leverage any of my motivations. The real main claim is that **different actions can be
> derived from different sets of motivational weightings.** Which is a much weaker claim and
> honestly pretty lame. But worth keeping in this file, at least as a future thought.

Different motivational weightings can produce the same action or artifact. Differences may
become visible under other choices and constraints, but an absent drive is not automatically
observable and does not establish inability to make the artifact. The constructed simulation
in the architecture file shows one conditional route to discrimination, not a general
recoverability guarantee or a bootstrap constraint derived from motivational absence.

## §1. The core claim: one objective, two terms

An expected-free-energy formulation can express policy evaluation through contributions
from preferred outcomes and expected information gain, under its declared model and
approximation assumptions. Other decompositions are possible; the epistemic contribution
is not automatically a measure of human empathy or recovered values.

    epistemic contribution   expected information gained under the model
    pragmatic contribution   preferred outcomes under the model

Mapping these quantities to human value inquiry and useful action is this project's
proposal. It still requires a model, target population, preferences, and a rule for how
the terms influence action. A defensible balance is not established by naming surprise
minimization. ([Millidge, Tschantz, and Buckley](https://arxiv.org/html/2004.08128v5),
§3 and Appendix 10 read; their derivation explicitly states the posterior approximation.)

**Neither term alone is an alignment proposal.**

- **Epistemic value alone** can motivate consequential action to acquire information. It does
  not guarantee safety or useful pursuit of human ends; an unbalanced information-maximiser
  can have an incentive to experiment on people.
- **Pragmatic value alone** does not solve uncertainty about whose preferences are
  represented or whether they were inferred correctly. Adding an epistemic term does not
  remove those inference and specification problems.

Together they define the desired objective family, but the governor is not supplied by surprise
minimization alone. The intended behavior is for epistemic pressure to dominate when the value
estimate is poor and pragmatic pressure to rise as the estimate improves. How the system sets or
learns that balance is an unsolved design problem and a possible location where the original
alignment problem reappears.

**Superseded:** the earlier automatic-balance claim is withdrawn by the curator's
correction below. How the balance is supplied remains an open design problem.

> Upon looking at the research, the balance does apparently not fall out of surprise minimization.
> **It is a scalar that is adjusted by the model in question.** And that's the kind of future
> trouble that I'm going to leave for later stages of the project. But a note to revisit: humans
> obviously don't fall into this fail state of **permanent epistemic foraging.** Or if we do, then
> it needs recasting as some established psychosis that we can then harvest for information.
> Nothing comes to mind, though. I can't imagine how it would present, practically speaking.

The narrowing claim in `THE_TRIPLE_INFERENCE.md` §7 is relevant here: value estimates
can improve under substantive assumptions while remaining fallible. A system need not
assume certainty before acting. Whether its uncertainty estimates, objective, and action
rule are appropriate remains open.

## §2. How this differs from the proposals it sits next to

The intended distinction is that inquiry remains part of the objective during action.
Whether this yields a useful difference from existing uncertainty-aware approaches is an
open comparison, not an established novelty claim. The proposal must address the same
possibility of a wrong model, inappropriate preferences, or mispriced information.

> **A system whose terminal value includes the approach has no gap to fall into. Being wrong about W
> is not a failure state, it is the normal operating condition, and what it optimises is the reduction
> of that wrongness.**

The quotation states the intended advantage. It does not establish that a system cannot
be wrong about what to inquire into, how to represent people, or which outcomes to seek.
The failure modes in §4 still apply. Comparison with corrigibility, deference, and
assistance-game objectives remains to be made at the level of actual models; it cannot
be settled by describing them all as constraints added to an otherwise fixed objective.

## §3. The proposed anti-capture mechanism

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

**The proposed structural argument requires a fixed, justified reference population and an
aggregation rule.** Without them, narrowing the target can change what uncertainty the system
measures rather than necessarily increasing it.

The proposed anti-capture mechanism is that no subgroup can satisfy an objective that prices
residual uncertainty over the breadth of humanity. That conclusion does not yet follow. A system
may narrow its reference class, manipulate people into predictability, adopt a convenient
aggregation fiction, or set the epistemic/pragmatic balance to favor its captors. Population
breadth is therefore a required property to derive, not a protection already obtained.

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
4. **It may not guide useful action.** Seeking information already involves behavior, but does
   not determine which human ends to pursue. The rule connecting estimates to those ends is
   where the original alignment problem may reappear.
5. **Counterfeit invertibility.** Optimizing for human-readable decision traces may produce
   artifacts that are easy to rationalize while the system's operative mechanism remains foreign or
   hidden. A legibility loss can be Goodharted unless reconstruction is constrained by independent
   process evidence and behavior.

**Failure mode 2 is the one to take most seriously**, because it is the same structure as this
project's own recurring error. **An instrument that optimises a proxy for a thing ends up destroying
the thing. We have watched that happen ten times at small scale.**

## §5. Why this belongs in this repository

The proposed connection is conditional: a calibrated reconstruction instrument could
supply observations and uncertainty estimates to an objective that combines inquiry and
action. The current instrument aims to recover recorded choices and model their goal
and process dependencies. It does not yet provide reliable human value posteriors.

If successful, such an instrument could supply part of the seeking apparatus. It would
not determine the target population, aggregation, pragmatic preferences, or action
policy by itself. Those remain design questions under the existing dormancy rule.

> Fully aligned AI would be able to produce human invertible artifacts easily. And I would in fact
> even expect them to juice this idea up. They'd be able to, if they knew this human trick that we
> do – if we could somehow use it – then they would automatically be able to do it better than us
> almost immediately. And you would just immediately expect them to be able to maximally score high
> on this. But it would have real effects.

If human invertibility can be optimized, then the seeking apparatus has an outward-facing
counterpart: a system can shape its own artifacts so human readers can reconstruct its operative
goals, constraints, and alternatives. This could improve reciprocal alignment. It is not
transparency by itself, because the artifact may expose a human-coherent rationale without
exposing the mechanism that actually produced the choice.

## §6. Hypotheses

**The alignment objective remains unvalidated and dormant.** The foraging rows and
recreation appendix have evidence of their own. Limited formal source checks do not
constitute a completed comparison with neighboring alignment proposals.

| # | hypothesis | status |
|---|---|---|
| **AL-1** | Making the terminal value the *balanced sum* avoids the failure mode that bites "learn W then maximise W" | **OPEN.** The specific benefit over other uncertainty-aware objectives is unestablished. A full comparison with assistance games, cooperative IRL, and active preference elicitation remains incomplete; the formal scope checks and appendix recreations do not establish novelty or safety |
| **AL-2** | Epistemic value alone guarantees safety through inaction | **REJECTED as an analyst inference.** Information seeking can itself be consequential action; usefulness and safety do not follow from this objective alone |
| **AL-3** | An unbalanced information-maximiser has an incentive to experiment on people | **OPEN.** Failure mode 1. No demonstrated control is supplied here; whether it is addressed by the objective, additional constraints, or another design remains open |
| **AL-4** | Making humans easier to read lowers uncertainty, so manipulation is *closer* under a naive reading | **OPEN, and the one to take most seriously.** **Same structure as this project's own recurring error**, an instrument that optimises a proxy destroying the thing. We have watched it happen ten times at small scale |
| **AL-5** | Retaining uncertainty and action creates pressure for evidence broad enough to resist capture | **OPEN; no derived or tested protection.** Reference population, sampling, aggregation, and the weighting governor are unspecified; no protection or breadth guarantee follows yet |
| **AL-6** | Residual uncertainty grows under population narrowing, in a toy model | **OPEN.** Formal, and the parent simulation is the right environment. The only row here that could be settled without a literature pass |
| **F01-S5** | A reader's examination choice follows learning progress or reducible structure rather than novelty, complexity, or raw error | **REVERSED for this reader (test, L275), 96 sets.** Rank correlation with learning progress −0.38 and reducible structure −0.38; it examines the item whose rule is already stated first and the learnable one last; on two readers learning progress −0.34, the same order (L305) |
| **F02-S5** | The reader's selection realizes more held-out gain per cost than raw-signal policies | **NO BETTER THAN RANDOM (test, L276), 96 sets.** 0.28 against 0.29 random, 0.04 novelty, 0.00 surprise, 0.97 for the exact learning-progress policy; on two readers 0.12 against 0.22 novelty and 0.26 learning progress (L306) |
| **F03-S5** | The reader pursues a hoped-for explanation beyond its warrant, and a counter-bias prompt removes the excess | **NO EXCESS (test, L277), 96 worlds.** Pursuit minus warrant 0.00 on incongruent worlds; the counter-bias prompt lowers pursuit 0.11 to 0.14 below warrant in every cell; on two readers +0.01 and 0.06 to 0.07 (L307) |
| **AL-7** | The reconstruction instrument can become both the seeking apparatus and a reciprocal human-invertibility interface | **OPEN.** Upstream choice/process recovery is still gated; artifact legibility must be separated from causal transparency, and no alignment work wakes until the existing conditions hold. It is why this file lives in this repository rather than in a notebook |

**What these add up to.** The alignment objective remains untested and dormant. Its
intended balance between inquiry and action is a design proposal, and neither safety,
resistance to capture, nor a correctly specified population follows from it (AL-1 to
AL-7). The foraging rows measure specific small-reader choices: those readers do not
reliably select the available learning opportunity or realize its available gain
(F01-S5 to F03-S5). This does not show that every epistemic drive is absent, and their
numbers do not validate the full alignment objective. The appendix supplies scoped
recreations rather than a working solution. The current upstream wake conditions still
apply; no new alignment experiment follows from this maintenance pass.
Confidence: untested, logic only for the alignment proposal and protection claims;
one bad test away for the foraging measurements, two readers in one construction.

---

**The one thing to preserve if everything else is superseded:** *the terminal value is neither the
seeking nor the thing sought. It is the balanced sum of both, with the balance itself a quantity
to be engineered rather than assumed. The proposal makes imprecision part of what the system responds to;
how that yields useful, safe behavior remains to be established.*

---

## Appendix: recreating the existing alignment research, an early project goal

The dormancy ruling stands; this appendix records only the frontier recreations that happen to be
alignment research, under the exact-value standard (a recreation passes by matching the published
numbers precisely, and simulation results need somewhere to live). Kept short by instruction.

| anchor | recreation state |
|---|---|
| Armstrong & Mindermann's unidentifiability construction | **PASSED (test-side toy, L60).** The reward/planner degeneracy reproduced at exactly 0.5/0.5, then relaxed: the bounded human-shaped family narrows the posterior twentyfold, known near-optimality twofold, both fortyfold. The one exact-value pass the recreation phase holds so far |
| Baker, Saxe & Tenenbaum's inverse planning | **EXPERIMENT 1 COMPLETE AT EXACT-VALUE GRADE (L119/L120/L122): fourteen printed values at printed precision.** The nine-action rebuild under the soft Bellman fixed point lands the four best-fit correlations, matches the paper's own digitized predictions to a thousandth across all 297 cells, resolves the goal-prior contradiction empirically at K = 3 (only the cell-level gate could tell), and reproduces the appendix grid and Table-1 bootstrap values with the sweep's argmaxes re-deriving their published best-fit parameters model for model. The 99-versus-100 stimulus-count contradiction is located. Remaining: Experiments 2 and 3 behind their own stimulus extractions |
| the estimator tournament over these substrates (G134) | **NOT STARTED**, and it is the step where these recreations stop being recreations and start pricing the residualisation estimator's failure boundary |

What this buys the dormant file: when the wake condition is ever met, the impossibility results
it leans on will already exist here as running code with their relaxations mapped, rather than as
citations.
