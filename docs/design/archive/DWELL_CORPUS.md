# The dwell corpus — spec, not yet acquired

**Deferred design notice (2026-08-21).** The controlled same-maker/two-form design remains
valid, but it is not the current highest-value unblocked item; Phase 2.3's known-answer process
roots govern current work. Reopen this corpus only if a live branch again requires a
dwell-definedness test.

**2026-08-05.** Specified because sim **T-3** named the regime where decision-counting is a
well-defined event, and it is the first time this project has had a corpus request with a *reason*
attached rather than a vibe. C-14 was never more than "we should get better data."

---

## §1. What T-3 actually said

Sweeping what makes the reader's sub-goal posterior concentrate:

| | | effect on mean entropy |
|---|---|---|
| artifact length | 12 → 192 steps | **−0.120** |
| **mode dwell** | 2 → unbounded | **−0.232** |

> **Concentration is governed by how long a maker stays in one mode relative to how informative each
> emission is — not by how long the artifact is.** Dwell moves it roughly twice as far as length.

At long dwell, "a decision was recovered" becomes well-defined in up to **100%** of rollouts, against
**2%** at baseline for the same threshold. That is not a marginal improvement; it is the difference
between a measurable event and an undefined one.

They also marked their own prediction wrong — *"the prediction that length is inert was too strong
and is reported as wrong"* — which is why the ranking rather than the sign is what to trust.

## §2. Why Gate 3's corpus is the worst possible case

Gate 3 is 51 fetched web pages. A commercial web page changes purpose **every paragraph**: hook,
credential, explanation, objection-handling, call to action. **Maximum mode switching, minimum
dwell.** T-3 says the sub-goal posterior can never concentrate there, which means every
count-based measure run on it was undefined by construction.

**That independently explains N13's failure.** Within-artifact sd 0.808 against between-half 0.087
is exactly what a non-stationary sub-goal produces. We recorded it as an instability in the
*measure*; T-3 says it is a property of the *corpus*.

## §3. The design — construction-controlled, which is the only kind that has ever worked

The obvious version is "compare high-dwell genres to low-dwell genres." **Do not build that.** It
reintroduces register, which has killed four measures.

**Build this instead:**

> **One maker, one venue, two structural forms.** A writer's sustained single-argument piece against
> the same writer's multi-item piece — the long essay against the link roundup, the deep-dive against
> the weekly notes, the incident postmortem against the status update.

Maker, register, vocabulary, platform, editorial process and era are all held **constant by
construction**. The only thing that varies is how long the author stays on one sub-goal. That is the
same design as G-2, which is the only within-human comparison that has ever produced a positive
(2.05×).

### Candidate sources, ranked by how cleanly the pairing exists

| | high dwell | low dwell | why it pairs |
|---|---|---|---|
| **engineering blogs** | incident postmortem | weekly/monthly notes | same author, same site, same register, wildly different structure |
| **academic authors** | single-argument paper | review or survey | one thesis vs. a tour of many |
| **newsletters** | the one long piece | the linkdump issue | often literally alternating weeks |
| **appellate opinions** | majority on one issue | omnibus multi-issue rulings | extreme dwell contrast, very uniform register |

**Target: 15–20 makers × 2 forms.** Smaller than Gate 3 and worth more, because it is controlled.

## §4. The pre-registration, written before any acquisition

    PASS   count-based measures are DEFINED (posterior concentrates past threshold) substantially
           more often on the high-dwell arm than the low-dwell arm, WITHIN maker

    FAIL   definedness is the same in both arms  ->  T-3's regime does not transport off the
           simulator, and count-based measures are dead in practice as well as in principle

**Note what is being tested and what is not.** This tests **definedness**, not accuracy. Whether a
count *means* anything is a separate question and needs labels we do not have. Establishing that the
event exists at all is the prerequisite, and it is the thing T-3 says is achievable.

**Required controls, from the standing battery:** length (the high-dwell arm will be longer — this
must be matched or partialled, and it is the likeliest way this test dies), register (same maker
handles it), and the positive control on the harness.

## §5. Status

**Not acquired.** This is a fetching decision, not a night of compute, and it is the curator's call.
Estimated cost: an afternoon of sourcing, then it runs on existing machinery.

It was the highest-rated unblocked corpus request on 2026-08-05, because every measure that has
ever worked has worked on a construction-controlled corpus, and this would be the **first controlled
corpus of human artifacts** the project has ever had. It is now deferred behind the
process-inversion root map (the notice at the head of this file).
