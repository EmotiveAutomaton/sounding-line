# EX5: questions and the answer the asker chose

The two-day packet section 3G commissions a local benchmark export: 2,000
questions, 400 from each verified Stack Exchange site, with 3–8 answers and a
known accepted answer not written by the asker. This makes no scientific claim.

## DESIGN CHECK

Read LESSONS sections 2–5 and CONTROLS sections 6–7. The case requires enough
complete questions in every site and actual answer records, not a declared count
without records. The constructed control provides 401 eligible questions/site
and checks the expected lowest 400 hashes independently, every export field,
accepted-answer flags, code-point lengths, ties and privacy exclusions. A
399-question site must yield unsupported without a replacement sample. Full
source and bundle replay, immutable copied checkpoint reentry and source-change
refusal precede real admission. Smaller route: no reduced deliverable is claimed
as EX5; if its fixed support does not fit, record the cost/support hold explicitly.

## Inputs and exact selection

Reuse the exact five completed GO3 source runs and their verified `Posts.xml`
members. Authenticate each completion, native verification, archive/licence
binding and every output digest using the existing collection contract. No
archive is retrieved or extracted again; no user/profile table is loaded.
One public post row per XML line is a strict source-format check. The two parsers
(ElementTree execution and Expat replay) must recover identical fields.

Count actual answers in the current dump. Require 3–8, an accepted-answer ID
that joins to one of those answers, and known positive owner IDs for both asker
and accepted-answer author. Hash owner equality locally with the original source
salt; unknown ownership is excluded and counted. No owner ID or hash enters
the export. The accepted answer must have a different owner. No answer score
or posting order influences selection. A question's `source_row` is its one-based
row ordinal among all rows of the pinned Posts.xml. Rank SHA-256 of
`EX5|20261112|site|source_row` lexicographically and retain the lowest 400/site.

The declared 80–600-word gate uses the exported plain-text question body after
code-block replacement, split on whitespace. This is an explicit implementation
choice for owner review, before source inspection. Convert HTML to visible text
and normalize whitespace; replace each `pre` block by `[CODE_BLOCK:length=N]`,
where N counts Unicode code points of its decoded contents. Inline code remains
text. Record the lengths separately. No duration, embedding or language model
is involved. Malformed source markup is preserved as a source failure, not guessed.

Alternatives retained for audit: counting raw HTML whitespace tokens would count
markup; counting all rendered prose plus original code would count text the engine
does not receive. The candidate instead counts the exact exported body, including
each replacement marker as one word. For code length, UTF-8 bytes and rendered
words were alternatives; this candidate uses decoded Unicode code points.
These choices remain pending owner review, not treated as reviewed or ratified.
Source columns used are Id, PostTypeId, ParentId, AcceptedAnswerId, OwnerUserId,
Score, CreationDate, Title and Body. The complete original pinned member remains
untouched, so its original fields are recoverable by public ID and row ordinal.
SELECTION.json records those public IDs, ordinals and hash ranks, with column
names but no owner values; it is provenance, not another benchmark target.

## Export fields and provenance

Question: site, public question ID, title, transformed body, code-block lengths,
answers and public attribution URL. Each answer has its public answer ID,
transformed body and lengths, final score, posting order and accepted flag.
Posting order is source creation time, then numeric public post ID on an exact
timestamp tie. No source user fields are exported. Public URLs are generated
only from validated positive numeric post IDs and the fixed site allowlist.

Retain the supplied CC BY-SA 3.0 notice, cite original contributors through
each public post URL and describe the derivative text/selection transformations
in the README. Manifest pins complete upstream identities and exported files.
This is ignored local material; no publication or provider transfer is allowed.
The owner separately reviews the completed bundle and uses the existing EV4
procedure for the authorized copy to ToMpathy `.local/bench/EX5/`. The builder
does not execute a materializer or write outside the repository.

## Bounded pipeline and remaining gates

SQLite stores only needed post fields and private salted equality keys. Complete
source lines form approximately one-MiB blocks; the cursor retains byte offset,
site and exact source-row ordinal. A cooperative pause closes and hashes the
database with its cursor. Changed or unsealed output cannot resume. The owner
sets the first counted source quantum to at least 5% of actual total member
bytes, from pinned file sizes, if the forecast exceeds 7,200 CPU seconds; no
sample replaces the full five-site scan. Memory/commit/output guards remain the
existing runtime's. The first measured prefix excludes prior authentication,
selection and full replay and is not a complete cost claim.

After complete scan, produce all fixed site selections or an unsupported result.
Independent verification scans every pinned source again through its separate
parser, reconstructs all required fields, compares source/exclusion counts and
replays the complete bundle exactly. A partial verifier returns verified false.
All attempts, authentication, selection and replay share the 20,000 CPU-second
EX5 ceiling within remaining EX family allowance. CPU-only, at most two numerical
threads. Owner review/design filing, constructed checks, current source roster,
measured resources/cost and final local-copy review remain gates. Record kind
`run`, theory_tags empty, by_construction false for real source, activation empty.
