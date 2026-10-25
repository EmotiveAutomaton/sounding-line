# Week 3 values-label preparation and calibration

The commissioned question is whether choice-derived directions predict values
stated in explanations, and whether value language recurs in a writer's separate
argumentative sessions. This build prepares the private labeling input and
calibration machinery. It computes neither scientific comparison.

`runners/drive/cards/week3_values_inputs.py` accepts authenticated complete CA1
preparation, the authenticated EV full-source index and the H01 roster receipt.
For each person in the fixed CA1 population it samples at most ten nonempty
explanations by a hash ordering with seed 20261026. Missing explanations and
zero-selected people remain explicit in the private population census. Sampling
does not use choices, country, language or model scores. Identical texts are
deduplicated while every comparison/session link remains private.

The CoAuthor source retains the previously admitted 1,399-session EV population.
The original EV summary records 46 additional H01 roster sessions outside that
population; these remain separate audit rows, with genre and disposition. They
are not new missing members of the canonical population. Every canonical
argumentative session contributes authenticated surviving human-authored spans,
using the existing `typed_fragments` representation and its provenance checks.
Two newlines mark gaps where non-typed text was removed. This is fragmented
artifact text, not continuous original prose. Empty typed sessions remain
explicitly unsupported, never all-zero value profiles. The interpretation based
on all produced words, including deleted words, remains separate and unrun.

`runners/drive/week3_val.py` binds this completed preparation to a fixed prompt,
model and JSON schema. Its only outbound content is the target text; joins,
identities, prompts, choices, country and profile metadata stay local. All ten
categories remain present in every request. A ten-bit string encodes, in order,
self-direction, stimulation, hedonism, achievement, power, security, conformity,
tradition, benevolence and universalism. A second binary field represents other.
The two-field encoding is a format choice, not a reduction in semantic dimensions.

The prompt's short operational definitions paraphrase Schwartz's
[primary overview](https://scholarworks.gvsu.edu/orpc/vol2/iss1/11/), definition
pages 5–7, inspected through a [copy of that paper](https://dsdweb.co.uk/wp-content/uploads/2021/08/An-Overview-of-the-Schwartz-Theory-of-Basic-Values.pdf).
Coding endorsement rather than mention, treating readability/accuracy alone as
other, and allowing multiple simultaneous codes are explicitly agent-authored
annotation rules. They are not a validated survey or independent human gold.

The model is `claude-haiku-5-5`, thinking disabled, maximum output 32 tokens.
The [official schema documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
was checked October 25: simple anchored character-class patterns, batch requests,
token counting and Haiku 5.5 are supported. The schema uses `^[01]{10}$`, not
unsupported string-length bounds. A separate parser checks exact bits, binary
integer other, unique JSON keys, one text block, exact model and normal end.
Refusals, truncation, malformed fields or incomplete coverage fail the entire
rung; there is no silent recoding or dropped response.

The first 100 distinct texts, in a frozen outcome-blind order, require complete
owner-made blind agent labels before provider access or token counting. Primary
Cohen agreement is pooled across all eleven binary categories and must reach
0.6. Per-category agreement is reported when blind-gold prevalence reaches 5%;
both gold and provider prevalences are recorded. CA3's later 5% coded-sample
prevalence rule remains separate. The rung is a small, agent-labeled instrument
check, not human or cross-language semantic validation.

A failed first rung permits one recorded prompt clarification. It must use the
next 100 distinct original texts, with no overlap in semantic item identity.
The failed first hundred remain in the full population and are recoded under the
repaired prompt if that fresh rung passes. A second failed rung stops. Repair
does not change categories, source population or gate. Original attempt files
and charges remain intact.

The owner invokes `prepare`, `count`, `submit`, `retrieve`, `replay`, `reconcile`
and `assemble` explicitly. Counts include the schema; every submission has a
unique identity, recent access/count preflight and an immutable reservation
before POST. Unknown submits retain their reservation and cannot be resubmitted.
Reconciliation is a separate explicit owner action. The existing Week 3 budget
guard remains unchanged: VAL's 250-cent cap, campaign's 1,000-cent cap, previous
node reconciliation and paid cutoff all apply. No bare Messages endpoint exists
in this path. Preparation and tests make no actual provider request.

Nineteen targeted constructed checks pass, including complete source replay,
sampling invariance, provenance/empty/source-gap handling, retained joins,
schema parsing, known-null/planted agreement, fresh repair preservation,
reservation-before-POST, uncertain-submit refusal and explicit reconciliation.
Owner-native source validation, full private preparation, blind labeling,
actual token counts, calibration and downstream CA3/WE1 remain separate steps.
