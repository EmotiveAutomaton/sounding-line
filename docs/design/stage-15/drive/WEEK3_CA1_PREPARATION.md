# CA1 source preparation and CPU encoder intake

The October 25 packet commissions an individual preference reader against
country and population readers. These two preparation handlers do not fit that
reader or announce a scientific result.

`week3_alignment_inputs` authenticates completed CA0 and reconstructs exactly
its usable turn population from the same source bytes. It emits a private
turn table, deduplicated candidate/prompt texts, and an outcome-blind split.
The public summary contains only counts and checksums. Participant identifiers
are hashed within this dataset; no cross-dataset identity join is attempted.
Hashes are pseudonyms, not a claim that participant data are anonymized.

The split joins every conversation's turn prompts and every repeated exact
prompt into connected components within each annotator. Components are assigned
to halves by seeded, largest-first balancing of prompt counts. This prevents
both repeated prompts and different turns of the same conversation crossing
training and evaluation. An annotator with one connected component cannot
supply this split and is recorded as unsupported. The rule uses no preferred
candidate or explanation. It preserves the original eligibility threshold
before checking this additional split feasibility.

The private prepared table retains country, language, wave, turn number, selected
candidate, full preceding context and explanations for the commissioned downstream
cards. It invents no chronology between conversations. Explanations are not
CA1 choice-prediction features. Full replay reconstructs every output line and
all partitions, then verifies their retained file hashes.

`week3_alignment_model` downloads only the declared files of the fixed
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` revision
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. This is the public encoder selected
in CA0, under its Apache-2.0 model-card license. It makes no inference, paid call,
GPU request or participant-data transfer. The download is serial and the retained
capsule is capped at one billion bytes; fresh verification hashes every file.
The owner must dispatch network intake separately from scientific feature work.

Six source/split tests and three mocked-transport model-intake tests pass. These
cover complete CA0 binding, split leakage, unsupported components, choice-label
invariance, exact replay, changed private outputs, fixed revision, exact download
allowlist and mutated/missing weights. Native validation, real model download,
actual source preparation, embedding timing and the statistical reader remain
separate owner dispatch/build steps.

`week3_alignment_features` is also built. It binds the completed prepared input
and model capsules, embeds only candidates and current prompts on two CPU
threads, and creates the fixed 50-cluster prompt fallback. Each 512-text chunk
has a private checksum and timing receipt; continuation authenticates saved
chunks, while fresh verification re-encodes all of them in the same batch layout.
No text is sent to a provider. The pinned encoder's 128-token limit is retained
and explicit; the resulting reader concerns this representation of the choices.

The first feature run selects 10% of comparisons with the frozen seed, without
using their choices. It is timing-only. Its projection covers one encoding pass;
admission must add a second fresh pass, source work and statistical fitting.
Pilot chunks are not silently reused in a differently batched main encoding.
The full mode requires all prepared comparisons and all 50 prompt clusters.
Six additional constructed checks pass: outcome-blind sampling, actual handler
and full replay, interruption/continuation, tamper detection, completion binding,
and refusal of inadequate full-cluster support. Real CPU embedding throughput,
the full feature table and the statistical reader remain owner dispatch or build
steps; these tests do not establish a preference direction.
