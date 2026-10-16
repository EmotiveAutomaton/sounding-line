# Saved-forecast convergence repair, version 2

Authorized October 15 by the curator's acceptance of the Gear 3 recommendation.
This is a CPU-only successor to T0b, using the same saved forecasts, writers,
folds, labels, invalid policy and useful-gain margin. The original remains intact.

**Question.** Did incomplete optimization materially change the calibration and
stacking comparison? Numerical convergence cannot validate label-shift assumptions.

**DESIGN CHECK.** LESSONS sections 3–5 and CONTROLS sections 1–3 read. Under
the numerical null, old and optimized forecasts agree within 1e-6 in maximum
absolute probability. Under the alternative, they differ; every original
contrast is recomputed, regardless of its sign. An optimization failure produces
an instrument failure, never a scientific negative. Constant evidence must yield
an unidentified prior without fabricated information; a known interior optimum
and a boundary optimum must pass. Malformed inputs and changed evidence refuse.

## Fixed method

For each of all four reader arms and every inner and outer writer fold, replay
the original 2,000-step EM implementation and scalar temperature fit. Verify the
saved parameters, predictions and stack weights before comparing successors.
No labels enter the label-shift optimization. Keep the original mean-training-
forecast source prior; do not substitute a claimed language-model training prior.

Independently maximize mean log((forecast / source prior) @ target prior) over
the four-class probability simplex using SLSQP, initialized at the source prior.
Use analytic derivatives, maximum 2,000 iterations and objective tolerance 1e-13.
If the first solve fails the certificate, use the fixed additional starts:
uniform and each of the four vertices. Return the first candidate that passes the complete numerical certificate;
never return an earlier uncertified candidate merely because its objective is lower. The concave objective's Frank–Wolfe gap (maximum gradient
minus prior-weighted gradient) must be at most 1e-7; the EM fixed-point residual
must be at most 1e-7, and objective cannot be worse than replayed EM by over 1e-10.
Failure of any certificate prevents the scientific summary. Preserve solver
status even when the independent mathematical certificate passes.

Reapply the unchanged scalar temperature and nested stack-weight rule to the
optimized probabilities. Recompute all original half-Brier and log-loss
contrasts, six baselines, own-versus-donor comparison, and the 0.01 useful-gain
screen. Carry the independently hashed original bias-corrected branch unchanged.
Keep complete original and successor arrays, fits, certificates and both summaries.
No tuning, selected folds, new model calls or new data. Maximum probability
change is a numerical diagnostic, not a new scientific significance test.

Intervals retain the original deterministic writer and crossed-prompt bootstrap.
They condition on fitted predictions, omit refitting uncertainty and are not
simultaneous. This remains exposed retrospective analysis, with no engine
admission, fresh confirmation, e-value or label-shift validation.

## Execution and evidence

`runners/next_round/convergence_v2.py` prepares immutable source/input pins and a
unique claim under `results/phase_2_4_stage_15/raw/t0b-convergence-v2/`.
One CPU thread, below-normal priority, RAM/commit floors 8 GiB, disk floor
20 GiB, maximum two hours. Native identity and final/failure/disappearance
monitoring precede computation. Changed pins, duplicate attempt or unmet
resources refuse; no automatic retry. Completion requires independent manifest
and certificate verification plus the full internal write-through before ACK.

Prior work: [Guo et al., section 4 read](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf)
separates calibration from evaluation;
[Yao et al., section 1.3 read](https://arxiv.org/html/1704.02030v3) fits stacking
on out-of-sample predictions. This is an audit of our existing implementation,
not a new calibration method or a rerun of the paid reader study.

Version 1 and its selector failure are retained. The numerical threshold, source prior, objective, all folds and full scientific contrasts are unchanged.
