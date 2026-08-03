# Family v3, for review

**Built 2026-08-03 from S1.4.** Locked, not default, not yet run. `soundingline/family/family_v3.yaml`.

This is the first non-instrumental dimension the family has ever had, and it is the answer C-23 has
been owed since it was raised. It is also the change most likely to make the probe confabulate, so
it is worth arguing about before it runs rather than after.

**Where I guessed, I have said so and marked it ⚑.** Those are the four places your answer changes
the design.

---

## §1. What it is

One new dimension, `performed_affect`, categorical, reported as a distribution like purpose and
audience:

| value | gloss |
|---|---|
| **none_legible** | no affective stance is performed. Not calm — **absent** |
| **seeking** | curiosity, enthusiasm, the pleasure of working a problem |
| **rage** | irritation, frustration, grievance |
| **fear** | anxiety about standing — hedging, credentialing, pre-empting the objection |
| **care** | concern for the reader's success; effort spent making it land rather than impress |
| **play** | humour, wordplay, delight in the form |
| **grief** | loss, nostalgia, resignation; something is over and the artifact knows it |

Panksepp's primary-process systems, at your suggestion, in the vocabulary of what an artifact can
show rather than what a mammal can feel.

---

## §2. The three design decisions I took without asking

**LUST is omitted.** It is Panksepp's seventh and it is not legible in this corpus type. Including
a value the probe can only confabulate weakens every other value in the dimension, because a model
that has learned it must sometimes pick the seventh option will pick it somewhere.

**`none_legible` is listed first and is a real value, not the residual.** The wall has to be
something the instrument can *say*, not something it backs into by giving everything else a low
number. This is E37 given a name in the family.

**PERFORMED, not felt — and this is the load-bearing scope limit.** It is your distinction, made
twice in session 01 and both times unprompted:

> Low-level anger is something that I get, but performative in nature, frankly. **It's not real,
> but it was real at some point.** At this point they're kind of half recreating it.

> I'm being presented a specific face... **it is the presentation that I'm tapping into**, and I'm
> extrapolating off of that through the ways that they *imperfectly* presented it.

So the dimension reports the face and treats the slips as evidence. A reading that claims to know
how the maker felt has left the family. This is also what keeps it inside an instrument rather than
inside a personality test — a performance is a decision, and a decision is rebuttable.

---

## §3. The safeguard, because this dimension needs one more than any other

An affective label is exactly what a language model supplies fluently whether or not anything
supports it. Two constraints, both written before the dimension existed:

**Evidence.** Every affect above 10 points needs a located verbatim span, on the same terms as
`alternative_rejected`. An affect that cannot be pointed at was supplied by the reader.

**N-AFF, the mandatory null.** On artifacts with no reconstructible maker the affective posterior
must stay **flat** — normalised entropy above 0.85. This is E36's N28 applied in advance rather
than discovered afterwards, and it is what Gate 2's unlock control did not have.

> **If N-AFF fails, `performed_affect` is measuring the model's fluency and every number that uses
> it is uninterpretable.** It gets reported as failing. It does not get tuned until it passes.

`runners/run_controls.py --affect` runs it on the three locked generated artifacts. It queues
behind Gate 3.

---

## §4. ⚑ The four things I want you on

### ⚑ 1. Is `fear` the right name for what it does?

The gloss is *anxiety about standing — hedging, credentialing, pre-empting the objection*. That is
what you actually described twice in session 01: *"someone who has to prove something"*, and the
performative expertise you called *"a game I personally play all the fucking time."*

But Panksepp's FEAR is threat-to-body, and this is closer to **social-status anxiety**, which in
his scheme is nearer PANIC/GRIEF (separation distress) than FEAR. I may have merged two systems
because the artifact-level signature looks the same.

**Does the distinction matter here, or is one status-anxiety value enough?**

### ⚑ 2. Is `care` doing two jobs?

*Concern for the reader's success* covers the roofer's competent-professional register **and** the
essayist patiently building a metaphor for newcomers. Those felt like different things in your
readings — one is duty, one is generosity.

**Split, or leave merged?** Splitting adds a value; every added value is another thing the probe
can reach for wrongly.

### ⚑ 3. Should there be a value for the flat-motive case?

Your slot 06 observation: *"a hidden motive so shallow that an AI could accomplish it easily."*
That is not `none_legible` — there **is** a maker, and they wanted attention cheaply. But it is not
`seeking` either; nothing is being sought.

I did not add a value for it, because I could not tell whether it is an affect at all or just a low
value on `purpose_breadth` with `none_legible` on top. **You are better placed to say whether it
felt like a stance.**

### ⚑ 4. Is a distribution the right shape, or should this be dominant-plus-leak?

Everything else categorical in the family is a distribution, so I made this one too. But your
readings weren't distributions — they were *one dominant performed stance* plus *the places it
slipped*, which is a different object and arguably the more honest one.

A dominant-plus-leak shape would make N-AFF harder to state (there is no entropy to check) and
would need a different null. **It might still be right.**

---

## §5. What it does not change

`family_v1` and `family_v2` are untouched and still locked. The Gate 3 run in flight loads v2 and
renders `bounded_v5`, byte-identical to before this file existed. Nothing here can reach it.
