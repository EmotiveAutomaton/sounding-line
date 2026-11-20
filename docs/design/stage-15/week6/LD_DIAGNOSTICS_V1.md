# LD1 comparisons and LD2 role component

This implements existing packet section 3.1, without opening a participant
source, returning a scientific verdict or qualifying a complete study runner.
The new module is separate from the already pinned binding/source components.

For LD1, a binary diagnostic comparison uses the unchanged context-product
model and its raw-rating diagnostic. Outputs use reference/comparison labels.
The real adapter must first bind communication and partner-count codes from
the source codebook. No numeric code is guessed here. These diagnostic
comparisons are descriptive and do not add predictions to the frozen 44 rows.

For LD2(a), review single-partner criticism and leadership metadata before
calling any loader of feeling outcomes. Both role groups need at least 60
above-floor criticism prompts from at least 40 distinct people. Leadership
must be greater in the below group. Failed support returns counts without
reading feelings; failed coding returns that disposition. The outcome loader
must bind the same source hash, ordered unique row keys and criticism values.
One common complete-case mask covers all six events and all four feelings;
the original support/coding checks must still pass on those retained rows.
Missingness counts are retained. No floor, variance or sign filter is added.

The role model extends the supplied `pf_fixtures.py:ld2_contrast` occurrence
design with the five other required status events and all six person means.
Its rows are single-partner supervisor (above), employee/child (below), and the
declared peer roles. Other roles are counted, unscored and excluded from the
model. Predictors are centred/scaled over those card rows, before splitting
by role. The pooled model has all six event terms, two criticism-by-role
products, two role indicators, and six person-mean terms. Thus criticism has
three slopes and the other five events are joint common-slope adjustments,
as in the supplied fixture's pooled construction. All 17 coefficients and
all six event slopes by feeling/role are retained. A missing peer group or
singular design is an invalid fit, never a reference group invented afterward.

The primary is anger minus the mean of anxious, ashamed and insecure for
criticism below, minus the same contrast above; the original bar is 0.40.
Whole-person bootstrap weights rebuild within-person scales and all fits.
Observed support gates are not used to select bootstrap draws; failures must
be counted by the future producer. Point fits alone carry no interval or
scientific verdict. Role describes one relationship; all reports share a
prompt, and the child's age remains unknown.

DESIGN CHECK: LESSONS sections 3-5, read for this implementation. Under the
NULL, identical feeling outcomes give zero while separate failures remain
invalid; under the ALTERNATIVE, planted contrasts agree with independently
constructed statsmodels fits, with reversed roles reversing the sign. Literal
whole-person replication must match weighted fits. Fewer distinct people,
too few criticism prompts, reversed coding, missing fields, changed source,
reordered rows and metadata mutation cannot reach an inferred result. Outcome
loading is forbidden before support/coding pass. These are constructed checks,
not calibration of human sensitivity or whole-card admission.

Remaining work: codebook/source binding for these diagnostics; checkpointed
2,000-draw producers; complete independent replay; missingness/disposition
tables; temporal-order qualification for LD3's descriptive next-prompt table;
immutable owner review and ordinary runtime admission. Existing source-check
costs and these component costs must enter the applicable ES admission once.
Publication is separate from research admission.
