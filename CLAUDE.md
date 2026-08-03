# Working notes for an agent picking this up

**Read [`docs/STATE.md`](docs/STATE.md) first.** It is written to survive a context compaction and
is the only file that has to be current.

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
