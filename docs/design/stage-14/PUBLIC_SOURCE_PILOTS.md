# Public source intake pilots, October 10

The curator answered **“Allow both public sources”** to the question naming public
Wikipedia revisions through its official API and licensed GitHub blog histories,
with all text and computation kept local. This resolves source policy only.
No new scientific hypothesis was harvested from the approval.

These two pilots test acquisition and exact history retention. They do not admit
reconstruction, a personal-learning main, or fresh confirmation. Reader release
cutoffs remain to be verified before evaluation partitions are frozen. Dates here
are acquisition windows, not claims about training-data exclusion.

## Frozen selection and limits

Wikipedia: main namespace, four fixed pages (Artificial intelligence, Climate
change, Python (programming language), Music), September 1 through October 2,
2026 UTC. Inspect the first 100 ascending revisions per page, exclude anonymous,
hidden and current bot-group accounts, then retain the first eight eligible exact
parent/child pairs. Current group membership does not establish historical human
authorship. Pagination truncation and the shortfall from 64 editors remain explicit.
Reverts are unassessed, never negative by default; seven-day follow-up is a later
separately frozen task. No model sees revision summaries or future fields.

Blogs: freeze the first twelve candidates from the already retained GitHub search
for public, unarchived, non-fork personal blogs with a CC-BY-4.0 repository label,
ordered by stars. A search license label is insufficient for prose admission.
The executable card fixes the roster before reading edit outcomes. First inspect
metadata, historical root license and README. Only an individually reviewed,
explicit prose grant matching its retained README hash permits text acquisition.
The initial reviewed grant is sanctum-black/blog's explicit all-content CC-BY-4.0
statement; preserve every other candidate's rights-review hold. Inspect at most
two alphabetically selected nested Markdown documents and the newest listed change
per document in January 2023 through October 2, 2026. Retain every parent and
author/committer record, and require the prose grant and identical license at both
versions. Merges, missing parents and unchanged files are excluded explicitly.
The main's 20 dated posts, 30 document commits and eight post-reader-cutoff changes
remain unverified; this pilot cannot claim those criteria or author independence.

Each pilot has a 180-request ceiling, serial requests spaced at least one second,
a 30-minute acquisition ceiling within the two-hour integration bound, response
and text byte limits, and no automatic network retry. Server refusal remains a
failure or recorded source exclusion, not permission for a different route.
Wikipedia uses an informative User-Agent and maxlag=5. GitHub uses existing CLI
authentication only for public read endpoints; credentials are neither read nor
saved. No downloaded code is executed. Request/response hashes, attribution and
rights evidence stay beside exact UTF-8 text in the ignored local raw store.

## DESIGN CHECK

LESSONS sections 2-5 and the source/reader theory sections and afterwords were
reread. NULL: code-only rights, missing/hidden content, mismatched hashes, absent
parents or incomplete support refuse admission. ALTERNATIVE: valid exact pairs
are retained while scientific admission remains false. Every outcome is retained
as a pair, exclusion, source hold or failed attempt. No binary fresh label is
inferred from an absent exposure record. Known-byte Git/Wikipedia fixtures,
hidden-content refusal, parent chronology and the unchanged worker's completion
guard are tested before dispatch. Outcomes cannot select pilot pages or documents.

API references: [MediaWiki revisions](https://www.mediawiki.org/wiki/API:Revisions),
[request etiquette](https://www.mediawiki.org/wiki/API:Etiquette), and
[GitHub trees](https://docs.github.com/en/rest/git/trees). Their interface guidance
does not supply this project's scientific admission criteria.
