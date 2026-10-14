# Gear 3 Round 2: is the maker in the writer's own history?

**Campaign:** `G3-S14-MAKER-1`
**Prepared:** 2026-10-13, analyst thread, for the Sounding Line coding agent.
**Status:** implementation handoff. Nothing here launches work. Dispatch requires the curator's per-use approval through `runners/gear3.py`. The planned total exceeds $10, so it also requires his detailed final approval; section 15 is that request, ready for his words.

**Pins.**
- Sounding Line `main` at `428b3d944bd94deef325c170061be4ab86b23a38`.
- The Gear 3 Round 1 apparatus lives on branch `codex/gear3-round1` at `f1083efdd3688c20854f8af941a7c80a3508705a`. It is not on `main`.
- Stage 14 state was not visible to the analyst; section 4 says how to share its frozen targets.

**Supersedes** cards G3-A and G3-B in `SOUNDING_LINE_PROGRAM_ERRATA_2026-10-10.md` (SL-1), if they were not run. If either was run, keep its results and run only the arms here that it lacks.

---

## 1. Why this run, from the data

- **One real-text configuration has ever beaten the cheap baseline.** In Gear 3 Round 1, the 27B reader given the writer's own earlier decisions scored 0.3108 half-Brier against 0.3810 for the matched training-frequency control. The writer's own history also beat another writer's history by 0.0858. That was 24 targets from 13 writers, one dependency component, descriptive ([report](https://github.com/EmotiveAutomaton/sounding-line/blob/428b3d944bd94deef325c170061be4ab86b23a38/results/gear3/G3-S10-READER-1/REPORT.md)).
- **The replication attempt died on transport, not science.** Stage 12's cloud run used a client HTTP timeout of 41.4 s against a 56.4 s per-call allowance. Of 159 main calls, 87 returned, 1 is unknown and 71 never started (`results/phase_2_4_stage_12/ADDENDUM_CLOUD_TIMEOUT_INSPECTION.json`).
- **Stage 12 already designed this comparison and parked it.** Leaf A1 (`runners/stage12/prepare.py`) lists arms `own_history`, `no_history`, `training_donor`, `training_prior` and `persistence`, waiting on "admitted capable reader and new specific funding."
- **Round 1's history was the wrong history for the theory.** It was the same session's earlier decisions. That measures persistence. The theory claims familiarity: earlier sessions by the same maker (Round 1 critique 2.8 and mechanism 12, `claude/GEAR3_ROUND1_CRITIQUE_2026-09-13.md`). This run tests both.
- **No frontier reader has ever read a human record in this program** (errata SL-1).
- **Two arms answer this week's theory.** Effort annotations test whether costly departures carry preference strength. Written maker profiles test whether the history compresses into the representation ToMpathy would display.
- **The constructed world currently says no.** Ghost V21 found that a shared-maker model loses to the strongest matched rival by 0.42 to 1.00 nats across three label budgets, despite measured headroom (`docs/versions/v21-supporting-mechanisms/WIDE_NATIVE_SUPPORT_REPORT.md`). Replacing the history's maker-specific content with unrelated content did not remove the history benefit (`LEARNED_PERSISTENCE_REPORT.md`). This run is the real-text test of the same question. A null here closes the maker-history route on CoAuthor; a positive means human makers carry something the constructed makers do not.

## 2. Questions and predictions

Each prediction names its refutation. "Beats" means lower writer-mean half-Brier, with the 95% writer-level bootstrap interval of the paired difference excluding zero.

| # | Question | Prediction | Refuted if |
|---|---|---|---|
| Q1 | Does the Round 1 result replicate at scale? | 27B with same-session history (H1) beats the population baseline | interval includes zero or favors the baseline |
| Q2 | Is there a maker across sessions? | 27B and Opus with cross-session own history (H2) beat the population baseline | interval includes zero or favors the baseline |
| Q3 | Is it that maker? | H2 beats matched other-writer history (H3) for 27B and Opus | H2 minus H3 interval includes zero |
| Q4 | Does the history compress? | A 250-word profile (M1) keeps at least 70% of H2's information, and beats another writer's profile (M0) | retained share under 50%, or M1 minus M0 includes zero |
| Q5 | Does effort carry strength? | Effort-annotated history (H2e) beats plain H2 | H2e minus H2 includes zero |
| Q6 | Does any reader beat the writer's own base rates? | At least one reader-arm beats the writer-frequency baseline | no reader-arm does |

Q6 is the hardest bar and the one that matters most. If readers lose to the writer's own frequencies, the history's information is habit, and readers add nothing beyond counting.

## 3. Source

- **Corpus:** the prepared CoAuthor source used since Stage 9 (`private/prepared/coauthor-v2`, built by `runners/stage9/coauthor.py`). Stage 12's census counts 61 writers, 1,444 usable sessions, 20 prompts and 16,959 source-defined suggestion opportunities.
- **Decision classes:** `accept`, `edit`, `dismiss` and `ignore`, as `DECISIONS` in `runners/stage9/coauthor.py` defines them. Class text for prompts is in Appendix A.
- **Session order:** within each writer, by each session's first `eventTimestamp`. Verify the field exists in the prepared source before freezing. If it does not, use the raw log's timestamps and record the source.

## 4. Roster (freeze before any outcome is opened)

**Windows.** For each writer, order sessions chronologically. With n sessions:
- the history window is the first ⌊0.6·n⌋ sessions;
- the target window is the remaining sessions whose prompt does not appear in the history window (local prompt novelty, errata SL-2).

**Eligible writer:**
- n ≥ 3;
- at least 8 labelled decisions in the history window;
- at least one target-window session with 5 or more decisions.

If fewer than 40 writers are eligible, relax the prompt rule to "prompt absent from the writer's last three history sessions." Record the relaxation in `PLAN.json` before scoring.

**Targets.** Up to 8 per eligible writer:
- drawn from target-window opportunities with at least 4 earlier decisions in the same session (so H1 exists);
- chosen by ascending SHA-256 of `writer_id|opportunity_id|20261013`, which is blind to outcome.

The maximum roster is 61 × 8 = 488 targets.

**Exposure.** Record, per target, whether any model has scored that opportunity since Stage 9 (event-level ledger, errata SL-2). Prefer unexposed events when a writer has more eligible events than 8; never select on outcomes.

**Stage 14 sharing.** If Stage 14's P trunk has a frozen known-writer target list for the same estimand:
- adopt the intersection of that list with this eligibility rule, in the P trunk's order;
- record the source list's hash;
- the P trunk's personal models can then be scored on exactly these targets.

If P-trunk outcomes on those targets are already open, use the rule above on events not yet scored.

**Pilot exclusion.** Pilot targets (section 10) are drawn first, from 3 writers chosen by the same hash rule. They are excluded from the main roster.

## 5. Evidence arms

Every request carries the common block (Appendix A):
- the writing prompt;
- the last 1,200 characters of draft before the cursor;
- the displayed menu.

Arms add one evidence block:

| Arm | Evidence block | Header shown to the reader |
|---|---|---|
| H0 | none | none |
| H1 | up to 16 earlier decisions from the same session, most recent first | "Earlier decisions by this writer in this session" |
| H2 | 16 decisions from the writer's history window: most recent sessions first, at most 4 per session, at least 2 prompts | "Decisions by this writer in earlier sessions" |
| H3 | the donor's history-window decisions, length-matched to H2 | same header as H2 |
| H2e | H2 plus effort fields per decision | H2 header plus the effort legend |
| M1 | the writer's frozen profile (section 6) | "Profile of this writer, written from their earlier sessions" |
| M0 | the donor's frozen profile | same header as M1 |

**Decision rendering.** One line per decision:

`[k] prompt: {prompt_code} | draft end: "…{last 200 chars}" | menu: (1) {s1} (2) {s2} … | decision: {class}`

- For accept and edit, add `| inserted: "{first 200 chars}"`.
- For H2e, add `| typed after: {chars_typed_after} chars | decided in: {decide_seconds} s`.

**Effort fields** come from history-window events only; never compute or show them for a target:
- `chars_typed_after`: UTF-16 units inserted with `eventSource == "user"` between this menu's resolution and the next `suggestion-open` in the session (or session end), capped at 2,000. Resolution is select, close, or, for ignore, the open itself.
- `decide_seconds`: resolution minus open, from `eventTimestamp`, one decimal. For ignore, use the time to the next user insertion.

**Effort legend** (H2e only): "Effort fields show how much the writer typed after the menu and how long they took to decide. Larger values mean the writer spent more to do it their own way."

**Donor pairing.** Order eligible writers by SHA-256 of `writer_id|donor|20261013`; each writer's donor is the next writer in that cyclic order. Select the donor's history-window decisions with the same rules as H2, then adjust the count so the rendered block's characters are within ±15% of the writer's H2 block. Record the ratio if that is impossible. The same donor serves H3 and M0. The reader is never told the history belongs to someone else.

## 6. Maker profiles (built once, before any target is scored)

- **Writer:** `claude-sonnet-5-5` through the Message Batches API, temperature 0, `max_tokens` 500.
- **Input:** the writer's history-window decisions, up to 60 (most recent first, at most 6 per session), in the H2e rendering. No target-window material.
- **Prompt:** Appendix B. The output is plain text of at most 250 words. Over-length outputs are truncated at the last full sentence within 250 words and flagged.
- **Freeze:** profiles are hashed into `PLAN.json` before the main roster's first request.
- **Confound to report:** Sonnet writes the profiles and is also a reader. Report M1 for Haiku separately; Haiku did not write them.

## 7. Readers

| Reader | Package | Arms | Settings |
|---|---|---|---|
| R27 | `qwen3.5` 27B Q4_K_M on Ollama, Modal L40S, the Round 1 package and image | H0, H1, H2, H3 | `think=False`, temperature 0, seed 1001, output cap 2,048 tokens, context bound by tokenizer count (not the 15,104-byte rule), 16k context |
| RO | `claude-opus-5-5`, Message Batches API | H0, H2, H3 | temperature 0, `max_tokens` 400 |
| RS | `claude-sonnet-5-5`, Message Batches API | H0, H2, H3, H2e, M1, M0 | same |
| RH | `claude-haiku-5-5`, Message Batches API | H0, H2, H3, H2e, M1, M0 | same |
| R9 (optional, free) | local `qwen3.5:9b`, Gear 2 | H0, H1, H2, H3 | only when the card is idle; not a gate and not in the budget |

**R27 transport repairs** (Stage 12 failure and Round 1 critique):
- The client HTTP timeout must be at least max(240 s, 3 × the pilot's p99 call time) and strictly greater than the per-call allowance.
- Concurrency 2 (`OLLAMA_NUM_PARALLEL=2`) only after the pilot shows identical parse validity at 1 and 2.
- Order model loads so the 27B loads once per invocation.
- Pin `modal==1.5.4`.

**API lane.** Use a new module, for example `runners/gear3_api.py`:
- **Tool-free:** keep the probe client's posture (`soundingline/probe/client.py`: `EGRESS_ALLOWLIST`, `_assert_no_tools`).
- **Reserve before spending:** reserve integer cents in the same campaign ledger before each batch submission, against the same ceiling as the Modal lane.
- **Archive and replay:** keep complete raw request and response archives, and support replay with inference forbidden.
- **Record:** model strings, batch IDs and returned usage tokens.
- **Launch-day checks:** verify account access and current prices. If access fails, close the API lane with its evidence; the Modal lane continues.

## 8. Output contract and baselines

**Reader output:** JSON only:

```json
{"probabilities": {"accept": 0.0, "edit": 0.0, "dismiss": 0.0, "ignore": 0.0}, "choice": "accept"}
```

- Each probability must lie in [0.01, 0.97], and they must sum to 1 within 0.01.
- `choice` must be one of the four classes.
- A reply that violates the contract is invalid. It receives system half-Brier 1 and is excluded from log-loss means, with counts reported. There is no repair or clipping after the fact.
- Reuse the Round 1 parser where it fits (`runners/stage10/gear3_consumer.py` on the branch).

**CPU baselines** are free and fit on history windows only:

| Baseline | Definition |
|---|---|
| B-pop | class frequencies over all eligible writers' history windows |
| B-writer | the writer's history-window frequencies, Dirichlet-smoothed toward B-pop with α = 4 |
| B-last | 0.55 on the writer's most recent history-window decision, plus 0.45 × B-writer |
| B-mixlogit | multinomial logit with writer random intercepts (errata SL-9). Features: menu size, mean suggestion length, maximum word overlap between suggestion and draft, decision index in session, previous decision. Reuse Stage 14's P04 model if it exists; otherwise partial pooling fit by empirical Bayes |

## 9. Scoring and analysis

**Primary metric:** half multiclass Brier, $\tfrac12\sum_k (p_k - y_k)^2$, as system loss with invalid replies at 1.

**Secondary metrics:**
- Log loss in nats; the contract's 0.01 floor keeps it finite.
- Accuracy of `choice`.
- Expected calibration error with 10 bins.
- **Information about this writer**, in nats per decision. With predictive family V fixed per method:

$$I_V(\text{method}) = \overline{\ell}(\text{B-pop}) - \overline{\ell}(\text{method}),$$

  where $\overline{\ell}$ is mean log loss over the writer's targets. This is predictive V-information ([Xu et al. 2020](https://arxiv.org/abs/2002.10689)), the measure Value Profiles uses ([Sorensen et al.](https://arxiv.org/abs/2503.15484)). Positive means the method knows something about this writer beyond the population.

**Unit and inference:**
- The unit is the writer: each writer contributes the mean over its targets.
- Every contrast is paired within writer.
- Intervals: writer-level bootstrap with 10,000 resamples, plus a sign-flip randomization p-value.
- Sensitivity: two-way (writer, prompt) cluster estimate (errata SL-2).
- Prompts are fixed stimuli; the estimand is "over writers, conditional on these prompts."

**Primary contrasts** use Holm correction across five:
- C1: R27·H1 vs B-pop.
- C2: R27·H2 vs B-pop.
- C3: R27·H2 vs R27·H3.
- C4: RO·H2 vs B-pop.
- C5: RO·H2 vs RO·H3.

**Secondary contrasts** are reported in full, uncorrected and labelled descriptive:
- H2e vs H2 (RS, RH);
- M1 vs M0 (RS, RH);
- the retained share $I_V(\text{M1})/I_V(\text{H2})$ (RS, RH);
- H1 vs H2 for R27 (persistence against familiarity);
- every reader-arm vs B-writer, B-last and B-mixlogit;
- the ladder trend in H2 minus H3 from RH to RS to RO.

**Detectable effect.** This is a planning approximation from errata SL-3, not a measurement:
- Assumptions: per-event paired SD 0.36, between-writer SD 0.04.
- At 8 targets per writer: writer-mean SD 0.133.
- With 55 writers: standard error 0.018, and the minimal detectable effect at 80% power is about 0.050 half-Brier.
- That detects effects the size of Round 1's (0.070 and 0.086). It is underpowered for effects half that size.
- Recompute from the pilot and write the number into `PLAN.json` before the main run.

## 10. Pilot (node P, discarded)

- **Size:** 3 writers × 4 targets, all arms, all readers, plus those 3 writers' profiles.
- **Validity gate:** 12 of 12 contract-valid replies per reader-arm cell. Otherwise one scoped repair, then stop that reader.
- **Timing gate (R27):** measure p50, p95 and p99 seconds per call at concurrency 1 and 2, and model-load time.
- **Token gate (API):** measure input and output tokens per arm from the returned usage.
- **Replay gate:** a complete archive replay with inference forbidden passes.
- **Sizing:** compute the main reservations from measured rates. If the main projection exceeds its envelope, shrink the roster by dropping whole writers in hash order, never by outcome.
- Pilot outcomes are opened only for validity, never for effect direction.

## 11. Budget

Prices come from the official page as read on 2026-10-10 (errata SL-1); recheck on launch day. Per million input/output tokens: Opus 5.5 $4/$20, Sonnet 5.5 $2/$10, Haiku 5.5 $0.10/$0.50; the Batch API halves these.

**Token assumptions.** Input tokens per call:

| Arm | Input tokens per call |
|---|---|
| H0 | 900 |
| H1, H2, H3 | 4,100 each |
| H2e | 4,500 |
| M1, M0 | 1,250 each |

Output is 120 tokens per call. Profiles: 13,200 input and 350 output tokens per writer. R27 runs at 5.5 s per call effective at concurrency 2, plus 0.5 h of load and startup, at the retained $2.301264/h.

| Node | Work at 488 targets | Estimate | Envelope |
|---|---|---:|---:|
| P | Pilot, all readers | $2.55 | $3.50 |
| M-27 | 1,952 R27 calls, about 3.5 h | $8.01, or $11.22 with the 1.4 safety factor | $14.00 |
| M-API | RO 1,464 calls ($10.64), RS 2,928 ($9.61), RH 2,928 ($0.48), 61 profiles ($0.91) | $21.64, or $28.14 with 30% tokenizer headroom | $28.50 |
| Reserve | interrupted work, verified repair, storage, billing uncertainty | | $4.00 |
| **Total** | | **about $42** | **$50.00** |

- The reserve does not become extra science.
- If the pilot shows a main node would exceed its envelope, shrink the roster by the section 10 rule.
- Booked cents must be reconciled to measured duration at COMPLETE and FAILED (Round 1 critique §3).

## 12. Decision rules (fixed now)

- **C2 or C4 holds, and the matching C3 or C5 holds:** the writer's own cross-session history carries a maker. Stage 15 builds the maker-model engine on cross-session history, and ToMpathy's reading uses it.
- **C1 holds but C2 and C4 fail:** Round 1 measured same-session persistence. The familiarity claim stays unsupported on CoAuthor; record that in the HH-23 and G48 rows.
- **No reader-arm beats B-writer (Q6):** the information in history is the writer's base rates. Route effort to explicit preference models (costly-departure features and set-point estimates), not readers.
- **M1 keeps at least 70% of H2's information, and M1 beats M0:** maker profiles become the candidate ToMpathy representation for the bottom box.
- **H2e beats H2 by at least the recomputed detectable effect:** effort carries preference strength. Add the effort features to the P trunk.

## 13. Implementation map

1. **Gear 3 guard:** route every Modal invocation through `runners/gear3.py` with `--approval` (the curator's words and date) and `--cap-approval` (section 15).
2. **Port from `codex/gear3-round1`:**
   - `runners/gear3_campaign.py`, `gear3_plan.py`, `gear3_round1.py`, `gear3_runtime.py` and `gear3_sequence.py`;
   - `runners/stage10/gear3_batch.py`, `gear3_bundle.py`, `gear3_comparison.py`, `gear3_consumer.py`, `gear3_freeze.py` and `gear3_inputs.py`;
   - `docs/GEAR3_MODAL_WORKSPACE_GUIDE.md` and `requirements-gear3-controller.txt`.
3. **Apply the Round 1 critique repairs:** token-count context bound, booked-cent reconciliation, per-request journal keys for concurrency, model-load ordering and the pinned Modal SDK.
4. **Reuse Stage 12's cloud guard:** `reservation_guard`, `verify_return` and `restore` in `runners/stage12/cloud.py`, with the timeout repaired.
5. **Roster and histories:**
   - build from `runners/stage9/coauthor.py` replay records and `runners/stage10/human_history.py` donor logic, adapted to cross-session windows;
   - freeze with the conventions of the Stage 12 S12-03 card (`runners/stage12/prepare.py`);
   - close Stage 12 leaf A1 by reference to this campaign.
6. **Baselines:** `runners/stage10/human_baselines.py` and the Stage 13 CPU rivals (L461), plus B-mixlogit.
7. **Bundles never ship evaluator labels.** Profiles see history windows only.
8. **Offline tests before any paid call:**
   - renderer fixtures for every arm;
   - no target effort or label in any bundle;
   - donor length matching;
   - contract-validator refusals (out-of-range, wrong sum, extra keys, truncation);
   - full replay of a synthetic archive;
   - ledger arithmetic for both lanes.

## 14. Schedule, outputs and stop rules

**Schedule:**
- **Wednesday 14 October:** implement, run the offline tests, build profiles, pilot.
- **Thursday 15 October:** main R27 run; submit API batches.
- **Friday 16 October:** retrieval, replay, scoring, report.

If setup passes one working day, cut H1 for R27 first, then M0, and say so in the report.

**Outputs** go in `results/gear3/G3-S14-MAKER-1/`:
- `PLAN.json`: roster, donors, profile hashes, arms, detectable effect, decision rules;
- `APPROVAL.json`;
- `PILOT_INSPECTION.json`;
- raw archives;
- `RESULTS.json`;
- `REPORT.md`, in the Round 1 format: hypothesis, method, found, means, tables, worked examples, cost.

Also:
- add a FINDINGS entry;
- propose theory-row updates for HH-23, G48, G65 and Stage 12 leaf A1, without editing theory files (theory edits follow the curator's direction).

**Stop rules:**
- Account access fails: close that lane with its evidence.
- Pilot validity below 12 of 12 after one repair: stop that reader.
- A reader's invalid rate exceeds 5% in main: stop that reader and retain its records.
- Never re-run a block for a better result.
- No new provider, model, corpus or arm beyond those named here.

**Limits to state in the report:**
- CoAuthor is public (2022), so readers may have seen it. Decision logs are less likely to be memorized than texts; record each reader's release date.
- The suggestions came from GPT-3, so decisions partly judge GPT-3's output.
- 61 writers is the ceiling.
- This is one corpus.
- Sonnet both writes and reads the profiles.

## 15. Final approval request (for `runners/gear3.py --cap-approval`)

> **What will run.** Campaign G3-S14-MAKER-1. A discarded pilot (3 writers × 4 targets), then a main run on up to 488 CoAuthor targets from up to 61 writers.
> - qwen3.5 27B on one Modal L40S reads each target under four evidence conditions: none, same-session history, own earlier sessions, another writer's earlier sessions.
> - Claude Opus 5.5 reads three conditions: none, own earlier sessions, another writer's.
> - Claude Sonnet 5.5 and Haiku 5.5 read six conditions: those three plus effort-annotated history, the writer's own profile, and another writer's profile.
> - Sonnet 5.5 also writes one 250-word profile per writer from that writer's earlier sessions.
> - Every reply is a four-way probability forecast, scored against free baselines by writer-paired comparisons.
>
> **How long.** About one working day of setup and pilot, about 3.5 hours of Modal time, API batches returning within 24 hours, and half a day of analysis. Results are expected Friday 16 October.
>
> **Tests.** The five primary contrasts and the secondary contrasts of section 9, under the decision rules of section 12.
>
> **Total.** Estimated about $42; ceiling $50, comprising pilot $3.50, Modal $14.00, API $28.50 and reserve $4.00. Shrinking happens by whole writers in hash order if measured rates exceed the envelopes.

---

## Appendix A. Reader prompt (all readers)

**System:** "You forecast how one specific human writer handled one menu of AI writing suggestions. You have no tools. Reply with JSON only, matching the schema."

**User:**

```
TASK
A writer was composing a response to the prompt below in a collaborative editor. At the
cursor, the editor showed a menu of AI-generated continuations. Forecast what this writer
did next with this menu.

CLASSES
accept  = selected a suggestion and left the inserted text unedited until the next menu
edit    = selected a suggestion, then edited inside the inserted text before the next menu
dismiss = closed the menu without selecting
ignore  = left the menu without selecting or dismissing, and kept writing

WRITING PROMPT
{prompt_text}

DRAFT BEFORE CURSOR (last 1,200 characters)
{draft}

MENU
(1) {s1}
(2) {s2}
...

{evidence block for the arm, or nothing for H0}

Reply with JSON: {"probabilities": {"accept": p, "edit": p, "dismiss": p, "ignore": p},
"choice": "<one class>"}. Each p between 0.01 and 0.97; the four sum to 1.
```

## Appendix B. Profile-writer prompt

**System:** "You describe a writer's standing preferences from records of their decisions. You have no tools."

**User:**

```
Below are decisions by one writer handling menus of AI-generated suggestions while writing,
with how much they typed afterward and how long they took to decide.

Write at most 250 words describing this writer's standing preferences: what they reliably
protect or pursue in their own writing, what they accept or refuse from the AI and under
what circumstances, and how strongly, judged from the effort they spent. Describe general
tendencies, not individual decisions. Approximate rates are allowed. Do not invent biography.

{up to 60 decisions in the H2e rendering}
```

## Appendix C. Sources

- Gear 3 Round 1 report and spec: `results/gear3/G3-S10-READER-1/REPORT.md`; `docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md` (branch).
- Analyst critique of Round 1: `claude/GEAR3_ROUND1_CRITIQUE_2026-09-13.md`.
- Errata SL-1, SL-2, SL-3, SL-7 and SL-9: `claude/SOUNDING_LINE_PROGRAM_ERRATA_2026-10-10.md`.
- Predictive V-information: [Xu et al. 2020](https://arxiv.org/abs/2002.10689). Value profiles: [Sorensen et al.](https://arxiv.org/abs/2503.15484).
- CoAuthor: [Lee, Liang & Yang 2022](https://arxiv.org/abs/2201.06796).
