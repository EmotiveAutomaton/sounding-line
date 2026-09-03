# Sounding Line Stage 7 Theory Reconciliation Errata

**Status:** APPLIED 2026-09-02 and ARCHIVED as the provenance record (the curator's 2026-08-31
filing ruling). Implementation commit: pending; the working tree carries the application and
is committed on the curator's word (the completion report is in FINDINGS L331).

**Prepared:** 2026-09-02 from the curator's 2026-09-01/02 walkthroughs and the Stage 6
implementation audit.

**Intended baseline:** Sounding Line `5936b0b` or a descendant that has not independently changed
the target passages.

**Scope:** Apply small canonical corrections to four existing theory owners. Preserve every prior
curator quotation exactly. Add only the reconstructed quotations supplied below. Do not create a
sixth theory file, alter locked experiments, rewrite Stage 6 raw outputs, or promote any new result.

## 1. Implementation contract

Before editing, read `CLAUDE.md`, `docs/theory/README.md`, all five files in `docs/theory/`, the
affected Stage 6 entries in `FINDINGS.md` (L315 through L326), and
`docs/design/PHASE_2_4_STAGE_7_CONTEXT.md` sections 1 through 3.

Apply only these canonical theory files:

1. `docs/theory/THE_TRIPLE_INFERENCE.md`
2. `docs/theory/THREE_COGNITIVE_LAYERS.md`
3. `docs/theory/DECISION_TRACES.md`
4. `docs/theory/READER_HEURISTICS.md`

Review but do not change:

- `docs/theory/ALIGNMENT.md`
- `docs/theory/README.md`
- `docs/theory/essays/`

The transcript is noisy. The quotations in this errata reconstruct the curator's competent intended
claim after removing false starts, repetition, and obvious recognition errors. Do not restore the
raw transcript wording. Mark every new quotation with the supplied provenance line.

Whenever a hypothesis table changes, rewrite its afterword in the same edit. Do not change an OPEN
theory claim merely because it lacks evidence. The corrections below withdraw only interpretations
that the Stage 6 audit invalidated.

## 2. Executive ruling

This pass changes the theory at six joints:

1. **Operational definition.** Sounding Line reconstructs a revisable maker model from an artifact
   and tests it against hidden future or counterfactual behavior.
2. **Expertise and process.** Expertise `K` is the maker's learned transition/action model. Process
   `tau` is the realized path through it. They are not separate copies of the same quantity.
3. **Maker-relative possibility space.** External context, maker beliefs, maker-interpreted context,
   and the maker's subjective action set must remain distinct. An objectively available action was
   not necessarily available to the maker.
4. **Two-timescale attention evidence.** A dated artifact can preserve one comparatively sharp
   present allocation of attention plus a diffuse, anterior mixture of earlier attention and choice
   compressed through expertise. The historical component is not a second precisely dated point.
5. **Preference ontology remains open.** Stable parameters of context-conditioned attention may be
   preference itself, or attention may remain evidence for a deeper motivational organization `V`.
   A vector or slope is only geometric shorthand until coordinates and uncertainty are specified.
6. **Stage 6 interpretation is suspended.** Hidden future and generator dependencies void the
   architecture ranking, reader-boundary conclusion, M14 realization result, M15 semantic-invariance
   result, value and attention-history interpretations, and foraging interpretation. The CoAuthor
   result is invalid because the loader recorded only dismissals. Exact supplied-family likelihood
   selection survives only as known-law system identification.

## 3. Exact canonical changes

### 3.1 `docs/theory/THE_TRIPLE_INFERENCE.md`

#### A. Add the operational definition near the head of the file

Insert as unquoted canonical prose after the opening canonical-claim paragraph:

> **Operational definition, ratified 2026-09-01.** Sounding Line is an artifact-grounded
> inverse-generative system that reconstructs a revisable model of how a maker transformed their
> perceived possibilities into an artifact, then tests that reconstruction through hidden future
> and counterfactual behavior.

This is ratified project language. It is not a result claim.

#### B. Correct what a reader may bring to the artifact

After the existing expert and close-friend quotation in section 1, insert:

> You can arrive with expertise already, and you can arrive with strong knowledge of who the maker
> is and what they want. The one thing you have to infer on the spot is the proximal goal, and it is
> usually the easiest inference to make.

*2026-09-01 walkthrough; spoken wording lightly reconstructed.*

Keep the surrounding prose modest: domain expertise and maker familiarity are possible priors, not
guaranteed recovery. The realized process remains episode-specific even when useful expertise is
already present.

#### C. Expand the maker-model objects

Revise the object table so it contains these distinctions:

| object | canonical meaning | timescale |
|---|---|---|
| proximal goal `G` | what the maker is locally trying to accomplish | episode-local |
| process `P`, realized as `tau` | the particular decisions and actions that produced the artifact | artifact-local |
| expertise `K` | the maker's learned transition model, shaping reachable actions and expected consequences | cross-episode, domain-relative |
| drives `D` | currently active motivational pressures or primitive constraints | state-dependent |
| values `V` | persistent organization of tradeoffs among goals, drives, and trajectories | longitudinal |
| external context `C_ext` | commission, coercion, medium, audience, tools, and objective constraints | episode-local |
| maker beliefs `B` | information the maker possessed and what they believed | episode-local, history-shaped |
| maker context `C_m` | external context interpreted through the maker's beliefs and expertise | episode-local |
| subjective action set `A_tilde` | alternatives the maker believed were available after context and expertise shaped the possibility space | step-local |

Immediately after the table, insert:

> Sounding Line has to infer the information the maker possessed and believed, and the actions they
> thought were available. Those belong in the maker model: external context as transformed through
> the maker's beliefs and expertise.

*2026-09-01 walkthrough; spoken wording lightly reconstructed.*

The prose below the table must explicitly dissolve three conflations:

- expertise is the transition model; process is the realized path;
- external context is not maker-interpreted context;
- drives are not values.

Update the table afterword to call these identifiability constraints and to state that none has yet
been isolated by a clean designed comparison. Preserve the existing evidence claim about the
timescale asymmetry.

#### D. Replace the minimal generative schematic

Use this loose schematic in section 2:

```text
C_m,t = phi(C_ext,t, B_t, K_t)       maker-interpreted context
A_tilde,t = afford(C_m,t, B_t, K_t)  actions the maker believes are available
G_t = f(V, D_t, C_m,t, alpha_t)      the locally governing goal
a_t ~ pi_K(a | A_tilde,t, G_t, H_t)  one action through the expertise transition model
tau = (a_1, ..., a_T)                the realized process path
K_t+1 ~ L(K_t, E_t, alpha_t, C_m,t) + epsilon_t
                                     lossy consolidation into later expertise
O = h(tau, C_ext,1:T)                the medium's lossy artifact record

reader R approximates q_R(G, tau, V, D, K, H, B, A_tilde, C_m | O, C_ext)
```

Define `alpha` as time-varying attention, `H` as control/history residue, `E` as experienced
material, `L` as consolidation and learning, and `epsilon` as interference or forgetting. State:

- `K` is the transition model and `tau` the realized path;
- consolidation encodes and compresses the historical record;
- interference and forgetting are error in that record;
- attention must be measured independently of its later effect on `K`, or the account is circular;
- the posterior belongs to the reader-artifact-context relation, not directly to the maker.

#### E. Preserve the prospective understanding rule but withdraw its Stage 6 support

Where section 2 currently says Stage 6 measures the prospective prediction rule, replace that claim
with:

> Stage 6 attempted to instrument this rule, but its hidden dependencies voided the interpretation
> (M-S6). The rule remains a prospective criterion, not a claim that language is the required
> representation of the maker state.

Replace the `M-S6` result status with `VOID AS EVIDENCE FOR THE NAMED CLAIM`. Its status must state:

- the shared predictor accessed complete `target_actions`, future events and length, `stop_shift`,
  and exact transition and utility laws;
- I05 supplied prose labels rather than the full operative state;
- M14 received constructor variables;
- M15 followed hypothesis tags while ignoring semantic text;
- exact-likelihood selection survives only as known-law system identification;
- no architecture ranking, reader-boundary, realization, semantic-invariance, or reader-capacity
  conclusion is licensed.

Rewrite the table afterword so the Stage 5 reader failures retain their original scope, while the
Stage 6 tournament supplies no constructive comparator. End with the confidence distinction:

> Confidence: the Stage-5 reader boundary is one bad test away; the Stage-6 architecture
> interpretation is instrument-dead.

#### F. Add the two-timescale attention and preference proposal

In section 5, after the existing dated-trajectory quotations, insert:

> An artifact gives you two different kinds of evidence: a probabilistic distribution of previous
> attention, compressed lossily through expertise, and a record of what the maker chose to attend to
> when the artifact was created. Because we can separate current from past, we get a much richer
> preference estimate: not a single point, but a weighted trajectory.

> If someone repeatedly pays costs to redirect effort away from an old trained tendency, that
> redirection is a preference expressed currently. The trained tendency may preserve an older
> history; the present allocation records what they are trying to become.

> I am not assuming that there has to be a separate latent value field. A context-controlled
> probabilistic mapping of where attention chooses to focus may itself be the latent preference.

*2026-09-01/02 walkthroughs; spoken wording lightly reconstructed.*

Then add the following constraints in canonical prose:

- One artifact supplies one dated present allocation plus an anterior, context-filtered mixture
  carried by expertise. It does not supply two equally dated points.
- Weak relative-age cues may exist inside the historical mixture, but they do not precisely date it.
- Several dated artifacts can make their mixtures constrain one another and narrow the posterior
  over directions of change.
- Present costly redirection is present preference evidence even when automatic capture reflects
  older training or pressure.
- Preference may be stable parameters of a context-conditioned attention-allocation policy, or that
  policy may be evidence for deeper `V`. Keep both ontologies live.
- A vector or slope is shorthand until coordinates, a time basis, and uncertainty are specified.
- Direction earns a preference interpretation only by predicting later costly choices beyond
  context, local goal, habit, and expertise.
- Homeostatic return can express a stable preference, so movement alone is not the target.

Replace the `V-S6` result status with `VOID AS CURRENT EVIDENCE FOR THE NAMED CLAIM`. State that the
value cards inherit the dependency-tainted predictor, several questions duplicate one planted
mapping or statistic, and the changed-context target exposes hidden generator structure. License no
Stage 6 conclusion about breadth, search, value trajectory, preference, or changed-context choice.

Rewrite the section afterword to preserve the four existing value accounts, add the dated trajectory
as a separator rather than a fifth account, keep the attention-policy ontology unresolved, and state
that Stage 6 contributes no reader-side evidence. No real maker's values have been recovered.

### 3.2 `docs/theory/THREE_COGNITIVE_LAYERS.md`

#### A. Add the expertise correction

After the existing 2026-08-30/31 expertise-history quotation cluster, insert:

> The transition model is just expertise. You can already have expertise when you walk up to
> something; that is one of the pieces that changes the rest of the equation.

> All the times you have been in a situation like this, what did you choose to attend to, and what
> decisions did you make while attending to it? That is what expertise compresses.

> If you make those decisions repeatedly, your expertise bends in a different direction. You become
> your choices in a lot of ways.

*2026-09-01 walkthrough; spoken wording lightly reconstructed.*

Revise the following canonical prose to include every constraint below:

- Expertise is the maker's learned transition model; a realized process is one path through it.
- A reader may arrive with domain expertise before seeing the artifact.
- Expertise is a lossy, consolidation-transformed record of prior attention and choice under prior
  context, not an intact historical log.
- Consolidation is encoding and compression. Interference and forgetting are error.
- Transfer and unequal learning change which contexts and repetitions bear on the present case;
  they do not require a separate object beside expertise.
- Repeated choices reshape the later transition model.
- Goal selection and attention allocation remain distinct operations.
- The formation hypothesis is circular unless attention is measured independently.

#### B. Withdraw the Stage 6 architecture and attention-history readings

Replace both affected rows:

- `C-S6`: `VOID AS CURRENT EVIDENCE FOR THE NAMED CLAIM`. The event reader and controller comparison
  inherit hidden future and generator-law dependencies. License no architecture recovery,
  controller comparison, or switching conclusion.
- `A-S6`: `VOID AS CURRENT EVIDENCE FOR THE NAMED CLAIM`. The event and changed-context reads inherit
  the common predictor's privileged state. The dated-history contrast does not validate the rest of
  the family. License no Stage 6 attention-history, expertise-versus-goal, or changed-context
  inference.

Rewrite the table afterword around the surviving theory rather than the void measurements. It must
state that expertise is the transition model, repetition reshapes it, consolidation compresses it,
and interference corrupts it. The scaffold and expertise-formation account remain logic-only. The
Stage 6 reader instrument is instrument-dead.

### 3.3 `docs/theory/DECISION_TRACES.md`

#### A. Withdraw the Stage 6 foraging interpretation

In section 1, replace the claim that Stage 6 instruments the exploration standard. State instead:

- the F track attempted the test;
- the outcome read inherited hidden future and generator-law dependencies;
- several questions reduced to one planted statistic;
- Stage 6 supplies no evidence that a reader separates exploration, error, habit, and hidden goal;
- the outcome-sufficient exploration rule remains a classification standard, not a result.

#### B. Add the two-timescale artifact trace

In section 3, after the opening leaked/emblematic quotation cluster, insert:

> An artifact gives you two different kinds of evidence. It gives you a probabilistic distribution
> of previous attention, compressed lossily through expertise, and it gives you a record of what the
> maker chose to attend to when the artifact was created.

*2026-09-01/02 walkthroughs; spoken wording lightly reconstructed.*

After the paragraph on automaticity as compiled reachability, add canonical prose with these points:

- Automatic fluency, omissions, and deformations can carry a graded historical mixture from related
  prior contexts.
- Present costly allocation, including effort spent resisting or redirecting an old tendency,
  supplies a more sharply dated trace.
- The present action may express preference while the automatic tendency records older pressures.
- Neither channel identifies one cause or date for every component of the historical mixture.
- Multiple dated artifacts can progressively narrow the uncertainty.
- Artifacts are privileged because they persist and accumulate decisions, not because other behavior
  is excluded. Speech, gesture, tool use, and edits can carry the same trace classes.
- Keep the preference interpretation in `THE_TRIPLE_INFERENCE.md` section 5. This file owns the
  observable traces only.

Update the section afterword to say that no clean instrument has yet separated the dated present
allocation from the expertise-borne historical mixture inside one artifact. The two-timescale trace
is untested, logic only, and does not inherit evidence from existing automatic-channel results.

### 3.4 `docs/theory/READER_HEURISTICS.md`

Replace the Stage 6 archaeological-boundary paragraph in section 10 with a corrected interpretation
containing all of the following:

- The narrow ScholaWrite result survives: the reader under-runs previous-label, `-0.575` at 144
  units (`T01/x4`, L319).
- The narrow drawing result survives: the reader under-runs the placement prior, approximately
  `-0.39` at 2448 units (`T04/x1`, L323).
- The CoAuthor result is invalid. The loader consumed `suggestion-select` as a document delta before
  recording acceptance, so all 686 scored Stage 6 decisions were dismissals. The perfect
  reconstruction gate did not validate the intended document state.
- The constructed-world comparator is dependency-tainted. It cannot show that the ecological gap
  belongs to evidence rather than machinery.
- The Stage 6 run therefore cannot close every real-record path or establish a general reader
  boundary.
- The surviving claim is only that cheap sequential priors beat these frozen readers on two corpora.
  CoAuthor awaits repaired event semantics, and all three await a clean artifact-visible comparator.

Do not alter the general calibration rule immediately above it: a reconstruction must constrain
evidence that did not build it.

## 4. Mandatory claim ceiling

The edited theory must not claim that:

- an artifact contains a precisely dated record of every earlier attention state;
- attention allocation has been established as identical to preference;
- a direction of attentional change proves a value change;
- a single artifact establishes a preference trajectory;
- movement away from a trained tendency proves durable change without later costly choice;
- expertise is an intact memory log or a separate latent beside the transition model;
- objectively available actions were subjectively available to the maker;
- Stage 6 ranks architectures or identifies a reader-weighing bottleneck;
- Stage 6 validates semantic invariance, changed-context realization, stopping, value inference,
  attention-history inference, or foraging inference;
- the Stage 6 CoAuthor run measures acceptance behavior;
- the surviving ScholaWrite and drawing negatives establish a universal ecological boundary.

## 5. Visual-model constraint

If the README image is later revised, preserve this distinction:

- historical attention appears as a diffuse weighted cloud, distribution, sediment, or confidence
  band;
- attention at artifact creation appears as a comparatively sharp dated point;
- several artifacts narrow a curved posterior trajectory with an uncertainty ribbon;
- any forward continuation is dashed or probabilistic;
- secondary traces from speech, gesture, tools, and edits may feed the same inference;
- never depict the historical mixture as one exact old point or the trajectory as certainty.

This is a visual specification only. Do not generate or replace a README image as part of this
errata unless the curator separately supplies or approves the asset.

## 6. Required verification

After implementation:

1. Run `python tools/theory_lint.py`.
2. Run `python tools/verify_locks.py`.
3. Run `git diff --check`.
4. Confirm no pre-existing blockquote line was removed or altered.
5. Confirm every changed theory table has a rewritten afterword.
6. Confirm no suspended Stage 6 interpretation survives elsewhere in the five theory files.
7. Confirm `ALIGNMENT.md`, theory essays, locked specifications, and Stage 6 raw results are
   unchanged.
8. Change this file's status from `READY FOR APPLICATION` to `APPLIED`, adding the application date
   and implementation commit.

## 7. Completion report

Return a short report containing:

- files changed;
- reconstructed quotation blocks added;
- Stage 6 claims withdrawn;
- surviving narrow results;
- lint, lock, and diff-check outcomes;
- any conflict with newer theory prose that prevented an exact application.
