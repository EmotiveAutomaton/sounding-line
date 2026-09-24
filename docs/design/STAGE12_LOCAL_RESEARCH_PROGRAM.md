# Extensive local reader research program

**Status: proposed, September 23, 2026. Research and planning complete; implementation and scientific dispatch unstarted.**

Commission: the curator requested a much larger local program, derived from the
theory, previous tests and fresh exploratory research, to validate measurements,
explain results and extend the research frontier. This is an analyst proposal,
not a new theory definition, an execution manifest or a change to Stage 12 limits.
Gear 2 remains the existing allocation. No cloud, new training, downloads, agents
or additional shared fits are required by the first tranche.

The recommendation is **22 packages, up to 23,600 local model calls**, including
two zero-call analysis packages. Start with seven packages totaling **4,864
calls**. Their controls address the strongest unresolved issues in the previous
288-call addendum. Broader packages follow in dependency order, with a separately
reserved replication and an explicitly conditional mechanism extension.

The [source review](STAGE12_LOCAL_RESEARCH_SOURCES.md) identifies what was actually
read and what each source licenses. The [planning roster](STAGE12_LOCAL_RESEARCH_ROSTER.json)
contains checked call arithmetic, dependencies and readiness; it cannot dispatch
jobs. The original [week commission](PHASE_2_4_STAGE_12_CONTEXT.md) and
[completed addendum freeze](STAGE12_ADDENDUM_IMPLEMENTATION.md) remain unchanged.

## 1. The questions this program should answer

The theory asks whether a reader can construct a useful, revisable model of a
maker from choices, constraints and traces. Prediction is one discriminator;
recovering a witnessed process, identifying missing evidence, and constructing a
usable account are distinct achievements. A plausible story alone establishes
none of them. Relevant anchors are Reader Heuristics §§1, 4–7 and 10; The Triple
Inference §§1, 2 and 7; Decision Traces §§1 and 6; Three Cognitive Layers §§3 and 8.

The following table maps research strands to the distinctions they must preserve.
Package identifiers refer to the concrete cards below, not existing theory rows.

| Strand | Question in plain language | Packages |
|---|---|---|
| Measurement and assistance | Does the reader infer something, select something supplied, or merely produce the right format? | LP00–03 |
| Revision and warrant | Does new evidence improve the account, and when does an old answer or attractive explanation obstruct it? | LP04–06, LP09 |
| Investigation | Does the reader choose a useful next observation and know when further investigation is worth its cost? | LP07–08 |
| Reusable understanding | Does a compact account transfer to new questions and distinguish individual experience from generic domain familiarity? | LP10–12 |
| Historical process | Which actions and dependencies are recoverable, and which histories remain indistinguishable? | LP13–18 |
| Ambitious transfer and replication | Can understanding support adaptation to a changed task, survive another reader family, and replicate on a frozen new roster? | LP19–21 |

Three recent findings determine the initial emphasis. L434 separates pair ranking
from probability quality. L435 shows that saved-answer effects depend on method
and history, but its truthful and false frames occur on different histories.
L436 separates copying fidelity from correctness and exposes presentation
sensitivity even in supplied-answer tasks. These motivate crossed controls and
more independent source units, not selecting whichever prompt previously won.

The research review supplies competing explanations rather than a replacement
vocabulary. Intrinsic self-correction can fail while independently verified
correction succeeds [R1–R3]. A visible prior answer and contrary advice can exert
different biases [R4]. Evidence location and memory access can masquerade as
understanding [R5, R9]. Artifact interpretation already has inverse-planning
precedents [R11–R12]; the contribution here is the controlled conjunction of
reconstruction, revision, access and independently witnessed consequences.

## 2. Source support and what counts as a new observation

The table distinguishes verified availability from a future eligibility target.
No source passage, restricted identifier or evaluator label belongs in a public
planning receipt or a reader's request unless explicitly part of that condition.

| Substrate | Verified now | Consequence for the proposal |
|---|---|---|
| Existing constructed law | Existing development/test fixtures and source-bound renderers, exact references and revision handlers are present | Compile new prospective rosters with the unchanged law; exclude old frozen test IDs and all previously exposed content. New draws remain evidence within one law, not independent mechanisms |
| ARIES | Fresh read-only census: 42 papers, 36 eligible for both explicit labels and current size bound; 21 compiled paper identities, of which 20 are eligible; 16 eligible papers remain outside that compiled roster | LP15 can broaden correspondence across these 16. Reserve eight before development, but call them locally reserved, not globally untouched or pretraining-free |
| CoAuthor | Existing population census: 564 evaluation records across 53 sessions and 15 writer components; zero fresh confirmatory components | LP16 is a descriptive, narrower record-operation diagnostic. It cannot repair the incomplete capable-reader main or become a fresh human confirmation |
| ScholaWrite | Local released dataset and strict successor extractor exist; five project groups, previously evaluated in full | LP17 can test temporal/persistence alternatives. Eligibility is exact visible-text continuity and source filtering, not presumed consecutive physical keystrokes. Aggregate-only reporting; existing restricted-use terms remain |
| Witnessed local operations | Eight completed source-bound paths with actual operations, goals and public projections | LP14 has eight content groups even if many questions are asked. Extend questions, not the claimed number of independent paths |
| G159 and role records | Existing realization audit distinguishes exact and approximate checks; the role corpus has 40 cases with selection/veto audit | LP18 uses at most the 64 exact-auditable G159 items after revalidation. Prompted instructions are not assumed realized. Role records are an optional later source, not extra uncounted calls |
| Other local readers | Cached Qwen2.5 and SmolLM2 instruction models are present | Presence is not a complete-weight, memory, output or task admission. LP20 loads them serially after separate checks |
| Changed tool/goal mechanisms | Current shared fits already consumed; joint composition is not admitted | LP19 needs an owner-approved native export of valid changed-task episodes. No replacement simulator or third fit is smuggled into this plan |

LP00 must freeze a source/exposure map before compilation. Independence is at
history, maker component, paper, writer component or project as appropriate.
Questions, repeated requests, renderings and descendants of one history do not
increase that count. Across-package reuse is allowed only with an explicit
shared-parent map. The replication roster is disjoint from all development.
If an eligibility target cannot be met, record the actual census and reduce the
unopened design before freeze; never fill it with disguised duplicates.

## 3. Common measurement and validity contract

**DESIGN CHECK:** LESSONS §§3–5, especially known-answer rulers, source-dependent
denominators, answer-position pairing, dynamic range, realized manipulations,
invalid-output retention and cold/resident resource accounting; CONTROLS §§5–7.
Each card adds its specific failure direction below. Existing gates are not
silently reused under a different statistic.

Use the current source-bound local reader profile first: Qwen3.5 9B, 8,192-token
context, current fixed seed/temperature and 2,048-token output cap, one GPU owner.
Verify actual prompt length including template and output allowance. Long human
records use an outcome-blind declared projection or fail eligibility; no silent
truncation. Direct and account conditions receive the same task evidence. Account
production is charged, including acquisition calls; exact answers/states and
evaluator computations are visibly privileged controls. No private targets,
future records or hidden source-law coefficients enter an ordinary reverse read.

For a probability forecast p and an exact target distribution q, retain the
existing expected half-Brier loss, one half of `1 + sum(p*p) - 2*sum(p*q)`.
The exact reference has loss `(1 - sum(q*q))/2`; excess loss above it equals
`sum((p-q)^2)/2`. This is not simply squared distance when the irreducible
uncertainty is retained. On human labels q is the declared one-hot annotation,
not an unobserved distribution over a person's motives. Keep ranking, literal
validity, support, fidelity and useful yield separately. Zero probability on a
possible outcome retains infinite logarithmic loss; invalid attempts retain the
existing maximum finite penalty of one. No retrospective clipping or smoothing
replaces a primary result [R10].

CPU rulers must pass exact identity, label-inversion, known wrong-answer,
missing-evidence and should-change controls before any model call. Inspect one
assembled instance per factor level. A diagnostic update must change its exact
target; an irrelevant update must leave it invariant. Later-snapshot references
are independently recomputed. Mutations cannot copy their parent's hidden target.
Select scientific units by source properties, never by reader success. Retain
all invalids and both-valid sensitivity denominators.

Model admission is task-specific. The existing broad human-history capability
failure remains. A narrow new record task needs a frozen, balanced development
admission with literal validity and known-answer controls before its larger
roster opens. These development requests are counted inside that card, not free
attempts. Failure stops its dependent interpretation; it does not prove that the
theory is false or block unrelated admitted constructed tasks. No automatic
prompt repair, resampling until valid, or cloud fallback.

All proposed effect directions below are hypotheses. For numerical contrasts
report paired source-cluster means, distributions and uncertainty intervals.
The common exhaustive disposition is: **BLOCKED** before execution; **VOID** if
source/ruler validity fails; **INCOMPLETE** if an attempt lacks required returns;
otherwise **BENEFIT**, **HARM**, **EQUIVALENT** or **UNRESOLVED**, using a frozen
contrast direction and margin. For half-Brier contrasts the proposed smallest
material difference is 0.02, an engineering convention to ratify at freeze, not
a literature-derived universal threshold. Benefit/harm requires the entire 95%
cluster interval beyond that margin; equivalence requires the whole interval
inside it; every other complete outcome is unresolved. Deterministic ruler
identities use numerical tolerance, not statistical equivalence. Non-loss
outcomes get named units and their own margin in the implementation freeze.

All development strands are exploratory; do not manufacture dozens of
confirmatory p-values. LP21 reserves two primary replication contrasts, with
familywise correction if significance tests are used and registration in the
existing multiplicity audit. Repeated seeds do not become independent histories.
As a planning illustration only, a paired standard deviation of 0.15 gives a
95% interval half-width near 0.037 at 64 independent histories, near 0.026 at
128. This is not a power guarantee, and 16 papers or five projects cannot be
turned into a large human population by generating more calls.

## 4. Study cards

Counts are maximum planned model requests, not measured duration or unique
subjects. All cards inherit the common contract, final-packet policy and full
internal write-through. References R1–R15 resolve in the source review.

### LP00 — Freeze what the program can actually measure — 0 calls

Build exposure/dependency/source maps; replay the existing readers' request and
score bindings; census every proposed population before choosing it. Produce
CPU truth tables for all public projections, exact uncertainty floors, positive
and negative controls, semantic duplicates and forbidden future fields.
**Null/failure:** unchanged input must reproduce the original summary; altered
source bytes, copied mutation targets or zero-range interventions must fail.
**Meaning:** a preparation gate, not scientific support. Reuse existing complete
receipts; do not relaunch completed inference. DESIGN CHECK: LESSONS §§3/5.

### LP01 — Does presentation change the answer to the same problem? — 384 calls

64 fresh constructed histories × six presentations: canonical, identical repeat,
reversed option order, invertible label permutation, diagnostic evidence first,
and the identical evidence last. Match padding and content; hold the nuisance
ordering paired in every later method comparison. Infer normally rather than
copying a supplied answer. Measure canonicalized probability change, invalids
and excess loss. **Null:** exact references are identical; repeat variation
sets a descriptive noise scale. **Alternative:** systematic order/position
errors identify an access or readout problem, not a changed maker. A failed
label inverse voids the ruler. Derived from L436, Reader §10 and R5.
DESIGN CHECK: LESSONS §3 option-order and short-candidate corrections.

### LP02 — Separate selection, copying and inference — 768 calls

64 histories × two queries × six conditions: unaided inference, one correct
supplied vector to copy, selection from a correct multi-query bank, its inverted
labels, a matched irrelevant bank entry, and a deliberately wrong supplied
vector. Supplied vectors have sufficient separation from truth to make the
wrong-answer control informative. Measure lookup selection, literal fidelity
and task loss separately. **Null:** exact copying of a wrong answer should
retain fidelity and worsen task loss; agreement between those measures would
expose a defective scorer. **Alternative:** bank-only failures locate selection
cost, whereas unaided-only failures locate an inference deficit. Derived from
L436, Triple §2 and R10. DESIGN CHECK: LESSONS §§3–4, validate the ruler first.

### LP03 — Reconcile probability quality, ranking and abstention — 0 calls

Analyze complete frozen outputs with the original all-attempt score, paired
ranking, reliability plots, proper-score components and coverage/error curves.
Use a fixed abstention grid declared before new outcomes; show error alongside
useful coverage and invalid rate. Never select a new winning threshold on the
test roster or fit a calibrator under the exhausted shared-fit allowance.
**Null:** uniform and exact distributions have their analytic scores; a good
ranker may still be badly calibrated. **Alternative:** a localized confidence
defect motivates a later separately frozen intervention, not rewriting L434.
Derived from L434 and R10. DESIGN CHECK: LESSONS §3 denominators/calibration.

### LP04 — Can an account recover from a false starting frame? — 2,688 calls

64 histories × direct/account × three frames (truthful, contradicted, neutral)
× seven calls: one initial answer plus fresh/saved-answer reads at unchanged,
diagnostic and length-matched irrelevant snapshots. **Every history receives
every frame**, removing the L435 between-history confound. All ordinary evidence
is identical within each later-snapshot comparison; a frame is attributed as a
fallible claim. Retain the actual initial reply even when invalid.
**Primary:** saved-versus-fresh excess loss after diagnostic evidence, and its
interaction with frame truth; unchanged/irrelevant drift is a specificity check.
**Null:** extra text or answer preservation alone explains movement.
**Alternative:** selective movement toward the later target survives the false
frame. General harm or improvement in all snapshots is not selective updating.
Reader §4; R1/R4. DESIGN CHECK: LESSONS §3 dynamic range and paired conditions.

### LP05 — Which property of an old answer obstructs correction? — 1,152 calls

32 histories × two methods × two later evidence types × nine states: fresh, or
eight supplied-answer states crossing accurate/inaccurate modal prediction,
low/high stated confidence, and claimed self/other ownership. Supplied vectors
are standardized, length matched and checked against the initial target; stated
confidence is independently manipulated text. These are attributed predictions,
not genuine hidden memories or a claim that the model previously authored them.
**Null:** copying explains retention irrespective of owner label; contrary
advice can also cause overreaction. **Alternative:** ownership, certainty or
content explains a distinct paired interaction after correctness is controlled.
Separate arbitrary provenance effects from evidence use. Reader §§1/4; R4/R8.
DESIGN CHECK: LESSONS §§3–4, treatment realization and output/content separation.

### LP06 — One cause repeated, or genuinely additional evidence? — 640 calls

64 histories × two methods × five views: one observed event, the same event
repeated verbatim, the same event restated through a verified renderer, an
additional independent source event, or length-matched irrelevant material.
Repeated reports retain the same event identity. Exact references count an
event once and update only on genuinely additional evidence; independence is
defined by the existing source law, not asserted from different wording.
**Null:** confidence rises equally for repetition and new observations.
**Alternative:** warranted improvement follows independent evidence while
duplicate reports remain appropriately bounded. Reader §4's common-cause
warning; R1/R3/R11. DESIGN CHECK: LESSONS §3 effective units and invariance.

### LP07 — Can the reader choose a discriminating next question? — 1,408 calls

64 histories, three sequential observations, four selectors. Neutral and
counterexample-seeking model selectors each cost seven calls (initial forecast,
then three question/forecast pairs). Random and exact-information selectors
each cost four forecast calls; their selections are CPU-computed references.
Candidate observations come from the existing finite law. Selectors never see
unrevealed outcomes or evaluator targets. Counterbalance option position and
wording without changing information value. Measure actual later loss, exact
expected information gain, redundancy and all-attempt cost. **Null:** position,
surface difficulty or indiscriminate negation explains selections. **Alternative:**
chosen observations discriminate live candidates and improve subsequent reads.
Model-policy comparisons have matched calls; CPU references are cheaper and
privileged, reported on cost curves rather than falsely called equal-budget.
Reader §4; R6/R7. DESIGN CHECK: LESSONS §3 difficulty and active-query controls.

### LP08 — When should investigation stop? — 768 calls

64 histories × two declared reader purposes × three public observation costs ×
two offer orders. Each call chooses stop/buy and gives the current forecast.
Use the existing finite candidate observations and publicly specified decision
losses. CPU enumeration supplies the value-of-information reference, including
cases where buying is and is not worthwhile. **Primary:** selection regret in
declared utility units. This measures the decision to investigate; actual
post-purchase use is tested by LP07, not assumed here. **Null:** always-buy,
always-stop or option position explains decisions. **Alternative:** appropriate
stopping shifts with task and cost rather than generic uncertainty. Reader §5;
R6/R7. No claim about human interest or an ordered-unexplained scalar.
DESIGN CHECK: LESSONS §3 both target classes and visible feasibility.

### LP09 — Can source reliability constrain a persuasive frame? — 864 calls

48 histories × two methods × three source-channel reliabilities × three cue
states (supporting, opposing, absent). Use an explicit finite observation channel
over existing world facts, with public reliability 0.50, 0.75 or 0.90 and matched
calibration examples; this changes reader evidence, not the maker mechanism.
Truth and cue direction are balanced and separately retained. CPU references
condition on the declared channel. **Null:** equally persuasive text dominates
regardless of reliability. **Alternative:** trustworthy evidence matters more,
and low-reliability disagreement does not automatically trigger reversal.
This is a reliability-use diagnostic, not evidence that a human source has that
accuracy. Reader §4; R4/R11. DESIGN CHECK: LESSONS §3 every factor is realizable.

### LP10 — Does a compact account support genuinely new questions? — 1,664 calls

64 histories × [two acquisition calls + six views × four evaluation queries].
Acquire one free summary and one structured account before showing future query
identities. Compare full raw history, outcome-blind indexed retrieval, the two
learned representations, an exact sufficient state, and a deterministic
task-specific fact table. Only the exact state receives evaluator knowledge.
Use four distinct later query types admitted by the same source; a fact table
must mark unsupported queries unknown. Charge acquisition and retrieval cost.
**Null:** retrieval or privileged answer access explains the benefit.
**Alternative:** a learned account preserves useful relations across unseen
queries at its declared storage/call cost. Failed acquisition remains failed,
not replaced. Triple §2 and Reader §6; R5/R9. DESIGN CHECK: LESSONS §§3–4 leakage,
query access, compression and acquisition accounting.

### LP11 — Individual familiarity or general domain expertise? — 1,536 calls

64 target histories × two methods × four prior-experience sources × three doses
(one, two or four earlier records). Sources: same maker, a matched other maker,
domain examples pooled without the target maker, and irrelevant matched-length
records. Current target evidence is common. Match difficulty and source depth,
exclude future events and sibling copies, and keep the donor relation explicit.
**Null:** longer context or generic task teaching explains all gains.
**Alternative:** own-maker history supplies something beyond domain knowledge,
with a dose pattern tied to the independently known target. The reader is not
retrained; this is in-context familiarity. Reader §§1/6 and Triple §§1/2;
R9/R11. DESIGN CHECK: LESSONS §3 dependency, donor support and effective N.

### LP12 — Can the reader recognize a missing explanation? — 768 calls

64 histories × two methods × three candidate libraries × two evidence snapshots.
Libraries contain the full declared family, omit the generating candidate, or
add a matched irrelevant candidate; every response permits outside-family or
insufficient-evidence mass. Candidate omission is never repaired using test
answers. Compute the reference over the full source family and its observable
equivalence classes, not a renormalized list that guarantees false certainty.
**Null:** a coherent forced choice survives contradictory evidence.
**Alternative:** evidence changes support or prompts an appropriate unknown
without making every case unknown. Report supported yield with coverage.
Triple §7 and Reader §4; R11. DESIGN CHECK: LESSONS §3 null that can fail and
identifiability at the actual observation count. Finite omission is not open-world discovery.

### LP13 — Same artifact, different history — 768 calls

Up to 64 verified pairs × two members × two methods × three views: identical
artifact alone, discriminating witnessed record, or a matched misleading frame.
Enumerate pairs in the existing law and collapse shared-parent/content clusters
before freezing N. Measure probability assigned to compatible historical classes
and improvement from the genuine trace. **Null:** artifact-only readings must
not uniquely recover two observationally identical histories. **Alternative:**
the real trace separates them; a false frame changes belief without creating
warrant. Fewer than 64 eligible independent pairs reduces the unopened design,
not the control standard. Triple §7 and Decision Traces §1; R11/R12.
DESIGN CHECK: LESSONS §3 exact twins and no copied mutation targets.

### LP14 — Recover local goals and dependencies from witnessed operations — 256 calls

Eight existing paths × two methods × four evidence views × four questions.
Views: endpoint, full witnessed changes, an outcome-blind partial record, and a
matched misleading context. Questions separate recorded local goal, preceding
operation, dependency relation and next-operation prediction under a supplied
goal. The source must independently support each answer; unsupported questions
are excluded before freeze. Use recorded-change and compatible-template rivals.
**Null:** a plausible reenactable route substitutes for the actual path.
**Alternative:** witnessed evidence improves the corresponding historical target
without unsupported mental assertions. Goals that can coexist are not forced
into one exclusive probability simplex. Eight paths remain eight content groups.
Triple §§1/2, Decision Traces §6; R8/R11. DESIGN CHECK: LESSONS §3 target separation.

### LP15 — Broader human request/edit correspondence — 384 calls

16 remaining eligible ARIES papers × two explicit labeled examples × two methods
× two question formulations × three evidence views. Use one positive and one
explicit negative per paper, selected without model outcomes. Views: the supplied
pair alone, outcome-blind local context, and a verified change-focused rendering
of the same available material. This tests access, not additional evaluator
answers. Keep eight papers reserved from prompt development. Cheap lexical/diff
ranks, all probability scores and paper weighting remain. **Null:** lexical
overlap or question wording explains account gains. **Alternative:** any gain
survives the matched controls and is not just overconfident ranking. Never treat
unannotated silver pairs as negatives. Balanced sampling is not natural prevalence
or author-purpose recovery. Reader §10; R13. DESIGN CHECK: LESSONS §3 labels/denominators.

### LP16 — Human recorded handling with own and donor history — up to 1,440 calls

Up to 120 eligible CoAuthor events × two methods × six views: current record,
own prior history, matched donor history, domain-only history, outcome-blind
indexed own history, and a witnessed handling record. The last is an assistance
control, not a prediction arm. Target observable handling/retention supported by
the strict event reconstruction; do not ask for private intention. Use existing
prior/persistence/alignment controls and writer-component weighting. Reserve the
first balanced 16 events for frozen narrow task admission within this cap.
**Null:** generic persistence, future leakage or common prompt identity explains
history gains. **Alternative:** source-specific evidence helps under those controls.
All components are previously exposed. This cannot stand in for the incomplete
cloud human-history comparison. Decision Traces §6; R9/R11. DESIGN CHECK: LESSONS
§§3–4 dependency, capability and same-snapshot labels.

### LP17 — Human revision boundaries, temporal continuity and persistence — up to 2,000 calls

Up to 250 ScholaWrite windows, at most 50 per project, × two methods × four views:
current visible artifact, immediately prior continuous record, earlier history
within that project/author stream, and a length/task-matched donor stream.
Freeze 25 balanced development windows inside this cap for narrow admission.
Forecast the next released edit category/location; preserve gaps, timestamp ties
and text-discontinuity exclusions. Reuse frozen training-only prior, persistence
and duration controls; add no fit. Separate within-span persistence from real
annotation transitions. **Null:** runs of identical annotator labels explain
apparent prediction. **Alternative:** information beyond those baselines survives
whole-project comparisons. Five projects remain five; labels are retrospective
annotations, not writer-reported cognition. Decision Traces §§1/6; R14.
DESIGN CHECK: LESSONS §§2–4 extractor boundaries, grouping and trivial predictors.

### LP18 — Requested action versus realized action — up to 384 calls

At most 64 exact-auditable G159 items × two methods × three views: artifact alone,
artifact with requested instruction, and artifact with a checkable execution
trace. Recompute realization before selection; retain fulfilled and unfulfilled
requests and both instruction signs. Use an exact feature checker and cheap
text/diff reference. **Null:** the instruction is echoed even when its checkable
action did not occur. **Alternative:** actual realization, rather than requested
purpose, controls recovery. Exact-auditable does not mean fulfilled, and does
not validate the approximate annotation subset. Reader §§6/7 and Decision Traces
§6; R8/R12. DESIGN CHECK: LESSONS §§2–3 manipulation realization and label leakage.

### LP19 — Adapt the same process model to a changed task — conditional 768 calls

32 episodes × two declared purposes × two tool/action sets × two methods × three
calls (plan, independent check, revision). This is the ambitious local extension:
does a recovered account enable a feasible new route when the old habit is no
longer appropriate? Score executable feasibility, task outcome and witnessed
historical fidelity separately. Old-route replay, native planner and a direct
reader are rivals; a public exact checker, not another model's opinion, validates
actions. **Null:** fluent re-description or blind reuse explains success.
**Alternative:** adaptation follows the changed constraints while preserving
what remains applicable. Reader §§6/7, Triple §2; R2/R3/R12.
**BLOCKED pending native episode support:** Ghost owns mechanisms and any new
fits; current joint-composition failure remains. No mechanism is invented here
to fill this card. DESIGN CHECK: LESSONS §3 the population's own route must pass.

### LP20 — Does the key signature survive another local reader family? — 864 calls

Two cached instruction models, provisionally Qwen2.5 1.5B and SmolLM2 1.7B, each
receive 48 admission calls plus 64 units × six frozen sentinel conditions. Define
the sentinel before primary-reader outcomes: canonical/inverted lookup,
fresh/saved diagnostic update and duplicate/independent evidence. Reuse matched
source units with dependency retained; each family is loaded serially. Compare
each against its own admitted baseline, not raw capability as if model size were
controlled. **Null:** one family or format drives the apparent signature.
**Alternative:** its direction survives independently admitted readers.
Failed admission is reported without dropping the family from the ledger.
R1/R4/R5; DESIGN CHECK: LESSONS §§4–5 family admission and resource ownership.

### LP21 — Reserved replication of correction and investigation — 4,096 calls

Before exploration starts, reserve a disjoint 64-history roster for the complete
LP04 matrix (2,688 calls) and another 64 for the complete LP07 matrix (1,408).
Freeze their two primary contrasts now: diagnostic saved/fresh effect modified
by frame truth; counterexample-seeking versus neutral question selection on
later forecast loss. Run regardless of attractive or disappointing discovery
effects, once the instruments are admitted and capacity is commissioned.
**Null:** the discovery signature vanishes or reverses. **Alternative:** it
replicates with complete controls and multiplicity accounting. An instrument
revision consumes development and requires a new unopened replication freeze;
the old reserve cannot be relabeled untouched after inspection. This tests
within-law replication, not a second mechanism or human generalization.
DESIGN CHECK: LESSONS §3 independent units, power and quiet controls replicated.

## 5. Sequence, cost and stopping boundaries

The table shows complete planned request caps by phase. CPU analyses are present
even where their request count is zero. Dependencies can narrow an unopened
phase; they never authorize adding new conditions after seeing results.

| Phase | Packages | Calls | Review breakpoint |
|---|---|---:|---|
| First local tranche | LP00–04, LP06, LP15 | 4,864 | Complete rulers, presentation/binding, crossed revision, corroboration and broader correspondence packet |
| Explanation and investigation | LP05, LP07–09 | 4,192 | Distinguish prior-answer, reliability, question selection and stopping effects |
| Reusable accounts | LP10–12 | 3,968 | Transfer, familiarity and missing-family packet |
| Historical process breadth | LP13–14, LP16–18 | 4,848 | Constructed twins plus separately reported human/realization diagnostics |
| Local family check | LP20 | 864 | Family admission and complete sentinel comparison |
| Reserved replication | LP21 | 4,096 | Confirmatory within-law contrasts, whether positive or negative |
| Conditional mechanism extension | LP19 | 768 | Native export/admission decision before any dispatch |
| **Whole proposal** | **22 packages** | **23,600** | Complete program synthesis |

Timing is based on actual raw service durations from the completed addendum:
128 ARIES calls used 290.810 seconds, 112 revision calls 500.737 seconds, and 48
binding calls 166.778 seconds. Their total is **958.325 seconds (about 16 minutes)**
of model service; whole-queue time was longer. The old large reservation was not
actual utilization. Larger contexts and newly complex tasks may take much longer.

The following are scenario calculations, **not measured future throughput or
completion promises**. They use six or twelve seconds per request plus 25%
orchestration overhead. Thirty seconds is a stress scenario. Model loading,
implementation and CPU analysis are separate; small additional families are not
assumed to share Qwen3.5's measured rate.

| Work | Six-second scenario | Twelve-second scenario | Thirty-second stress |
|---|---:|---:|---:|
| First 4,864 calls | 10.1 hours | 20.3 hours | 50.7 hours |
| Core without conditional LP19, 22,832 calls | 47.6 hours | 95.1 hours | 237.8 hours |
| Full 23,600 calls | 49.2 hours | 98.3 hours | 245.8 hours |

The first tranche plausibly fits an overnight/day run after implementation, but
Friday morning delivery is conditional on setup and actual measured admission.
Budget roughly 6–10 active engineering hours for the first tranche and another
16–28 for later adapters/analyses; these are planning allowances, not verified
estimates. The whole program is several days of local inference plus setup and
analysis, not a promise to finish in the remaining two days.

At the last completed closeout, original Stage 12 ceilings leave approximately
29.96 GPU-service hours and 21.69 CPU-process hours after the four-hour reserves,
and about 0.89 diagnostic-GPU hours. These are accounting headroom, not wall-clock
availability. Recompute them from the original ledger before any selection.
The full program exceeds the original GPU allowance under these conservative
scenarios; it therefore requires a later local execution allocation. No reset
of the week clock, extra fits or cloud spending is implied. Admission and warm-up
count against diagnostics; scientific instrumentation comparisons do not replace
or weaken that admission. Every consumed second still counts in the relevant
original accounting dimensions.

A sensible first implementation freezes the complete 4,864-call tranche, then
admits only whole paired blocks that fit current hard capacity and reporting
reserves. Its longest declared request timeout, aggregate reservations and
unknown-response disposition must all fit; unused total budget cannot cure an
undersized individual timeout. If capacity does not cover the whole tranche,
freeze a smaller complete selection before dispatch and identify the rest as
unstarted. Do not splice retries, shorten prompts after failures or hide missing
conditions. No additional inference is authorized by this planning document.

## 6. Implementation handoff and reporting

1. Preserve old source pins, failures, call records and score versions. Create a
   distinct implementation freeze, with source census, factor tables, request
   counts, prompt/output bounds, exact target checks and parent-cluster mapping.
   Keep the planning roster non-executable; translate the selected cards manually.
2. Extend the existing source/reader interfaces and scoring/replay handlers.
   Require negative tests for future leakage, inverted labels, semantic duplicate
   detection, wrong-source targets, absent responses, invalid outputs and budget
   refusal. Full fake-roster rehearsal must cover every condition and successor.
3. Perform actual native/resource and task admission once, respecting existing
   cold/resident memory handling, CPU cooling limits and one GPU owner. Register
   each terminal produce and verify watcher delivery before background launch.
   Do not stop unrelated applications or start any paid route from this plan.
4. Retain the four-hour health cadence and immediate failure/terminal alerts.
   Health inspection includes native identities, output freshness, failures,
   locks, remaining bounds, runnable selected work and actual delivery. A pause
   is not an automatic restart instruction. Routine success can be batched.
5. Land each complete scientific cell through FINDINGS, the relevant theory row
   and afterword, TODO and the curator roll-up before ACK. Keep family synthesis
   complete-only; no unfinished artifact scores. Source/ruler failures remain
   distinct from model harm, equivalence or unresolved effects.
6. For each whole family provide question, method, all-attempt results, controls,
   dependency/coverage limits, costs and the next warranted claim. Select case
   roles before outcomes: a supported recovery, a persuasive failure, an
   indistinguishable pair, a correction and a failed correction, where available.
   Do not cherry-pick examples or publish restricted human source passages.

The existing reviews remain Friday September 25 at 06:17 PDT and Monday September
28 at 06:17 PDT, with protected reporting beginning Sunday at 18:17 PDT. The new
program's first scientific review is after a complete selected tranche, not an
unfinished score stream. Source/ruler failure, a hard resource boundary or a
needed native mechanism export is an earlier engineering breakpoint. There is
no new curator decision required for every successful ordinary block; a changed
theory definition or consequential scope change follows the existing interrupt.

The final program should distinguish six possibilities: a usable reader; a
reader helped mainly by evidence access; a reader that copies privileged answers;
a persuasive but poorly calibrated storyteller; a record-limited task with
genuinely unidentifiable history; and an invalid instrument. Separating these
outcomes is what makes the larger local program useful even when an ambitious
branch fails.
