# TR3 discovery suggestion candidate counts

This is a component of the commissioned TR3 comparison under its original
7,200 CPU-second ceiling. The exposure and typing sources are complete. This
component prepares the model-side counts needed for discovery-only selection;
it does not choose a feature threshold or inspect a human carryover outcome.

DESIGN CHECK: LESSONS 2-5 and the Three Cognitive Layers habit account and
afterword reread on October 26. Under NULL and ALTERNATIVE, known text has exact
counts, reopened menus contribute once, and test writers never feed discovery.
Missing or changed source, split membership, menu identity, or independent
replay refuses. Exhaustive states are verified counts or explicit failure;
neither is a scientific result.

Reuse the existing produced-word tokenizer from `timing_text`. Count all word
unigrams, bigrams and trigrams, with Unicode case folding, and literal Unicode
category-P punctuation. Only whitespace may connect words in an n-gram:
punctuation, symbols and unparsed non-whitespace break the run. Never join
different alternatives. These counts include function words and short hedge
phrases as lexical candidates; they are not semantic function or hedge labels.
No candidate is selected or dropped by observed frequency in this component.

Use the exact WB1 writer split from the completed chronological source. Read
only the 745 discovery-session payloads. Each original menu and each of its
offered alternatives contributes once. A reopen must match its original menu
and contributes no new frequency mass. Empty orphan reopens remain counted
as empty records without an invented offer. Repeated identical text in distinct
original offers remains distinct; dose counting is a separate later quantity.

Save per-session counts, aggregate occurrence counts and session support for
every candidate. Validate raw parent hashes and exact population, then replay
all counts in an independent process. The test half remains in the population
census but its suggestion payloads are not read by this component. The fixture
deliberately omits its test payload to exercise this boundary. Tests also cover
Unicode, punctuation, symbols, apostrophes, repeated text, no adjacency across
sentences/offers, empty menus, changed split/menu identities and output tamper.

Reserve 60 additional CPU seconds for construction and tests. The native
fixture receives at most 60 CPU seconds; full counts and independent replay
receive at most 600, all charged to TR3's unchanged ceiling. Preserve prior
charge/reserve of 1,350.71875 seconds. No GPU, paid work or holdout access.
Human production-time counts, model-versus-human pointwise mutual information,
feature selection, matched unseen placebos, calibration and full-study cost
admission remain separate gates.
