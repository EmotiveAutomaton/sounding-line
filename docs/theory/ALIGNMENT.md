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

**The one thing to preserve if everything else is superseded:** *the terminal value is the seeking,
not the thing sought* — and the reason that helps is that recovering values is a limit, so any design
whose terminal value is the limit itself must act correctly while wrong, forever.
