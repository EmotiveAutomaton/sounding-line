# LA5: subsequent speaking after others laugh, with and without joining

Prospective implementation of the two-day packet's section 3C, authorized
November 13. AMI is the primary; ICSI is a labelled secondary. This compares
observed timed words after a laugh pattern, not whether someone felt shame or
whether a remark was mockery. The original LA modules and source attempts stay
unchanged. R13–R15 supporting handoffs were absent at build; the packet supplies
the commissioned definitions and attribution.

## DESIGN CHECK

Read LESSONS sections 2, 3 and 5, CONTROLS sections 6 and 7, the qualified LA
source and social-layer code and their design. Four constructed speakers have
two events with hand-computed target shares: 4/10 before and 2/10 after the
unjoined event, 2/10 before and 4/10 after the joined event. The unadjusted
difference is −0.4. The independent extractor uses literal scans rather than
the primary's binary-search windows. Duplicate laughs by one other person,
overlapping earlier laughs, boundary times, annotation marks, missing identities
and recording-span edges have explicit expected behavior.

Adjusted regression must retain residual variation in joining after the required
effects and controls. Its qualified absorbed fit is checked against a separate
dense weighted dummy-regression oracle, including global people repeated across
meetings and resampled meeting multiplicities. A known −0.1 coefficient must
recover; zero must classify as band-null. The complete null consumer runs all
2,000 draws for AMI, ICSI and a role panel, with execution and independent
verification both pausing and re-entering. A failed draw is retained and blocks
the interval; there is no successful-only resampling. One meeting supplies no
population interval. Fewer than 300 eligible events in either group or fewer
than 20 meetings retains a pooled descriptive comparison.

The smaller route is a prospectively sampled set of whole meetings, keeping all
their eligible events and global-person links, if amendment E's measured cost
route is needed. This full-scope candidate has no sampling switch; a frozen
sample must have its own binding and cannot borrow a full-population checkpoint.

## Source and timing

Use the completed, independently replayed LA4 metadata/timed-speech extension
`week5_la_back_half_source_v2`, whose only prior schema repair accepted both AMI
clock syntaxes. Authenticate its native completion, plan and every output, then
the original ACTS, LAUGHS and METADATA table hashes pinned by that plan. Reuse
SPEECH and METADATA_EXT directly. There is no original archive re-extraction,
lemmatizer, reader model or new source qualification in LA5.

Count act words under the original annotation-safe rule. For an act with at
least three words by X, require vocal laugh **onsets** in the closed interval
from its end to two seconds later from at least two distinct other speakers.
All qualifying other onsets determine the first and last times. Repeated marks
from one other speaker do not satisfy the two-person rule. X joins if an own
vocal onset lies from one second before the first other onset through three
seconds after it, inclusive.

This differs deliberately from the old `laughed_after` field: that field also
admitted laughs overlapping the second before the act ended and required only
one hit. The new packet supplies the stricter rule, so no old positive flag is
silently treated as the new case. ICSI-plus is not another population.

Count every qualified lexical word by its **start** timestamp in left-closed,
right-open windows: sixty seconds before act start and sixty seconds after the
last qualifying other onset. The outcome is target share after minus target
share before, with all speakers' observed words as each denominator. Do not
reconstruct words missing timing or replace missing speech with zero. Every
candidate event remains in the private table. Zero-denominator events have an
undefined outcome. Windows extending outside [0, qualified annotation duration]
and missing global-person links are counted outside adjusted fits. Their
nonempty-window shares remain in an explicitly unadjusted description. This
full-window requirement prevents an unobserved recording tail from being called
silence. Qualified duration is an annotation span, not a claim of audio coverage.

Global-person metadata supplies speaker effects across meetings; no local label
is invented as a global person. AMI role secondary panels use only recorded
qualified roles. ICSI roles stay absent. This card needs no cross-meeting dates,
so ICSI's chronology hold is retained without blocking its within-meeting
timing comparison. Existing unsupported-word-timing counts remain an inherited
limitation: this measures observed timed lexical words, not total speaking time.

## Frozen comparison and interpretation

Fit target share change on an indicator for **not joined**, with global-speaker
and meeting fixed effects, meeting minute at act start, act word count and the
number of distinct other laughers. Reuse the qualified weighted global-speaker
absorption and partial-coefficient primitive from LA3/LA4, adding meeting dummy
columns explicitly. Redundant nuisance columns are handled by its existing
pseudoinverse; an absorbed target is unsupported. Refitting resampled speaker
means preserves people who cross meetings. Whole meetings are the bootstrap
unit; canonical meeting order and seed `[20261113,5,draw]` fix 2,000 draws.

One primary is the adjusted AMI not-joined minus joined coefficient. Its bar is
0.02 and its prediction is negative. A complete interval below −0.02 supports
that operational prediction; one above +0.02 is against; one wholly inside the
practical band is band-null; otherwise it is inconclusive. Report estimate,
interval, bootstrap standard error, `sees = 2.8 SE`, and
`supports_at = 0.02 + 2.8 SE` as a magnitude in the negative direction, with
limited-sensitivity and degenerate flags. The normal approximation is optimistic.
ICSI and all observed AMI role strata are descriptive secondaries with the same
full draw count when identifiable. No partial or failed bank yields an interval.

The result carries `record_kind`, `theory_tags=[H14-mockery]`,
`by_construction=false`, and an activation entry for SHAME carried on PLAY's
signal, explicitly attributed to the packet's proposal. Its observed field is
the completed operational contrast, not a channel measurement. Laughter at a
remark and laughter at its speaker cannot be distinguished; not joining may
mean holding the floor, which predicts more talk and works against the proposed
direction. These limits remain in every completed result.

## Preparation, replay and cost

The first counted phase derives one sealed numerical event block per meeting.
Its first 13-meeting quantum covers at least 5% of the already qualified
246-meeting source. Complete independent preparation reconstructs every event
and exclusion through the literal reference formula. Analysis admits only that
complete event table, then checkpoints complete meeting draws every ten draws
and before a yield. Operational changes are only `max_new_draws` and
`max_wall_seconds`; the first field counts meeting units in preparation and
draw units in analysis. Source, module, phase, panel and table identities remain
bound on re-entry. Partial verification explicitly returns `verified=false`.

The first analysis quantum is 100 draws of its primary. Its cost forecast must
include every supported corpus/role panel and complete independent replay. If
the measured full forecast exceeds 7,200 CPU-seconds, the owner must extend the
checkpointed in-slot prefix to at least 5% of that declared total work before
full continuation, under the unchanged packet rules. No fixture duration is a
human-data cost estimate.

LA5's ceiling is 30,000 CPU-seconds within the unchanged LA family allowance;
source derivation, failures, pauses, fitting and full replay all charge. The
source/analysis memory envelope is a prospective 4 GiB, inherited from the
qualified source stage rather than newly measured. At most two numerical
threads, CPU only, unchanged resource floors. Owner review, design filing,
targeted qualification and current remaining-cost admission are outstanding.
This candidate claims no commit, launch or result.
