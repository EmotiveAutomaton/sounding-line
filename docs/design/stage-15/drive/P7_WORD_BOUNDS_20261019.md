# Bounded common-event validation for P7

The commissioned common-word validation continues within its existing 900-second
diagnostic allowance. Earlier work charged 305.547291 seconds. Charge all new
component/handler tests, launch overhead and native execution plus fresh replay
to that same allowance. No automatic doubling or new scientific branch.

DESIGN CHECK: LESSONS sections 3–5 reread for this design. Under both scientific
null and alternative, known finite token trees must contain the exact answer
inside every returned interval. Missing mass, alternate tokenizations, casefold
aliases, skipped separators and context limits cannot become zero probabilities.
Impossible conditioning events, invalid distributions, changed source, decoder
disagreement and any fresh oracle/reconstruction disagreement refuse. Width above
0.0001 nats refuses a point score; a completed wide bound is not a scientific null.

The inspected derivation assumes exact tokenizer support; its beginning-boundary
correction uses both start and end masses. It explicitly requires marginalization
for inexact models and makes the word definition part of the boundary rule.
[Pimentel and Meister, sections 4.3, 5.1, 5.3–5.5, READ](https://arxiv.org/html/2406.14561v2).

Implementation choice under week S5/S7: keep the original fixed canonical token
history and its original crop. Condition on any observed byte overlap before the
focal target. The predicted event is the next original regex TOKEN, casefolded,
including its existing whitespace/underscore skipping and apostrophe rule.
Decode arbitrary native token continuations incrementally with the actual UTF-8
replacement convention. Do not lowercase the context, replace the word by its
canonical spelling, or reinterpret a single token path as the word probability.
This is conditional on the observed canonical history, not marginal over histories.

Traverse disjoint token-prefix cylinders in descending probability. Preserve
accepted mass and all unexpanded/context-limited mass as an interval. Normalize
the joint target/prefix event by the observed-prefix event using interval division.
Outward arithmetic encloses the normalized finite weights emitted by the numerical
oracle; it does not certify neural floating-point errors or model truth. No midpoint,
probability floor, sampled-string selection or omitted-mass imputation is permitted.

Native validation uses the same first/last word from each original pilot domain,
four fixed targets. The earlier 612-target inventory remains intact. Each joint
or prefix event expands at most four native prefixes. Full-vocabulary oracle
weights and every interval are saved and reconstructed in a fresh native process.
GPT-2 medium remains CPU float32 with two threads, local pinned files only.
Float64 exponential weights must all be positive and finite. No context is
shortened for lookahead; exhausted contexts retain unresolved mass.

Forecast 300 seconds from the previous 229.259-second execution/replay of 49
paths and at most 32 new distinct prefixes per execution. One counted CPU slot,
the demo reservation, existing memory/commit/disk floors and immediate terminal
monitoring remain. Full scoped P7-D33 execution, cache compatibility across the
whole population and any corpus runtime forecast remain unadmitted. A wide
four-prefix bound does not establish algorithmic impossibility.
