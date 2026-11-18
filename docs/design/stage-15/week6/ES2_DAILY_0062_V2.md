# ES2: documented daily-source binding, member 0062, version 2

The full-week extension section 3C commissions a distinct daily replication.
The curator approved daily perceived-adversity ratings in place of the packet's
incorrect event-count description. This binding uses the existing qualified
operator; it is not a new hypothesis or a replacement primary selected from
earlier outcomes.

Version 1 and its failed attempt are preserved. Version 1 incorrectly bound
the positive-day parser even though the source-specific day adapter was already
documented and qualified. This successor corrects that integration error; it
does not choose a mapping from observed scientific outcomes or change the
curator-approved daily agreement comparison. Its original seed, source, items,
support requirements, estimator and cumulative budget are unchanged.

## Source, units and support

Use openESM0062 version 1.0.0, [record 17347975](https://zenodo.org/records/17347975),
the retained 6,917,023-byte source with SHA256
`1c27ae6f25d972f870c836791a9906493cab4ce395c2d70754329750c4019293`.
Credit Neubauer and colleagues' [original study](https://doi.org/10.1007/s11618-023-01182-8)
and openESM under CC BY 4.0. The supplied metadata describes 322 participants;
the counted source phase must establish its actual population and exclusions.
Only the fixed daily field whitelist is read. No static or demographic fields
are included, and no individual rows, identities or slopes are published.

The original STECCO codebook, version 1.0 (July 31, 2022), page 3,
explicitly defines codes 0 through 13 as study days 1 through 14. The preserved
official cleaning script renames the original day field without shifting it.
The versioned adapter preserves source codes and derives study day as code plus
one for this exact source release. Missing days stay missing; no observed-minimum
rebasing, timestamp reconstruction or wave stitching is permitted. Select only
the source table tagged daily and count excluded momentary records explicitly.
The original file is never modified. Unknown source tags or invalid codes refuse.

The four daily predictors ask agreement
that the person faced failure, pressure, feeling unappreciated and disagreements
or conflicts, referring to today. The daily outcomes ask whether the person felt
angry, afraid and worried today. All seven ratings run from 1 (completely disagree)
to 7 (completely agree). Their agreement scale does not count events or directly
measure emotion intensity. Empty fields and `NA` are missing; other invalid
encodings fail visibly.

Use the conservative qualified layout `one_nonempty_daily_record_per_person_day`.
Entirely blank selected daily rows are counted separately from excluded momentary records. Missing person/day
keys are excluded and counted. Any repeated nonempty daily record for the same
person and original day refuses this binding, even if its ratings match. Do not
silently average, collapse or choose among duplicates. A refusal requires a
separate source-layout review and retained original evidence before recovery.
This is a prospective assertion checked inside the counted source phase, not
a claim that the raw layout has already been independently verified.

## Unchanged comparison and decisions

Within each person's common complete daily reports, center and scale each item
by the pooled within-person sample deviation, with observations minus people
as denominator. Average the four scaled adversity items. Compare the person's
anger slope with the slope of the average scaled afraid and worried ratings,
each fitted separately on original odd and even study days. Require at least
ten complete daily reports; undefined half slopes stay undefined and are counted.

Use the unchanged average cross-half correlation divided by the root product
of the two own-half reliabilities, without clipping. Both reliabilities must
be at least 0.15, including equality. Use 2,000 whole-person resamples, seed
20261116006202, recomputing scales and gates. Invalid draws stay in the bank,
without replacement or a valid-draw-only interval. With a full valid bank, the
95% percentile interval gives the existing decision: lower bound at least0.90,
one-dial reading; upper bound at most0.85, more-than-one reading; otherwise
unresolved. Unsupported reliability or unavailable uncertainty licenses neither.
Below twenty people retain the descriptive fallback; below two no population
interval. Report approximate sensitivity only where a full-bank SE is defined.

This is a separate daily agreement measure, not the same interaction-level
anger/fear item families or an independent proof of biological channel identity.
Shared reporting, daily recall, short day halves, restricted rating variation
and possible source-population overlap remain limitations. Do not pool its
estimate with the interaction members or use it to replace their primaries.

## Qualification, accounting and execution

Use the exact additive modules es_source_v2, es_handler_v3 and
week6_es_day_v3 authenticated against the complete 56-case native daily
qualification (OPS-S15-W6-ES-DAILY-QUALIFIED-20261117). The earlier original,
clock and population qualifications remain filed, totaling 222 parent cases.
These exact daily modules were already tested; their byte-exact installation
introduces no estimator change. The original positive-day modules remain for
0056/0057. Source-era, all fourteen day codes, missing/invalid values, duplicate,
privacy, population, active entrypoint and fresh-replay fixtures remain binding. Production still authenticates all source bytes
and requires complete fresh source, support and draw replay in a distinct native
worker, Job accounting, exit verification and owned-lease release.

Commit before freezing the plan. Keep ES2's cumulative accounting identity,
the100,000 CPU-second ES family and6,000,000-second Week6 campaign. Retain1,800
CPU/wall seconds per attempt,1,500 cooperative quantum,128 MiB output cap,
2 GiB projected RAM and two numerical threads. Existing resource floors,
eight shared slots, CPU-only Gear2, closure dates and event/four-hour/single-pending
wakes remain unchanged. Register all terminals. No earlier evidence or charge
is reset, and no paused GPU work is restarted.

## DESIGN CHECK

Relevant LESSONS source, sampling-model, immutable-receipt and native-accounting
sections were reread. The NULL uses independent cross-half responses and recovers
zero in qualified known-answer worlds; the ALTERNATIVE uses shared sensitivity
and recovers one. Same-prompt noise cannot replace independent halves. Weak
reliability, conflicting layout or inadequate day support blocks both directions.
The source phase counts whether the required case actually exists. The smaller
route is an authenticated unchanged checkpoint, not an easier gate or a selected
population. Full write-through precedes ACK; final scientific synthesis stays
in the campaign packet.
