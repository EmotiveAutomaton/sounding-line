# CH census successor: independent prefix verification

**DESIGN CHECK — 2026-11-07.** LESSONS §§2–5: a copied checkpoint is execution state, not independent evidence. The live `week5_ch_source.py` stays byte-identical. Its execute handler may resume an authenticated SQLite checkpoint; its original verifier propagates `resume_frame`, so copied prefixes need separate validation.

`week5_ch_census_replay.py` delegates execution unchanged and independently verifies from source ordinal zero in a fresh SQLite database. It deliberately excludes `resume_frame`, compares complete source counts, schemas, and every ordered row in frame, openings, opening_positions, histories, checkpoints and settings. Salt and source pins remain unchanged. No successful suffix replay certifies a copied prefix.

The native fixture supplies an honest prefix and a falsified prefix with a freshly matching SHA-256; only the honest whole result may verify. Fresh-process replay also proves a requested verifier yield produces a sealed partial checkpoint without a verified terminal. The partial verifier database is not automatically trusted or reused: a new attempt starts verification at ordinal zero unless a separately reviewed verification-prefix protocol is later admitted. This qualification is included in the checkpoint.

Whole execute-plus-replay cost, all predecessor cost, the CH family ceiling and campaign clocks apply. Resource and slot policy is unchanged. Root admission must allow the full independent replay, not only the remaining execution suffix. This changes execution assurance only; no source eligibility, clock, sample or scientific estimator changes.
