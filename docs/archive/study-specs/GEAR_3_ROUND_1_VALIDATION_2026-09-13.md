# Sounding Line Gear 3 Round 1: revised validation and pre-run repair handoff

**Revision 2 — 2026-09-13. Campaign: G3-S10-READER-1.**

This replaces the earlier September 13 validation handoff. It consolidates its outstanding repairs, adjudicates `GEAR3_ROUND1_CRITIQUE_2026-09-13.md`, and adds two observed confounds in the procedure-naming comparison. The original commissioned study remains the authority for the budget, models, sources and scientific arms. This document is an assessment and implementation handoff; the analyst has not changed the repository or operated cloud resources.

**Recommendation:** finish a bounded repair pass and run the usable commissioned comparisons. Do not replace Round 1 with a new model, corpus or human inference architecture. Its useful deliverable is a comparison of prediction interfaces, evidence and representations. The existing human rule arm cannot establish a persistent model of a writer. Make that boundary executable in the report rather than allowing its name to carry a stronger claim.

**No further curator decision is needed for the repairs below.** A frontier API arm, human history-likelihood inference, cross-session familiarity, or a different primary evidence view would require a separately specified study. They are not prerequisites to this launch.

## 1. Current state and evidence

The latest inspected branches, checked again at the end of source review:

| Branch | Commit | What changed since the previous validation |
|---|---|---|
| `codex/gear3-round1` | `a12a68a12f8fc5681cf015ef1232ed63404868dc` | Records discarded-pilot launch; no implementation changes |
| `main` | `d9b6f5c772e9fa437683e379f5c9d73949af64f8` | Records the same launch and its initial ledger reservation |
| Code used by the launched pilot | `54aac56f60f234f44daece930c1b06ffabb51a4b` | The source reviewed in the preceding validation |

The [launch receipt](https://github.com/EmotiveAutomaton/sounding-line/blob/d9b6f5c772e9fa437683e379f5c9d73949af64f8/results/gear3/G3-S10-READER-1/PILOT_LAUNCH.json) records CPU-cache submission followed conditionally by the L40S pilot, with a **combined reservation ceiling of $2.45**, within the $3 pilot allowance. It records launch, not completed device admission or actual charges. Main-study dispatch still awaits the returned pilot, measured sizing and the final consumer. The public snapshot does not establish the live provider state.

**Method:** compared the new commits with the previously inspected source; read the adversarial critique in full; reread the relevant theory and all changed theory passages; traced human and Ghost execution, memory packing, scoring, sampling and cost controls; reran the six earlier constructed reproductions; and added bounded checks of rule readout, lapse arithmetic, dependency grouping and both naming paths. Checked relevant provider documentation.

**Evidence limits:** these were local source/fixture checks, with no model or provider calls. The repository reports 42 focused offline checks and five subsequent privacy checks; the analyst did not rerun that complete suite. Its private source fixtures, pytest and Modal SDK were unavailable here. Actual scientific forecasts, current billing and returned cloud-pilot evidence were not available for this review. A constructed failure demonstrates a code path, not that the real campaign already suffered it.

All six previous reproductions still hold because the implementation has not changed. In particular, the latest launch commit does **not** implement the previous repair handoff.

## 2. What this experiment can contribute to the theory

The theory's live question is whether a reconstructed maker model constrains unfamiliar behavior beyond shared domain competence and strong direct prediction. It distinguishes reenactable routes, historical correspondence and motivational inference. Neither an executable object nor a correct next-choice prediction alone establishes all three. See [THE_TRIPLE_INFERENCE §2](https://github.com/EmotiveAutomaton/sounding-line/blob/a12a68a12f8fc5681cf015ef1232ed63404868dc/docs/theory/THE_TRIPLE_INFERENCE.md) and [DECISION_TRACES](https://github.com/EmotiveAutomaton/sounding-line/blob/a12a68a12f8fc5681cf015ef1232ed63404868dc/docs/theory/DECISION_TRACES.md).

Keep the experiment's questions and their limits explicit:

| Comparison | What a useful result would license | What it would not establish |
|---|---|---|
| Human A: direct, deliberation and proposed rules, at 9B and 27B | Whether this text-conditioned rule/vote interface improves next-menu handling prediction, and how its benefit changes between packages | A recovered, persistent writer model; human goals, expertise or historical process |
| Ghost opportunity A | Whether proposals combined with the existing native likelihood model improve prediction on the declared constructed worlds | Human invertibility or a universal size boundary |
| Ghost reading A | Whether proposed libraries support useful native forecasts; separately, whether proposed routes recreate visible artifacts | That reconstruction success caused the forecast benefit or matched the historical route |
| B: correct, other-writer and absent history | Whether the writer's session-local sequence of earlier handling labels improves prediction beyond the matched alternatives and persistence control | Cross-session familiarity, a learned biography, or stable personal values |
| C: examples, procedures and grounded annotations | Whether permitted representations help prediction, and whether grounded descriptions help when all other supplied information is held fixed | Recovery of the writer's historical internal procedures; reproduction of LILO |
| Artifact-only portion of B | Prediction from the current draft and displayed menu on the matched B population | A general finished-artifact recovery result, or the whole A population |

The human rule limitation is real. `human_programs.evaluate()` applies task-specific proposed threshold rules to fourteen already visible features, weights them equally, and adds fixed lapse. There is no likelihood fit against earlier draft/menu/action triples and no requirement to keep a writer hypothesis fixed across later decisions.

But the critique overstates this as “nothing inferential.” The proposer sees the text and can encode a content judgment in the selected rules and their action votes. Those votes affect the probability forecast, not only the separately generated choice. The correct boundary is **no demonstrated persistent or retrospectively tested maker model**, not absence of any inference.

This matters especially for C: human procedures are induced from training records, but the final R4 proposal is still made afresh for each target. C can test representation assistance; it does not automatically test persistent personal modeling.

**Pursuit value:** distinguish proposal, representation, evidence and readout bottlenecks cheaply, and identify a worthwhile next mechanism. **Warrant:** descriptive comparisons on exposed human records and constructed cases. Preserve the broader theory as an open ambition; do not promote or reject it from these proxies.

## 3. Fixed commission and execution order

Retain the original archived [Round 1 specification](https://github.com/EmotiveAutomaton/sounding-line/blob/a12a68a12f8fc5681cf015ef1232ed63404868dc/docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md), SHA-256:

`6fbd1e32b63db00d8350812ab7d627e06d4ab6ef87a3d8fc3c1b199fda4596f9`

- Gross budget before credits: **P $3, A $17, B $7, C $9, D $4, Reserve $10; total $50**. Initial P+A ≤ $20; ordinary planned work ≤ $40. Lower verified account headroom still applies.
- Existing pinned 9B/27B packages, Ollama image, one L40S container, two physical CPU cores, 32 GiB RAM, one active model and one request at a time.
- Existing arms, output allowances, source allocations, conservative context checks, human rule family/lapse and native Ghost laws.
- No model selection, cohort selection or calibration fitting on evaluation outcomes. No new global audit, provider migration, training, scraping or corpus adapter.
- One canonical campaign ledger across worktrees; historical entries and unknown charges survive. Credits do not enlarge the $50 allowance.
- Complete paired blocks, finite native supervision, no periodic LLM wakes, no minimum expenditure or GPU occupancy.

Use four bounded work units rather than ten separate implementation projects:

1. **Controller and accounting:** V1, V4, V6 and V10.
2. **One offline consumer:** V2, V3, V5 and V8.
3. **Sampling and C pairing:** V7 and V9; C-specific work need not block a ready A/B path.
4. **Inspect the existing pilot, freeze affordable work, then execute.**

Aim for a few focused hours, not another multi-day setup cycle. If an optional enhancement grows, defer it. If a required repair remains unresolved, identify the affected branch and run other usable commissioned branches when their prerequisites hold. Shared spending, leakage or replay defects cannot be bypassed to save time.

At implementation start, read the current operator handoff and inspect the existing pilot's native/provider identities. Do not edit a running owner's source, reset its ledger, launch a duplicate pilot or infer failure from stale Git status. If the pilot has ended, retrieve its evidence first. Apply repairs to subsequent dispatch and verify returned evidence under its original producer identity.

## 4. Required repairs

### G3-V1 — An obstructed cancellation must not prevent application stop

**Observed/reproduced.** `runners/gear3_round1.py::request_stop()` calls cancellation before AppStop. Holding the first callback on an event prevents the app-stop callback from starting.

**Repair.** Attempt the bounded AppStop path first, or independently within a fixed deadline. Give call cancellation its own bounded path; a blocking SDK call must not obstruct the other stop attempt. Preserve the verified client/workspace, original expiration and unresolved-owner reservation.

**Acceptance.** Block cancellation, raise from cancellation and fail AppStop in focused fixtures. The independent stop attempt still occurs; unresolved ownership prevents further dispatch; no path falsely records verified termination. Validate the installed SDK adapter's signatures/imports without creating resources.

This is a reproduced ordering hazard, not evidence of a real provider hang. Provider execution timeouts remain useful redundancy but are not a substitute for the absolute campaign deadline.

### G3-V2 — Verify derived science from raw evidence, not just mutually consistent caches

**Observed/reproduced.** `ollama.call()` checks bindings and raw hashes on resume but returns saved parse/status/cost fields. Several completed human/reading routes return saved `ROUTE.json` after inventory checks. `gear3_batch.run_block()` and `verify_completed_blocks()` can therefore revisit caches without redoing all claimed semantic work.

The reproduction changed a cached uniform forecast to a point mass while leaving its raw response unchanged; direct resume accepted it. An unchanged outer inventory would catch that particular file edit. The deeper issue is a self-consistent archive whose derived values disagree with its raw evidence.

**Repair.** Add one reusable offline verification path, invoked for reused partial units, completed blocks, returned archives and final scoring:

1. Reconstruct the literal request using the original task, representation, feedback and profile.
2. Reparse the retained raw response; recompute validity, forecast/proposal and every raw-exposed cost field using the required key set.
3. Re-execute proposed human rules and native Ghost candidates from permitted public inputs in a fresh scratch output, with all model APIs forbidden.
4. Recompute feedback, mixtures and the route's final readouts; compare them with retained derivations.
5. Verify request order, source identity, inventories and completeness separately.

Reuse existing parsers/executors. This is not a second research runner. Record verifier identity separately from producer identity. Preserve original files, including invalid responses; never silently repair a saved forecast or rewrite its source hash.

**Acceptance.** A cached parse inconsistent with RAW fails even after internal inventories are consistently refreshed. Wrong execution, mixture, cost or next-round feedback fails. An intact archive, including validly recorded invalid attempts, reproduces with model access disabled. Partial reuse and complete return use the same verifier.

### G3-V3 — Complete the consumer and check affordability of the whole admitted plan

**Observed.** The review and current status explicitly leave the final evaluator join/packet unfinished. `gear3_sequence.run_plan()` validates job identities and dependency order, but not an aggregate affordable study. Per-invocation reservations protect spending; they can still leave an unnecessarily incomplete scientific prefix.

**Repair.**

- Implement the local answer join and A/B/C/D consumer before paying for their main forecast bank. Bind it to the frozen public population and private evaluator hashes; keep answers out of cloud bundles.
- Prove one small synthetic end-to-end case through plan, archive, verification, answer join, contrasts and final report with no model calls.
- After inspecting P, size a full admitted core using measured route demand, 25% execution margin and measured startup/load/export overhead. Derive a deterministic affordable prefix; identify the maximum candidate roster separately from the admitted roster.
- Check the admitted core against every applicable branch, initial, ordinary, campaign and workspace limit, including already booked P and uncertain costs. Preserve the locked per-job check at dispatch.
- Bind pilot admission to its actual source, model/configuration, reservation and verified output evidence. A hash around an arbitrary `PASS` Boolean is insufficient.
- Check B/C dependencies against the A events actually admitted. An aspirational full tree may have a not-admitted tail, explicitly identified in PLAN; it must not masquerade as an affordable commitment.

**Acceptance.** An individually affordable set that exceeds a whole-plan limit refuses before its science begins. A valid smaller plan produces complete contrasts and explicit excluded/unstarted inventory. Missing outcomes, duplicate events, mixed targets, incorrect donor joins and fabricated pilot admission refuse. Valid invalid-attempt records count as attempted failures; unattempted work does not receive invented forecasts.

This is one minimal consumer, not a requirement to finish every deferred Stage 10 analysis first.

### G3-V4 — Count each cost once; keep estimates distinct from settled charges

**Reproduced.** With $18 already booked and then reflected in the provider's usage meter, a subsequent otherwise affordable $9 job is refused because `account_campaign_cap()` subtracts metered use and `account_reservation_guard()` also subtracts the same campaign bookings. In the constructed example, $18 + $9 + $10 reserve + $1 storage fits a $50 gross ceiling.

**Repair.** Keep two explicit constraints:

- the campaign's original allocation, charged against its verified charges and outstanding/uncertain reservations;
- current workspace headroom, charged against additional work and costs not already reflected in that same meter.

Only remove overlap that can be attributed to campaign charges already included in the snapshot. Retain conservative uncertainty when attribution is unavailable. Bind the baseline, refreshed snapshots, attribution evidence and billing cycle; do not reset the campaign or ignore other usage.

Also populate terminal service estimates separately from provider-confirmed charges. Retain the original reservation and an append-only settlement event. The critique's proposed `duration_seconds × rate` substitution is **not** sufficient to release the entire hold: worker duration excludes some startup/export lifecycle time and is not the provider invoice.

A verified provider-attributed settlement may reduce the outstanding hold, under the ledger lock. Without adequate evidence, keep the reservation and report the resulting unspent capacity honestly. Do not make a new billing-integration project necessary to launch.

**Acceptance.** An unchanged economic situation has the same dispatch decision before and after an attributed meter refresh. Unrelated usage reduces headroom; unknown spend stays reserved; settlement cannot resurrect spent branch/campaign capacity or reset at a new cycle. Show reserved, service-estimated, provider-confirmed and unresolved amounts separately.

### G3-V5 — The “direct model difference” must use R0

**Reproduced.** `gear3_comparison.interaction()` currently labels the 27B-versus-9B **R2** comparison `direct_model_package_difference`.

**Repair.** Rename that field to its actual R2 meaning, and have the consumer compute the genuine paired **R0** model contrast. Keep the four-cell R2/R3 interaction unchanged and report R3–R0 for both models.

**Acceptance.** A fixture with identical R0 predictions and different R2 predictions reports zero direct-model benefit. Altering only R0 changes only its appropriate contrast. No inference rerun is needed.

### G3-V6 — One recovery means one for the original interrupted work

**Reproduced.** `CampaignLedger.reserve()` can admit a recovery of a recovery because it checks the immediate parent rather than the original lineage. The reproduced third attempt retained the original deadline and counted costs; it violated the one-recovery rule, not those two guards.

**Repair.** Reject a recovery whose parent is itself a recovery, or enforce an explicit root-work identity and one recovery count. Bind recovery to the same original work; a new invocation name is not a new entitlement. Preserve the prior-owner-ended requirement, original expiration and all costs.

**Acceptance.** Original → one verified recovery is legal; a second sibling, chained recovery or changed work payload is refused. An unknown owner never enables a retry. Keep existing ledger events; do not migrate by deleting old reservations.

### G3-V7 — Enforce the commissioned breadth and subset rules

**Reproduced/risk.** `gear3_inputs.roster()` admits eight B opportunities per writer in a constructed three-writer fixture, despite the initial maximum of two. Ghost ordering ranks tasks without enforcing distinct-case coverage before extra queries. Actual private roster violations were not established by this audit.

**Repair.** Enforce A's maximum eight events per writer and initial B's maximum two; select Ghost cases before additional task queries from a case. Preserve deterministic identity-based ordering and declared source strata. Resolve B donor eligibility and C overlap against the actual affordable A population.

**Acceptance.** A synthetic roster with abundant records per writer respects both caps, prefers new Ghost cases and preserves every retained counterpart. Report distinct events, writers, sessions, prompts, Ghost cases and connected dependencies, plus exclusions and the candidate/admitted distinction. Do not duplicate evidence views to reach a count target.

### G3-V8 — Make the interpretation and cheap readout diagnostics explicit

**Observed and mathematically checked.** For four human actions, if `f(a)` is the fraction of proposed rules returning action `a`, the implemented forecast is:

`q(a) = 0.05 + 0.80 × f(a)`.

On the task being scored, replacing each rule with a constant program returning its executed action leaves the probabilities identical. This demonstrates why a good score cannot distinguish a reusable behavioral rule from an action-voting representation on its own.

**Repair in the consumer/report, without new paid arms:**

- Keep human handling, Ghost opportunity and Ghost reading separate, further separated by target and evidence view. The existing freeze already prohibits pooling human and synthetic outcomes; retain that rule.
- Use the meanings in §2. Describe human R3 as task-specific proposed handling rules; do not label its score persistent maker reconstruction. Report B as session-local history specificity.
- Preserve original probability scores, generated-choice accuracy, probability-argmax accuracy with the existing tie convention, validity, calibration and costs.
- Add a fixed, secondary **same-confidence choice diagnostic** for each human arm: map its already recorded generated choice to 0.85 and each other action to 0.05, then score it on the identical population. Invalid attempts remain invalid. Freeze this formula before opening the joined outcomes; fit nothing and replace no original forecast.
- Report human rule count, action-vote concentration, constant-rule share, and agreement between generated choice and executed-mixture argmax. Label any rule collapsing as a readout identity, not an ablation of model reasoning.
- For Ghost, separately report candidate support, evidence fit/model mismatch, legal reconstruction, visible-artifact matching and predictive performance. A successful reconstruction is not automatically used as a forecast validity gate in the present implementation; do not silently change that rule.
- Retain prompt/donor/constructor-linked components. Report actual support and component contrasts. Fewer than ten components remains descriptive leave-one-component-out reporting, not a population interval.

**Why this is worth doing.** If a structured arm's proper-score gain disappears under the common choice readout, calibration/mixture representation is a live explanation. If its generated choices improve too, there is additional predictive usefulness, still without proof of persistent writer reconstruction. This supplies a next-step discriminator at zero extra inference cost.

**Acceptance.** Check the exact vote formula and constant replacement on constructed rules. Preserve original forecasts byte-for-byte. Verify four-class choice projection, invalids, ties and option-label permutation. A source-family/view mixture refuses; no output field turns a narrow null into a theory-wide conclusion.

### G3-V9 — Make C's naming conditions differ only in the declared descriptions

**New, verified in both paths.**

**Human:** `human_memory.represent()` gives grounded procedures `training_uses` counts as well as descriptions. `human_memory_routes.representation_for()` strips both from opaque procedures. A constructed cloud-profile call returned matching/exceptions counts of 6/0 only to the grounded arm. Definitions and examples matched; supplied information did not differ solely in grounding.

**Ghost:** `reading_routes.route()` reserves the actual bytes of each naming condition before calling `reading_memory.examples()`. Longer grounded descriptions can change the selected episodes. An isolated packing fixture admitted a complete episode with opaque definitions and rejected it with grounded definitions. This was a representation-boundary fixture, not a claim about an actual exported Ghost task.

**Repair for C only.**

- Derive one common representation from the same learned library and public task. Preserve numeric training-support metadata in both naming conditions; vary only the declared description field. Alternatively omit it from both, but choose once before science and record the choice. Prefer keeping it in both.
- Pack once using the longer grounded representation and the full serialized wrapper, including field names, metadata and descriptions. Select identical ordered procedures and complete episodes for both conditions; then remove only descriptions for the opaque condition.
- Apply this rule to human and Ghost paths. Retain the same storage ceiling and shared feedback/context reserve. No padding, evidence clipping, different examples or target-label-derived names.
- Enforce a pair invariant after stripping descriptions: the two supplied memory objects must be identical. If a shared store cannot be admitted, give both conditions the same explicit disposition under the existing contract.
- Keep historical local attempts unchanged. Bind the repaired cloud path to its own source/request identity; do not make old archives appear to have used the repaired contrast.

**Acceptance.** Exercise nonempty and empty libraries, support metadata and a near-cap complete-episode fixture. Removing the description field makes paired representations identical, their ordered examples match and both fit their declared limits. Repeat this check on the actual selected C roster before dispatch, without evaluator access.

This restores the original naming comparison; it does not introduce a new scientific arm. If C is not ready, defer C rather than delay usable A/B work.

### G3-V10 — Pin and verify the small SDK adapter actually being used

**Observed/risk.** The controller imports private Modal synchronization/protobuf surfaces. The inspected root `requirements-lock.txt` does not pin Modal. The critique reports version 1.5.4; the analyst cannot verify the operator's installed version from this snapshot. A `shellingham==1.5.4` entry is not a Modal pin.

**Repair.** Record and pin the actual validated controller SDK version, preferably in a small Gear 3 environment specification rather than altering unrelated local dependencies. Include controller Python/SDK identity in dispatch receipts. Keep the private surface behind the existing small adapter, and check its imports and method signatures before reservation. Do not upgrade merely to match a version quoted in the critique.

**Acceptance.** The actual pinned environment can construct/import the adapter and pass the bounded mocked workspace/stop tests. An unsupported environment refuses before resource creation. Changing this controller pin does not overwrite the source identity of an already launched pilot.

## 5. Disposition of the adversarial critique

The identifiers below refer to the supplied critique. “Keep” means adopt the concern or its bounded diagnostic; it does not accept every inference drawn from it.

| Critique | Disposition and reason |
|---|---|
| 2.1: human R3 is effectively an action selector | **Keep the central limitation; qualify the wording.** The threshold/mixture mechanism is verified. It does not retrodict prior situations or preserve a writer model. Text judgments can still influence candidate votes. Implement V8. |
| 2.1: A pools human and Ghost into one inverse-inference statistic | **Do not adopt.** The commissioned spec and Stage 10 freeze explicitly require separate populations; the scorer rejects mixed dimensions. The unfinished consumer must maintain that separation. |
| 2.2: 9B/27B cannot close the size/interface/identifiability question | **Keep the claim limit.** This is a package comparison with asymmetric evidential value, not a decisive size test. |
| 2.2: a frontier null would close the size branch | **Reject.** A frontier reader can also fail because of elicitation, interface, hypothesis support or the target. Stronger capability evidence would be useful but would not uniquely identify the cause of a null. |
| 2.3: small clustered support limits sensitivity | **Keep.** The receipt verifies fourteen evaluation writers and three prompts. The actual selected graph, particularly with history donors, must be reported. |
| 2.3: a roughly 0.1 minimum detectable interaction is established | **Not established.** Its assumed variance and covariance are not measurements of this four-cell contrast. Local 9B variance alone cannot determine a 9B/27B interaction's sensitivity. |
| 2.3 / mechanism 7: shared prompts cancel, permitting exact writer sign flips | **Reject as a general rule.** Pairing removes a common additive prompt effect, not prompt-by-method effects. These fixed algorithms were not randomly assigned labels within writers. Exact independent sign flips require additional symmetry/exchangeability assumptions, including dependence handling. Do not weaken the existing graph or add a significance gate. |
| 2.4: records are being mistaken for artifact evidence | **Keep the distinction; not a hidden substitution.** A explicitly commissions the process-record view; B contains the artifact-only contrast. Show both at their actual scope. |
| 2.5 / mechanism 10: local 9B results make cloud repetitions redundant | **Reject for this commission.** Same-cloud execution was explicitly accepted. Different request/profile identities and cloud pilot exclusions from training also matter. Sixteen agreeing tasks would be a diagnostic, not proof that unobserved local/cloud counterparts are interchangeable. |
| 2.6: lapse can impose an unfavorable calibration profile | **Keep.** The single-rule arithmetic is correct; see below. Multiple rules produce different concentration levels. |
| 2.6: lapse predetermines loss and cancels from the interaction | **Reject.** Accuracy and vote concentration remain empirical. A common lapse changes the two R3 losses differently and need not cancel. Use fixed secondary diagnostics, not post-outcome calibration. |
| 2.7 / mechanism 2: enumerate the native support | **Useful optional diagnostic, with corrected meaning.** A declared-support reference can distinguish proposal coverage from prediction. It is not automatically a performance ceiling or a known human law; see §6. |
| 2.8 / mechanism 12: session-local history is not cross-session familiarity | **Keep.** Rename the claim precisely; reserve chronology-verified cross-session work for a later study. |
| Mechanism 1: score landed local cells | **Keep within the existing freeze.** Read completed comparisons for defects and context. Freeze cloud identity-based choices first; do not choose arms, cases or calibration from the results. This need not become completion of all Stage 10 work. |
| Mechanism 3: replace the byte bound now | **Defer.** The code intentionally uses UTF-8 bytes as a conservative text-token bound; 16,384 is the configured token ceiling. This narrows admitted evidence and deserves disclosure, but is not evidence that the server's context is secretly 15k bytes. Exact tokenizer/chat-template accounting would change admission and potentially representations. |
| Mechanism 4: settle reservations to worker duration × rate | **Reject that settlement rule; keep the accounting concern.** It is an estimate, not a complete charge record. Apply V4. |
| Mechanism 5: concurrency 2–3 is safe and saves 2–3× | **Not demonstrated; defer.** Concurrency changes memory demand and the journal protocol, and has no measured speedup here. |
| Mechanism 5: run all 9B blocks before all 27B blocks | **Reject as the default.** It sacrifices the commissioned complete-block order. A smaller optimization preserves that order; see §6. |
| Mechanism 6: pin SDK, prepare local-disk weights | **Pin the validated SDK.** A disk-copy fallback is conditional on measured load overhead, not a prerequisite or known performance improvement. |
| Mechanisms 8–9: new history-weighted R3 and artifact-primary A | **Separate study design.** These change the method/evidence, not merely repair its implementation. Do not silently substitute them. |
| Mechanism 11: frontier API or 70B/A100 | **Credible future option, not this repair.** Requires a provider/model profile, token/charge accounting, source-handling review and matched comparison. Another size point still does not isolate parameter count. |
| Stress tests: local offload and excessive setup | **Useful management cautions, not measured alternatives.** No measured local 27B throughput or free capacity was provided. Existing sunk engineering is not a reason to run an unusable cell. Stop adding infrastructure once the listed obligations are satisfied. |

### Lapse arithmetic and interpretation

For one rule, the four-way forecast is 0.85/0.05/0.05/0.05. Half-Brier loss is **0.015 when right and 0.815 when wrong**. For the illustrative prior 0.51/0.25/0.23/0.01, prior loss is 0.3122 and the crossover accuracy is **62.85%**. These are arithmetic examples, not an estimate of the actual selected cohort.

Two disagreeing rule votes give 0.45/0.45/0.05/0.05 and loss 0.255 when the truth is among the two, 0.655 otherwise. The arm therefore does not have one universal confidence.

A constructed interaction with equal R2 scores, an incorrect 9B rule and a correct 27B rule changes from 0.8 to 0.6 when both R3 lapse settings change from 0.15 to 0.30. This directly disproves automatic cancellation. Retain the commissioned 0.15 setting and diagnose it; do not tune it on evaluation outcomes.

### Frontier pricing: plausible alternative, not a ready replacement

The official page currently lists Opus 5 at $5/$25 per million input/output tokens and Fable 5.1 at $10/$50, with batch prices halved; Sonnet 5 is $2/$10. At exactly 3M input and 0.3M output tokens, the calculated standard/batch costs are $22.50/$11.25, $45/$22.50 and $9/$4.50 respectively. The critique's affordability direction is credible. These are token-cost scenarios, not a measured whole-tree budget. Its roughly 675 calls cover A–C for one reader before P, D and contingencies; a bytes-to-English-tokens estimate is not a tokenizer guarantee. [Official pricing](https://platform.claude.com/docs/en/about-claude/pricing).

## 6. Optional improvements that must not delay the repaired study

### A. Native full-support diagnostic

Reuse an already available, source-matched native reference first. If absent, a small **local-only descriptive analysis** may enumerate the declared public hypothesis support through the same exported laws:

- Opportunity: distinct cause × cost × lapse states, with an explicitly stated prior and the existing observation likelihoods.
- Reading: the four library states; find/check a legal visible-artifact reconstruction separately. Do not count several equivalent reconstruction programs as extra prior mass for one library.
- Record the enlarged diagnostic search/evaluation budget. The eight-candidate reader interface is bounded; exhaustive computation is not cost-matched merely because it runs on CPU.
- Report candidate mass covered under the declared reference, discrepancy between proposal and reference predictions, and paired prediction losses. Preserve zero evidence mass as mismatch.
- Do not call it a universal ceiling or report “percent of ceiling.” Finite-sample outcomes can favor another forecast, the chosen prior may differ from the maker distribution, and loss ratios can be undefined or misleading.
- Do not feed the diagnostic posterior to the paid reader or use it to select favorable evaluation cases. No hidden state enters the diagnostic input.

The original spec excludes inventing a new Bayesian oracle solely for this burst. A documented analysis using existing native semantics is potentially useful; a new solver, changed likelihood model or private-state reconstruction is outside this handoff. If it cannot be a small reuse task, defer it. V8's coverage/execution reporting remains required without this enhancement.

### B. Reduce loading overhead while preserving complete blocks

Measure actual loads and useful work from P first. If loads materially consume the budget and several blocks share one invocation, a deterministic alternating model order can reduce switches:

- block 1: 9B then 27B;
- block 2: 27B then 9B;
- continue alternating, completing every block before starting the next.

For K blocks in one persistent worker, this can reduce package loads from approximately 2K to K+1. It changes no task, arm, maximum call count or paired-block barrier. Freeze the order in PLAN before outcomes; verify both orders with mocked dispatch and retain actual timings. If every block starts a fresh container, this optimization provides no cross-block benefit.

Do not introduce parallel requests in this pass. Ollama documents that parallel request processing multiplies context-memory demand; a throughput improvement must be measured, not assumed from the concurrency setting. [Ollama FAQ](https://docs.ollama.com/faq).

### C. Context and storage measurements

Report configured context tokens, admitted prompt bytes, actual prompt-token counts, effective memory allowance and exclusions as distinct quantities. The repeated-character pilot request exercises the conservative admission boundary; it does not establish representative 16k-token throughput.

Keep volume-served weights unless P demonstrates a material loading problem. Modal documents Volumes as a model-serving mechanism with caching; a volume mount is not intrinsically an error. A local-disk copy must count its copy time, disk capacity and lifecycle cost and preserve verified model bytes. [Modal Volumes](https://modal.com/docs/guide/volumes).

Coalesce nonessential journal commits only if measured overhead warrants a small change. Never remove durable request-before-call, raw-attempt or completed-block evidence boundaries.

## 7. Pilot reuse, acceptance and closeout

**Reuse evidence rather than rerunning for new hashes.** Verify the launched pilot against its original archived source/profile and the repaired offline verifier. Controller, sampler and report changes do not by themselves require another full inference pilot. If C's supplied representation changes, check that changed literal path with a scoped discarded example under remaining authorized pilot/repair capacity. If that cannot fit, defer C. Do not reset P, reserve or campaign accounting.

The coding-agent return should include:

1. One repair receipt listing V1–V10 as fixed, not applicable with evidence, or blocked for an explicitly named branch; exact code/environment identities and focused test results.
2. Pilot disposition with verified model/device identity, actual request envelope, memory, load/run/export timing, archives and cost status. Distinguish launch, completion and admission.
3. One finite affordable PLAN with actual selected populations, dependencies, exclusions, optional diagnostic dispositions and no outcome-selected expansion.
4. One working local consumer and a constructed end-to-end output demonstrating that the forecast bank can be turned into the promised comparison.
5. After execution, one final curator packet with separate human/Ghost targets, complete paired contrasts, cheap controls, readout diagnostics, connected support, worked examples and all expenditure/uncertainty.

Run the focused changed-module checks once, plus the named reproductions/regressions. Broaden only for a concrete unresolved risk. Preserve existing public-ledger privacy protections, the standard historical lock checks, source boundaries and original evidence. Do not add recurring supervision, rewrite theory prose or manufacture new curator quotes for this infrastructure landing.

Before accepting science, the consumer must be able to answer:

- Did the larger package improve direct prediction, the benefit of additional deliberation/rule execution, or both?
- On humans, did the advantage involve better generated decisions, different calibration/action mixtures, or only a narrower subset of valid outputs?
- Did session-local history help beyond wrong-writer history, no history and cheap persistence?
- Did reusable representations help, and did descriptions help when procedures, examples and support metadata were identical?
- On Ghost, did proposal coverage, observation fit, reconstruction and prediction move together or separately?
- Which pattern warrants the next experiment, and what remains genuinely unmeasured?

The likely next human mechanism worth specifying is a maker hypothesis inferred from **pre-cutoff situations and actions**, then held fixed or updated under a declared rule and tested on unfamiliar situations. That would address the theory more directly than per-task action voting. It is the next design candidate, not a silent R3 replacement or a reason to postpone all current learning.

**Stop condition for this repair pass:** the ready commissioned branches have correct spending/ownership guards, semantically verifiable evidence, an affordable roster and a functioning consumer with the correct claim boundaries. Then run them. Optional optimization, frontier-model comparison and broader theory development stay off the critical path.
