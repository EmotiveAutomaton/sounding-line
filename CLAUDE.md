# Working notes for an agent picking this up

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
