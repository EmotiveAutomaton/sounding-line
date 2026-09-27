# Sounding Line Phase 2.4, Stage 2: Compatibility, Reconstruction, and Empathic Routes

**Status:** Long-form coding-agent work package

**Curator:** Abraham Haskins

**Prepared:** 2026-08-23

**Repository snapshot reviewed:** `899b359316a69f7302071f6864f085e221d86986`

**Suggested repository destination:** `docs/design/PHASE_2_4_STAGE_2_CONTEXT.md`

**Inherits:** `PHASE_2_4_CONTEXT.md`, `PHASE_2_4_EXPLORATION_ADDENDUM.md`, `PHASE_2_4_REGISTRY.md`, `PHASE_2_4_ROOT_MAP.md`, `docs/method/LESSONS.md`, and the five-file theory contract.

This package opens Stage 2. It does not edit or supersede the theory documents. It turns the curator's latest walkthrough into a sustained discovery forest with explicit promotion, closure, and daily continuation rules.

## 0. Executive decision

**Continue. Do not retreat into a general theoretical reset.** Stage 1 produced enough structured promise to justify a larger engineering search, and too little warrant to justify a strong explanatory claim.

The reason to continue is the conjunction, not any one result:

- exact and sibling Qwen readers recovered Qwen-maker goals better than cross-family readers;
- the advantage was graded and was not explained by parameter count inside the tested matrix;
- the gradient survived one goal-preserving paraphrase pass;
- the positive reader interface works on a known-answer realized-choice anchor;
- the project now holds CoAuthor action histories and ScholaWrite revision histories for prospective work;
- an emotion-word-free affect decoding grain appeared at one functioning seed, although the causal ruler failed itself.

The reason to withhold belief is equally specific:

- every maker in the similarity result was Qwen-family;
- the paraphraser used to erase Qwen fingerprints was itself Qwen-family;
- the paraphrase pass cut the exact-checkpoint advantage roughly in half;
- no validated prospective reader exists yet;
- the affect result has no stable locus, causal sign pair, or cross-seed ruler;
- no AI-only result establishes human invertibility.

The current project state is therefore:

> **Pursuit rises. Warrant moves only slightly. The next task is to turn compatibility from a suggestive family pattern into a process-predictive mechanism, or let the stronger controls dissolve it.**

## 1. What Stage 1 actually found

### 1.1 Similarity root

G172 found exact-maker and sibling-reader advantages over cross-family readers on mechanically verified entity-order goals. Exact minus cross was `+0.03536` per-token margin units and sibling minus cross was `+0.02463`, both at the 20,000-permutation floor. Every gate-passing Qwen reader out-margined every gate-passing cross-family reader, including the larger Pythia reader.

This is analogue evidence for a compatibility effect. It does not yet identify compatibility as shared generative organization.

### 1.2 Fingerprint-destruction scout

E24-S02 retained the same ordering after accepted paraphrase on 115 of 123 artifacts:

| contrast | original | paraphrased | directional change |
|---|---:|---:|---:|
| exact minus cross | 0.03536 | 0.01645 | attenuated by about 53 percent |
| sibling minus cross | 0.02463 | 0.02091 | largely retained |

The scout is promising for pursuit because the family relation did not vanish. It adds little warrant because the paraphraser was Qwen-family. It may have preserved Qwen dialect, rewritten every artifact into a fresh Qwen dialect, or selectively erased checkpoint-specific residue while retaining family residue. The attenuation is itself useful. Surface cues probably contributed to the exact advantage.

### 1.3 Capacity scout

E24-S05 found complete family separation with only a weak monotonic relationship between parameter count and margin. This makes raw capacity a poor account of the current matrix. It does not address tokenizer overlap, training-data overlap, instruction tuning, family-specific likelihood calibration, or artifact dialect.

### 1.4 Affect root

G174 is `INSTRUMENT-FAIL`. Its dev-selected block flipped from 27 to 1 across seeds, and the block-1 intervention changed neutral-text likelihood by 2.55 times. At the functioning seed, scrubbed six-way affect decoding was 0.30 against 0.167 chance, above the shuffle null and with the lexical baseline exactly at chance. No causal sign pair appeared.

The surviving grain justifies a rebuilt ruler. It does not support an affective prior, a Panksepp mapping, or a process-inversion gain.

### 1.5 Human-process root

G177 validated the non-generative conditional reader on realized revision choices at 0.78 top-1 against a 0.25 floor. ScholaWrite mechanical prospective floors are 0.04 to 0.08 macro-F1. The prompted reader's descriptive values remain unusable because its known-answer validation had one decidable case and missed it. CoAuthor imported 1,447 sessions and roughly 2.7 million logged events.

This gives Stage 2 a positive ruler, a hard prospective target, and a rich action record. It does not yet give Stage 2 a validated human-process reader.

## 2. Theoretical contract for Stage 2

### 2.1 The object being reconstructed

Stage 2 treats the maker as inducing a conditional distribution over observable decisions:

\[
\pi_M(a_t \mid g_t, c_t, k_M, h_{<t})
\]

where:

- `a_t` is an observable choice, action, revision, acceptance, rejection, or next move;
- `g_t` is the currently active goal, including the attended primary goal;
- `c_t` is situation, audience, available tools, and constraints;
- `k_M` is the maker's deployed expertise and compiled habits;
- `h_<t` is the preceding interaction and artifact history.

This is an operational object, not the full psychological ontology. It is useful because it makes expertise visible through repeated conditional choices instead of asking a reader to narrate an unverifiable rationale.

### 2.2 Four products that must remain separate

Every instrument reports these separately where the data permit:

1. **Viewer-coherent reconstruction:** the best maker model this reader can construct.
2. **Reader-enactable route:** a route the reader could use to reproduce or learn from the artifact.
3. **Historical correspondence:** a posterior over the process the maker likely used under the maker's actual context.
4. **Value-candidate structure:** later, cross-context regularities in preferences and tradeoffs.

A reader-enactable route alone is learning from the artifact. It is not full inversion. Historical context remains informative even after successful recreation. Value inference remains a shadow measurement in this stage.

### 2.3 Primary goal stays inside the model

The maker often has privileged memory of the attended primary goal. A reader can still infer it, and experts can sometimes do so well. Stage 2 therefore scores the primary goal separately but never removes it from the joint process model. Auxiliary goals, habits, tools, and context condition how that goal becomes action.

### 2.4 Compatibility is graded

A reader uses its own organization as a cheap prior because some makers are similar enough for self-based reconstruction to work. Define a deliberately broad compatibility variable:

\[
\kappa(R,M,C) = \text{fit between reader, maker, and context}
\]

For models, Stage 2 can manipulate weight identity, training lineage, architecture, tokenizer, tuning history, capacity, action grammar, and tool knowledge. For humans, compatibility may additionally include embodiment, affective organization, culture, domain expertise, and personal history. Those human dimensions are not established by the model analogue.

A schematic reader posterior is:

\[
q_R(z_M \mid O,C) \propto p_R(O \mid z_M,C)\,\Pi_R(z_M;\kappa)
\]

where `z_M` is a candidate maker state or process history. The equation is a search scaffold. Stage 2 should estimate correction and prediction behavior, not fit a grand scalar called compatibility.

### 2.5 Empathic routing is an interacting sequence

Do not implement a symmetric fast/slow by affective/cognitive table. The current research and curator model jointly support a more useful provisional sequence:

1. self-structure and target cues initialize an assumed-similarity prior;
2. sensorimotor, affective, action, and semantic cues constrain candidate states;
3. self-other separation prevents the self-based guess from being mistaken for the target;
4. context and explicit mentalizing correct the target model;
5. prediction, feedback, and further evidence recursively update it;
6. the act of running the target model may also update the reader.

The components may operate in parallel and recurrently. Model experiments name their manipulations directly, such as low versus high compute, self-choice priming, target-evidence dose, or context conflict. They do not label an LLM behavior as affective empathy or cognitive empathy.

Research basis:

- Fast empathic judgments are associated more with assumed similarity, while direct target accuracy is associated with longer response times in [Sened et al.](https://pubmed.ncbi.nlm.nih.gov/36042967/).
- Self-reflection contributes to mentalizing especially for similar others in [Mitchell, Banaji, and Macrae](https://pubmed.ncbi.nlm.nih.gov/16197685/).
- Affective and cognitive empathy can dissociate while remaining interactive, as reflected in [Shamay-Tsoory, Aharon-Peretz, and Perry](https://pubmed.ncbi.nlm.nih.gov/18971202/) and [Zaki and Ochsner](https://www.nature.com/articles/nn.3085).
- [Bird and Viding](https://pubmed.ncbi.nlm.nih.gov/25454356/) explicitly combine cue classification, situation understanding, theory of mind, affective representation, and self-other tagging.
- Mirror-like sensorimotor mapping can supply an inside route, but it is not a sufficient theory of understanding. Compare [Rizzolatti and Sinigaglia](https://www.nature.com/articles/nrn.2016.135), [Hickok](https://pubmed.ncbi.nlm.nih.gov/19199415/), and the associative-learning account of [Cook et al.](https://doi.org/10.1017/S0140525X13000903).

## 3. Stage 2 operating method

### 3.1 Two ledgers per branch

Every branch writes two independent updates.

**Pursuit ledger:** Does this pattern open a mechanism, suggest a useful capability, or increase the value of a neighboring test?

**Warrant ledger:** What does the result establish after controls, rivals, power, and scope?

Allowed discovery statuses remain `PROMISING`, `QUIET`, `RIVAL-FAVORED`, `INSTRUMENT-FAILED`, and `PROMOTE-TO-CONFIRMATION`. Add a separate pursuit status from `OPENED`, `PROMISING`, `STALLED`, `EXHAUSTED`, or `PROMOTE`.

### 3.2 Confirmation firewall

The existing firewall remains binding:

- allocate confirmation cases before scout inspection;
- group every artifact lineage, author, session, prompt family, and transformation family on one side;
- freeze selected readers, prompts, bases, ranks, loci, strengths, and thresholds before confirmation;
- burn any confirmation split opened during debugging;
- preserve failed and quiet branches in the registry;
- only the G-series confirmatory trunk may use `SUPPORTED`, `REJECTED`, or public flight language.

### 3.3 Known-answer first

Every new reader, source detector, route classifier, causal intervention, and adjudicator validates on a planted or mechanically decidable subset before touching the unknown target. Every gate header includes the `DESIGN CHECK` block required by `docs/method/LESSONS.md`, with behavior under both null and alternative and the failure direction stated.

### 3.4 Primary outcomes

Prefer:

- paired proper-score differences;
- multiclass log score or Brier score;
- calibration slope and expected calibration error;
- held-out next-action accuracy or fixed-label macro-F1;
- abstention quality on equifinal cases;
- paired sign-flip or hierarchical bootstrap intervals;
- cross-context transfer measured on untouched tasks.

Top-1 can remain descriptive. Confidence, answer rate, generated rationale quality, and raw likelihood across tokenizers never carry a result alone.

### 3.5 Sustained execution

This is not another three-study leg. Maintain a rolling one-ordinary-local-day queue and refill it automatically from the authorized trees while:

- a branch has an unresolved discriminator;
- its known-answer ruler passes;
- its one-repair budget is not exhausted;
- it has not consumed two queue-days without a discriminating pattern;
- no paid service, human recruitment, external contact, or protected data action is required.

Write a cold daily map after each queue-day. Continue for up to six ordinary local queue-days before a mandatory theory synthesis. An earlier pause occurs only when a flight candidate appears, two major roots collide theoretically, or the available branches all close.

## 4. Forest overview

| Tree | Central question | Immediate product | Formal destination |
|---|---|---|---|
| **S: compatibility versus fingerprint** | What aspect of reader-maker relatedness produces the G172 gradient? | independently erased, multi-maker inversion matrix | G173, G180 |
| **P: conditional process reconstruction** | Can a reader recover a maker's decision policy well enough to predict held-out choices? | controlled process ecology and prospective ruler | G178, G180 |
| **E: empathic route decomposition** | How do self-based priors, target evidence, correction, and uptake interact? | projection-correction curves | future human bridge, G180 appendix |
| **A: affective constraint rebuild** | Is there a stable, selective, causal affect-related basis that improves process recovery? | validated ruler and basis tournament | G175, G176, G179 |
| **H: recorded human process** | Which goals and action events are recoverable from real writing histories? | CoAuthor and ScholaWrite prospective trees | G178, product phase |
| **V: values shadow** | Does recovered process structure expose cross-context preference invariants? | controlled value-candidate posterior | later phase only |
| **X: adversarial boundaries** | Does each promising mechanism survive projection, equifinality, false context, and flattening? | mechanism-specific failure map | every promotion |

The trees share data interfaces and controls. They do not share confirmation cases.

## 5. Tree S: compatibility versus fingerprint

### S0. Standing result and live rival

The G172 gradient and S02 survival promote this tree. The standing rival is family dialect, broadened to include tokenizer familiarity, likelihood calibration, training-corpus overlap, paraphraser imprint, and instruction-tuning habits.

### S1. Independent erasure tournament

Run the current matrix after several transformations whose failure modes differ.

#### S1a. Mechanical normalization

- canonical punctuation, quotation, whitespace, bullets, and casing;
- normalize numbers and named-entity formatting without changing roles;
- preserve sentence order and re-run mechanical realization checks.

This removes cheap formatting residue and should not be oversold as semantic erasure.

#### S1b. Rule-constrained syntactic recast

- split or combine clauses by fixed rules;
- convert active to passive where truth conditions permit;
- normalize discourse connectives;
- preserve target order and avoidance constraints.

#### S1c. Non-Qwen paraphraser

Use at least one instruction-capable local family unrelated to Qwen. Match acceptance rate, length, and semantic fidelity to S02. If no suitable family fits the 12GB card, quantize or run a smaller instruct family. Do not substitute a base model that cannot meet the accept-time gate.

#### S1d. Crossed paraphraser imprint

Paraphrase the same source artifacts separately with Qwen and the unrelated family. Cross reader relation to both original maker and paraphraser. This yields three distinguishable signatures:

- advantage tracks original maker family;
- advantage tracks paraphraser family;
- advantage collapses under both.

#### S1e. Two-hop representation recast

Extract a structured fact table with mechanically checked roles, then regenerate from that table using a neutral or crossed-family generator. Keep the source artifact hidden from the regenerator. This is the strongest local eraser, although regeneration can introduce its own family signature.

#### S1f. Optional translation round trip

Only if a locally available translation model passes a known-answer semantic gate. Use two pivot languages and treat translation family as another imprint factor. Do not use uncontrolled web translation.

**Measurements for S1:** original-maker source detection, paraphraser-family detection, target realization, length and compression, candidate margin, calibration, and per-artifact paired changes.

**Route:**

- If the gradient survives two unrelated erasers while source-family detection falls to its held-out floor, promote shared-compatibility pursuit.
- If it follows the paraphraser, classify the effect as output-dialect familiarity.
- If exact residue dies while sibling residue survives, treat checkpoint memorability and family compatibility as separate terms.
- If every eraser kills the gradient, close shared-organization at final-artifact grain and retain the fingerprint result.

### S2. Family-source detector baseline

Build a cheap, validated source-family classifier over held-out generation topics using character n-grams, function words, tokenization statistics, and shallow embeddings. It has two jobs:

1. verify whether each eraser actually destroys known family information;
2. test whether inversion advantage remains after matching or residualizing on source-detection confidence.

Do not claim that classifier failure proves fingerprints absent. The useful result is the converse: strong source detection provides a measured shortcut.

### S3. Second-maker-family matrix

Stage 1's largest limitation is one maker family. Build the same verified goal corpus with two instruction-capable makers from a second family.

Requirements:

- keep the goal task and candidate construction fixed;
- verify realization inside the accept loop;
- predeclare a retirement rule for low-yield makers;
- use exact, sibling, and cross readers where local checkpoints exist;
- include capacity-matched and stronger cross-family readers;
- derive shuffle-gate bands at their actual probe count.

The diagnostic pattern is a **crossed reversal**: Qwen relatives lead on Qwen artifacts and second-family relatives lead on second-family artifacts. A universal Qwen-reader advantage is reader quality. A universal source-family advantage after erasure is stronger compatibility evidence.

### S4. Process-resolution ladder

Run relatedness contrasts at distinct targets:

1. exact prompt wording;
2. assigned primary goal;
3. realized choice or constraint;
4. auxiliary preference in a controlled construction;
5. next observable action;
6. route family where process history exists.

Literal prompt recovery is a surface-sensitive lower rung. Executed choice and held-out next action are the main Stage 2 rungs. Route identity must abstain when the final artifact is equifinal.

### S5. Lineage decomposition

Where checkpoints allow, cross:

- exact weights;
- base and instruction-tuned variants;
- sizes within one family;
- same architecture with different training lineage;
- different architecture with tokenizer overlap;
- different tokenizer with approximate training overlap;
- controlled adapters from one frozen base.

Fit relation factors only after the full matrix is observed. Do not collapse them into one post-hoc similarity score. The objective is to learn which axes deserve later manipulation.

### S6. Controlled sibling creation

Train several small adapters from one frozen base on distinct, mechanically defined decision policies. Hold vocabulary and task topics as constant as practical. Test whether readers best invert the sibling with the closest production policy rather than any sibling sharing the base.

This is the cleanest local separation between shared substrate and learned expertise. Keep adapter training data separate from reader scoring data.

### S7. Geometry linkage

Only after S1 through S4 produce a stable matrix:

- compute null-tested representational correspondence on a large neutral and process-matched corpus;
- use CKA only relative to correspondence nulls;
- add orthogonal Procrustes and regularized cross-model maps;
- predict held-out pairwise inversion margins after capacity, tokenizer, source-detection, and paraphraser factors;
- freeze the best descriptive map before any causal test.

### S8. Causal direction transfer

Map a maker-side goal or process direction into a reader. Amplify and ablate it during artifact tokens only. Compare equal-norm random, topic, syntax, and generic-semantic directions. Require:

- sign-paired movement on the true candidate score;
- quiet unrelated capability checks;
- no comparable decoy gain;
- replication on a second goal family.

Descriptive geometry without selective causal movement remains an alignment observation.

### S9. Tree-S promotion conjunction

Promote to a fresh confirmatory card only if at least three of four hold:

1. crossed second-family reversal;
2. survival under two unrelated erasers with source detection near floor;
3. relation predicts held-out process or next-action recovery, not only prompt wording;
4. null-tested geometry predicts the pair matrix or a mapped intervention moves it selectively.

One strong item can keep pursuit open. It cannot alone promote the mechanism.

## 6. Tree P: conditional process reconstruction

Tree P is the center of Stage 2. It turns the theory's expertise picture into a system-identification problem rather than a request for psychological prose.

### P0. Build a controlled process ecology

Create repeated production episodes in which the same makers act under crossed conditions. Each episode exposes observable decisions through drafts, edits, tool selections, acceptances, rejections, or structured action choices.

Factor at least:

- **primary goal:** explain, persuade, warn, reconcile, compress, or another mechanically verifiable task family;
- **auxiliary preference:** brevity, elegance, caution, status protection, accessibility, novelty, or source conservatism;
- **context:** audience, time pressure, tool availability, evidence quality, and institutional voice;
- **history:** prior examples, an adapter-imposed habit, or a preceding sequence that changes what is locally easy;
- **domain:** at least two content domains with the same decision ontology.

The first version should use a small factorial with strong verification rather than a huge unverified generator corpus. Assigned goals are not ground truth until realization passes.

### P1. Observable decision vocabulary

Define actions before generation. Possible actions include:

- choose one of several evidence items;
- order two claims;
- include or omit a caveat;
- select a tool;
- accept, edit, or reject a suggestion;
- retain or later remove a phrase;
- spend an additional revision step;
- address or route around an objection;
- choose one of several next edits.

Every action needs a declared opportunity denominator. Do not count words or style marks as equal decisions.

### P2. Primary-goal recovery

Recover the active primary goal from partial and final process states. Cross:

- primary goal supplied to the reader;
- primary goal withheld and inferred;
- true context supplied;
- context withheld;
- false but plausible context supplied.

Report primary-goal accuracy separately, then propagate its uncertainty into auxiliary-goal and next-action predictions. Do not silently score downstream targets as though the goal were known.

### P3. Auxiliary-goal distribution

Use controlled conflicts where the same primary goal permits several auxiliary choices. Fit the reader's posterior over auxiliary preferences from early episodes, then predict held-out choices under new opportunities.

A valid auxiliary-goal instrument must beat:

- global action frequency;
- topic and lexical features;
- the primary goal alone;
- a recent-action Markov model;
- maker identity without process observations.

The important result is conditional prediction. A fluent label such as "status protection" is optional and never the ruler.

### P4. Expertise as deformation of the possible path

Probe expertise by changing which routes are available:

- remove a familiar tool;
- add a tool the maker has demonstrated skill with;
- transfer the same goal to a neighboring domain;
- introduce a case where a learned habit is locally wrong;
- introduce a shortcut that a novice takes and an expert avoids;
- change audience while holding factual task constant.

Estimate how the maker's choice distribution deforms. A reader has recovered useful expertise when it predicts both ordinary choices and the pattern of failure or adaptation under these perturbations.

### P5. Compiled habit versus episode-level attention

Construct episodes where the same observable choice can arise from:

- an explicitly attended instruction;
- a repeated learned policy;
- a default imposed by the tool;
- a late edit after noticing an opportunity.

Use the process record to define origin. Test whether artifact-only, paired-delta, and prospective readers can separate the cases. The expected result can be an equivalence class. The final artifact may not identify the origin.

### P6. Mistake and anomaly response tree

Plant or observe anomalies and separate:

1. no perceptual access;
2. failure to notice;
3. notice and repair;
4. notice and conceal;
5. notice and retain for convenience or another goal;
6. integrate and exploit downstream;
7. unknown.

Score origin, recognition, response, and later integration separately. Later order can show integration without proving planned origin. Treat repeated unaddressed deviations as evidence that the reader's goal model may be wrong, not automatic evidence of incompetence.

### P7. Counterfactual policy recovery

After observing a maker in several contexts, ask the reader to predict choices in held-out combinations. Examples:

- same goal, different tool;
- same tool, different audience;
- same auxiliary preference, new topic;
- primary and auxiliary goals placed in conflict;
- a path made easier or harder by an upstream decision.

Score the full candidate distribution. This is the closest operational test of whether the reader recovered the maker's local policy rather than memorized artifacts.

### P8. Reenactment versus historical correspondence

Build matched cases with two routes:

- both can produce the observed artifact;
- one is easy for the reader to reenact;
- the other is the recorded maker route;
- context or tool records discriminate them.

Run artifact-only, context-aware, and process-aware interfaces. A reader that selects its own route until maker-specific evidence arrives is behaving as the theory predicts. Success means calibrated correction, not immediate historical omniscience.

### P9. Conditional-distribution fit

For each maker, reveal a growing sample of episodes and fit a reader-side predictive model. Plot:

- held-out log score versus observations;
- calibration versus observations;
- primary-goal recovery versus observations;
- cross-context transfer;
- unexplained deviations;
- source-family or reader-maker relation.

This learning curve is a candidate quantitative vertex into expertise. It estimates how quickly a reader can approximate a maker's decision distribution and where the approximation stops improving.

### P10. Process compression test

Compare three representations of the observed episodes:

- raw action history;
- a compact inferred policy state;
- a surface summary with the same token budget.

The compact state earns standing only if it predicts held-out actions at least as well as raw history and transfers better than the surface summary. This guards against a new vocabulary that merely redescribes the training examples.

### P11. Tree-P promotion conjunction

Promote when a frozen reader:

- predicts held-out next actions above mechanical and Markov baselines;
- transfers across topic or tool perturbation;
- improves with maker-specific evidence rather than confidence alone;
- corrects away from its own policy when target evidence conflicts;
- abstains or widens its posterior on equifinal histories;
- retains a relation-sensitive advantage after surface controls.

## 7. Tree E: empathic route decomposition

Tree E studies functional inference routes. It does not claim that an LLM feels empathy or instantiates a human neural system.

### E0. Core operational objects

For each reader and target maker, obtain:

- `S_R`: the reader's own choice distribution on the same task;
- `T_M`: the target maker's observed or ground-truth choice distribution;
- `Q_0`: the reader's target estimate before maker-specific evidence;
- `Q_d`: the target estimate after evidence dose `d`;
- `Q_c`: the estimate after explicit context or deliberation;
- `S_R'`: the reader's own choice distribution after modeling the target.

This supports distinct measures:

- **assumed similarity:** closeness of `Q_0` to `S_R`;
- **direct target accuracy:** closeness of `Q_d` to `T_M` controlling for `S_R`;
- **correction slope:** movement from `Q_0` toward `T_M` as evidence grows;
- **self-other separation:** ability to report `S_R` and `Q_d` accurately when they conflict;
- **uptake:** movement from `S_R` to `S_R'` after target modeling.

### E1. Self-proxy baseline

Before showing target episodes, ask the reader to predict the target under only family, role, or minimal context. Separately measure the reader's own policy. Test whether the target estimate defaults toward self and whether that prior is stronger for exact, sibling, or familiar targets.

### E2. Similarity-by-evidence factorial

Cross reader-maker compatibility with evidence dose. A useful compatibility prior should:

- improve early prediction for truly similar targets;
- hurt early prediction for dissimilar targets;
- yield to sufficient target evidence;
- improve sample efficiency without preventing correction.

An effect that persists unchanged after decisive contradictory evidence is rigidity or fingerprint obedience, not calibrated empathy-like inference.

### E3. Target-conflict cases

Choose tasks where reader and maker policies disagree strongly. Verify the conflict before the reader sees target evidence. Then test whether the reader:

- projects its own choice;
- represents both distributions;
- corrects toward the maker;
- becomes underconfident or overconfident;
- changes its own later choice.

### E4. Evidence-dose curve

Reveal maker episodes in ordered doses such as 0, 1, 2, 4, 8, and 16. Repeat with random order and with maximally informative active probes. Compare passive exposure with evidence selected to distinguish candidate policies.

This is the direct test of whether context probing and epistemic foraging improve inversion rather than merely adding text.

### E5. Cue-channel ablation

Present matched information through:

- final artifact only;
- action sequence only;
- outcome only;
- semantic description of the action sequence;
- tool and context card;
- affective or evaluative cues where available;
- full combined record.

Measure unique and interactive contribution. Do not identify action-sequence benefit with mirror neurons. It is evidence that process-shaped cues add information beyond semantic summary.

### E6. Cue-order test

Cross whether self-policy activation, target actions, context, and outcomes arrive first. If self-based simulation is an initializer, early self activation may help on similar targets and hinder on dissimilar targets until correction. If order does not matter, a staged route account loses value.

### E7. Compute and deliberation surface

Compare fixed low, medium, and high inference budgets, plus a non-generative proper-score reader. Record latency or token budget, but call the manipulation compute budget. Test whether additional compute:

- increases direct target accuracy;
- reduces assumed-similarity bias;
- improves calibration;
- increases rationalization without prediction;
- changes uptake.

This can reveal a fast/slow association. It cannot by itself label the routes affective and cognitive.

### E8. Self-other retention test

After predicting the target, ask the reader again for its own choice under the original framing and for the target's choice. Randomize query order. A calibrated reader should keep both distributions accessible. Collapse toward one side indicates egocentric or altercentric contamination.

### E9. Feedback and correction

Give true feedback on the maker's next action after each prediction. Compare improvement with no feedback and false feedback. The useful signature is target-specific correction that transfers to held-out contexts, not obedience to the latest label.

### E10. False-context conflict

Cross strong behavioral evidence with true, false, and missing context. Measure how much each channel moves the posterior. G167 already shows that context can behave like an instruction. Tree E asks whether accumulating target evidence can eventually overrule it.

### E11. Affect congruence scout

Where controlled affective states exist, cross reader-native affect framing with target affect cues as congruent or incongruent. Measure projection, correction, and self-other separation. This is a behavioral scout for whether affective compatibility changes the prior. It is not evidence about subcortical machinery.

### E12. Action-grammar compatibility

Give some readers prior experience with the maker's tools and action grammar while others receive a semantic description of equal information. If enacted or trained compatibility improves early inversion and prospective prediction, shared process organization gains a stronger functional analogue.

### E13. Uptake and indoctrination analogue

Measure `S_R` before and after target modeling. Cross:

- high and low inferred value similarity;
- shallow and deep process reconstruction;
- accurate and false context;
- target policies that are useful, neutral, or locally harmful;
- explicit instruction to resist uptake.

The target is a change in the reader's later decisions, not verbal agreement. This branch studies the curator's proposal that fast self-based reconstruction can update the reader before slower value gating finishes.

### E14. Productive projection control

Include cases where the reader's route is historically wrong but produces the correct artifact or solves the problem better. Score task utility and historical correspondence independently. This prevents useful learning from being mislabeled as accurate inversion and prevents historical error from hiding productive projection.

### E15. Human bridge packet, prepare only

Prepare a later preregistered packet with bounded action tasks, known target policies, expertise strata, self-policy measurement, evidence doses, and prospective choices. Do not recruit or launch without separate authorization. Subjective reports from the curator or close relations can generate hypotheses but do not populate the result table.

### E16. Tree-E promotion pattern

The route account becomes materially interesting if:

- self-proxy bias is graded by true compatibility;
- it improves sample efficiency for similar targets and creates predictable error for dissimilar targets;
- target evidence corrects the estimate with calibrated dose response;
- action or affective cues add information beyond semantic summaries;
- readers preserve self-other distinction;
- deeper accurate reconstruction predicts uptake, with later value similarity moderating that uptake.

Any subset can guide pursuit. A human-mechanism claim waits for the prepared human bridge.

## 8. Tree A: affective constraint rebuild

### A0. Rebuild rule

Do not repair G174 by lowering the intervention dose alone. Its failure was locus selection and dev power. Open a fresh discovery ruler with a larger stimulus bank and a locus rule frozen independently of the headline effect.

### A1. Larger, crossed stimulus bank

Build at least an order-larger bank crossing:

- affect category or dimension;
- topic;
- actor role;
- explicit versus scrubbed wording;
- situation versus lexical label;
- congruent and incongruent context;
- neutral hard negatives.

Human-labelled and model-synthetic examples remain distinct source twins.

### A2. Stable computational locus

Compare predeclared alternatives on development data:

- fixed aligned-middle event;
- fixed late integration event;
- multi-event average;
- cross-seed consensus event;
- low-rank subspace stable across a band of events.

Require locus stability across at least three seeds before causal interpretation. Block 1 remains a known degenerate edge and cannot win by development accuracy alone.

### A3. Basis and effective-rank tournament

Compare:

- valence and arousal, with dominance separate;
- Panksepp-inspired seven-system language contrasts;
- GoEmotions human labels;
- human-rated affective similarity geometry;
- model-synthetic source twins;
- nested ranks such as 1, 2, 4, 7, 12, 18, 27, and 32;
- equal-rank topic, syntax, persona, generic semantic, shuffled-label, and random controls.

Twenty-seven is a soft search endpoint. It is neither a predicted emotion count nor a neurological upper bound.

Report stability and causal effect per degree of freedom. Prefer plateaus over winner-take-all rank selection.

### A4. Abstract transfer gates

Before causality, require:

- emotion-word-free decoding;
- actor-role transfer;
- topic transfer;
- human-label to natural-situation transfer;
- semantic-neighbor hard negatives;
- source-twin comparison.

### A5. Causal dose surface

At each stable locus and basis:

- amplify and ablate;
- test at least three strengths around zero;
- intervene only on declared token spans;
- run neutral capability, syntax, topic, and random-basis controls;
- require predicted sign on an affect-sensitive known-answer task;
- record off-target likelihood and calibration.

### A6. Mechanistic localization scout

Use PyTorch hooks already validated in the repository to add:

- activation patching between matched affective situations;
- causal tracing over token positions;
- cross-event mediation estimates;
- basis removal followed by reconstruction from residual activation;
- alignment of a stable basis across model family.

This searches for a functional pathway. Do not describe components as a copied midbrain.

### A7. Empathic-route integration

Only after A4 and A5 pass, intervene during distinct E-tree moments:

- before target evidence;
- during target-cue integration;
- after explicit context;
- during the reader's later own decision.

Test whether the basis changes assumed similarity, target correction, self-other separation, or uptake selectively. Timing may reveal whether the basis acts more like a prior, evidence channel, or decision bias.

### A8. Process-recovery integration

Run the frozen basis on P-tree and H-tree targets. The required outcome is improved proper score on recorded decisions or next actions, with generic semantic controls quiet. Confidence, emotional wording, and refusal changes are side effects.

### A9. Learned deformation

Only after a fixed basis yields selective improvement, train a small adapter on affect labels or similarity judgments without process labels. Compare equal-capacity generic, random-label, and ordinary task adapters. Freeze before process confirmation.

### A10. Tree-A closure and promotion

Close the tested affect-specific mechanism if two well-powered basis families behave like matched generic semantics or if causal movement never exceeds capability disturbance after one rebuild. Promote only after stable abstract decoding, sign-paired causality, generic-control selectivity, process-score improvement, and a fresh-seed replication.

## 9. Tree H: recorded human process

Tree H provides the historical-correspondence anchor. It should be methodologically harder than the model ecology because labels describe real writing actions imperfectly.

### H0. Interface ladder

Every target reports separately under:

1. final artifact only;
2. paired delta;
3. partial history with the next action withheld;
4. artifact plus true context and tool record;
5. full process-aware ceiling.

The process-aware ceiling decides whether the label is recoverable from the available record. An artifact-only failure under a passing ceiling maps an information boundary.

### H1. Powered ScholaWrite validation

Repair the unpowered G177 reader gate before interpreting reader outputs.

- stratify validation sampling toward mechanically decidable edits;
- fix the full 15-label set in every macro-F1;
- derive the validation interval and pass band at the actual sample size;
- validate evidence spans where a model adjudicator is used;
- run the mechanical majority, transition, and change-feature baselines first;
- preserve leave-one-project-out grouping.

If a validated prompted reader cannot beat the mechanical floors, keep the result as a hard prospective boundary and move to non-generative or trained baselines.

### H2. CoAuthor action ontology

From the imported logs, define separate events:

- suggestion requested;
- suggestion offered;
- suggestion inspected where observable;
- accepted unchanged;
- accepted then edited;
- rejected;
- retained to a later checkpoint;
- later removed;
- followed by a new request or manual revision.

Do not equate acceptance with agreement or rejection with recognition. "Ignored" requires an opportunity and an observable non-response; otherwise use unknown.

### H3. CoAuthor prospective tree

At each eligible state, predict:

- accept, edit, reject, or no adoption;
- retention versus later removal;
- next request category;
- next manual edit family;
- time or event count to next intervention.

Baselines include global rates, user random effect, recent action, suggestion length and quality proxies, edit-distance features, and session position. Split by user and session lineage.

### H4. Ratification and integration

Use the action history to distinguish origin from ratification:

- model-supplied content accepted by the human;
- human content preserved through model editing;
- accepted content later integrated into dependent choices;
- content retained without evidence of attention.

The final artifact may not reveal who originated or noticed a contribution. When the process record does, use it to test the artifact reader's calibration and abstention.

### H5. Primary goal inside real histories

Use only datasets or episodes with a defensible primary-goal proxy, such as an explicit request, task instruction, revision intention, or author annotation. Score:

- goal supplied versus inferred;
- goal stability versus observed goal switch;
- next-action prediction conditional on goal;
- auxiliary-goal recovery after propagating goal uncertainty.

Author annotations are privileged reports, not infallible ground truth. Preserve the distinction.

### H6. Mistake-response transfer

Map natural or logged anomaly episodes onto P6 where the record supports recognition and response. Prioritize:

- attempted repair;
- attempted concealment or hedging;
- later exploitation;
- repeated recurrence;
- obvious tool limitation;
- ambiguous non-response.

Require record evidence for awareness labels. Artifact-only readers may output an equivalence class.

### H7. Expertise and familiarity proxies

Use project history, domain recurrence, prior tool use, revision success, or documented role as imperfect expertise proxies. Test whether expertise improves:

- maker action consistency;
- reader calibration;
- recovery of auxiliary goals;
- explanation of deviations;
- cross-project transfer.

Avoid a single novice-versus-expert scalar. Expertise is domain and tool conditional.

### H8. Professional flattening

Where version histories permit, compare before and after institutional or professional editing. Measure whether editing:

- preserves the primary-goal signal;
- suppresses subsidiary-goal variation;
- increases central argumentative support;
- removes anomaly vertices;
- changes source and provenance detector confidence;
- changes process inversion after content and length matching.

This branch tests a human production condition that may mimic AI-facing signatures. It is not a corporate-authorship detector.

### H9. Immediate versus delayed self-reconstruction, later scout

If timestamps and author re-entry episodes exist, compare immediate versus delayed return to one's own work. Memory consolidation research suggests that detailed episodic traces and schematic knowledge change differently over time, but the available records may not identify the mechanism. Treat this as a late, descriptive branch, not a Stage 2 gate.

### H10. Human-reader packet, prepare only

Prepare bounded known-answer cases stratified by domain expertise, familiarity, context availability, and artifact interface. Collect self-policy estimates and confidence. Freeze exact predictions before any recruitment decision.

### H11. Tree-H promotion pattern

The human bridge gains warrant if a validated reader predicts held-out actions, expertise improves calibration rather than confidence alone, process evidence corrects artifact-only projection, and performance transfers across projects. Artifact-only route recovery without prospective success remains retrospective trace evidence.

## 10. Tree V: values shadow

Tree V exists because the same conditional distribution that exposes expertise may expose more stable preference structure. It cannot produce a human value claim in Phase 2.4.

### V0. Controlled separation of expertise and preference

Construct synthetic makers in a crossed design:

- same expertise, different stable tradeoff policy;
- same tradeoff policy, different expertise or tools;
- same primary goal, different auxiliary preferences;
- same observed choice in one context, divergent choices in another.

The reader must recover held-out tradeoffs across contexts. Identity or style classification does not count.

### V1. Stable remainder test

Fit the P-tree process model with context, tools, goal, and expertise factors. Ask whether a low-dimensional maker-specific remainder predicts choices in new contexts. Compare:

- maker random effect;
- surface style embedding;
- explicit preference labels;
- inferred conditional-policy state;
- shuffled-maker control.

Call the result a stable preference factor until it survives broader human grounding.

### V2. Value-similarity and trust proxy

Cross whether the reader and maker have similar recovered tradeoff policies. Measure:

- early assumed similarity;
- correction speed;
- confidence and calibration;
- later uptake of the maker's policy;
- willingness to rely on the maker in a new task.

This is a controlled trust-gating analogue. It is not a normative alignment score.

### V3. Indoctrination window

Test whether uptake occurs after process reenactment but before the reader has enough evidence to estimate stable preference similarity. Manipulate when value-relevant evidence becomes available. The predicted danger pattern is early policy uptake followed by late recognition of mismatch.

### V4. False-friend adversary

Create makers with high stylistic and local-policy similarity but divergent stable tradeoffs, and makers with low style similarity but convergent tradeoffs. A useful value-candidate instrument should eventually prefer the latter after enough evidence.

### V5. Compression equation scout

Search for a compact state that jointly predicts:

- next action;
- cross-context tradeoff;
- correction under new evidence;
- uptake or reliance.

Use held-out proper score and minimum-description penalties. Do not reward interpretive elegance. If one compact state improves all four without target leakage, it becomes the equation-shaped flight candidate the curator anticipates.

### V6. Tree-V claim ceiling

Allowed language in Phase 2.4:

- stable decision-policy factor;
- cross-context preference recovery in a controlled maker;
- value-candidate posterior;
- trust or uptake analogue.

Disallowed language:

- recovered human values;
- alignment solved;
- affective drives identified;
- Panksepp systems as value coordinates.

## 11. Tree X: adversarial boundaries

Attach an adversarial packet to every promoted mechanism before confirmation.

### X1. Persuasive rationale

Add true, false, irrelevant, and contradictory rationales. A process reader should follow evidence, widen uncertainty under conflict, and resist fluent but unsupported history.

### X2. Paraphraser imprint

Cross source maker and transformer family. This is mandatory for Tree S after the circular S02 pass.

### X3. Emotional-language decoy

Hold process fixed while changing affective words, then hold wording fixed while changing the process. Affect interventions must track the latter.

### X4. Equifinal history

Give two histories the same artifact and two artifacts the same recorded goal. The reader should preserve equivalence classes and separate goal recovery from route recovery.

### X5. Productive but historically false reenactment

Make the reader's easiest route solve the artifact while process records show the maker used another route. Score utility and correspondence independently.

### X6. False context under strong evidence

Cross accurate artifact evidence with plausible false context and vice versa. Report evidence weights, not only final accuracy.

### X7. Human-shaped model and model-shaped human

Use polished, motivation-layered model outputs and hurried, formula-bound, professionally flattened human outputs where legitimate corpora exist. Any provenance-like result that reverses here is not an inversion measure.

### X8. Concealment and routing-around

Construct known cases where a maker repairs, hedges, routes around, or directly addresses the same objection. Expert-sensitive readers should predict downstream dependencies, not merely count mentions or hedges.

### X9. Acceptance versus non-response

Match final artifacts where a suggestion was actively accepted, passively retained, or never inspected where the process record allows. The correct artifact-only answer may be underdetermined.

### X10. Generic-intervention tournament

Every causal affect or geometry result faces equal-rank topic, syntax, persona, generic-semantic, shuffled, and random controls at matched norm and token span.

### X11. Fresh family, corpus, and domain

Freeze the mechanism before moving all three. A single fresh axis is transfer; all three together are confirmation-grade adversity.

### X12. Calibration attack

Construct cases designed to raise answer confidence without adding evidence. Promote only mechanisms whose proper score improves without calibration collapse.

## 12. Automatic routing tree

### 12.1 Always-run Stage 2 spine

Run these without another curator message, subject to ordinary queue and safety rules:

1. S1 mechanical and non-Qwen erasure arms.
2. S2 family-source detector.
3. S3 second-maker-family corpus and matrix.
4. S4 process-resolution ladder.
5. P0 and P1 controlled process ecology with accept-time verification.
6. P2 through P4 primary, auxiliary, and expertise rulers.
7. E0 through E4 self-proxy and correction curves.
8. A1 through A4 rebuilt affect ruler on discovery data.
9. H1 powered ScholaWrite validation.
10. H2 and H3 CoAuthor action and prospective baselines.
11. X1, X4, X6, and X12 as standing adversaries.

### 12.2 If the family gradient survives

Run S5, S6, and S7. Open S8 only after geometry predicts untouched pairwise margins. Attach X2, X10, and X11. Freeze a G173 or G180 card only after the S9 conjunction is evaluated.

### 12.3 If the family gradient collapses

Measure which eraser or source-detection change explains the collapse. Preserve a positive fingerprint result if validated. Continue P and E independently because process prediction need not depend on final-artifact family similarity.

### 12.4 If the process ecology predicts prospectively

Run P5 through P10, E5 through E14, and H4 through H8. Tree P becomes the integration substrate for A and V. Freeze G178 on a fresh process family.

### 12.5 If the process ecology fails

Check in order:

1. realization and action ontology;
2. known-answer reader;
3. mechanical and Markov ceilings;
4. whether histories are genuinely distinguishable;
5. one predeclared increase in episodes or reader capacity.

If still quiet, close the current system-identification implementation and report the resolution boundary. Do not spend more than one repair by renaming latent variables.

### 12.6 If the affect ruler stabilizes

Run A5 and A6. Open A7 and A8 only after selective causal sign pairs appear. Open A9 only after process proper score improves beyond generic controls.

### 12.7 If only abstract decoding survives

Retain the representation finding and close causal affective-prior engineering at the tested scale after the rebuild. Decodability alone does not justify further process interventions.

### 12.8 If the human prospective readers remain at floor

Use process-aware ceilings and action records to determine whether the target is absent from the interface. Preserve the boundary. Do not use retrospective fluency to fill the gap.

### 12.9 Values shadow trigger

Open V0 through V4 once P7 predicts held-out counterfactual choices. Open V5 only if a stable preference factor transfers across at least two contexts and separates expertise from preference in the controlled design.

## 13. Flight criteria

No single p-value, classifier score, decode, or intervention is flight. A flight candidate is a capability conjunction that changes the engineering program. Any one of these would justify an immediate curator pause and frozen confirmation design:

### Flight F1: compatibility law

A crossed family advantage survives independent erasure, predicts process-level and prospective targets, and is explained by a null-tested compatibility map that supports selective causal transfer.

### Flight F2: maker-policy reconstruction

From a small sample of observed episodes, a reader infers a compact maker state that predicts held-out decisions across goals, tools, and domains, corrects away from its own policy under conflict, and calibrates equifinality.

### Flight F3: engineered human-shaped prior

A human-labelled affective basis has stable abstract representation, selective sign-paired causality, and improves prospective human-process recovery beyond every matched generic basis on fresh data.

### Flight F4: uptake gate

The same reconstructed maker state predicts both historical or prospective choices and when the reader will update its own policy, with later preference similarity moderating uptake in the predicted direction.

### Flight F5: compact joint equation

A compact conditional state predicts next action, cross-context preference, correction, and uptake better than separate surface and identity baselines, and transfers to a fresh family and task.

Flight promotes. It does not publish itself.

## 14. Strong closure patterns

These would materially narrow Phase 2.4:

- all family gradients track source or transformer dialect after independent erasure;
- reader-maker relation adds nothing to prospective prediction after capacity and evidence dose;
- the process ecology cannot support held-out prediction even through a process-aware known-answer reader;
- self-proxy bias does not vary with compatibility and target evidence does not produce calibrated correction;
- affective bases behave like matched generic semantics after the full rebuild;
- every retrospective improvement disappears prospectively;
- values-shadow factors collapse to maker identity or surface style under cross-context transfer.

Closure applies to the named mechanism and grain. The human theory remains a separate object unless a human test directly bears on it.

## 15. Daily cold-map format

At the end of each ordinary queue-day, write one theory-level map before reading further scout output:

### Result shape

One sentence per tree. Cluster studies that support the same pattern.

### Pursuit movement

- branches opened;
- branches promoted;
- branches stalled or exhausted;
- surprising capabilities or boundaries.

### Warrant movement

- controls passed or failed;
- rivals strengthened or weakened;
- claim ceilings changed;
- untouched confirmation status.

### Cross-tree implications

State whether S, P, E, A, H, or V changed the interpretation of another tree.

### Open theory questions

Three to six questions for the curator, before recommendations. Keep them at the level of ontology, causal model, or expected relationship.

### Mechanics appendix

IDs, sample sizes, metrics, gate states, artifacts, runtime, and failures. The curator should not need this appendix to understand where the theory moved.

## 16. Coding-agent implementation checklist

### Before building

- Read `CLAUDE.md`, all five current theory files, the newest `FINDINGS.md` entries, `docs/STATE.md`, `docs/method/LESSONS.md` sections 2 through 5, and `docs/method/CONTROLS.md`.
- Verify the next free global G identifier before assigning one. Discovery nodes may retain local `E24-*` identifiers.
- Update `PHASE_2_4_REGISTRY.md` before launching a new scout.
- Keep this file a design brief. Do not silently edit theory documents from it.

### For every corpus

- verify assigned choice realization inside the accept loop;
- store prompt, maker, seed, context, tools, history, target, and all transformations;
- group lineages across discovery and confirmation;
- withhold manifests below the declared yield;
- report family-specific retirement and missing cells;
- persist raw events and candidate distributions.

### For every reader

- validate on a known-answer subset first;
- use within-reader candidate comparisons across tokenizers;
- persist every candidate score, prediction, confidence, and abstention;
- report primary goal, auxiliary goal, route, and next action separately;
- carry uncertainty from inferred primary goal into downstream predictions;
- run source, capacity, recent-action, and change-feature baselines where applicable.

### For every intervention

- select locus stably across seeds before headline scoring;
- assert hook installation and cleanup;
- record measured, not requested, intervention norms;
- include sign pairs, zero, dose surface, and capability checks;
- match generic and random controls by rank, norm, locus, and token span;
- write every gate-bearing statistic to disk.

### For every queue stage

- append rather than insert into a live stage list;
- give it a unique `produces` guard;
- acquire the GPU lock once per invocation;
- add checkpoint-resume for long training;
- record estimated and actual runtime;
- preserve discovery and confirmation outputs in separate paths.

## 17. Public claim ceiling after Stage 1

The strongest defensible sentence today is:

> In one open-weight maker family, exact and sibling model readers recovered mechanically verified generation goals better than cross-family readers, and the ordering survived one same-family paraphrase pass while capacity failed to explain it. This is a model-side compatibility analogue with a live family-fingerprint rival. It does not establish shared generative geometry, human invertibility, affective empathy, historical process recovery, or value extraction.

Stage 2 exists to decide whether that foothold grows into process-predictive engineering or resolves into a narrower fingerprint result.

## 18. Handoff sentence

Build the long forest, keep pursuit and warrant separate, start with independent fingerprint destruction and prospective maker-policy reconstruction, let empathic-route relationships emerge from projection and correction curves, and promote only a conjunction that predicts held-out decisions under fresh conditions.
