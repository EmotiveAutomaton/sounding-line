# EM1: private materials for the curator's existing correspondence

Prospective static candidate, November 11. The packet commissions two local
folders, not another model comparison or a message to anyone. Nothing has been
materialized, copied, sent or scanned from the corpora by this build.

DESIGN CHECK: LESSONS §1d, §§2–5 and packet EM1/T/Q. The source row, split and
normalization are part of an overlap count. A prefix length cannot be chosen to
recreate an old number. Within-project and project-held-out folds are different
questions. Labels, predictions, author fields and third-party text do not belong
in these materials. The fixtures retain exact duplicates, negative cases,
alignment failures, delimiter ambiguity, source changes and complete replay.

## Original evidence and the explicit gap

L106 records PAN23-hard training reuse in PAN24-hard validation at documents,
paragraphs and consecutive paragraph pairs. L108/LESSONS §1d retain the
within-year check and revised paragraph-level removal rule. The preserved
`run_pan_winner.py` loader specifies nonempty newline-separated paragraphs,
UTF-8 replacement decoding, and scored pairs only where paragraph count matches
the truth change count plus one. The new material builder follows those units;
it does not rerun any model or rescore a prediction.

ScholaWrite L68 records 1,060 of 1,241 unique before-text prefixes shared with
training. The inspected entry and preserved runner do **not** specify the
prefix length. That exact historical definition remains unrecovered. A fresh
source capsule must therefore include a positive code-point prefix length and
an owner-reviewed, SHA-bound definition receipt saying whether the historical
rule was recovered. There is no default and no search over widths to hit the
old count. If the owner instead admits an explicitly new fixed prefix audit,
its README says it does not reproduce L68's number. This gap is not concealed
by an otherwise complete folder.

The preserved `run_scholawrite.py` specifies the original leave-one-project-out
folds: combine shipped train and test, sort the original project values, and
hold each whole project out in turn. `test_small` and `all_sorted` are not
silently added to that union. The current builder retains that rule exactly,
with only hashed project keys in its tables.

## Source capsule and outputs

The owner prepares a frozen `EM1-LOCAL-1` capsule, containing the exact file
trees and SHA-256 values for PAN23 hard training, PAN24 hard training and
validation, and the original local ScholaWrite dataset. Every source root must
resolve inside this repository. Symlinks, escaping members, extra/missing files
and changed hashes refuse execution. This intake has not been performed. Old
source presence is not presented as new campaign qualification.

The output run's ignored `output/bundle/` holds `pan_style/` and `scholawrite/`.
Each has a README, one-paragraph plain summary and portable hash arithmetic
script. PAN tables contain raw-document SHA-256, stripped-paragraph SHA-256,
canonical JSON ordered-pair SHA-256 and the historical separator-joined MD5.
Canonical pairs avoid silently merging text containing the legacy separator.
Problem filenames become hashes. Reports distinguish unique hashes from
occurrences and retain alignment failures. Both within-year and cross-year
comparisons are included; no hidden-test inference or model score is added.

ScholaWrite reads only `project` and `before text`, immediately hashing full
before text and the explicitly defined prefix. Output contains hashed project,
split and row ordinal, hashes, length and an empty-prefix flag, plus per-project
counts and the exact fold definitions. Empty prefixes are separately counted
and excluded from the shared-prefix numerator; this convention is explicit and
cannot be described as the undocumented historical convention. No source text,
author field, timestamp, label, contact details or model output is exported.

The portable script checks overlap from the supplied hash lists without any
network. The bundle manifest pins every file and the source-capsule hash; it
does not embed local source paths. These are private correspondence materials,
not an assertion that hashes are anonymous or safe for arbitrary publication.
The handler contains no external-send, upload or cross-repository copy action.

## Execution and verification

New modules `week5_em1_hashes`, `week5_em1`, `week5_em1_fixture`; originals stay
unchanged. Checkpoint complete document and row projections with source and
implementation bindings. The initial five percent PAN projection is an in-run
cost prefix, not a forecast for the entire ScholaWrite pass. Source hashes and
full independent replay are charged. Yield and wall/quantum bounds return
`status=yielded, verified=false`; fresh verification reconstructs the complete
bundle and compares every byte. No fit, random sample, science verdict or new
performance metric exists.

Ceiling 10,000 CPU seconds under EX's 100,000 total; current actual remaining
allowance and unchanged floors are owner admission gates. Proposed peak RAM
2 GiB is an unmeasured source-load forecast, ≤2 numerical threads. The source
dataset adapter is substituted by constructed rows in the fixture and explicitly
does not qualify the real Arrow dataset. The exact file-tree boundary and full
hash/material execution and replay run in that fixture. A source-capsule intake
and owner review remain necessary before the real run; amendment Q does not
turn older unqualified source presence into a qualified current dependency.

Current status: static, untested, unadmitted. No source capsule or historically
supported prefix width is supplied. The owner must review the source schema,
historical-prefix limitation, exact local-only content, passing constructed
checks and measured intake costs. Record kind is `run`, theory tags empty,
by-construction false for real source material. No scientific ledger claim or
communication is generated by this candidate.
