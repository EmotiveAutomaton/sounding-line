# Stage 4 curator packet (final, the only one)

Run 2026-08-27T22:22:50 to 2026-08-28T22:22:50; label RUN_TO_EMPTY; contract eb45570a6e779d0a.

## What changed in the model of the world

Support candidates: A01, T01, T02, P02, F01. Valid nulls or counterevidence: C03, A02, A03, T03, H01, H02, H03. Instrument failures: none. (Plain-language synthesis is written by the analyst after the run from these classes; this section is the machine draft.)

## Tracks

| track | asked | observed | leading explanation | strongest rival | pursuit | warrant | next decision |
|---|---|---|---|---|---|---|---|
| context | Did contextual adjustment improve new predictions beyond the same facts, and did individual evidence correct a wrong adjustment? | C01 INCONCLUSIVE (+0.085); C02 INCONCLUSIVE (-0.084); C03 COUNTEREVIDENCE (-0.257) | see appendix | see card controls | OPENED | NONE | analyst |
| appraisal | Did appraisal steering help predict someone else, or only change the reader's own answers? | A01 SUPPORT_CANDIDATE (+0.109); A02 COUNTEREVIDENCE (-0.080); A03 VALID_NULL (-0.052) | see appendix | see card controls | PROMISING | BOUNDED_MODEL_EFFECT | analyst |
| transmission | Did a message's transmissibility, usefulness, and source transparency come apart, and did the reader preserve useful uptake while resisting misleading selection? | T01 SUPPORT_CANDIDATE (+0.146); T02 SUPPORT_CANDIDATE (+0.623); T03 VALID_NULL (-0.008) | see appendix | see card controls | PROMISING | BOUNDED_MODEL_EFFECT | analyst |
| hierarchy | Did relay/edit dependencies identify historical choices beyond conventions, superficial anomalies, and annotation persistence? | H01 COUNTEREVIDENCE (-0.134); H02 VALID_NULL (-0.004); H03 COUNTEREVIDENCE (-0.011) | see appendix | see card controls | OPENED | NONE | analyst |
| physical | Did a final physical artifact provide action information beyond cheap shape priors, and how much extra information came from process records? | P01 INCONCLUSIVE (+0.037); P02 SUPPORT_CANDIDATE (+0.198) | see appendix | see card controls | PROMISING | BOUNDED_MODEL_EFFECT | analyst |

*Table: one row per track; the analyst's synthesis replaces the placeholder cells after the run.*

## The five questions

1. Did contextual adjustment improve new predictions beyond the same facts, and did individual evidence correct a wrong adjustment? C01: INCONCLUSIVE; C02: INCONCLUSIVE; C03: COUNTEREVIDENCE.
2. Did appraisal steering help predict someone else, or only change the reader's own answers? A01: SUPPORT_CANDIDATE; A02: COUNTEREVIDENCE; A03: VALID_NULL.
3. Did a message's transmissibility, usefulness, and source transparency come apart, and did the reader preserve useful uptake while resisting misleading selection? T01: SUPPORT_CANDIDATE; T02: SUPPORT_CANDIDATE; T03: VALID_NULL.
4. Did relay/edit dependencies identify historical choices beyond conventions, superficial anomalies, and annotation persistence? H01: COUNTEREVIDENCE; H02: VALID_NULL; H03: COUNTEREVIDENCE.
5. Did a final physical artifact provide action information beyond cheap shape priors, and how much extra information came from process records? P01: INCONCLUSIVE; P02: SUPPORT_CANDIDATE.

## Appendix: execution

Elapsed 21.184 h; GPU lock held 14.95 h; recorded lost time 0.0 h; full window completed: False.
Cells: {"COMPLETE": 28}. Outcomes: {"VOID": 4, "INCONCLUSIVE": 4, "COUNTEREVIDENCE": 6, "SUPPORT_CANDIDATE": 9, "VALID_NULL": 5}. Coverage: 307/322 expected cells complete; 0 missing; 15 under floor.
Tier minimum; label FULL; deferred []; readers ['Qwen/Qwen2.5-1.5B-Instruct', 'HuggingFaceTB/SmolLM2-1.7B-Instruct'].
Expansion ladder: rung 1 (more worlds) implemented; rungs 2 and 3 predeclared and not reached unless listed above.

## Appendix: per-card verdicts

- **I01** COMPLETE / VOID: ; point not measured, ci None, n None; 
- **I02** None / None: ; point not measured, ci None, n None; 
- **I03pilot** COMPLETE / VOID: ; point not measured, ci None, n None; 
- **I03** COMPLETE / VOID: ; point not measured, ci None, n None; 
- **C01** COMPLETE / INCONCLUSIVE: bundle minus facts, future-choice log score; point +0.085, ci [-0.021905471803507704, 0.19751844328163812], n 256; interval includes zero and cannot exclude a useful benefit
- **C02** COMPLETE / INCONCLUSIVE: misleading-prior correction, records 6 minus 0, direct route; point -0.084, ci [-0.20628777807392687, 0.030982755925911886], n 256; interval includes zero and cannot exclude a useful benefit
- **C03** COMPLETE / COUNTEREVIDENCE: fraction of the oracle's exact gain captured by the reader's selection, minus the random selector's third; point -0.257, ci [-0.2696078431372549, -0.2434640522875817], n 204; interval entirely below zero
- **A01** COMPLETE / SUPPORT_CANDIDATE: valuation and audience-aim recovery over 0.25; point +0.109, ci [0.06313864716080032, 0.15889398079207204], n 256; directional support at or above the frozen threshold
- **A02** COMPLETE / COUNTEREVIDENCE: appraisal-aligned steering benefit, target log score; point -0.080, ci [-0.14450272348542026, -0.01154656068577261], n 256; interval entirely below zero
- **A03** COMPLETE / VALID_NULL: context-phase minus answer-phase aligned benefit; point -0.052, ci [-0.11764834809880566, 0.014662274923258183], n 128; interval includes zero and excludes a practically useful benefit
- **T01** COMPLETE / SUPPORT_CANDIDATE: support effect on novel-case application, aligned stratum; point +0.146, ci [0.111328125, 0.181640625], n 256; directional support at or above the frozen threshold
- **T02** COMPLETE / SUPPORT_CANDIDATE: reconstruct2 minus summary2 judgment log score, uptake preserved; point +0.623, ci [0.5029255312366095, 0.752641165501402], n 256; directional support at or above the frozen threshold
- **T03** COMPLETE / VALID_NULL: technique minus control reliability AUROC on the held-out family; point -0.008, ci [-0.018402099609375, 0.002777099609375], n 256; interval includes zero and excludes a practically useful benefit
- **H01** COMPLETE / COUNTEREVIDENCE: constraint retention hop 3 minus hop 1, shared minus remapped convention, director; point -0.134, ci [-0.24390243902439024, -0.012195121951219513], n 82; interval entirely below zero
- **H02** COMPLETE / VALID_NULL: history-type recovery, ordered history minus artifact-only; point -0.004, ci [-0.025520833333333336, 0.018229166666666668], n 192; interval includes zero and excludes a practically useful benefit
- **H03** COMPLETE / COUNTEREVIDENCE: online next-boundary forecast beyond duration and persistence; point -0.011, ci [-0.021087115770145416, -0.0007457961559823812], n 5; interval entirely below zero
- **P01** COMPLETE / INCONCLUSIVE: first-stroke quadrant from the final raster minus the best cheap prior; point +0.037, ci [-0.017426271693954713, 0.08947113174901127], n 788; interval includes zero and cannot exclude a useful benefit
- **P02** COMPLETE / SUPPORT_CANDIDATE: learned first-stroke identification minus geometry heuristic (unordered access); point +0.198, ci [0.16243654822335024, 0.233502538071066], n 788; directional support at or above the frozen threshold
- **F01** COMPLETE / SUPPORT_CANDIDATE: ; point not measured, ci None, n None; 

Claims in the ledger: 2.

---

## Analyst synthesis (written 2026-08-28 23:50, after the run; the machine draft above is unedited)

### What changed in the model of the world

**The readers in this family can be taught and cannot be defended, and they can be read but not
steered into reading better.** Three things landed that were not known on the 27th. First, a
small reader keeps a maker's *appraisal* and its *intended audience response* apart from what
happened and what is true, weakly, and that separation held on an untouched reserve (A01,
confirmed). Second, a worked example makes a lesson's rule learnable whether the rule is true
or false and whether the source is helping or steering, while what the reader then *does*
follows the source's advice regardless; that too held on the reserve (T01, confirmed). Every
attempt to make uptake selective failed in the same direction: reconstructing the source's
selection rule costs against reading directly because the readers cannot infer the rule they
can use when told (T02); a lesson in misleading techniques raises no discrimination and lowers
acceptance of everything, true advice most (T03). Third, and against the theory's model-side
hopes, every context card came back empty from a different direction (framing not content,
C01; no correction, C02; no active reading, C03), the valence handle moves the reader and
lowers its prediction of the maker (A02, A03), and relay and history read as convention, not
as a director's choice or a tradition's change (H01, H02). The physical track kept its one
support (P02: strokes as an unordered set carry the first stroke beyond geometry) and its one
inconclusive (P01).

**The Stage-3 re-runs that rode behind the run change two entries of the standing record and
open one door.** The family signature does not survive the stake-free eraser once both families
are powered (zero, L251); the wish override stands parser-free at 0.79 and 0.92 (L252); the
transmission channel's carrier is present and surface-trivial, so that failure is at uptake
(L254); suggestion uptake tracks fit a little and position a lot (L253); and steering a reader
with a held-out maker's true tendency direction raises its inference about that maker where a
random direction does not (L255): the first causal-use-during-inversion result, oracle-directed,
one checkpoint, one domain.

### Tracks

| track | leading explanation | strongest rival | pursuit | warrant | next decision |
|---|---|---|---|---|---|
| context | these readers treat any preamble as an instruction and take its frame, not its content; they neither correct on records nor choose evidence by information | the constructions' contexts are too thin to reward a maker model (the exact ruler gains only 0.13 to 0.16 from six records) | CLOSED model-side at this scale | NONE | none; the mechanism rests on human evidence |
| appraisal | the products (appraisal, aim, action, fact) are separable in the reader and confirmed on the reserve; the valence handle grips the reader's own continuation and hurts its model of the maker | the separation is thin (0.32 to 0.41 balanced against 0.25) and thinnest where a maker induces what it does not feel | PROMISING for the separation, CLOSED for the valence bridge in this family; the tendency representation's causal use (L255) is the live door | BOUNDED_MODEL_EFFECT | fund the second checkpoint and domain for L255 (about an hour of GPU) |
| transmission | legibility and usefulness come apart: a worked example teaches a false rule as well as a true one, uptake follows the advice whatever the reader learned, and no route tried makes uptake selective | the readers are too weak to infer a source's rule at all, so selective uptake is untested rather than absent (the oracle ceiling +0.4 says the information is usable when handed over) | PROMISING for the dissociation (confirmed), CLOSED for selective uptake in this family | BOUNDED_MODEL_EFFECT | none |
| hierarchy | relay keeps the convention and loses the choice; ordered history adds nothing to type recovery and costs on the next decision; the human record's next-intention signal is temporal, not lexical | three hops and twelve steps are short; the makers are the same weak family as the readers | CLOSED at this scale | NONE | none |
| physical | an unordered stroke set carries the first stroke beyond geometry (P02); the raster does not beyond cheap priors (P01) | the learned prior fits drawing conventions rather than action | OPENED | BOUNDED_MODEL_EFFECT | none owed |

*Table: the analyst's replacement for the machine draft's placeholder cells; classes and numbers are in the per-card entries (FINDINGS L236 to L255).*

### The five questions, answered

1. **Contextual adjustment** did not improve new predictions beyond the same facts (+0.09 nats, crossing zero), a wrong context cost nothing, individual evidence corrected nothing (a flat curve), and the readers did not choose evidence by information (8 percent of the oracle's gain). The mechanism has no model-side analogue here.
2. **Appraisal steering** changed the reader's own answers (a fifth of the mass) and lowered its prediction of the maker (-0.08 nats, below zero at 256 worlds); steering during intake did no better than during the answer. The appraisal *products* are recoverable and confirmed; the valence *handle* is not a way to read a maker in this family. The tendency representation, by contrast, is causally used to infer a held-out maker (L255), with the floor unmet.
3. **Transmissibility, usefulness, and source transparency come apart**, confirmed: learning +0.15 whatever the truth and intent, uptake of the advice above 0.92 regardless, the source's goal read at 0.32 to 0.63 and never with uncertainty. The reader did not preserve useful uptake while resisting misleading selection by any route: reconstruction costs, technique lessons shift the criterion.
4. **Relay and edit dependencies** did not identify historical choices beyond conventions: the shared convention keeps a little more of a director's constraint and the flipped constraint is kept as often; the readers call every tradition a shared brief; ordered history adds nothing; the human record forecasts its next boundary by duration, not text.
5. **A final physical artifact** carries action information beyond cheap shape priors as an unordered stroke set (+0.20 over the geometry heuristic, P02) and not as a raster (+0.04, crossing zero, P01); process records were not tested beyond that split.

### Read the receipts with these in view

- **Fifteen control cells sit under the coverage floor.** Twelve are structural: the withheld-fact and mismatched-target controls exist only in the worlds where the fact is withheld or the profile breaks its context (about half), and the floor is set at the full unit count; the A02 own-choice control records a probability vector and no score. Three are honest: H01's workshop cells reached 40 to 42 complete chains of 48 required (hop-zero realization 0.85 overall, lower in that domain). No expected cell is missing.
- **One duplicate construction** among 3,104 root units: a same-domain seed repeat in A01's expansion, caught by the live duplicate control (the control that could not fire on the 27th); the card clusters on the id, so its 256 is 255, a difference under a point.
- **The T-track was rebuilt mid-run** (TODO R7): the first T01 attempt on 54 distinct constructions is preserved and superseded; every T-track number here is from the enumerated construction with hashes on every row.
- **Pre-repair discovery roots** (C01, C02, A01, A02, T01's first attempt) carry no content hash by construction; the id-rebuild audit covers them and reads all distinct.
- **The label** is RUN_TO_EMPTY under the 2026-08-28 ruling; the brief's 24-hour window is accounting (21.2 hours elapsed, 14.95 GPU-lock hours held, no lost time recorded beyond the two deliberate stops).
- **The machine draft's I02 line reads `None / None`** because the reader-gate card writes its verdict without the exec and outcome keys the draft prints; its content (both readers admitted at 0.94 and 0.88) is in L236's fold-in and the freeze record.
- **The readers are one family** (two 1.5B-class instruct checkpoints); every null above is a null for this family at this scale, never for the world; the two confirmations are model-scope claims.

### Decisions requested

1. **L255's floor (Yes recommended):** a second reader checkpoint and a second artifact domain for the held-out maker causal-use read, about an hour of GPU, before the affect-to-inversion bridge is called built.
2. **The Stage-3 assessment** on the record as it now stands (L171 to L235 plus L251 to L255), and the Stage-4 assessment on this packet.
