# Sounding Line Stage 11.2: mechanisms for a persistent maker model

Coding-agent handoff, 19 September 2026. Status: commissioned design, not implemented or executed by the analyst. This is a bounded local research continuation. It is not a Gear 3 Round 2 commission or a browser implementation.

## Purpose and authority

The curator explicitly wants a broader mechanism search: how a reader can represent another maker, retain that representation, update it with context, and use it to reconstruct contributions and goals. The prior emphasis on process records remains useful but is insufficient. Prediction is a validation instrument for the reconstruction, not the sole product goal.

Start useful experiments while implementing later branches. Have a substantive packet ready for the existing Sunday checkpoint, **20 September 2026 at 15:00 UTC / 08:00 PDT**, or an earlier operator-recorded appointment. The Pacific time is an inherited planning assumption, not a claim about the user's location. Late receipt shortens this study; do not silently start another 48-hour clock. If the appointment has already passed, return a bounded ready-to-run packet and seek the next scheduling instruction instead of inventing a new deadline.

Use the current machine allocation and cooling rules, predominantly Gear 1. Existing explicit Gear 2 availability may accelerate this same scope; this document does not raise the allocation. No paid/cloud/API calls, new large model downloads, or bulk private-data ingestion. Sounding Line owns any shared local GPU. Ghost's companion study uses CPU only. Respect the local agent-delegation rule: this document does not commission a fleet of agents.

Reviewed main: `2f4e47fb6758e9b42f961d0d671ab68444e046d3`. Inspect current native state before changing anything. Preserve active workers and all prior manifests/results. Record new source, environment and input pins; do not reset to the reviewed commit. Proposed namespace: `runners/stage11_2/` and `results/phase_2_4_stage_11_2/`. Adapt placement to established conventions without altering old science.

## Read narrowly, reuse aggressively

Read current repository instructions and the five living theory files, following their existing read-progress rules. This handoff changes research priority; it does not replace the theory. Keep curator claims separate from analyst operationalizations.

Inspect these existing assets before creating alternatives:

| Asset | Reuse and limit |
|---|---|
| `soundingline/probe/interventions.py` | Existing block/token-scoped interventions and cleanup. Preserve capability and zero-dose controls. |
| `runners/scout_stage2_geo.py`, `runners/scout_stage2_s8.py`, `results/scouts/s8_transfer.json` | Prior geometry/transfer work. S08 is QUIET one way and INSTRUMENT-FAILED the other; shuffled amplification is an important rival. Do not rerun it under a new title. |
| `runners/stage8/model_server.py`, `runners/stage9/neural.py` | Existing teacher-forced candidate scoring and memory-conscious likelihood path. Normalized candidate likelihood is not automatically calibrated confidence. |
| Current Stage 10/11/11.1 public-capsule, account and scoring paths | Reuse evidence boundaries and saved-response consumers. Do not propagate invalid accounts as if valid. |
| Local resource index / `docs/TOOLS.md` | Verify cached HF model snapshots and the 17 reference-code entries. Some entries are incomplete; inspect a callable path before treating a framework as available. |

Historical cached candidates include Qwen2.5 0.5B/1.5B and SmolLM2 360M/1.7B. Their current completeness must be checked locally. Use the smallest competent installed HF checkpoint for activation work. Ollama Qwen3.5:9b remains useful for the existing direct-reader comparison, but it is a different condition: do not attribute differences between checkpoints/backends to a representation method.

The current reader-family theory records stronger surface erasure removing the earlier own-family advantage. Prior affect decoding also did not establish helpful causal steering at tolerated doses. Preserve both facts in the report. The task is to test a better-specified mechanism, not reset the evidential history.

## Common testbed: state with a job to do

Use a compact constructed maker task before the human bridge. Start with an existing finite-world/task renderer where possible. A thin additional fixture is acceptable; building a new general simulation platform is not.

The latent target has separately manipulated components:

- A persistent preference or tradeoff policy, operationally defined within the fixture.
- Acquired skill/repertoire, which can remain after a local goal changes.
- Current goal and the maker's information/belief state.
- Public context and tools; these need not be known completely to the reader.

Generate choices by actually executing the maker policy. Do not generate a biographical label, ask an LLM to write behavior that matches it, then score recovery of that label as independent validation. Keep generator truth in evaluator-only records. Reader input contains permissible earlier behavior and current observations, never the test target or an oracle state name.

Use four-way action queries where feasible, plus separately scored latent-variable queries. Include ambiguity: different states can explain the same history. Score predictive distributions and equivalent explanations; do not require a unique hidden story where the evidence cannot identify it.

Freeze disjoint training, development and test **maker × world-family × rendering-family** rosters. Hold out meaningful factor combinations, not merely filenames or renamed objects. No test family enters lens fitting, alignment training, layer/dose selection or narrative examples used for tuning. If the first fixture cannot support all three separation axes, report the narrower split and reserve the missing one as the next branch.

Initial size: 64 development episodes and 128 test episodes, organized into counterfactual families with at least 32 distinct maker/world units. Up to four renderings of a case are robustness probes, not four independent makers. Extend to 256–512 test episodes only after measuring the first completed block. Each mechanism uses the same frozen family block. This is a scout; uncertainty estimates use maker/world clusters, and branch selection is disclosed.

### Controls required before a mechanistic null

1. The evaluator and reference policy reconstruct every known-answer fixture exactly.
2. A full-information oracle predicts the defined action distribution; otherwise the target/generator is broken.
3. The reader can use explicitly supplied current state on the intended task. Predeclare a development capability criterion: default at least 70% four-way action accuracy and 80% direct factual-state accuracy on the development set. These are pragmatic admission criteria, not theory thresholds; any revision occurs before test access and is recorded.
4. Intervention hooks at zero dose preserve logits within the backend's measured numerical tolerance and leave no hooks attached after a request.
5. All fitted probes, lenses and patches are checkpoint-, layer-, token-mask- and precision-bound. A map fitted to another model is a transfer experiment, never silently the same instrument.

A failed capability criterion blocks interpretation for that checkpoint/task combination. It does not block CPU comparisons or a different predeclared competent checkpoint. One bounded repair per adapter family is allowed; no repeated tuning against test outcomes.

## Branch queue

Launch M0 immediately. M1–M4 are independent once their minimal inputs exist. M5 and M6 are continuations with explicit admission conditions. A negative result in one branch does not stop the others.

### M0 — persistent executable hypotheses versus direct prediction

Maintain a small weighted set of maker hypotheses inferred from earlier observations. Each includes an executable policy or likelihood over future choices. Compare:

- No-history direct reader and the strongest cheap task predictor.
- Direct reader with the same raw history.
- Persistent, frozen-before-outcome candidate model.
- Matched-length other-maker history/model and shuffled chronology where chronology matters.

Allow candidate revision only after the corresponding observation becomes available. Retain each version and its predictions. Do not optimize only for lower entropy; use held-out predictive performance and an explicit model-mismatch route.

Measure action log loss/Brier score, accuracy, state-query performance, compute cost, and which observations changed the account. Test an immediate goal change with stable expertise, a belief change with stable goal, and a new context that discriminates previously equivalent makers. Compare both equal deployment budgets and amortized cost across repeated encounters; these are different estimands.

**Advance:** if persistent structure helps, test a fresh factor combination. If it ties, test the same predictor under a history/context bottleneck. If it harms, examine stale-state and donor-history cases before one development-only repair. Do not conclude that persistence helped solely because its prompt was longer.

### M1 — Jacobian-lens target-state readout and intervention

Primary source: [workspace paper](https://transformer-circuits.pub/2026/workspace/); source code: [anthropics/jacobian-lens](https://github.com/anthropics/jacobian-lens). Inspect `jlens/fitting.py` and `jlens/hf.py`. Reuse a small pinned portion or isolate the dependency; preserve its license. The released repository is reference code, not a maintained plug-in promise.

Fit on neutral cached text excluded from all study cases. Start with 16 prompts at 128 tokens for timing/numerical checks, then target 100 prompts if affordable. This is a reduced scout fit, not the paper's full reproduction. Select at most two intermediate layers on development cases. Record fit size, precision, gradient cost and stability across neutral-text halves. Do not spend the whole window seeking an ideal lens.

Compare J-lens readouts with the logit lens and a fitted linear state probe. Crucially, then intervene on a target's inferred belief/goal using matched base/donor cases whose evaluator establishes the intended counterfactual. Select concept vectors using training/development data, not attractive test readouts. Include prompt-word echo controls, lexically different renderings, and cases with the relevant belief implicit in observed behavior.

Patching an overlapping frame requires the method's actual projection/update operation; do not treat token vectors as orthogonal. Verify the implemented operation against a small numerical known-answer case. Log patch norms and selected coordinates.

**Primary contrast:** correctly targeted patch versus an equal-norm wrong-target or unrelated patch on counterfactual action likelihood. Report preservation of other state variables and ordinary task capability. A top lens word alone earns no maker-inference claim and no product confidence label.

Evaluator-defined donor matching is legitimate for this causal diagnostic, but it is privileged experimental construction. Report it separately from deployable inference, where donor/state selection must use only public evidence. Never credit an oracle-chosen intervention as an artifact-only prediction improvement.

**Advance:** a selective effect gets an independent rendering or withheld goal/belief combination. A readable but nonselective effect goes to M2's causal alignment. A failed fit gets the single bounded repair, then remains instrument-limited while M0/M2 continue.

### M2 — learned causal alignment, distinct from prior S08

Primary source: [Distributed Alignment Search](https://arxiv.org/abs/2303.02536); implementation reference: [pyvene](https://github.com/stanfordnlp/pyvene). Existing hooks may be simpler to reuse than installing the full framework.

Fit a low-rank alignment for **one** variable at a time: current belief, then goal if the first harness works. Use training counterfactual pairs and evaluate unseen combinations. Default ranks 8 and 32, one development-selected layer first; these are a small comparison, not a wide hyperparameter sweep. Keep the base model frozen.

Compare learned interchange with unmodified activations, a simple mean direction, random equal-rank subspaces, shuffled-variable supervision, and an equal-norm wrong-variable patch. Train and apply with target labels hidden at inference: labels may supervise alignment during training, but the test-time state comes from the allowed history. An explicitly oracle-state injection is reported separately as an upper-bound control.

Include an invertible-rotation-plus-inverse identity check. It should preserve predictions. Any benefit of rotation must arise from a declared bottleneck, selective intervention or learned readout, not the coordinate change alone.

Score correct counterfactual transfer, unrelated-variable preservation, neutral-task change, and held-out action prediction. Default acceptable ordinary-task degradation is at most five percentage points on the frozen development capability set; also report the raw tradeoff, including failed doses. Choose dose/layer before test evaluation.

**Advance:** distinguish a learned causal role from a label decoder through crossed goal/belief cases, then a second cached checkpoint if time permits. Cross-family transfer is an extension after within-model selectivity, not the initial prerequisite.

### M3 — target state versus the reader's own disposition

Reuse M0–M2 cases. Cross what the target observed with what the reader knows. Include false belief, a reader-only correction, and a target-only observation summarized through the allowed evidence protocol.

Compare a target-state intervention with a norm-matched reader-style/persona intervention and an ordinary instruction to adopt the target's perspective. The purpose is to distinguish accurate other-modeling from changing the reader's own default preferences or language. Freeze the action vocabulary so a tone change does not score as a goal change.

**Advance:** add a contrary private belief or a case where reader and target share the same belief. Check that a helpful method does not force disagreement where none exists. This branch can run with activation methods or with persistent executable models; absence of a working lens does not block it.

### M4 — disciplined context updating

Use controlled evidence cards, not a live web crawl. Compare raw facts, a free-form contextual summary, and the same summary accompanied by source-linked claims. Match available facts and record token/compute differences. Include true context, plausible but wrong context, a correction, duplicated sources, and an unknown date/tool constraint that becomes known.

Ask whether the account updates the affected choices while preserving unrelated ones; distinguish a changed hypothesis weight from adding a previously absent hypothesis. Score factual support and downstream prediction separately. This operationalizes the future context subagent without allowing uncited biography to become ground truth.

**Advance:** after the controlled test, apply the already working human adapter to at most 24 chronological targets from available writers. Treat this as an exposed descriptive bridge if those records have been used before. Keep the strongest mechanical/prior baseline and score only outcomes the source actually labels. No inference of private review duration, effort or lifelong values from absent logs.

### M5 — recurrent latent-state feasibility

Sources: [Coconut and its code](https://github.com/facebookresearch/coconut), [J-CoT preprint](https://arxiv.org/html/2607.21981v1). Do not claim these are installed capabilities. Coconut's training requirements and the unverified J-CoT code release make full reproduction unsuitable as an unconditional overnight obligation.

If M1/M2 supply a validated read/write path within the existing budget, build a small state-retention/reset control. Compare two or four latent update steps with equal-compute extra verbal/direct passes. Admit a scientific comparison only if the task capability checks pass; otherwise retain a transport and timing result. Do not count merely feeding an arbitrary hidden vector back into an untrained model as a faithful reproduction.

No new large model or full training curriculum tonight. A trainable tiny-model variant may be specified for the following week with measured resource needs.

### M6 — preauthorized extensions when work is faster than forecast

Take the next informative branch in order, without requiring a positive score:

1. New goal × belief combinations and delayed goal changes.
2. A genuinely withheld world/rendering family, preserving the same latent roles.
3. Evidence ablation, contradictory context and duplicated-source controls.
4. Longer histories with stale-state risk, compared with equal-budget raw-history retrieval.
5. A second already cached competent model; fit its own lens/alignment.
6. Independent seed clusters for the most decision-relevant complete comparison.

The first five change an explanatory uncertainty. The sixth tightens precision only after those uncertainties are addressed. Do not fill time by multiplying rows from the same tiny world. Stop if no scientifically distinct, valid, authorized branch remains and explain that fact; do not quietly call the campaign complete after the first batch.

## Throughput, resources and execution order

The user's repeated observation is that earlier plans finish roughly twice as fast as forecast. Treat that as a planning correction, not a scientific multiplier.

- One local GPU owner; all fit, forward/backward, generation, failed-attempt and recovery time counts. Hard campaign ceiling **18 cumulative GPU service hours**, further bounded by actual authorized Gear windows and the Sunday deadline. It is a ceiling, not a target or permission to occupy the machine continuously.
- CPU-side planning/scoring can overlap GPU service without contending with Ghost's worker. Use low priority and existing thread limits. No new global hardware-policy changes.
- First hour: reconcile state, freeze the first fixture, start M0's CPU comparison and a 32-request/activation timing pilot. In parallel with running work, implement M1/M2 in small increments. Do not wait for every branch to exist.
- By hour three, aim for a complete first comparison and a consumer that can render one raw case through scoring. If one adapter consumes more than two focused engineering hours without a usable result, record it and move on. Model fitting itself is charged experiment time, not a hidden setup exemption.
- Initial allocation of the available GPU budget: roughly 3 hours M0, 3 M1, 3 M2, 2 M3/M4 and 1 M5; retain up to 6 hours for meaningful extensions/recovery. Scale these down together if fewer hours are actually available. Unused M5 time transfers to M0–M4.
- Maintain a persisted queue with estimated p50/p90 runtime, prerequisites and terminal dispositions. Forecast both observed speed and a **twice-as-fast scenario**. Keep enough admitted distinct follow-on work to cover that faster scenario, within the same ceiling. Update after each complete block; do not schedule by an invented constant seconds-per-call across generation and backpropagation.
- Native bounded supervision may dispatch the next admitted item when a worker exits. Follow existing watcher rules; no periodic LLM wakeups. Resume retains the original deadline and consumed budget.
- Begin synthesis 90–120 minutes before the checkpoint. Small complete blocks can finish during reporting. Do not stop mid-pair to improve a result; report incomplete cells as incomplete.

## Scoring and evidence contract

Use raw action probabilities/logits and saved responses as appropriate. Recompute semantic outcomes from those records; a hash-only replay is insufficient. Keep invalid outputs, timeouts and instrument failures in denominators where the target is end-to-end task performance. Conditional-on-valid scores are secondary and labeled.

For each branch record: claim, strongest rival, independent unit, information tier, predeclared split, selected hyperparameters, actual compute, effect with clustered uncertainty, capability tradeoff, and one counterexample. Multiple seeds/renderings are nested within the underlying maker/world. No large row count substitutes for broad support.

Keep public observations and evaluator truth separate. For activation caches record the exact input, model revision, layer, token positions, dtype and transform hash. A change to the input sequence invalidates position-based cache reuse. Fit costs and reusable-cache amortization are reported separately; all methods get equivalent declared reuse rights.

Any saved illustrative maker state must state its status: observed fact, inferred hypothesis, deliberately supplied oracle, or unknown. Do not show a calibrated percentage without a defined outcome and calibration evidence. Expert selection without editing may carry judgment; the present records do not measure decisions per second or convert expertise into a validated contribution scalar.

## Required packet and stopping point

Deliver a concise `REPORT.md`, branch ledger, machine-readable comparisons, integrity/semantic-replay receipt, and at least six inspectable cases selected by a frozen rule: a useful reconstruction if present, a wrong but plausible reconstruction, a selective intervention if present, a nonselective intervention, a context correction and an unresolved case. Label outcome-selected additions separately.

The report must answer:

1. Which actual mechanism was implemented, rather than named?
2. What did persistence or intervention add beyond the strongest direct rival?
3. Did the represented variable behave selectively under a controlled change?
4. Which failure was scientific, which was instrument-limited, and what did one repair resolve?
5. What should receive the next week's effort, with measured setup and run cost?

Update the normal findings/status/exchange records after actual results. Do not rewrite curator quotations or promote every scout into theory. A positive overnight demonstration opens confirmation; it is not confirmation. No UI, bulk source crawl, new cloud campaign or full latent-model training is required to complete this handoff.
