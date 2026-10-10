# Errata: Sounding Line research program of 10 October 2026

**For the coding agent and the planning thread, before dispatch.** Analyst review dated 2026-10-10.

- This file amends `SOUNDING_LINE_RESEARCH_PROGRAM_2026-10-10.md`; it does not replace it.
- Nothing here launches work, changes a gear or authorizes spending.
- Items marked **OWNER DECISION** wait for the curator.
- A companion file covers Ghost Scale: `GHOST_SCALE_PROGRAM_ERRATA_2026-10-10.md`.

**Pins verified 2026-10-10.**
- Live `main` is `428b3d944bd94deef325c170061be4ab86b23a38`, the program's pin.
- The ToMpathy review's pin `b1396ac` differs from it only in `docs/TOOLS.md` and `docs/README.md`.
- Ghost `main` is `e347de02aa098b6fb9a905868924cec1b481d5d7`.

**Checked for this file:**
- the program;
- the current inventory in `docs/TOOLS.md`;
- the Stage 11.1, 11.2, 12 and 13 reports and receipts named below, including the Stage 13 health snapshots;
- `runners/stage11_1/targets.py`, the Stage 12 evidence-view code and `soundingline/probe/client.py`;
- every reuse-map path in program section 14 (all exist; `runners/stage9/train.py` does call `torch.set_num_threads(6)`);
- the theory text changed since 20 September, and the 2 October level-set note in the project.

Literature was checked against primary pages where linked. Not checked: raw local archives, the workstation, and the Ollama server version.

**Priority:**
- **A:** change before dispatch.
- **B:** change during the first implementation day.
- **C:** correction to the record.

---

## SL-1 (A). The stronger-reader comparison the program already prefers is justified now

**Program text.**
- Section 3's "Capable local readers" row lists only Ollama packages of 9B or less.
- Section 12 names "one stronger-reader matched comparison" as a preferred cloud use. It also says "Prepare a cloud proposal only after a local pilot identifies a bottleneck that changes a scientific decision," and marks the branch `BLOCKED_AUTHORIZATION` until approval.
- R04, J01 and P05 compare against a "strong reader" without defining it.

**Finding.**
- **The record already identifies the bottleneck. No new local pilot is needed to justify the proposal.**
  - *Matched-history cell, Gear 3 Round 1* (24 targets, 13 writers, one dependency component; [report](https://github.com/EmotiveAutomaton/sounding-line/blob/428b3d944bd94deef325c170061be4ab86b23a38/results/gear3/G3-S10-READER-1/REPORT.md)):
    - 27B direct reading with the writer's own session history scored 0.3108 half-Brier.
    - The matched training-frequency control scored 0.3810.
    - 9B direct with the same history scored 0.4199.
    - In the records reviewed, this is the only model configuration that beat the cheap control on human records.
  - *Main human comparison* (64 opportunities, 14 writers, one component): the frequency baseline (0.3209) beat every model arm, 27B direct included (0.3880).
    - So the evidence that size matters is one descriptive component.
    - The size question is open. That argues for a clean test early, not for six days of results that hold only for the 9B reader.
  - *Stage 12 witnessed paths:* "All model/question aggregates lose to uniform" for the local Qwen reader ([S12-LOCAL-1 row](https://github.com/EmotiveAutomaton/sounding-line/blob/428b3d944bd94deef325c170061be4ab86b23a38/docs/theory/THE_TRIPLE_INFERENCE.md), L424 and L426).
- **Stage 12 already tried to replicate the 27B result and failed on transport, not science.**
  - The approved $20 cloud comparison ran Modal/Qwen3.5 27B on the human-history roster (`docs/design/STAGE12_ADDENDUM_PROPOSAL.md`, option E).
  - It returned 87 of 159 main calls; 1 was unknown and 71 never started.
  - The client HTTP timeout was 41.4 s against a 56.4 s per-call allowance ([receipt](https://github.com/EmotiveAutomaton/sounding-line/blob/428b3d944bd94deef325c170061be4ab86b23a38/results/phase_2_4_stage_12/ADDENDUM_CLOUD_TIMEOUT_INSPECTION.json)). The main reservation was $6.66.
  - The program does not mention this comparison.
- **The 2 October level-set note recommends the same test with a frontier reader.** Run a frontier direct reader on the frozen Gear 3 human tasks. If it closes the gap and reconstruction still subtracts, retire reconstruction-for-accuracy.
- **A frontier client is already configured.** `soundingline/probe/client.py` sets `API_MODEL = "claude-opus-5"`; account access was not verified (TOOLS.md).
- **List prices**, per million input/output tokens ([official page](https://platform.claude.com/docs/en/about-claude/pricing), read 2026-10-10):
  - Opus 5.5: $4/$20.
  - Opus 5, the configured string: $5/$25.
  - Sonnet 5.5: $2/$10.
  - Haiku 5.5: $0.10/$0.50 for prompts up to 100k tokens.
  - The Batch API halves all of these.
- **Workload cost.** The whole Gear 3 Round 1 workload was 1.94M input and 0.20M output tokens. With 30% tokenizer headroom it prices at roughly:
  - $8 on Opus 5.5 batch ($10 on Opus 5 batch);
  - $4 on Sonnet 5.5 batch;
  - under $1 on Haiku 5.5 batch.
  - Any vendor's frontier model serves; the existing client is simply the lowest-friction path.

**Change.**
1. **Add card G3-A** (OWNER DECISION, about $15 ceiling; above $10 it needs the detailed final approval that AGENTS.md requires). Re-run the frozen Stage 12 human-history main under a new identity:
   - same 27B package, roster, prompts, schema, parser and seed;
   - fix only the transport timeout;
   - reuse the 87 retained calls only if their bindings allow; otherwise run the whole main.
2. **Add card G3-B** (OWNER DECISION). Run a matched API reader ladder (small, medium, frontier) on the same frozen roster and on the Gear 3 Round 1 human tasks:
   - full raw logging through the existing ledger;
   - the contamination controls of SL-7.
3. **Define the reader label in R04, J01, P05 and X04.**
   - Call the best admitted local package "local reader," never "strong reader."
   - A P05 or J01 result obtained only with a local reader of 9B or less is conditional on that reader. It does not test the program's question.

---

## SL-2 (A). The human-data split rule discards most of CoAuthor; split by estimand

**Program text.**
- Section 4: "Split linked evaluation components containing author, project, session, prompt, revision lineage, duplicated passage and transformation."
- Section 4: "If the component graph collapses into one unit, the comparison remains descriptive."
- The P trunk starts at "12 eligible makers × 16 later decisions."

**Finding.** CoAuthor writers and prompts are a crossed design: each writer wrote on several prompts, and each prompt was used by many writers.
- **Requiring writer and prompt disjointness together discards almost everything** (Stage 12 [census](https://github.com/EmotiveAutomaton/sounding-line/blob/428b3d944bd94deef325c170061be4ab86b23a38/results/phase_2_4_stage_12/CENSUS_REPAIR_INSPECTION.json) and `PRIMARY_SETUP_INSPECTION.json`):
  - The prepared source holds 61 writers, 1,444 usable sessions, 20 prompts and 16,959 source-defined suggestion opportunities.
  - 1,390 sessions were excluded for "writer/prompt mismatch or source/pilot-dependent component," and 1,112 under the crossed allocation.
  - The census reports 0 unexposed confirmatory components; Stage 13 reports one connected component per partition.
- **The rule makes the personalization question permanently descriptive** on the only human corpus with recorded alternatives.
- **The P trunk's most valuable fact is about 278 recorded choices per writer** (16,959 / 61, a mean that will be skewed). The start of "12 eligible makers × 16 later decisions" uses about 1% of them.
- **Psycholinguistics settled this design problem.** Subjects × items is a crossed random-effects design ([Clark 1973](https://doi.org/10.1016/S0022-5371(73)80014-3); [Baayen, Davidson & Bates 2008](https://doi.org/10.1016/j.jml.2007.12.005); [Judd, Westfall & Kenny 2012](https://doi.org/10.1037/a0028347)).
- **Prompt-disjointness is needed only for claims that generalize to new prompts.**

**Change.**
1. **Writer-level estimands** (new-maker transfer, known-maker future prediction, P01 to P09, H07): split by writer or by time within writer.
   - Treat the 20 prompts as fixed stimuli. State the estimand as "over writers, conditional on these prompts."
   - Within a writer, test sessions must use prompts that writer has not used in training. This is local prompt novelty, not global disjointness.
2. **Primary inference:** paired per-writer contrasts with a writer-level bootstrap or sign-flip. Keep the dependence created when evaluation makers donate to one another, as section 4 already requires.
3. **Sensitivity:** a two-way (writer, prompt) cluster estimate ([Cameron, Gelbach & Miller 2011](https://doi.org/10.1198/jbes.2010.07136)) or the pigeonhole bootstrap ([Owen 2007](https://doi.org/10.1214/07-AOAS122)).
4. **Keep the double-disjoint split only for "new prompt" claims.**
5. **Build the exposure ledger at event level as well as writer level.**
   - An opportunity never scored by any model since Stage 9 is unexposed for a known-writer prediction claim.
   - Report separately whether its writer's other events were used to select methods.
6. **Replace the P trunk's "12 eligible makers × 16 later decisions"** with all eligible writers and chronological splits. Report the eligible-writer distribution before fitting.

---

## SL-3 (A). The 0.01 Brier margin cannot produce PARITY on human data

**Program text.**
- Section 4: "Default proposed practical margin for historical probability loss is 0.01 absolute Brier units after fixing its normalization."
- Section 10 maps a "Valid but imprecise result" to "One frozen precision expansion on new units if it can change a decision; otherwise defer."

**Finding.**
- **The normalization is still open.** 0.01 full multiclass Brier equals 0.005 half-Brier. Sounding Line has mostly reported half-Brier; Ghost V20 reports full Brier.
- **Measured spread is large.** Writer-level paired standard deviations from landed cells:
  - 0.230 and 0.224 for account minus direct operation loss (14 writers, 2 to 3 episodes each; `results/phase_2_4_stage_11_1/S1_ACCOUNT_INITIAL.json`);
  - 0.036 to 0.092 for review minus direct (`S1_REVIEW_INITIAL.json`, `S1_REVIEW_EXTENSION.json`).
- **A ±0.01 interval needs about 2,000 writers:** n ≈ (1.96 × 0.23 / 0.01)² ≈ 2,000. CoAuthor has 61.
- **Many events per writer (SL-2) shrink this but do not eliminate it.** The following is a planning approximation, not a measurement:
  - Assume per-event SD ≈ 0.36, implied by 0.23 at 2.5 events, and between-writer SD 0.03 to 0.05.
  - Then 80 events per writer give a writer-mean SD of 0.05 to 0.065.
  - 40 to 60 writers then give a minimal detectable effect (80% power) of roughly 0.02 to 0.03 half-Brier.
- **No CoAuthor contrast can take the "new units" branch.** There are no unexposed CoAuthor components (SL-2), so that branch will defer every time. The manifest should say so before the result, not after.

**Change.**
1. Freeze the Brier normalization and state the margin in it.
2. Before each human manifest, compute from landed cells for that contrast:
   - the minimal detectable effect;
   - the expected interval half-width.
3. Declare PARITY unattainable for a contrast whose expected half-width exceeds the margin.
4. Where no untouched units exist, record `UNRESOLVED, NO FRESH UNITS` as the expected disposition at manifest time.

---

## SL-4 (A). The failed admission field is deterministic by construction; stop eliciting it

**Program text.**
- R01 compares response formats.
- R03 teaches "the relation contract" with an adapter, including `none`, `unknown` and `unrelated`.

**Finding.** In [`runners/stage11_1/targets.py`](https://github.com/EmotiveAutomaton/sounding-line/blob/428b3d944bd94deef325c170061be4ab86b23a38/runners/stage11_1/targets.py):
- `relation` is a deterministic function of slot presence (line 129: `relation=relation if present else 'none'`).
- The surrounding slot uses `'unrelated' if inserted else 'none'` (line 122).
- Actor and related slot are fixed per slot.
- The Stage 13 control that refused admission is exactly this field: a dismiss case returned `unrelated` for absent slots.
- The interface requests 123 numeric judgments plus spans (count from the 10 October ToMpathy review). Most of them follow from about a dozen free quantities.

**Change.**
1. Make the R01 compact contract elicit only the free quantities:
   - handling;
   - per-slot presence;
   - change operation (delete, format edit or content edit);
   - surrounding operation (format or content);
   - spans.
2. Compute relation, actor, related slot and span state with the existing target constructor.
3. Treat this as a new prospective interface identity. The Stage 13 refusal stays recorded, and nothing is relabeled.
4. Narrow R03 to any relation that remains genuinely inferential after this change. If none remains, close R03 as unnecessary rather than training an adapter to reproduce a lookup table.

---

## SL-5 (A). The new evidence-view names collide with reused Stage 12 code

**Program text.** Section 4 defines E0 as context only, E1 as artifact plus context, E2 as earlier works, then E3 to E5.

**Finding.** Stage 12 code, which section 3 tells agents to reuse, gives the same names different meanings:
- E0 = artifact only, E1 = added context, E2 = witnessed process (`E2-full`, `E2-sparse`), O = oracle.
- The names appear in:
  - `runners/stage12/casebook.py`;
  - `local_operator.py` (`TIERS = ('E0','E1','E2-full')`);
  - `studies.py` and `program_sources.py`;
  - `provider.py`, whose packets default to `tier='E0'`.
- A new-scheme "E0" (no artifact) would be indistinguishable from an old artifact-only E0 in casebooks and provider exports.

**Change.**
- Rename the new ladder (for example V0 to V5), or put an explicit old-to-new map in every reused consumer.
- Never emit E0, E1 or E2 with the new meanings.

---

## SL-6 (A). Local readouts: what Ollama can and cannot provide

**Program text.**
- R02 compares "sequence likelihood, order-balanced first-token choice, generated probability objects".
- P03 and P05 use an "adapted-minus-base likelihood signal" and late fusion.

**Finding.**
- **Ollama's limits.** Ollama added logprobs for generated tokens in 0.12.11 ([release note via package tracker](https://forum.cloudron.io/topic/14470/ollama-package-updates); [client code requiring 0.12 or later](https://ollama-classifier.readthedocs.io/en/latest/_modules/ollama_classifier/backends/ollama.html)). It does not return logprobs for prompt (echo) tokens.
- **What that blocks.** The sequence likelihood of arbitrary candidate text from `qwen3.5:9b` is therefore not directly available.
- **Local alternatives are small.** The HF cache tops out at 3B, and `bitsandbytes` is absent (TOOLS.md). TOOLS.md lists the Ollama tags but not the server version.
- **The option-ID readout is the right first logit readout.**
  - LLM-as-Jev reports that a training-free 4B model scoring numbered options reached 81.4% on JevBench with ECE 0.057 ([Li & Wagle 2026](https://arxiv.org/html/2610.02076v2)).
  - The method lists options as "[1]..[K]", prefills "Best answer: [", and reads the "k]" suffixes.
  - No code release is stated.
- **First-token readouts can be less coherent than verbalized ones** ([Beyond Calibration](https://arxiv.org/html/2609.33209v1); MIT code; ChaosNLI items CC BY-NC).
  - A Qwen 27B first-token readout violated negation complementarity by 0.293, against 0.122 when verbalized.
  - It rejected both a statement and its negation in 196 of 480 pairs.

**Change.**
1. Record the Ollama server version.
2. For Ollama readers, implement R02's logit arm as the option-ID readout: raw-mode prompting plus `top_logprobs`.
3. Run sequence likelihood only on HF models of 3B or less, or on a cloud vLLM with prompt logprobs (Gear 3).
4. Add the negation and partition coherence checks to every R02 readout before ranking them.
5. P03/P05 fusion with a 9B reader must use one of these feasible readouts or the elicited probability vector, named as such.

---

## SL-7 (A/B). Freshness covers project exposure, not pretraining contamination

**Program text.** Section 4 defines freshness against the project's own exposure ledger.

**Finding.** Most H, C and D sources are public text that capable readers may have trained on:
- arXiv versions (arXivEdits, CASIMIR, EarlySciRev);
- OpenReview (ARIES);
- public Git;
- CoAuthor (2022);
- ScholaWrite;
- PRISM.

A reader asked to reconstruct an earlier version from a final artifact can partly retrieve it from memory. API readers (SL-1) raise the same issue.

**Change.**
1. Record each reader's release date as a conservative cutoff.
2. Stratify every historical-reconstruction claim into pre-cutoff and post-cutoff sources.
3. For any blind-reconstruction claim on Git or Wikipedia (SL-8), sample commits and edits made after the latest reader cutoff.
4. For readers that run under HF transformers, run a Min-K% Prob membership probe on final artifacts ([Shi et al., ICLR 2024](https://arxiv.org/abs/2310.16789); [code](https://github.com/swj0419/detect-pretrain-code)). Report the result as a contamination indicator, not a proof.
5. For Ollama and API readers, use date stratification alone.

---

## SL-8 (B). The largest public production record is missing: Wikipedia revisions, and the method built on them

**Program text.** The H trunk and the section 7 data plan list CoAuthor, ARIES, ScholaWrite, IteraTeR, arXivEdits, Git, NIRVANA, EarlySciRev, CASIMIR, PRISM and Humanly. Neither Wikipedia revision histories nor PEER appears.

**Finding.**
- **PEER-Undo is the closest existing artifact-to-history model** ([PEER, Schick et al. 2022](https://arxiv.org/abs/2208.11663)).
  - It "is trained to guess and undo the latest edit," predicting the edit plan and the previous version from an edited text.
  - PEER was trained on about five million Wikipedia edits, using edit comments as noisy plans, and used to synthesize edit histories for domains that lack them.
  - The paper states: "we release a variety of PEER models as well as the data and code used to train them." Whether they can be obtained today was not checked.
- **Labelled edit purposes exist.** Wikipedia edit intentions have an annotated taxonomy ([Yang et al., EMNLP 2017](https://aclanthology.org/D17-1213/)), and Wikimedia maintains an edit-type diff library ([mwedittypes](https://meta.wikimedia.org/wiki/Research:Wikipedia_Edit_Types/Python_package)).
- **What Wikipedia supplies:**
  - thousands of makers with long, timestamped, attributed histories;
  - stated plans (edit summaries) separate from actions;
  - reverts as rejection signals;
  - a continuous supply of edits made after any reader's cutoff.
- **It addresses two binding constraints at once.**
  - It supplies independent makers for known-maker future prediction.
  - It carries out the curator's instruction to use recorded histories as targets that improve inference.
- **It matches the product scenario.** A personal blog hosted on GitHub supplies both author text (for P03) and commit history (for H03). That is exactly the ToMpathy case.

**Change.**
1. **Add a Wikipedia substrate card** (OWNER DECISION on source policy). Use official dumps or the API, keep text local, and follow the fetch boundary.
   - Target: an editor's next edit type, and whether a later edit is reverted.
   - Units: editors.
   - Fresh units: edits made after the reader cutoff.
   - Edit summaries are typed as declared intention, never as the private goal.
2. **Add a PEER-Undo-style reverse-edit rival to H02.** Use a released model if one can be obtained; otherwise train a small model locally on Wikipedia before/after pairs.
3. **Add a "blog with Git" substrate to H03 and P03.**
   - Select GitHub-hosted personal blogs by criteria declared before any outcome is read: post count, commit count and a post-cutoff window.
   - Respect each repository's rights and keep text local.

---

## SL-9 (B). The personal-model block needs a clean text definition, its closest precedent and a fusion guard

**Program text.**
- P03 fits "next-token adapters to strictly earlier, deduplicated maker text"; the initial ceiling is "96 true-maker fits".
- P05 includes "calibrated late fusion" of the reader with the learned personal scores.

**Finding.**
- **CoAuthor's text is not all the writer's.** Session text interleaves human-typed spans with accepted GPT-3 insertions.
  - A per-writer adapter trained on full session text learns GPT-3 prose plus the writer's acceptance history, which is P04's target.
  - That turns P03 into a disguised choice model.
- **The writer's own text is probably small.** Per-writer human-typed text has not been counted; it is likely a few thousand tokens.
- **The direct precedent for the curator's idea** (a tiny tuned model shifting a large model) is proxy-tuning ([Liu et al. 2024](https://arxiv.org/abs/2401.08565)).
  - Token-level fusion requires a shared tokenizer.
  - Sequence-level likelihood-ratio fusion avoids that requirement, but needs candidate likelihoods from the large reader (SL-6).
- **The textbook rival for repeated personal choices** is the mixed (random-coefficient) logit ([Train 2009, free text](https://eml.berkeley.edu/books/choice2.html)). P04's partial pooling approximates it.
- **Late fusion can count the same history twice.** In P05 the personal scores and the reader both condition on the same history.
  - Ghost's only confirmed V20 win came from a product of factors that counted one fact twice (Ghost errata GS-1).

**Change.**
1. Define three training corpora per writer and report them separately:
   - human-typed spans only, from the replay;
   - full final text;
   - accepted-suggestion text alone.
2. Count tokens per writer before admitting P03. If the human-typed corpus is under roughly 10k tokens, label P03 a sparse-data stress test.
3. Add a mixed-logit choice model, with suggestion features and writer random coefficients, to P04 as the principal cheap rival.
4. Fit any fusion weight on separate units (stacking); never use a unit-weight product of likelihoods. Report the fused forecast's sharpness beside its loss.

---

## SL-10 (B). ARIES has 42 gold papers, and some are spent

**Program text.** The H trunk's "Initial targets" include "64 reviewer/edit links"; H05 uses ARIES for confirmation-grade claims.

**Finding** ([ARIES, D'Arcy et al.](https://arxiv.org/html/2306.12587v2)):
- **The gold set is small.** It holds 42 papers, 196 comments and 131 aligned edits. Only 85 comments map to textual edits.
- **The silver set is synthetic.** It holds 1,678 papers and 3,892 comments, aligned automatically.
- **Some gold papers are already exposed.** Stage 13 used 8 training-tagged and 8 reserve-tagged papers, and Stage 12's ARIES breadth used more.

**Change.**
- The H05 unit is the paper.
- State the remaining unexposed gold papers before design.
- Treat silver as training data and as a separately labelled evaluation.
- If fewer than about 20 gold papers remain, H05 is descriptive this week.

---

## SL-11 (B). GPU headroom: the Stage 11.2 slowdown was never diagnosed, and idle VRAM is often too small

**Finding.**
- **Stage 11.2 slowed sharply.** Median generation time rose from 2.96 s at repaired admission to 77.7 s over the final thirty retained worker calls. The report says "A shared-machine slowdown is observed; a single cause is not established" ([report](https://github.com/EmotiveAutomaton/sounding-line/blob/428b3d944bd94deef325c170061be4ab86b23a38/results/phase_2_4_stage_11_2/REPORT.md)).
- **Memory was held by something else.**
  - At the Gear 2 health check, 11,684 of 12,282 MiB were in use.
  - After the worker exited, 5,922 MiB remained in use with no project GPU lock (`WORKER_TIMEOUT.json`).
- **Idle VRAM varies widely and is often too small.** Twelve Stage 13 health snapshots recorded no science owner (1 to 2 October). Free VRAM in them ranged from 2,374 to 8,161 MiB of 12,282.
- **The model barely fits even the best case.** `qwen3.5:9b` Q4_K_M stores 6.59 GB of weights before KV cache and compute buffers.
- **No diagnosis is recorded.** Nothing in `docs/` or `results/` diagnoses system-memory fallback or VRAM.
- **The likely mechanism is documented** ([NVIDIA](https://nvidia.custhelp.com/app/answers/detail/a_id/5490)).
  - From driver 536.40, near VRAM exhaustion, allocations move to system memory and keep running "at lower speeds."
  - Driver 546.01 adds a per-application "Prefer No Sysmem Fallback" setting.
- **A second documented slowdown mechanism:** changing `num_ctx` between clients forces a full model reload ([report](https://dev.to/pat9000/pin-your-context-window-or-pay-the-reload-tax-3nfo)).

**Change.**
1. Gate each GPU block on measured free VRAM sized to model plus KV cache.
2. Set "Prefer No Sysmem Fallback" for the Ollama runner and the project interpreter, so that oversubscription fails fast instead of crawling.
3. Log tokens per second per call (`eval_count` / `eval_duration`), and park GPU lanes that fall below a floor.
4. Unload Ollama models (`keep_alive: 0`) before any PyTorch LoRA fit; never share the card between the two.
5. Pin one `num_ctx` for every client of the server.
6. Before sizing GPU blocks, tabulate `load_duration`, `prompt_eval_duration` and `eval_duration` from the 943 retained Stage 11.2 calls. This is offline work with no GPU.
7. Identify the non-project VRAM tenant before Sunday's GPU pilots.

---

## SL-12 (C). Smaller corrections

- **The GDM figures disagree internally.**
  - Section 16 quotes a fall "from 77.6% to 64.2%". That is the prose figure; the paper's Table 3 gives 66.1%.
  - Median and tail latency also differ between prose and table: P50 156.1 versus 160.6 s, P95 1,009.5 versus 816.0 s ([Duan et al.](https://arxiv.org/html/2610.03935)).
  - Report the range. Jev is TypeSafe AI's hosted model; InnerJev is the open replication.
- **Intern-Decision cannot run at 4B locally.**
  - The 4B is fine-tuned from Qwen3.5-4B and tagged at about 5B parameters ([card](https://huggingface.co/internlm/Intern-Decision-4B)).
  - In BF16 it will not fit beside the observed idle VRAM use (SL-11), so only 0.8B and 2B are local candidates.
  - It needs Python 3.12 or later and a transformers build with the `qwen3_5` architecture.
  - Limits: HF backend only; 8,192-token inputs; 1 to 16 questions and at most 62 options per question.
- **The theory's "load-bearing prediction" has no card.**
  - THREE_COGNITIVE_LAYERS section 3 calls the missing-middle fingerprint the "load-bearing prediction" and notes it "has never been run." In that fingerprint, drive ambiguity produces a specific goal-inference failure while surface affect and expertise reads stay intact.
  - The 2 October level set recommends it.
  - One reserve card on logged model-makers, varying drive constraints independently of surface affect, would cost little.
- **Correction to the analyst's 21 September objections report.**
  - O4 allowed that "up to 44 CoAuthor writers" might be unexposed. D1 proposed a replication "using unexposed CoAuthor writers."
  - The Stage 12 census found 61 writers in usable sessions and 0 unexposed confirmatory components.
  - D1's replication must therefore run on exposed writers. It should be scored as known-writer future prediction on events no model has scored (SL-2).

---

## Decisions for the curator

These need an answer before the cards they gate are dispatched. The coding agent can apply everything else above.

1. **Capable-reader spend (SL-1).** Example answers:
   - "Approve G3-A only, $15 ceiling."
   - "Approve G3-A and an API ladder on the frozen rosters, $30 total."
   - "No paid readers this week; label every result conditional on the local reader."
2. **Human split estimand (SL-2).** Example answers:
   - "Writers only; prompts are fixed stimuli this week."
   - "Keep double-disjoint splits and accept descriptive human results."
3. **New public sources (SL-8).** Example answers:
   - "Wikipedia via dumps or API, and Git blogs, local only."
   - "Wikipedia only."
   - "No new sources this week."
