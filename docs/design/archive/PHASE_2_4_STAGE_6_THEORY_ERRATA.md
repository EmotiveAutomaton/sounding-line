# Sounding Line Stage 6 Theory Update Errata

**Status:** APPLIED 2026-08-31 and ARCHIVED as the provenance record (the curator's
2026-08-31 filing ruling; the 2026-08-30 first drop applied the shared four-joint subset,
this update added the rest)

**Intended baseline:** `origin/main` at or descending from `b31ffda`

**Reference implementation:** local commit `bff8be0` (`Apply Stage 6 theory reconciliation`)

**Scope:** Make small canonical changes to three theory owners and add this pass's provenance
record. Do not reclassify results, add a fourth inference, alter alignment objectives, modernize
historical essays, or absorb unrelated Stage 6 research-program drafts.

## 1. Implementation contract

Before editing, read the repository instructions, `docs/theory/README.md`, and the three target
files in full. Preserve unrelated working-tree changes. Apply only these files:

1. `docs/theory/THE_TRIPLE_INFERENCE.md`
2. `docs/theory/THREE_COGNITIVE_LAYERS.md`
3. `docs/theory/DECISION_TRACES.md`
4. `docs/design/PHASE_2_4_STAGE_6_THEORY_ERRATA.md` — add this provenance record

The audio transcript is a noisy source. The block quotations below preserve the curator's intended
spoken claims after removing repetitions, false starts, and obvious recognition errors. Do not
strengthen them further or silently convert them into established findings.

## 2. Executive ruling

This pass changes the theory at four joints:

1. A mental-state label is a lossy pointer. Understanding requires a context-realized maker state
   that improves prospective prediction.
2. Proximal goal, attention, and expertise remain coupled but are not aliases.
3. Current foreground goals and lagging expertise can provide differently dated evidence about
   value change, but only through later discriminating behavior.
4. An unusual act counts as epistemic exploration only when it obtains information or belongs to a
   probe sequence capable of doing so.

These are theory clarifications and evaluation rules. They do not alter the Stage 5/5R
measurements, establish a human control architecture, or promote value recovery.

## 3. Exact canonical changes

### 3.1 `docs/theory/THE_TRIPLE_INFERENCE.md`

#### A. Extend the minimal generative account

In the existing schematic near the beginning of section 2, add expertise formation after the
process-policy line:

```text
K_t+1 ~ L(K_t, E_t, A_t, C_t) + epsilon_t
                             expertise is updated through a lossy consolidation map
```

Define `E` as experienced material, `L` as a consolidation-and-learning transform, and `epsilon`
as interference or forgetting. State explicitly that this records the curator's live
expertise-formation hypothesis, not an established identity. Attention must be specified
independently of its later effect on expertise; otherwise the proposal is circular.

#### B. Clarify why goal remains a separate inference

After the passage that says Sounding Line reports goal, process, and a route the reader could use
separately, insert:

> Strictly speaking, flawless expertise and context could let you reconstruct the process without
> first recovering the goal. But the goal is needed to understand the creator's trajectory and to
> decide what is worth taking up. A book by a torturer and a book by an ex-torturer should not be
> read in the same way.

*2026-08-31 walkthrough; spoken wording lightly reconstructed.*

Follow it with this ruling:

> Goal is therefore neither the mandatory first step of every process reconstruction nor a
> redundant label. A sufficiently complete conditional policy can predict production without
> explicitly naming the current goal. Goal remains a separate inference target because it
> identifies present motivational direction, helps distinguish inherited expertise from current
> correction, and informs later character and uptake judgments. Reconstruction accuracy,
> character evaluation, and uptake must still be scored separately so that a preferred maker
> model cannot make itself appear more accurate.

#### C. Replace label-level understanding with predictive realization

After the existing paragraph describing the reader's distribution over a maker's possible process,
add a subsection introduced as the 2026-08-30 pass, with provenance pointing to this errata file.
Preserve these quotations:

> If you had all three pieces, you should be able to recreate the activity quite precisely. If the
> labels sound insightful but do not improve the prediction, then no, the maker has not been
> understood.

> A candidate is only a small piece of the full prediction. To use it, I have to align it with an
> existing structure that can predict the whole artifact. The words lose precision, and the
> artifact re-centers what the candidate actually means in context.

> Can you predict stopping? Yes. I think you should be able to predict stopping and the next edit.
> Those are two things that would demonstrate understanding.

*Spoken wording lightly reconstructed.*

Then add the canonical rule:

> **A short mental-state label is a pointer, not the reconstructed maker state.** Its operative
> meaning must be re-centered in the whole artifact, context, and possibility space until it
> entails a distribution over the maker's remaining decisions. Different descriptions may realize
> the same predictive state, and the same words may realize different states for different makers.
> A longer rationale does not solve this by itself. The representation may be language, structured
> slots, a program, or a latent vector. What earns credit is prospective constraint on a hidden
> continuation, next edit, stopping decision, or changed-context choice.

In the Stage 5 empirical summary, add that naming the intended latent or producing a coherent
explanation does not establish understanding when even a reader handed the true latents cannot use
them to predict what happens next. Mark the maker-state realization requirement as an open
architectural proposal, not a reinterpretation of the failed reader.

#### D. Add a prospective rule for value-change trajectories

Immediately before the section's current state-of-claim paragraph, insert:

> The best evidence that the value changed, rather than merely becoming better concealed, would be
> evidence elsewhere that the maker's foreground goals are different. The historical tendency
> preserved in expertise may give you an older data point. Together they give you a trajectory.

> The slope is between inherited, expertise-shaped tendencies and the maker's current proximal
> goals. Future edits should reveal whether that mismatch is a direction of change.

*2026-08-30/31 walkthroughs; spoken wording lightly reconstructed.*

Then add:

> **Diagnostic value evidence may arrive after an initially ambiguous choice.** An
> accuracy-oriented and a prestige-oriented maker can cite the same prestigious source.
> Discovering later that the source is wrong creates a separating opportunity: direct correction
> and argument repair compete with retention, hedging, and reputation management. Until such an
> event, the honest output is a posterior over behaviorally compatible motivational organizations.
> A changed foreground goal can be evidence of present direction when it predicts later choices,
> while lagging expertise can preserve an older tendency. Their mismatch is only a candidate
> direction of change, not literally a linear slope: temporary context, coercion, concealment,
> relearning, and nonlinear return toward an older mean remain rivals. It earns a trajectory
> interpretation only by predicting later edits, stopping, or changed-context choices.

In the state-of-claim paragraph, say that this adds a **prospective separator**, not a fifth account.
No real maker's values have been recovered by this addition.

### 3.2 `docs/theory/THREE_COGNITIVE_LAYERS.md`

#### A. Remove the goal-attention identity

Replace the paragraph beginning `Goal is not a fourth level` so its operative prose reads:

> A proximal goal is a locally governing control target selected under values, drives, context,
> expertise, and attention. Its effects can be expressed through every functional level. Other
> motivations may remain as maintained intentions or learned constraints without governing focal
> control. Goal is therefore not a fourth address, but neither is it identical to the attention
> allocated while pursuing it.

Preserve the existing curator quotation that rejects a fourth level.

#### B. Add the narrowed expertise-formation hypothesis

After the existing quotation cluster about expertise and background goals, add:

> Proximal goal is not identical to attention. I think the relationship between proximal goal,
> attention, and expertise is complex and interesting in a way that we have been glossing over.

> Expertise is an imperfect record of previous attention given prior context. Consolidation is the
> encoding layer for that record; interference contributes noise.

*2026-08-30/31 walkthroughs; spoken wording lightly reconstructed. The earlier shorthand remains
historical evidence; these statements narrow its identity claim without removing its example.*

Replace the following expertise paragraph with a formulation that contains every constraint below:

- Expertise is the learned transition structure through which all three functional levels can
  constrain action.
- The curator's live formation hypothesis is that expertise is an imperfect,
  consolidation-transformed record of prior attention under prior context.
- Practice, feedback, and instruction affect what is attended and repeated.
- Constraints, tools, opportunity, and embodiment help define the context in which that attention
  occurred.
- Consolidation compresses and reorganizes the record; interference adds noise.
- The hypothesis is testable only if attention is measured independently. Defining attention as
  whatever later changed expertise is circular.
- The same attended material can produce different expertise, and the same expertise can later
  direct attention away from the current goal.
- Goal selection and attention allocation are different operations.
- `Compiled decision structure` describes formation history, not intact storage of past decisions.
- The functional object remains the trajectory constraint.

#### C. Preserve control-architecture rivals

Replace the paragraph on goal drift and switching with:

> Human goals can genuinely drift while attention relocates, but neither movement entails the
> other, and surface movement is not sufficient evidence of goal drift. The same persistent
> concern can appear and disappear as opportunity and expertise change its local expression. The
> curator's live control candidate is one foreground goal with rapid switching. Maintained
> intentions and compiled habit can still alter behavior while another goal is focal, and
> concurrent control remains a rival. Serial switching is therefore a candidate description of
> focal control, not a frozen mechanism.

Update `G26` to read:

> A goal is a weighting across all levels rather than a level or attention state of its own.

Rewrite the table interpretation so it keeps **goal, attention, and expertise distinct but
coupled**. Mark the entire scaffold as logic-only and untested; do not imply anatomical settlement.

### 3.3 `docs/theory/DECISION_TRACES.md`

At the end of the anomaly-trace definitions, before the hypothesis table, insert:

> If you are going to explore, you need to explore all the way. You need to see the result one way
> or another.

*2026-08-30 walkthrough; spoken wording lightly reconstructed.*

Then add:

> **An unusual action is not yet a trace of epistemic exploration.** The exploratory account needs
> an outcome-sufficient commitment or an escalating probe, an observation capable of reducing the
> maker's uncertainty, and later stopping or policy change consistent with what was learned. An
> ordinary error may be repaired before it reveals an outcome. A familiar technique used in the
> wrong context may run farther because it is weakly monitored. A hidden artifact-level goal should
> integrate the unusual action with wider structure. These rivals can remain observationally
> equivalent in a finished artifact, in which case the trace stays indeterminate.

In the section's evidence summary, add that the exploration discriminator now has a trace standard,
but no artifact reader has yet separated these four rivals. Do not promote this ruling to a result.

### 3.4 `docs/design/PHASE_2_4_STAGE_6_THEORY_ERRATA.md`

Add a concise provenance record containing:

- the four-part executive ruling in section 2 above;
- the reconstructed quotations in sections 3.1–3.3;
- a file-by-file record of the canonical changes;
- a note that `READER_HEURISTICS.md`, `ALIGNMENT.md`, `docs/theory/README.md`,
  `docs/theory/essays/`, and `FINDINGS.md` were reviewed but not substantively changed;
- the claim ceiling below.

After implementation, set its status to `APPLIED` with the application date.

## 4. Mandatory claim ceiling

The edited theory must not claim that:

- language is the required maker-state representation;
- humans maintain exactly one active goal;
- expertise is only stored attention;
- a foreground-goal change is a value change;
- an unusual or extended action is necessarily epistemic exploration;
- a model that predicts the next edit has recovered the maker's historical process or values.

The public claim remains bounded maker-state engineering in named model readers under known-answer
and recorded-process tests.

## 5. Acceptance checks

Run:

```bash
python tools/theory_lint.py
git diff --check
git diff -- docs/theory/THE_TRIPLE_INFERENCE.md \
  docs/theory/THREE_COGNITIVE_LAYERS.md \
  docs/theory/DECISION_TRACES.md \
  docs/design/PHASE_2_4_STAGE_6_THEORY_ERRATA.md
```

Before committing, verify:

- only the four intended files are staged;
- all curator block quotations are labeled as lightly reconstructed spoken wording;
- no finding, confidence grade, or completed-study result was reclassified;
- prediction is an evaluation criterion, not proof that every predictive model recovered the true
  historical process;
- attention is not defined circularly from whatever expertise later contains;
- value-change and exploration readings retain their explicit rival explanations;
- unrelated result artifacts and broader Stage 6 program files remain untouched.

Use a narrow commit message such as `Apply Stage 6 theory reconciliation`.


## Application record (2026-08-31)

Applied to the three theory owners on 2026-08-31. The 2026-08-30 drop had applied the shared
four-joint subset the day before; this update added the consolidation line and its legend, the
goal-remains-separate ruling, the canonical pointer rule, the Stage-5 summary sentence, the
slope quotation with the rival list and the prospective-separator note, the ten-constraint
expertise formulation, the explicit control rivals, the G26 narrowing, and the enriched
exploration standard. `READER_HEURISTICS.md`, `ALIGNMENT.md`, `docs/theory/README.md`,
`docs/theory/essays/`, and `FINDINGS.md` were reviewed and not substantively changed. The
reference commit `bff8be0` does not exist in this clone; the errata text itself was the
implementation source. `tools/theory_lint.py` first flagged fourteen em-dash prose violations (this pass's and two
earlier passes' debt); all were restructured the same pass, after which the lint and
`git diff --check` ran clean. No commit was made (commits happen only on the curator's word). The
provenance pointers in the three owners cite this file at its archived path.
