# CLAIM ANCHOR CORRECTION 20261029

**Hypothesis.** Does each claim-ledger source pointer identify its own finding rather than a later correction with a similar identifier?

**METHOD.** Compare every FINDINGS source anchor with an exact full heading, require exactly one match, and inspect mismatches against the retained entries. Exercise the actual record writer on a constructed original/correction pair and on missing and duplicate headings. Refresh line pointers and source hashes after recording this correction, then compare all pre-existing non-source claim fields byte-for-byte as parsed records.

**Correction.** The private record writer used prefix matching. S15-GEN1, S15-CA5 and OPS-S15-W3-TR4-H1-COST pointed to suffixed headings. Each original entry exists uniquely. The writer now requires exact equality and refuses missing or duplicate headings. The old active-corrections entry explicitly qualifies its earlier, weaker anchor audit. The prior ledger is retained privately for replay.

**Found.** Three claim-source pointers are corrected to exact original headings; all findings and scientific outcomes are retained.

**Means.** This is a provenance correction, not a reanalysis or a change in a result. All existing public wording, estimates, scope, supersession and pursuit fields remain unchanged. The historical TR4 cost hold remains superseded by its recorded admission correction. Native research work and its immutable source closures are unaffected. The ready buffer remains incomplete.
