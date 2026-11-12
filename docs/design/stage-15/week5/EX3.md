# EX3: the frozen public goal task as identifiers and offsets

**DESIGN CHECK.** Read packet EX3/T/Q and R4, LESSONS section 2, and the original
GO1 parser, source licence exclusions, candidate allocation and two-reader
preparation. A later reader mask must not change the exported task. Fixtures
must refuse changed source bytes or allocation and retain nested Motivation
exclusion, all 49 ordered distractors and exact writer hashes.

Require complete independent replay of the R4 primary preparation with 49
distractors, and the original full GO source. Match both source-row and candidate
allocation digests to the preparation. This source-only dependency is sufficient;
the export does not wait for encoder or language-model scoring and computes no
reader result. Texture or first-draft allocations are not substitutes.

For every original source document, retain its local task ID, public repository
and relative path, pinned commit, original source-byte SHA-256, hashed first
author and accepted licence. Decode source UTF-8 with CRLF/CR normalized to LF
as in the original reader. Record both zero-based half-open line spans and
Unicode-code-point spans for each section's heading/body, immediate end and
subtree end. Include the original level, role and query-inclusion flag.
Re-parsing the exact local public source must reproduce all original semantic
fields and the first-author HMAC; no name or proposal text enters the bundle.

Query reconstruction follows the original pinned parser, including rendering
the heading, joining immediate section bodies, and excluding the header,
copyright and entire Motivation subtrees. Section offsets identify original
source pieces; they do not pretend the reconstructed query is one contiguous
source span. Each query retains the exact ordered fifty candidates, its truth
position and the forty-nine distractor IDs. No new candidate draw or model
context limit is applied.

Checkpoints seal every completed document projection. Resource/wall and
operational-document limits stop at document boundaries. Independent verification
re-parses every source and repeats every task join, with its own resumable
checkpoint, before bytewise bundle equality. The constructed fixture uses real
original parsing/allocation on fifty known proposal documents; it substitutes
only read-only git HEAD/status responses for its synthetic checkout. It creates
no Git commit, contacts no service and changes no original source checkout.
The unchanged original source qualification remains the production prerequisite.

The EX3 ceiling is 5,000 CPU seconds within EX 100,000; CPU only, at most two
numerical threads and projected memory 1 GiB. Amendment Q's first cost probe
remains inside the run. The local materializer accepts only the exact new ignored
EX3 directory after complete independent verification; the owner separately
handles any authorized recipient copy. The README carries original public-domain
or CC0 source scope, record ID, reconstruction convention and counts.

This design and its fixtures are prepared only, uncommitted and untested. A
complete matching GO1 R4 preparation must be supplied before production can
start. No source or task export was executed during build.
