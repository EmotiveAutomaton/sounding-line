# Sounding Line kickoff: every quick check, most interesting first, with staged Gear 3

16 October 2026, revision 2, after the curator's 14:17 answers. **For the Sounding Line agent, from the curator.** Handing this packet over is the curator's authorization for everything in it, within the limits of section 8. Nothing is left open: where a choice had to be made, it's made here, with the reason. Card numbers from revision 1 and from the fast-lane plan are kept; D21 onward and the shared passes P1 to P4 are new. Record the curator's handoff message verbatim, with its date and this packet's SHA-256: that's the authority section 8 and the Gear 3 route cite.

## 0. How to run this

1. **Start everything now.** Run the shared passes and the downloads in section 3 immediately. Take the cards in section 4 in rank order as their inputs land, as many in parallel as the machine allows. Sounding Line has priority over Ghost Scale on the machine.
2. **Rank is interest.** The order follows the curator's current theory questions, most interesting first. When resources conflict, the higher rank wins.
3. **Time box.** Give each card about three hours of agent effort.
   - **Definitions.** A card's result is:
     - **positive** when its primary effect's 95% interval excludes zero in the predicted direction;
     - **negative** when the interval excludes zero the other way;
     - **marginal** when the interval includes zero but the point estimate is in the predicted direction;
     - **null** otherwise.
   - **Marginal or positive at the time box:** extend once by three hours. This is the curator's rule: marginal results run in full.
   - **Negative, null or blocked at the time box:** record that, with the reason, and move on.
4. **Results land per card**, as described in section 2.
   - Keep going down the ranks through Tuesday until the curator stops or redirects the run, probably at his next research pass on Saturday morning.
   - Work in flight when he stops it finishes and is reconciled.
   - Plan for more work than fits.
5. **Gear 3.** The first $10 runs on handoff. The repository's stone rule needs one detailed final-approval request before spending past $10, and that request is the only thing this packet sends back to the curator (section 6).

## 1. State read (16 October, 14:30 PDT)

- **Sounding Line `c95dff4ad`.** Stage 14 is closed with no useful maker-specific advantage. Phase 0 descriptive results are recorded, and Stage 15 is open. No scientific worker or paid batch is active. Profile fitting is blocked by the failed Ghost profile witness.
- **Ghost Scale `d84e023a2` (14:19 PDT).**
  - The twins T1 to T4 are built, and they wait on measured shape summaries that only Sounding Line can supply (`docs/versions/v23-research-division/TWIN_INPUT_CONTRACT.md`). Card S0 delivers them.
  - Ghost's 90 CPU-hour total now binds. The Ghost kickoff raises it locally, so Ghost will use more of the machine, at lower priority than Sounding Line.
- **Gear 3.**
  - Stage 14's campaign `G3-S14-MAKER-1` has about $43.35 of headroom. Its approval is bound to its 13 October plan, and its API route refuses submissions after 15 October, 17:00 UTC. It isn't standing authority for this work.
  - This packet opens its own campaign, `G3-S15-DRIVE-1` (section 6).
  - `runners/stage14_midweek/api.py` is the tool-free Message Batches adapter to clone. It makes integer-cent reservations through the gear3 ledger (`budget.py`). Don't write a new spender.

## 2. Rules

**Lane.** Every result here is **DESCRIPTIVE**:
- freeze code and comparators per card before outcomes are read, and record the hash;
- report the whole specification curve, not a chosen cell;
- never promote a result or use it as an admission witness;
- confirmation, if wanted later, runs under the full gates on locked holdouts.

**Every card reports:**
- question, data, frozen code hash and comparators;
- the effect with a writer-resampled 95% interval;
- for scored forecasts, the reliability and resolution split (card V2);
- one line on what the result means for the theory question it names.

**Controls on every writer-specific claim:**
- a within-writer shuffled control (labels permuted within writer);
- a writer-shuffled control (writer identities permuted across sessions).

**Privacy and data:**
- Aggregates only in public files. No raw CoAuthor text leaves `private/` or `raw/`. No identification model is published.
- CoAuthor states no license. API and Modal transfer happen only as section 8 states.

**Where results land:**
- each card writes `results/phase_2_4_stage_15/DRIVE/<card>.md` and `.json` when it finishes;
- `DRIVE/INDEX.md` stays current: done, running, queued, blocked, with one line per result;
- the index is what the curator reads when he stops the run.

## 3. Shared passes and downloads (start immediately)

These are dependencies, not ranked by interest. Each is short.

### S0. Ghost twin references (aggregates only)

**Why.** Ghost's twins are built and wait on measured summaries that only Sounding Line can supply. It's about an hour of work, and it removes a cross-repository block.

**Contract** (`ghostscale/validation/soundingline/v23/twin_contract.py` at Ghost `d84e023a2`). For each twin, supply one JSON object with:
- `source`, with exactly the keys `revision` (a 40-character committed revision), `sha256` (64 hex characters, for the locally retained source file) and `citation`;
- `aggregates`, with exactly these keys:

| Twin | Data | Required keys |
|---|---|---|
| T1 writing | CoAuthor (prepared `coauthor-v2`) | `makers`, `sessions`, `decisions`, `records_per_maker`, `sessions_per_maker`, `options_per_decision`, `latency_quantiles_s`, `keystroke_quantiles`, `handling_marginals` |
| T4 ratings | DICES-350 only, as `nominal_yes_no_unsure`. Community Alignment's multi-response preferences fit neither of Ghost's rating semantics | `raters`, `items`, `ratings_per_rater`, `raters_per_item`, `rating_semantics`, `rating_marginals` |
| T3 revisions | Wikipedia full histories: card D8's five articles, plus a random sample of 100 articles | `editors`, `edits_per_editor`, `editors_per_article`, `summary_coverage`, `revert_fraction` |
| T2 games | One CC0 Lichess month with clock annotations, downloaded and parsed locally | `players`, `games_per_player`, `move_clock_quantiles_s`, `moves_per_game` |

**Formats Ghost's code checks.** Read the consumers at `d84e023a2` before writing.
- **Quantiles** are objects `{probabilities, values}`, with probabilities strictly increasing from 0 to 1. Ghost's sampler refuses anything else.
- **T1 lists and histograms:**
  - `records_per_maker` and `sessions_per_maker` have one entry per writer (61);
  - `options_per_decision` is a histogram in which every menu size is at least 2, with positive mass;
  - `handling_marginals` is exactly four positive values summing to 1.
- **T1 timing.** Define both exactly as Ghost's writing twin samples them (`twin_writing.py`), one value per decision record, from P2's timelines:
  - `latency_quantiles_s`: seconds from the menu opening to the writer's handling decision;
  - `keystroke_quantiles`: characters the writer typed between the previous decision record and this one.
- **Single-suggestion menus.** CoAuthor has them, and the contract can't represent them. Deliver the histogram over sizes 2 and up, which is what the contract accepts. Report the true histogram, including size 1, in a note to Ghost's owner.
- **T4:** `rating_semantics` is exactly `nominal_yes_no_unsure`, with three marginals.
- **T2: a Ghost bug.** `twin_chess.py` reads `move_clock_quantiles_s` as `{probabilities, seconds}`, while Ghost's own shape code emits `values`. Deliver both `values` and an identical `seconds` array; the contract doesn't refuse the extra key. Ghost's kickoff fixes the reader.

**Rules:**
- Compute from the development data Phase 0 used. If a sealed confirmation lineage exists for a source, exclude it and say so.
- **DICES:** `T4.json` covers all 123 released raters, and is the one Ghost uses. `T4_104.json` covers the 104 left after the paper's quality exclusions, as a frozen sensitivity reference.
- **Revert fraction:** count identity reverts by revision SHA-1. Separately count the `mw-reverted` tag, where the API returns it.
- **Summary coverage:** the share of edits with a non-empty, non-automatic summary.
- **Timing:** deliver T1 and T4 first. Deliver T3 and T2 when their downloads land.

**Output.** `results/phase_2_4_stage_15/TWIN_REFERENCES/{T1,T2,T3,T4,T4_104}.json`, plus a note to Ghost's owner thread with the paths and hashes.

### V2. Reliability and resolution (a tool every forecast card uses)

**Why.** The curator called the accept-proneness finding "a resolution issue". Forecast verification has a precise word for it. The Brier score splits into three parts:
- **reliability** (calibration error);
- **resolution** (how much the forecasts separate cases with different outcomes);
- **uncertainty** (the outcome's own variance).

**Method.** For each of the four handling classes, bin the forecast probability (deciles, plus the exact distinct values for population rates). With N decisions, bins b of size n_b, mean forecast f̄_b, observed frequency ō_b and overall frequency ō:
- reliability_k = Σ_b (n_b/N)(f̄_b - ō_b)²
- resolution_k = Σ_b (n_b/N)(ō_b - ō)²
- uncertainty_k = ō(1 - ō)
- Brier_k ≈ reliability_k - resolution_k + uncertainty_k. This is exact up to within-bin variance; report that residual.

Sum over the four classes and halve for half-Brier. The equivalent multi-category form:
- UNC = ½ Σ_j ō_j(1 - ō_j);
- RES = (1/2N) Σ_k n_k ‖ō_k - ō‖²;
- REL = (1/2N) Σ_k n_k ‖f̄_k - ō_k‖², with k grouping identical forecast vectors.

When vector bins get sparse, fall back to the per-class sum. Correct each class's reliability for small bins by subtracting (1/N) Σ_b n_b ō_b(1 - ō_b)/(n_b - 1).

**Apply to:** population rates, personal frequencies, the Phase 0 backbone, the calibrated 27B reader, and every forecast card here.

**Prediction.** The 27B reader lost on reliability before calibration (it projected a 43% edit rate against 22% observed) and on resolution after calibration. The backbone's gain is almost entirely resolution.

**Cost:** under an hour.

### P1. Reader scoring pass (GPU)

**Feeds:** D12, D13, D21, D23, D27 and D28.

**Readers.** Pin each by file hash:
- Qwen2.5-0.5B;
- SmolLM2-360M;
- the Pythia suite at 410M, 1B and 1.4B. Pythia is Apache-licensed and ungated. Its sizes share training data and order, so it gives a clean size ladder.

GPT-3's logged `probability` serves as an extra reader, for suggestions only.

**Contexts:**
- **c0:** the item alone;
- **c1:** the prompt only;
- **c2:** the prompt plus the preceding 100 tokens;
- **c3:** the prompt plus the whole preceding document;
- **c4,** for writer-typed sentences only: c3 plus the writer's earlier sessions on other prompts, truncated to a fixed 1,024-token budget.

**Items:**
- every offered suggestion: its mean per-token surprisal and its rank within the menu. Share the menu's context across its suggestions with a reused key-value cache.
- every writer-typed sentence: per-token surprisal.

**Outputs.** Surprisal arrays stay private. Per-item summaries go to the cards.

**Cost.** About 100 million tokens across readers and contexts: about 3 to 5 GPU-hours, overnight.

### P2. Timeline rebuild (CPU)

**Feeds:** D16, D17, D23, D24, D28 and D29.

Rebuild per-keystroke timelines by replaying the logged text deltas; the release stores document text only at initialization. Also extract session clocks, hover sequences per menu, and the origin of every span of the final text (typed, accepted and kept, accepted then edited).

**Cost:** under 1 CPU-hour.

### P3. Edit-intent pass

**Feeds:** D4 and D22.

1. **Calibrate first.** The agent labels a calibration set of 200 CoAuthor edit pairs, blind to the classifier's output, against written criteria, and declares the labels as agent-made. Style and coherence are the classifier's weakest labels (F1 0.13 and 0.32), and they carry the preference signal.
2. **Classify every edit pair:** accepted-then-edited suggestions, and writer-typed spans later edited. Use the released IteraTeR intent classifier, `wanyu/IteraTeR-ROBERTA-Intention-Classifier` on Hugging Face. Its classes are fluency, coherence, clarity, style and meaning-changed.

**Cost:** under 1 GPU-hour, plus the hand labels.

### P4. Frozen base model for G3-A's looks (CPU)

**Feeds:** G3-A's futility looks, and D1.

Fit the Phase 0 backbone plus D1's free local features, chronologically: the embeddings and their cosine, length and position, novelty, session state, and the effort term. Use no paid features. Freeze it and record its hash before G3-A's first look. G3-A's statistic is the gain of this model plus the Haiku features over this model alone. D1 later reports the same model in full.

**Cost:** under 1 CPU-hour.

### Downloads (network)

- **Wikipedia full histories** of "Empathy", "Theory of mind", "Affective neuroscience", "Jaak Panksepp" and "Aesthetics", plus a random sample of 100 articles. These feed S0's T3 reference and D8.
  - Send Wikimedia's `Api-User-Agent` header.
  - Make at most 3 concurrent requests, and obey `Retry-After`.
- **One Lichess month with clock annotations,** CC0. This feeds S0's T2 reference, D23b and G3-D. Take the smallest recent month whose games carry clocks, and parse it locally.

## 4. The cards, most interesting first

| Rank | Card | Question | Needs | Cost |
|---|---|---|---|---|
| 1 | D21 | Do readers converge as context grows? | P1 | GPU via P1; under 1 CPU-hour |
| 2 | D22 | Does editing protect higher-order goals? | P2, P3, D14 vectors | 1 to 2 CPU-hours |
| 3 | V1 | Can our pipelines find planted personal effects? | none for its Phase 0 and Stage 14 arms; its D16 arm waits on D16 | 4 to 6 CPU-hours |
| 4 | D27 | What does the page keep of its making? | P1, P2 | 1 to 2 CPU-hours |
| 5 | D6 | Attention against preference (a natural experiment) | P2 | 1 to 3 CPU-hours |
| 6 | D16 | Writer verification: what against how | P2, D17 features | 1 to 2 CPU-hours |
| 7 | D23 | Does play narrow error bars? | P1, P2 | under 1 CPU-hour |
| 8 | D14 | Controlled variables (set points) | none (G3-A adds features) | 2 to 3 CPU-hours |
| 9 | D12 | Departures from the model's own favorite | P1 | under 1 CPU-hour |
| 10 | D29 | Where writers stop: stopping points as set points | P2 | under 1 CPU-hour |
| 11 | D13 | Goldilocks, and "easier than expected" | P1 | under 1 CPU-hour |
| 12 | D24 | Does a solution follow its need? | P2 | under 1 CPU-hour |
| 13 | D20 | Influence without selection | none | under 1 CPU-hour |
| 14 | D28 | Going back and forth marks near-ties | P1, P2 | under 1 CPU-hour |
| 15 | D2 | Are menus near-ties? Do writers differ in taste at all? | none | under 1 CPU-hour |
| 16 | D18 | Sacrifice (exploratory) | none | 1 to 2 CPU-hours |
| 17 | D15 | Holding the common pieces constant | none | under 1 CPU-hour |
| 18 | V3 | How many records each personal feature needs | D15 | hours |
| 19 | D11 | Expertise in what gets accepted | none | under 1 CPU-hour |
| 20 | D1 | Content features for better overall prediction | none (G3-A adds features) | 1 to 3 CPU-hours |
| 21 | D4 | Corrections as preference records | P3 | 1 to 2 CPU-hours |
| 22 | D3 | Reversal timing: flow state or near-tie | none | under 1 CPU-hour |
| 23 | D17 | Pauses, bursts and interaction states | P2 | under 1 CPU-hour |
| 24 | D5 | The leapfrog inside a session | none | 1 to 2 CPU-hours |
| 25 | D8 | Stated purposes on Wikipedia | Wikipedia download | 2 to 4 hours |
| 26 | D7 | Dwell decomposed | none | under 1 CPU-hour |
| 27 | D9 | Pooling and stylometry on panels | D10 | 1 to 3 CPU-hours |
| 28 | D23b | Play in chess | Lichess download | about 2 CPU-hours |
| 29 | D24b | Devaluation on Wikipedia: editing after promotion | Wikipedia download | about a day |
| 30 | D19 | A dictionary of shared recipes | none | under 1 CPU-hour |
| 31 | D10 | Embeddings for panels, WildChat and DiffusionDB | GPU | under 1 GPU-hour |

### 1. D21. Do readers converge as context grows? (new)

**Theory.** The curator, today: readings differ between readers through noise and missing context, and "the goal is to fully align with context and thus have removed the difference". There's a classical theorem behind this. When two Bayesian readers' priors allow the same possibilities, their predictions of what comes next merge as shared evidence grows ([Blackwell & Dubins 1962](https://doi.org/10.1214/aoms/1177704456)). Where one reader rules out what the other allows, context isn't guaranteed to close the gap.

**Measures, per reader pair and context (from P1):**
- **menus:** Kendall's τ between readers' within-menu rankings, and agreement on the top suggestion;
- **typed text:** Spearman correlation of per-token surprisal, and Jaccard overlap of the readers' top-decile departure tokens (ToMpathy's deviation-map definition).

**Tests:**
1. **Convergence.** Disagreement falls from c0 to c3 (and to c4 for typed text). Use writer-clustered intervals.
2. **Floor.** Report where the curve flattens. That floor is the noise.
3. **Size.** Along the Pythia ladder, larger readers agree more with the other families. A position paper argues that representations in different models are converging as models grow ([Huh et al. 2024](https://arxiv.org/abs/2405.07987)); this tests it on predictions.
4. **Agreement predicts accuracy.** On menus where readers agree, their shared favorite predicts the writer's choice better than on menus where they disagree.
5. **What the residual means.** Disagreement left at c3 marks one of two things:
   - a **support gap**: one reader can't represent the move. It concentrates on rare tokens, names and dialogue.
   - a **real alternative**. It concentrates on prompts where writers themselves diverge, measured as the dispersion of choices across writers at matched points on the same prompt.

**Prediction.** Disagreement falls monotonically with context and flattens above zero. The residual sits more in support gaps than in real alternatives, since, in the curator's words, a truly alternative solution "is not really a thing that happens in physical space".

**Dissent to report alongside.** Larger models' surprisal fits human reading times worse ([Oh & Schuler 2023](https://aclanthology.org/2023.tacl-1.20/)). Readers converging with each other may move away from human readers. Report the size result with that caveat.

**Use.** ToMpathy's two-reader view shows this curve on any page.

### 2. D22. Does editing protect higher-order goals? (new)

**Theory.** The curator, on two makers:
- "The creator tried to make the whole decision."
- The model "tried to do all the decisions, fit it in where it went best they could."
- "The follow-up person looked and tried to make sure that all the higher order hierarchical goals were properly satisfied. That's what editing is."

Writing research says the same: reviewing evaluates the text against the writer's goals ([Flower & Hayes 1981](https://doi.org/10.58680/ccc198115885)).

**Data:**
- each accepted suggestion's fate: kept unedited, housekeeping edit, content edit, or deleted;
- writer-typed spans and their later edits;
- intents from P3;
- each suggestion's disturbance vector from D14.

**Tests:**
1. **Level shift.** Compare intents on edits to accepted model spans with edits to the writer's own typed spans of matched length and position. Edits to model spans should carry a higher share of higher-order intents (meaning-changed, coherence, style); edits to the writer's own spans should skew to fluency. Report both distributions and their difference, with writer-clustered intervals.
2. **Restoration.** Among accepted suggestions, the probability of a content edit rises with the suggestion's disturbance to variables the writer protects (D14 test 1), and the edit moves the variable back (D14 test 2).
3. **Missed subversions.** These are accepted, unedited suggestions with large disturbance to a variable the writer protects elsewhere. Report their rate per writer, and whether they concentrate in argumentative essays (stance). The check can fail: opinionated suggestions shifted the views writers expressed in a controlled study ([Jakesch et al. 2023](https://arxiv.org/abs/2302.00560)).
4. **A decision ledger per session,** aggregates only. It counts decisions by maker:
   - words drafted by the model and kept;
   - words typed by the writer;
   - the writer's accepts, dismissals and edits.

   This is the input ToMpathy's makers panel needs for logged sources.

**Prediction.**
- Tests 1 and 2 are positive.
- Test 3 is nonzero and concentrates on weakly protected variables. A goal held strongly is defended; a goal held weakly drifts.

**Cost:** 1 to 2 CPU-hours after P3 and D14. Add G3-A's tone and contradiction features when they land.

### 3. V1. Can our pipelines find planted personal effects?

**Why.** The curator: "Is our testing correct? I don't know." We don't know whether "the human is weakly identified" is a fact about writers or about our instruments.
- Astronomers answer the same question about planet searches by injecting fake planets into real light curves and counting how many come back.
- Epidemiologists use plasmode datasets: real covariates, with planted outcomes of known size.

**Method:**
1. **Base.** Take the Phase 0 population model's predicted handling probabilities for every decision, fitted chronologically as in Phase 0.
2. **Null world.** Redraw every outcome from those probabilities. This erases all real personal signal, so any personal effect found is a false positive.
3. **Planted worlds.** For a random half of writers, add a known effect to the accept log-odds before drawing:
   - **offset:** a constant δ (pure accept-proneness);
   - **content taste:** δ times a standardized content feature (similarity between the suggestion and the writer's own earlier text), with a random sign per writer;
   - **habit:** δ times the writer's own last-three-decision accept rate, centered.
4. **Grid:** δ in {0, 0.1, 0.2, 0.4, 0.8} log-odds, with 10 replicate worlds per cell.
5. **Run each pipeline unchanged:**
   - Phase 0's writer-backbone against the population comparison;
   - Stage 14's own-history against donor-history contrast, if its code runs without paid calls;
   - card D16's writer verification.

**Report:**
- **Recovery rate against δ,** per effect type and pipeline: the completeness curve.
  - Also plot recovery against x = (true injected gain) / (the pipeline's standard error), with a smooth fit, as the Kepler planet search did. Read off where detection reaches 50% and 90%.
  - Thresholds aren't detection rates. Kepler's pipeline at its nominal 7.1-sigma threshold recovered only 25.8% of the injected planets there ([Christiansen et al. 2015](https://arxiv.org/pdf/1507.05097)).
  - For a chosen δ, the true gain over the baseline forecast q₀ is the mean of (q₀ - p)², because E[(q - Y)²] = (q - p)² + p(1 - p).
- **The false-positive rate** at δ = 0.
- **The smallest δ recovered 80% of the time,** translated into an intraclass correlation of handling, to compare with V3's measured value.
- **Empirical interval calibration.** Use the planted effects to estimate each pipeline's systematic error, as drug-safety studies do with negative and positive controls. Widen the reported intervals accordingly.

**Meaning:**
- If moderate planted effects come back, the weak real signal is about writers.
- If they don't, our instruments are blind at the scale that matters, and every null so far needs that caveat.

**Cost:** about 120 runs at 2 to 3 CPU-minutes each, 4 to 6 CPU-hours.

### 4. D27. What does the page keep of its making? (new)

**Theory.** The essays' central claim is that an artifact is physical evidence of compressed decisions. Robotics has a formal version: infer what people want from the state of the world, because they've already acted on it ([Shah et al. 2019](https://arxiv.org/abs/1902.04198)). CoAuthor holds both the finished page and the full process, so it can measure what the page keeps.

**Method:**
- **Features from the final text only:**
  - MiniLM embedding;
  - function-word and character n-gram profiles;
  - the readers' surprisal profile on the final text (P1);
  - length and paragraphing.
- **Targets from the logs:**
  - the writer's identity (enrolled on other sessions);
  - the share of the final text that came from accepted suggestions;
  - accept rate and content-edit rate;
  - mean decision latency and request rate;
  - pause shares (P2);
  - handling profile.
- **Models.** Ridge or logistic. Leave writers out for process targets; leave sessions out for identity.
- **Baseline:** prompt identity alone.

**Report.** For each target, held-out R² or AUC from the page alone, against the same target predicted from the logs (the ceiling). The ratio is the share of each process fact the page keeps.

**Prediction.** The page keeps identity and composition well, keeps decision latency and pauses poorly, and barely keeps handling preferences. So a reading from a page alone should claim style and composition, not timing or taste.

**Privacy.** No composition model is published or applied outside CoAuthor; aggregates only.

**Use.** It sets what ToMpathy's page-only readings may claim.

### 5. D6. Attention against preference: a natural experiment already in the data

**Why this is the cleanest card.** The analyst's rerun on the public CoAuthor release found three things:
- **Display order is independent of the model's probability.** Across 9,084 five-item menus, the mean probability rank is 1.96 to 2.05 at every slot (2.0 expected). So position effects are causally identified.
- **Position matters.** Selections by slot run 23.5%, 21.3%, 18.9%, 18.4% and 17.9% (7,345 matched selections).
- **There's an examination signal.** There are 77,684 `suggestion-hover` events in 1,394 sessions, an event the paper's event table doesn't list. The research pass also counted 1,390 of 3,391 dismissals with no hover at all.

Confirm all three against the prepared source.

**Method:**
- Web search separates examination (did the user look at a result?) from attractiveness (did they like it?) with click models. A selection closes the menu, so fit a cascade model, or a position-weighted logit with a dismiss option: P(slot k) ∝ θ_k × exp(u(content)).
- Treat unhovered suggestions as unseen, with latent exposure, as recommender systems do. Unchosen and unseen is not disliked.
- Compare with a one-stage content model. Also compare with a two-stage consideration model, where consideration depends on context: typing speed, time since the request, session phase.
- **Check one confound first.** The released interface code auto-highlights the first suggestion unless the domain is "story". If the argumentative sessions ran that way, Enter selects item 1 by default. That could explain their steeper position gradient: 25.2% to 16.9%, against 22.7% to 18.4% for creative sessions, from the research pass.

**Prediction:**
- Examination falls with position.
- Some content effects in the one-stage model move into examination.
- Dismissals without a hover are mostly non-examination, not rejection.

**Cost:** 1 to 3 CPU-hours.

### 6. D16. Writer verification: what against how

**Theory.** Speaker verification works with seconds of speech by modeling how people speak, not what they say. It has three parts:
- a universal background model of everyone;
- a per-speaker model adapted from it with weight α = n/(n + r);
- a likelihood-ratio score against the background.

Chess shows the same split. Fine-tuning a move model per player adds about 4 percentage points of accuracy, yet 100 games identify a player among 400 with 98% accuracy ([McIlroy-Young et al. 2022](https://arxiv.org/abs/2008.10086)). If the person lives in the how, writers should be identifiable from process even though their handling rates barely differ.

**A planning identity.**
- The adaptation constant r is the ratio of within-person to between-person variance. With that r, α = n/(n + r) equals the Spearman-Brown reliability of a person's average over n records. So r is the number of records at which a person's own data and the population count equally.
- **Don't take r from Phase 0.** Its only variance split (T0a) is of the backbone's paired gain over the population, on 234 decisions from 31 writers: between-writer share 0.025, with an interval from 0 to 0.109. That isn't handling behavior. Its history bins also mix different writers, which the report itself says prevents reading them as a learning curve.
- Card V3 estimates r for handling and for each how feature. Use those values as priors for writer offsets.

**Feature families per session:**
- **Keystroke timing: the positive control.** Use intervals between inserted characters, latencies of frequent letter pairs, burst lengths and deletion runs.
  - In real essay writing, timing and writing-process features told same from different writers at a 4.7% equal error rate (an ETS study of 3,110 repeat test takers; [Hao & Fauss 2024](https://arxiv.org/abs/2411.13699)).
  - CoAuthor logs text inserts, not key presses and releases, so there are no hold times. Check the timestamp resolution first.
- **Process:** request rate, decision latency (from menu opening to decision), edit-after-accept sizes, and D17's pause shares.
- **Outcomes only:** handling rates.
- **Content taste:** the mean embedding of accepted suggestions minus the mean of those offered.

**Method:**
- Build per-session vectors. Reduce them with linear discriminant analysis. Score with a two-covariance PLDA model (probabilistic linear discriminant analysis), or with cosine after within-writer whitening.
- Train leaving writers out. Enroll held-out writers from k = 1, 3 or 5 sessions.
- **Target trials:** the same writer, with a different prompt and a different decoding setting.
- **Non-target trials:** different writers on the same prompt. This is the hard case, because it holds the stimulus constant. The CoAuthor paper describes 20 prompts, 4 GPT-3 decoding settings and 5 suggestions per request, and writers repeat prompts, so repeated prompts would otherwise inflate same-writer matches.
- Report the equal error rate (where false accepts equal false rejects) and rank-1 identification. Bootstrap over the 61 writers, not over trials.
- Report the leading eigenvectors of between-writer against within-writer variance: the features where writers differ most.

**Predictions:**
- keystroke timing: an equal error rate under 10%;
- process: between 15% and 35%;
- outcomes only: 40% to 50%, near chance.

**Pre-mortem.** If the how wins only through motor timing, the result is biometric, not cognitive. To count as cognitive, decision latency alone must identify writers above chance.

**Read first.** Two papers already analyze CoAuthor timing. Reuse their features and don't duplicate them:
- Davalos & Zhang (arXiv 2609.17883, September 2026), against each author's own baseline;
- Yang et al. (arXiv 2406.14885), which clustered sessions into four temporal patterns.

**Reconcile.** The CoAuthor paper reports 63 writers; the prepared source has 61. Record why.

**Meaning.** If process beats outcomes by a wide margin, the person is in the how. That's the reading ToMpathy should build, and the outcome-prediction nulls stop being the headline.

**Privacy:** aggregates only; no model published.

### 7. D23. Does play narrow error bars? (new)

**Theory.** The curator, today: play "solves the problem of having error bars that are too wide over unfamiliar situations", and "you use play in order to decrease the error bars around those solutions". Animal research agrees on two points:
- play trains responses to unexpected events, and animals create such events in play by handicapping themselves ([Špinka, Newberry & Bekoff 2001](https://doi.org/10.1086/393866));
- play starts when an animal is "adequately fed, healthy, and free from acute or chronic stress", while mild stress such as boredom can facilitate it ([Burghardt 2010](https://www.museumofplay.org/app/uploads/2022/01/2-3-article-comparative-reach-play-and-brain.pdf)).

In the active inference framework, this is the novelty term: information gain about the parameters of one's own model ([Schwartenbeck et al. 2019](https://doi.org/10.7554/eLife.41703)).

**Exploration measures,** per menu and per session:
- requests per 100 words;
- hovers per menu (breadth of examination);
- choosing below the model's favorite (D12);
- accepting high-surprisal suggestions (D13);
- accepting and then deleting (trying something and discarding it).

**Tests:**
1. **Familiarity.** Within writer, exploration is higher in a writer's first session on a prompt than in their repeats. Phase 0's own-prompt-novel split already marks 6,155 first-exposure decisions.
2. **Experience.** Exploration falls across a writer's sessions in time order, most steeply in the first few. Separate the session-order effect from prompt repeats.
3. **Other needs met.** Exploration drops when another deviation is large. Here that means the writer is behind their own usual pace: words per minute below their own median for that point in a session.

**Prediction.** Tests 1 and 2 are positive: exploration falls as error bars narrow. Test 3 is negative: pressure suppresses exploration.

**Cost:** under 1 CPU-hour. The chess version is D23b.

### 8. D14. Controlled variables (set points)

**Theory.** The curator: set points are what a person is trying to keep, and "anything can be a set point". Perceptual control theory has a standard test for what a person controls: disturb a candidate variable and see whether they act to restore it. In CoAuthor every suggestion is a disturbance.

**Disturbance vector** per offered suggestion (the change it would make to the text):
- **local and free today:**
  - topic drift from the preceding paragraph (1 - embedding cosine);
  - changes in sentiment and formality;
  - tense share and grammatical person share;
  - dialogue introduced;
  - a new named entity;
  - length.
- **from the literal transcriber, when G3-A lands:** topic continuity (Q1), register (Q3), tone change (Q4), dialogue (Q5) and contradiction (Q7).

**Tests:**
1. **Protection.** Does the probability of dismissing or editing rise with the size of the disturbance on a variable, beyond D1's features? Steep slopes mark population-level controlled variables.
2. **Restoration.** After an accept-then-edit, does the edit move that variable back toward its pre-suggestion value? Opposing the disturbance is the signature of control.
3. **Personal set points.** Writer-specific protection slopes, partially pooled, with split-half reliability across sessions.

**Prediction.** Topic, tense and person are protected by nearly everyone, because of genre rules. Register and tone protection differ reliably by writer (split-half r above 0.3).

**Meaning.** If restoration shows up, corrections are a direct read of set points, and the engine should treat them that way.

**Cost:** 2 to 3 CPU-hours, plus GPU minutes for the classifiers. D22 reuses the disturbance vectors.

### 9. D12. Departures from the model's own favorite

**Theory.** The curator: the AI reader predicting its own habits "would be useful information". In the essays' definition, attention is a departure from the reader's own expected process. So the reader's habit is the reference, and the person's departures from it are the signal.

**The data already holds the model's own preference.**
- Every `suggestion-open` event in the public CoAuthor release stores each suggestion's `probability`. The released interface code computes it as exp(sum of token log-probabilities) × 100 over the raw GPT-3 completion.
- In the analyst's rerun, writers took the menu's most probable suggestion 22.4% of the time and its least probable 17.0% (7,345 matched selections from five-item menus; chance is 20%).

Confirm both against the prepared source.

**Method:**
- Rank and standardize each suggestion's logged probability within its menu.
- Add P1's local readers, to see how much the reader's identity matters.
- **Per decision:** did the writer take the model's favorite, or a less likely option?
- **Per writer:** the mean standardized probability of chosen suggestions minus the menu mean, with split-half reliability across sessions (odd against even).

**Prediction.** Writers differ reliably in how far they depart from the model's favorite (split-half r above 0.3), and that departure carries more personal signal than accept rates do.

**Cost:** under 1 CPU-hour.

### 10. D29. Where writers stop: stopping points as set points (new)

**Theory.** "Anything can be a set point." Where people stop reveals their targets:
- taxi drivers quit at a daily earnings target (Juechems & Summerfield 2019 review the case);
- marathon finishing times bunch just ahead of round numbers ([Allen et al. 2017](https://doi.org/10.1287/mnsc.2015.2417)).

**Method:**
- Take the distributions of final word counts and session durations.
- Run a bunching estimator around round numbers and just after the ten-minute timer, which enabled the finish button.
- Compute per-writer stopping lengths and their reliability across sessions: does each writer have their own length set point?

**Prediction.** Durations bunch just past the timer, which is an imposed set point. Beyond it, stopping lengths are writer-consistent personal set points, with split-half r above 0.5.

**Cost:** under 1 CPU-hour.

### 11. D13. Goldilocks, and "easier than expected"

**Theory.** The curator defines aesthetic pull as compression progress. Three findings bracket the test:
- Infants look away from events that are too predictable or too surprising ([Kidd, Piantadosi & Aslin 2012](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0036399)).
- Liking of music is an inverted U in surprisal (Gold et al. 2019).
- Pleasure from easy processing peaks "when processing is expected to be difficult, yet turns out to be easy" ([Reber, Schwarz & Winkielman 2004](https://pages.ucsd.edu/~pwinkielman/reber-schwarz-winkielman-beauty-PSPR-2004.pdf)).

**Method:**
1. Fit acceptance and decision latency against each suggestion's mean per-token surprisal given context (P1, c3), with splines, within writer. The logged GPT-3 probability covers the whole completion, so normalize it by length if it's used.
2. Add surprisal relative to expectation: the suggestion's surprisal minus the mean surprisal of the writer's own recent text.

**Predictions:**
- An inverted U in raw surprisal supports interest as learning progress.
- Acceptance rising as suggestions get easier than the recent text, at fixed raw surprisal, supports the curator's "pleasure is better than expected".
- Acceptance falling steadily with raw surprisal alone supports a plain ease account.

**Cost:** under 1 CPU-hour.

### 12. D24. Does a solution follow its need? A natural need switch at the ten-minute timer (new, exploratory)

**Theory.** The curator adopted animal learning's test today: a solution has become an end if it continues after the need it served is met another way. CoAuthor has a natural need switch. Writers had two requirements: collaborate for at least ten minutes, and give the piece a clear ending or stance. A timer enabled the finish button once the ten minutes were up ([Lee, Liang & Yang 2022](https://arxiv.org/pdf/2201.06796), sections 4.2.1 and 4.3.2). At the timer, the time need is met and the ending need remains.

**Method.** Run a regression discontinuity in session time at the timer. Use sessions that continue past it, compared within writer. Measure:
- request rate and acceptance per minute;
- the closure content of accepted suggestions and typed text: concluding markers, final-stance phrases and story-ending cues, from a frozen lexicon plus embedding similarity to known endings.

Repeat around each writer's own median final length, and report sensitivity to the window width.

**Prediction:**
- **Goal-directed use:** the content of requested and accepted suggestions shifts toward closure at the timer, so the solution follows the active need. Requests that served only the time need drop.
- **Use as an end, or play:** rate and content stay the same across the timer.

**Label.** Exploratory: endings are self-selected, and writers who continue past the timer differ from those who stop.

**Cost:** under 1 CPU-hour.

### 13. D20. Influence without selection

**Theory.** Rejecting a suggestion doesn't mean ignoring it. Writers "abstracted and extracted" parts of suggestions they rejected, and suggestions shifted their plans ([Bhat et al. 2023](https://arxiv.org/abs/2208.00636)). That's the leapfrog at its smallest scale: the model shapes the middle even when it loses.

**Method.** Measure overlap, both content-word and embedding, between each dismissed suggestion and the writer's next 50 typed words. Compare against a permutation baseline: menus from other sessions on the same prompt at a similar point.

**Prediction.** Uptake of dismissed suggestions exceeds the baseline, and it varies reliably by writer.

**Cost:** under 1 CPU-hour.

### 14. D28. Going back and forth marks near-ties (new)

**Theory.** In ethology, out-of-context acts appear under motivational conflict. In a menu, moving back and forth between options is the visible sign of a near-balanced choice.

**Method.** Per menu, count hover switches between distinct suggestions before the decision. Relate the count to:
- within-menu dissimilarity (D2);
- the spread of the readers' scores (P1);
- decision latency;
- later reversal (D3).

**Prediction:**
- Alternation is higher on near-tie menus.
- It predicts longer latency and more later reversals.
- Per-writer alternation is a reliable trait.

**Cost:** under 1 CPU-hour.

### 15. D2. Are menus near-ties? Do writers differ in taste at all?

**Method:**
- For menus with more than one suggestion, compute within-menu dissimilarity: the mean pairwise embedding cosine distance. Fit the content choice model, and report its log-loss gain over uniform by dissimilarity quintile.
- Also fit a hierarchical Bayes multinomial logit, the standard individual-preference model in marketing's choice-based conjoint. Per-writer coefficients on suggestion attributes are drawn from a population distribution. The attributes are length, position, context overlap, decoding setting and novelty. The estimated spread of that distribution tests directly whether writers differ in taste at all.

**Prediction.** The gain is near zero in the most similar quintile and positive in the most dissimilar.

**Theory.** Ties carry little information about preference, so the candidate-choice null would be a property of the menus.

**Cost:** under 1 CPU-hour.

### 16. D18. Sacrifice (exploratory)

**Theory.** The curator's question 2: which goal is on top shows in "what are you willing to sacrifice for the one above it".

**Method.**
- Find spans, accepted or typed, that are later deleted.
- Compare deleted with surviving spans on fluency (model likelihood), length and prompt-fit. A writer who deletes fluent but off-prompt text is sacrificing fluency for the prompt goal.
- Estimate per-writer sacrifice rates and their split-half reliability.

**Prediction.** Writers differ reliably in what they sacrifice.

**Label.** Exploratory: the goals here are task-level (fluency, length, prompt), not drives.

**Cost:** 1 to 2 CPU-hours.

### 17. D15. Holding the common pieces constant

**Theory.** The curator: "hold the human common pieces constant."
- Survey researchers do this with anchoring vignettes: everyone rates the same stimulus, so differences are about the person.
- Neuroscientists do it with hyperalignment: map everyone into a shared response space first, then read individual differences from what's left. After alignment, the split-half reliability of fine-grained individual differences rose from 0.78 to 0.87, while coarse differences didn't change ([Feilong et al. 2018](https://www.biorxiv.org/content/10.1101/296012)).

**Method:**
- Fit crossed random effects for writer, prompt, decoding setting and writer × prompt.
- Take each writer's residual profile, conditional on context.
- Compare split-half reliability of writer-to-writer dissimilarities at a coarse grain (handling rates) and at a fine grain (context-conditional residuals).
- State the estimand as "over writers, conditional on these 20 prompts".

**Prediction.** Fine-grained writer differences are more reliable than coarse ones, as in the brain-imaging result.

**Cost:** under 1 CPU-hour.

### 18. V3. A reliability table for every personal feature

**Why.** The reliability paradox: tasks with robust group effects often have poor individual reliability, because the conditions that produce strong group effects keep differences between people small ([Hedge, Powell & Sumner 2018](https://orca.cardiff.ac.uk/id/eprint/102138/1/Hedge.%20The%20reliability%20paradox.pub.pdf)).

**Method:**
- For each candidate personal feature, both what (handling) and how (timing, edits, pauses), estimate the intraclass correlation from D15's crossed model.
- Report the decisions needed for 0.8 reliability: n = 4 × (1 - ICC) / ICC.
- Phase 0's 0.025 is the between-writer share of the backbone's gain on 234 decisions, not of handling. Don't reuse it; this card replaces it with measured values.
- Use trial-level hierarchical models, not difference scores.

**Use.** ToMpathy shows a personal feature only once a person has enough records for that feature to be reliable. D16 uses the values as priors.

**Cost:** hours.

### 19. D11. Expertise in what gets accepted

**Theory.** The curator: writers "take suggestions that they can see the value of through their expertise", so acceptances should still reflect expertise.

**Method:**
- **Predictive.** Add own-fit (similarity between the suggestion and the writer's own typed text earlier in the session) and prompt-fit to D1. Fit writer-specific slopes for own-fit with partial pooling.
- **Descriptive, flagged as using later text.** Are accepted suggestions closer than dismissed ones to the writer's next self-typed sentence?

**Prediction.** Own-fit predicts acceptance at the population level, and the writer slopes are reliable.

**Meaning.** If own-fit matters only when menus are dissimilar (crossed with D2), expertise shows only when the menu gives it something to see.

**Cost:** under 1 CPU-hour.

### 20. D1. A population model with content features

**Evidence it should help.** In Copilot telemetry, acceptance prediction rose from an AUC of 0.631 to 0.780 with suggestion features. Programmer identity added only 0.015, under a changed split ([Mozannar et al. 2024](https://arxiv.org/html/2306.04930v3)).

**Method.** Start from the Phase 0 backbone's features and add:
- the stored MiniLM embeddings of the suggestion and the preceding context, and their cosine;
- suggestion length and menu position;
- novelty against the document;
- session state (recent accepts, time since the last request);
- D12's model-preference features;
- **an effort term.** Accepting saves typing, and writers were paid per session. So acceptance overstates preference for model text unless keystrokes saved and time to the session minimum are modeled.

Fit regularized logistic and gradient-boosted models, chronologically. Then add partially pooled writer offsets. Add G3-A's literal features when they land.

**Prediction.** At least 0.01 half-Brier over the backbone; writer offsets add under 0.01.

**Cost:** 1 to 3 CPU-hours.

### 21. D4. Corrections as preference records

**Method:**
- Classify accepted-then-edited suggestions as housekeeping or content.
  - **Housekeeping:** small character edit distance, one word, or punctuation.
  - **Content:** an embedding shift above a frozen threshold, or a clause added or removed.
- Use P3's intents.
- Fit the half-space model: each content correction says the writer prefers after over before. Robotics learns objectives the same way from physical corrections, with a relevance gate for corrections that no candidate objective explains. Pool the directions, then score later choices by their projection.
- Compare edits to accepted model text with edits to writer-originated text (D22 takes this further).
- **D4b.** Does the content edit move the text toward the writer's own earlier typed style (character n-gram and function-word profiles) and toward the prompt? Is a writer's edit direction consistent across sessions?

**Prediction:**
- Content corrections beat uniform on later choices; housekeeping corrections don't.
- Edit directions are consistent within writers.

**Cost:** 1 to 2 CPU-hours.

### 22. D3. Reversal timing: flow state or near-tie

**Method.** For accepted suggestions, record whether the span survives to the session's end, and how much of it is later edited. Plot reversal against decision latency standardized within writer, with content features as covariates.

**Predictions:**
- The curator's flow-state account: reversals rise at short latencies.
- The near-tie account: reversals rise at long latencies.
- A U shape means both.

**Cost:** under 1 CPU-hour.

### 23. D17. Pauses, bursts and interaction states

**Method:**
- On P2's timelines, classify each interval by location, as writing-process researchers do: within a word, between words, between sentences, between paragraphs, before a suggestion request, and between a menu opening and the decision.
- Instead of a fixed 2-second threshold, fit per-location mixtures of log pause durations. Between-word components correspond roughly to word retrieval, sentence planning and reflection ([Hall, Baaijen & Galbraith 2022](https://eprints.soton.ac.uk/457616/1/Hall2022_Article_ConstructingTheoreticallyInfor.pdf)).
- Compute three kinds of burst:
  - production bursts, which end in a pause;
  - revision bursts, which end in a revision;
  - suggestion bursts, which end in a request.
- **Drop system waits.** The median time from request to menu is about 1.96 seconds, right at the conventional threshold.
- Fit an unsupervised hidden Markov model of interaction states, as a 2021 email study with parallel suggestions did. Report per-writer transition entropy, as the Copilot state taxonomy work did.

**Prediction.** Between-sentence pauses precede requests more often than within-word pauses do: requests follow planning.

**Cost:** under 1 CPU-hour. D16 takes its features as soon as they exist.

### 24. D5. The leapfrog inside a session

**Method.** Bin sessions by the share of model text. Identify the writer of held-out sessions among the 61 from three channels:
- final-text character n-grams;
- human-typed text, matched for length;
- selections and timing.

**Predictions:**
- Channel 1 falls with the model share (trivial).
- Channel 3 holds.
- The non-trivial one: channel 2 becomes less distinctive per word as the model share rises.

**Caution.** On the CoAuthor platform, an instruction-tuned model (text-davinci-003) made essays more alike than solo writing did (0.166 against 0.154). Base davinci, the model CoAuthor used, didn't significantly ([Padmakumar & He 2024](https://arxiv.org/abs/2309.05196)). Expect small effects.

**Cost:** 1 to 2 CPU-hours.

### 25. D8. Stated purposes on Wikipedia

**Data:**
- the labeled edits of [Yang et al. 2017](https://aclanthology.org/D17-1213/) (13 intent categories; the paper links its data);
- the five full histories from the downloads.

**Method:**
- Predict the edit intent from diff features alone, from the summary alone, and from both, stratified by diff size.
- Then predict each editor's next intent from their history.

**Prediction.** Ghost's stated-purpose result (up to 0.64 nats at the root when leaf evidence is sparse) predicts that the summary helps most for small diffs.

**Why.** It runs on public data anyone can check.

**Cost:** 2 to 4 hours, mostly serial fetching.

### 26. D7. Dwell decomposed into preference, information and cost

As specified in the 14 October spec, F11.

**Prediction.** The information term adds prediction beyond preference.

**Cost:** under 1 CPU-hour.

### 27. D9. Pooling curves and preference stylometry on panels

**Data:** Community Alignment and DICES-350, with D10's embeddings.

**Method:**
- **Pooling curves:** individual prediction against each person's number of records.
- **Stylometry:** identify a person among others from their choices alone.

**Prediction.** Well above chance, and far below chess.

**Cost:** 1 to 3 CPU-hours.

### 28. D23b. Play in chess (new)

**Data.** The Lichess month from the downloads.

**Method.** For each player, measure opening novelty: leaving their own repertoire, against their earlier games in the month. Relate it to their state at the time:
- after a win streak, against after a loss streak;
- with their rating above, against below, their own recent mean.

**Prediction.** Novelty rises when other needs are met (after wins, above their mean) and falls under pressure. That's D23's test 3 in a second domain.

**Cost:** about 2 CPU-hours after parsing.

### 29. D24b. Devaluation on Wikipedia: editing after promotion (new; about a day)

**Method.** Compare editors' activity on an article before and after it's promoted to Good or Featured status, against matched articles that weren't promoted. Promotion meets the need "make this article good".

**Prediction:**
- If editing the article was a solution, activity drops after promotion.
- If it has become an end (for example, ownership of the page), activity persists.

**Cost:** about a day, mostly fetching assessment histories. Run it only after everything above it has started.

### 30. D19. A dictionary of shared recipes (exploratory)

**Theory.** Drives and learned recipes are pre-made pieces reused in many places. Interpretability research finds reused features in networks with sparse dictionary learning.

**Method.** Run non-negative matrix factorization over per-session process and content features, with k from 5 to 15. Check component stability across bootstrap resamples, and the reliability of per-writer loadings.

**Cost:** under 1 CPU-hour.

### 31. D10. Embeddings

MiniLM encodings for the panels, for WildChat (200,000 user turns) and for DiffusionDB (200,000 prompts). This feeds D9 and later rounds.

**Cost:** under 1 GPU-hour on the local GPU.

## 5. The spending ladder

The curator's rule: spend small money on clear negatives, and run marginal and positive results in full. Clinical trials use the same rule under the name non-binding futility stopping. Every paid node climbs these rungs.

**Rung 0: known-answer checks.** Run the batteries, parse validity checks and positive controls, for pennies. Any of these stops that line:
- parse validity under 95%;
- a failed battery;
- a failed positive control.

**Rungs 1 to 3: three looks, for futility only.**
- **The statistic.**
  - d is the per-session gain of the card's model over its baseline, in half-Brier.
  - z_t is the mean of d divided by its standard error, clustered by writer (sessions nest within the 61 writers). Never compute it over decisions.
  - t is the share of sessions scored.
  - Draw sessions in a writer-stratified random order fixed before the first look.
- **At 20%: stop if z_t < -0.5.** The gain is clearly negative.
- **At 50%: stop if z_t < 0.** There's no gain after half the data.
- **Otherwise run to 100%,** and test at the full run only, one-sided at α = 0.05. "Useful" is declared only there.

**What this rule does.** The research pass simulated it with 400,000 replicates, for a run powered at 80% to detect a 0.01 gain:
- with no real effect, it spends about 63% of the full cost on average, and the false-positive rate stays at about 0.046;
- with a real effect of the design size, power drops only from 0.80 to 0.77, at about 95% of full spend.

The same simulation rejected three alternatives:
- conditional power at the current trend cuts spend more, but drops power to 0.70;
- conditional power at the design effect almost never stops early;
- a 10% pilot saves nothing extra.

**Three rules keep it honest:**
1. Write the rule into the card before the first look.
2. Never call a result "marginal" by eye between looks. The thresholds decide.
3. Never stop early for a positive. The curator pays for positives to run in full.

**Margins.** The test is "gain above zero", powered to detect 0.01 half-Brier. That isn't "gain above 0.01". Report both the test and whether the point estimate reaches 0.01.

**Open-ended batches.** If a node runs "another batch and so on" with no fixed end, report e-values instead of p-values. They keep their error guarantees under optional continuation.

## 6. Gear 3 campaign G3-S15-DRIVE-1

**Prices** as checked on 16 October, Anthropic batch pricing per million tokens:
- Claude Haiku 5.5: $0.05 input, $0.25 output;
- Claude Sonnet 5.5: $1 input, $5 output.

Dollar figures include a 1.4 safety factor. Count the actual deduplicated inputs before any estimate is final.

| Node | Order | What it buys | Rungs | Forecast | Cap | Wall-clock |
|---|---|---|---|---|---|---|
| **G3-A0. Haiku batteries** | 1 | Whether Claude Haiku 5.5 passes the same 200-item constructed batteries as the local readers, on Q1 and Q3 to Q10 | Rung 0 | under $0.10 | $1 | about an hour |
| **G3-A. Haiku literal pass** | 2 | Literal features for D22, D14, D1 and D4: Q1, Q3, Q4, Q5 and Q7 on about 80,000 deduplicated option inputs; Q8 and Q9 on about 5,000 correction pairs and on the D8 Wikipedia edits | Runs only if G3-A0 passes. Label sessions in the fixed writer-stratified order. At 20% and 50%, compute the gain of P4's frozen base model plus the Haiku features over P4 alone, on the labeled sessions, and apply section 5's stops. Questions Haiku passes run here; any it fails go to G3-F | about $17 for CoAuthor, plus about $1.50 for Wikipedia (assumes about 12,000 edits, two questions each, about 800 input tokens per call; count first) | $20 | under a day; batches mostly finish within an hour and expire at 24 hours |
| **G3-B. Sonnet agreement audit** | 3 | Agreement with the reader that ran the literal pass, on a random slice. It's one input to reference labels, not truth by itself | A 1% slice first. Expand to 5% in total, including the 1%, only if Cohen's κ is under 0.8 on any question | $3.40 at 1%; about $17 at 5% in total | $20 | a few hours |
| **G3-D. Chess slice** | 4 | Deviation classes, and the identification positive control, on the Lichess download | One week of games first. The stylometry positive control must reach at least 25% rank-1 identification among 100 players (chance is 1%), or the node stops. Then the month. Maia-2 runs on the local GPU when it's free, otherwise on Modal | $0.50 to $1 pilot; $2 to $6 in full | $8 | hours for the pilot; about a day in full |
| **G3-F. Fallback literal pass** | only for questions Haiku fails | Qwen 3.5 9B with vLLM on a Modal L40S | Only the failed questions, never one G3-A also runs. The same three looks as G3-A | about $21 | $25 | about 9 hours; the cap stops it |
| **Reserve** | | A recovery plan, reviewed separately | Not used without that plan | | $5 | as planned |

**Ceiling.** The $60 gross ceiling is enforced in code and binds in every case. If Haiku passes some questions and fails others, G3-A and G3-F split them, and G3-B's expansion beyond 1% yields first. $60 covers either pure branch:
- Haiku branch: $1 + $20 + $20 + $8 + $5 = $54;
- fallback branch: $1 + $25 + $20 + $8 + $5 = $59.

**The first $10, on handoff.** These run in order, all inside the $10 window:
1. G3-A0 (under $0.10);
2. G3-A's first 20% look (about $3.40 for CoAuthor and $0.30 for Wikipedia);
3. G3-B's 1% slice, drawn from the sessions already labeled ($3.40);
4. G3-D's one-week pilot ($0.50 to $1).

That's about $8.20 at most. Futility can stop G3-A at its first look before the larger approval is even read.

**The one request to the curator.** Build the route first. As soon as it exists, submit the detailed final-approval request that the stone rules require before spend passes $10:
- exact commands;
- wall-clock per node;
- test details;
- total dollars;
- its hash.

Nothing past $10 runs until he approves that request.

**Not worth buying:**
- rerunning the 27B reader as a judge (it lost to base rates, and calibration didn't rescue it);
- more profiles (their test is blocked on a Ghost witness, not on money).

**Implementation.** Clone the `runners/stage14_midweek` pattern into a new namespace, for example `runners/drive_g3/`:
- `CAMPAIGN='G3-S15-DRIVE-1'`, the node caps above, and a 6,000-cent gross ceiling;
- `APPROVAL.json` carrying the curator's handoff message verbatim, its date, and this packet's SHA-256;
- **the $10 limit enforced in code**, as standing ruling 6 in `docs/STATE.md` requires. The route refuses any reservation past 1,000 booked cents until a cap approval exists holding the curator's dated reply to the final-approval request;
- **G3-D and G3-F through the same route.** The generic `gear3.py run` path refuses new spend without a cap approval. Never pass `--cap-approval` with packet text;
- reservations before every POST, no automatic resubmission, and reconciliation from provider usage;
- a `gear3.py drive` route like the existing `stage14` routes;
- **set `max_tokens` to 32 or less** for literal answers, and disable thinking for Sonnet. The Stage 14 adapter reserves 1.3 times the counted input plus the full `max_tokens` of output:
  - at Stage 14's 512 tokens, G3-A would reserve about $66 and be refused at its cap;
  - at 32 tokens it reserves about $17, plus the Wikipedia edits;
  - at 64 it would already exceed $20;
- **replace the hard-coded submit cutoff** (Stage 14's adapter refuses submissions after 15 October, 17:00 UTC) with this campaign's own window, ending Monday 19 October, 17:00 PDT, so every batch finishes or expires before Tuesday's close.

## 7. Running order to Thursday

| When | Local (Gear 2, $0) | Gear 3 |
|---|---|---|
| **Fri 16, now** | S0 (T1 and T4), V2, P1 to P4 and the downloads start together. Cards start in rank order as inputs land: D22 waits on P3 and D14; D21 on P1; D6 on P2's hover sequences. V1's Phase 0 arm starts at once | Build the route, submit the final-approval request, then the first $10 |
| **Fri night to Sat morning** | P1 runs overnight on the GPU. CPU cards run in rank order. S0's T3 and T2 follow their downloads | After approval: G3-A to its 50% look, then in full unless stopped; G3-B as its rule says |
| **Sat to Mon** | Continue down the ranks. Extend marginal and positive cards once | G3-D in full if its pilot passed |
| **Tue 20** | A one-page plain-language digest of the descriptive results, for the talk | Close the campaign; reconcile |
| **Wed 21** | Freeze. The machine goes to ToMpathy's rehearsal | |

## 8. Authorization (in force when the curator hands this packet over)

1. **Descriptive lane.**
   - Run every card and shared pass here at Gear 2, on data already held or freely downloadable: CoAuthor, DICES, Community Alignment, WildChat, DiffusionDB, the Yang et al. 2017 Wikipedia edit labels, Wikipedia histories through the API, one Lichess month, and the released IteraTeR classifier. This runs before Ghost twins and engine admission.
   - Every result is DESCRIPTIVE: frozen code and comparators per card, full specification curves, never promoted, never an admission witness.
   - Time-box and extend as section 0 says.
   - Deliver S0's references to Ghost Scale as aggregates only.
2. **Gear 3 campaign G3-S15-DRIVE-1.**
   - Build the route in section 6 with a hard gross ceiling of $60 and the node caps above.
   - G3-F runs only for questions Haiku fails, and never on a question G3-A runs.
   - The $5 reserve isn't usable without a separately reviewed recovery plan.
   - Implement section 5's ladder:
     - known-answer checks first;
     - looks at 20% and 50% of sessions, in a fixed writer-stratified order, with writer-clustered errors;
     - stop on an engineering failure, at 20% if z < -0.5, or at 50% if z < 0;
     - otherwise run in full;
     - never stop early for a positive.
   - Run the first $10 as section 6 lists.
   - Submit the detailed final-approval request as soon as the route exists. Nothing past $10 runs until the curator approves it, and the route enforces that in code.
   - These runs serve the descriptive lane; their outputs are never admitted.
3. **Data transfer.** The curator accepts sending:
   - deduplicated CoAuthor suggestion, context, and correction before-and-after text, and Wikipedia edit text, to the Anthropic API for G3-A and G3-B;
   - the same text to Modal containers, only for the questions G3-F covers;
   - Lichess games (CC0) to Modal for G3-D, when the local GPU is busy.

   No raw text appears in public outputs.

## 9. Pre-mortem

| Failure | Guard |
|---|---|
| Descriptive positives that won't replicate | Frozen code per card, full curves, no promotion, confirmation later on locked holdouts |
| V1 shows our instruments are blind at the scale that matters | That's a result. It reframes every null so far, and it tells the engine where to spend effort |
| D21's readers converge because they share training data, not because of context | Hold the item fixed and vary only context. The Pythia ladder shares data across sizes, which isolates size from data |
| D22's intent labels are too weak to separate levels | P3's hand-labeled calibration set comes first. If style and coherence stay near chance, report meaning-changed against fluency only |
| D27 reads as an AI detector | It's measured inside CoAuthor, with ground truth, in aggregate. No model leaves the repository |
| D16 mostly identifies prompts, not writers | The hard-trial version holds prompts constant |
| D16's how wins only through typing rhythm | Then the result is biometric, not cognitive. Decision latency must identify writers on its own |
| D24 confuses wrapping up with satiation | The ending requirement is still active after the timer. The closure-content measure separates a solution following its need from a writer quitting; within-writer comparison, window sensitivity and the exploratory label do the rest |
| Agents spend the week on operations | The time box. Blocked cards are recorded, not repaired indefinitely |
| An early look stops a real effect | At the design effect, power drops from 0.80 to 0.77. The stop report keeps the interim interval, so the curator can overrule it |
| Interim looks computed over decisions instead of writers | Standard errors over decisions, or over sessions without clustering, inflate z. Cluster by writer |
| Hover counts read as attention | A hover isn't reading. D6 treats it as evidence of examination, not proof, and checks the first-item auto-highlight confound |
| CoAuthor licensing | API and Modal transfer only as section 8 states; aggregates only in public |
| Ghost's larger allocation slows Sounding Line | Sounding Line keeps priority, and Ghost's 5% interference rule still binds |
| The demo week starves the machine | ToMpathy's rehearsal has priority on Wednesday; research yields |

## Sources

**Repositories read 16 October:**
- **Sounding Line `c95dff4ad`:**
  - `runners/gear3.py`, `runners/stage14_midweek/api.py` and `budget.py`;
  - `CURRENT_STATUS.md` and `docs/STATE.md` (standing rulings 6 and 7);
  - `docs/design/stage-15/DATA_INTAKE.md` and `F4_NATIVE_READINESS.md`;
  - `results/phase_2_4_stage_15/PHASE0_REPORT.md` and `PHASE0_SUMMARY.json`.
- **Ghost Scale `d84e023a2`:**
  - `docs/versions/v23-research-division/TWIN_INPUT_CONTRACT.md`;
  - `ghostscale/validation/soundingline/v23/twin_contract.py`;
  - `results/v23/CURRENT_STATUS.json`.

**CoAuthor:**
- [Lee, Liang & Yang 2022](https://arxiv.org/pdf/2201.06796): davinci with four decoding settings, 20 prompts, five suggestions per request, 63 writers.
- The display-order, selection-share, model-probability and hover figures are the analyst's rerun on the public release. Confirm them against the prepared source.

**New today:**
- Merging of opinions: [Blackwell & Dubins 1962](https://doi.org/10.1214/aoms/1177704456).
- Convergence across models (a position paper): [Huh et al. 2024](https://arxiv.org/abs/2405.07987).
- The Pythia suite: [Biderman et al. 2023](https://arxiv.org/abs/2304.01373).
- Model size and reading times: [Oh & Schuler 2023](https://aclanthology.org/2023.tacl-1.20/).
- The writing process: [Flower & Hayes 1981](https://doi.org/10.58680/ccc198115885).
- Opinionated suggestions: [Jakesch et al. 2023](https://arxiv.org/abs/2302.00560).
- Preferences in the state of the world: [Shah et al. 2019](https://arxiv.org/abs/1902.04198).
- Bunching at round numbers: [Allen et al. 2017](https://doi.org/10.1287/mnsc.2015.2417).
- Play: [Špinka, Newberry & Bekoff 2001](https://doi.org/10.1086/393866); [Burghardt 2010](https://www.museumofplay.org/app/uploads/2022/01/2-3-article-comparative-reach-play-and-brain.pdf); novelty in active inference, [Schwartenbeck et al. 2019](https://doi.org/10.7554/eLife.41703).
- Influence without selection: [Bhat et al. 2023](https://arxiv.org/abs/2208.00636).

**Methods carried from revision 1** (details and more sources in `claude/STEAL_LIST_2026-10-16.md`):
- Copilot acceptance: [Mozannar et al. 2024](https://arxiv.org/html/2306.04930v3).
- Speaker verification: [Reynolds, Quatieri & Dunn 2000](https://www.ll.mit.edu/r-d/publications/speaker-verification-using-adapted-gaussian-mixture-models).
- Keystrokes in essays: [Hao & Fauss 2024](https://arxiv.org/abs/2411.13699).
- Chess: [McIlroy-Young et al. 2022](https://arxiv.org/abs/2008.10086).
- Hyperalignment: [Feilong et al. 2018](https://www.biorxiv.org/content/10.1101/296012).
- The reliability paradox: [Hedge, Powell & Sumner 2018](https://orca.cardiff.ac.uk/id/eprint/102138/1/Hedge.%20The%20reliability%20paradox.pub.pdf).
- Testing our tests:
  - plasmode simulation: [Vaughan et al. 2009](https://pmc.ncbi.nlm.nih.gov/articles/PMC2678733);
  - injection-recovery: [Christiansen et al. 2015](https://arxiv.org/pdf/1507.05097);
  - Brier decomposition correction: [Siegert 2013](https://arxiv.org/pdf/1303.6182).
- Futility stopping: [Kunzmann et al.](https://arxiv.org/pdf/2010.06567).
- E-values: [Grünwald, de Heide & Koolen](https://arxiv.org/abs/1906.07801).
- Latent exposure: [Liang et al. 2016](https://arxiv.org/pdf/1510.07025).
- Edit intents: [Du et al. 2022](https://arxiv.org/pdf/2203.03802); [Yang et al. 2017](https://aclanthology.org/D17-1213/).
- Pause mixtures: [Hall, Baaijen & Galbraith 2022](https://eprints.soton.ac.uk/457616/1/Hall2022_Article_ConstructingTheoreticallyInfor.pdf).
- The Goldilocks effect: [Kidd, Piantadosi & Aslin 2012](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0036399).
- Fluency and pleasure: [Reber, Schwarz & Winkielman 2004](https://pages.ucsd.edu/~pwinkielman/reber-schwarz-winkielman-beauty-PSPR-2004.pdf).
- Homogenization: [Padmakumar & He 2024](https://arxiv.org/abs/2309.05196).

**Prices:** [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing); [Anthropic batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing); [Modal pricing](https://modal.com/pricing).
