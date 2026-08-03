# D, costed honestly

**You said you don't trust my estimate. You were right not to.** I said "years, not weeks" without
looking at what already exists. Here is the version done against local information.

---

## §1. D is mostly already built, in the other repository

**D = a generative model of maker → artifact, inverted with Bayes.** Baker/Saxe/Tenenbaum inverse
planning, which is what the essay's appreciation-as-IRL already is.

`ghost-scale-sim` implements exactly this and it runs:

| piece | file | state |
|---|---|---|
| maker as a POMDP that emits features from a goal | `creators.py :: HumanCreator` | **done** |
| observer that infers a goal posterior from emissions | `observer.py :: rollout_observer` | **done** |
| generative model, A/B/C/D construction | `generative_model.py` | **done** |
| exact inference | `exact.py` | **done** |
| pymdp installed and working | its venv | **verified just now** |

**The inversion machinery is not the work.** It exists, it has four audit passes behind it, and it
is the thing this project was spun out of.

---

## §2. The actual gap is one function

The sim inverts over **synthetic feature vectors**. Artifacts are text.

So D reduces to a single question:

> **What maps real text to a feature vector this machinery can invert?**

And §1 of `LEAKAGE.md` just answered a large part of it. **Function-word distributions are a
feature vector** — low-dimensional, topic-independent, non-conscious, and structurally the same
kind of object as the sim's `sig[g]`: an emission distribution over a fixed alphabet, produced by a
maker in a state.

That is a much better fit than a text embedding, which is high-dimensional, topic-dominated, and
has no generative story.

---

## §3. The blocker, and the cheap way round it

To invert `P(features | maker state)` you need it. The sim *constructs* it from a goal signature.
For real text you would have to **learn** it — from artifacts with known maker states, which do not
exist and are what C-14 has owed since the beginning.

**The way round: use the LLM as the forward model.**

Ask the model to *write* an artifact under a specified state — purpose × affect × depth — extract
its function-word vector, repeat across the state space. That gives `P(features | state)`
empirically. Then invert it with the machinery that already exists.

Synthetic forward, real inverse. **Which is exactly what the sim does, with an LLM in place of the
pymdp creator.**

---

## §4. The number

| stage | work | wall clock |
|---|---|---|
| function-word extractor | public category lists, no ML | **hours** |
| **the gating test (§5)** | ~200 generations | **~2 hours GPU** |
| forward model over a reduced state space | 8 purpose × 8 affect × 3 depth = 192 cells × 5 = 960 gens | **~6–8 h GPU** |
| port the inversion | pymdp is installed next door; A-matrix from measured emissions | **1–2 days** |
| N28-analogue: generate from a no-maker process, posterior must stay flat | reuses §4 | **hours** |
| validation against the curator's readings | session 01 + 02 already collected | **hours** |

**A first runnable D: 2–3 days of my working time, GPU-bound, not thinking-bound.**
**A D worth reporting: 1–2 weeks**, most of it validation.

Not years. I was wrong by roughly two orders of magnitude, and the reason is worth naming: I costed
it as *inventing inverse planning* when the local information said *porting a working
implementation from a repo on the same disk*.

---

## §5. One cheap test gates the entire thing

Before any of §4 beyond row two:

> **D-0.** Have the model write N artifacts under specified maker states. Do their function-word
> vectors **separate by state**?
>
> - **Yes** → the emission model exists, D is engineering, proceed.
> - **No** → function words carry maker identity but not maker *state*, the feature channel is
>   wrong, and D dies for **two hours of GPU** instead of two weeks.

This is the N28 discipline applied before the build rather than after. It is the single highest
value-per-hour thing on the whole list, including A, B and C.

**And it has a second reading.** If function-word vectors separate by state *in LLM-generated
text*, that is also E38 in a new place — the model's own emissions may be more separable than human
ones. So D-0 must be re-run on human artifacts with known-ish states, which is what session 01 and
02 are.

---

## §6. B, also re-costed

I said "needs a hook into Ollama we do not have," which was true and beside the point. Ollama is
not the only way to run the model.

`transformers` + `torch` are **not installed** in this venv. Installing them and loading a 9B in
fp16/int8 on a 12GB card with output-hidden-states is **an afternoon**, not a project. The
mechanistic-interpretability method is published: extract emotion directions, probe mid-layer
activations, read valence/arousal.

**B is days, not months.** The real cost is VRAM contention with Gate 3, which is a scheduling
problem.

---

## §7. Revised recommendation

**A, B, C, D — and D-0 first**, because it is two hours and it decides whether D is real.

Order by value per hour:

1. **D-0** — 2h GPU, gates everything downstream
2. **A** — function-word leakage, hours, no GPU, runs on the corpus we have
3. **C** — stage E kept and re-scoped as emblematic-only; already built
4. **B** — transformers + activation readout, an afternoon plus VRAM scheduling
5. **D** — 2–3 days to runnable, given D-0 passes

Everything except B and D-0 is CPU-only and can run beside Gate 3 right now.

---

## §8. What this is for, in your framing

**Detect depth → give empathy → extract values.** Three parts of one thing, and the third is the
alignment goal the essay's appendix already names.

D is the piece that makes the second two possible, because inverse planning over artifacts *is*
the "juiced-up inverse reinforcement learning" the essay asks for. Sounding Line measuring depth
and Sounding Line extracting values are not two projects that drifted into each other. **They are
the same inversion, read out at two different levels.**
