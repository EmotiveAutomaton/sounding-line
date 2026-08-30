# Sounding Line Phase 2.4, Stage 5: Routed Joint Reconstruction

**Status:** research-informed coding and execution handoff; this document does not claim that the experiments have run.

**Prepared:** 2026-08-29, after the Stage 4 and Ghost Scale V13 result audit and the curator's second verbal walkthrough.

**Reviewed Sounding Line commit:** `8230a933fab805a4ee39c256f1e189fe46314dfe`.

**Companion constructed-world handoff:** Ghost Scale Sim `V14_SPEC.md`.

**Scope:** 29 mandatory cards across eight tracks, including at most two fresh confirmations.

**Runtime:** one continuous 24-hour local execution window. Internal checkpoints are required. **No early, daily, milestone, or partial curator packets are permitted.** Emit one final curator packet after the window closes.

**Claim class:** bounded model-reader, controlled-artifact, method, and dataset results only.

This handoff inherits `CLAUDE.md`, `docs/STATE.md`, `TODO.md`, the five living theory files, the standing method shelf, locked preregistrations, and the Analyst–Curator Epistemic Protocol. It does not create a sixth theory file. All paths below are relative to the repository root.

---

## 0. Executive instruction

Build and run Stage 5 around one question:

> Can a bounded reader improve held-out maker prediction by jointly reconstructing a process, an episode goal, and a standing preference while selecting among action, semantic, contextual, and forensic evidence routes—and can it keep the maker's appraisal, intended audience effect, its own response, source reliability, and later uptake separate?

The stage has five substantive obligations:

1. meet the unmet floor on Stage 4's only causal-use-during-inversion result, L255/A07b, using a second checkpoint and a second artifact domain;
2. compare joint reconstruction with equally informed independent and staged pipelines rather than assuming that the three inferences must be solved simultaneously;
3. distinguish a route's predictive reliability from its ease or fluency, and test whether route conflict usefully opens a missing-goal or strategic-communication hypothesis;
4. separate reader affect, maker appraisal, intended audience response, content truth, communicative goal, reliability, and uptake in surface-matched controlled artifacts;
5. preserve the distinction between a process the reader can enact and the historical process that actually produced an artifact.

Do not pause for curator input once the execution clock begins. A failed track may close while independent tracks continue. Downstream architecture cards receive oracle or graded upstream posteriors when an upstream reader fails, so one weak reader cannot silently cancel the scientific program.

This authorization is local only. Do not spend money, use paid APIs, recruit people, contact authors, start cloud training, or change the user's GPU gear. Do not add agent delegation. Respect existing model and dataset licenses.

## 1. What the walkthrough changed

### 1.1 The three inferences may be recurrent without being inseparable

The curator's revised picture is not a clean serial pipeline. A proximal goal may become probable while process and persistent preference remain broad; a proposed process can then change the likely goal; repeated episode goals can constrain a standing preference; and a standing preference can reweight earlier process explanations. Stage 5 therefore compares:

- a factored independent reader;
- `goal -> process -> preference`;
- `process -> goal -> preference`;
- `preference -> goal -> process`;
- a recurrent joint reader that revises all three;
- an oracle joint posterior.

All receive the same evidence, candidate hypotheses, prior mass, token allowance, and scoring interface. A joint reader wins only if it improves prospective prediction or calibration, not because its rationale sounds more coherent.

### 1.2 Evidence can accumulate without a single decisive cue

Save a posterior trajectory after each evidence item. Measure when each latent becomes provisionally useful, how often it later reverses, and whether high early confidence causes failure to notice inconsistent evidence. Do not force an “earliest clue” when the construction supplies only a stacking effect.

### 1.3 Familiarity supplies routes, not truth

The curator reports that familiar production domains make tools, gestures, and revision paths easier to propose. In the model, Stage 5 may manipulate domain demonstrations and measured route competence. It may not call short in-context demonstrations human expertise or identify expertise with prior attention history. Ghost V14 performs that factorial dissociation in a known-answer world.

### 1.4 A felt effect is a proposal about intended effect

The reader's own response can cheaply initialize an intended-audience hypothesis. It cannot establish that the maker shared that response or that the intended target and causal reason were correctly recovered. Stage 5 keeps four owners separate:

| Variable | Question |
|---|---|
| reader response | What continuation or choice did the presentation induce in this reader? |
| intended audience effect | What response did the maker try to induce? |
| maker appraisal | What did the maker appear to believe or value about the subject? |
| world/content state | Was the described threat, benefit, or claim actually supported? |

Communicative goal, reliability, and later uptake remain additional variables. A source may sincerely believe a false warning, strategically present a true fact, or induce the same fear under either regime.

### 1.5 Understanding technique is not automatically protection

Stage 4 found that a technique lesson shifted criterion without improving discrimination. Stage 5 therefore tests three distinct operations:

1. recognizing a technique;
2. reconstructing why this maker selected it for this audience;
3. changing evidential weight or policy uptake appropriately.

A response that simply rejects every persuasive message fails. A response that accurately identifies a tactic but preserves the same indiscriminate uptake is comprehension without protection. Conversely, useful fear may remain after a truthful, proportionate warning is understood.

### 1.6 Interest is not equivalent to unexplained error

The curator's proposed compression is testable: novelty, complexity, and coping potential may partly track structured decisions the reader cannot yet explain. But random noise is unexplained and often uninteresting; a novel item can be immediately explained; and a complex artifact can be highly compressible. Stage 5 crosses these cases and scores evidence choice, not a free-form claim of interest.

## 2. Research that changes the implementation

The sources below motivate discriminators; they are not Sounding Line results.

| Research object | Design import | Limit |
|---|---|---|
| [CLIPS: cooperative language-guided inverse plan search][R01] | Jointly use actions and language to infer a goal and plan; retain posterior uncertainty and score assistance prospectively. | CLIPS assumes a cooperative planner. Stage 5 crosses cooperative, neutral, sincerely alarmed, and strategically manipulative source goals. |
| [Grounding Language about Belief][R02] and [LaBToM][R03] | Use a constrained latent language and evaluate statements against an inverted generative model. Grammar-constrained decoding is preferable to unconstrained rationales. | Their tasks concern agents in controlled navigation worlds, not artistic values or human empathy. |
| [Storytelling as inverse-inverse planning][R04] | A maker may choose observable actions to shape an audience's inverse inference. Compare ordinary inverse planning with an audience-modeling maker. | Expressive construction does not by itself distinguish sincere teaching from manipulation. |
| [Learned value and attentional capture][R05] | Past value-linked attention can persist and can bias present selection. | A model prompt cannot establish a human attentional habit. Ghost V14 supplies the constructed dissociation. |
| [Expert–novice relevance selection in chess][R06] | Domain skill can change which information is selected early. Measure route competence instead of assuming that a familiar narrative is accurate. | Chess expertise does not establish a domain-general maker-reading mechanism. |
| [Self-generated cognitive fluency][R07] | Internally constructed models can alter fluency and evaluation. Cross operational ease with actual predictive reliability. | Model entropy, latency, or likelihood is not subjective human fluency. |
| [Influence awareness and affect misattribution][R08] | Source awareness can moderate affect-based judgment. Add explicit source attribution and influence-awareness conditions. | Awareness does not guarantee correct source reconstruction or resistance. |
| [Learning progress as intrinsic motivation][R09] | Compare raw novelty and prediction error with expected reducible error or learning progress. | The cited work is a computational/robotic hypothesis, not a settled neural account of curiosity. |
| [Hierarchical inverse reinforcement learning][R10] | Repeated transition structure can support subtask inference. | A readable subtask hierarchy need not identify a final value or historical director. |
| [Multiple suboptimal experts and reward ambiguity][R11] | Diverse calibrated demonstrations can shrink a compatible reward set; identical evidence adds no constraint. | Do not average reader posteriors: intersect or combine them under explicit reliability bounds. |
| [AutoToM][R12] | Use uncertainty to decide when to add a missing mental variable or a longer evidence window. | Model expansion must pay a search cost and face consistent-world false positives; adding latents after every error would overfit. |
| [LLM-augmented inverse planning][R13] | Let a language model propose open-ended hypotheses while a generative inverse-planning layer scores them. | Hypothesis proposal and warrant must remain separate; an eloquent proposal is not evidence. |

The practical import from the current Tenenbaum-associated work is a representation discipline: infer a structured latent state, preserve alternatives through a sequence, and model a maker who may be choosing evidence for an audience. It is not permission to copy a cooperative-agent assumption into propaganda, art, or ordinary authorship.

## 3. Starting record and mandatory debts

### 3.1 Stage 4 facts that govern Stage 5

| Result | Stage 5 disposition |
|---|---|
| A01 weakly separated maker appraisal from intended audience response and confirmed it. | Retain as a bounded readout anchor; add reader response, world truth, and communicative goal. |
| A02/A03 valence steering changed the reader's own answers and harmed maker prediction. | Do not rerun generic positive/negative steering as empathy. Use it only as a negative/control route. |
| L255/A07b congruent tendency steering improved held-out-maker prediction while random and incongruent controls did not. | Mandatory second checkpoint and second domain before any general bridge claim. Preserve coordinate, dose, decode, and zero controls. |
| T01 showed that a worked example can teach true and false rules; uptake followed either lesson. | Keep comprehension and uptake distinct. Test source-rule reconstruction before policy advice. |
| T02 reconstructed source rules better than summary but below direct/oracle. | Structured source-goal inference is live, but weak. Use candidate likelihood scoring and oracle bypasses. |
| T03 changed criterion without improving discrimination. | Technique knowledge is not media literacy. Require discrimination and appropriate selective uptake. |
| C01–C03 context, correction, and active selection were null or counterevidence. | Do not rerun prompt-only perspective taking or ask the model to choose among nearly equivalent probes. Validate route information first. |
| P02 recovered action information from unordered strokes beyond final raster. | Separate stroke-set/action constraints from actual stroke order and exact history. |
| Hierarchy cards read conventions better than hidden director choices. | Use dependency predictions only where process records exist; do not infer a director from coherence. |

### 3.2 Ghost V13 facts that govern Stage 5

- A fair local prior still produced selective near-maker advantage and far-maker projection cost, but almost no hidden-next-goal gain.
- Common-substrate cards C03/C05 failed their own controls and remain repair debts in Ghost, not Sounding Line evidence.
- Duplicate evidence increased confidence without accuracy; naive pooling of readers worsened inference.
- Cost and opportunity helped only under the correct cost model.
- Communicative goal, source reliability, content evidence, and uptake were separable in a constructed reader.
- Active selection helped only when actions changed access to meaningfully different evidence; the current PyMDP route closed.
- Full interaction logs could reveal a production hand that artifact-only and partial records could not.

Stage 5 imports these as controls and hypotheses only.

## 4. Construction requirements

### 4.1 Structured latent record

Every controlled world defines, without exposing by label:

```text
episode_goal            what this artifact is meant to accomplish now
process_plan            ordered or partially ordered production decisions
standing_preference     cross-episode weighting that predicts a future choice
maker_belief            what the maker believes about relevant world facts
maker_appraisal         the maker's signed/intensity assessment
audience_effect_goal    response the maker wants in an audience
communicative_goal      inform / assist / warn / impress / recruit / conceal / mislead
content_support         evidence for the proposition independent of the source
source_reliability      history-conditioned predictive reliability
reader_response         measured model continuation or decision
reader_uptake           later belief, process, or policy change
```

The first three are the triple-inference target. The remainder prevent an apparently successful result from succeeding by merging owners or stages.

Use a constrained schema with explicit `unknown`, posterior mass or candidate scores, and evidence-span references. Free-form explanation is a qualitative appendix only. Candidate order, labels, and surface length are balanced and permuted.

### 4.2 Controlled source families

Construct at least two domains whose surface language and choices are generated independently. One may be a workshop/editorial domain and one a public-warning or instructional domain. Do not use real political groups, personalized propaganda, protected classes, or diagnoses.

The warning family crosses rather than labels:

- source belief in danger: low/high;
- actual evidential support: low/high;
- desired audience arousal: low/high;
- desired audience action: absent/present;
- evidence selection: representative/cherry-picked/fabricated/uncertain;
- willingness to correct after counterevidence: low/high;
- surface intensity: low/high.

“Honest warning,” “sincere fanatic,” “strategic propagandist,” and “neutral report” are derived regions of this factorial, not four templates with telltale vocabulary. Surface-matched collisions are required. If a factor cannot be made live without leaking, close that attribution rather than accepting the label.

### 4.3 Evidence routes

Every route-selection world offers a declared subset of:

- **action/process:** strokes, revisions, tool constraints, or ordered decisions;
- **semantic/rhetorical:** claims, associations, framing, and audience-facing organization;
- **contextual:** role, institution, convention, opportunity, and source history;
- **forensic:** an optional costly observation that changes temporal or material resolution.

An exact or construction-based ruler computes each route's marginal information about the target before a model chooses. Candidate routes must differ materially. A model-choice card is void if the best and second-best routes differ by less than the frozen information floor.

### 4.4 Historical identity and enactability

For drawing/process cards, distinguish:

1. final geometry or text;
2. unordered action set;
3. partial order;
4. true chronological prefix;
5. exact historical sequence.

Create equifinal pairs with identical final artifacts and different valid histories. Artifact-only readers should retain uncertainty. An enactability score asks whether the reader proposes a valid way to produce the artifact; historical correspondence asks whether it identifies the actual held-out sequence. Never use one as a proxy for the other.

## 5. Shared card contract

Each card record must declare: ID; scientific question; construction; available evidence; target; estimand; null; directional or interaction alternative; strongest cheap rival; independent unit; minimum effective sample; domains/checkpoints; positive, placebo, surface, oracle, prediction, and calibration gates; dependency; repair; closure; claim ceiling; expected cells; and unique output paths.

Required lanes are `pilot`, `discovery`, `transfer`, and `confirmation`. Pilot outputs are never promoted. A reserve opened after inspecting its construction is not confirmation. Later items from one maker or source remain the same lineage.

All substantive claims require a hidden future choice, held-out process decision, or source response. Retrospective label recovery alone is method evidence.

## 6. Mandatory card inventory

There are 29 mandatory cards. The coding agent must instantiate every row in the expected-cell manifest before the runtime pilot. A failed prerequisite may substitute an oracle upstream object only for cards explicitly marked as downstream diagnostics.

### I — integrity and calibration (4)

| Card | Question and construction | Primary endpoint and closure |
|---|---|---|
| I01 | Can Stage 4 anchors and the relevant L255 rows be regenerated from committed inputs and hashes? | Numeric/hash receipt; mismatch blocks reuse but not independent new tracks. |
| I02 | Are the structured parser, label permutations, `unknown`, confidence, and evidence-span fields live and invariant? | Exact fixtures and order invariance; failure closes all affected structured readouts. |
| I03 | Are latent factors independently live, surfaces matched, and construction identities counted? | Factor manipulation, leakage baselines, collision registry, and lineage audit. |
| I04 | Do candidate routes and source regimes pass oracle, null, surface, and discriminability gates before model use? | Route information matrix and regime confusion floor; dead contrasts are void. |

### B — owed causal bridge (3)

| Card | Question and construction | Primary endpoint and closure |
|---|---|---|
| B01 | Does L255/A07b reproduce at a second checkpoint in the original artifact domain? | Congruent minus zero held-out-maker log score, with random and incongruent quiet; same frozen locus/dose and decode controls. |
| B02 | Does the selective causal-use signature reproduce in a second artifact domain? | Predeclared checkpoint × domain × steering interaction; a domain-specific result remains bounded rather than pooled away. |
| B03 | Is the effect coordinate- and information-specific rather than a generic activation or answer-bias effect? | Nearby/random coordinates, sign reversal, dose response, label permutation, and own-answer control. Failure narrows or closes the causal bridge. |

### J — joint reconstruction (5)

| Card | Question and construction | Primary endpoint and closure |
|---|---|---|
| J01 | Can each of process, episode goal, and standing preference be recovered when the other two are supplied? | Three known-answer rulers plus abstention on equifinal cases. |
| J02 | Does recurrent joint inference beat independent and three staged orders under identical evidence and compute? | Held-out maker-choice log score and calibration, followed by per-latent recovery. |
| J03 | Which latent becomes useful first as evidence stacks, and how often do provisional conclusions reverse? | Posterior trajectory, first useful prediction point, reversal rate, and overconfidence after contradiction. |
| J04 | When process, goal, and preference routes conflict, does explicitly opening a missing-goal/strategic-source hypothesis improve prediction? | Conflict-triggered search minus fixed hypothesis set, cost-matched; false-alarm cost in consistent worlds. |
| J05 | Does the inferred standing preference predict a new episode after process and current goal are changed? | Cross-episode prospective log score against habit, topic, style, and last-goal baselines. |

### A — appraisal, audience, and strategic communication (5)

| Card | Question and construction | Primary endpoint and closure |
|---|---|---|
| A01 | Can the reader separate its own response, intended audience effect, maker appraisal, and world/content support? | Four-way proper scores under owner swaps and matched surface intensity. |
| A02 | Can it distinguish derived honest-warning, sincere-fanatic, strategic-propagandist, and neutral regions without regime labels? | Factor posterior and held-out evidence-selection/correction prediction; abstain on surface collisions. |
| A03 | Does inverse-inverse planning explain audience-shaped artifacts better than ordinary inverse planning only when the maker actually models an audience? | Crossed maker mechanism × reader model interaction; same artifact quality and goal availability. |
| A04 | Do affect/source labeling and causal reappraisal improve source attribution or merely lower all influence? | Discrimination, criterion, calibration, and true/false selective uptake; blanket rejection fails. |
| A05 | Does trust alter uptake after reconstruction without rewriting content evidence or inferred communicative goal? | Factored posterior-to-policy bridge under reliable/unreliable histories and honest/deceptive episodes. |

### R — route reliability, ease, and conflict (4)

| Card | Question and construction | Primary endpoint and closure |
|---|---|---|
| R01 | Can the reader estimate which action, semantic, contextual, or forensic route is most predictive for this artifact? | Chosen-route information minus random/first/easiest, only after I04 divergence. |
| R02 | Does operational ease masquerade as route reliability? | Cross measured ease proxy with exact accuracy: equal-accuracy/different-ease and equal-ease/different-accuracy contrasts. |
| R03 | Do domain demonstrations change route competence and appropriate route use rather than merely confidence? | Demonstration × route diagnosticity interaction, plus calibration and a misleading-demonstration control. Call this familiarization, not human expertise. |
| R04 | Is a costly forensic observation selected only when its expected information gain justifies cost? | Proper prediction improvement per declared cost; compare exact, model-selected, random, and always-forensic policies. |

### P — process and physical traces (3)

| Card | Question and construction | Primary endpoint and closure |
|---|---|---|
| P01 | How much action-chain information is present in final geometry, unordered strokes, partial order, and a true prefix? | Conditional held-out next-stroke/action log score at each access level, beyond category and shape baselines. |
| P02 | Can the reader propose a valid production route when it cannot identify the historical route? | Enactability and exact-history scores on equifinal artifacts; uncertainty is required when history is unidentifiable. |
| P03 | Does measured domain route competence improve action-chain reconstruction selectively? | Competence × access-level interaction across two domains; no mirror-neuron or human embodiment claim. |

### F — interest and epistemic foraging (3)

| Card | Question and construction | Primary endpoint and closure |
|---|---|---|
| F01 | Are novelty, complexity, unexplained structure, reducible prediction error, and relevance distinguishable in the reader's evidence ranking? | Full crossed ranking and likelihoods for novel-explained, complex-compressible, random-unlearnable, structured-residual, trivial-known, and learnable-intermediate items. |
| F02 | Does learning-progress or expected-information-gain-per-cost predict useful selection better than raw surprise or novelty? | Realized held-out gain per cost, not stated interest; exact and simple baselines. |
| F03 | Can pursuit value remain separate from warrant when an attractive hoped-for explanation is weakly supported? | Selection behavior, posterior confidence, counter-bias prompt, and false-discovery rate under hope-congruent/hope-incongruent worlds. |

### C — frozen confirmation and closure (2)

| Card | Question and construction | Primary endpoint and closure |
|---|---|---|
| C01 | Does the strongest qualified bridge replicate on untouched makers, sources, and construction seeds? | One frozen estimand, rivals, and interval; no substituted endpoint. |
| C02 | Does the strongest qualified boundary or second effect replicate independently? | Prefer a discriminating boundary over a weak positive. At most two claims total enter confirmation. |

## 7. Analyses and promotion rules

### 7.1 Primary scores

Use log score, Brier score, calibration slope/error, selective risk–coverage, and held-out prediction. Use accuracy only as a secondary descriptive score. For route selection, report exact available information and realized information gain per cost. For process reconstruction, report valid enactability and historical correspondence separately.

Independent units are makers, source histories, construction worlds, or drawings—not prompts, tokens, posterior samples, or repeated observations. Use cluster-aware intervals or hierarchical bootstrap. Report conditional interactions before pooled averages whenever the treatment is expected to change sign.

### 7.2 Joint-reader criterion

The recurrent joint reader is supported only if it:

1. beats every same-evidence staged/independent comparator on a prospective score;
2. remains calibrated or abstains under equifinality;
3. improves because evidence passes between latents, demonstrated by an ablation;
4. transfers to the second domain or is explicitly reported as domain-bound;
5. survives label, surface, candidate-order, and free-form-rationale controls.

If supplying one latent improves another but end-to-end estimation fails, report a downstream method result, not a solved triple inference.

### 7.3 Communication criterion

Distinguishing a sincere fanatic from a strategic propagandist requires predicting a behavior on which their hidden states diverge: evidence selection under an opportunity to cherry-pick, willingness to correct, private/off-audience action, or cost paid when audience influence is impossible. Surface classification without such a counterfactual cannot pass.

### 7.4 Confirmation selection

At elapsed hour 20, freeze at most two candidates. A candidate must have passed construction, positive, surface, oracle, prediction, and calibration gates and have a fresh reserve capable of answering the same question. Selection order:

1. B01/B02 causal-use bridge if both checkpoints/domains form the selective signature;
2. J02/J05 joint prospective reconstruction;
3. A02/A03 owner/regime separation;
4. R02 route reliability beyond ease;
5. P01/P02 process information boundary;
6. F01/F02 foraging discriminator.

Do not promote a large retrospective label score over a smaller prospective effect.

## 8. Continuous 24-hour runtime contract

### 8.1 One clock, no early packets

The run clock begins when the discarded calibration pilot starts and ends exactly 24 elapsed hours later. Calibration, model loading, GPU-lock waits, repairs, inference, scoring, confirmation, and closure preparation occur inside this one window. A restart resumes the original deadline; it never earns a fresh 24 hours. The curator packet is generated only after the 24-hour execution window has closed.

The program writes internal checkpoints and machine-readable state continuously. It must not write or emit an early, daily, milestone, preview, interim, or partial curator packet. The only curator-facing report is:

`results/phase_2_4_stage_5/CURATOR_PACKET_FINAL.md`

generated after new experimental work stops at the deadline. Debug logs, manifests, and checkpoints are not curator packets and must not contain premature prose conclusions.

### 8.2 Allocation

| Work | Elapsed-window allocation |
|---|---:|
| integrity, construction gates, discarded calibration | 2.0 h |
| owed causal bridge | 3.0 h |
| joint reconstruction | 4.5 h |
| appraisal and strategic communication | 4.5 h |
| route reliability and process traces | 3.5 h |
| interest and foraging | 2.0 h |
| fresh confirmation, validation, and closure preparation | 4.5 h |
| **Total** | **24.0 h** |

These are scheduling allocations, not result quotas. Quiet and negative tracks retain their allocation until their prescribed severity or closure cells run.

### 8.3 Pilot and frozen expansion ladder

Pilot every heavy execution path on non-scientific lineages, measure end-to-end GPU-lock time, and freeze the smallest workload tier forecast to leave 4–5 hours for confirmation and closure. The workload lock must be written before discovery outputs are opened.

If the required 29-card spine is predicted to finish early, add useful independent work in this frozen order:

1. independent makers and source histories in both domains;
2. the second reader checkpoint across all promoted controls;
3. harder surface-matched regime collisions;
4. additional equifinal production histories and drawing categories;
5. additional conflict magnitudes and evidence-dose points;
6. transfer construction seeds.

Never fill time by sleeping, repeating identical seeds, duplicating one maker's rows, increasing token output without new information, or rerunning a saturated cell. If all scientifically admissible expansion is exhausted before 24 hours, emit `SHORT_RUN` with the actual time; do not claim the runtime contract was met.

At elapsed hour 20, stop opening exploratory branches, freeze confirmation candidates, and begin confirmation/closure. At hour 24, stop launching new model calls and safely checkpoint active work. Then validate the realized record and generate the one final packet. A partially completed card stays `DEFERRED` or `FAILED`; it is not silently marked complete.

### 8.4 Resource coexistence

Preserve the existing GPU lock and first-gear policy. CPU-side construction and scoring use at most two ordinary workers while Ghost V14 is active. Record elapsed, GPU-lock-held, CUDA-active, CPU, load, and wait time separately. The presence of a 24-hour wall clock is not proof of 24 GPU-hours.

## 9. Implementation and validation

Suggested paths:

- `soundingline/stage5.py` — schemas, constrained latent record, seed and path helpers;
- `runners/s5_lib.py` — shared model, scoring, route, and construction helpers;
- `runners/s5_run_i.py`, `s5_run_b.py`, `s5_run_j.py`, `s5_run_a.py`, `s5_run_r.py`, `s5_run_p.py`, `s5_run_f.py`, `s5_run_c.py`;
- `runners/run_stage5_program.py` — resumable scheduler with immutable deadline;
- `runners/validate_stage5_program.py` — read-only structural/result/runtime validator;
- `results/phase_2_4_stage_5/` — complete record.

Required root records:

- `RUN_CONTRACT.json`;
- `EXPECTED_CELLS.json`;
- `SOURCE_LINEAGES.json`;
- `CONSTRUCTION_IDENTITIES.json`;
- `ROUTE_INFORMATION.json`;
- `QUEUE_MANIFEST.json`;
- `WORKLOAD_LOCK.json`;
- `COVERAGE.json`;
- `COMPLETION.json`;
- `CONFIRMATION_REGISTRY.json`;
- `CLAIM_LEDGER.json`;
- `CURATOR_PACKET_FINAL.md`.

Per-card outputs include cases, raw model outputs or exact scored alternatives, metrics, verdict, hashes, charged compute, and the strongest surviving rival. Do not rely on ignored completion markers. Preserve raw generations where generation is used; candidate-likelihood paths preserve exact candidates and token-level scoring metadata.

### 9.1 Required tests

1. Parser fixtures cover negation, quotation, `unknown`, malformed output, evidence spans, and label permutations.
2. Removing one card, factor corner, domain, checkpoint, route, source regime, or control fails expected-cell validation.
3. Exact surface collisions remain collisions after prompt assembly and tokenization audit.
4. Every route-selection card fails closed when route information does not exceed the frozen divergence floor.
5. Enactability and historical-sequence metrics cannot alias.
6. Reader response, maker appraisal, intended audience effect, content support, communicative goal, reliability, and uptake cannot overwrite one another in schemas or aggregation.
7. Joint and staged readers receive the same evidence, priors, candidate set, and effective compute allowance.
8. L255 replication verifies intervention coordinates, dose, sign, hook removal, cached/full replay, and own-answer controls.
9. Confirmation access is rejected after any discovery read or shared ancestry.
10. Aggregation is invariant to row order and clusters at the true independent unit.
11. Deadline validation includes waits/restarts and rejects a short run labeled continuous 24-hour.
12. Reporting guards reject any curator packet path except `CURATOR_PACKET_FINAL.md` and reject its creation before closure.

Smoke every runner end-to-end on a scratch result root before the pilot. Then manually inspect assembled prompts, candidate mappings, hidden truth, surface matches, and one positive and null case per card. Smoke the scheduler through resume and final-only report suppression. Run existing tests, new focused tests, lock verification, design lint with the actual file path payload, and `git diff --check` before a proposed commit.

## 10. Outcome and claim ceilings

Execution states and scientific outcomes remain separate. Use the repository's existing vocabulary, including `INSTRUMENT_FAILED`, `VALID_NULL`, `COUNTEREVIDENCE`, `HETEROGENEOUS`, `INCONCLUSIVE`, and `VOID`.

Stage 5 may establish only:

- that specified small model readers use or fail to use a structured latent schema;
- that a measured internal direction causally changes held-out maker prediction at named checkpoints/domains;
- that controlled artifact information supports a bounded prospective inference;
- that one evidence route contains more usable information than named rivals;
- that some histories are not identifiable from a final artifact;
- that a constructed source-regime discriminator succeeds or fails under specified factors.

It cannot establish mirror neurons, a default-mode-network mechanism, human expertise, human affect transfer, propaganda immunity, persistent human values, or a general theory of empathy. “Sincere fanatic” and “strategic propagandist” name controlled latent combinations, not diagnoses of real people.

## 11. Required final packet

Write one packet after the 24-hour run. Begin with a plain-language account of how the project world changed, then one row per track containing question, observation, leading explanation, strongest rival, pursuit status, warrant status, and next decision. Report these seven answers before metrics:

1. Did L255's selective causal-use result survive a second checkpoint and domain?
2. Did joint reconstruction improve a hidden future choice beyond same-evidence staged readers?
3. Which latent became useful first, and did contradictions revise it appropriately?
4. Could the reader distinguish who owned an affective appraisal and why a maker tried to induce it?
5. Could it distinguish sincere alarm from strategic influence by predicting divergent behavior?
6. Did it choose reliable evidence routes rather than easy ones, and did forensic access buy enough information to justify its cost?
7. Did learning progress or structured reducible uncertainty explain useful foraging better than novelty, complexity, and raw error?

Then print:

> **STOP READING HERE**

The appendix contains full conditional matrices, intervals, gates, attacks, repairs, raw-output receipts, lineages, forecast versus actual runtime, deferred cells, and file hashes. Do not automatically prescribe Stage 6. Recommend a next stage only if a result survives prospective prediction, its strongest rival, and fresh confirmation.

## 12. Pre-mortem

Stage 5 is scientifically empty if:

1. a long free-form rationale is mistaken for a structured posterior;
2. the joint reader receives more facts or compute than staged readers;
3. a proximal-goal label is used as evidence for a standing value;
4. the reader's induced affect is relabeled as the maker's affect;
5. source distrust is credited as selective media literacy;
6. honest warning and propaganda differ in telltale vocabulary;
7. route fluency is called route accuracy without crossing them;
8. demonstrations are called human expertise;
9. a valid production path is called the historical path;
10. active selection is tested when probes are information-equivalent;
11. random noise is called interesting because it is unpredictable;
12. a pooled mean hides a planned sign reversal;
13. one maker's many prompts become many independent makers;
14. an oracle bypass is called end-to-end success;
15. duration is filled with duplicate work or sleep;
16. an interim result becomes an early curator packet;
17. a bounded model effect is reported as human or neural evidence.

## 13. Definition of done

Stage 5 is complete only when all 29 cards have valid dispositions; required domains, checkpoints, routes, regimes, controls, and independent-unit floors are accounted for; the L255 floor is met or explicitly closed; the joint/staged comparison is evidence- and compute-matched; owner/source variables remain factored; equifinal histories force uncertainty; route divergence is proven before selection; at most two untouched confirmations are opened; the execution window is one continuous 24 hours or honestly marked short; no early curator packet exists; and the final-only packet, claim ledger, coverage record, hashes, and clean-clone validation receipt agree.

If every instrument is valid and the results are negative, Stage 5 can be complete. If a striking result lacks its prospective endpoint, fair comparator, surface collision, or independent confirmation, Stage 5 is not complete.

---

[R01]: https://arxiv.org/abs/2402.17930 "Zhi-Xuan et al. (2024), Cooperative Language-Guided Inverse Planning"
[R02]: https://arxiv.org/abs/2402.10416 "Ying et al. (2024), Grounding Language about Belief in a Bayesian Theory-of-Mind"
[R03]: https://aclanthology.org/2025.tacl-1.30/ "Ying et al. (2025), Understanding Epistemic Language with a Language-augmented Bayesian Theory of Mind"
[R04]: https://pubmed.ncbi.nlm.nih.gov/37962526/ "Chandra et al. (2024), Storytelling as Inverse Inverse Planning"
[R05]: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0027926 "Anderson, Laurent, and Yantis (2011), Learned Value Magnifies Salience-Based Attentional Capture"
[R06]: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2014.00941/full "Sheridan and Reingold (2014), Expert–novice relevance selection in chess"
[R07]: https://pages.ucsd.edu/~pwinkielman/VonHecker-Hanel-Jin-Winkielman_Fluency-mental-models_CE-2023.pdf "von Hecker et al. (2023), Self-generated cognitive fluency"
[R08]: https://link.springer.com/article/10.3758/s13428-022-01879-4 "Hughes et al. (2023), Influence awareness and affect misattribution"
[R09]: https://www.frontiersin.org/journals/neuroscience/articles/10.3389/neuro.01.1.1.017.2007/full "Kaplan and Oudeyer (2007), Learning progress and intrinsic motivation"
[R10]: https://arxiv.org/abs/1604.06508 "Krishnan et al. (2016), HIRL: Hierarchical Inverse Reinforcement Learning for Long-Horizon Tasks with Delayed Rewards"
[R11]: https://proceedings.neurips.cc/paper_files/paper/2024/file/9bcd1fa0c05e5f25ba7a1261f1852e82-Paper-Conference.pdf "Multiple sub-optimal experts and reward ambiguity (NeurIPS 2024)"
[R12]: https://arxiv.org/abs/2502.15676 "Zhang et al. (2025/2026), AutoToM: Scaling Model-based Mental Inference via Automated Agent Modeling"
[R13]: https://arxiv.org/abs/2507.03682 "Gelpi, Xue, and Cunningham (2025), Towards Machine Theory of Mind with Large Language Model-Augmented Inverse Planning"
