# D24 closure instrument: native known-answer pilot

**Question.** Does the frozen closure measure distinguish held-out literal endings from matched incomplete passages and reproduce its scores?
**METHOD.** Score twelve held-out endings and twelve matched incomplete passages with the fixed lexical/MiniLM composite, retaining cosine alone, anchor-self sanity, a misleading lexical example and uncached repeated-forward identity.
**Found.** Both held-out directional checks pass and repeated scores match; the misleading midstory example still receives a high closure score. **Means.** The native instrument can run the registered comparison, but this small known-answer check does not establish semantic specificity, intention or a need-state measure.

The table reports ending-minus-incomplete mean score differences. The composite
equally weights lexical cues and rescaled anchor cosine; cosine is also separate.
No hypothesis probabilities are computed for this instrument check.

| Known-answer check | Difference or outcome |
|---|---:|
| Held-out composite | 0.22048332 |
| Held-out cosine | 0.04859995 |
| Uncached repeated forward | exact match |
| Misleading midstory composite | 0.78420100 |

The held-out examples are disjoint from the twelve frozen anchors. Anchor-self
similarity is a sanity check only. The misleading lexical case remains an explicit
false-positive limitation. Native first 254-token truncation is recorded; lexical
matching sees the full text. Seven original synthetic controls and three focused
held-out checks passed; the actual CPU pilot independently verifies all 33 pins
and 13 output hashes. Native workers exited and released their counted slot.
This pilot contains no study outcomes and admits only the registered main
execution under its existing 900-second forecast and 2700-second cap.
[Aggregate receipt](D24-pilot.json).
