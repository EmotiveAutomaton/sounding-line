# Bounded source acquisition

This is source preparation, not an analysis or a claim of corpus-wide inference.
DESIGN CHECK: LESSONS 3–5. Missing continuation, duplicate revisions, altered
checksums, hidden fields and exhausted limits refuse complete-history claims.
Complete source bytes and continuation receipts permit a later fixed analysis.

Wikipedia: freeze five named pages and 100 namespace-zero random pages from one
retained official API response. Fetch complete revision **metadata** in chronological
order, including IDs, timestamps, editor, comment, SHA-1 and tags. This first
pass supports T3 shape extraction; it is not the full-text/diff input for D8.
Retain hidden fields as missing. Freeze the upper timestamp at preparation so
new edits cannot shift the census during pagination. Bounds: one request at a
time, 5,000 requests, 1 GiB response bytes, 250,000 revisions, four hours. A
truncated article is never reported as a complete history. Later text acquisition
is separately counted and bounded, with retained metadata identifying every edit.

The official revision API allows up to 500 metadata revisions per call, but only
50 when content is included. [API contract](https://www.mediawiki.org/wiki/API:Revisions/en).

Lichess: retain the official checksum list, then download July 2026 standard
rated games, the smallest of the last three completed months by the current
index (July–September). Bounds: 35 GiB, one stream, 12 hours, at least 50 GiB
free disk before start and the ordinary resource floors throughout. Require
exact Content-Length when supplied, EOF and the published SHA-256 before
completion. No automatic restart or unreviewed range resume. Download completion
does not authorize unbounded inference; cohort/game/position caps and complete
parser tests precede the 100-player pilot and any full scoring.
[Source and CC0 release](https://database.lichess.org/),
[checksums](https://database.lichess.org/standard/sha256sums.txt).

DICES: keep the complete 123-rater main panel. The paper's 104-rater sensitivity
cannot be reproduced from an invented exclusion list. The upstream unresolved
[quality-filter issue](https://github.com/google-research-datasets/dices-dataset/issues/2)
asks for the missing rater identities or exact criteria. This blocks only that
sensitivity reference; no authors are contacted.
