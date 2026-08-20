# Sounding Line Phase 2.2: Trajectory-Conditioned Inverse Reading

**Status:** Operative coding-agent handoff  
**Curator:** Abraham Haskins  
**Repository snapshot reviewed:** `c5e8f4c5e3d8f6c99b0316f892d75ce136f32455`, 2026-08-19  
**Phase relationship:** Phase 2.2 begins by closing the remaining Phase 2.1 realized-choice work, then changes the representation before any detector stacking  
**Artifact status:** This context is a work package, not a sixth theory document. If archived in the repository, its canonical destination is `docs/design/PHASE_2_2_CONTEXT.md`.

---

## 1. Executive directive

Phase 2.2 must stop treating the problem as binary adjudication of whether a human or model "made the decisions" in an artifact. The current theory and evidence no longer support that as the primitive question.

The new task is:

> **Build and validate a bounded reader that reconstructs human-coherent trajectories from artifacts, using declared context, expertise-shaped reachability, habits, anomalies, repairs, and realization evidence, while preserving uncertainty about hidden process and provenance.**

The reader should begin from a human generative model and adjust it to the apparent maker. It should estimate what goal, trajectory, expertise, and handling process would make the artifact intelligible to a human reader. It must not silently equate that reconstruction with the maker's actual internal process.

The immediate product of Phase 2.2 is a **reconstruction profile**, not a human-versus-AI verdict. A provenance classifier may later use parts of that profile as features. The profile itself is not provenance.

The phase has three governing consequences:

1. **The existing binary adjudication set does not freeze.** Preserve it as a historical design that exposed the wrong question. Do not delete it and do not keep expanding it.
2. **The Phase 2.1 G159 realized-choice battery still runs.** It answers a valid narrow question about whether a verified executed choice leaves recoverable evidence. It does not answer who owns the artifact or how human the artifact is.
3. **No detector stacking begins until the trajectory-conditioned reader has a validated ruler and an honest output contract.** The existing re-gate on 2.0F remains.

---

## 2. Reload and authority order

Before changing anything:

1. Resolve the current default-branch commit. The reviewed baseline is `c5e8f4c5e3d8f6c99b0316f892d75ce136f32455`; if the repository has advanced, reconcile this brief against the newer state rather than reverting it.
2. Read the whole of `docs/theory/`, newest first, including its README.
3. Read `FINDINGS.md`, then `docs/STATE.md`, then the Phase 2.0 and evaluation-contract material in `docs/design/`.
4. Read the matching sections of `docs/method/LESSONS.md` and `docs/method/CONTROLS.md` before converting any construct into a measure.
5. Inspect `docs/assets/visual-map.png` directly. Its geometry is the working mental model this phase must preserve.

Authority remains:

1. The curator's explicit rulings and quoted theory.
2. The five living theory files.
3. Validated repository results and their folded end states.
4. This Phase 2.2 context.
5. External literature and implementation convenience.

Do not let a familiar formalism replace the visual map. Use external work to sharpen or test the map.

Standing constraints remain unchanged:

- Preserve the five-file theory architecture.
- Do not create a new conceptual or theory file.
- Do not edit curator blockquotes except on explicit instruction.
- Structural theory changes are proposed before they are landed.
- No subagents unless the curator explicitly asks.
- No material spend or cloud burst without the repository's existing approval conditions.
- Alignment remains dormant. Phase 2.2 may clarify an upstream prerequisite but may not start value-extraction or alignment experiments.

---

## 3. The trajectory map is the binding ontology

The README diagram already contains the theory this phase needs. Do not replace it with a generic policy model.

### 3.1 Forward picture

Use the following objects as the working decomposition:

- **Latent preference field:** persistent positive and negative weighting over possible trajectories. It is not recoverable from one artifact and is not a Phase 2.2 target.
- **Current proximal goal:** a region temporarily lifted by attention under context.
- **Expertise and transition map:** the elastic trajectory lattice. Expertise changes reachability, path cost, reliability, and available routes. It is not merely another goal or a bag of remembered decisions.
- **Habit:** residue of repeated behavior, including prior attention-weighted behavior, training, convenience, accident, and practice. Habit is one historical record carried beside expertise, not a clean value readout.
- **Composed policy-propensity landscape:** the surface produced by the interaction of the lower objects.
- **Behavior point:** the candidate actually selected.
- **Lower-likelihood alternatives:** suppressed but potentially recoverable deformations of the possibility space.

The minimal forward account remains loose:

\[
G_t = f(V,D_t,C_t,A_t)
\]

\[
P_t \sim \pi(K,H,G_t,C_t)
\]

\[
O = h(P_{1:T},C_{1:T})
\]

where the artifact \(O\) is a lossy trace of the realized trajectory. The equations organize the objects; they do not assert a fitted mechanism.

### 3.2 Inverse picture

A reader \(R\) does not recover these objects directly. The reader begins with its own human model and adjusts it using the artifact and declared context:

\[
q_R(G,P,K,H \mid O,C)
\]

The output belongs to the **reader-artifact-context relation**. Reader expertise, available maker information, tools, medium, commission, audience, and constraints can all change the reconstruction.

The reader's human self-model is both the source of traction and a projection hazard. Phase 2.2 must record reader identity and conditioning as part of every reading rather than treating one reader as an oracle.

### 3.3 Expertise and past attention

The curator's clarified claim is:

> Expertise is the trajectory or transition map shaped through previous attention, practice, correction, and learning. It constrains present possibilities and allows current attention to operate at a different level of the problem.

Do not collapse that into "expertise is a record of past attention." Habit more directly preserves repeated behavior, while expertise changes the shape of possible movement. Both are historical, and they can overlap, but they play different roles in the current map.

### 3.4 Attention

An **active goal** is the region currently promoted by attention. A background concern such as elegance, status protection, rhythm, or methodological defense ordinarily acts through the deformed trajectory space and learned constraints. It becomes an active proximal goal when it recruits focal control.

Human goals can genuinely drift because attention can relocate. Surface goal movement can also occur without a change in persistent motivation because opportunities change and expertise expresses the same constraints differently across the artifact.

Do not hard-code a known cause for attention allocation. Do not use attention as a gap-filler. Model it as a latent, time-varying selection process whose transition law is open.

Do not freeze the claim that foreground cognition is always one serial goal rapidly switching. Task switching is real, but general attention and skilled action permit interacting forms of parallel constraint satisfaction. Serial switching is a candidate approximation, not a phase assumption.

---

## 4. Retire “decision weight” as a primitive

The term has absorbed several different questions. Phase 2.2 should use plain descriptions until the distinctions earn stable names.

For every relevant choice, keep at least these quantities separate:

1. **Formation difficulty:** the work a reader estimates a human would need to reach the choice from the declared starting conditions.
2. **Trajectory leverage:** how much the choice changes later reachability or reduces the downstream problem.
3. **Episode control:** who specified, selected, rejected, revised, or vetoed the choice in this artifact's production history.
4. **Trace support:** how strongly the finished artifact supports the proposed reconstruction.
5. **Historical shaping:** what learned expertise and habit appear necessary to make the trajectory available.

These are temporary descriptive labels. Do not install them as five new canonical nouns without curator review.

### 4.1 What the reader actually estimates

The reader does not know actual cognitive effort. It estimates a distribution over plausible human routes:

> What would I have to notice, know, try, or already have learned to arrive here, and what evidence says this maker differed from me?

That estimate can be useful even when it is causally wrong. It is human-coherent reconstruction, not direct workload measurement.

### 4.2 The observational-equivalence rule

This rule is non-negotiable:

\[
(O_1,C_1,R_1)=(O_2,C_2,R_2) \Rightarrow q_1=q_2
\]

Two identical artifacts shown to the same reader under identical declared context cannot receive different artifact-only readings merely because one maker secretly deliberated for weeks and the other guessed. If expertise, tool access, biography, drafts, or process records are supplied as context, the readings may differ. If they are not supplied and leave no trace, the instrument must remain uncertain.

This preserves the curator's reader-relative answer without pretending the reader can recover inaccessible history.

### 4.3 Why a thesis outweighs punctuation

A thesis may be reconstructed as difficult to reach, may reshape a large portion of the later trajectory space, and may organize many visible dependencies. Punctuation may be locally automatic while still expressing a deeply trained transition map.

The thesis does not outweigh punctuation because one visible event is literally equal to hundreds of hidden events. It outweighs punctuation when the reader's best human generative account assigns it greater formation difficulty, trajectory leverage, or recoverable hierarchical consequence. Those grounds can diverge and must be reported separately.

---

## 5. Human invertibility is representational, not uniquely human

The curator's answer is clear:

> A sufficiently aligned model could produce artifacts that are highly human-invertible and could optimize this property better than humans once the trick was understood.

Therefore:

- Human invertibility is not a proof of human provenance.
- A model artifact can legitimately score high.
- A high score means the artifact supports a strong human-coherent reconstruction under the tested reader and context.
- A low score may reflect foreign generation, deliberate concealment, unfamiliar expertise, strong institutional constraint, sparse evidence, or reader failure.

Keep three propositions separate:

1. **Core recoverability hypothesis:** bounded human-coherent reconstruction is possible and useful.
2. **Current detector hypothesis:** present model artifacts may differ statistically from human artifacts on some reconstruction dimensions.
3. **Alignment-direction hypothesis:** a better aligned system may intentionally become more human-invertible, erasing or reversing the detector signal.

A result can strengthen the first while killing the second. That is not a contradiction.

### 5.1 Rationalization versus reconstruction

A rationalization explains the evidence it was built after seeing. A reconstruction becomes more credible only when it constrains something independent of the evidence used to form it.

The phrase "predict held-out choices" should not be interpreted as unconstrained prediction of a person's future behavior. Phase 2.2 requires one of these bounded checks:

- recover an independently recorded process fact withheld from the reader;
- rank a later repair or revision that was not shown during reconstruction;
- identify which known counterfactual variant the inferred trajectory would make more probable;
- transfer the reconstruction to another artifact or segment made under the same known process.

Without an external constraint of this kind, a flexible reader can always mistake projection for understanding. This validation requirement remains even if the specific held-out-choice wording is retired.

### 5.2 Causal limits

The artifact-only reader may establish structural reconstructability. It cannot prove that the reconstructed human route was the maker's actual internal causal mechanism.

Process-aware studies can test correspondence where ground truth exists. Artifact-only outputs must retain the distinction:

- **supported human-coherent route**;
- **known process correspondence**;
- **causal process unknown**.

---

## 6. Anomalies, mistakes, and unexplained order

Anomalies are the most promising entry vector added by the curator pass, and the existing theory already contains the correct seed: the reader enters at an odd decision whose explanation is not yet available.

Do not call every unfamiliar construction a mistake. Use the following provisional ladder:

1. **Unexplained order:** a structured choice the reader cannot yet explain. It may reflect expertise, another goal, unfamiliar convention, accident, or error. This is the broad entry class and the likely bridge to interest and aesthetics.
2. **Apparent error:** the choice appears to work against the reader's inferred goal or trajectory.
3. **Confirmed error:** a process record, explicit correction, or controlled construction establishes that the choice missed the intended trajectory.
4. **Noticed and repaired:** the maker changes course in a way that exposes recognition and a preferred alternative.
5. **Noticed and concealed:** the maker overpaints, compensates for, reframes, or hides the failure. The concealment strategy becomes evidence about the maker's model of the reader and the goal being protected.
6. **Unnoticed isolated error:** the artifact preserves the miss without evidence of recognition.
7. **Repeated error or habit:** recurrence suggests a stable transition-map limitation, prior learning, or repeated goal pressure rather than one local accident.
8. **False mistake:** unfamiliar expertise or convention creates order the reader initially misclassifies as failure.

The target is **error handling**, not error rate. Error rates cluster, depend on opportunity, and are confounded by task difficulty. Handling exposes recognition, counterfactual preference, metacognition, and concealment.

The reader must be able to answer "ordered but unexplained" without forcing it into error. That category is necessary to keep unfamiliar corporate, technical, artistic, and cultural expertise from becoming false evidence of failure.

---

## 7. Phase 2.2 mission and exclusions

### 7.1 Mission

> **Validate trajectory-conditioned inverse reading on known answers: recover which proximal goal and trajectory constraints were realized, how expertise and context shaped the available route, and how anomalies were handled, while separating reconstruction from provenance and causal certainty.**

### 7.2 Primary questions

1. Can a bounded reader distinguish **realized trajectory constraints** from assigned, ignored, spontaneous, and contradicted constraints?
2. Can anomaly and repair evidence improve reconstruction of the maker's goal or trajectory beyond context-only and lexical-echo baselines?
3. Does declared expertise, tool access, and task context alter the reconstruction in the direction required by known construction rather than merely supplying a label cue?
4. Does the reconstructed account recover independent process evidence it was not fitted to?
5. Which parts transfer across reader and generator families, and which are reader-specific projection?

### 7.3 Explicit exclusions

Phase 2.2 does not:

- extract a person's values;
- wake the alignment program;
- infer actual lifetime effort from one artifact;
- prove causal access to a maker's mind;
- define human invertibility as uniquely human;
- use raw entropy, perplexity, or bits per word as a decision-count surrogate;
- optimize a binary detector before the representation passes its own gates;
- add a sixth theory file;
- require a single permanent scalar.

---

## 8. Sub-goals and dependencies

### 2.2A. Close the Phase 2.1 realized-choice boundary

Run the already prepared G159 recovery card under its frozen design. Do not rewrite the preregistration to fit this context.

Its narrow question is:

> Can the artifact-only reader distinguish verified executed instructions from uninstructed twins and unexecuted or spontaneous alternatives when lexical echo and consequence are controlled?

Required interpretation:

- A positive result supports recoverable realization evidence.
- A null narrows the final-artifact interface and may leave paired-delta or process-aware recovery intact.
- Neither result is human-versus-AI attribution.
- The amount comparison measures dilution or overlap in trace recovery, not total decision mass.

Land the result through the existing grind and curator-roll-up contract before beginning a new text battery.

### 2.2B. Replace the adjudication target and freeze the interfaces

Amend the evaluation contract and Phase 2 queue so that:

- `ADJUDICATION_SET_2_0.md` is marked **unfrozen and superseded as the decision ontology**, retained for history.
- Binary substantial-model-contribution policy remains a product-policy label only.
- The core representation is a trajectory reconstruction profile.
- Every field declares which of the three existing interfaces it requires:
  1. final artifact only;
  2. paired delta;
  3. process-aware audit.
- No field trained or validated with process metadata may silently appear in the final-artifact interface.
- A provenance label and a reconstruction score remain separate outputs.

Implement a typed internal schema with tests. Exact module names are agent-owned, but the conceptual fields below are required.

### 2.2C. Build the anomaly-handling ruler on known answers

Before collecting or reading natural text, construct a known-answer battery containing at least:

- no anomaly;
- unusual but intentional order;
- planted error left unnoticed;
- planted error repaired;
- planted error concealed or compensated for;
- repeated error or habit;
- a case where a secondary goal makes an apparent error rational under the full goal set.

Mechanism questions belong in Ghost Scale Sim or an equivalently explicit constructed world first. If implementation ownership remains separate, write a bounded exchange request through the existing simulation interface rather than duplicating the simulator inside Sounding Line.

The ruler must prove that it can:

- abstain or select no anomaly when none exists;
- distinguish unexplained order from confirmed error;
- distinguish repair from concealment;
- avoid reading recurrence as intentionality without a constraint control;
- recover the relevant goal or trajectory more accurately when valid anomaly evidence is supplied.

### 2.2D. Port anomaly handling to process-recorded text

Only after the ruler passes, build a text battery with recorded generation or revision histories. Use controlled families rather than open-ended adjudication.

The minimum families are:

1. issue introduced, then corrected;
2. issue introduced, then concealed or locally compensated for;
3. issue introduced and never noticed;
4. same issue repeated across opportunities;
5. unusual construction deliberately preserved because it serves a secondary goal;
6. matched ordinary text with no issue.

Every family needs:

- known target and handling state;
- evidence that the final artifact actually realizes that state;
- consequence-matched and echo-matched alternatives;
- final-artifact and paired-delta arms reported separately;
- a no-anomaly option;
- negative-class-heavy ruler validation before full adjudication;
- context-only and cheap-feature baselines.

The natural first output is a confusion matrix over handling states, not an aggregate "mistake score."

### 2.2E. Test context and trajectory-map conditioning

Construct matched cases where the same visible choice has a different interpretation under declared making conditions, including:

- forced by task or medium versus freely selected;
- tool available versus unavailable;
- relevant expertise supplied versus absent;
- familiar convention versus superficially similar unfamiliar convention.

The context card must not state the answer. It should alter what routes are feasible, not merely name the target class.

The test asks whether the reader changes its reconstruction in the direction required by the known transition map. It does not ask whether the prose becomes more persuasive.

Record the full reader-artifact-context cell. A reader that succeeds only when the context alone identifies the answer has failed the artifact contribution gate.

### 2.2F. Validate reconstruction outside the fitting evidence

For every reconstruction family that appears to work, require one independent constraint:

- a withheld process fact;
- an unseen repair;
- a held-out segment;
- a matched counterfactual artifact;
- or a second artifact from the same known process.

This is the boundary between a reconstruction and an attractive story. The test remains bounded to known answers and does not claim general prediction of a person.

Use at least one held-out reader or reader family where affordable. Reader agreement is reliability, not validity. Process correspondence and known-answer recovery remain the validity checks.

### 2.2G. Decide what survives into the detector program

Only after 2.2A through 2.2F have interpretable verdicts, decide whether any trajectory fields enter 2.0F.

A field is eligible only if it:

- passes its own known-answer ruler;
- adds artifact information beyond context and echo;
- has a declared input interface;
- has calibrated abstention;
- transfers beyond the construction family used to invent it;
- and makes errors different from the conventional detector substrate.

No eligibility result turns the field into proof of human authorship.

---

## 9. Required reconstruction profile

The internal representation should support the following structure. The implementation may normalize or split fields, but it may not discard the distinctions.

```text
reading identity
    artifact id
    reader id and configuration
    input interface
    declared context and its provenance
    candidate family and baseline family

proximal reconstruction
    ranked proximal-goal candidates
    evidence spans or artifact relations
    confidence and abstention reason

trajectory reconstruction
    ranked process or route candidates
    constraints inferred as active
    constraints treated as forced by context
    expertise and tool assumptions required by the route
    alternatives apparently suppressed

historical traces
    habit or recurrence evidence
    historical-shaping inference
    explicit statement that lifetime formation history is not identified

anomaly profile
    unexplained order
    apparent or confirmed error
    noticed / repaired / concealed / repeated / unknown
    evidence and competing explanation

realization
    assigned / realized / unrealized / spontaneous / ambiguous
    ground-truth source when known

validation status
    context-only margin
    echo or cheap-feature margin
    independent withheld-evidence result
    reader-family transfer status

claim boundary
    human-coherent route supported
    known process correspondence supported or unavailable
    provenance known from records or not inferred
    causal process unknown
```

### 9.1 Scalar outputs

If a compact score is needed, name the projection and preserve its components. Possible projections include:

- calibrated reconstruction margin over matched alternatives;
- proportion of independently recorded trajectory facts recovered;
- residual uncertainty after bounded reconstruction.

Do not name any of these "probability human" or "decision weight." The public substantial-model-contribution probability, if retained, is a separate classifier output trained on provenance labels.

---

## 10. Evaluation and ruler gates

Every preregistration and gate-bearing runner follows the existing DESIGN CHECK rule: expectation under the null, expectation under the alternative, and the failure direction are derived before the run, with exhaustive verdict bands.

At minimum, each new reader family must pass:

1. **No-signal gate:** no anomaly or no realized choice produces chance ranking or calibrated abstention, not a fluent invented process.
2. **Known-answer gate:** planted trajectory and handling states are recoverable under conditions where the answer is present.
3. **Artifact contribution gate:** the full reader beats the context-only arm.
4. **Echo gate:** the full reader beats lexical and semantic assignment similarity where those can carry the label.
5. **Negative adjudication gate:** validation is enriched for ignored, absent, and false candidates; evidence spans must discriminate rather than merely exist.
6. **Unfamiliar-order gate:** intentional but unfamiliar structure is not automatically labeled error.
7. **Forced-constraint gate:** medium, task, and tool constraints are not credited as freely chosen decisions.
8. **Observational-equivalence gate:** indistinguishable cases produce equal readings or an explicit dependence on supplied context.
9. **Interface gate:** final-artifact performance is never pooled with paired-delta or process-aware performance.
10. **Independent-evidence gate:** the reconstruction constrains a withheld known fact, repair, segment, or counterfactual beyond the evidence used to construct it.
11. **Reader-transfer gate:** reader-specific successes are labeled as such; no universal-reader claim follows from one model family.
12. **Fabrication gate:** an explicit none or underdetermined option is available wherever the known-answer space contains absence.

Report per-class confusion, calibration, and abstention. An aggregate can supplement these but cannot replace them.

---

## 11. Result routing

### 11.1 G159 realized-choice result

- **Positive:** realized choices leave artifact-only evidence under consequence- and echo-matched comparison. This licenses continued trajectory recovery, not provenance attribution.
- **Amount dilution:** trace overlap or reader capacity remains a measurement issue. Do not infer that additional decisions disappeared.
- **Null final-artifact / positive paired-delta:** the core narrows to a process-aware interface; the artifact-only claim weakens.
- **Echo wins:** the construction does not yet identify realized decision structure.

### 11.2 Anomaly-handling result

- **Ruler passes and text transfers:** anomaly handling becomes a validated entry channel for the Triple Inference.
- **Ruler passes, text fails:** the mechanism remains feasible in construction but unsupported on text.
- **Repairs work, concealment fails:** the reader detects explicit counterfactual evidence but not hidden recognition.
- **Unfamiliar order is mislabeled error:** the instrument is projection-heavy and cannot be used on open-domain artifacts.
- **Only paired deltas work:** error handling is a process trace, not a final-artifact trace under current resolution.

### 11.3 Context-conditioning result

- **Correct conditional shift beyond context-only:** supports the trajectory-map reading.
- **Context alone decides:** no artifact-side gain; the reader is restating supplied biography or tools.
- **Wrong shift under unfamiliar expertise:** documents a reader prior failure and strengthens the need for abstention.

### 11.4 Independent-evidence result

- **Transfers to withheld evidence:** supports structural reconstructability.
- **Fits shown evidence and fails withheld evidence:** the reader is rationalizing.
- **Human and model artifacts both transfer:** core recoverability survives; detector differentiation narrows or dies.
- **Highly directed model artifacts outperform ordinary human artifacts:** consistent with human invertibility as an optimizable artifact property and hostile to using it as direct provenance.

---

## 12. Documentation changes authorized by this package

The coding agent should perform a reconciliation pass, not a prose expansion pass.

### 12.1 Design and operational documents

- Archive this governing context at `docs/design/PHASE_2_2_CONTEXT.md` if that is the repository's established pattern.
- Amend the evaluation contract to replace the binary decision-adjudication primitive with the reconstruction profile while retaining binary policy only at the product layer.
- Mark the existing adjudication set unfrozen and superseded as an ontology. Preserve its examples as historical stress cases where useful.
- Add Phase 2.2 sub-goals and dependencies to `TODO.md` without renumbering existing identifiers.
- Update `docs/STATE.md` with the phase transition and the continuing 2.0F gate.
- Keep G159 under its existing identifier and record it as the Phase 2.1 closure boundary.

### 12.2 Five theory owners

No new theory file. Reconcile only the owners below, rereading `docs/theory/README.md` before each edit batch.

- **THE_TRIPLE_INFERENCE:** the reader begins with its own human model and adjusts under artifact and context; structural human invertibility is reader-relative and may be produced by an aligned model; causal correspondence requires process evidence.
- **THREE_COGNITIVE_LAYERS:** expertise is the trajectory or transition map, not a generic policy state; attention promotes a proximal region but its allocation law remains open; do not hard-code serial switching. The Thousand Brains reference-frame adjacency may be cited only after a source-level read and with its theory-versus-evidence status explicit.
- **DECISION_TRACES:** distinguish unexplained order, apparent error, confirmed error, repair, concealment, unnoticed error, repetition, and false mistake. Keep error handling separate from error rate.
- **READER_HEURISTICS:** anomaly is the broad entry cue; a mistake is a sharpened, evidence-supported subclass. Add the self-model/projection hazard and the requirement that reconstruction constrain independent evidence.
- **ALIGNMENT:** no substantive edit. A note elsewhere may state that aligned systems could optimize human invertibility, but the dormant file does not wake.

Update hypothesis rows and their afterwords only where the new curator ruling changes the standing interpretation. Do not manufacture result statuses for untested distinctions.

### 12.3 README

Do not rewrite the public README merely because the theory moved. Its current map is the source of the correction. A public claims update waits for a Phase 2.2 result or for a direct contradiction between the README's current binary-wedge language and the frozen evaluation contract.

---

## 13. Curator interaction rule for load-bearing theory work

Integrate the smallest enforceable version of this rule into the authoritative agent workflow. Do not replace the existing grind.

```markdown
<curator_first_theory_loop>
- Report the theory-group consequence and classify the change before implementation detail.
- When a result changes a load-bearing definition, do not supply a completed synthesis or queue expansion first.
- Ask no more than three interpretation questions and provide hostile cases without a preferred answer.
- Wait for the curator's rough verbal or written prior unless he explicitly delegates the theory choice.
- Preserve the curator's account, the analyst's additions, result-forced constraints, literature imports, and unresolved tensions as distinguishable sources.
- Only after ratification write the operational handoff.
- Routine implementation remains agent-owned. Mission, ontology, public meaning, value inference, and possible theory death escalate.
</curator_first_theory_loop>
```

This is a theory-change interrupt, not a requirement to stop for every study or coding decision.

---

## 14. Bounded research imports

### 14.1 Thousand Brains reference frames

The Thousand Brains work is a closer adjacency than generic brushstroke simulation. Its project paper explicitly extends reference-frame representations from environments and physical objects to abstract concepts, hierarchical goal states, and theory-of-mind capabilities. Use it as a candidate architecture and engineering comparison, not as settled evidence that the human brain implements the full abstract claim. The implementation currently relies heavily on explicit 3D graph models and acknowledges biological simplification.

Primary source: [The Thousand Brains Project: A New Paradigm for Sensorimotor Intelligence](https://arxiv.org/abs/2412.18354).

The useful friction to record is:

- their reference frames organize features at locations and actions through movement;
- Sounding Line's trajectory map organizes feasible routes, goals, and recoverable maker structure;
- the possible bridge is structured movement through conceptual spaces;
- the unearned leap would be declaring the two the same mechanism.

### 14.2 Attention and switching

The task-switching literature supports switching costs and separate control of focus and flexibility. It does not license a universal claim that all simultaneous goal satisfaction is implemented as serial switching. Preserve serial focal promotion as a candidate account and leave background constraint satisfaction open.

Useful source-level orientation: [Egner, “Principles of cognitive control over task focus and task switching”](https://doi.org/10.1038/s44159-023-00234-4).

### 14.3 Information theory

Do not build a raw entropy detector in Phase 2.2. Existing probability-geometry detectors already exploit more than perplexity, and entropy varies with genre, model, sampling, semantic complexity, and editing.

The only information-theoretic direction compatible with this phase is conditional and hierarchical:

> Does adding a bounded trajectory reconstruction reduce the residual description of independently withheld evidence enough to justify the reconstruction's added complexity?

That can be explored after the profile and withheld-evidence gate exist. It is not a prerequisite for the anomaly ruler.

### 14.4 Rewritten-text benchmark correction

ARB is not itself a detector. It is a matched benchmark showing that existing detectors which catch direct model generation often fail on human-authored text rewritten by a model. FastDetectGPT fell from 91.2% recall on direct model text to 30.8% on human-to-model rewrites at 1% human false positives; Binoculars fell from 93.5% to 15.1%. The labels are known because the benchmark authors constructed the histories. A final artifact does not reveal that it belongs to the hard class merely because a benchmark reports the class-level failure.

Primary source: [ARB: A Matched Authorship-Rewriting Benchmark Dataset for AI-Text Detector Evaluation](https://arxiv.org/abs/2607.29539).

Its Phase 2.2 consequence is that content origin and surface realization must remain separate. It strengthens the need for mixed-process records and weakens any claim that current direct-generation detector performance transfers to realistic revision.

---

## 15. Pre-mortem

Phase 2.2 has failed if any of the following occurs.

1. **Projection is mislabeled recovery.** The reader produces human-shaped stories that do not constrain independent evidence.
2. **Unfamiliar order is mislabeled error.** Corporate, technical, cultural, or artistic expertise outside the reader's competence becomes a false mistake signal.
3. **Context states the answer.** Tool or expertise cards create an easy semantic-classification task instead of changing feasible trajectories.
4. **Process metadata leaks into the artifact interface.** A field appears successful only because it consumed drafts, assignments, or realization labels unavailable at inference.
5. **The anomaly score becomes another aggregate.** Repair, concealment, repetition, and no-anomaly errors disappear inside one number.
6. **Serial attention is hard-coded as truth.** The instrument can only find the switching pattern it assumed.
7. **Human invertibility is relabeled human provenance.** Highly directed or aligned model artifacts become "false negatives" when the core instrument is actually reporting correctly.
8. **The reader adjudicator is trusted before negative validation.** The G158 yes-machine failure repeats under a new prompt.
9. **A raw entropy proxy replaces the trajectory model.** The phase returns to a surface detector with theoretical language added afterward.
10. **Theory documents expand without sharper ownership.** The same idea is repeated across files, the five-file map blurs, and a future agent cannot tell what changed.
11. **The detector stack resumes because one narrow gate passes.** Complementarity and representation validity remain separate gates.
12. **A constructed-world success is reported as a human mechanism.** Simulation validates a ruler or feasibility regime, not human cognition.

---

## 16. Immediate execution order

1. Confirm the repository head and perform the reload in §2.
2. Run and land the frozen G159 recovery battery. Do not change its target or reinterpret it as attribution.
3. Reconcile the evaluation contract, Phase 2 state, and adjudication-set status around the trajectory profile.
4. Implement the typed reading schema and interface guards with unit tests.
5. Build the anomaly-handling known-answer ruler in the constructed environment.
6. Run every ruler gate before generating a natural-text anomaly corpus.
7. Build the process-recorded text battery only after the ruler passes.
8. Add context and tool-conditioning arms with context-only controls.
9. Add the independent-evidence test.
10. Produce a curator brief at theory-group altitude and decide which, if any, fields are eligible for the detector stack.

The coding agent may reorder independent implementation work, but it may not move natural-text inference ahead of its ruler or detector fusion ahead of representation validation.

---

## 17. Completion conditions

Phase 2.2 is complete when:

- G159 has an honest landed verdict.
- The binary adjudication set is no longer blocking or defining the core representation.
- The three input interfaces are frozen and structurally enforced.
- The trajectory reconstruction profile exists as a tested schema.
- The anomaly-handling ruler can distinguish no anomaly, unexplained order, error, repair, concealment, and repetition under known answers, or the failed distinctions are explicitly retired.
- At least one process-recorded text battery has run with negative validation, context-only, echo, forced-constraint, fabrication, and interface controls.
- Every apparent reconstruction has faced an independent-evidence check.
- Reader-specific projection is reported rather than averaged away.
- The five theory owners, state, queue, and findings record agree on the verdict.
- A curator-facing phase brief states what strengthened, narrowed, died, or remained infrastructure.
- The detector program receives either a justified eligible representation or an explicit ruling that Phase 2.2 produced none.

The phase does not require solving value recovery, attention allocation, actual cognitive effort, or unique causal inversion. It requires a ruler that can fail for interpretable reasons while preserving the trajectory model the project is actually trying to test.
