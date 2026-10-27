# PP3: bounded first-generation follow-ups

Registered after the complete parent and before any follow-up outcome, under
Week 3 section 0.3.C. The parent is `S15-PP3-20261026`. Each card retains every
released row, the source and feature definitions, held-project partitions,
fixed class lists, both complete 200-draw outcome-reassignment banks, paired
2,000 author and 2,000 project bootstrap resamples, and the training prior.
No new dataset or human data collection is involved. No descendant follows
these cards. Each card has its own ceiling of 3,600 CPU seconds including
construction, tests, native validation, timing and independent replay.

- **PP3.s, specification curve.** Vary the fixed ridge penalty to 0.1 and 10,
  retaining the parent's penalty-1 result as a labelled historical anchor,
  not a new independent replication. Rationale: establish whether the scoped
  accuracy claim depends on one regularization choice. The primary is the
  smaller process-only excess over the better prior/reassignment reference
  across the two new settings. Its interval resamples the same clusters in
  both settings and recomputes the minimum. Report both settings in full and
  the parent anchor, without selecting a preferred setting after outcomes.
- **PP3.m, edit-feature mechanism probe.** Compare the full 24-feature process
  model with the same model omitting the nine edit size, operation, position
  and visible-length features (indices 3 through 11). Keep timing and LaTeX
  structure, every row and the training recipe. Rationale: the annotation
  categories may be recovered mainly from the visible editing operation.
  The primary is full minus ablated macro-F1, direction positive, with paired
  cluster intervals and the same difference under both reassignment banks.
  This tests predictive dependence, not causal necessity or a mental mechanism.
  Recompute the parent's full process predictions and require exact agreement
  with its aggregate confusion matrix before interpreting an ablation.
- **PP3.p, second pipeline.** Replace ridge with one deterministic decision
  tree per target and arm: entropy criterion, maximum depth 5, minimum leaf
  size 25, no class balancing, seed 20261026. Fit separate three- and
  fifteen-category trees; do not infer a three-way model by collapsing a
  fitted fifteen-way tree. Keep the same full process/content matrices,
  prior, references and primary contrast as the parent. Rationale: test
  whether scoped process-label recovery survives a fixed nonlinear reader.
  Probabilities are training-leaf class proportions, with missing fitted
  classes expanded to the complete frozen class list. No tuning on held data.

All states use the frozen shared interval rule. The specification curve's
primary is the minimum; its stronger all-settings claim requires each setting's
interval positive. The mechanism uses the paired accuracy drop; its reference
probabilities are descriptive. The second pipeline uses the parent's primary.
Report half-Brier and all confusion matrices, including any accuracy/probability
disagreement. No unrestricted writing-goal, value, cross-corpus or badge claim
follows. Released rows and the few project clusters retain their limitations.

DESIGN CHECK: LESSONS sections 3–5 and CONTROLS reread for these cards. Constant
features must reproduce training class probabilities and classify exact-null
contrasts as null. Known separable signal must survive held-project evaluation;
label reassignment must remove it on average. A constructed signal carried only
by the removed edit block must disappear under that ablation, whereas a retained
timing signal must survive. Penalty-1 parity is checked against the original
solver, and the mechanism's source baseline against the completed parent.
Project leakage, wrong truth marginals, incomplete rows, corrupted checkpoints,
nonfinite predictions or failed fresh replay invalidate the instrument.

Build and test the shared runner serially. Rehearse all three native modes before
source dispatch. Each whole-population timing pass uses twenty draws per bank
and the full bootstrap, discards scores and independently replays. Twelve times
its complete measured cost must fit the remaining card ceiling before main
dispatch; otherwise hold that card without reducing banks or population.
Each job takes one counted CPU slot with at most two numerical threads. Reserve
120 CPU seconds per card for construction and tests. Prior source preparation is
already charged to the parent, with every new read/fit charged to its consumer.
