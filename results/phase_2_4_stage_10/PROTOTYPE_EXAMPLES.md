# Stage 10 prototype examples

These are actual retained predictions and rule executions, not new calls or invented demonstrations. The [machine-readable bundle](PROTOTYPE_EXAMPLES.json) contains the exact rules, distributions, selected features, source digests and costs. Human source prose and identities are withheld. Examples illustrate mechanisms and failures; their selection is not a prevalence estimate.

## A correct next-edit prediction from a weak purpose proxy

A scientific-writing draft contains 167 words on two lines, one section marker and no explicit citation markers. The reader proposes two alternatives: a short draft implies content production rather than planning; absence of citation markers implies content production rather than reference revision. Both threshold programs execute to the implementation category.

The committed probabilities are implementation 0.85, revision 0.075 and planning 0.075. The next released edit is annotated implementation. Two model calls, 5,633 input tokens, 360 output tokens and four executor evaluations take 6.80 recorded callback seconds.

The rule predicts this annotation correctly. Its input thresholds are evidence for its consequence, not proof of the writer's private goal. This is the first retained row of the final project's current-draft category comparison, not a selected best score.

## A legal rule that is confidently wrong

Another current draft has 324 words and no permitted prior handling record. The reader proposes that fewer than 500 words calls for planning and that absent prior records should default to planning. Both rules execute as written. The committed planning probability is 0.85, but the next released edit is annotated implementation.

Two calls use 3,703 input tokens, 391 output tokens and four executor evaluations, taking 7.48 callback seconds. This example is selected by first task hash among valid wrong forecasts with declared confidence at least 0.85. Executable consistency does not make the writer hypothesis correct; lack of an observed history is not affirmative evidence that the writer is planning.

## A history intervention exposes two conflicting readouts

The current draft, displayed suggestion menu, option order and future handling target stay fixed. Eight own-writer history records are replaced by exactly eight records from another writer.

With own history, the reader declares accept-and-retain. Its probability vector ties that outcome and dismissing the menu at 0.45 each. With swapped history, it declares dismissal, although its executed probability vector assigns accept-and-retain 0.85 and dismissal 0.05. The recorded outcome is accept-and-retain.

The swapped run uses two calls, 5,360 input tokens, 385 output tokens and four executor evaluations, taking 9.16 callback seconds. Original reused costs are separately retained. Selection is the first pair hash where the own-history generated choice is correct and the swapped choice is wrong. This example deliberately preserves the contradiction: probability scoring and generated-choice scoring cannot be used interchangeably. The average controlled history effect is reported over all 77 matched pairs in the final report.

## A constructive route is not a historical trace

In the public four-cell Ghost world, actions set or clear bits of an initially empty board. A current observed artifact is bitmask 9, produced under construction target 3. The question is the maker's artifact on a new construction with target 12; the actual withheld artifact is 8. The reader proposes acquired-library and action-route alternatives, executes them, and weights their predictions by compatibility with allowed observations.

The JSON retains each candidate, its observation likelihood, route legality, visible-artifact match, future distribution, committed forecast and cost. The forecast's declared choice is wrong on this example. A legal route may fail to reproduce the visible artifact; even a matching artifact does not identify the maker's actual historical trace. The executor explicitly leaves historical identity uninspected and warns that omitted hypotheses may explain the observations.

No dependency-damage example exists in the retained local evidence. It is listed as an unresolved comparison rather than replaced by a made-up result.
