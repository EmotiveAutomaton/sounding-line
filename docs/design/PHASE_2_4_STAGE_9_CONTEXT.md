# Sounding Line Stage 9: usable competence, individual makers, and a broader testbed

**Coding-agent handoff · September 6, 2026 · specification, not a launch receipt**

This is the successor specification to the closed Phase 2.4 Stage 8. It integrates the curator's two verbal walkthroughs, the September 5 research review, the completed Stage 8 testbed work, and the September 6 maintenance. The curator requested a comprehensive pass of approximately five days on existing local resources, without Gear 3, and explicitly asked for a specification rather than implementation in this analyst turn. No new experiment, reference checkout, repository mutation, or paid call was performed to produce this handoff.

**Recommendation:** undertake one broad, branching Stage 9. Put competence and measurement at its entrance, and run corpus intake alongside them. Then compare ways of reconstructing a particular maker across artifacts, changed constraints, revisions, and different reader objectives. Preserve useful branches when another branch fails. Finish with a map of capabilities and boundaries, selected confirmations, and concrete examples that explain the map.

The breadth is deliberate: **42 cards, including 32 scientific questions, plus 12 shared attacks.** These are questions and required dispositions, not 54 promised positive results or a Cartesian product of every condition. Runtime calibration and the expansion rules below determine how many independent units each eligible question receives.

## 1. What Stage 8 actually changed

The question was whether learning the ordinary production process would let a reader recognize the maker's departures and increasingly understand that maker across works. The method trained two small local language-model adapters on constructed, maker-free process logs, checked prediction and generation, and then measured surprise, purpose use, and accumulation against a domain baseline and construction truth.

The following rows separate the experiment's direct findings from what they mean. “Prediction gain” is an increase in the probability assigned to actual choices, measured by log score. These are constructed-process results, not tests of human literary or visual understanding.

| Question | Finding | Change to our understanding |
|---|---|---|
| Can training teach something useful? | Both trained readers improved next-action prediction: about +0.24 and +0.20 nats on the expanded sample. | Yes, the training installed useful predictive information. The question is what kind of competence it installed and where that competence stops. |
| Can these readers produce the process? | Neither passed generation. Only 29/40 and 23/40 sampled logs met visible feasibility, and both missed the population likelihood criterion. | The intended broadly competent reader was not established. This is a substantive capability gap, not a minor formatting rejection. |
| Does the maker announce themselves through surprise? | Raw surprise ranked designated maker departures in the wrong direction. | The specified locator failed. It does not follow that individuality is absent, or that a competent reader must always find familiar individuality surprising. |
| Does naming purpose improve understanding? | Executing the reader's proposed purpose made prediction worse on both readers. Supplied true purpose had better point estimates. | A purpose label is not yet a usable maker model. Candidate quality and the ability to execute a candidate need separate tests. |
| Does a person emerge across their works? | One reader had a small accumulation gain on the surprise statistic; neither showed a consistent, above-domain result, improved law/residue recall, or established benefit from its explicit maker model. | Useful accumulation remains unestablished. “Nothing accumulates” is too categorical, but the intended capability has not appeared. |
| Was the main theory decisively tested? | No reader passed the composite gate; no confirmation was selected or executed. | The stage tested implementations and exposed bottlenecks. It did not settle the theory under its stated competence precondition. |

Sources: [corrected packet](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/results/maintenance_20260906/STAGE8_CURATOR_PACKET_CORRECTED.md), [generation measurements](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/results/phase_2_4_stage_8/E04/metrics.json), [purpose comparison](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/results/phase_2_4_stage_8/G02/x1/metrics.json).

Two qualifications determine this successor. First, Stage 8's prediction task scores offered continuations after a genuine prefix; generation creates a whole log from a header. The difference includes sustained execution, generated history, outcomes, and stopping. “Surface-only learning” is one possible explanation, not an isolated finding. Second, the constructor's maker-departure label is a probability difference against the domain model; the tested reader statistic is raw rarity. Those quantities need not rank events alike. Both qualifications preserve the original failures while changing the next discriminator. [Prediction/generation implementation](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/runners/stage8/reader/forward_model.py), [departure construction](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/runners/stage8/constructor/population.py).

The earlier learned-law program success remains a bounded positive anchor. The supplied-state direct-reader comparison remains owed under matched operative information and the repaired scorer. Neither fact licenses treating every earlier failure as broken, or every repair as a scientific success.

**Current judgment:** pursuit value is high; warrant for a general maker reader remains low. A five-day campaign can be valuable if it distinguishes competing explanations and acquires genuinely usable external substrates. More samples through the unchanged Stage 8 pipeline would leave its central ambiguity in place.

## 2. What the walkthrough contributes

This section is an analyst reconstruction, not verbatim quotation, experimental evidence, or permission to strengthen uncertain statements.

- **Criticism:** the reader reconstructs the maker's goal and considers a different way to meet it. Expertise gives the comparison substance. The latest answer adds immediate, hierarchical explanation of details as a phenomenological sign of competence.
- **Familiarity:** many small cues can evoke a director reflexively, before their individual contributions are verbalized. The feeling can itself prompt examination of who made the work. An anomaly is consequently one entry route, not the only route.
- **Stable ends, changed means:** a director may preserve an effect under a camera constraint by changing staging or performance. Crew preparation can preserve similar traces for a different reason.
- **Reader purpose:** learning how to play better and learning how this particular player thought make different uncertainties worth resolving. Stopping an inquiry need not mean inability.
- **Repurposed expertise:** a novelist may redirect an existing rhetorical operation from ridicule toward admiration. This was the curator's more confident conjecture. More revisions and small-habits-first sequencing remain weaker conjectures.
- **Persistent context:** a fact about the maker's situation may reorganize interpretation across the artifact. Whether that reorganization becomes more accurate is a separate empirical question.

**Narrow disagreement:** feeling unsurprised and having an immediate explanation do not, by themselves, demonstrate a forward generator. An explanation can accommodate a choice after seeing it without predicting what a change would do. Test explanation, local construction, and sustained generation separately. This is an evidential distinction, not a claim that the curator's experienced process is fictitious.

If “flawless” means demonstrably correct about unfamiliar counterfactual consequences, the disagreement disappears: that already entails the prospective check. If it names the experienced immediacy and coherence of an explanation, the check remains necessary. Do not silently choose between those readings of the audio.

The new familiarity answer also does not yet distinguish recognition of surface regularities from recognition through an enacted production model. Keep both live. Do not write a neural mechanism for the reported feeling or translate it into model internals by analogy.

There is enough here to specify experiments. No further curator answer is a prerequisite. For future difficult follow-ups, use an extended concrete scene with several contrasting possible cases the curator can modify, combine, or reject. These are examples, not forced response categories. Do not ask for statistical or implementation choices.

## 3. Inheritance and repairs required before use

### 3.1 Pinned baseline and scope

The reviewed Sounding head is **6c090560e01d1ddf2386d26da047ef1a08a22697**, unchanged at this check. The committed state says Stage 8 and the subsequent three maintenance jobs have ended and no eligible work remains. The reviewed Ghost head is **36927fae0356c0080276380f2f0ad560b658aa40**, also unchanged at this check. These are repository checks, not live inspection of the home workstation.

Create a separate Stage 9 lineage. Keep Stage 8 raw outputs, admission criteria, confirmations, and historical source limitations intact. Use the current canonical AGENTS contract and Codex operating loop. Do not relaunch completed maintenance jobs to occupy hardware. This handoff selects Sounding work; it does not authorize modifying Ghost, restarting V15, contacting authors, paid APIs, or external compute. Mechanism proposals requiring a new acting-agent simulation belong in a future Ghost handoff; use Sounding's existing constructor for the bounded tests here.

### 3.2 The external work did land, with narrower readiness than the summaries suggest

T01 records 17 pinned repository checkouts. Three corpora were already in hand: ArgRewrite, CoAuthor, and ScholaWrite. Most of the new corpus entries hold landing pages or READMEs, not data. The seven new loader fixtures parse miniature invented formats; they do not establish parsing of the publishers' real releases. T05's three numeric entries are inventory counts, not three reproduced predictive baselines. CoAuthor's 690 reconstructed discovery sessions are a subset count, not reproduction of the published 1,445-session total. [Catalog](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/docs/TOOLS.md), [T04 receipt](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/results/phase_2_4_stage_8/T04/metrics.json), [T05 receipt](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/results/phase_2_4_stage_8/T05/metrics.json), [loader implementation](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/runners/stage8/testbed/loaders.py).

The following repairs are part of Stage 9 preparation, with new receipts. Original receipts remain preserved.

| Repair | Exact owners to inspect | Required result |
|---|---|---|
| Correct testbed readiness | docs/TOOLS.md; FINDINGS.md L372; corrected packet's testbed paragraph; Stage 8 T04/T05 receipts | Separate source-page availability, actual data availability, real-schema parsing, inventory reconciliation, baseline reproduction, and scientific admission. Add a dated correction to the interpretation; preserve historical metrics. |
| Verify reference checkouts | runners/stage8/testbed/clones.py and TESTBED_SOURCES registry | Require the requested commit, necessary files, clean checkout status, complete referenced assets, and measured read-only isolation. gpudrive-CoDec and inverse_painting each record zero checked-out files. The current receipt hardcodes read_only=true; that is not enforcement. Do not count a surviving Git head after a failed checkout as an executable acquisition. |
| Complete scoring repair | runners/readout_repair.py; maintenance DEPENDENCIES.json; Stage 7/8 direct-reader consumers | Freeze matched numeric state, operative rules, candidate support, and execution access. Rerun representative affected scientific contrasts in a new lineage. Missing historical predictions remain missing. |
| Validate the surprise target | Stage 8 constructor/population.py and engines.py | Retain raw surprise and the old departure label. Establish which new measure answers which question on exact predictors and fresh known-answer cases before using it for discovery. |
| Repair semantic intervention meaning | Stage 8 engine_dpa.py and G06/X04 interpretation | Every claimed purpose-changing intervention must realize and verify its new target; an action-type swap retaining the old purpose does not establish a newly correct purpose. Preserve the original crossover outcome with its narrower meaning. |
| Qualify the competence interpretation | THE_TRIPLE_INFERENCE.md §2, relevant rows and afterword | Remove unsupported certainty that the observed pattern uniquely identifies surface-only expertise. Retain prediction success, generation failure, and unsuccessful maker reading. |
| Record the conversation | results/readings/PROVENANCE.md; existing theory owners; TODO.md | Preserve relative confidence and reconstructed-wording labels. Add familiarity as an entry-route hypothesis without making it the sole route. Update the difficult-follow-up format in the existing operating contract. |

Do not open a new theory section merely to hold these changes. Theory edits use existing rows and afterwords, preserve curator blockquotes, follow the folder README, and pass theory lint. Stage 9's candidate interpretations are explicitly analyst proposals; the walkthrough does not ratify their mechanisms by implication.

### 3.3 Carry every prior acquisition forward, but prioritize operations

This table retains all 17 T01 entries. “Use” means a selected operation or reference role, subject to a local fixture; it does not claim the external system was reproduced or is installed correctly.

| Reference | Stage 9 role |
|---|---|
| MMToM-QA / BIP-ALM; MuMA-ToM | Learned action likelihood within explicit inference; single-maker operation first, multi-agent work deferred unless existing mixed-control data require it. |
| Hypothetical-Minds | Propose, evaluate, revise hypotheses; compare proposal improvement with evaluation improvement. |
| InversePlanning.jl | Known-law comparator and enumeration checks; execute only if the local Julia environment is available and independently verified. |
| LaBToM.jl; CLIPS.jl | Belief-factor and instruction/evidence distinctions; reading references, not automatic new runtime installations. |
| acting-as-inverse-inverse-planning | Expressive choice aimed at an audience; useful for the constrained-director discriminator, not historical author psychology by default. |
| gpudrive-CoDec | Attention/construal reference; repair the empty checkout receipt. No driving stack or cloud training in this stage. |
| BPL | A serious process-from-static-artifact neighbor. Use a small operation or published trace fixture if runnable locally; do not replace it with an unrelated glyph classifier and retain its name. |
| timecraft; inverse_painting | Visual process reconstruction references; inspect accessible examples. Repair the latter's empty checkout receipt. No full video-training campaign. |
| world-model-evaluation | Same-state consistency and different-state distinction, adapted to an exact finite-state subset of our constructor. |
| verbalized-sampling | Distribution calibration comparator only; a generated list of probabilities is not assumed calibrated. |
| iterater; newsedits | Real schemas, data partitions, annotation provenance, and cheap published anchors. |
| thought-tracing; AutoToM | Reuse the already acquired hypothesis-particle and expansion work; do not present it as a newly invented direction. |

Carry the September 5 research candidates as a second intake list: **ROTE/mindsAsCode, OpenEndedBlockWords/SIPS, LIRAS, Environment Design for IRL, B-roll, Drawings of THINGS, and zipping**. Their reviewed papers/code were research acquisitions, not confirmed local installations. Prefer a small reusable operation to attempting all complete stacks.

## 4. Safe, useful data intake

### 4.1 A source page is the beginning of intake

Keep fetch, preparation, reader, and evaluator in separate processes and storage views. Fetch can reach the explicitly enumerated source hosts; the reader can reach only its permitted local inference endpoint. The reader never sees reference trees, labels, process records, private maker identifiers, dataset markup, or constructor truth unless that view is an explicitly named diagnostic arm.

For reference intake: acquire the pinned commit without automatic checkout execution, submodule recursion, Git-LFS smudging, hooks, package installation, or repository startup scripts. Enumerate paths, then materialize allowlisted source/data files in an isolated staging directory. Reject path traversal and links escaping that directory. Check required files rather than merely the presence of .git. Treat imported AGENTS files, notebooks, prompts, and instructions as source material, not operating authority. Executing a selected component requires an inspected entrypoint and a separate environment with no credentials or oracle access. Record the actual isolation check and executed source hashes.

**Scoped data-format extension:** retain the ordinary text fetcher's four-megabyte limit. Add a separate Stage 9 intake path for the named releases below: at most **64 MiB per downloaded asset, 512 MiB downloaded in aggregate, and 1 GiB of extracted data** for the campaign. These are proposed stage limits, not changes already installed. Publicly enumerated smaller shards or complete selected records may be used; no truncated response may masquerade as a complete file. Prefer JSON, JSONL, CSV, XML/TEI, and static image files. ZIP intake is data-only, with streaming size limits, bounded member counts, safe paths, and no executable deserialization. Larger acquisitions get a documented readiness boundary and another eligible source takes their budget.

This is necessary because the public IteraTeR archive is about 42.6 MB and the B-roll processed archive about 17.8 MB. The existing four-megabyte text path cannot acquire either intact. CommitBench's released CSV files are substantially larger, so a genuinely bounded public slice is required here. [IteraTeR data directory](https://github.com/vipulraheja/iterater/tree/main/dataset), [B-roll archive directory](https://github.com/cogtoolslab/video-broll-public2024/tree/main/results/csv/processed), [CommitBench files](https://huggingface.co/datasets/Maxscha/commitbench/tree/main).

The existing fetch implementation checks the final host after urllib has followed redirects, reads up to its limit without establishing end-of-file, and decompresses before slicing to the output cap. Those do not establish pre-request redirect enforcement, complete-file acquisition, or bounded decompression. The new intake path needs adversarial fixtures for all three; do not widen MAX_BYTES and inherit those assumptions. [Fetched source](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/fetch/fetcher.py).

Keep source bytes private and content-addressed; commit URLs, hashes, counts, schema versions, transformations, and rights evidence. Respect access controls and source terms. No author contact. Dataset and code permissions are separate: a license phrase found in a sample document is not a dataset license. In particular, the Stage 8 CommitBench manifest's heuristic “mit license” hint must not replace the release's **CC-BY-NC-4.0** metadata. Verify exact permissions for the selected files before acquisition or reuse; do not infer a new restriction or permission from the absence of a root LICENSE alone.

### 4.2 Corpus priorities and honest targets

Rows distinguish what humans supplied from what the study could establish. Ready means usable after this stage's own data gate; it is not asserted here.

| Source | Current evidence / acquisition priority | Use and ceiling |
|---|---|---|
| **ArgRewrite v2** | In hand; reuse canonical revision-unit construction and the project's prior reproduction/correction history. | Agreement with reader-assigned revision purposes. Preserve multi-label rules; file counts are not essay counts. A reader's label is not privileged maker intention. |
| **CoAuthor** | In hand; use repaired document-state and suggestion-decision loaders. | Mixed-control prospective choices as a diagnostic bridge. Preserve who offered, selected, edited, or dismissed; no single human/model authorship ratio. |
| **ScholaWrite** | In hand; grouped project/session splits and published-protocol corrections already matter. | Writer-recorded revision labels and next-change prediction. Prior evaluated units are historical discovery, not a new untouched confirmation reserve. |
| **IteraTeR-HUMAN** | First new revision intake. Public archive and documented real schema are available. | Human annotation on revisions, with document IDs, depth, domains, and raw annotator disagreement. Keep FULL's model-predicted labels out of human-ground-truth claims. Do not pursue the restricted Plus/v2 route that requires author contact. |
| **arXivEdits** | Second revision intake if selected release terms and source files pass. | Span edits and annotator intentions; group full paper/version lineages, deduplicate against IteraTeR's arXiv material, and retain coauthorship ambiguity. |
| **Shelley-Godwin Archive** | First genetic-edition intake; public TEI data and open-license information verified. | Finished/reconstructed text as reader input, editorial additions/deletions and hand attribution as evaluator evidence. Preserve partial order and uncertainty; four famous writers do not constitute a broad population or unseen-pretraining guarantee. |
| **Woolf Online** | Carry forward, bounded second-edition intake attempt. A landing page is currently all that the Stage 8 manifest proves. | Cross-draft case studies only where actual transcription, sequence, and permissions are established. Do not invent a chronological trace from page order. |
| **B-roll** | High-value new creative-choice branch. Archive exists; verify reuse basis and repeated-person structure before promotion. | Human concept selections under informative/entertaining commissions. Same-person prior selections may predict a held-out script. These are selections for imagery, not completed films, and supplied commissions are not values. |
| **Drawings of THINGS** | High-value visual branch, conditional on accessible data, rights, repeated makers, and a resident usable image interface. | Final-image features or image reader only in the primary arm; stroke history reserved for evaluation. If only an analysis repo is acquired, report that. No pretend visual test through oracle-derived stroke summaries. |
| **CommitBench** | Bounded code-domain branch if a versioned, complete public slice fits intake limits. | Diff/artifact to maker-stated change description; repository-grouped. A commit message is a communication about a change, not transparent historical intent. No deanonymization to manufacture maker series. |
| **NewsEdits 2.0** | Carry forward with a bounded acquisition attempt and edition check. | Revision/update baselines and editorial-label provenance. Do not substitute the older NewsEdits release for 2.0 while retaining the latter's claims. |
| **Genius** | Carry forward as blocked unless public permitted data access resolves the existing failure. | Distinguish crowd commentary from verified artist statements. No lyric scraping, API workaround, or contact campaign to fill this slot. |

Primary source checks: [IteraTeR real schema](https://github.com/vipulraheja/iterater/blob/main/dataset/README.md), [arXivEdits release](https://github.com/chaojiang06/arXivEdits), [Shelley-Godwin infrastructure and licensing](https://shelleygodwinarchive.org/about/), [TEI repository](https://github.com/umd-mith/sga), [B-roll methods and release](https://github.com/cogtoolslab/video-broll-public2024), [Drawings of THINGS paper](https://link.springer.com/article/10.3758/s13428-025-02887-w), [CommitBench release](https://huggingface.co/datasets/Maxscha/commitbench).

**Intake acceptance:** a real released example must traverse the actual loader; canonical units and all relevant fields must survive; attempted/excluded/usable counts must reconcile; one source-defined count or statistic must be checked; an ordinary predictive baseline must run; and the split must be defensible. Numerical source reproduction and a newly computed local baseline are separate receipts. Human-labeled and model-labeled subsets never silently merge.

Target two newly usable sources, including one creative/artifact source if possible, plus the three in-hand corpora. Every listed source receives an honest disposition. If external access or identifiability blocks that target, continue valid existing-data work and disclose the shortfall. A second landing page or a duplicate corpus does not count as expansion.

## 5. Readers, evidence, and the questions we can distinguish

### 5.1 Competence is a profile

Retain the original broad prediction-plus-generation admission as a historical comparator. Register separate Stage 9 capabilities: offered-choice prediction; prediction after an altered prefix; local constructive repair; self-directed rollout; stopping; and rule-consistent transfer. A reader can pass one and fail another. **A local pass licenses a local claim, not retrospective admission as a Stage 8 full generator.** A claim specifically requiring broad process competence still needs that gate.

Use the two resident Stage 8 base packages and frozen adapters as reference arms. New training uses the same pinned bases: Qwen2.5-1.5B-Instruct and SmolLM2-1.7B-Instruct. Report base, adapter, tokenizer, precision, renderer, scorer, and execution interface together. A tool-assisted reader is a separate package. Constrained decoding can establish a usable system while providing some legality externally; it cannot be credited as unaided model competence.

**Admission is explicit and local to the claim.** The historical broad comparison retains Stage 8's 100% sampled feasibility requirement and original population-score rule on its original task distribution. On expanded distributions, compute the reference population's 20th-percentile score on a separate frozen construction sample before evaluating readers; report that as a new Stage 9 gate, alongside the old-distribution result. No result retrospectively changes Stage 8 admission.

For a new constructed local-repair package, the proposed engineering gate is: at least 95% legal attempts; correct goal-improving repair on at least 80% of independently verified fixable cases; collateral constraint damage on at most 5%; and prospective consequence prediction improving by at least 0.05 nats over the strongest cheap comparator with a paired interval above zero. Report uncertainty around all rates and retain all attempted cases. These are finite-battery criteria, not universal competence guarantees. Validate that the exact executor passes and blind/story-only controls fail before scientific use. Human branches without independently decidable repair truth cannot borrow this gate; they retain their corpus-specific predictive and label-agreement claims. A package is identified by its domain, operation, assistance, model and scorer, so passage cannot silently transfer to another task.

For new training, use a **2 × 2 design**, three seeds per family: the original law family versus both existing law families; expert-prefix training versus a matched mixture including learner-visited states with correct training-only continuation targets. Match total target tokens, examples where feasible, optimizer, and exposure. Include a replay of the old recipe in the factorial. Start at the Stage 8 scale of 1,600 examples and three epochs; distinguish broader training coverage from the state-distribution intervention. Withhold parameter combinations and problem instances across all recipes. A law family used in broad training is no longer an unseen-family test.

This makes 24 small adapter fits, not 24 unrelated architectures. Historical training logs total roughly 1.33 hours for Qwen and 0.37 for Smol per three-epoch fit, giving about 20.4 hours for twelve paired fits before new overhead. This is a sizing prior, not a runtime guarantee. Pilot the token-matched recipes and learner-state collection before locking the schedule. [Stage 8 training receipt](https://github.com/EmotiveAutomaton/sounding-line/blob/6c090560e01d1ddf2386d26da047ef1a08a22697/results/phase_2_4_stage_8/E02/metrics.json).

The learner-state intervention is motivated by [DAgger](https://proceedings.mlr.press/v15/ross11a.html): policies can fail when their own actions produce states unlike training states. It is a discriminating adaptation, not a claim that exposure bias caused Stage 8 or that this modified training inherits the paper's guarantee.

### 5.2 Common comparators

Use a strong population model, a cheap individual-adaptation model, an executable behavioral-program mixture, and a differentiated maker model. The last model explicitly represents purpose, relevant context, available actions, expertise/law, and history only where those factors imply different observations. Do not require natural-language explanations as the representation.

All compared inference routes get identical permitted artifacts, context, candidate support, and declared resource budgets. Add copied-brief, matched-other-maker, duplicated-evidence, and simple feature/retrieval rivals. Model selection happens on development data. Report both predictive gain at a fixed budget and cost to reach a fixed quality, rather than letting more calls silently win.

Borrow operations with source attribution. [LIRAS](https://aclanthology.org/2025.findings-emnlp.654/) motivates separating representation construction from execution over the same representation. [ROTE](https://github.com/KJha02/mindsAsCode) motivates executable behavioral mixtures. [Open-ended SIPS](https://github.com/cosilab/OpenEndedBlockWords.jl) motivates replenishing proposals after contradictory evidence. Their original tasks and guarantees do not become artifact-reading results by import. Unknown language-model proposal probabilities do not support claims of exact importance weighting or an exact posterior.

### 5.3 Evidence views

| View | Reader receives | Permitted interpretation |
|---|---|---|
| Artifact primary | Finished artifact or explicitly defined current draft, ordinary task context, and permitted earlier artifacts | Artifact-based reconstruction and held-out prediction, at the available label quality. |
| Artifact plus verified context | Same artifact plus a source-identified cue, with cue reliability modeled | Whether context improves prospective inference, not merely changes a story. |
| Process-record diagnostic | Explicit before/after pair, action history, or genuine production trace | What extra process access buys; never pooled with artifact-only results. |
| Supplied-state / supplied-purpose diagnostic | Declared numeric state, operative rule representation, or true purpose | Information/execution ceiling. Privileged input remains labeled. |
| Evaluator-only truth | Constructor state, hidden continuation, stroke order, labels, future drafts, confidential split keys | Scoring only, after reader predictions are frozen. |

A finished artifact may erase the route that produced it. Preserve equivalence classes rather than force a unique historical answer. Reader-enactable reconstruction, historical correspondence, and later value inference remain distinct outputs; this stage does not promote value or alignment claims.

## 6. Card inventory

Every card's implementation must include a plain-language hypothesis, method, primary contrast, independent unit, permitted evidence, strongest rival, gates, null and alternative expectations, exhaustive outcome bands, source pointer, runtime, and unique produces path. The tables below specify the scientific content; the coding agent fills measured scheduling quantities before the scientific lock. All contrasts use the common analysis rules in §7.

### I. Six preparation and instrument cards

| Card | Question and operation | Required boundary |
|---|---|---|
| I01 | Can we reconstruct current state, source identities, dependency scope, and all inherited failures? Build the Stage 9 manifest and reconcile Stage 8 references. | Missing old evidence is recorded, never filled with current hashes. |
| I02 | Are external checkouts and data really usable? Apply §4, real-schema fixtures, count reconciliation, and separate reproduction receipts. | A failed source blocks only its consumers; inventory is not scientific replication. |
| I03 | Does the repaired scorer treat every option correctly on the actual task supports? Include supports beyond 12, boundary ties, stop, permutations, missing values, and frozen precision fixtures. | Component failure invalidates the aggregate; no uniform fallback disguised as a prediction. |
| I04 | Do surprise, maker-conditioned gain, and attribution behave correctly when the answer is known? Use exact population/individual predictors, no-individuality worlds, predictable signatures, noise, and equifinal histories. | Raw surprise retains its old sign. New rulers use fresh lineages and their own meanings. |
| I05 | Does each borrowed method perform its defining operation? Reproduce a cheap released anchor where possible; otherwise report a verified operation adaptation with an independent exact fixture. | No paper-level reproduction claim from a toy adaptation, renamed algorithm, or matching one unrelated count. |
| I06 | What survives the repaired supplied-state comparison? Compare direct and explicit execution over the same declared operative information, then separately remove or add information. | Distinguish information access, encoding, readout, and execution. Do not call unlike model packages a pure size test. |

### C. Eight competence questions

| Card | Question and method | Discriminating outcome |
|---|---|---|
| C01 | Where does offered-choice success end? Run genuine prefixes, equally legal altered prefixes, and generated prefixes with the same next-action scoring. | A generated-history deficit at matched current state differs from basic rule ignorance. |
| C02 | Which component breaks sustained generation? Compare offered actions, freely named actions with environment-produced outcomes, and full self-generated logs; score stopping separately. | Locates action selection, outcome production, or termination failure without crediting an external legality mask to the model. |
| C03 | Can a local critic make a useful change? Predict consequences of an unseen local edit, propose a repair, execute it under visible rules, and score goal satisfaction and collateral damage. | Separates an explanatory account, a usable local operation, and a whole-artifact generator. |
| C04 | Does the reader preserve a coherent process across equivalent and distinguishable states? Adapt compression/distinction tests on the exact finite-state subset, including longer distinguishing continuations. | Good one-step prediction with inconsistent future consequences identifies a specific competence gap. |
| C05 | Does training breadth or learner-state exposure repair the gap? Run the 2 × 2 training design with three seeds per family and fixed exposure. | Identifies which intervention helps, their interaction, and seed fragility. |
| C06 | How does failure grow with horizon? Use matched horizons of 1, 4, 8, and 16 supported actions; compare periodic genuine-state reset with uninterrupted rollout. | Distinguishes compounding error from an immediate inability; reset assistance remains visible. |
| C07 | Does competence transfer to new rules and combinations? Keep the original second-family challenge for narrow-training arms; evaluate broad arms on withheld compositions/parameters. | Training-family fit and broader rule use receive separate verdicts. |
| C08 | Does process competence survive the artifact projection? Compare finished outputs, partial artifacts, and full logs while holding underlying units fixed. | Quantifies what the artifact erases and whether the reader can operate without being handed the production record. |

C04 imports the distinction between histories that reach the same state and histories whose future possibilities differ from [Vafa et al.'s world-model evaluation](https://arxiv.org/html/2406.03689v3). Its finite-automaton results do not automatically apply to a stochastic maker with hidden state; use the exact supported subset and label extensions separately. Do not run the reference repository's default multi-GPU training setup.

### M. Six maker-reconstruction questions

| Card | Question and method | Discriminating outcome |
|---|---|---|
| M01 | Does modeling this maker improve prediction beyond a capable generic process? Compare population, cheap individual adaptation, program mixture, and differentiated maker model on another artifact. | Individual gain must beat matched-other-maker context and the strongest cheap rival. |
| M02 | Is the bottleneck missing hypotheses or scoring them? Cross a shared candidate pool with different evaluators; separately test widened proposals and evaluator-only known-support ceilings. | Proposal quality and evaluation quality can improve independently; oracle assistance stays diagnostic. |
| M03 | Does purpose help when it is correct, uncertain, or confidently wrong? Compare no purpose, inferred distribution, selected single purpose, supplied truth, and matched false purpose. | Distinguishes harmful commitment, missing support, and inability to use a good purpose. |
| M04 | Do earlier works accumulate? Dose 0, 1, 3, and 7 distinct prior artifacts, with same-maker, matched-other-maker, and duplicate controls. Score a new work, not fit to the supplied works. | Tests useful predictive accumulation without requiring rising raw surprise. Unsupported long series get a recorded shorter dose. |
| M05 | Can the reader preserve ambiguity while remaining useful? Use identical-output/different-history cases and changed-context continuations that separate some, but not all, hypotheses. | Credits calibrated equivalence and useful reenactment separately from historical identification. |
| M06 | When does the maker's share become visible? Cross decision freedom with constraint strength and artifact lossiness using existing supported constructor manipulations. | A boundary surface, not an aggregate “artfulness score”; verify realized degrees of freedom independently of the reader's result. |

### T. Six walkthrough-derived transfer questions

| Card | Question and method | Discriminating outcome |
|---|---|---|
| T01 | Does an end survive a ban on its familiar means? Hold purpose fixed, remove one tool/operation, and test prediction of an alternative way to produce the effect. | Separates repeated surface technique from prediction of adaptation. |
| T02 | Does familiar authorship require surprise? Cross familiar/unfamiliar maker with expected/unexpected choices; compare recognition, prospective gain, and entry-point selection. | Recognition may rise while surprise falls. Surface recognition alone receives no process-recovery claim. |
| T03 | Does old skill transfer to a changed goal? Keep an identifiable operation reusable while reversing its intended use; include unchanged-goal harder-task controls. | Operation reuse differs from simple persistence, erasure, or generic task difficulty. |
| T04 | Does enduring context reorganize predictions more than a local detail? Supply true, false, and irrelevant cues with global or local causal reach in constructed cases. | Measures prospective correction and susceptibility separately from explanation change. |
| T05 | Is the trace the maker's adaptation or inherited collaborators' practice? Use existing supported mixed-control cases with maker and collaborator interventions separately. | Avoids assigning every persistent signature to the director. If the existing constructor cannot identify the contrast, route it to a Ghost design note and keep human cases descriptive. |
| T06 | Does learning that a better move exists reveal how the old move was chosen? Separate independently observed non-consideration, misvaluation, changed information, and mere later endorsement. | Prevents treating acceptance of a superior alternative as proof it was absent from the earlier search. |

### H. Eight external-data questions

Each row is conditional on its own data gate. A corpus may support label agreement or a record-based diagnostic while failing artifact-only identifiability. Say which happened.

| Card | Source and test | Required rival or limit |
|---|---|---|
| H01 | ArgRewrite: artifact-only versus actual revision-pair access for purpose-label recovery; where a genuine later version exists, predict its revision family. | Canonical units, multi-purpose handling, before/after lexical features, majority and prior-label baselines. No invented future version. |
| H02 | IteraTeR-HUMAN and eligible arXivEdits: compare evidence views, domain transfer, and prediction across actual successive revisions. | Separate human versus model labels, retain disagreement, group documents and linked versions, deduplicate the overlapping scientific-paper sources. |
| H03 | B-roll: use earlier selections from a person to predict concept choices on a held-out script under its stated commission. | Commission, noun/adjective selection, population word preference, highlight budget, and matched-other-person context. Report reader/person and script/topic dependence separately. |
| H04 | Shelley-Godwin, then Woolf if ready: reconstruct a usable local revision or predict a withheld documented change from the permitted text view. | Editorial hand and transcription uncertainty, partial temporal order, copied-text baselines, famous-text memorization, and strictly qualitative claims when independent works are too few. |
| H05 | Drawings of THINGS, if ready: do earlier finished drawings help predict another finished drawing's observable structure, beyond object and device? | Object geometry, population drawing features, device/skill metadata, and wrong-maker histories. Historical stroke claims require genuinely withheld trace evidence and a calibrated instrument. |
| H06 | CommitBench slice: infer stated change purpose from a diff, then test transfer across repositories rather than merely retrieval of message vocabulary. | Boilerplate, change size, filenames, repository/topic identity, and coauthorship. Without stable permitted maker IDs, do not run individual accumulation. |
| H07 | CoAuthor: prospective suggestion handling after proper document reconstruction, with artifact and explicit-record views reported separately. | Action base rate, previous decision, text state, suggestion quality proxies; repaired accept/edit/dismiss/ignore semantics and mixed agency retained. |
| H08 | ScholaWrite and eligible NewsEdits: predict the next revision category/location from the current draft and permitted prior context. | Previous-label/persistence and lexical-difference baselines; grouped evaluation and edition provenance. An unexplained failure below those baselines remains a failure. |

H03 needs repeated-person and script structure verified before implementation. A leave-one-script-out analysis is not a temporal forecast unless trial order is available and respected. H04 is not a population-level test simply because many manuscript pages exist. H05 remains a conditional branch, not a promise that a working visual model is installed.

### S. Four reader-objective and information-selection questions

| Card | Question and method | Discriminating outcome |
|---|---|---|
| S01 | Does the reader's objective change what evidence is worth inspecting? Compare learning a useful technique with predicting this maker, on the same permitted evidence pool and cost. | Different acquisition/stopping can be appropriate while underlying inferential capability is unchanged. |
| S02 | Which entry route is useful? Compare anomaly, familiar signature, affordance, random, and full-view entry at fixed observation budgets. | Score quality and cost separately; an entry route can save effort without changing the eventual answer. |
| S03 | Should the reader seek uncertainty or consequential disagreement? Compare random acquisition, model entropy, and candidate disagreement about future choices. | Evaluate realized predictive gain; high entropy alone can select noise. The pool contains only permitted observations. |
| S04 | Can the reader know when its current account is enough? Predict uncertainty reduction and future improvement before buying another artifact or stopping. | Calibration and useful stopping, not confidence inflation from repeated exposure. |

The regret-based environment-selection literature is an adjacent method for S03, not a proof that the adaptation works: [Environment Design for IRL](https://proceedings.mlr.press/v235/kleine-buening24a.html). These cards select existing observations or supported constructor contexts; they do not authorize contacting makers or collecting new human participants.

### B. Four closure cards

| Card | Required product |
|---|---|
| B01 | Freeze at most three claim packets, each with an exact reader package, target, contrast, gate scope, untouched reserve, sample size, and strongest adversary. An empty selection is allowed. |
| B02 | Execute those frozen confirmations once, retaining every outcome. Reconcile three-seed evidence where training is part of the claim. No replacement of an unsuccessful claim after viewing its reserve. |
| B03 | After all scientific and repair outputs, validate complete source/adapter/data lineage, live gate decisions, cell counts, read-only isolation, resource accounting, and a genuine fresh-process reproduction of selected final calculations. Distinguish this from a new scientific replication. |
| B04 | Produce the final textured curator packet, full internal write-through, coverage map, external-readiness register, and next decisions. Do not pick a subsequent stage automatically. |

## 7. Shared design and analysis rules

### 7.1 Separate the quantities

The primary maker benefit is the held-out log-score difference between individual conditioning and the strongest appropriate baseline on the **same target and evidence budget**. Average within the independent maker/world/document unit before summarizing across units. For human selection tasks, use an appropriate proper probability score such as Brier score and report selection overlap separately; do not pretend selections have a mutually exclusive next-action distribution.

Keep these separate: raw surprise; probability gain from maker conditioning; ability to identify a maker; actual effect of an intervention in a constructed world; reader-enactable success; historical correspondence; calibration; and cost. No aggregate intent score and no pooled league table across incompatible units.

A simple known-answer example belongs in I04: population action probabilities (0.25, 0.01, 0.74), individual probabilities (0.80, 0.02, 0.18). The first action has a larger probability uplift, while the second is more surprising under either predictor. This demonstrates why the orderings need not agree. It does not explain Stage 8's empirical sign. Perfect individual conditioning should improve expected future log score under a correctly specified generator; realized finite samples can still vary.

Every instrument must pass both an absent-signal case and a present-signal case. A random or constant reader cannot pass a competence claim. A masked decoder cannot demonstrate that its unmasked model knows legality. A label supplied through markup cannot demonstrate inference.

### 7.2 Units, split, and sample allocation

Use separate construction/training, discarded timing pilot, discovery, development/selection, and sealed confirmation lineages. Split at the highest shared source unit: maker series in the constructor, paper/project/version lineage for revisions, participant and script for B-roll, drawing maker plus object family, repository for code. Do not count words, pages, actions, or multiple adapters' readings as independent people.

For synthetic discovery, begin with **192 independent world or maker-series units per principal contrast**, balanced across the two existing artifact domains and declared conditions. Use **96 generation units per reader package** for the broad gate profile, reporting feasibility with intervals and the original criterion's pass/fail separately. Use fresh paired worlds for differences. The full generation-and-horizon diagnostic initially runs on the archived adapters and a development-selected new recipe per family, retaining that recipe's three seeds. All 24 fits still receive their declared validation and basic admission measurements; do not quietly drop bad seeds.

For human data, report the actual eligible groups and class counts before assigning sample sizes. A corpus with fewer than 60 independent groups can still supply a descriptive or bounded paired analysis; it cannot support a broad new population claim merely by sampling more rows. In particular, the B-roll task's limited scripts and the genetic editions' limited authors constrain generalization even with many decisions. Use grouped cross-validation for discovery where needed. Prior project exposure and plausible foundation-model memorization are separately disclosed.

Reserve **30% of genuinely untouched eligible groups** for confirmation when a feasible reserve exists. If all of a corpus was already examined in earlier stages, its reused data remain discovery or robustness evidence. New split names do not create untouched data. Human branches without a credible reserve can still be informative and cannot provide that stage's independent confirmation.

### 7.3 Effect size, uncertainty, and selection

Report paired effect sizes and 95% cluster-resampled intervals, class/condition coverage, all seed results, and exclusions. Use two-way grouping or leave-one-script/topic sensitivity when both people and stimuli drive dependence. For deterministic exact worlds, use exact contrasts where feasible and say so.

For forward-choice log scores, **0.05 nats per averaged independent target** is the proposed practical-effect threshold for promoting a discovery, not a law of the theory. For other scales, freeze a task-appropriate practical threshold before evaluating discovery, derived from known-answer and null distributions and stated in plain language. Zero-crossing intervals are inconclusive; an interval contained inside a declared practical-equivalence region supports a bounded small-effect conclusion. Never translate a low-power null into theory death.

Choose confirmation sample size once from discovery variance and the frozen practical effect, targeting 90% power with the familywise error budget for at most three confirmations. If the feasible reserve cannot provide it, report the achieved detectable effect and keep the result exploratory. Adjust confirmatory tests across the selected claims, for example Holm at familywise 0.05; register any additional significance analyses in the project's multiplicity audit. Discoveries are a search map, not dozens of uncorrected confirmations.

Do not select only positive branches. Selection priority is: identifying a broken comparison; discriminating serious rival explanations; then a useful capability. A clean negative that distinguishes two proposed mechanisms can merit confirmation. Predetermine the claim-selection rule and any sequential stopping before opening the reserve.

### 7.4 Twelve attacks, applied where relevant

| Attack | What it must expose |
|---|---|
| X01 | Exact and near-duplicate leakage across train, earlier works, target works, corpora, and reserve. |
| X02 | Hidden labels/state leaking through IDs, path names, markup, caches, adapters, or reference imports. |
| X03 | Topic, genre, length, device, edit size, and familiar wording standing in for the maker. Preserve the intended signal rather than subtracting it away. |
| X04 | Wrong-person context and shuffled maker assignment at the correct grouping level. |
| X05 | Duplicate evidence counted as independent support or extra effective sample size. |
| X06 | Candidate order, wording, count, truncation, support omissions, and component-invalidity propagation. |
| X07 | Batch/precision effects exceeding the separately measured apparatus envelope; retain both old and amended historical tolerances. |
| X08 | Purpose/context interventions that fail to realize the claimed target or change several causal factors together. |
| X09 | Fluent explanatory stories without useful prospective consequences; false context that increases confidence while reducing accuracy. |
| X10 | Equifinal histories, absent proposals, forced unique answers, and uncalibrated certainty. |
| X11 | Pooled success hiding reversed families/domains, minority classes, low realization, or a single lucky training seed. |
| X12 | A killed/resumed real job duplicating units, silently changing its clock, losing cost, closing on fragments, or allowing one process to overwrite another's status. |

Derive each attack's expected response under both the null and the intended alternative. A shuffle or ablation that destroys the relevant task is not a clean control. Read the existing CONTROLS and LESSONS before implementation; the new stage must not repeat the dose-eating or direction-blind tests already corrected there.

## 8. Five-day operating plan

**Approximately 120 wall hours is the planning horizon, including preparation and closure.** It is not a reason to sleep until a deadline or fabricate occupancy. Preserve the currently authorized local gear; this specification does not itself switch the user's machine into another gear. Budget below assumes the available full-machine local allocation. If the curator takes back the GPU, record the availability change, keep eligible CPU work running, and revise the forecast visibly. No Gear 3, paid frontier probe, or remote inference fallback.

The ordinary run-to-empty policy remains: finish the finite selected queue. At the horizon, stop admitting new expansion work, finish or checkpoint the bounded active job as declared, and report any overrun. Do not silently turn the horizon into either an endless campaign or an abrupt kill of valid work.

The table is a resource envelope, not measured utilization. CPU intake and analysis can overlap GPU jobs without giving two processes ownership of the card.

| Wall-hour region | Main work | Initial GPU-hour allowance |
|---|---|---:|
| 0–12 | Source/data intake, known-answer gates, matched-information contract, discarded timing pilot, early CPU baselines | 4 |
| 12–38 | Training factorial and competence profiles; continue real-data parsing and anchors | 24 |
| 38–68 | Maker comparisons, purpose, accumulation, and transfer; complete conditional external pilots | 26 |
| 68–92 | Eligible human branches, reader objectives, information selection, decisive boundary expansions | 18 |
| 92–110 | Frozen confirmations and predeclared confirmation controls | 16 |
| 110–120 | Final calculations, necessary reproducibility checks, reconciliation, theory write-through, packet | 4 |

The initial total is **92 GPU hours**, leaving wall-time room for transitions, CPU-bound work, repairs, and availability loss. It is not a target for utilization padding. Log GPU reservation, actual observed utilization when available, CPU work, I/O, failures, and unmeasured periods separately.

**Pilot before lock:** run complete representative cells for training, full generation, all-option scoring, one long maker-series context, one real external loader, and one actual kill/resume. Pilot outputs do not enter science. Lock source copies, task-specific maximum support/context sizes, split units, sample counts, and complete cell identities only after the measured throughput supports the schedule. Test manifests must enumerate actual runs, not hypothetical output files. Every planned cell has a unique produces guard and reads its prerequisites' verdicts.

**Keep the queue roughly one day deep when the gear permits.** Reforecast after the first training pair, each completed trunk, and any availability change. CPU work must never wait on an unrelated failed neural-reader gate. The code agent manually translates cards into the queue under the existing operating contract; a scheduler must not invent studies from prose.

### Useful expansion ladder

The expansion order is frozen before discovery, with eligibility decided from completed results and measured rates:

1. Repair a failed instrument once on separate fixtures, then rerun only its dependent contrasts with a new lineage.
2. Increase independent units for the highest-value rival-discriminating contrast from 192 to 384, then 768, if the expected interval reduction matters. New units, not repeated scoring of old ones.
3. Complete the second corpus or second task family for a promising operation; prioritize a different failure mode over another rendering of the same task.
4. Increase earlier-artifact dose only where actual distinct works and context capacity exist; compare diversity with repetition at matched tokens.
5. For the best recipe only, increase training data to 4,800 examples if learning curves and gates show a concrete unresolved sample-limited boundary. Keep all three seeds and the matched-exposure comparator needed for the claim.
6. Map a decision boundary by varying one realized constraint at a time, then its prespecified interaction. Do not add new conceptual factors merely because compute remains.

Release unused confirmation budget only after the claim selection is formally empty or its bounded work is complete. Use the same ladder. If no eligible rung would resolve an open question, close early with the actual reason. Underfill itself gets an explanation: blocked data, thin hypothesis coverage, underestimated setup, faster cells, exhausted repairs, or unavailable hardware. It is not hidden by reservations or wait loops.

### Failure branches and repair budget

- **No full generator passes:** complete the competence map, any independently qualified local-operation tests, exact program comparisons, and external-data baselines. Full-process maker claims stay blocked. Do not run every expensive downstream neural condition merely to rediscover the failed precondition.
- **Local construction passes but full generation fails:** pursue maker reading within the qualified operation and test whether it scales with horizon. This is a new bounded claim, not a lowered full-generation threshold.
- **Surprise ruler fails its intended mechanism test:** keep its recorded hypothesis as a failed locator; use separately validated predictive/attribution measures on fresh data. No post-hoc sign reversal as a confirmation.
- **External data are inaccessible or unsuitable:** cap each source at one canonical route and one verified public alternative, at most two active operator-hours, then continue another named source. No repeated access workaround or author request.
- **Proposal family misses plausible makers:** spend the predeclared proposal-revision branch; a second failure closes that implementation family for the stage, not the whole theory.
- **A true implementation defect appears:** one repair per root cause, retained failed attempt, updated dependency scope, and fresh eligible data where outcomes influenced the change. A second substantive defect in the same instrument closes its consumer branch unless already-reserved independent alternatives remain.
- **A result changes a load-bearing definition:** prepare the narrow theory-change interrupt with extended examples. Continue unaffected authorized work. Do not silently ratify the analyst's preferred ontology.

## 9. Implementation and final reporting

Use new Stage 9 modules and result roots; reuse stable, tested components rather than copy the whole stack. Likely owners are runners/stage9/, its reader and testbed subpackages, the existing constructor through a pinned interface, fetch-side intake, tests for the new gates, and results/phase_2_4_stage_9/. The final file layout is an implementation choice. Do not edit locked SPEC/preregistration/lock files; record scoped deviations through the existing method owner.

Before launch, require: real positive/negative instrument fixtures; a source/data access inventory; reader-package identities; complete scheduled-cell enumeration; honest source availability; forecasted workload; a functioning owner-session wake; and a successful real interruption/restart rehearsal. Preserve the repaired atomic status writes, process-creation checks, and one-writer ownership. No new subagent delegation is authorized by this handoff.

Every completed result receives the existing full internal write-through in order: FINDINGS, appropriate theory row and afterword or TOOLS instrument row, TODO, and the curator roll-up. Keep source-scoped failures and public-claim ceilings attached to the result. The final integrity check runs after all scientific and repair outputs. Routine mechanics stay with the coding agent; the curator receives one final synthesis plus material blockers or requested progress updates.

**The final packet must make the science understandable without identifiers.** Begin with the world-model changes, then show:

1. A competence map: what each reader can predict, change, generate, transfer, and stop, including assistance supplied.
2. A maker map: which benefits come from population knowledge, individual evidence, purpose, and explicit reconstruction; where the cheap rival suffices.
3. A substrate map: constructed logs, finished constructed artifacts, human selections, revisions, genetic editions, code, and any admitted visual task. Show where the evidence stops.
4. The confirmation results, including all failures and the exact scope of successes.
5. A readiness register distinguishing 17 inherited source checkouts from newly executable operations, actually acquired data, real loaders, reproduced anchors, and new scientific results.
6. **Eight preselected case types**, sampled by fixed seeds within each type: useful local repair; first sustained-generation failure; predictable maker signature; unsupported confident explanation; helpful true context; harmful false context; persistent ambiguity; strongest cheap-baseline victory. Report a case type as absent if it did not occur. Include denominators so examples do not substitute for the distribution.
7. Separate pursuit and warrant ledgers, the strongest remaining rival, and one recommended next decision with its real objection.

The record must distinguish IMPLEMENTATION INVALID, INCONCLUSIVE, PRACTICALLY SMALL, COUNTEREVIDENCE, SUPPORT CANDIDATE, CONFIRMED WITHIN SCOPE, DESCRIPTIVE, and NOT RUN WITH REASON. These are disposition labels for this handoff; map them explicitly to existing registry enums rather than silently inventing incompatible storage values.

### How the final patterns would change the project

These are prospective interpretation rules, not predictions of success. They prevent a long battery from returning another list of disconnected scores.

| Possible pattern | What it would mean |
|---|---|
| Local intervention prediction and repair work; sustained generation still fails | Useful production knowledge can be local. The broad generator remains unbuilt, while the local critic becomes a legitimate bounded test subject. |
| Broader training or learner-state exposure repairs generation; maker adaptation still adds nothing | Missing production competence was a real engineering bottleneck, but fixing it was insufficient for the individual-inference operation. |
| Explicit execution wins after operative information is matched | Some usable knowledge is available but does not become reliable consequences through direct inference alone. Keep the aided system's success and its assistance explicit. |
| Individual adaptation predicts new works; a cheap model matches the differentiated one | There is useful individual structure, without evidence that the richer explicit representation adds value on this task. Inspect whether the cheap representation encodes equivalent distinctions. |
| Familiarity rises, surprise falls, and individual prediction improves | Predictable signatures can support reading. The old raw-surprise locator was an incomplete instrument for that route. |
| All readers fail despite an independently verified artifact-visible oracle advantage | A real boundary of the tested inference family, with the next target identified more sharply than by a generic negative. |
| Neither oracle nor readers can separate the proposed histories from the permitted artifact | This observation cannot identify that historical difference. A useful reconstruction may remain possible; do not charge the reader with information the artifact erased. |
| Revision-pair or process-record views work; finished-artifact views fail | The extra record supplies decisive information. A bridge has been built, while artifact-only reading remains unresolved. |
| Context produces richer explanations and more confidence, but worse unseen-choice prediction | Projection is being amplified. This is evidence against that update method, not a reason to discount the reported subjective reorganization. |

These patterns can coexist in different domains and readers. Report the interaction instead of collapsing them into one project-wide success or failure.

### Pursuit and warrant at launch

| Branch | Why pursue it | Present warrant |
|---|---|---|
| Competence beyond one-step prediction | A usable local or sustained producer may make the central test possible. | Prediction gains; no Stage 8 full-generator admission. |
| Familiar maker without surprise | The walkthrough supplies an entry route the raw-surprise measure does not capture. | Curator hypothesis and logical measurement distinction. |
| Executable maker reconstruction | A strong alternative to labels, and a serious rival to differentiated latent descriptions. | Bounded prior program success plus adjacent literature; not general artifact reading. |
| Changed means and repurposed skill | Could identify what persists across context better than simple signature matching. | Walkthrough hypotheses, with unequal confidence retained. |
| External creative and revision data | Supplies genuine human decisions and different observability limits. | Acquisitions and source-defined labels; historical motives remain only partly observable. |
| Reader objectives and stopping | Separates inability from a rational choice not to investigate. | An operational hypothesis; no human neural or empathy-mechanism claim. |

## 10. Future difficult prompts, if a result requires another discussion

These are optional examples of the revised question format, not another required answer round.

**A critic in the editing room.** Imagine three people watching the same scene. One can explain each shot beautifully after it plays. Another predicts how an unfamiliar cut will change the scene, but cannot sustain a film alone. A third can direct a new scene under unfamiliar constraints and anticipate the result. You might think these are different degrees of one capacity, different capacities that usually grow together, or a misleading division. Walk through where you would place the forward generator, and change any example that misdescribes the experience.

**Recognizing a director before knowing why.** One film uses the director's usual framing. Another bans that framing but produces a similar pressure through performance. A third imitates the familiar shots while feeling hollow. A fourth comes from someone else but briefly gives you the same feeling. Describe what associations you would trust, what you would inspect next, and what could make you revise the first confident recognition. There is no requirement that the first feeling be wrong, verbally explicit, or surprising.

## Acceptance of this handoff

The proposed next stage is broad enough to spend five days usefully, but its scientific value is not proportional to its job count. Its decisive product is whether we can locate usable production competence, exploit it to read an individual beyond generic knowledge, and carry that operation into more faithful human artifacts. A stage that identifies a concrete failure boundary and builds two genuinely usable external substrates can advance that program without manufacturing a positive theory verdict.

This file is ready to hand to the coding agent for implementation and local scheduling. It does not assert that implementation has begun or that any future hypothesis has already earned support.
