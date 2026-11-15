# WEEK6 IN14 PERSON CALIBRATION 20261115

**Hypothesis.** Can shared-survey sampling covariance be removed well enough to
recover differences among writers' carry-over coefficients?

**METHOD.** Freeze the candidate and all gates in
[the prospective design](../../../docs/design/stage-15/week6/IN14_PERSON_CALIBRATION_V1.md), then run nine complete
whole-survey worlds: 600 writers per world, balanced 4/8/12 pairs, three planted
half correlations and three fixed noise families. Correct full and half
coefficient moments with their joint fitted AR(1)-by-feeling sampling covariance.
Check the complete matrix calculation against an independent dense reference,
and test shared boundaries, missing raw pair positions, rank refusal and the
hand-known correction. No human source outcome was read or computed.

**Found.** The proposed IN14 person-level reliability correction failed its completed constructed qualification; that secondary remains instrument-held.

**Completed constructed evidence.** The candidate fails three fixed correlation gates. All nine adjusted
trait relations meet their separate gate, but passing that component does not
admit an instrument whose joint gate failed. No ratio is clipped and no world
is removed. The person secondary remains instrument-held. No further sweep ran.

Each row below is one complete constructed world. The plant and recovered
values are left/right half-coefficient correlations. The trait column is the
attenuation-adjusted coefficient/N relation, whose plant is 0.4 in every row.
Both tolerances are 0.1; the final column requires both gates to pass.

| Survey noise family | Half plant | Recovered half correlation | Adjusted trait relation | Both gates |
|---|---:|---:|---:|---|
| IID recurrence innovations | 0 | 0.006911 | 0.429099 | pass |
| IID recurrence innovations | 0.5 | 0.486117 | 0.420043 | pass |
| IID recurrence innovations | 1 | 0.994139 | 0.393725 | pass |
| AR(1)=0.4 recurrence innovations | 0 | 0.079664 | 0.437229 | pass |
| AR(1)=0.4 recurrence innovations | 0.5 | 0.641803 | 0.359760 | fail |
| AR(1)=0.4 recurrence innovations | 1 | 0.997999 | 0.402792 | pass |
| Independent survey measurement noise | 0 | -0.196053 | 0.415863 | fail |
| Independent survey measurement noise | 0.5 | 0.451144 | 0.382774 | pass |
| Independent survey measurement noise | 1 | 1.122817 | 0.363668 | fail |

## Read-only diagnosis and limits

The dense independent coefficient/covariance reference agreed within the frozen
1e-8 tolerance, and the hand-known shared-boundary correction passed. All 24
other checks, including the existing IN14/IN16 checks, passed. The failing check
is recovery by the proposed statistical model, not an exception, timeout,
rank-refusal accident, dropped world or failed independent matrix calculation.
No implementation error has been identified; these checks do not prove its
absence outside their constructed coverage.

The AR(1) family estimates pooled residual phi near 0.186 to 0.193 despite
innovation phi 0.4. The measurement-noise family estimates phi near -0.066 to
-0.076. Those are fitted residual parameters, not direct estimates of raw
innovation correlation: short fitted trajectories and regressors affect them.
The hostile family has residual eta[t+1] - 0.6 eta[t], with a different covariance
shape from AR(1), and its baseline contains eta[t]. The conditional covariance
model does not model that baseline-error relation. These are concrete violated
or unverified model assumptions consistent with the failed recovery; the
aggregate report cannot apportion the error among them. It is therefore not
justified to repair this by choosing a different phi bound or another lag after
seeing the numbers. No replacement estimator is proposed or implemented here.
A replacement would require a separately named prospective design retaining
these hostile worlds and explaining its estimand and baseline-error assumptions.

This failure is confined to the corrected person candidate. The primary,
decay, shape, dose, same-valence reach and IN16 formula checks retain their own
constructed evidence. The earlier blanket empirical-control hold was withdrawn after the owner
identified Week 5 section 0.6's CoAuthor-specific scope; the
[scope correction](../../../docs/design/stage-15/week6/IN14_IN16_CONTROLS_V1.md) preserves that history. Ordinary
owner review and the Q/U/AA admission requirements remain. These constructed worlds do
not measure human carry-over, human trait relations or human sensitivity.

## Auditable run

- Pre-run source pins: `.agent-state/week6-builder-b/person-tests-20261115T104234Z-before.json`.
- Receipt: `.agent-state/week6-builder-b/person-tests-20261115T104234Z.json`,
  SHA-256 `83d93210f01cfd61125d94bb45f11735dd78cff91b04830fb751d9d3417d98e4`.
- Complete nine-world report: sibling `person-tests-20261115T104234Z-calibration.json`,
  SHA-256 `d55b742b66e69710e2bd7555d3836a884214664ea530618b549d10e661a54fcd`.
- Captured pytest output: sibling `.stdout.txt`; empty `.stderr.txt` retained.
- Command: declared venv Python, pytest on `tests/test_week6_in14_in16_v1.py`
  and `tests/test_week6_in14_person_v1.py`, `-q -p no:cacheprovider`, unique
  basetemp `.agent-state/week6-builder-b/person-pytest-20261115T104234Z`.
- Exit 1 at the preserved frozen qualification assertion; 24 other checks pass.
  Source pins unchanged during execution. Two numerical threads.
- Native Windows Job Object contains the suspended launcher before resume and
  all descendants. 180-second complete-tree deadline; no timeout. All four job
  processes exited, active count zero, no observed owned survivors after close.
- Whole-job CPU 28.1875 seconds; wall 29.8936935 seconds; peak job commit
  299,732,992 bytes; peak observed aggregate tree RSS 225,021,952 bytes.

These are fixture costs, not a forecast for 2,000 human resamples. They count
with all prior attempts inside the card/family accounting. Parent owner receives
this evidence for the full internal Week 6 write-through; no live pinned source,
runtime or companion repository was changed by this qualification.

This is pre-campaign Week 6 instrument preparation, filed with the currently active operational evidence. It does not change any human claim, the separate primary analysis, or a theory row. All failed and successful worlds and their costs remain in the record. No p-value or new hypothesis is introduced. The full findings, tools, queue, ledger, index, operations and theory-return write-through is complete in this pass.
