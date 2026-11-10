# GO1 single-author texture

Week 5 section 0.6 explicitly asks for a texture excluding multi-author PEPs
and EIPs. This cell was missing from the original GO1 grid. It reuses the
complete selected-reader pipeline and changes only the eligible documents:
exclude every current pinned document whose parsed header has multiple
authors, before allocating any query or distractor. A missing or non-boolean
authorship flag refuses; missing metadata never means one author.

The primary configuration keeps 49 distractors and the original same-stratum
fallback, all three readers, full-context support intersection and the
author-cluster comparison. Every reader receives the newly frozen identical
roster. Existing score banks with different documents or allocations refuse.
The same source manifest and admissible AT2 model/revision/numerical selection
remain required. No model, threshold, likelihood or feature is selected anew.

Report all source documents, excluded multi-author documents, eligible
single-author documents and author clusters. The texture uses 200 complete
cluster draws and cannot upgrade a primary claim; the existing below-floor
descriptive fallback remains. It uses current documents, not a guess about
which historical revisions had one author. GO2 historical authorship requires
its own source-supported projection before that separate cell can run.

## DESIGN CHECK

- **Case and check:** a fixed roster must contain only documents explicitly
  marked single-author. Native constructed worlds include excluded documents
  whose apparent retrieval signal is deliberately strong; none may enter the
  query roster or distractors. All three complete score banks, collection and
  fresh replay are exercised with signed and null known score banks, 49
  distractors and 200 draws. Selected-reader precision remains qualified by
  its separate actual-transformer proof; this fixture isolates filtering and
  complete bank alignment rather than claiming model performance.
- **Smaller route:** use the existing whole-author sample rule following the
  counted first-5% cost stage. The ordinary 3,600 CPU-second texture ceiling
  and 600,000-second GO family ceiling apply. A roster with too few eligible
  candidates records unsupported scope; never fill it with excluded authors.

Module `week5_go1_single_author` delegates the unchanged numerical work to
`week5_go1_pipeline_v2`. Exact same producer quanta must be retained on resume
under the current adapter. It remains dependency-waiting for the full AT2
selection, like the original GO1 comparison. No human results were read to
choose this packet-specified filter.
