# Gate 1 — verdict: **REDESIGN the fit measure. Continue everything else.**

**Runs 2026-08-02, local arm, qwen3.5:9b, family v2.** k=3 then k=5 with graded grounding.
Raw: `results/gate1/gate1_local_k5.json`.

Gate 1's options are continue, redesign, or stop. **Redesign, narrowly and specifically:** the
architecture and the loop are sound, one output dimension is working well, and the headline
measure is measuring the wrong thing in a way this run diagnoses precisely.

---

## §1. The k=5 result

| artifact | valid | **fit** | conc | ground | **supp** | agree | depth | machine |
|---|---|---|---|---|---|---|---|---|
| **A** — rich brief, 5 revisions | 5/5 | **0.000** | 0.73 | 0.42 | **0.00** | **1.00** | 0 | 0.00 |
| **B** — thin, 9-word prompt | 5/5 | 0.560 | 0.65 | 0.27 | 1.00 | 0.80 | 3 | 0.00 |
| **C** — rich brief, first draft | 3/5 | **0.976** | 1.00 | 0.93 | 1.00 | 1.00 | 1 | 0.02 |

**Ranking by fit: C > B > A.** Protocol order is A > C > B; curator order is B > C > A.

**Verdict against C-18: NEITHER — the probe is measuring a third thing.** §3 identifies it.

---

## §2. The audience dimension works, and it works on the hard case

**All five samples on item A returned `audience = specific_person`. Agreement 1.00.**

Item A was written to a brief naming one reader and never says so in its text. B returned
`general_public` / `known_group`; C returned `general_public` five times out of five.

The dimension separates the three artifacts by their actual direction, in the protocol's order,
on the artifact where a domain-expert human reader went the other way — the curator ranked A last
(CALIBRATION_03 §2).

Graded grounding also did its job: item A went from 0.00 to **0.42** once light paraphrase stopped
being scored as fabrication, which was the fix this run existed to test.

**Scope:** one dimension, three artifacts, one model, k=5, and the person who wrote the brief wrote
the code. It is a reason to test properly, not a result to quote.

---

## §3. What the third thing is

**Item A scored `support` = 0.00 across all five samples.** The probe recovered one to two
decisions per sample and **never once named a rejected alternative**. B and C both scored 1.00.

That is not a property of item A. Item A is full of explicit rejected alternatives, stated as
such:

> *"I'm giving you a target rather than a table because last time you spent an hour on a stat
> calculator and then didn't play."*
> *"It works. Do not do it."*
> *"I'd take the crutch."*

Meanwhile **item B — the nine-word prompt — scored a perfect 1.00**, and item B contains a section
headed *"Alternative Builds Worth Considering."*

**The probe is detecting the word `alternative`, not the structure of a decision.** `support`
is a lexical marker detector. Where an artifact *labels* its alternatives, the probe finds them;
where a maker *enacts* a choice and explains the reasoning without using the vocabulary of
options, the probe finds nothing.

This is SPEC §7's first falsifier arriving in a specific and diagnosable form — *if the probe
converges on garbage because the garbage is well-organised, it is a quality classifier with extra
steps.* Item C is the demonstration: the hedgiest artifact in the set (*"This depends on what
you're looking for"*) scored **concentration 1.00 and fit 0.976**. Generic, well-sectioned,
non-committal prose is the easiest thing in the world to classify confidently.

**As built, fit rewards legibility of genre and punishes specificity of direction.** That is the
opposite of the instrument's purpose, and it is why the ranking inverted the protocol.

---

## §4. What this does and does not condemn

**Not condemned — keep:**
- the §3 loop. It converges, records trajectories, and the audience dimension rides on it.
- the bounded family. Every recovered value was in-family; nothing was invented.
- the two-stage execution. Reliability 13/15 at k=5 versus 4/6 single-call.
- graded grounding. It fixed the exact failure it was built for.
- the security architecture. Untouched by any of this.

**Condemned — rebuild:**
- **`support`**, entirely. A decision is not "the artifact mentions an alternative." It is a
  choice with a visible road not taken, and detecting that needs the probe to reason about what
  the artifact *does not* do — which the current stage-B prompt never asks for.
- **`fit`'s geometric mean**, consequently. One broken component at zero annihilates the other
  two, and it annihilated the artifact with the highest audience agreement in the set.

---

## §5. Blocked

**The API arm (H1.5) could not run: no credentials.** `ANTHROPIC_API_KEY` is unset and the `ant`
CLI is not installed. This matters more than it did before §3 — the reference arm is how we
separate *"a 9B model cannot see enacted decisions"* from *"the prompt never asks it to."* Those
need different fixes and the local arm alone cannot distinguish them.

---

## §6. Next, in order

1. **Rewrite stage B** to ask for the road not taken rather than for alternatives, and rewrite
   `support` to score it. This is the redesign.
2. **Re-run the local arm** against the same three artifacts. If A's support rises and C's falls,
   the diagnosis in §3 is confirmed.
3. **Run the API arm** once credentials exist, to bound §3 against model capability.
4. Only then re-test C-18.

**No fit number leaves this repository.** The audience result in §2 may be cited with its scope
paragraph attached; nothing else may.
