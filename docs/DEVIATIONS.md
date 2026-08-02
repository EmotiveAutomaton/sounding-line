# Deviations

**Every deviation is logged where it happened.** Carried from the Ghost Scale Simulation, where
the practice caught four separate criteria that turned out to be unable to do their own job — each
found by a later pass, and each retained and still computed rather than replaced.

## The rule

When a hash-locked artifact changes:

1. **Record it here**, before the change is made, with the reason.
2. **Retain the original** and keep computing it.
3. **Report it as failing if it fails.** A criterion rewritten after seeing a result and then
   reported as passing is the one thing this project cannot do.

Updating a lock hash without an entry here is a defect, not a shortcut. `soundingline/hashlock.py`
raises rather than warns for this reason.

## Amendments to the spec

`SOUNDING_LINE_SPEC.md` is pre-registered and is **not edited**. Amendments live in
[`gate0/LITERATURE.md` §8](gate0/LITERATURE.md) — A-1 through A-5 — because that is where they were
decided. They are indexed here so this file is the single entry point.

| id | what changed | where decided |
|---|---|---|
| A-1 | §6's novelty claim amended — bounded-family Bayesian inversion is prior art | Gate 0 §2 |
| A-2 | Gate 3 promoted; the free-form arm runs from Gate 1 in parallel | Gate 0 §2 |
| A-3 | D-4 resolved to "harden, and log" rather than "harden first, measure second" | Gate 0 §8 |
| A-4 | No fetcher until Gate 2 clears; corpora from RAID and the DFRLab audit | Gate 0 §8 |
| A-5 | The probe is hybrid — local for volume, API as quality reference | Gate 0 §8 |

## Deviations from pre-registered criteria

*None yet. Gate 1 has not run.*

| date | artifact | old hash | new hash | reason | original still computed? |
|---|---|---|---|---|---|
