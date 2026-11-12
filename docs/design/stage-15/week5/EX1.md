# EX1: final-word stop labels and provenance, without text

**DESIGN CHECK.** Read the complete back-half packet and Round 12 handoff,
LESSONS section 2 and the Unicode-fixture lesson, the canonical UTF-16 replay,
P6 production-occurrence mapper and Week 4 timing ruler. This card exports
already qualified source labels; it fits no psychological or predictive model.
Canonical composition, multi-source words, repeated spellings, deleted and
reinserted text, unsupported timing and a stale source can make a plausible
looking export wrong. The fixture exercises exact source ancestry and full
producer/independent-verifier pause and reentry before any human source scan.

The complete canonical AT source supplies its exact P6 and Week 4 timing roots,
raw-log roster and repository root. All completion receipts and retained output
hashes are authenticated; its complete population is retained. An upstream-only
raw-log entry does not add a downstream session. Missing source sessions refuse.
No sampling, model selection, language model or new timing fit is performed.
The exact surviving occurrence locations come from this independently verified
AT source, rather than repeating its 5,074.734375-CPU-second preparation. Every
location row is joined to the same P6 occurrence and source/writer identity;
reconstructed final text must still match each supported location exactly.

Each final document is replayed through the original UTF-16 delta contract.
Initial characters retain prompt provenance. User insertions retain typed
provenance. API characters are classified as accepted suggestions only when the
original canonical handler verified the offered full-document insertion. Other
API or unknown-source characters are unresolved; they never become typed or
accepted merely by exclusion. Canonical replay errors refuse the source.

Normalize CRLF and CR to LF, apply `rstrip()` to the **whole document**, then
NFC-normalize. No per-line trimming occurs. Canonical decomposition, ordering and
composition preserve each code point's original ancestry; compare the resulting
string against Python's standard NFC implementation. Word spans use the
existing P6 TOKEN/WORD rules on this normalized text. Offsets are zero-based,
half-open Unicode code points. Hash the normalized text as UTF-8 SHA-256.
Neither the text nor word strings are written into the export.

Every final word remains. Uniform provenance uses the packet's three labels:
typed, accepted suggestion, prompt. As the owner directed during review on
November 11, mixed words use a **null source**, a mixed-provenance quality flag,
their constituent source labels and source code-point counts. Unresolved
provenance has a separate flag. A normalized point can combine multiple source
characters, so constituent counts can sum above word length; the README states
this. These quality fields create no fourth scientific source category.

Only wholly typed final words that exactly match a surviving P6 occurrence
receive timing. The occurrence key is original character ancestry, never
spelling. Its onset must join a unique Week 4 interval, with the frozen ruler's
onset support and positive single-character onset pause. The interval must agree
with the original production pause. Stop means fluent posterior strictly below
0.5. Log pause is the natural logarithm of that raw interval in seconds. Missing
or unsupported timing remains null and is counted, including modified words;
no excluded timing record causes a final word to disappear.

Writer identifiers remain the canonical hashed identifiers. The five-fold
assignment exactly follows the original AT rule: sort unique writer hashes,
NumPy seed 20261107 permutation, then round-robin five folds. All sessions from
one writer remain together. Session identifiers retain the original private
pipeline identity, which the receiving local replay must reconstruct.

Publication uses the existing UUID atomic JSON writer. Complete session files
are individually sealed by SHA-256 in a contiguous checkpoint. The operational
`max_new_documents` means complete sessions; `max_wall_seconds` and resource
yield requests also stop only at a session boundary. The fresh verifier
reconstructs every source session and compares every exported field, with its
own separately resumable checkpoint. It returns explicit `verified=False` on a
partial replay. Partial sources never become a materializable export.

The output bundle contains only schema-checked session JSON, an aggregate
manifest and a README stating definitions, counts, source notices and the exact
source ledger IDs. The owner-only local materializer requires an authenticated
complete producer and exact file inventory; it writes only a new
`corpora/store/exports/engine_bench_20261111/EX1/` directory. That path is ignored
under the existing `corpora/store/` rule. The owner separately performs and
records any authorized ToMpathy copy. No copy outside this repository or to a
provider is implemented by this card.

The original EX1 ceiling is 10,000 CPU seconds, the EX family ceiling 100,000.
CPU only, at most two numerical threads, projected RAM 3 GiB. Amendment Q uses
design and fixture for this already-qualified-source card; its first measured
cost prefix is inside the run. A partial prefix is not silently promoted to an
effect or export: the owner sets the exact first 5% ceiling from
the canonical population (70 of 1,399 sessions) if required by its forecast,
checks costs and remaining family headroom, then admits continuation. The
completed full source and independent replay precede local materialization.

This design and fixture are newly prepared and unadmitted. No corpus scan,
timing re-fit, statistical test, native start or local export was executed during
build. Targeted constructed checks await the owner's serial test token.
