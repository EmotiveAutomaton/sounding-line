# Sounding Line and Ghost Scale Sim: coding-agent errata

Prepared 2026-09-05. This is one consolidated maintenance handoff for work alongside the active stages. It supersedes the operational assumptions in the earlier September 5 baseline where the newer commits differ. It does not commission a new scientific campaign.

## 1. Scope, evidence, and operating boundary

| Repository | Reviewed revision | State established by committed evidence |
|---|---|---|
| [Sounding Line](https://github.com/EmotiveAutomaton/sounding-line/tree/7384809b00760f984120f8c8a59d16f6e84768df) | `7384809b00760f984120f8c8a59d16f6e84768df` | Stage 8 already running; prediction gate passed, generation gate failed; subsequent relevant trunks are diagnosis. Contract ceiling September 6 at 08:06:58, as recorded by the runner; timestamps do not specify a timezone. |
| [Ghost Scale Sim](https://github.com/EmotiveAutomaton/ghost-scale-sim/tree/36927fae0356c0080276380f2f0ad560b658aa40) | `36927fae0356c0080276380f2f0ad560b658aa40` | V15 in progress. Scheduled freeze September 6, 23:43:05 UTC; confirmation end September 7, 15:43:05 UTC; final deadline September 7, 17:43:05 UTC. |

These are repository snapshots, not a live inspection of the workstation. Before implementation, re-pin the working revision, inspect local changes, identify actual running processes and their source roots, and determine whether selection or closure has since occurred. Preserve newer legitimate fixes. Stage 8 already has trained forward-model readers, sequence scoring, adapter provenance, fragment handling, and a repaired root guard. Its separately authorized Gemini frontier probe has a $40 cap. Do not prescribe those improvements as missing or revoke that authorization through an older general local-only paragraph.

**Prepare source fixes in an isolated checkout.** A live dispatcher can import or copy modules later; changing its checkout can mix implementations within one stage. Redirect every test output, registry, manifest, checkpoint, and report to temporary roots. An `out_dir` parameter alone may not isolate global ledger writes. Run deterministic fixtures only for this maintenance pass.

**Continue valid running work.** Before the next affected confirmation or closure step, install verified administrative repairs at a controlled process boundary, recording old/new revisions and input hashes. If that boundary has already passed, preserve the original packet and issue a dated correction from an immutable evidence snapshot. Do not erase locks, reset the run clock, regenerate frozen specifications, alter scientific thresholds, or restart scientific cards merely to refresh a report.

**Check source-lock membership before any installation.** A controlled process boundary does not itself authorize changing locked sources. Ghost's `prereg_v15.GENERATOR_FILES` includes `common.py`, `particles.py`, `schemas.py`, and other generator modules; their hash changes make scientific/confirmation continuation refuse the lock. Keep repairs touching locked files staged until closure unless an existing or separately authorized, recorded amendment covers them. Apply the same membership check to Sounding's active lock. Do not regenerate locks merely to make maintenance pass. Detached revalidation of preserved evidence can still produce an explicitly revised report.

The labels below distinguish **reproduced defect**, **source-confirmed defect**, and **reachable risk without an observed incident**. None of the review diagnostics ran models, paid calls, production experiments, or project jobs.

## 2. Implementation order

| Priority | Items | Required before |
|---|---|---|
| P0: eligibility and evidence integrity | S1–S3, G1, G4 | Affected confirmation selection, registry mutation, or acceptance of final claims |
| P1: honest interpretation and reporting | S4–S5, G2, G3, D1–D5 | The next analyst/curator or public result packet |
| P1: operational accounting | G5 | Any assertion that V15 met its utilization contract |
| P2: workflow consolidation | W1–W4 | The next campaign handoff |

P0 does not mean kill all running work. It means an affected claim or mutation must not proceed through a known defective gate. Scorer changes, changed training, new experiments, and amended estimands require their own recorded lineage under existing authorization rules.

## 3. Sounding Line repairs

All paths in this section are relative to Sounding Line at the pinned revision. Primary operational owners are [Stage 8 code](https://github.com/EmotiveAutomaton/sounding-line/tree/7384809b00760f984120f8c8a59d16f6e84768df/runners/stage8), [STATE](https://github.com/EmotiveAutomaton/sounding-line/blob/7384809b00760f984120f8c8a59d16f6e84768df/docs/STATE.md), and the [Stage 8 context](https://github.com/EmotiveAutomaton/sounding-line/blob/7384809b00760f984120f8c8a59d16f6e84768df/docs/design/PHASE_2_4_STAGE_8_CONTEXT.md).

### S1. Use one admission predicate everywhere

**Targets:** `runners/stage8/engines.py::admitted_readers`, `::run_E03`; `confirmation.py::freeze_confirmations`, `::run_B04`; `report.py::write_final_packet`; existing `EXPERTISE_GATE.json` and `GATES.json` owners.

**Evidence — reproduced.** The repaired runtime predicate combines prediction and generation evidence, but confirmation and reporting still use raw `EXPERTISE_GATE.readers[*].passed`. E03 expansion overwrites that raw flag. Current committed registries yield two admitted readers through the raw flags and zero through the composite predicate. Missing generation evidence also needs explicit treatment.

**Repair:** Reuse one read-only, per-reader eligibility function. Retain separate prediction, generation, admission, and reason fields. Updating prediction evidence cannot overwrite the composite decision. Missing required evidence is pending; failed generation is not admitted. Every confirmation selector, branch summary, and report must use the same predicate. A qualifying reader cannot confer eligibility on another reader. Diagnosis-only support remains diagnosis.

**Acceptance:** E03 pass/E04 fail admits nobody in every consumer; an E03 rerun cannot reverse it; absent E04 stays pending; one passing reader does not qualify a second; current registries produce zero admitted readers; diagnosis findings cannot enter confirmation. Prediction and generation evidence must match model, adapter, construction, and scoring lineage, not just the reader's name. Preserve and supersede any already-frozen ineligible selection explicitly.

### S2. Make final reporting respect the complete integrity verdict

**Targets:** `runners/stage8/validate.py::validate`, `report.py::write_final_packet`, scheduler validation/packet call sites, expected-cell manifest.

**Evidence — reproduced in the reporter; source-confirmed in validation.** The reporter checks missing coverage/mandatory files but ignores `cov.ok`, invalid dispositions, and cap failures. A fixture with failed integrity passed its guard. The validator itself mainly counts files and allowed outcome words; it does not fully reconcile expected identity, schema, and execution resolution. The scheduler can swallow packet failure and return success.

**Repair:** Make one explicit integrity result and its reasons authoritative. Reconcile expected cells with actual identities and terminal dispositions. Check applicable schemas, source/result identity, required receipts, confirmation mapping, and existing caps. Distinguish valid negative results, honestly blocked branches, unresolved work, instrument failure, and corrupt evidence. Surface integrity failure in scheduler status/exit and report labeling. An explanatory failure packet is legitimate; calling it validated completion is not.

**Acceptance:** Malformed or wrong-card output, unknown outcome, unresolved required cell, broken mapping, cap failure, and absent required receipt prevent validated completion. A complete valid null and a properly documented blocked branch still close administratively. Reporter and validator agree. Label the validator revision when rechecking old artifacts; change derived outputs only.

### S3. Give confirmation claims explicit result identities

**Targets:** `runners/stage8/confirmation.py::freeze_confirmations`, `::run_card`, `::run_B03`; `cards.py::CONF_CELLS`.

**Evidence — reachable defect, not an observed false confirmation.** Selection allows three claims, but executable confirmation slots are B01/B02. Enumeration in B03 can assign a third claim to B03 itself, the reconciliation card. B01/x8 repeats slot one; it is not slot three. Current admission failure should select no claims.

**Repair:** Store an explicit claim/reader/slot/source/result-path mapping. Either provide the third executable path already allowed by the contract, or decline its selection and mark it unimplemented. Never infer confirmation identity by enumeration. Do not create scientific work merely to exercise a slot.

**Acceptance:** Three eligible fixture claims have unique executable paths or explicit unrun status. B03 never supplies confirmation evidence. Zero eligible claims closes honestly with zero confirmation claims. An existing failed confirmation cannot be replaced by a different result. Preserve an already-frozen third claim as explicitly unrun if its path is unimplemented; do not silently shrink its packet or change B03's identity.

### S4. Quarantine the inherited direct-reader scoring defect; repair it under a new measurement lineage

**Targets:** [Stage 7 reader client](https://github.com/EmotiveAutomaton/sounding-line/blob/7384809b00760f984120f8c8a59d16f6e84768df/runners/stage7/reader/client.py) `Client.likelihood_any`; Stage 7 `supplied_state.py`, `model_server.py`; Stage 8 `runtime.py::materialize`, `reader/worker.py`, `reader/forward_model.py::score_boundary`; affected findings and theory rows.

**Evidence — reproduced.** The arbitrary-option helper partitions candidates, selects group finalists, concatenates them, then truncates to six. With 21 options, all finalists from groups three and four are excluded from the final comparison. Invalid component outputs can be replaced by uniform distributions while the overall result says `valid=True`. Stage 8 DIR0 invokes the unchanged Stage 7 direct path; its capsule copies these sources per unit. Stage 8's new FM sequence scorer evaluates all offered continuations and avoids this particular defect.

**Repair now:** Inventory dependency by arm, target, cell, helper, and actual candidate count. Add a bounded limitation to affected Stage 7 conclusions and Stage 8 DIR0 contrasts. Preserve unaffected FM-versus-DOM and learned-law solver evidence. Do not call all Stage 7/8 evidence invalid. Do not change the shared helper underneath the active capsule builder.

**Subsequent measurement amendment:** Define and validate an all-option probability readout, including invalid-component propagation, score semantics, label/order receipts, and exact model/scorer identity. Fixing truncation alone does not make hierarchical scores equivalent to a probability distribution from one common scoring rule.

The supplied-state comparison also needs an explicit semantic contract: numeric parameters, operative transition/action rules, and execution access are different kinds of information. Stage 7 direct text rounds parameters and does not supply the solver's complete operative law. Its results cannot cleanly isolate an inability to use fully specified state. Expanded prose also uses the defective readout. Record this limitation now; matched-information prompts and reruns belong to the later measurement amendment.

Treat Stage 7's 9B route as a package change: model family/version, quantization, server, and scoring differ. A pure size interpretation is unsupported. Missing top-logprob letters are a measurement risk, not a demonstrated explanation for every outcome. Stage 8 already records base revision/adapter hashes; preserve and extend that work rather than claiming provenance is wholly absent.

**Acceptance for the replacement:** Known distributions with maxima in every group; option permutations and ties; more than 24 candidates; invalid/missing component scores; normalization; every intended option has an observable scoring path. Invalidity survives aggregation. Freeze both operative information and readout in future model comparisons. Retain original raw rows and scope any rerun to actual dependencies.

### S5. Record outcome-informed repairs as measurement amendments

**Targets:** Stage 8 `REPAIRS.json`, original/repaired verdicts, findings, report, relevant theory evidence rows and afterwords.

**Evidence — source-confirmed.** X05 order tolerance changed from `1e-6` to `0.01` after observing TV `0.0013`. Other recorded repairs include E04 feasibility semantics, E08 solver-state execution, and OOM/fragment/resume handling. These do not all have the same scientific consequences. The one-repair clause does not make an outcome-informed threshold predeclared.

**Repair:** For each entry state original rule/result, diagnosed defect, implementation or criterion change, whether outcomes informed selection, retained/rerun rows, affected conclusions, and remaining independent verification. Preserve archived attempts. Establish a numerical-invariance tolerance using independent precision/batching fixtures; present original and repaired X05 judgments together. A repaired analysis is not fresh confirmation of the amended threshold.

**Acceptance:** No post-outcome criterion appears predeclared; raw rows retain stable identity; diagnostic/confirmatory grades agree across owners. Recheck only affected dependencies. Do not change thresholds again under this maintenance item.

## 4. Ghost Scale Sim repairs

All paths below are relative to Ghost. Core sources: [V15 cards](https://github.com/EmotiveAutomaton/ghost-scale-sim/tree/36927fae0356c0080276380f2f0ad560b658aa40/ghostscale/validation/soundingline/v15/cards), [main runner](https://github.com/EmotiveAutomaton/ghost-scale-sim/blob/36927fae0356c0080276380f2f0ad560b658aa40/runners/run_v15.py), [confirmation runner](https://github.com/EmotiveAutomaton/ghost-scale-sim/blob/36927fae0356c0080276380f2f0ad560b658aa40/runners/run_v15_confirmation.py), and [healing plan](https://github.com/EmotiveAutomaton/ghost-scale-sim/blob/36927fae0356c0080276380f2f0ad560b658aa40/docs/versions/v15-boundary-map/HEALING_PLAN.md).

### G1. Rebuild final claims from applicable, valid evidence

**Targets:** `ghostscale/validation/soundingline/v15/cards/trunk_b.py::_walk`, `::unit_B01`, `::reduce_B01`; `runners/run_v15.py::stage_integrity`, `::_queue`, `::stage_science`; `ghostscale/prereg_v15.py` flight/attack definitions; `cards/trunk_x.py`; `CLAIM_LEDGER.json`, `COMPLETION.json`.

**Evidence — reproduced.** B01 reports survival with missing transfer/confirmation, a failed same-ID attack, or a discovery result marked `INSTRUMENT_FAILED` whose criterion happens to be `HELD`. It omits attacks from its survival conjunction, gathers failures only from discovery, and silently skips unreadable verdicts. B01/B02 execute in discovery; integrity does not rebuild their aggregates after later evidence.

There is an existing flight-level attack relevance map. However, each X card currently executes against one hard-coded representative estimand. Same-ID joins cannot connect ordinary cards to X cards, and one representative X result does not validate every flight listed as relevant. The declared `ATTACK_MATRIX` artifact is absent at the reviewed revision. Do not manufacture broad coverage by relabeling that representative result.

**Repair:** Derive requirements from the locked manifest, actual endpoint/estimand identity, flight definitions, attack relevance, and frozen packet. Represent required/pass, required/fail, required/missing, invalid, and justified inapplicable separately. Require valid execution, appropriate scientific criterion, and intact provenance. Join attack evidence through explicit demonstrated applicability. Unimplemented coverage stays missing. Retain discovery-only findings as such; do not impose all four lanes on every card without a contract basis.

Collect failures from all applicable lanes. Build a new final derived ledger after evidence collection, recording input hashes and revision. Recompute deterministically when inputs change. Preserve original discovery closure. Do not rerun scientific cards to refresh aggregates.

**Acceptance:** The three reproduced counterexamples cannot claim complete survival. Missing required attack remains incomplete; justified inapplicability remains distinct; an unrelated X01 pass does not establish hierarchy coverage. Adding failed confirmation changes final closure while original discovery bytes remain unchanged. Unreadable expected evidence is an explicit gap.

### G2. Remove count-based scientific direction and misleading report rankings

**Targets:** `cards/trunk_b.py::unit_B02`, `::reduce_B02`; `runners/report_v15.py::build`; existing pursuit, warrant, publication-map owners.

**Evidence — source-confirmed.** Discovery counts and arbitrary fractions select successors such as V16 or a human study. A two-family count checks field length, not successful replication. The report calls the first six alphabetically sorted findings strongest, uses held/failed card lists as theoretical gains/losses, and hardcodes the absence of curator questions. Declared warrant/publication paths are not both written by B02. The reporter can continue after validation errors.

**Repair:** Keep counts administrative. Produce a claim-level table: supported finding, live rival, missing measurement, distinguishing evidence, bounded warrant, and pursuit rationale. Successor status remains pending actual analyst–curator interpretation unless an existing ruling supplies it. Report interpretation must be authored from the final ledger. If ordering is administrative, label it selected results; never pretend alphabetic order measures strength. Place relevant failures and missing evidence beside positives. A failed integrity gate must prevent validated-complete labeling.

Remove the hardcoded theory answer. The current user requests ten example-led discussion questions, first five primary and five optional. The report supplies evidence for that discussion; it does not decide the theory by counting dispositions. Preserve the early-report guard and original packets.

**Acceptance:** Renaming card IDs cannot change scientific recommendation or strength ranking; adding administrative held cards cannot promote V16; failed confirmation appears with its discovery claim. A publication assertion cannot be inferred from pursuit alone.

### G3. Separate posterior validity, approximation error, and impoverishment

**Targets:** `cards/trunk_m.py::unit_M01`, `::reduce_M01`; V15 `particles.py::divergence_from_exact`, `::impoverishment`; `common.py::tv`, `::normalize`; healing plan M01 entry.

**Evidence — reproduced.** Maximum total-variation distance is named `norm_error` and checked against one. The TV helper normalizes first and substitutes a uniform distribution for zero/NaN sums. Actual functions pass this supposed normalization gate for raw sums four, zero, and NaN. The gate cannot establish that original posteriors were normalized or diagnose why they were not.

**Repair:** Measure raw finiteness, nonnegativity, shape, and unit-sum residual before fallback/normalization, for approximate outputs and references. Keep these distinct from approximation divergence, predictive performance, and particle impoverishment. Correct the healing plan's unsupported non-normalization diagnosis while retaining genuine approximation failures and impoverishment. Historical raw diagnostics absent from saved evidence are unavailable, not inferable from normalized distances.

**Acceptance:** Malformed raw arrays fail integrity. A normalized but inaccurate posterior remains a scientific approximation failure, not a normalization failure. Extend `tests/test_v15_metamorphic.py::test_posteriors_are_normalized` to relevant factor-graph/particle outputs and malformed inputs. Do not increase particles, alter estimators/margins, or revise historical scientific verdicts to make a gate green.

### G4. Preserve confirmation membership, hashes, and concurrent updates

**Targets:** September 5 `runners/run_v15_confirmation.py::freeze`, `::verify`, `::amend`, `::run`, `--widen`; shared registry, `COMPLETION.json`, `AMENDMENTS.json` writers.

**Evidence — source-confirmed, with concurrency impact a reachable risk.** Resume now preserves resolved cards and external mode avoids `RUNNER_STATUS.json`; retain those fixes. But amendment adds candidates without discovery hashes. Verification visits existing hash entries only and can accept absent hashes/files. Long-running writers save old registry snapshots; a primary completion can erase a concurrent amendment, and `--only` can replace results with its subset. We did not observe an actual lost update.

**Repair:** Every packet entry must have an extant, matching source hash. Verify membership as well as equality. Validate candidate identity, eligibility, duplicates, frozen selection basis, lineage, and added provenance before mutation. Preserve the original packet/hash and label supplements separately. The immediate conservative implementation is one registry writer with serialized amendment/confirmation. If concurrency remains, protect read–modify–write with appropriate locking or compare-and-swap and merge by candidate identity. Atomic rename alone does not prevent lost updates. Include other shared ledgers in the write audit.

Resolved results must match the frozen lineage and intended source before resume accepts them. This handoff does not select extra candidates, widen the packet, advance freeze, or extend the schedule. More hours are not themselves a scientific rationale for supplemental confirmation.

**Acceptance:** Missing hash, missing/changed source, duplicate/unknown candidate, and incompatible resumed result are rejected. Interleaved amendment/completion retains both entries and all results. `--only` preserves unrelated results. External operations leave runner status intact. Never backfill an observed outcome into a supposedly untouched selection rationale.

### G5. Make utilization receipts measure actual activity across resumptions

**Targets:** V15 `runtime_contract.py::Occupancy` methods; `runners/run_v15.py::stage_science`, `::run_card`, `::run_coverage_block`, `::stage_resume`, `::stage_all`; confirmation runner; `WORKER_OCCUPANCY.json`; healing plan.

**Evidence — source-confirmed.** Each science restart constructs zeroed occupancy. Ticks credit the entire allocated pool around blocking work without measuring occupied workers. Deadline waits do not invoke `note_waiting`; confirmation/integrity intervals are omitted. The checked receipt's ratio 1.0 is therefore not proof of measured full utilization. The healing plan already records missing wait accounting and roughly 3.7 hours without science.

**Repair:** Preserve cumulative receipts through stint identities and downtime. Separately record allocated capacity, observed occupied-worker time, task CPU time, waiting, and governor restriction; these are not interchangeable. Include confirmation/integrity and avoid double-counting overlaps. Historical unmeasured intervals stay unknown or explicitly estimated from records. Apply the existing runtime contract honestly, separately from scientific validity. Future forecasts use measured representative work. Do not pad the current campaign with duplicate rollouts.

**Acceptance:** Restart continuity; full capacity with zero active workers; partial pool use; deadline wait; overlapping primary/external work without double credit. Extend existing `tests/test_v15_runtime.py`, retaining its governor, waiting, and confirmation-reserve checks. A curator decision cannot make an unmet utilization contract factually met.

## 5. Documentation contradictions

**All edits here preserve curator quotations byte for byte.** Correct analyst prose, evidence grades, and ownership links. Read all five theory owners before updating their claims. Change a row and its section afterword together. Preserve result IDs and the complete underlying history; compress dead findings in theory rather than deleting their evidence. The canonical [theory index](https://github.com/EmotiveAutomaton/sounding-line/blob/7384809b00760f984120f8c8a59d16f6e84768df/docs/theory/README.md) owns the vocabulary and five-file structure.

### D1. Absent drives do not imply an artifact is impossible

**Targets:** `docs/theory/THREE_COGNITIVE_LAYERS.md` §3, analyst paragraph beginning “Three consequences,” particularly “Absent drives are constraints”; `ALIGNMENT.md` §0 analyst afterword.

The strong construction claim conflicts with the curator's explicit retraction in ALIGNMENT §0. Replace it with the already-ratified narrower proposition: different motivational weightings can produce the same action or artifact; differences may become visible in other choices and constraints. Absence is not automatically observable, nor proof the maker could not produce the artifact. Preserve the separate proposed specificity test and its unrun status. Remove analyst restatements that silently reinstate the stronger claim.

**Acceptance:** Neither owner claims missing motivation makes the artifact impossible; both agree about the retraction and unresolved recoverability. No curator quotation changes.

### D2. Separate non-identifiability from useful narrowing

**Target:** `THE_TRIPLE_INFERENCE.md` §7 literature table, the “Recovery stays impossible with unlimited episodes” row, and G138/afterword wording.

The table calls the literature contested while the afterword concedes the theorems and reports bounded narrowing. Replace the broad row with an assumption-specific statement: observations alone do not uniquely identify reward jointly with an unrestricted unknown planner; substantive priors restrict the admissible family. [Armstrong and Mindermann](https://arxiv.org/abs/1712.05812) explicitly distinguish observations from the additional assumptions needed. Useful predictive narrowing under those restrictions is the project's empirical question. Do not claim the human setting refutes the theorem. Describe G138 as bounded posterior narrowing in its toy family, not demonstrated asymptotic convergence or general historical recovery. Preserve its numbers and limits.

**Acceptance:** Row, afterword, and public gloss consistently distinguish uniqueness, predictive equivalence, and finite-data narrowing. Retain the actual cited theorem's assumptions rather than generalizing from its title.

### D3. Retire stale reader-heuristic support language

**Targets:** `READER_HEURISTICS.md` §2 HH-3, its afterword, §11 dashboard probe-activation row, maker-reader similarity row and adjacent summaries; cross-check `DECISION_TRACES.md` HH-3/L39 and `READER_HEURISTICS.md` §1 L225/L251/L236 history.

The dashboard still promotes the initial human-versus-machine activation comparison while the trace owner records its deflation to register/family and rejection as a provenance mechanism. Preserve historical numbers but label the original interpretation superseded. The current interpretation is model/register sensitivity with mechanism unresolved, not general human provenance detection.

The family-similarity dashboard still implies weak-rewrite survival excludes artifact dialect. Stronger independent erasure later removed the advantage with both families above their floors. Retain original-artifact support, weaker-rewrite results, corrected full-matrix aggregation, the strong-erasure null, and the retrospective nature of later splits. Shared organization and shared convention remain rivals. Do not delete the original relation or promote a mechanism its stronger control did not preserve.

**Acceptance:** Each affected row and afterword says the same current thing as its owning history. Search claim phrases as well as IDs so the summary does not retain the superseded conclusion. No silent upgrade of retrospective robustness to untouched confirmation.

### D4. Remove guarantees from the dormant alignment proposal

**Targets:** `ALIGNMENT.md` opening analyst anti-capture paragraph, §0 afterword, §1 “safe and useless” sentence, §3 lead-in and AL-2/AL-5 consistency.

The opening asserts protection and forced population breadth; §3 correctly says these do not follow. Replace the opening assertion with an untested proposal: an objective retaining uncertainty and action might favor broader evidence, but reference population, sampling, aggregation, and the weighting governor remain unspecified. No guarantee of capture prevention, safety, or breadth has been established. Bring §3's lead-in into agreement. Information seeking can itself involve consequential action, so remove the contradictory statement that an epistemic agent never acts and is therefore safe.

**Acceptance:** Hypothesis, conditions still needed, and dormant status agree throughout. Preserve curator aspirations as quotations. Do not wake an alignment research program or import a new objective under an errata label.

### D5. Correct the artifact-versus-action prior-art claim

**Target:** `DECISION_TRACES.md` §9 naming discussion, analyst parenthesis claiming inverse planning takes action sequences while this project's contribution is residue.

Finished-artifact inference is already part of inverse-planning research. [Hurwitz, Brady, and Schachner (2019)](https://bradylab.ucsd.edu/pdfs/HurwitzBradySchachner2019.pdf) explicitly models inference from completed tools, including availability and functional constraints. Correct the categorical exclusion and add the source to the existing literature owner. A concise replacement is: “Inverse planning is a close neighbor, including inference from finished artifacts. Our proposed extensions require separate evidence.”

**Acceptance:** No first-artifact-inference claim remains supported by the old distinction. Mark the intended differentiation as pending the analyst–curator theory discussion; do not unilaterally ratify a replacement theory. This is a factual attribution correction, not a requirement to rename the project or discard its ambition.

## 6. Workflow fold-ins

### W1. One current operational summary, with explicit authority and dates

**Targets:** Existing `docs/STATE.md`, `CLAUDE.md`, stage contracts, and existing operating-loop owner. Do not create another permanent protocol or a sixth theory document.

Put the operative stage pointer, current scope, scientific grade, actual budget exception, freeze/closure state, and next eligible action at the top of the existing state document. Date older general instructions and resolve their applicability explicitly. Reconcile unconditional queue-loading prose with actual frozen stage boundaries; a general instruction to keep work running cannot justify invented filler, extending a frozen campaign, or turning an analysis-only task into an experimental launch. Preserve previously authorized work and normal agent autonomy.

Latest explicit curator corrections govern; current source evidence governs factual claims. Historical context attachments are orientation, not an override of newer ratified theory. Keep repository state and live-machine observations labeled separately. Do not overwrite the current task-scoped subagent policy with a new permanent policy merely because subagents were explicitly authorized for this research round.

### W2. Install the requested verbal-discussion format

**Targets:** `CLAUDE.md` curator-first theory loop, existing analyst operating-loop/reporting instructions. Announce changes to CLAUDE as it requires.

Preserve the ordinary short Pass A. Add the explicit stage-level override requested September 5: **ten philosophical, example-led prompts; first five prioritized, next five optional.** Begin with concrete situations involving makers, works, readers, directors, authors, or ordinary design. Use open questions that support a wandering verbal response. Do not ask the curator to choose statistical knobs, code architecture, or an unranked menu of polished theoretical answers.

Before the walkthrough, provide the evidence and live tensions without answering the examples for the curator. After the response, reconstruct the strongest account, distinguish curator statements from analyst additions and literature imports, challenge narrowly, and then produce one operational handoff. New load-bearing definitions still require the existing theory-change conversation unless choice is explicitly delegated. Routine implementation remains agent-owned.

**Acceptance:** The at-most-three ordinary interrupt and the explicitly requested ten-question stage pass have clear scopes; neither silently cancels the other. The handoff preserves quotations and uncertainty and does not turn an agent's research proposal into curator ratification.

### W3. Keep administrative completion, scientific warrant, and pursuit separate

**Targets:** Existing result schemas/helpers, findings, theory rows/afterwords, closure/report owners, pursuit and warrant ledgers.

Reuse existing machinery to distinguish execution resolution, instrument integrity, scientific outcome, report delivery, curator processing, and chosen pursuit. A valid null is useful completed work. An invalid instrument does not refute its target hypothesis. A held discovery criterion is not confirmation. Internal subagent review is not independent replication. A theory worth pursuing can have weak current warrant.

For a repaired instrument, record affected dependencies: hypothesis → method → result → interpretation. Repair only conclusions relying on the defective component; preserve unaffected evidence. Use the theory index's established confidence vocabulary. Do not introduce new confidence adjectives to make equivalent results look stronger.

**Acceptance:** One representative invalid result, valid null, discovery positive, failed confirmation, and blocked branch remain distinguishable through every aggregate. A row reversal propagates to its afterword and public summary while its history remains available.

### W4. Make source identity and recovery receipts useful, not ceremonial

**Targets:** Existing manifests, capsule/source-lock builders, model stamps, repair logs, resume validators, and operational lessons.

Preserve and verify the actual imported/copied source closure, model revision, adapter identity, dataset split, scoring version, and result lineage. A repository commit alone does not identify dynamically loaded code or ignored adapter weights. Stage 8's latest commit correctly says weights remain excluded by the safetensors ignore rule; keep the hash/location manifest accurate without requiring weight files in git. Retain its repaired protection against resolving into the closed Stage 7 root.

Failures should resume from verified compatible evidence, not overwrite it. Keep original attempts and supersession links. Use small adversarial fixtures against existing validators rather than introducing another framework or a documentation rewrite campaign.

## 7. Delivery, verification, and rollback

Each repository's coding agent should implement only its assigned repository unless separately tasked with both. Read the other repository as needed for interfaces. Cross-repository scientific claims require explicit evidence links; one repository's success does not grant the other's admission.

Deliver a reviewable branch/PR with: item IDs addressed; before/after behavior; exact deterministic checks; unresolved limitations; source/evidence hashes used; whether the patch is staged or installed; and the process boundary used if installed. Link existing owner documents. Keep a short unresolved list rather than silently expanding scope.

Ghost test anchors include `tests/test_v15_gates.py`, `test_v15_metamorphic.py`, `test_v15_runtime.py`, and `test_v15_fresh_clone.py`. Extend defect-specific coverage. Sounding fixtures should exercise admission, closure, slot identity, and scorer counterexamples without GPU/server calls. Do not change a test simply because preserving an audited historical failed gate makes a broad “everything committed passes” assertion uncomfortable; distinguish historical evidence from current apparatus validity.

Rollback reverts source changes and labels superseded derived reports. It never erases receipts, rewrites scientific rows, restores stale registries over newer evidence, or resets a clock. If a safe live cutover is unavailable, finish the isolated patch and apply derived-report corrections after collection. No global shutdown, new participant recruitment, additional spending, new scorer deployment, or expanded experiment schedule is authorized by this document.

The companion research briefing contains proposals for the next scientific discussion. Those proposals are deliberately outside this maintenance checklist.
