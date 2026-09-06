# Stage 8: corrected final curator packet

Dated 2026-09-06. This derived correction supersedes the interpretation of the preserved original packet; it does not replace raw results or reopen the stage. Administrative integrity is revalidated; scientific limits and curator ratification remain separate.

## Pass A

The hypothesis was that a reader able to run the standard process could recognize a maker in its departures and accumulate that maker across works. METHOD: Stage 8 trained two local readers on maker-free process logs, tested prediction and generation separately, then compared surprise, purpose use and earlier-artifact context with the domain model and known construction truth. Neither reader passed generation, so the subsequent results are diagnoses rather than tests on admitted experts. Prediction improved while surprise ranked maker departures in the wrong direction; proposed purposes hurt prediction, and earlier artifacts produced one small diagnostic gain without monotone or above-domain recovery. The instrument audit also withdraws the claim that Stage 7 cleanly isolated an inability to use fully supplied state, because operative information was unmatched and some direct scores used a defective option readout. The curator's account of reading as running a forward process therefore remains open: the experiment did not establish that its required reader had been built.

### Gate and prediction ladder

Each row names its comparison and construction. Values are log-score differences in nats (positive favors the named reader), with recorded 95% intervals and scored-unit counts where available. Whole and maker-divergence tail are distinct populations; cross-card values are not directly interchangeable. Qwen and Smol refer to the two frozen local adapters. All purpose and accumulation rows are diagnosis.

| Comparison / construction | Reader | Whole | Tail | Status |
|---|---|---|---|---|
| DOM domain prior | Both | Reference, 0 | Reference, 0 | Common baseline |
| FM process-trained, E03/x1 | Qwen2.5-1.5B | +0.2410 [+0.1345, +0.3563]; n=306 | Not an E03 endpoint | Prediction passes; generation fails |
| DIR0 direct option reader, E05 | Qwen2.5-1.5B | -2.3891 [-3.0117, -1.7877] | Not measured | Historical; defective grouped readout |
| FM plain, purpose worlds (G02/x1) | Qwen2.5-1.5B | +0.1256 [+0.0380, +0.2122]; n=327 | +0.8681 [+0.6445, +1.0997]; n=66 | Diagnosis |
| FM+P proposed purpose, purpose worlds (G02/x1) | Qwen2.5-1.5B | +0.0390 [-0.0612, +0.1402]; n=327 | +0.8577 [+0.5858, +1.1283]; n=66 | Diagnosis |
| FM+true purpose, purpose worlds (G02/x1) | Qwen2.5-1.5B | +0.1983 [+0.1081, +0.2893]; n=327 | +0.9844 [+0.7485, +1.2132]; n=66 | Diagnosis |
| FM+3 maker context, series worlds (A03) | Qwen2.5-1.5B | +0.2072 [-0.0761, +0.5246]; n=35 | +1.5600 [+1.1481, +2.0362]; n=6 | Diagnosis |
| FM process-trained, E03/x1 | SmolLM2-1.7B | +0.2014 [+0.0892, +0.3186]; n=306 | Not an E03 endpoint | Prediction passes; generation fails |
| DIR0 direct option reader, E05 | SmolLM2-1.7B | -0.8936 [-1.1812, -0.5792] | Not measured | Historical; defective grouped readout |
| FM plain, purpose worlds (G02/x1) | SmolLM2-1.7B | +0.0999 [+0.0175, +0.1858]; n=327 | +0.7365 [+0.4927, +0.9668]; n=66 | Diagnosis |
| FM+P proposed purpose, purpose worlds (G02/x1) | SmolLM2-1.7B | +0.0418 [-0.0472, +0.1343]; n=327 | +0.6252 [+0.3579, +0.8772]; n=66 | Diagnosis |
| FM+true purpose, purpose worlds (G02/x1) | SmolLM2-1.7B | +0.1450 [+0.0524, +0.2386]; n=327 | +0.8397 [+0.5822, +1.0865]; n=66 | Diagnosis |
| FM+3 maker context, series worlds (A03) | SmolLM2-1.7B | +0.1328 [-0.1580, +0.4499]; n=35 | +1.4497 [+0.9491, +1.8762]; n=6 | Diagnosis |
| FR frontier probe (E07) | Gemini 3.5 Flash Lite | -2.6408 [-4.5239, -0.9442]; n=41 | Not measured | Gate failed; historical paid probe only |
| Oracle minus DOM, Purpose worlds | Exact program | +0.4351 | +1.6268 | Construction ceiling, privileged truth |
| Oracle minus DOM, Maker-series worlds | Exact program | +0.3504 | +1.7302 | Construction ceiling, privileged truth |

Generation (E04): header-visible feasibility was 0.725 for Qwen and 0.575 for Smol versus a required 1.0; median event scores -3.177 and -2.773 were below the population 20th-percentile cutoff -2.653. The feasibility repair was outcome-informed. Composite admission: zero; frozen confirmations: zero.

### Purpose and pull ordering

Rows compare the same reader's goal objects in G05 (96 worlds), execution in the larger G02/x1 sample (327 whole / 66 tail units), and equivalence-class coverage in G04 (nine equivalent worlds). Recall is the share of correct choices; coverage is the share retaining the whole true class. Intervals below apply to paired log-score differences, not recall.

| Reader | Purpose / pull recall | Proposed purpose minus plain FM: whole | Same: tail | Equivalence coverage |
|---|---|---|---|---|
| Qwen2.5-1.5B | 0.354 / 0.594 | -0.0867 [-0.1198, -0.0532]; n=327 | -0.0103 [-0.0957, +0.0681]; n=66 | 0.000 |
| SmolLM2-1.7B | 0.552 / 0.698 | -0.0581 [-0.0879, -0.0292]; n=327 | -0.1113 [-0.1981, -0.0333]; n=66 | 0.222 |

Pull recall is easier in this construction; it does not decide which goal ontology the curator should adopt. Proposed purposes hurt whole-log prediction. Equivalence failed on both readers. The meaning-change control did not establish meaning-sensitive purpose recovery.

### Accumulation

The larger A01/x1 table reports surprise alignment (area under the receiver operating characteristic curve; 0.5 is random ranking). Available/scored series differ where a log is degenerate or missing.

| Reader | Earlier artifacts | Reader surprise alignment | Domain alignment | Paired reader-minus-domain interval | Scored / available series |
|---|---:|---:|---:|---|---|
| Qwen2.5-1.5B | 0 | 0.2422 | 0.4904 | -0.2481 [-0.2790, -0.2158]; n=165 | 165 / 192 |
| Qwen2.5-1.5B | 1 | 0.2519 | 0.4904 | -0.2385 [-0.2677, -0.2076]; n=165 | 165 / 192 |
| Qwen2.5-1.5B | 2 | 0.2567 | 0.4904 | -0.2337 [-0.2630, -0.2030]; n=165 | 165 / 192 |
| Qwen2.5-1.5B | 3 | 0.2563 | 0.4898 | -0.2336 [-0.2636, -0.2038]; n=164 | 164 / 191 |
| SmolLM2-1.7B | 0 | 0.2761 | 0.4904 | -0.2143 [-0.2438, -0.1841]; n=165 | 165 / 192 |
| SmolLM2-1.7B | 1 | 0.2770 | 0.4907 | -0.2137 [-0.2430, -0.1850]; n=164 | 164 / 191 |
| SmolLM2-1.7B | 2 | 0.2864 | 0.4904 | -0.2039 [-0.2342, -0.1728]; n=165 | 165 / 192 |
| SmolLM2-1.7B | 3 | 0.2842 | 0.4955 | -0.2114 [-0.2425, -0.1801]; n=162 | 162 / 189 |

Paired three-minus-zero comparisons use matched series; both dose sequences are nonmonotone.

| Reader | Three earlier artifacts minus none | Monotone from zero to three? |
|---|---|---|
| Qwen2.5-1.5B | +0.0136 [+0.0032, +0.0235]; n=164 | No |
| SmolLM2-1.7B | +0.0073 [-0.0041, +0.0195]; n=162 | No |

Law and residue recall in A02 do not rise with earlier artifacts (three and four offered candidates respectively, unaffected by group truncation here). A03 compares a maker model inferred from three artifacts with the same reader without it: whole-log differences +0.0019 [-0.0671, +0.0740] and -0.0555 [-0.1084, -0.0002]; tail differences -0.0273 [-0.1324, +0.1001] and +0.0223 [-0.1058, +0.1605], on only six tail units. No established accumulated-maker benefit follows.

### Testbed

The completed catalog records 17 repositories, seven available corpus manifests of ten, and three cheap-baseline reproductions of seven. Availability is not permission to rehost or start corpus studies. License and access details remain in docs/TOOLS.md and the original catalog/manifest receipts; B04's zero counts were stale. No reference checkout was edited during this repair.

### Four executive answers

1. Can the reader make? Neither trained reader passed generation, despite passing prediction.
2. Does it look in the right places? As diagnosis, surprise is anti-aligned with maker divergences; the larger localization sample remains below the domain model. An admitted expert was not tested.
3. Does it recover purpose and use it? Recall is partial, equivalence and meaning sensitivity fail, and executing the proposed purpose hurts whole-log prediction.
4. Does the maker accumulate? One small diagnostic gain appears on Qwen, without monotonicity or above-domain recovery; law/residue recall and maker-model prediction do not establish the proposed accumulation.

### The requested verbal walkthrough

These are open philosophical prompts, not answers or a recommended Stage 9. The first five are prioritized; the remaining five are optional under the curator's explicit stage-discussion override.

1. A critic recognizes an unusual brushstroke but cannot paint competently. What, in that example, counts as running the painter's process?
2. A carpenter makes an ordinary chair with one awkward joint because it must fit a relative's home. What makes the joint evidence about the carpenter rather than the room?
3. A director's films repeatedly linger on departures, while their plots serve very different purposes. What would you count as accumulating the director, and what could remain a shared convention?
4. A reader predicts every sentence of a familiar genre but misses the reason this author wrote this work. What knowledge does the successful prediction demonstrate?
5. Two authors produce the same passage for different reasons. What later work or ordinary choice could make their difference legible without presuming that this passage already contains it?
6. A child makes a drawing that moves an adult more than a technically accomplished copy does. Where would you place the adult's process knowledge in that reading?
7. A restoration team recreates a damaged work from detailed plans while a historian explains its choices. In what respects are their reconstructions the same activity?
8. An architect reuses a standard plan but spends unusual effort on one threshold. How would you distinguish personal concern, expertise and a local constraint in that effort?
9. A reader changes their account of a writer after three books. What distinguishes understanding that writer from becoming fluent in the writer's dialect?
10. Several motives remain compatible with an artifact and all predict the same next choice. What uncertainty matters to the reading even before a future choice separates them?

## Pass B: evidence and administrative appendix

The original packet remains [preserved](../phase_2_4_stage_8/CURATOR_PACKET_FINAL.md), including its historical detailed scores, but its machine interpretation is superseded here. [Versioned integrity](STAGE8_INTEGRITY.json) records input and validator-source hashes, terminal checks and ten explicit superseded manifest declarations (271 original declarations, 261 applicable). [Dependencies](DEPENDENCIES.json) and [input hashes](INPUT_HASHES.json) give the S4 scope and missing references. [Amendments](AMENDMENTS.json) retain original/repaired judgments and remaining verification. [Independent apparatus fixtures](FIXTURES.json) and [model precision](MODEL_PRECISION.json) are a new maintenance lineage.

The 61 rows below cover every terminal cell including all five expansions. Each links the full original verdict and metrics, preserving all intervals, lineage and disposition details; raw labels do not confer admission. Diagnosis governs difference/purpose/accumulation reader claims. A support label is not confirmation, a valid null is completed work, an instrument failure is not a theory refutation, and a blocked confirmation is not a negative replication.

| Cell | Execution | Original outcome | Applicable interpretation / full detail |
|---|---|---|---|
| A01 | COMPLETE | VALID_NULL | Diagnosis only; [verdict](../phase_2_4_stage_8/A01/verdict.json), [metrics](../phase_2_4_stage_8/A01/metrics.json) |
| A01/x1 | COMPLETE | SUPPORT_CANDIDATE | Diagnosis only; [verdict](../phase_2_4_stage_8/A01/x1/verdict.json), [metrics](../phase_2_4_stage_8/A01/x1/metrics.json) |
| A02 | COMPLETE | DESCRIPTIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/A02/verdict.json), [metrics](../phase_2_4_stage_8/A02/metrics.json) |
| A03 | COMPLETE | INCONCLUSIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/A03/verdict.json), [metrics](../phase_2_4_stage_8/A03/metrics.json) |
| A04 | COMPLETE | DESCRIPTIVE | See bounded original receipt; [verdict](../phase_2_4_stage_8/A04/verdict.json), [metrics](../phase_2_4_stage_8/A04/metrics.json) |
| A05 | COMPLETE | INCONCLUSIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/A05/verdict.json), [metrics](../phase_2_4_stage_8/A05/metrics.json) |
| B01 | COMPLETE | NOT_RUN | No frozen eligible claim; no confirmation; [verdict](../phase_2_4_stage_8/B01/verdict.json), [metrics](../phase_2_4_stage_8/B01/metrics.json) |
| B02 | COMPLETE | NOT_RUN | No frozen eligible claim; no confirmation; [verdict](../phase_2_4_stage_8/B02/verdict.json), [metrics](../phase_2_4_stage_8/B02/metrics.json) |
| B03 | COMPLETE | INFRASTRUCTURE | Presence check superseded by dated full integrity; [verdict](../phase_2_4_stage_8/B03/verdict.json), [metrics](../phase_2_4_stage_8/B03/metrics.json) |
| B04 | COMPLETE | DESCRIPTIVE | Two-admitted routing superseded; zero admitted; curator pursuit pending; [verdict](../phase_2_4_stage_8/B04/verdict.json), [metrics](../phase_2_4_stage_8/B04/metrics.json) |
| D01 | COMPLETE | COUNTEREVIDENCE | Diagnosis only; [verdict](../phase_2_4_stage_8/D01/verdict.json), [metrics](../phase_2_4_stage_8/D01/metrics.json) |
| D01/x1 | COMPLETE | COUNTEREVIDENCE | Diagnosis only; [verdict](../phase_2_4_stage_8/D01/x1/verdict.json), [metrics](../phase_2_4_stage_8/D01/x1/metrics.json) |
| D02 | COMPLETE | DESCRIPTIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/D02/verdict.json), [metrics](../phase_2_4_stage_8/D02/metrics.json) |
| D03 | COMPLETE | DESCRIPTIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/D03/verdict.json), [metrics](../phase_2_4_stage_8/D03/metrics.json) |
| D04 | COMPLETE | INCONCLUSIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/D04/verdict.json), [metrics](../phase_2_4_stage_8/D04/metrics.json) |
| D05 | COMPLETE | COUNTEREVIDENCE | Diagnosis only; [verdict](../phase_2_4_stage_8/D05/verdict.json), [metrics](../phase_2_4_stage_8/D05/metrics.json) |
| D06 | COMPLETE | DESCRIPTIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/D06/verdict.json), [metrics](../phase_2_4_stage_8/D06/metrics.json) |
| E01 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/E01/verdict.json), [metrics](../phase_2_4_stage_8/E01/metrics.json) |
| E02 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/E02/verdict.json), [metrics](../phase_2_4_stage_8/E02/metrics.json) |
| E03 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/E03/verdict.json), [metrics](../phase_2_4_stage_8/E03/metrics.json) |
| E03/x1 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/E03/x1/verdict.json), [metrics](../phase_2_4_stage_8/E03/x1/metrics.json) |
| E04 | COMPLETE | COUNTEREVIDENCE | See bounded original receipt; [verdict](../phase_2_4_stage_8/E04/verdict.json), [metrics](../phase_2_4_stage_8/E04/metrics.json) |
| E05 | COMPLETE | COUNTEREVIDENCE | See bounded original receipt; [verdict](../phase_2_4_stage_8/E05/verdict.json), [metrics](../phase_2_4_stage_8/E05/metrics.json) |
| E06 | COMPLETE | INCONCLUSIVE | See bounded original receipt; [verdict](../phase_2_4_stage_8/E06/verdict.json), [metrics](../phase_2_4_stage_8/E06/metrics.json) |
| E07 | COMPLETE | COUNTEREVIDENCE | See bounded original receipt; [verdict](../phase_2_4_stage_8/E07/verdict.json), [metrics](../phase_2_4_stage_8/E07/metrics.json) |
| E08 | COMPLETE | INCONCLUSIVE | See bounded original receipt; [verdict](../phase_2_4_stage_8/E08/verdict.json), [metrics](../phase_2_4_stage_8/E08/metrics.json) |
| G01 | COMPLETE | INFRASTRUCTURE | Diagnosis only; [verdict](../phase_2_4_stage_8/G01/verdict.json), [metrics](../phase_2_4_stage_8/G01/metrics.json) |
| G01/x1 | COMPLETE | INFRASTRUCTURE | Diagnosis only; [verdict](../phase_2_4_stage_8/G01/x1/verdict.json), [metrics](../phase_2_4_stage_8/G01/x1/metrics.json) |
| G02 | COMPLETE | INCONCLUSIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/G02/verdict.json), [metrics](../phase_2_4_stage_8/G02/metrics.json) |
| G02/x1 | COMPLETE | INCONCLUSIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/G02/x1/verdict.json), [metrics](../phase_2_4_stage_8/G02/x1/metrics.json) |
| G03 | COMPLETE | INCONCLUSIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/G03/verdict.json), [metrics](../phase_2_4_stage_8/G03/metrics.json) |
| G04 | COMPLETE | COUNTEREVIDENCE | Diagnosis only; [verdict](../phase_2_4_stage_8/G04/verdict.json), [metrics](../phase_2_4_stage_8/G04/metrics.json) |
| G05 | COMPLETE | DESCRIPTIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/G05/verdict.json), [metrics](../phase_2_4_stage_8/G05/metrics.json) |
| G06 | COMPLETE | COUNTEREVIDENCE | Diagnosis only; [verdict](../phase_2_4_stage_8/G06/verdict.json), [metrics](../phase_2_4_stage_8/G06/metrics.json) |
| G07 | COMPLETE | DESCRIPTIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/G07/verdict.json), [metrics](../phase_2_4_stage_8/G07/metrics.json) |
| G08 | COMPLETE | DESCRIPTIVE | Diagnosis only; [verdict](../phase_2_4_stage_8/G08/verdict.json), [metrics](../phase_2_4_stage_8/G08/metrics.json) |
| I01 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/I01/verdict.json), [metrics](../phase_2_4_stage_8/I01/metrics.json) |
| I02 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/I02/verdict.json), [metrics](../phase_2_4_stage_8/I02/metrics.json) |
| I03 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/I03/verdict.json), [metrics](../phase_2_4_stage_8/I03/metrics.json) |
| I04 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/I04/verdict.json), [metrics](../phase_2_4_stage_8/I04/metrics.json) |
| I05 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/I05/verdict.json), [metrics](../phase_2_4_stage_8/I05/metrics.json) |
| I06 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/I06/verdict.json), [metrics](../phase_2_4_stage_8/I06/metrics.json) |
| I07 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/I07/verdict.json), [metrics](../phase_2_4_stage_8/I07/metrics.json) |
| I08 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/I08/verdict.json), [metrics](../phase_2_4_stage_8/I08/metrics.json) |
| T01 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/T01/verdict.json), [metrics](../phase_2_4_stage_8/T01/metrics.json) |
| T02 | COMPLETE | DESCRIPTIVE | See bounded original receipt; [verdict](../phase_2_4_stage_8/T02/verdict.json), [metrics](../phase_2_4_stage_8/T02/metrics.json) |
| T03 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/T03/verdict.json), [metrics](../phase_2_4_stage_8/T03/metrics.json) |
| T04 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/T04/verdict.json), [metrics](../phase_2_4_stage_8/T04/metrics.json) |
| T05 | COMPLETE | DESCRIPTIVE | See bounded original receipt; [verdict](../phase_2_4_stage_8/T05/verdict.json), [metrics](../phase_2_4_stage_8/T05/metrics.json) |
| X01 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/X01/verdict.json), [metrics](../phase_2_4_stage_8/X01/metrics.json) |
| X02 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/X02/verdict.json), [metrics](../phase_2_4_stage_8/X02/metrics.json) |
| X03 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/X03/verdict.json), [metrics](../phase_2_4_stage_8/X03/metrics.json) |
| X04 | COMPLETE | INSTRUMENT_FAILED | See bounded original receipt; [verdict](../phase_2_4_stage_8/X04/verdict.json), [metrics](../phase_2_4_stage_8/X04/metrics.json) |
| X05 | COMPLETE | INFRASTRUCTURE | Original 1e-6 FAIL; outcome-informed 0.01 PASS; DIR0 limitation separate; [verdict](../phase_2_4_stage_8/X05/verdict.json), [metrics](../phase_2_4_stage_8/X05/metrics.json) |
| X06 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/X06/verdict.json), [metrics](../phase_2_4_stage_8/X06/metrics.json) |
| X07 | COMPLETE | INSTRUMENT_FAILED | See bounded original receipt; [verdict](../phase_2_4_stage_8/X07/verdict.json), [metrics](../phase_2_4_stage_8/X07/metrics.json) |
| X08 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/X08/verdict.json), [metrics](../phase_2_4_stage_8/X08/metrics.json) |
| X09 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/X09/verdict.json), [metrics](../phase_2_4_stage_8/X09/metrics.json) |
| X10 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/X10/verdict.json), [metrics](../phase_2_4_stage_8/X10/metrics.json) |
| X11 | COMPLETE | INFRASTRUCTURE | See bounded original receipt; [verdict](../phase_2_4_stage_8/X11/verdict.json), [metrics](../phase_2_4_stage_8/X11/metrics.json) |
| X12 | COMPLETE | INFRASTRUCTURE | 54 verdict hashes and fake scratch resume only; [verdict](../phase_2_4_stage_8/X12/verdict.json), [metrics](../phase_2_4_stage_8/X12/metrics.json) |

B01 and B02 had no eligible frozen claims. B03 originally checked presence around 55 verdicts; X12 rehashed 54, and its fake scratch resume grew 23 rows to 36 with zero duplicates and the deadline retained. Neither is a full independent scientific rerun. The detached validator checks all final terminal cells under its stated historical-provenance limits. Runtime: 40.03 elapsed hours; 26.567 GPU-lock reservation hours, not measured useful GPU utilization; historical frontier spend $2.141298. Lost-time accounting is incomplete and must not be reported as measured zero. No new spending, successor stage, delegation, human-reader claim or value/alignment inference follows.

Curator processing and chosen pursuit remain pending the verbal pass.
