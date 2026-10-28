# FIC1 gallery preparation and length adjustment

This implements the length covariate requested by Week 3 FIC1 without computing
human identification or its controls. It consumes only the completed FIC1
session features and exact prefix preparation, retaining all original writers,
sessions, genre/prompt halves and dictionary. LESSONS sections 3–5, CONTROLS
sections 1–7 and the play/genre theory row and afterword were reread on October 27.

Typed style and rhythm use the completed pooled prefix vectors, preserving
their full token denominators and pooled interval medians. Final-document
style pools word and punctuation counts across the original profile members;
the accepted-character covariate is total accepted characters divided by total
final characters, not the mean of session shares. Final text remains mixed
prompt, model and typed production. No source text is transferred.

The full-length nuisance is log base two of the profile's actual word count.
Each feature is regressed on an intercept and this covariate using the gallery
half B only. The fitted coefficients apply to both halves. Raw full vectors
are retained. Final style also retains the separately adjusted length-plus-AI
share form required by the inherited page controls. Fixed-length vectors stay
raw. Every later reassignment and independent-donor rotation must rebuild its
profiles and refit on its own gallery B; observed fitted values cannot substitute
for a reconstructed reference. This component does not define or license that
reference implementation.

No feature imputation precedes fitting. Missing feature/covariate rows remain
missing; absent or rank-exhausted fits are unsupported. Collinear covariates
are recorded by their actual rank. Residual numerical zeros below 1e-12 use the
existing gallery's numerical scale rule. Later matching keeps the established
B-only scaling and partial-missing imputation, complete fixed gallery and
fractional ties. The gallery is never bootstrapped; paired writers are.

Support is explicit for each level across both genres and halves. The all-length
common writer set is also retained so a future length trend can distinguish
sample composition from added evidence. No unsupported profile is padded,
silently removed from its census or promoted to a zero score. A consumer still
has to freeze its complete paired-support and length-trend rule before scores.

Known-answer tests remove pure linear length and AI effects, preserve an
orthogonal planted fingerprint, verify that altered probes cannot alter fitted
coefficients, retain missing and rank-exhausted cases, and check exact pooling,
source membership, serialization, immutable reentry and altered-output refusal.
Those numerical checks validate this transformation only. The complete
identification calibration, permutation and context references, paired genre
table, scored length curve and full-design cost admission remain unbuilt.
AUTH's primary stays separately gated. Original failed gates are unchanged.

This preparation, its tests and native replay count toward FIC1's original
7,200 CPU seconds. The preceding complete prefix landing charged 1,556.109375
seconds. Reserve 120 additional seconds for this build and targeted checks;
native validation is capped at 120 seconds and complete preparation at 300,
with one numerical thread, 4 GiB projected RAM and a 256 MiB output cap.
