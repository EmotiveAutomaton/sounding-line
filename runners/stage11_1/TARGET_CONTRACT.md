# Production relations v1

Frozen before any Stage 11.1 model outcome. Six fixed questions concern witnessed
operations during the menu-to-cutoff episode. Every method answers all six; extra
prose creates no extra scoring opportunities. Historical handling is secondary.

| Slot | Witnessed question | Positive actor and operation | Relation |
|---|---|---|---|
| selection | Was an offered fragment selected and its insertion verified? | human_writer / select | selects entry |
| entry | Did offered model material enter the document through the verified API transform? | model / insert | selected_by selection |
| change | Was the inserted material changed by recorded human deltas? | human_writer / format_edit, content_edit or delete | modifies entry |
| continuation | Did the person insert new material after the current insertion, or at the endpoint if no insertion occurred? | human_writer / insert | extends entry, or none without entry |
| surrounding | Did the person change pre-existing material outside the current insertion? | human_writer / format_edit or content_edit | unrelated to entry, or none without entry |
| removal | Were any characters attributed to this offered insertion deleted? | human_writer / delete | removes entry |

`model` identifies the producer of verified offered text; the API is its insertion
mechanism. This does not turn an API call into a mental event. Other actor choices
are `tool` and `unknown`. Every operation/relation distribution includes `unknown`.
For complete, valid logs, no witnessed event is scored as `absent`, with unknown
actor and no relation. This means absence from the retained trace, not proof that
an unrecorded mental act never happened. Missing/malformed telemetry excludes the
affected source; it never supplies a negative mental-state label.

Formatting means equality of the surviving fragment's case-folded letters and
digits after stripping Unicode punctuation/spacing. This operational typography
distinction is not a judgment of semantic importance. Fragment edits retain lineage
through replacement; additions outside that lineage remain separate continuation
or surrounding changes. Complete deletion remains an unlocated operation. Removal
can co-occur with a replacement or formatting change; the slots are dependent.

Endpoint anchors are fixed consecutive 160-codepoint windows derived from the
endpoint alone, with offsets into the exact endpoint text. They are identical across evidence
tiers and methods. A predicted anchor denotes overlap with the affected region,
not homogeneous authorship of the whole window. Score anchor-set exactness and
intersection-over-union separately; record unlocated/deleted, absent and unknown
states explicitly. The stored evaluator also retains exact source positions.

Artifact evidence has endpoint anchors and common menu-availability context. No
separate brief is inferred; `brief` is null, with availability false. Alternatives
adds actual before text, all displayed alternatives and explicit character-level
differences. Assisted observations are separately identified and never pooled with
blind forecasts. Opaque source IDs, selected index, outcome labels, private target
facts and full logs never enter a blind request.

Output probabilities are elicited, not calibrated. Primary finite scores are
half multiclass Brier loss per operation, actor and relation, equally weighting
fixed slots within episode, then episodes within writer. Report each target,
session and prompt-component distributions and raw counts. Invalid forecasts retain
worst loss one and accuracy zero. Correct positive witnessed claims per episode,
contradictions, coverage and error at matched coverage accompany accuracy; predicting
all unknown cannot win by being empty. Fixed abstention uses maximum probability
at least 0.75, with no learned calibration claim. Risk curves also show fixed
coverage fractions using stable, outcome-independent tie order.

Review, endorsement and understanding are explicitly unobserved attributes. Yes
or no claims about them are unsupported; unknown is warranted. Purpose and maker
traits remain hypotheses outside the finite historical score. Mechanical account
checks validate enums, real public anchors, evidence pointers and references to
earlier events. Passing them establishes compatibility, never historical truth.
