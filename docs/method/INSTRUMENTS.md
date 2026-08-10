# Instruments: the tools ledger

Finished tools and their validation state, one row each. Results that adjudicate *claims* go to
`docs/theory/`; results that validate or break *instruments* land here, with the full record in
`FINDINGS.md`. Created 2026-08-10 at the curator's instruction as the home for finished tools.

| instrument | what it is | state |
|---|---|---|
| **the event-recovery harness** (`run_event_harness.py`, G130) | synthetic decision events, five known-answer gates, the code path every choice-recovery test runs through | **VALID (L56).** Two of its gates caught real faults during its own build (a mis-specified decoy arm; deterministic tie-breaking) |
| **candidate-set construction** (`run_arg_recovery.py`, G129 pilots) | bounded candidate sets for purpose recovery | **TWO LESSONS BANKED (L62/L64).** The blind floor follows the truth's label marginal regardless of decoy scheme; the estimand is the margin over the measured floor; truth-balanced subsampling (pilot-c) makes the floor analytic |
| **covariate matching** (`run_arg_matched.py`, G130b) | content/surface matching for the lexical-shortcut control | **v1 FAILED ITS OWN BALANCE GATE (L64), correctly.** Greedy 1:1 with caliper cannot balance these covariates (SMDs to 1.29 before, 0.49 after); v2 is coarsened exact matching |
| **the exact-replication pipeline** (`run_arg_replication.py`, G136) | their features, their encoder, their classifier grid, their folds | **NOT MATCHED in v1.** Binary within 0.02 to 0.06 of the published cells, fine off by 0.16+; label-conflicting duplicates from multi-purpose splitting are the prime suspect; v3 extraction (first purpose only, per-cycle n audit) queued |
| **the maze-world models** (`run_bst_gridworld.py`, G137) | exact value iteration, three inverse-planning models | **GATES-PASSED (L63).** Analytic gates all pass; figure-level half owed |
| **the impossibility toy** (`run_am_construction.py`, G138) | enumerable reward × planner posterior with prior relaxations | **RECREATED+NARROWS (L60), exact at the degeneracy** |
| **the loop scripts** (`run_forever_day.sh` / `run_forever_night.sh`, G121) | winpid locks, tree kills, orphan sweep, PATH self-repair | **HARDENED AND LIVE-VERIFIED.** Cross-session refusal works; a seven-process tree kill witnessed; the bare-launch PATH fault found when the first night launch died at birth and fixed in-script |
| **the window feature cache** (`build_features.py`) | corpus features at chosen window sizes | **REPAIRED TWICE (L43).** Default-argument binding and NaN guards; takes `--corpora` (plural), which one night stage learned the hard way |
| **the CKA implementation** (`run_cka_alignment.py` family) | linear CKA with permutation null | **SANITY-PASSED (L61)** at machine precision, with the regime caveat banked: independent noise scores 0.985 at thirty samples in two thousand dimensions, so only null-tested structure is ever quoted |
