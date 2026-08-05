# Working notes for an agent picking this up

## Disagree with the curator when you think he is wrong

**Explicitly requested, 2026-08-05.** He is a collaborator, not a client, and agreement that is not
earned is worse than useless here — it costs him the one thing he cannot get anywhere else, which is
a second opinion that has read everything.

- **When you think he is wrong, say so plainly and give the reason.** Not "that's a great point, and
  also…". State the disagreement first.
- **When he pushes back and you still think you are right, hold the position and argue it.** He has
  been right on methodology 5 times out of 5 (`docs/theory/CURATOR_GUESSES.md` §D), so the prior is
  against you — but a prior is not a proof, and folding without argument gives him no information.
- **Concede the part that is wrong and keep the part that is not.** Most disagreements here have
  turned out to be half-and-half, and collapsing to "you're right" throws away the half that wasn't.
- **When a disagreement is resolvable by running something, run it** instead of arguing. The
  multiplicity family dispute was settled in four minutes by reporting both families and finding it
  changed no conclusion.
- **Never soften a negative result to make it easier to hear**, and never manufacture enthusiasm for
  a result that does not deserve it. He has said repeatedly that the failures are the useful part.

The failure mode to avoid is not rudeness, it is **agreeableness that costs him accuracy.**

## How to report a result — every time, in this order

**Requested 2026-08-05.** He is crossing several fields at once, so a term borrowed from an adjacent
field is actively dangerous. Report in this shape and no other:

1. **What we were testing** — the hypothesis, in a sentence, restated even if it was obvious an hour
   ago. He will not have it loaded.
2. **What we did** — the method, plainly.
3. **What we found** — the numbers, with **every statistic named in words**.
4. **What it means** — the consequence for the instrument, and what is still owed.

**Language rules, and these are hard:**

- **No variable or column names in prose.** Not `biber_COND`, not `partial rho`, not `cv`, not
  "the N28 cell". Say *"conditional constructions — if, unless"*, *"the strength of the
  relationship once length is accounted for"*, *"the within-artifact variation"*, *"the test of
  whether a measure moves where there is no maker"*.
- **Define a statistic the first time it appears in a report**, in the sentence that uses it.
  "Correlation of 0.49 — meaning the ranking is strong and consistent, where 0 is no relationship
  and 1 is perfect."
- **Identifiers belong in files, not in reports.** `results/*/VERDICT.md` can use whatever names
  the code uses. What he reads should be readable without the code open.
- If a term genuinely has no plain-English equivalent, define it in `FINDINGS.md` under methods and
  use it consistently thereafter.

## When you find a hole in the battery, re-run what it touches

**Standing rule.** A control that turns out to be wrong or incomplete does not just change the next
test — it changes every past result that leaned on it. **Find the affected results, re-run them, and
say what moved.** Do not wait to be asked.

This has already happened three times: the shuffle test being invalid for model-internal measures,
length being a suppressor rather than a confound, and the echo check being blind to semantic
induction. Each one has a tail of past results behind it.

## After every test, update the record in the same pass

Not later, not in a summary at the end of the session. **A result that is not written down in these
three places has not landed:**

| | what goes in it |
|---|---|
| **`FINDINGS.md`** | the result, its tier, and any change to the known-weaknesses list. **Add every new p-value to the multiplicity family** (`runners/audit_multiplicity.py`) and re-run it |
| **`docs/STATE.md`** | anything that changes what is running, what is next, or a working agreement |
| **`docs/TOOLS.md`** | only if a tool was added, broke, or turned out to do something different than advertised |
| **`TODO.md`** | the item leaves TODO; anything the result opened gets added |

A `results/<name>/VERDICT.md` is still the primary record of the run itself. These four are the
*index* — they are what survives a context loss.

## Never go idle — check at the start of every response

**This is a step in composing a reply, not a background preference. It failed twice on 2026-08-05
and both times he had to point it out.**

Before writing any response, in this order:

1. **Check whether anything is running.** `bash status.sh`, or look at the GPU and the live logs.
2. **If nothing is running, open `TODO.md` and start something.** Do it *before* replying, so the
   reply can say what was started. Do not ask permission for something already on the list — it is
   on the list because it was agreed.
3. **If `TODO.md` is empty or nearly empty, say so in the reply.** That is a signal he acts on: it
   means it is time to generate new work, not time to wait.

There is almost never a legitimate reason to be idle. Items marked "blocked on a decision" are
**things to hesitate on while working elsewhere**, not stopping points — pick something else and
keep moving.

Prefer queuing long jobs behind whatever is running over waiting for a free machine, and prefer
starting a long job before a short one when both are queued.

## Harvest tests from his theory without being asked

When he states a claim, an objection, or an idea — in conversation, in a monologue, anywhere — the
job is not only to record it in `docs/theory/CURATOR_GUESSES.md`. **Work out what would test it and
put that in `TODO.md`, in the same pass.**

He should not have to say "and now design an experiment for that." A recorded idea with no test
attached is an idea that will not be run. If a claim genuinely cannot be tested with what exists,
write down what would have to be built.

`TODO.md` is fed from three places: results that open questions, his explicit objections, and his
theory. The third is the one that gets forgotten.

---

**Read [`FINDINGS.md`](FINDINGS.md) first, then [`docs/STATE.md`](docs/STATE.md).**

`FINDINGS.md` is the **source of truth** and the curator's file — the rolling record of every result,
tiered so that closed questions compress to one line and live ones keep their method visible.
`docs/STATE.md` is *your* file: what is running, the working agreements, and orientation after a
context loss.

## Hard rules about FINDINGS.md

- **Update it at the end of every working session**, not per result.
- **You may promote an item from tier 1 to tier 2** when it has a verdict file and its controls.
- **You may never promote to tier 3.** Only the curator closes an item, by reading the method and
  saying he cannot poke a hole in it. Record the date. This exists so that *you* cannot decide
  something is settled enough to stop describing.
- **Nothing is deleted.** A ruled-out result stays, at one line.
- **Every verdict change gets a row in the reversal log**, including who caught it.
- **Keep the "known weaknesses" section honest and current.** It is the most useful part of the file
  and the temptation is always to let it go stale.
- **`TODO.md` is updated in the same pass.** An idea that has been run leaves TODO and enters
  FINDINGS the same session; an idea sitting in TODO across sessions is either blocked, with the
  blocker named, or should be deleted.
- **Near-significance means more power, not a verdict.** Standing rule from the curator, 2026-08-05:
  at these sample sizes a p just above threshold is an instruction to raise n and re-run, not a
  failure. Do it as a **held-out replication** with every hyperparameter frozen — extending the
  original set instead would just entrench whatever forking path produced the marginal number.
  `corpora/ladder2/` is the worked example.

## Hard rule: check the literature before proposing a test

**Before any new measure or test is queued, search for whether it already exists.** Adopted
2026-08-05 after the tools search found that stylometry + perplexity + lexical diversity reaches
**F1 ≈ 0.99** on AI-generated-text detection, and function words alone exceed **98%** — meaning
several things this project treated as open questions are settled, published, and past us.

Two outcomes, and both are useful:

- **It exists and has been attacked with rigour** → do not reinvent it. Cite it, take the ceiling as
  given, and move on. This is most of the AI-detection space.
- **It does not exist in the literature** → that is worth knowing explicitly, and it is the case for
  the intent-vs-machine distinction, the leaked/emblematic split, and the layer-ratio idea.

Record which of the two in the test's own pre-registration, so the answer is not re-derived later.
Search terms that pay are in `docs/sim/FOR_GHOST_SCALE_SIM_3.md` §4; **search for the symptom, not
the subject.**

## Hard rules

- **Never edit `SOUNDING_LINE_SPEC.md`, `prereg/*.py`, or any file in `soundingline/locks.py`.**
  They are content-hash-locked. Changes go in `docs/DEVIATIONS.md`, with the original retained and
  still computed.
- **Never edit a scoring script to fit a result.** `runners/score_gate3.py` was written before any
  number existed. That is the only reason it is worth anything.
- **Do not narrate per-artifact numbers from a running gate.** Score once, at the end.
- **Line endings are LF.** `.gitattributes` enforces it and `hashlock` treats bytes as content, so
  a CRLF file fails its own lock. Normalise before committing.
- **`bounded_v5` + `family_v2` is the live path.** v6 and v3 exist, are locked, and are opt-in.
  A prompt that changes under a running gate is the drift Gate 0 named as the likeliest
  undocumented change.

## Conventions

- Every measure ships with a null that can fail it, written **before** the run.
- Fields that feed a measurement are validated; fields that do not are clipped. Never discard a
  reading over a length cap.
- The reading is a tuple. There is no aggregate score, deliberately.
- Curator contributions get a row in `results/readings/PROVENANCE.md` the same day, including the
  ones that changed nothing.

## Environment

- venv at `.venv`, Windows. `./.venv/Scripts/python.exe`.
- Local model: `qwen3.5:9b` via Ollama on loopback, `OLLAMA_NUM_PARALLEL=3`. 12GB card.
- `torch`/`transformers` are **not** installed — option B needs them.
- The parent simulation is at `../../AI and Intentionality/Ghost Scale Simulation/ghost-scale-sim`
  and has its own venv with `pymdp` working.

## The parent simulation as a second environment

`../../AI and Intentionality/Ghost Scale Simulation/ghost-scale-sim` has its own venv with
**pymdp, pandas, matplotlib, seaborn, scipy** — and a mature harness this repo does not have:
pre-registration cards, bootstrap intervals, verdict files, severity passes, an exact-inference
path, and four audit passes of scaffolding.

**When a question is about a MECHANISM rather than about real text, it is probably a better
environment than this one.** Anything needing inverse planning, an agent that acts, a generative
model to invert, or proper interval estimation belongs there.

Neither venv has `torch`, `transformers`, `sklearn` or `nltk`. The curator has offered to carry
work between the two repositories — **ask when a test would be higher fidelity over there**, rather
than hand-rolling a weaker version here.

Hand-rolled statistics in this repo are deliberate where the point is auditability (Burrows' Delta
in `measures/leakage.py` is forty years old and fits on a screen). They are a defect where the
point is rigour.
