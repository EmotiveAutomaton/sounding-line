# PLAN calibration: proposal-format phase

This implements the already approved PLAN node in packet section 5. It does not
admit T5 inference or change the original 3,600 CPU-second allowance. The source
census is complete and independently replayed; its completion hash must match its
full-write-through receipt before preparation.

DESIGN CHECK: LESSONS sections 3–5 reread November 4. Under either a scientific
null or alternative, valid source projection and complete response accounting must
pass. Corrupted bindings, extra private fields, incomplete batch coverage, malformed
plans or uncertain submissions must refuse advancement. Format cannot distinguish
scientific null from alternative. A successful format phase leaves semantic
agreement untested and the main node and T5 consumer blocked.

**Case and check.** A qualifying session has nonempty midpoint text and at least
four usable canonical later menu openings. Ignored menus remain unchosen; they are
not recoded as dismissals. The full source census must contain at least 300 such
sessions. Identical midpoint requests are deduplicated by content, retaining all
session joins privately. Sort unique inputs by the SHA-256 of seed 20261102 and
their content digest. The first 100 distinct inputs supply this format rung; the
next 100 are reserved for a fresh correction if required. Preparation refuses
fewer than 200 unique requests. Eligibility never depends on observed choices.

**Smaller route.** This phase is only 100 requests with 300 output tokens each.
Count the exact wire payloads and reserve their conservative ceiling before one
batch submission. The existing PLAN cap is 150 cents and campaign cap 1,000 cents.
No smaller calibration or automatic resubmission is permitted. Prior node charges
must be reconciled. Reserve 120 CPU seconds for this interface's tests, preparation
and local accounting inside T5's original allowance; retain measured elapsed work
and all prior source charges. Later local analysis still requires measured admission.

The proposal receives only midpoint text. Its system instruction asks for five
distinct, plausible one-line continuation plans grounded in visible text. Future
options, choices, identities, genre metadata and profiles are absent. Text is data,
not instructions. The commissioned Haiku model has thinking disabled and no tools.
The response is a required five-key object, p0 through p4, each a string. Fixed
keys avoid unsupported array cardinality constraints in the provider's
[structured-output schema](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).
The local parser requires the entire response, exact model and end-turn marker,
text-only content, exact keys, nonempty single-line strings and five distinct
normalized strings. It does not salvage prefixes or clip responses.

The format floor is 98 valid sessions out of 100. All invalid responses and
charges remain. A terminal format receipt explicitly says semantic agreement is
untested, node calibration is incomplete and main admission is false. A failed
rung has only the packet's one separately recorded prompt correction, using fresh
items; nothing in this implementation automatically corrects or resubmits it.

After this phase is fully recorded, the separate fit-rating preparation must
freeze 100 option/plan pairs without reference to choices or provider ratings.
The owner labels them blind before the rating call. Ratings 1–2, 3 and 4–5 form
the predeclared low, middle and high levels; Cohen's kappa must reach 0.6, with
complete denominator and invalid-response accounting. The packet's 120-token
menu-level constrained matrix remains required. That phase and main dispatch
have no executable admission route in this proposal-format module. T4's model,
prequential updating, scientific controls and whole-workload costing remain
separate dependencies.

Source, request, design, tests and code closures are frozen before any transfer.
Provider token counting and model access use the existing authenticated,
redirect-refusing client. Batch submission has one durable reservation identity;
unknown delivery retains it and forbids retry. Retrieval is finite and read-only,
with terminal and disappearance watches registered before submission. Usage is
reconciled before completion is reported, or explicitly retained as unsettled when
provider evidence is incomplete. No source text, identities or private joins enter
public receipts.
