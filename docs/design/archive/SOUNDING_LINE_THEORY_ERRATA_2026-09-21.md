# Sounding Line theory errata: local goals, reorganization, expertise and simulation

**Exact coding handoff, filed 21 September 2026.** Based on Sounding Line `9d193b75cb117c999f197ca0319ff946656eba3f`, the current five-file theory store, the curator's latest walkthrough, and the review of the Stage 12/V19 plan. This is a proposed patch, verified on an isolated copy. It has not been applied to either live repository.

## 1. Intended change

The new walkthrough adds texture to the existing joint reconstruction account. A reader can reorganize familiar evidence into a different explanation, discover that apparent competence was performance for an audience, and revise an earlier reading after the end of a work. Fluent production may carry a history of practiced choices. A simulation advantage remains a central hypothesis to pursue, with its mechanism unresolved.

Two inconsistencies in analyst prose also need repair. The store alternates between reserving “proximal goal” for the governing purpose and requesting local sentence-level goals. It also sometimes defines understanding exclusively through future prediction, although the later curator priority includes understanding the work itself. The edits make scope explicit and preserve historical correspondence, reader-enactable usefulness and prospective discrimination as distinct achievements.

**Seven small conceptual changes, four existing files, eight new curator excerpts.** Every older curator quotation and every existing table row remains. No result is upgraded, no identifier is changed, and no new theory file or inference family is introduced. The net addition is 979 whitespace-delimited words across the four files. `ALIGNMENT.md` is unchanged.

The week-long experimental mechanics belong in the companion handoffs. The theory patch contains standing distinctions and limited research context, not a new chronological recap or a list of planned experiments.

## 2. Exact edit map

| Edit | Location | Change and purpose |
| --- | --- | --- |
| **E1** | `THE_TRIPLE_INFERENCE.md` §1 object table and its interpretation; §2 terminology paragraph | Add local subordinate goal `g_t` beneath governing purpose `G`. A sentence is an inspection address, not one proven decision. External requests and adopted goals remain different. Update both locations so the old exclusive wording does not contradict the local output request. |
| **E2** | `THE_TRIPLE_INFERENCE.md` §2, before historical correction | Preserve the “final line” observation. Later context can reinterpret earlier choices. Keep uncertainty among complete accounts distinct from simultaneous goals, switching and collaboration; do not force nonexclusive goals to sum to one. |
| **E3** | `THE_TRIPLE_INFERENCE.md` §2, “A label is a lossy pointer…” | Retain the earlier demanding curator quotations about prediction. Replace duplicated analyst prose that made future prediction the sole definition of understanding. Corroborated local/process interpretation and reader-enactable routes receive their own standards. |
| **E4** | `READER_HEURISTICS.md` §2, before the definition of mistake | Add the jiu-jitsu excerpts. Expertise changes what the reader can distinguish; apparent errors can become purposeful choices. Fighting skill, convincing choreography and observational familiarity are separate. |
| **E5** | `READER_HEURISTICS.md` §4, existing context/reorganization paragraphs and nearby flower example | Integrate the new organization-of-evidence insight and the curator's own caution about overbiasing. Additional facts, new relations and new candidate families can coexist; explanatory reach alone does not establish an author's motives. |
| **E6** | `DECISION_TRACES.md` §1 control definition and §3 automatic traces | Separate automatic execution from the technical construct of outcome-insensitive habit. Add the flow conjecture as a possible historical trace, preserving “would” and “perhaps.” Past practice is not automatically current endorsement. |
| **E7** | `THREE_COGNITIVE_LAYERS.md` §2, before the functional human-generative-prior definition | Preserve the expected simulation advantage as a pursuit hypothesis. Distinguish decodable state, usable state, process inference and human correspondence. A coordinate change alone adds no information; its usefulness to a bounded reader remains a live question. |

## 3. Quote provenance and transcription repairs

All eight excerpts come from the latest long walkthrough beginning “Alright, the update makes sense,” addressing local goals, Worth the Candle, acquired jiu-jitsu expertise and flow. Its recording date was not separately supplied. **2026-09-21 is the filing date, not an invented date of speech.** Earlier contribution, attention and trust remarks already have homes in the current theory; this pass does not duplicate them.

| ID / edit | Source excerpt | Treatment |
| --- | --- | --- |
| Q1 / E1 | “For the broad scope, we're going to need a weighted list of proximal goals with respect to each local sentence, at least, of an output.” | Words preserved; line wrapping only. The analyst explains the two goal scopes outside the quotation. |
| Q2 / E2 | “You're often waiting for the final line of the play or riddle to understand the point the author was trying to make.” | Words preserved. No claim that the ending uniquely identifies the actual author is inserted. |
| Q3 / E4 | “the ones previously thought were good were the ones that were best at appearing good rather than actually being so, which doesn't look as flashy.” | Restore the omitted subject **I** after “The ones”; capitalize the extracted sentence. The surrounding speech explicitly concerns the curator's earlier judgment. This is the only substantive lexical repair. |
| Q4 / E4 | “Knowing that there's true knowledge there makes staring at it more interesting.” | Words preserved; separate excerpt, not joined to Q3 as continuous speech. |
| Q5 / E5 | “It was this data organization that explained many of the choices that I had not even remarked upon as unusual.” | Words preserved. The named literary example is evidence of changed reading, not verified private motives. |
| Q6 / E5 | “I actually worry that my specific explanation is overbiasing me and isn't being treated as one of many possible solutions.” | Words preserved, including “overbiasing.” Kept beside Q5 as a separate excerpt. |
| Q7 / E6 | “things that come out in a flow state would be more like the kinds of decisions one has made in the past and would be more likely to have things like, not Freudian slips, but context-based errors perhaps.” | Contiguous excerpt after a spoken restart; capitalize its beginning. Preserve the hesitation and uncertainty; do not strengthen “would” into “do.” |
| Q8 / E7 | “There will be some kind of simulation-based advantage.” | Words preserved. The adjacent provenance notes that the surrounding speech calls this an implicit assumption guiding the search. |

**Older quotes retired or changed: none.** No analyst synthesis is put into the curator's mouth. Ambiguous name fragments and speculative claims about identifiable authors are not repaired into factual claims.

## 4. Research texture and limits

The added literature context is deliberately small. Human flow research studies an experience under particular task conditions; it does not establish that fluent output reveals stable values. Work on human habit induction also cautions against equating repetition with outcome-insensitive control. Those distinctions preserve the curator's historical-trace conjecture while leaving rival explanations open. [Ulrich et al., 2016](https://academic.oup.com/scan/article/11/3/496/2375154), [Pool et al., 2022](https://doi.org/10.1101/lm.053413.121).

The simulation clarification is a conceptual scope repair, not a new literature result. Predictive-state methods, causal interchange and J-space work inform the experimental handoffs. They are not imported into the theory as proven explanations of human appreciation. The existing corrected model-family evidence retains its current status in `READER_HEURISTICS.md` §1.

Claude's additional bootstrap and the new primary-source checks change the research plan. They do not create new theory evidence rows here: the bootstrap still needs the native reaggregation specified by V19, and the theory already records the underlying completed campaigns. Preserve those receipts and their limitations.

## 5. Implementation and acceptance

1. Read the current `docs/theory/README.md`, relevant sections and their afterwords. Reconcile source changes since the pinned revision. This handoff carries the curator's requested theory maintenance; it does not authorize a broader rewrite.
2. Copy the single `diff` fence below to a temporary patch file. Run `git apply --check` from the Sounding Line root. If the base matches, apply it normally. If later edits moved an anchor, integrate the specified change against the current text; do not reset the file to this snapshot or delete intervening evidence.
3. Run the repository's `tools/theory_lint.py` with its established Python environment on all five theory files. The isolated proposed files already pass the current checker. Do not treat a green format check as scientific approval.
4. Compare all old blockquote lines and existing table rows in order. The only new table row is the local subordinate-goal definition; its section interpretation is revisited. Confirm identifiers, evidence statuses, older quotes and their provenance are unchanged.
5. Read the edited paragraphs together. Check that local goals are not equated with measured attention; external requests are not equated with adopted aims; a changed literary interpretation is not reported as discovered biography; flow is not equated with endorsement; and “simulation” is not frozen to one architecture.
6. File this handoff in the repository's normal design archive if desired, and include a concise theory-maintenance entry through the existing process. Do not create a scientific result or FINDINGS measurement merely because a documentation patch passed. No full experiment rerun is necessary for these prose edits.

The patch was checked and applied in an isolated copy. Its resulting files match the generated proposal byte-for-byte; all 664 old quote lines and all 426 old table lines survive in order. The five-file format check passes. These are documentation checks only. No live repository was modified.

### Source fingerprints

Use these when checking the reviewed base and the exact result of the patch. A later source hash is a reconciliation task, not a reason to overwrite newer work.

| File under `docs/theory/` | Reviewed SHA-256 | Proposed SHA-256 |
| --- | --- | --- |
| `THE_TRIPLE_INFERENCE.md` | `dc7f6579be470dc9889718a2111f714652011c6ec3f497b316c49beb146cc672` | `065e312bd679d1a7fc8005a9a23996ef7351579f3f7a0f90eec5f59035c49914` |
| `READER_HEURISTICS.md` | `a1c4c08377fb63a96617d2809309a1debfa5093ec2aa14ae733f25604428c586` | `54ec94db3cb78b9eb76eff5620114ce0fe0bbc70c7ad6582348b9c23f8695c6c` |
| `DECISION_TRACES.md` | `f3f395d8abf4817ff8698ee5acca05e5df3b24b9c8f59650f70bcf81067f67a0` | `87f89fefc85326d4c52a0d01113fc4b85681731aa66364db1d828cedde015116` |
| `THREE_COGNITIVE_LAYERS.md` | `3d984f377660ca00e649e4bc53707422f9e380ac10c34d7fdfd04f902d777cf9` | `8135e6021347bdae6415a2adcd866e0b32433f843ca23da3f7530030c2eb5cb0` |
| `ALIGNMENT.md` | `5f02ed27dc11f67d236f9039d61cf0926641477cf59a4f3d170507255805441b` | `5f02ed27dc11f67d236f9039d61cf0926641477cf59a4f3d170507255805441b` |

## 6. Exact patch

This is the complete replacement/insertion text. Context lines locate it; removed analyst prose remains recoverable in Git. The patch preserves old curator quotations.

```diff
--- a/docs/theory/THE_TRIPLE_INFERENCE.md
+++ b/docs/theory/THE_TRIPLE_INFERENCE.md
@@ -82,8 +82,9 @@
 
 | object | canonical meaning | timescale |
 |---|---|---|
 | **proximal goal** `G` | the governing purpose of the artifact or declared episode; distinct from the subordinate target currently in attention | artifact or episode scale; often maintained during production |
+| **local subordinate goal** `g_t` | the purpose of a particular choice or region, potentially serving one or several governing goals; not identical to the fact of attending to it | step or region scale |
 | **process** `P`, realized as `tau` | the particular decisions and actions that produced the artifact | artifact-local |
 | **expertise** `K` | the maker's learned transition model, shaping reachable actions and expected consequences; the shared language of a domain; the largest part, never the whole, of the ability to recreate | cross-episode, domain-relative |
 | **drives** `D` | currently active motivational pressures or primitive constraints | state-dependent |
 | **values** `V` | persistent organization of tradeoffs among goals, drives, and trajectories | longitudinal |
@@ -96,8 +97,22 @@
 > thought were available. Those belong in the maker model: external context as transformed through
 > the maker's beliefs and expertise.
 
 *2026-09-01 walkthrough; spoken wording lightly reconstructed.*
+
+> For the broad scope, we're going to need a weighted list of proximal goals with respect to each
+> local sentence, at least, of an output.
+
+*Curator's local-goal, evidence-reorganization and expertise walkthrough, supplied in the
+analysis thread; recording date not separately supplied; filed 2026-09-21. Wording preserved,
+with line wrapping and punctuation normalized.*
+
+The curator's latest product language uses proximal goals at the passage level. The object table
+retains governing purpose `G` and names its local subordinate targets `g_t`, so scope is explicit
+rather than silently changing the earlier definition. A sentence is an address for inspection,
+not proof of one psychological decision or one active goal. A reviewer request or commission is
+external context; the maker may adopt it, reinterpret it, oppose it or satisfy only part of it.
+Recovering that request does not by itself recover the maker's governing purpose or attended goal.
 
 Three conflations this table dissolves. **Expertise is not process.** Expertise is the maker's
 learned transition model, the map of which actions are reachable and what they are expected to
 do; process is one realized path through it, and results about one do not automatically transfer
@@ -136,10 +151,12 @@
 | **L-tier2** | Diverse episodes can narrow persistent motivational organization; the relative evidence needs of goal and value recovery remain to be measured | **OPEN for human value recovery and the relative-timescale comparison.** The author-identification curve measures identity, not values (test, L34; G60). Bounded constructed profiles can be recoverable from one artifact or from repeated artifacts (§5 G54; §6 S-15); these are construction-specific results, not human value ground truth. G65 remains the open comparison |
 
 **State of the section's claim.** The object table fixes the working distinctions among
 expertise and process, external and interpreted context, drives and values, and governing
-purpose and focal subgoals. These definitions do not establish recoverability. Repeated,
-diverse episodes are a proposed source of leverage on persistent motivational organization;
+purpose and focal subgoals. Local estimates carry their region and parent-goal scope;
+recovering an external request does not establish that the maker adopted it. These definitions
+do not establish recoverability. Repeated, diverse episodes are a proposed source of leverage
+on persistent motivational organization;
 no clean comparison here shows that human values require a particular number of artifacts
 or that goals require only one (L-tier2, G65). The measured real-text curve is a small
 identity-channel improvement followed by an early plateau (G60, L34). Constructed profile
 recovery establishes what can be recovered under its planted assumptions, not recovery of
@@ -232,8 +249,23 @@
 clues. Explanatory reach is not specificity: a broad aim may fit many makers, and its repeated
 manifestations may share one cause. Expertise can constrain purposeful behavior while also
 expanding the repertoire; it does not make experts universally more predictable than novices.
 
+> You're often waiting for the final line of the play or riddle to understand the point the
+> author was trying to make.
+
+*Curator's local-goal, evidence-reorganization and expertise walkthrough, supplied in the
+analysis thread; recording date not separately supplied; filed 2026-09-21. Wording preserved,
+with line wrapping and punctuation normalized.*
+
+Later parts of a work can change the interpretation of earlier choices. That is a legitimate
+revision using a later evidence snapshot, not evidence that the earlier meaning was already
+recoverable. Uncertainty between complete maker accounts differs from one maker pursuing
+several aims, switching aims, or collaborating with another maker. Marginal local-goal weights
+can conceal these differences. Preserve compatible goal and process combinations; nonexclusive
+goals need not form a distribution summing to one. These are distinctions within joint
+reconstruction, not new inference families. Confidence: untested, logic only.
+
 Historical correction also changes the evidence for a proposed technique. If its only
 warrant was that it supposedly produced this artifact, discovering a different actual route
 removes that warrant. A reconstruction independently made to work retains its demonstrated
 usefulness. The historical route is evidence of feasibility under the maker's conditions,
@@ -264,13 +296,14 @@
 > midway through the creation of an artifact.
 
 *2026-09-04 walkthrough; lightly cleaned transcript.*
 
-The current terminology reserves proximal goal for the artifact's governing purpose,
-the reason resources are spent on the work. The quotation uses goal at both governing
-and attended levels; the prose distinguishes them. Purpose can persist while attention
-moves among subordinate goals, and a genuine change of purpose remains possible. Its
-stability is a working expectation, not a universal fact about artifacts.
+The earlier terminology reserved proximal goal for the artifact's governing purpose,
+the reason resources are spent on the work. Both this quotation and the later local-output
+request in §1 use the phrase at more than one level. Keep governing purpose `G` and local
+subordinate goal `g_t` explicit whenever scope matters; neither is identical to attention.
+Purpose can persist while attention moves among subordinate goals, and a genuine change of
+purpose remains possible. Its stability is a working expectation, not a universal fact.
 
 The K-family pull ordering supplied and scored in Stage 7 is a preference over move types
 derived jointly from purpose and law. Stage 8 scores an artifact purpose beside that pull
 ordering; their different readability does not decide which is the more fundamental goal.
@@ -325,9 +358,9 @@
 working account. The artifact can help its maker work backward from choices to the goals
 and expertise that shaped them. Maker and outside reader estimate the same targets from
 different observations.
 
-**A label is a lossy pointer; understanding is realized prediction** *(the 2026-08-30/31
+**A label is a lossy pointer; prospective constraint tests its realization** *(the 2026-08-30/31
 passes; provenance in `docs/design/archive/PHASE_2_4_STAGE_6_THEORY_ERRATA.md`)*:
 
 > If you had all three pieces, you should be able to recreate the activity quite precisely. If the
 > labels sound insightful but do not improve the prediction, then no, the maker has not been
@@ -341,27 +374,22 @@
 > Those are two things that would demonstrate understanding.
 
 *2026-08-30 assessment; spoken wording lightly reconstructed.*
 
-A mental-state label is a lossy pointer into `q_R`, not a recovered state. A short hypothesis
-about the maker underdetermines the state it names; to carry evidential weight it must be
-realized against the artifact and declared context into a state that changes the reader's
-predictive distribution, and the test of that realization is prospective: the hidden
-continuation, the next edit, stopping, a declared recipient response, or the changed-context
-choice. A label whose realization
-moves none of these has not been cashed, however insightful it sounds.
-
-**A short mental-state label is a pointer, not the reconstructed maker state.** Its operative
-meaning must be re-centered in the whole artifact, context, and possibility space until it
-entails a distribution over the maker's remaining decisions. Different descriptions may realize
-the same predictive state, and the same words may realize different states for different
-makers; a longer rationale does not solve this by itself. The representation may be language,
-structured slots, a program, or a latent vector; what earns credit is prospective constraint
-on a hidden continuation, next edit, stopping decision, declared recipient response, or
-changed-context choice. Stage 6
-attempted to instrument this rule, but its hidden dependencies voided the interpretation
-(M-S6). The rule remains a prospective criterion, not a claim that language is the required
-representation of the maker state.
+A mental-state label is a lossy pointer into `q_R`, not a recovered state. Its meaning must be
+realized against the artifact, context and possibility space. Different descriptions can realize
+the same predictive state, and the same words can realize different states for different makers;
+a longer rationale does not resolve this. Language, structured slots, programs and latent vectors
+remain possible representations.
+
+The earlier quotations state a demanding prospective criterion: a maker account should constrain
+hidden continuations, edits, stopping, recipient responses or changed-context choices. The later
+walkthrough above also makes understanding the work an intended benefit in its own right.
+Independently corroborated process relations, correctly located decisions and a useful route the
+reader can enact are separately assessable contributions. A persuasive description alone earns
+none of them, and a predictive gain alone does not establish historical correspondence. Stage 6's
+attempt to instrument the prospective criterion was voided by hidden dependencies (M-S6).
+The criterion survives without becoming the sole definition of useful understanding.
 
 A recipient-effect prediction is credited against a declared, independently checked
 response. It does not establish the exact edit or historical route that produced it.
 The editing example is developed in `DECISION_TRACES.md` §2.
--- a/docs/theory/READER_HEURISTICS.md
+++ b/docs/theory/READER_HEURISTICS.md
@@ -279,8 +279,26 @@
 association remain alternatives to correct identification. Identifying a maker, predicting
 that maker under a new constraint, and reconstructing a historical process are different
 achievements. An anomaly is therefore one entry route; familiarity is another candidate.
 
+> The ones I previously thought were good were the ones that were best at appearing good rather
+> than actually being so, which doesn't look as flashy.
+
+> Knowing that there's true knowledge there makes staring at it more interesting.
+
+*Curator's jiu-jitsu example in the local-goal, evidence-reorganization and expertise walkthrough,
+supplied in the analysis thread; recording date not separately supplied; filed 2026-09-21.
+Separate excerpts. The first restores the omitted subject I after "The ones"; all other wording
+is preserved, with line wrapping and punctuation normalized.*
+
+Added expertise can change which alternatives, constraints and consequences a reader sees,
+turning an apparent error into a purposeful choice or apparent skill into presentation skill.
+The operative goal still matters: convincing choreography and effective fighting can reward
+different moves. Recognition of genuine competence may invite closer attention without
+establishing the maker's history or values. Production competence, observational familiarity,
+shared tools and prior knowledge are live explanations for the reader's advantage, not synonyms.
+Confidence: untested, logic only for this proposed reader mechanism.
+
 A mistake is a sharpened anomaly for which evidence supports a mismatch between a choice and the
 maker's operative trajectory. The strongest evidence often comes from handling: repair exposes a
 preferred counterfactual, concealment exposes recognition and a protected goal, repetition
 suggests habit or a stable transition-map limitation, and non-response suggests either
@@ -468,28 +486,43 @@
 
 *Curator's six-question maker-model and context walkthrough, supplied in the analysis thread; recording date not separately supplied;
 filed 2026-09-18. Contiguous excerpt, wording preserved.*
 
-Context does not license a story in one step. It can reweight considered maker/process
-hypotheses, or cause a bounded reader to represent a possibility it had omitted. These are
-different computational events even if a more comprehensive model describes both as updating.
-No particular activation function or neural threshold is established by the introspection.
-
-A useful cue should change independently assessable expectations about other evidence; a
-false cue should not acquire authority merely because it organizes many details. One constraint
-can explain several choices, but those choices are then partly dependent observations rather
-than separate confirmations of the same story. A changed felt experience can be worth
-understanding without proving the inferred biography or private intention. The tool-conditioned
-form of the rule lives in §6, and target-specific correction remains open in HH-23 and HH-25.
+> It was this data organization that explained many of the choices that I had not even remarked
+> upon as unusual.
+
+> I actually worry that my specific explanation is overbiasing me and isn't being treated as one
+> of many possible solutions.
+
+*Curator's Worth the Candle example and its immediate qualification in the local-goal,
+evidence-reorganization and expertise walkthrough, supplied in the analysis thread; recording
+date not separately supplied; filed 2026-09-21. Separate contiguous excerpts, wording preserved,
+with line wrapping and punctuation normalized.*
+
+The new account can change which familiar details count as diagnostic choices, not only their
+weights after retrieval. Distinguish additional observations, improved access or organization of
+existing evidence, and expansion of the candidate family. A supplied explanation can do more
+than one of these; even a cue about already visible facts can introduce a new relation or
+privileged answer. No particular activation function, rotation or neural threshold follows from
+the introspection. The literary example records a changed reading, not independently verified
+knowledge of the author's motives or values.
+
+Context does not license a story in one step. A coherent false frame may reorganize many
+details, and details explained by one common cause are not independent confirmations.
+Historical interpretation gains warrant from independently assessed correspondence or
+discriminating consequences, not from explanatory reach or felt change alone. The curator's
+favored explanation remains one candidate. The tool-conditioned rule lives in §6, and
+target-specific correction remains open in HH-23 and HH-25.
 
 The flower example adds a candidate reason some context cues reorganize many details:
 a condition believed to persist through much of production may affect several choices
 together. Claimed loneliness could therefore change the reader's interpretation of a
 bright flower without establishing either the artist's actual state or the flower's
 intended meaning. Duration, explanatory reach, and source reliability are different
 properties. A broadly applicable cue can be reliable, misleading, or too flexible to
-constrain anything. The account earns support only if it improves predictions beyond
-the story it prompted; it does not inherit support from the reader's felt change alone.
+constrain anything. The historical account earns support through independently assessed correspondence or
+discriminating consequences beyond the story it prompted; it does not inherit support from
+the reader's felt change alone.
 
 **The current ordering conjecture places context especially at maker differentiation.** The
 artifact first supports a self-based candidate distribution; biography, prior work, tools,
 culture, role, and source reliability then help move that distribution toward this maker. This is
--- a/docs/theory/DECISION_TRACES.md
+++ b/docs/theory/DECISION_TRACES.md
@@ -39,10 +39,12 @@
 **1. Decision target.** *Polish*: recoverable decisions directed toward the reader, their attention
 or their comprehension. *Depth*: recoverable decisions directed toward the problem, subject, or
 artifact itself. Attraction and translation are subtypes of polish.
 
-**2. Degree of control.** *Deliberate*: consciously placed. *Automatic*: habituated, not actively
-held. `emblematic` and `leaked` are the **affect-specific** versions of this distinction, not
+**2. Degree of control.** *Deliberate*: consciously placed. *Automatic*: executed without the
+individual choice being actively held; practiced routines are one source. This does not by
+definition mean habitual control that is insensitive to the current outcome's value.
+`emblematic` and `leaked` are the **affect-specific** versions of this distinction, not
 synonyms for all deliberate and automatic behaviour.
 
 **3. Terminal-value topology**, a property of the artifact as a whole: *layered* (decisions serve
 several partially competing terminal values), *flattened* (many decisions reduce to one), or
@@ -400,8 +402,28 @@
 > of previous attention, compressed lossily through expertise, and it gives you a record of what the
 > maker chose to attend to when the artifact was created.
 
 *2026-09-01/02 walkthroughs; spoken wording lightly reconstructed.*
+
+> Things that come out in a flow state would be more like the kinds of decisions one has made
+> in the past and would be more likely to have things like, not Freudian slips, but context-based
+> errors perhaps.
+
+*Curator's flow-state conjecture in the local-goal, evidence-reorganization and expertise
+walkthrough, supplied in the analysis thread; recording date not separately supplied;
+filed 2026-09-21. Contiguous excerpt after a spoken restart; initial capitalization and
+punctuation normalized. The words "would" and "perhaps" retain its conjectural status.*
+
+The proposal gives fluent production a possible historical signal: a practiced policy may
+remain visible after its original context or aim has changed. It does not make flow, automatic
+skill, habitual control and present endorsement the same thing. Human flow studies measure a
+specific experience and task condition; fluent model output does not measure it. Evidence of
+outcome-insensitive habit is also distinct from repetition, whose induction effect is not
+uniform across human studies. A repeated choice can reflect old practice, a current purpose,
+a role, a tool default or an unnoticed constraint. These alternatives qualify how a trace is
+read without denying that expertise carries a transformed history. Confidence: untested,
+logic only for the proposed flow-to-trace relation. Literature context: [Ulrich et al.](https://academic.oup.com/scan/article/11/3/496/2375154),
+[Pool et al.](https://doi.org/10.1101/lm.053413.121).
 
 The original split came from the curator's ten-artifact think-aloud. It concerns the
 control and history of expression. Mapping automatic and deliberate expression onto
 primary affect and constructed emotion is an interpretive proposal, not a demonstrated
--- a/docs/theory/THREE_COGNITIVE_LAYERS.md
+++ b/docs/theory/THREE_COGNITIVE_LAYERS.md
@@ -299,8 +299,26 @@
 that produced its training data strongly enough to support some human-shaped inferences. The
 current evidence establishes decodable geometry and tracking behavior, not that the model
 reproduces the human generative mechanism. "Ghosts of a human brain" remains the curator's
 organizing hypothesis, not an architectural finding. The errors are the interesting part.
+
+> There will be some kind of simulation-based advantage.
+
+*Curator's local-goal, evidence-reorganization and expertise walkthrough, supplied in the
+analysis thread; recording date not separately supplied; filed 2026-09-21. Contiguous excerpt,
+wording preserved. The surrounding speech describes an implicit assumption guiding the search.*
+
+The expected advantage is a pursuit hypothesis with several possible realizations: a runnable
+process account, reusable predictive state, a learned transition model or a target-conditioned
+change in the reader. These are not equivalent to a full brain simulation. A coordinate change
+alone adds no information, though it can change what a bounded decoder can access or what an
+intervention can selectively control. Decodable state, usable state, accurate process inference
+and human correspondence are separate claims. A supplied world law or a failed reader cannot
+settle whether a learned simulation mechanism adds value. The corrected model-family evidence
+is owned by `READER_HEURISTICS.md` §1; the earlier surface-sensitive advantage is not a standing
+confirmation of shared simulation. Confidence: untested, logic only for a general simulation
+advantage and human correspondence.
+
 For Phase 2.3, "human generative prior" has only a functional meaning (2026-08-21): a model
 supplies candidate human-coherent processes that improve recovery of facts withheld from the
 candidate-generation step. Fluent mental-state labels and a plausible rationale do not count;
 the ablation compares this prior against target-specific context, a surface baseline, and no
```

## 7. What this does not settle

The local-goal output may be achievable before reliable maker-level value inference. An explanation can improve access to familiar evidence without being historically correct. Productive expertise may help inversion through several mechanisms, including better alternatives, observation, tools or training distribution. None of the edits selects one of these as the final account.

The simulation pursuit remains explicit and serious. Its warrant must come from comparisons in which a functioning mechanism does something useful under matched evidence, effort and information access. Preserving that distinction keeps the theory distinctive without making the next instrument's success a foregone conclusion.
