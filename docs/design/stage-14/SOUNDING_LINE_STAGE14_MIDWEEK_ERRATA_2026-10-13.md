# Midweek errata: Sounding Line Stage 14 (program of 10 October 2026)

**For the coding agent.** Analyst review dated 2026-10-13. This amends the 10 October program and its errata (`SOUNDING_LINE_PROGRAM_ERRATA_2026-10-10.md`); it replaces neither. Nothing here launches work, changes a gear or authorizes spending. Items marked **OWNER DECISION** wait for the curator.

**Basis and limits.** Read for this file:
- the 10 October errata;
- the Gear 3 Round 1 report and branch;
- `runners/stage9/coauthor.py`, `runners/stage10/human_history.py`, `runners/stage12/prepare.py` and `runners/stage12/cloud.py`;
- FINDINGS L192;
- the A02, A07 and B01 to B03 rows of `THREE_COGNITIVE_LAYERS.md`.

Not read:
- **The program text.** The uploaded file is not retrievable from the 10 October thread. I know it only through the errata's quotations.
- **Live Stage 14 state.** `main` is still `428b3d9`, and nothing from Stage 14 has been pushed.

The curator reports the run is "writing the rank 16 continuation." My reading is that the Block B per-writer adapters (P03, LoRA rank 16) are in a continuation. Every item below is conditional on what has already run. Skip any item whose premise is false, and record why.

**Priority:**
- **A:** apply before the next P-trunk block.
- **B:** apply if a lane frees this week; otherwise carry to Stage 15.
- **C:** a record correction.

---

## SM-1 (A). Freeze and share the P-trunk held-out targets

**Why.** Gear 3 Round 2 (`GEAR3_ROUND2_MAKER_HISTORY_SPEC_2026-10-13.md`, OWNER DECISION) scores capable readers on known-writer future prediction in CoAuthor. Its results and the P trunk's personal models are only comparable on the same targets.

**Change.**
1. If the P trunk has a known-writer held-out target list, freeze it now, before any further P-trunk outcome on it is opened. Write it to the Stage 14 results folder as JSON with its SHA-256, and record which targets any model has already scored.
2. If no list exists, adopt the Gear 3 Round 2 roster rule (its section 4): 60/40 chronological windows, local prompt novelty, up to 8 targets per writer, chosen by hash.
3. Do not open any outcome on these targets to select methods.

## SM-2 (A). Score every P-trunk result against the writer's own base rates, in information units

**Why.** Errata SL-9 made the mixed logit the principal cheap rival. The bar the theory needs is narrower: does a personal model know anything about this writer beyond that writer's own class frequencies? Gear 3 Round 2 makes this its hardest test (Q6).

**Change.** For every P-trunk method, report per writer and as the writer mean with a writer-level bootstrap:
1. Half-Brier against B-pop (population frequencies), B-writer (the writer's history frequencies, Dirichlet-smoothed toward B-pop with α = 4) and B-mixlogit.
2. Information about this writer in nats per decision, $I = \overline{\ell}(\text{B-pop}) - \overline{\ell}(\text{method})$, using log loss. This is predictive V-information ([Xu et al. 2020](https://arxiv.org/abs/2002.10689)).
3. The same quantity against B-writer, $\overline{\ell}(\text{B-writer}) - \overline{\ell}(\text{method})$. A personal model that cannot beat this has learned base rates and nothing else.

## SM-3 (A). Add effort features, and an effort-weighted history arm, at no cost

**Why.** The curator's 13 October definitions locate preference strength in costly departures from habit: effort a maker pays to do it their own way. CoAuthor records that effort, and no stage has used it.

**Definitions.** Compute these from the replay for history-window decisions only. Never compute them for a target, because effort after the menu reveals the decision.
- `chars_typed_after`: UTF-16 units inserted with `eventSource == "user"` between the menu's resolution (select, close, or the open itself for ignore) and the next `suggestion-open` in the session, or session end. Cap at 2,000.
- `decide_seconds`: resolution minus open, from `eventTimestamp`. For ignore, use the time to the next user insertion. Verify the field exists in `private/prepared/coauthor-v2` first; if it does not, use characters alone and record that.

**Change.**
1. Add both fields, aggregated per writer, as features to P04's choice model (and B-mixlogit).
   - For each class, compute the writer's mean `chars_typed_after` and median `decide_seconds` over history-window decisions.
2. Add arm **P04-E**: history decisions weighted by $w = 1 + \log(1 + \text{chars\_typed\_after}/50)$ when fitting the writer's random effects.
3. **Null:** the same weights shuffled within writer. This preserves the weight distribution and breaks the link to decisions.
4. **Promising** if P04-E beats both P04 and the shuffled null by at least the contrast's precomputed detectable effect (errata SL-3).

## SM-4 (B). Rank-16 adapters: check the data, label the corpus, add a prototype-initialized arm

**Why.**
- Errata SL-9 predicted that each writer's human-typed text is a few thousand tokens. A rank-16 adapter trained from the base on that much text overfits easily.
- In chess, individual models fine-tuned from the population model needed about 5,000 games, and lost to the base model at 1,000 ([McIlroy-Young et al. 2022](https://arxiv.org/abs/2008.10086)).
- Initializing each player from prototypes (similar players or skill levels) before refining cut that to about 20 games ([Maia4All, Tang et al. 2025](https://arxiv.org/abs/2507.21488)).
- This is the curator's "initialize from the similar, adjust at the differences" (`READER_HEURISTICS.md` §1), with the nearest prototype in place of the self.

**Change.**
1. Before admitting results from the running continuation, record per writer the token counts of the three SL-9 corpora: human-typed spans, full final text, accepted-suggestion text. If the adapter trains on full session text, label every result "mixed human and GPT-3 text."
2. Add arm **P03-PROTO** at equal optimizer steps:
   - Cluster writers on history-window decision rates and mean human-typed text embedding (k = 4, fit on history windows only).
   - Fit one pooled rank-16 adapter per cluster.
   - Initialize each writer's adapter from their cluster's adapter, then refine on the writer's own history-window text.
3. Compare P03 (from base) against P03-PROTO on the SM-1 targets, scored as in SM-2.
4. **Null:** initialization from a randomly assigned cluster.

## SM-5 (B). Re-run the self-reading test in the form the theory now predicts

**What L192 tested.** Readers predicted a target's next choice from that target's 8 recorded choices.
- **Targets:** the reader itself under an imposed policy prompt, another model family, and a program.
- **Accuracy with records:** 0.42 for the self target and 0.52 for the other family, against a two-draw consistency ceiling of 0.68 and chance at 0.25.
- **Self minus other:** −0.10, p = 0.55.
- **Without records:** the reader's prior about itself (0.32) was worse than its prior about the other family (0.48).

**Why re-run.**
- The self target ran under an imposed policy, so "same model" shared weights but not preferences.
- The curator's 13 October restatement predicts exactly L192's split: similarity helps infer process (shared expertise), and records help infer preferences.
- L192's own conclusion says similarity helps artifact reading, not choice forecasting.

**Change.** Re-run the E03 record task (`results/phase_2_4_stage_3/E/E03/`) with two target types, crossed with reader similarity (self, sibling, other family):
1. **Natural-policy targets:** each model's unprompted choices.
2. **Imposed-policy targets:** as in L192.

Score two separate targets:
- **process prediction:** which operation or route the target uses;
- **preference prediction:** which option the target picks when routes are fixed.

**Prediction:** similarity improves process prediction and not preference prediction; records improve preference prediction. Local and cheap; carry to Stage 15 if no lane frees.

## SM-6 (B). Steering inversion: fit the maker's direction instead of supplying it

**Why.** Your record already has half of the curator's "midbrain" idea:
- **The maker's true direction helps.** Steering a reader along the maker's true tendency direction lifted its held-out read of that maker by about half a nat on two artifact domains. A random direction of the same norm did nothing, the wrong direction was inert or costly, and the dose effect was monotone (A07-S3, B02-S5 and B03-S5; L255).
- **The reader's own affect does not.** Steering it did not improve prediction of the maker (A02-S4).
- **The second family showed no lift** (B01-S5).

The open step is finding the direction for an unknown maker.

**Change.** On the constructed makers with planted tendencies (the A07 worlds):
1. **Steering inversion.** Fit per-maker coefficients over the existing tendency directions: maximize the steered reader's likelihood of that maker's earlier artifacts. Then read the maker's held-out artifacts with the fitted steer.
2. **Rivals:**
   - no steer;
   - a random basis with the same number of coefficients;
   - a rank-1 LoRA fit to the same earlier artifacts;
   - the true direction, as an oracle ceiling.
3. **Known-answer gate first:** recovered coefficients must correlate with planted tendencies before any held-out read is scored.
4. **Promising** if the fitted steer reaches at least half the oracle's lift and beats the random basis. This is local; carry to Stage 15 if no lane frees.

## SM-7 (C). Vocabulary in new reports

The curator's 13 October usage, from a draft lexicon in the project (`claude/LEXICON_DRAFT_2026-10-13.md`, not yet adopted into theory):
- "preference" for choice-revealed quantities;
- "set point" for a state a maker works to keep or return to;
- "value" only for higher-level heuristics.

Use these terms in new report prose. Do not edit theory files; structural theory changes need the curator's direction (`docs/theory/AGENTS.md`).

---

## Decisions for the curator

1. **Gear 3 Round 2 (OWNER DECISION).** Example answers:
   - "Approve G3-S14-MAKER-1 as specified, $50 ceiling."
   - "Approve the Modal lane only."
   - "No paid readers this week."
2. **Optional local cards this week (OWNER DECISION).** Example answers:
   - "SM-5 and SM-6 this week if lanes free."
   - "Carry both to Stage 15."
