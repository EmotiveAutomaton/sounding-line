# Stage 6 dependency audit (Stage 7 record gate)

Written 2026-09-02T10:34:16. The Stage 6 raw outputs and packet are untouched; this file classifies them.

## Dispositions (D03)

| card | class | why |
|---|---|---|
| I01 | CLEAN | infrastructure receipt; no prediction path |
| I02 | CLEAN | infrastructure receipt; no prediction path |
| I03 | CLEAN | infrastructure receipt; no prediction path |
| I04 | CLEAN | infrastructure receipt; no prediction path |
| I05 | DEPENDENCY_TAINTED | the supplied-state gate realized the state through predictive_at_cut on the live world (target_actions, events, stop_shift, trajectory length) |
| I06 | CLEAN | infrastructure receipt; no prediction path |
| I07 | CLEAN | infrastructure receipt; no prediction path |
| I08 | CLEAN | infrastructure receipt; no prediction path |
| I09 | CLEAN | infrastructure receipt; no prediction path |
| I10 | CLEAN | infrastructure receipt; no prediction path |
| M01 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M02 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M03 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M04 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M05 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M06 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M07 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M08 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M09 | CLEAN | the exact oracle ceiling (construction, never a competitor) |
| M10 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M11 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M12 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M13 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M14 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M15 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| M16 | DEPENDENCY_TAINTED | non-oracle arms ['AD', 'CR', 'D', 'EX', 'GS', 'L', 'LD', 'TT'] reach hidden fields through realize -> predictive_at_cut |
| C01 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| C02 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| C03 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| C04 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| C05 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| C06 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| C07 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| C08 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| C09 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| C10 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| C11 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| C12 | DEPENDENCY_TAINTED | records reader cards depend on T02's loader or on tainted realization |
| A01 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| A02 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| A03 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| A04 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| A05 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| A06 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| A07 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| A08 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| A09 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| A10 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| A11 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| A12 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| A13 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| A14 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| V01 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| V02 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| V03 | DUPLICATE_ESTIMAND | identical per-unit primary vector with ['V02'] |
| V04 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| V05 | DUPLICATE_ESTIMAND | identical per-unit primary vector with ['V04'] |
| V06 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| V07 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| V08 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| V09 | DUPLICATE_ESTIMAND | identical per-unit primary vector with ['F02', 'F03', 'F09'] |
| V10 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| V11 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| V12 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| V13 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| V14 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| F01 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| F02 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| F03 | DUPLICATE_ESTIMAND | identical per-unit primary vector with ['F02'] |
| F04 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| F05 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| F06 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| F07 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| F08 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| F09 | DUPLICATE_ESTIMAND | identical per-unit primary vector with ['F02', 'F03'] |
| F10 | CLEAN | exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts |
| F11 | DEPENDENCY_TAINTED | reader cards realized supplied or inferred states through the live world object |
| F12 | DEPENDENCY_TAINTED | records reader cards depend on T02's loader or on tainted realization |
| P01 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P02 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P03 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P04 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P05 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P06 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P07 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P08 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P09 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P10 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P11 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| P12 | DEPENDENCY_TAINTED | scores adapted predictions produced by tainted arms (M08 rows) |
| T01 | CLEAN | narrow negative under reader-free, lineage-clean baselines pending D09 |
| T02 | CONSTRUCTION_INVALID | the CoAuthor loader consumed suggestion-select as a delta before the acceptance branch; every scored decision was a dismissal (§2.1.8) |
| T03 | CLEAN | narrow negative under reader-free, lineage-clean baselines pending D09 |
| T04 | CLEAN | narrow negative under reader-free, lineage-clean baselines pending D09 |
| T05 | CLEAN | narrow negative under reader-free, lineage-clean baselines pending D09 |
| T06 | DEPENDENCY_TAINTED | records reader cards depend on T02's loader or on tainted realization |
| T07 | DEPENDENCY_TAINTED | records reader cards depend on T02's loader or on tainted realization |
| T08 | CLEAN | narrow negative under reader-free, lineage-clean baselines pending D09 |
| T09 | CLEAN | narrow negative under reader-free, lineage-clean baselines pending D09 |
| T10 | CLEAN | narrow negative under reader-free, lineage-clean baselines pending D09 |
| B01 | DEPENDENCY_TAINTED | confirmation of a tainted discovery claim, or a ledger over tainted verdicts |
| B02 | DEPENDENCY_TAINTED | confirmation of a tainted discovery claim, or a ledger over tainted verdicts |
| B03 | CLEAN | read-only Ghost bridge ledger (CLEAN) |
| B04 | DEPENDENCY_TAINTED | confirmation of a tainted discovery claim, or a ledger over tainted verdicts |
| X01 | DEPENDENCY_TAINTED | covers ['M15', 'M08']: ['DEPENDENCY_TAINTED'] |
| X02 | DEPENDENCY_TAINTED | covers ['I08', 'M02']: ['CLEAN', 'DEPENDENCY_TAINTED'] |
| X03 | DEPENDENCY_TAINTED | covers ['M02', 'M03', 'M08']: ['DEPENDENCY_TAINTED'] |
| X04 | DEPENDENCY_TAINTED | covers ['M04', 'V06']: ['DEPENDENCY_TAINTED'] |
| X05 | DEPENDENCY_TAINTED | covers ['P09', 'F01']: ['CLEAN', 'DEPENDENCY_TAINTED'] |
| X06 | CLEAN | covers ['V01', 'V02']: clean |
| X07 | CLEAN | covers ['V09', 'A06']: clean |
| X08 | CLEAN | covers ['I04']: clean |
| X09 | DEPENDENCY_TAINTED | covers ['I08', 'M01']: ['CLEAN', 'DEPENDENCY_TAINTED'] |
| X10 | DEPENDENCY_TAINTED | covers ['M05', 'M08']: ['DEPENDENCY_TAINTED'] |
| X11 | DEPENDENCY_TAINTED | covers ['I07', 'M08']: ['CLEAN', 'DEPENDENCY_TAINTED'] |
| X12 | DEPENDENCY_TAINTED | covers ['M16', 'P11']: ['DEPENDENCY_TAINTED'] |
| X13 | CLEAN | covers ['C01', 'F01']: clean |
| X14 | CLEAN | covers ['T08']: clean |
| X15 | DEPENDENCY_TAINTED | covers ['A13', 'T06']: ['CLEAN', 'DEPENDENCY_TAINTED'] |
| X16 | CLEAN | covers ['V13', 'A13']: clean |
| X17 | DEPENDENCY_TAINTED | covers ['A07', 'T07']: ['CLEAN', 'DEPENDENCY_TAINTED'] |
| X18 | CLEAN | covers ['A02', 'A03', 'A04']: clean |
| X19 | CLEAN | covers ['F02', 'F04']: clean |
| X20 | CLEAN | covers ['F06']: clean |
| X21 | DEPENDENCY_TAINTED | covers ['P03', 'M12']: ['DEPENDENCY_TAINTED'] |
| X22 | DEPENDENCY_TAINTED | covers ['A12', 'V07']: ['CLEAN', 'DEPENDENCY_TAINTED'] |
| X23 | DEPENDENCY_TAINTED | covers ['P12', 'B04']: ['DEPENDENCY_TAINTED'] |
| X24 | DEPENDENCY_TAINTED | covers ['I10', 'B04']: ['CLEAN', 'DEPENDENCY_TAINTED'] |

*Table: one row per Stage 6 card and attack; class is one of the five audit classes; why names the evidence.*

Class counts: {"CLEAN": 59, "DEPENDENCY_TAINTED": 63, "DUPLICATE_ESTIMAND": 5, "CONSTRUCTION_INVALID": 1}.

## Suspended conclusions (D04)

- **architecture_ranking**: the nine-arm tournament (L over D +0.945 and every arm contrast): every non-oracle arm predicted through the exact realizer on the live world object; SUSPENDED (D04)
- **reader_boundary**: the supplied-true-state gate and the 'reader boundary' (I05; event/cue reads pay, latent inference nulls): the supplied state was a prose goal, controller label, and remaining count realized by the constructor, not an operative supplied state; SUSPENDED (D04)
- **M14_realization**: contextual realization beats copied realization (+2.187): fresh realization received the new world's constructor variables; close to tautological; SUSPENDED (D04)
- **M15_semantic_invariance**: paraphrase-invariant realization (TV 0.000 vs 0.425): predictions preserved through the hypothesis tag while paraphrase semantics were ignored; SUSPENDED (D04)
- **coauthor_T02**: CoAuthor accept/dismiss prediction (-0.368): the loader recorded no acceptance; INVALID (D04, D07)
- **retained**: exact supplied-family likelihood selection, renamed supplied-law selection / known-model system identification (D05); construction facts from reader-free world statistics; the narrow natural negatives pending D09

## Decomposition recomputed from committed rows (D02, descriptive)

| quantity | value |
|---|---|
| n_units | +128.0000 |
| direct_D | -2.0272 |
| equal_mix_exact | -1.0840 |
| label_weights_L_recomputed | -1.0837 |
| L_committed | -1.0819 |
| exact_posterior_mix | -1.0173 |
| CR_committed | -1.1013 |
| OR_committed | -0.9952 |
| delta_equal_mix_minus_D | +0.9432 |
| delta_label_weights_minus_equal | +0.0003 |
| delta_exact_adaptation_minus_labels | +0.0663 |
| delta_CR_minus_L | -0.0195 |

*Table: combined prospective primary (mean per unit) for the direct arm, the equal exact mixture, the label-weighted mixture, the exact-posterior mixture, and the committed L, CR, and oracle rows, with their differences; the brief's cited numbers sit in the JSON beside them.*

## Supplied-law selection (D05)

Exact selection among the four supplied controller laws: MAP accuracy 0.789, mean mass on truth 0.717; the label reader: MAP 0.297, mass 0.261 (marginal 0.25; n 128). This is known-model system identification, retained under that name only.

## Access graph (D01)

Direct hidden reads: {"realization.predictive_at_cut": ["cut", "events", "target_actions", "trajectory"], "realization.realize": ["cut", "events"], "realization._selftest": ["hidden"], "architectures.arm_D": ["hidden"], "architectures.arm_TT": ["cut"], "architectures._fit_markov_policy": ["trajectory"], "architectures.arm_EX": ["cut", "trajectory"], "architectures.arm_AD": ["cut", "trajectory"], "architectures._selftest": ["trajectory"], "worlds._stop_prob": ["stop_shift"], "worlds.simulate": ["events", "target_actions"], "worlds.trajectory_log_lik": ["events", "target_actions"], "worlds.make_process_world": ["cut", "events", "hidden", "target_actions", "trajectory"], "worlds.hidden_targets": ["cut", "trajectory"], "worlds.changed_context_dist": ["cut", "trajectory"], "worlds.oracle_posterior": ["cut", "trajectory"], "worlds.oracle_state": ["cut", "events", "target_actions", "trajectory"], "worlds.cheap_baselines": ["cut", "trajectory"], "worlds.render_evidence": ["cut", "trajectory"], "worlds.render_artifact": ["cut", "trajectory"], "worlds._selftest": ["cut", "hidden", "trajectory"], "engines.run_I04": ["trajectory"], "engines.run_I05": ["hidden"], "engines.run_I09": ["trajectory"], "engines._tournam

Arm transitive reach: {"D": ["cut", "hidden", "trajectory"], "L": ["cut", "events", "stop_shift", "target_actions", "trajectory"], "LD": ["cut", "events", "stop_shift", "target_actions", "trajectory"], "TT": ["cut", "events", "stop_shift", "target_actions", "trajectory"], "GS": ["cut", "events", "stop_shift", "target_actions", "trajectory"], "EX": ["cut", "events", "stop_shift", "target_actions", "trajectory"], "AD": ["cut", "events", "stop_shift", "target_actions", "trajectory"], "CR": ["cut", "events", "stop_shift", "target_actions", "trajectory"], "OR": ["cut", "events", "stop_shift", "target_actions", "trajectory"]}

Dynamic trace, keys the exact realizer touched: ["cut", "events", "stop_shift", "target_actions", "trajectory"]; the renderer: ["cut", "trajectory"].

## Identity matrix (D06)

Identical per-unit vectors: [('F02', 'F03'), ('F02', 'F09'), ('F02', 'V09'), ('F03', 'F09'), ('F03', 'V09'), ('F09', 'V09'), ('V02', 'V03'), ('V04', 'V05')]; identical verdict points: [('A14', 'V13'), ('F02', 'F03'), ('F02', 'F09'), ('F03', 'F09'), ('V02', 'V03'), ('V04', 'V05'), ('V04', 'V09'), ('V05', 'V09')].

