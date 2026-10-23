# GEN1: source-bound genre matching

The [week packet](WEEK_PACKET_20261018.md) commissions a same-writer comparison
between creative and argumentative writing. This component prepares its matched
input; it does not compute identification or a scientific contrast.

The frozen PMAP plan binds the original genre roster through its completed
foundation, and the completed production-word ledger through its verified index
and per-session hashes. Session, writer, prompt and timestamp must agree exactly.
Every source record is checked, including records subsequently excluded for
insufficient support. Source bindings and the complete matching manifest are
reconstructed in an independent process.

Under S5, matching uses deterministic prompt round-robin selection, with prompts
ordered by first session time and ties by prompt identifier. Within prompts,
sessions follow time and session identifier. Take the smaller genre's session
count, pair the selected sessions by round-robin position, and retain the smaller
pair member's completed typed-word count in both sessions. Keep the exact prefix
of the completed-token ledger through that word, including trailing punctuation
only when all typed words are retained. This is an explicit exposure-matching
choice, not selection by observed identification or style. Original full data
remain available; the matched question has its own scope.

The original eligibility census uses at least four sessions and two prompts in
each genre. With at least fifteen eligible writers, form PMAP's alternating
prompt halves separately within each genre. Otherwise use one alternating split
across both genres, explicitly exploratory. Zero-word records cannot contribute
positive matched exposure; retain their reasons and any resulting writer loss.
Falling below the primary support floor after those exclusions does not silently
change the selected mode. Missing genre-by-half cells remain missing. Whole-genre
session and typed-word totals match within each retained writer; prompt halves
need not have equal totals.

The ledger contains completed production occurrences, including later-deleted
words. Completion order is not necessarily raw-event order. Exact word indices,
token-prefix positions and event boundaries are retained. A boundary that splits
an event is explicitly flagged. A raw-event cutoff alone cannot reconstruct the
retained timing atoms. Neither complete-session rhythm aggregates nor later text
may be substituted for matched features.

Admission checks cover exact balancing, prompt diversity, timestamp ties, Unicode,
zero/missing support, primary/fallback separation, malformed records, altered
sources and altered saved outputs. These checks validate the matching component
only. The feature reconstruction, fixed galleries, planted/null controls, 2,000
paired writer draws, 200 session reassignments, within-writer reference and
same-row fake-writer comparison remain required before scientific admission.

Execution uses the existing counted, contained native runtime and watcher.
The original one-CPU-hour ceiling uses the existing conservative two-thread
conversion of 1,800 wall seconds; any S4 doubling is cumulative and available
only once. Reserve 120 seconds for this build and native validation; charge all
subsequent execution and fresh replay. The corpus preparation has a combined
600-second hard cap. This does not reserve or admit the unfinished comparison.
No paid work, new family count, GPU dispatch or genre-weighting claim follows.
