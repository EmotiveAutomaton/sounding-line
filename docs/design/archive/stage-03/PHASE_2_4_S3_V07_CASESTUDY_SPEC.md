# E24-S3-V07 · Barrett / Panksepp case-study specification (SPEC ONLY — no execution)

**Status: specified 2026-08-24. This document is the deliverable for V07; the study runs
only if the curator ratifies it after the A-trunk lands.**

## Why these two accounts, and why as a case study

The A trunk builds action-tendency structure (fear/anger/curiosity/care) in model
activations and tests its causal use. Two live theories of affect make DIFFERENT
predictions about what that construction should look like, and the A-trunk outputs land
exactly on their disagreement:

- **Panksepp (basic affect systems).** Discrete, evolutionarily old systems (FEAR, RAGE,
  SEEKING, CARE — the mapping to our four tendencies is deliberate). Prediction: the
  tendency geometry should be **discrete and modular** — A03's winner should separate all
  four with sharp boundaries; A05's blends should read as superpositions of two fixed
  components; A04's fear/anger split should be as clean as any other pair; A07 steering
  should move behavior along one system without dragging the others.

- **Barrett (constructed emotion).** Affect categories are constructed from a
  low-dimensional core (valence × arousal) plus conceptual context. Prediction: the
  geometry should be **dominated by continuous core dimensions** — the valence direction
  (A02) should carry much of the tendency separation; A04 should show fear/anger
  separating mainly where a second core dimension (approach/withdrawal or arousal) is
  available, not as dedicated directions; A05 blends should sit on a continuum rather
  than resolving into two components; A07 steering along "one tendency" should produce
  graded, context-dependent shifts.

## The discriminating table (to be filled from landed A cells, no new runs)

| observable | Panksepp-shaped | Barrett-shaped | source cell |
|---|---|---|---|
| 4-way decode geometry | 4 compact clusters | a 2D fan (valence × approach) | A03 |
| fear vs anger | separates like any pair, valence axis quiet | separates only via a second continuous axis | A04 |
| blends | top-2 superposition wins | intermediate points, top-2 no better than nearest-1 | A05 |
| suppression | tendency survives (system still active) | tendency fades with expression (construction suppressed) | A06 |
| steering | one-tendency shifts, others unmoved | graded shifts dragging correlated categories | A07 |

## Rules

- **X09 stands**: no clinical or identity labels; this is a claim about model geometry
  read through two published theories, never about any person.
- The case study CITES both accounts from fetched primary sources (READ grade) before any
  row is filled; the adversarial-search rule applies (criticism of each account goes in).
- The output is one comparative essay in `docs/theory/essays/` plus one row per theory in
  the affect section — it makes no new claims, it classifies existing landed results.
- If the A trunk's cells close instrument-limited, V07 reports that the discriminating
  table cannot be filled and why — a null with its mechanism named, not a verdict on the
  theories.
