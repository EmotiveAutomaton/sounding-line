# Values — what they are, why they resisted every attempt, and how to get ground truth

**2026-08-05.** The curator's formulation, and the first construction of values in this project that
explains its own failures rather than adding to them.

---

## §1. Values are a weighting over a policy. A goal is one component temporarily amplified.

> Take value space and treat it as a **weighting on a policy plan**. A goal would be a weighting of a
> specific policy plan — raising one action within that plan above the rest **temporarily, due to
> attention**.

**This closes the project's founding loop.** The original claim was that appreciation is *inverse
reinforcement learning*: the reader inverts the artifact to recover the maker's reward function. This
says the reward function **is** the value set, and a goal is a temporary re-weighting of it under
attention.

Values are not a third thing to be recovered alongside goal and process. They are **the standing
distribution that goals are drawn from.**

## §2. The prediction that explains a pile of failures

A reward function is not recoverable from one episode. It is recoverable from **behaviour across many
episodes**.

> **Values need multiple artifacts by the same maker. A goal needs only one.**

The curator, arriving at it independently: *"You need all of the actions of the person to extract
their value map. We need as much information as possible to get as close to an accurate value mapping
as we can."*

**Check this against the record and it is not a coincidence:**

| | |
|---|---|
| every attempt to extract values from **one** artifact | failed |
| every **within-maker, multiple-work** design | is where the positives are — author identification at 7.6× chance, and within-author work separation at 2.05×, the only within-human positive the project has |
| the simulation's finding that the values vertex adds **exactly zero** information | is what you would expect: a **single-artifact model cannot represent a quantity that is only defined across artifacts** |

That last line matters. It means the simulation did not discover that values are empty. It discovered
that its own construction could not hold them.

## §3. The layers are fractal. They are categories, not lines.

The working vocabulary is **mechanics / technique / metaphor** (Dennett's physical / design /
intentional stances; Marr, Newell and Pylyshyn converge on the same three). The curator's correction,
recorded because it constrains any instrument built on it:

> Not only would it be fractal, but there'd be **dozens of each layer**. There are various techniques
> layered on top of each other and various mechanics layered on top of each other. **Those are
> categories, not lines.**

**And the top layer is not the only one carrying goal.** *"I agree that the top layer carries goal,
but let's not assume it's the only layer that does so."*

So the three are a **useful coarse partition, not a stack with three rungs**. Nobody in the
convergence above argues three is forced — only that three is useful. An instrument that assumes
exactly three levels, or that goal lives only at the top, is assuming more than the theory supports.

## §4. The value-blindness problem — and it is a hard constraint on method

The obvious experiment is to have someone write down a coherent value set and generate artifacts from
it. **The curator says he cannot, and the reason is not modesty:**

> You always have an imperfect view of anyone else's value set, and **you are blind to your own.**
> It's why artists will make art and look at it — in part to get a sense of their own values. They
> learn about themselves through that expression.
>
> Anything I say, anything I make will be over-indexed and automatically full of error, because it
> will be **my view of my own value set.**

**Take this as a methodological constraint, not a personal limit.** If values were introspectively
available, art would not be one of the ways people discover them. The self-report route is closed for
the same reason the ANPS questionnaire cannot reach the leaked affect layer — the instrument does not
reach the thing.

**This kills a whole class of designs**, including the one this project had queued: *author a value
set, generate against it.* It cannot be done by the person whose values they are, and a third party
describing someone else's is a second-order guess.

## §5. Where ground truth on values could actually come from

The requirement is unusual and it is worth stating precisely:

> A corpus where **multiple makers were deliberately aligned to one declared value set**, and where
> the value set is recorded independently of the artifacts.

Values are normally latent. This is the rare case where they are **declared**.

**The curator's instance, and his own discomfort with it, both recorded:**

> Religion is probably the strongest force for value alignment I can think of in the world. It does
> curiously suggest you'd be able to **extract someone's religion from their words.** [...] It could
> be written by different people all trying to notionally align with a single set of values, and
> **selected specifically for value alignment**. [...] That's such a messy test. It's also straight
> trash as academic work.

**The generalisation is the useful form, and it is not about religion.** Any corpus of *declared
shared value commitment* has the same structure:

    religious traditions · political manifestos and party literature · professional codes of ethics
    open-source project governance · activist movement writing · corporate value statements

### The confound that would sink the naive version, and the fix

**A naive test recovers topic, not values.** Religious writing mentions God; political writing
mentions policy. That is lexical and would be trivially detectable — the same trap that turned 61 of
our 81 ladder survivors into machine-detectors.

> **The fix is the same one that has worked every other time: hold topic constant by construction.**
> Take the *same practical question* — money, work, family, obligation, death — answered from within
> different declared traditions. Comparative-ethics anthologies are structured exactly this way, and
> so are advice and ethics columns in publications with different declared commitments.

### The design, which also tests §2

Two levels, deliberately:

    several makers per declared value set  x  several works per maker

That structure tests the thing that matters. **If §2 is right, value recovery should improve sharply
with more works per maker, while goal recovery should not.** And recovery should be better at the
tradition level than any single artifact allows.

### The honest objections, kept

Canon formation is a selection effect. Translation is a confound. Era is a confound. And **declared
values are not held values.**

**That last one is less damaging than it looks.** The project does not need to know what a maker
truly valued. It needs **a ground-truth label for the value set an artifact was made under** — and
declared alignment supplies exactly that, which is more than any other available corpus offers.

**It is messy. It is also the only route to ground truth on values that anyone here has proposed**,
and this is an engineering project.
