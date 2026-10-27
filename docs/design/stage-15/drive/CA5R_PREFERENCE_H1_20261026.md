# CA5.r.h1: retain texts with no learned lexical-topic loading

The first text-only attempt failed before ratings access: the frozen
minimum-document-frequency vocabulary left one valid short joke with an empty
vector. This is an instrument/support failure, not a result about preferences.
The original attempt, code and design remain intact. Under Week 3 section 0.3B,
this representation-policy change is a separately frozen `.h1` card at CA5.r's
rank, using its existing cumulative allowance, not a new follow-up generation.

Keep every vocabulary, topic-fit, seed, split, estimator, permutation and decision
choice from [the original frozen design](CA5R_PREFERENCE_20261026.md). For a text
with zero vocabulary mass, or zero fitted component mass, its normalized topic
vector is the zero vector before the already specified softmax. Its final eight
weights are therefore uniformly 1/8. Record both support conditions explicitly
by item identity in private evidence and as counts in aggregate reports. This is
an uninformative topic assignment, not an imputed rating or invented category.
All text, all ratings and all persons still enter their original source and
additive baseline calculations. No alternative vocabulary is chosen from
outcomes. Non-convergence and nonfinite values still fail.

The amended test suite checks the exact uniform fallback, unchanged features on
fully represented texts, input mutation, full source consumer and counted native
replay. The original ten known-answer tests stay binding. The corpus-mask noise
check uses twenty fixed independent worlds at the same .03 ensemble tolerance;
stable and reversed plants retain .10 and -.10 thresholds. These choices were
validated before corpus preference scores. The original two unit-fixture
corrections remain in the build review; neither was a corpus-result change.

Costs remain cumulative: 376 CPU seconds including the original input/build
reserve, native comparison and failed text attempt, plus 60 seconds reserved
for this correction's construction and checks. The original 1,800-second
ceiling and complete pilot/main/replay gates remain. No corpus scientific score
has been produced or inspected when this amendment is frozen.
