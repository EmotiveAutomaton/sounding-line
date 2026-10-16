# Sounding Line next round: research division program, 14 October 2026

**What this is.** The commissioning spec for Sounding Line's next round, written for the curator and the Sounding Line coding agent. It turns walkthrough I's decisions into an operating model:
- a portfolio of sweep families with a stopping rule;
- zero-cost analyses of data we already hold;
- the repair pass;
- new testbeds and datasets (no human studies);
- reporting in textured form.

It is a design, not a launch. Admission, gear choice and spend follow the repository's existing rules.

**As of 14 October 2026, 20:15 PDT.**
- **Sounding Line `main`:** `0a956219c`. Stage 14 has no active scientific worker. The repair pass is authorized but not launched.
- **Friday's joint final packet:** due 16 October, 18:00 PDT, with new long comparisons held from 10:00 PDT Friday for reporting. This program starts after that packet, except Phase 0, which can run as soon as the packet work allows.
- **Cloud campaign:** $5.48 booked of $50, leaving $44.52.

**Companion specs.**
- `TOMPATHY_ENGINE_SKELETON_SPEC_2026-10-14.md`: the ToMpathy 0.3 engine whose modules these families test. The engine lives in `tompathy/engine/`, and each card pins the ToMpathy commit it tested.
- `GHOST_SCALE_NEXT_ROUND_SPEC_2026-10-14.md`: constructed twins of these testbeds, with planted truth.

**The curator's decisions this spec implements (walkthrough I, 18:08 PDT).**
1. **Testbeds:** add chess and Wikipedia, and keep going deeper on CoAuthor.
2. **No human studies.** Find existing datasets instead.
3. **Stopping rule:** stop a family after about five to seven null batches, not two. Use it to "sear through the possibility space" and return textured results: "a research division", not a lab.
4. **Noise:** a per-mark diagnosticity weight ("how informative") replaces a noise bin.
5. **Model everyone.**
6. **Weak individual signal is desired.** It should show that one person's values are hard to extract and that pooling ("the global tab") is the way out.
7. **Repairs:** run as many as can and should be done.
8. **Data:** find and download new data as needed.
9. **Gears:** Gear 2 by default. Gear 3 is acceptable when it burns through possibility space faster.

**Decisions applied from the curator's follow-up (14 October, 20:00 PDT).**
10. **Stopping rule:** the pooled rule with a hard cap of seven is adopted (Part 0.2).
11. **Gear 3:**
    - No new money up front.
    - Extra spend unlocks in three tranches, each only after a confirmed major positive, and only with the curator's go (Part 5).
    - With no positives, total spend stops at the $44.52 already approved.
12. **Engine pinning:** by ToMpathy commit.

---

## Part 0. Operating model: a research division

### 0.1 Units

- **Family.**
  - **One hypothesis**, taken from the theory store or the engine plan, with a pre-registered useful margin *δ* (delta): the smallest effect worth building on.
  - **Many variants**, the cells of a sweep grid.
  - **Datasets** on which it runs.
- **Batch.** A fixed, pre-declared slice of evidence on which every surviving variant in the family is scored, for example one block of ten CoAuthor writers' decisions in time order. Batches are defined before launch and never resized after a look.
- **Look.** The decision point after each batch.

### 0.2 The stopping rule, made rigorous

Counting null batches is the weakest version of the rule.

**Why counting fails.** If each batch has power *p* to detect a real effect at the margin, the chance that *k* batches in a row all come out null anyway is (1 − p)^k:

| per-batch power *p* | k = 2 | k = 5 | k = 7 |
|---|---|---|---|
| 0.1 | 0.81 | 0.59 | 0.48 |
| 0.2 | 0.64 | 0.33 | 0.21 |
| 0.3 | 0.49 | 0.17 | 0.082 |
| 0.5 | 0.25 | 0.031 | 0.0078 |

- **The power we have.** With small effects and about 60 writers, *p* between 0.1 and 0.3 is realistic. So "seven nulls" still kills 8% to 48% of real families.
- **The mirror error.** One lucky batch resets the count, so dead families also survive too long.

**The rule to use instead** keeps the curator's "seven" as a hard cap.

1. **Model.**
   - A hierarchical model of variants within the family, with makers as a crossed random effect.
   - The frozen baseline is scored in every batch on the same makers.
   - A mildly skeptical prior: centered at zero, spread about *δ*.
2. **Burn-in.** No kill decision before batch 2.
3. **Kill test.**
   - After each batch *b* from 2 to 7, compute *q*: the posterior probability that the family's best variant, after shrinkage, beats the baseline by at least *δ*.
   - Kill if *q* < 0.10.
   - An equivalent form: the predictive probability of success at batch 7 is below 0.10.
4. **Promotion.**
   - Promote a variant to confirmation when its posterior probability of beating zero exceeds 0.975.
   - Promotions pass through online false-discovery control: e-LOND, because families share makers and so are dependent.
5. **Hard cap.**
   - Seven batches.
   - If no boundary is crossed by then, the record is **inconclusive**, with the pooled interval. It is never "null".
   - A family is revived only with new makers or new data, never by rerunning.
6. **Calibrate before launch.**
   - Simulate the rule on the Ghost twin of each testbed, at zero effect and at effect *δ*, with realistic maker variance.
   - Tune the kill threshold so that at most 10% of margin-level families die across all looks.
   - Report the kill rate for dead families and the expected number of batches.
7. **Fallback for irregular looks.** Kill when the upper bound of a one-sided 90% confidence sequence falls below *δ*. That bound stays valid however often you look (Ramdas et al., 2023; Howard et al., 2021).
8. **Inside a family.**
   - **Compute:** successive halving shares it among variants (ASHA, η = 3).
   - **Scarce GPU or API slots:** they go to the top two variants by top-two Thompson sampling.

**What pooling buys** (normal approximation, per-batch power 0.2, one-sided tests at 5%):

| rule | dead families killed by batch 5 | margin-level families killed |
|---|---|---|
| 5 consecutive nulls | 77% | 33% |
| pooled one-sided 90% futility test at batch 5 | 70% | 10% |
| one-sided 90% confidence sequence, checked every batch | at least 24% | at most 10% across all looks |

Pooling kills dead families about as fast as counting, and loses about a third as many real ones.

### 0.3 Controls in every family

- **Positive control by spike-in.** Insert synthetic makers with planted preferences into the real dataset: about 5% of makers, generated from the Ghost twin and matched to real makers' depth and noise.
  - **Rule:** a family whose instrument cannot recover the spike-in is **blind**, not null, and its result is not reported as evidence about people.
  - **Why it's required:** this is how "weak" stays distinguishable from "broken". The curator wants weak results; weak only means something if the instrument can see strong ones.
- **Negative control.** The same variants run on labels shuffled within maker, or on donor histories. A variant that beats its negative control by less than *δ* cannot be promoted.
- **Pipeline robustness.** Two or three pre-specified analysis pipelines per batch, as a further multiverse axis. In a many-analysts study, 29 teams analyzing one dataset split 20 to 9 on significance (Silberzahn et al., 2018). A batch that is null under only one pipeline is not null.

### 0.4 Textured reporting

- **Specification curve** per family, published after every batch:
  - every variant's estimate, killed ones included, sorted by size;
  - the margin drawn in;
  - a panel showing which choices produced each estimate.
- **Joint tests:** any claim about a whole family uses joint tests across specifications, by permutation or bootstrap with the null imposed, because the specifications are not independent (Simonsohn, Simmons & Nelson, 2020).
- **Winner's curse:** promoted winners' effects are shrunk before anyone builds on them. The megastudy lesson is that top performers' effects are inflated (Milkman et al., 2021).
- **Write-through:** findings go to FINDINGS, the theory store's afterwords (Confidence vocabulary), and a per-family "ToMpathy implication" line: which engine module this admits, kills or leaves inconclusive.

### 0.5 Holdouts

**Three locked holdouts.** Reusing one holdout overfits it (Dwork et al., 2015).
1. **Time:** the last 15% of each dataset by time.
2. **Makers:** 15% of makers, never seen in any batch.
3. **Second dataset:** each family names one dataset it never trains or tunes on.

Confirmation needs all three.

---

## Part 1. Phase 0: what our existing data can settle now

**Scope.** No new data, no inference calls, CPU only. Each runs in minutes to an hour on saved outputs.

**T0a. Where our uncertainty comes from.**
- **Data:** the saved per-writer scores from the cloud-reader study and the midweek baselines (31 writers, 234 targets).
- **Method:** a random-effects decomposition of the paired contrast (partial pooling minus population) into:
  - **within-writer noise:** decision to decision;
  - **between-writer differences:** writers truly differ in how much personalization helps.
- **Decision rule:**
  - If within-writer noise dominates, prequential rescoring (T0c) can buy most of the precision we need from data we already hold.
  - If between-writer differences dominate, only more writers help, which points to the new datasets in Part 3.
  - Either way, a large between-writer spread is itself a finding: personal signal is concentrated in some makers. The engine should then report per-maker predictability.

**T0b. Does the cloud reader know anything base rates don't?**
- **Data:** the 936 saved forecasts from the 27B cloud reader (already paid), with the seven local baselines on identical targets.
- **Method:**
  - Cross-fitted by writer: fit on all writers but one, score the held-out writer.
  - Fit (a) a prior-shift correction by EM (Saerens et al., 2002), then temperature scaling, then (b) a stacked model combining partial pooling with the corrected reader probabilities, on a proper score (Yao et al., 2018).
  - Run separately for each evidence arm: no history, same-session, own cross-session, other-maker.
- **Why this matters:**
  - The raw reader lost to base rates by 0.078.
  - Its errors look like label bias: it put 43% of probability on "edit" against 22% observed, and never named "dismiss" against 23% observed.
  - Its same-session forecasts at 0.85 confidence or above were right about 72% of the time on 50 decisions.
- **Predictions, written now:**
  - Calibration recovers most of the deficit against population, but none against partial pooling.
  - Same-session history adds a little in stacking.
  - Own cross-session history adds nothing over another writer's history.
- **Decision rule:**
  - If stacking beats partial pooling by *δ* = 0.01 on both writer and prompt-crossed intervals, LLM readers re-enter the engine as evidence (Part 2, R1).
  - If not, they stay out as judges, and the transcriber is the only LLM role.

**T0c. Prequential backbone over all of CoAuthor.**
- **Data:** all usable CoAuthor decisions (16,959 handling opportunities from 61 writers).
- **Method:** the existing partial-pooling baseline refit after each session in time order. Each writer's decisions are forecast from everything before them: their own earlier sessions and all earlier writers.
- **Reports:**
  - the gain over population base rates and over personal frequencies, by history length;
  - **the convergence curve:** gain as a function of the writer's number of prior decisions. This is the global tab's curve, measured on real writers.
- **Limits:**
  - The data is historically exposed and the writers are public, so the result is descriptive.
  - This is a deliberate trade against the current design's prompt-novelty rule. Report both the all-decisions and prompt-novel subsets.

---

## Part 2. The repair pass

The curator: "any repairs that can and should be done, should be done". Each repair keeps the original attempt and its cost. Each repaired comparison gets a new identity and its own admission battery.

| ID | What is blocked | Repair | Framing change | Gear |
|---|---|---|---|---|
| **R1** | Three local readers held on the Ollama version mismatch (0.40.3 installed against 0.35.1 admitted) | Re-admit under the installed version with the existing admission battery, or pin 0.35.1 in a separate service | Repair as **evidence sources**: their outputs feed the T0b stacking layer, and are scored only after calibration, never as judges | 2 |
| **R2** | Prototype training held behind a failed readout (the 360M model answered "accept" to 16 of 16) | Replace the language-model readout with **statistical prototypes**: a mixture over writers' decision-feature histories, which is the engine's prototype variant. Admit it on the CoAuthor Ghost twin first | The prototype question becomes "does starting a new writer from the nearest prototypes beat starting from the population?", the Maia4All recipe | 2 |
| **R3** | API profile pilot failed: two of six profiles hit the 500-token output limit | A structured JSON profile with a fixed schema (up to 12 preference statements, each under 25 words) and a 1,500-token allowance; schema-validated | Profiles become **features** for the backbone, not judges. Published evidence ranks past choices first, value profiles second and demographics last (Sorensen et al., 2025) | 3 |
| **R4** | Natural handling screens refused (8B and 3B local models) | Retire as judges | Their literal prompts move into the transcriber catalogue where they ask about text, with admission batteries | 2 |
| **R5** | Paper versus release denominators for ARIES (85 against 87 linked comments) | Resolve by direct comparison of the released records with the paper's appendix; record both | Stays descriptive and paper-clustered | 2 |
| **R6** | 44 blocked cards in the Stage 14 plan | Triage each: rerun if its question is still open and not covered by a family below; retire with a supersession note if it is | Prevents the old forest from absorbing the new program's compute | 2 |
| **R7** | The five unavailable Opus slots in the cloud-reader family | Retire as judges | Optionally reappear in family F4 as a transcriber-backend comparison | 3 |

---

## Part 3. Testbeds and data acquisition

No human studies. Every dataset below is public or obtainable by request. Licenses are as stated on the source pages, checked 14 October 2026; "unstated" means no license was found.

### 3.1 The core testbeds (curator-approved)

| Testbed | What it gives | Ground truth | Depth per maker | Access | First families |
|---|---|---|---|---|---|
| **CoAuthor** (Lee, Liang & Yang, 2022) | Keystroke-level human-AI co-writing: suggestion requests, openings, selections and closes, all timestamped; edits after acceptance | Assigned prompts (goals); handling outcomes | About 23 sessions and about 280 decisions per writer; 61 usable writers | **Already local and fully replayed in Sounding Line.** No license is stated on the site; ask the authors before publishing derived data | F1, F2, F3, F8, F9, F11 |
| **Wikipedia** | Revisions with edit summaries (stated purposes on about 54% of English edits), reverts, bot flags | Stated purpose per edit; revert as policy-error proxy | Thousands of edits for active editors | Dumps (bulk) and API (one connection, about 100 ms between requests); content CC BY-SA | F6, F7, F9 |
| **Lichess** with Maia-2, Maia-3 and Maia4All | About 90M games a month; per-move clocks since April 2017; engine evaluations on about 6% of games | Known objective (win), known move quality (engine), clock pressure as context | Thousands of games for active players | CC0 database. Maia-2 code is MIT; Maia-3 is AGPL-3.0; the Maia4All code is GPL-3.0, marked work in progress | F1, F2, F7, F9 |

### 3.2 Ground truth without a human study

| Dataset | What it adds | Depth | Access | Families |
|---|---|---|---|---|
| **Community Alignment** (Zhang, Milli et al., 2025) | 233,319 four-way choices by 3,603 annotators in five countries; free-text explanations on 44% of choices; demographics and political leaning | Median 67 choices and 26 conversations per annotator | CC-BY-4.0, open | F1, F5, F9 |
| **PRISM** (Kirk et al., 2024) | Per person: stated importance ratings, a self-written system prompt, a value self-description, about 49 rated responses | About 6 conversations per person; 1,396 conversers | Open; human text CC-BY-4.0, model text CC-BY-NC-4.0; no re-identification | F5 |
| **MovieLens Beliefs** (Aridor et al., 2024) | People predict their rating, with a certainty score, before watching; join to the later rating | About 9 beliefs and about 539 prior ratings per user; 3,199 users | GroupLens research terms | F5, F2 |
| **MultiPref** (Miranda et al., 2024) | Choices on helpfulness, truthfulness and harmlessness, with stated reasons, confidence and time spent | About 140 annotations per annotator; 289 annotators | ODC-BY, open | F2, F5 |
| **DICES** (Aroyo et al., 2023) | Every one of 123 raters judged all 350 conversations; demographics; answer times | 350 per rater (DICES-350) | CC BY 4.0 | F1, F2, F9 |
| **summarize_from_feedback** (Stiennon et al., 2020) | Deepest per-labeler histories: about 1,750 comparisons per worker; axis ratings (accuracy, coverage, coherence) | 53 to 63 workers | Loader Apache-2.0; data license unstated | F1, F9 |
| **Persuasion for Good** (Wang et al., 2019) | Schwartz values, Moral Foundations and Big Five tied to a real donation | One dialogue per person; 1,285 people | Apache 2.0 via ConvoKit | F5 (validation only) |
| **PANDORA** (Gjurković et al., 2021) | About 1,800 Reddit comments per user, with self-reported Big Five for 1,608 users | Deep | By request; aggregate results only; honor deletions | F9, F13 |

### 3.3 Planted steering and stated goals in real human records

| Dataset | What it adds | Access | Families |
|---|---|---|---|
| **Jakesch et al.** (CHI 2023) | 1,506 writers co-writing with a model set to argue one side; keystroke-level logs per the paper | OSF materials; contents and license unverified | F8 |
| **Williams-Ceci et al.** (Science Advances, 2026) | 2,582 participants; prior attitudes measured weeks before writing with a biased assistant | Zenodo, CC BY 4.0; the 1.6 MB archive probably holds survey and acceptance data, not keystrokes | F8 |
| **SWE-chat** (COLM 2026) | 17,968 real coding-agent sessions; GitHub user IDs; timestamps; prompt-intent and pushback annotations | Gated (accept terms); ODC-By | F3, F6 |
| **HALIE** (Lee et al., 2023) | Interaction traces on tasks with correct answers (question answering, crosswords) | Apache-2.0 | F6, F7 |
| **CS1 keystroke datasets** (Edwards et al., 2023) | 505 students, 10 tasks, about 5M keystrokes, assignment specs as known goals | Harvard Dataverse; license unstated | F6, F7 |
| **IBM Project CodeNet** (2021) | 13.9M submissions to 4,053 assigned problems; user IDs, timestamps, verdicts | Repository Apache-2.0; separate data license not found | F7 |
| **WildChat-4.8M** (Zhao et al.) | Real chat histories by hashed IP; feedback makes up over half of user turns late in long conversations | ODC-BY; toxic full version gated | F3 |
| **DiffusionDB**; **Pick-a-Pic v2** | Prompt revisions as corrections; a stated prompt, then a choice between two images | CC0; Pick-a-Pic license unstated | F3, F13 |

### 3.4 Art and aesthetics per person (the art thesis, tested)

| Dataset | What it adds | Access | Family |
|---|---|---|---|
| **PARA** (Yang et al., 2022) | 438 subjects, about 1,840 ratings each, with Big Five, art and photography experience | Download page; no license stated; citation requested | F13 |
| **LAPIS** (Maerten et al., 2025) | 552 raters of WikiArt artworks, about 510 ratings each, with art-interest scores | By request | F13 |
| **ArtEmis** (Achlioptas et al., 2021) | 454,684 emotion attributions with written explanations by 6,788 annotators | Form and terms; annotator IDs unconfirmed | F13 |

### 3.5 Acquisition rules

1. **Raw data stays local.** Publish only aggregates and engine packets for public artifacts. Honor each dataset's terms: no re-identification (PRISM); aggregate-only publication and deletion requests (PANDORA).
2. **Pretraining exposure.** Nearly all public data may be in language-model pretraining. This matters only for LLM features: statistical models don't read text with a pretrained prior.
   - For LLM-feature families, prefer slices dated after the transcriber model's training cutoff: Lichess months, Wikipedia revisions, WildChat-4.8M through July 2025.
   - Record the cutoff gap per card.
3. **Identity.**
   - A hashed IP is not a person.
   - Filter WildChat's scripted templates (about 39% of later conversations are identical templates; Hicke & Tomlinson, 2026).
   - Never join makers across datasets.
4. **Exposure ledger.** Extend Sounding Line's exposure audit to every new dataset before first use.

---

## Part 4. The families

**What each card states.**
- the hypothesis, in plain words;
- the theory row it serves;
- datasets;
- variant axes, the sweep grid;
- the metric and margin *δ*;
- the batch;
- controls beyond Part 0.3;
- predictions in advance;
- gear and a rough compute estimate.

**Shared defaults.**
- **Metrics:** half-Brier and log loss, writer-weighted.
- **Holdouts:** Part 0.5's three.
- **Stopping rule:** Part 0.2's.
- **Margins:** proposals. Calibrate them against the Ghost twins before launch.

### F1. Backbone and pooling: the "together" curves

- **Hypothesis:**
  - Pooling across makers improves individual prediction.
  - The gain grows with a maker's history and then saturates.
  - The best pooling structure differs by domain.
- **Serves:** the global tab; the anti-capture principle; the theory store's alignment section ("no single person's data yields a confident estimate").
- **Datasets:** CoAuthor, Community Alignment, DICES, summarize_from_feedback, Lichess (with Maia-2 as the population model), MovieLens 32M.
- **Variant axes:**
  - **pooling structure:**
    1. none (personal only);
    2. population only;
    3. partial pooling of intercepts;
    4. partial pooling of slopes;
    5. prototypes (K = 4, 8, 16, 32);
    6. matrix factorization (rank 4, 8, 16);
    7. nonparametric mixture.
  - **features:** base; plus timing; plus session state; plus literal option features (from F4, once admitted).
  - **history length per maker,** subsampled: 2, 4, 8, 16, 32, 64, 128, 256, all.
  - **number of makers pooled,** subsampled: 10, 30, 100, 300, all.
- **Metric and margin:** gain over population.
  - **CoAuthor:** δ = 0.01 half-Brier.
  - **Chess:** δ = 1 point of move-matching accuracy. For scale, Maia4All gained 1.8 at 20 games.
- **Batch:** one block of makers. CoAuthor: about 10 writers per batch, about six batches, which fits the cap of seven.
- **Predictions:**
  - Partial pooling beats personal-only for makers with fewer than about 30 decisions, everywhere.
  - Personal-only overtakes pooling only in chess, past thousands of games, as Maia's individual models did at 5,000.
  - The between-maker spread of gains is large (T0a).
- **Output:** the convergence curves for the global tab, per domain.
- **Gear:** 2. Roughly 20 to 40 CPU-hours across all datasets. Chess needs GPU hours for Maia inference on sampled positions.

### F2. Diagnosticity: does decisiveness say how much a mark should count?

- **Hypothesis:**
  - Fast decisions carry more preference information than slow ones.
  - Weighting past evidence by decisiveness improves prediction beyond typing effort, which Stage 14 found useless.
- **Serves:** the noise debate's agreed replacement (walkthrough I, question 4).
- **Datasets:**
  - CoAuthor (`decide_seconds`);
  - Lichess (clock deltas, with time left as a separate context feature);
  - MultiPref (time spent);
  - DICES-350 (answer times);
  - MovieLens Beliefs (certainty, as a stated analog).
- **Variant axes:**
  - **weight function:**
    1. none;
    2. logistic in standardized latency;
    3. rank-based;
    4. learned per maker;
    5. shuffled within maker (control).
  - **where latency enters:** weight only; feature only; both (the double-counting control).
  - **near-tie proxy:** model-implied utility gap, used alone or combined with latency.
- **Metric and margin:** the gain of the weighted backbone over the unweighted one. δ = 0.005 half-Brier on CoAuthor (smaller, because this is a refinement); 0.5 points on chess.
- **Predictions:**
  - **Expected:** the latency weight is negative (fast counts more) and beats the shuffled control.
  - **If the curator's "nothing is noise" holds strictly:** weighting adds nothing beyond what latency adds as a feature.
  - **Chess:** decisions under severe time pressure are less diagnostic of style, and that is context, not noise. The weight should fall with time pressure even at equal latency.
- **Gear:** 2. Cheap.

### F3. Corrections as preference records

- **Hypothesis:**
  - Content corrections (edits that change what is said) reveal preference directions.
  - Those directions predict later choices among content-differing options.
- **Serves:** "improvements are corrections" (theory store); the engine's corrections module.
- **Datasets:**
  - CoAuthor: accepted-then-edited suggestions, then later candidate choice;
  - WildChat-4.8M: feedback turns, then later acceptance;
  - DiffusionDB: prompt revisions, then later prompts;
  - Pick-a-Pic: prompts, then choices;
  - SWE-chat: pushback, then later instructions.
- **Variant axes:**
  - **feature map:**
    1. deterministic;
    2. embeddings;
    3. literal transcriber features (once admitted);
    4. combined.
  - **correction filter:** all; content only (Q8 and Q9); process only, as a control.
  - **pooling:** none, or partial.
  - **model:** perceptron-style coactive update, or Bayesian logistic on differences.
- **Metric and margin:** candidate-choice gain over a uniform guess and over the backbone. δ = 0.01 half-Brier.
  - **The current state:** nothing beats uniform on CoAuthor candidate choice. Any clean gain here is the first.
- **Predictions:**
  - **Content-only corrections:** they beat uniform; process-only corrections do not.
  - **If CoAuthor's corrections are mostly local fixes:** the family is inconclusive there and positive on WildChat or DiffusionDB, where corrections are requests about content.
- **Gear:** 2. Transcriber features need GPU time (F4).

### F4. LLMs as evidence: transcriber, calibration, stacking

- **Hypothesis:**
  - Literal LLM answers about options and edits add information beyond deterministic features.
  - Calibrated reader outputs add information beyond the backbone.
- **Serves:** the engine's transcriber and calibration layer; repair R1; T0b's follow-up.
- **Datasets:** CoAuthor options and edits; Wikipedia diffs; Community Alignment responses.
- **Variant axes:**
  - **question set:** Q1 to Q10 from the engine spec, each admitted separately;
  - **model:** local 8B (admitted for factorized transcription), local 27B, a cloud model;
  - **context window:** 400, 1,200 or 3,000 characters;
  - **use:** as features, or as a stacked judge after prior-shift and temperature calibration.
- **Cost control:**
  - Deduplicate by text hash. CoAuthor has 76,891 unique texts.
  - Successive halving on a 10% sample first.
  - Questions that fail admission never reach full runs.
- **Metric and margin:** the gain over the backbone (δ = 0.005 half-Brier as features), and calibration error under 0.05 for any judge.
- **Predictions:**
  - Q2 (new entity), Q5 (dialogue) and Q8 (edit type) pass admission. Q4 (tone shift) and Q7 (contradiction) are borderline.
  - Features help candidate choice more than handling.
- **Gear:** 2 for local models. 3 for the cloud comparison: about 2 to 5 million short calls before deduplication. Budget in Part 5.

### F5. Stated against revealed: ground truth for values

- **Hypotheses:**
  - **(a)** Value directions inferred from a person's choices predict that person's stated preferences better than demographics do.
  - **(b)** Stated preferences add to choice prediction beyond history. The prediction is that this gain is small: published work ranks demonstrations above value profiles above demographics.
  - **(c)** Stated predictions made before an experience are worse than what a pooled model predicts from history.
- **Serves:**
  - the core values box's eventual calibration (the only route to `probability` semantics);
  - the curator's "values: personal and identifiable".
- **Datasets:** PRISM; MovieLens Beliefs; MultiPref (stated reasons, confidence); Community Alignment (explanations); Persuasion for Good (validation: Schwartz values against donation).
- **Variant axes:**
  - **representation of the inferred profile:** preference vector; prototypes; natural-language profile (R3's repaired format);
  - **stated measure:** importance ratings; self-written system prompt (embedded); explanations;
  - **pooling.**
- **Metric and margin:**
  - **(a) and (b):** correlation or area under the curve against stated measures, against a demographics baseline. δ = 0.05 AUC.
  - **(c):** proper score.
- **Predictions:**
  - Weak but real agreement between revealed and stated, matching PRISM's own report of weak correlations.
  - Pooled history beats people's own stated predictions on MovieLens Beliefs.
- **Gear:** 2.

### F6. Goal recovery with stated purposes (top-down entry)

- **Hypothesis:**
  - Joint inference, with a root cue (a stated purpose) and local evidence (the diff), recovers stated purposes better than either alone.
  - The root cue improves the explanation of local decisions.
- **Serves:** "the first goal where the decisions meet"; the curator's top-down function route; Ghost's goal-tree result (it tied at the root without a root cue).
- **Datasets:**
  - Wikipedia (edit summaries; Yang et al. 2017 intent categories as seed labels);
  - git-hosted essays (commit messages);
  - SWE-chat (prompt intent);
  - CS1 (assignment specs);
  - HALIE (known-answer tasks).
- **Variant axes:**
  - **local evidence:** diff features; transcriber edit types; both;
  - **root cue:** none; title; stated purpose; both;
  - **reliability weighting of the cue:** fixed; learned;
  - **hierarchy depth:** 2, 3, 4.
- **Metric and margin:** stated-purpose classification log loss (Wikipedia: 13 intent categories plus Other), and next-edit prediction. δ = 0.02 nats.
- **Predictions:**
  - The root cue helps most when local evidence is sparse.
  - Summaries are formulaic for experienced editors and blank for 46% of edits, so the recoverable signal concentrates in long-history editors.
- **Gear:** 2.

### F7. Deviation classes with partial ground truth

- **Hypothesis:** separating deviations by cause improves individual prediction and makes style estimates more stable.
  - **Classes:** context (clock pressure), policy error (blunders by engine evaluation), habit (repeated openings) and deliberate choice (residual style).
- **Serves:** the triple inference's second step; the divergence classes; the diagnosticity weights.
- **Datasets:** Lichess (primary); CodeNet (verdict types: wrong answer as policy error, time limit as context, language as habit); CS1 keystrokes.
- **Variant axes:**
  - **class model:** none; clock only; clock plus engine-loss; full four-class;
  - **reference policy:** Stockfish-best; Maia-2 at the player's rating; Maia4All personal.
  - **The reference-policy axis is the curator's "whose steps": the reader's own forward model, adjusted to the maker.**
- **Metric and margin:**
  - **Move prediction:** δ = 0.5 points of accuracy against Maia4All at matched history.
  - **Style stability:** split-half agreement of each player's style vector.
- **Predictions:**
  - Removing clock-pressure moves before estimating style raises split-half stability.
  - The full four-class model beats Maia4All by a small margin at 20 to 100 games and converges with it at large histories.
- **Gear:** 2, with a GPU for Maia inference.

### F8. Source trust and steering in real people

- **Hypotheses:**
  - **(a)** Writers' acceptance of AI suggestions tracks the recent quality of those suggestions, like a trust update, better than fixed rates.
  - **(b)** Where the AI was planted to steer, the engine's source-inference module detects steering from the suggestion stream and the writers' uptake.
  - **(c)** Writers with stronger prior attitudes take up less of the steered content.
- **Serves:** Ghost's source-inference and signature results, ported to people.
- **Datasets:** CoAuthor for (a); Jakesch et al. and Williams-Ceci et al. for (b) and (c), subject to the data actually present (verify first).
- **Variant axes:**
  - **trust model:** fixed; recency; Bayesian quality update; steering-aware;
  - **quality proxy:** survival to session end; later edit volume.
- **Metric and margin:**
  - **(a):** acceptance prediction, δ = 0.01 half-Brier.
  - **(b):** steering-condition detection, area under the curve above 0.6 at the session level.
- **Gear:** 2.

### F9. Are values identifiable? (preference stylometry)

- **Hypothesis:** a maker's preference vector, built from choices and corrections only (not text style), identifies the maker among others well above chance.
- **Serves:** "values: personal and identifiable" (filed 14 October).
- **Datasets:**
  - CoAuthor: 61 writers; identify a held-out session's writer;
  - Community Alignment;
  - DICES-350, where every rater saw every item;
  - Lichess: replicate known stylometry as the positive control. 85% top-1 among 2,844 players from 100 games without openings.
- **Variant axes:**
  - **representation:** handling only; corrections only; both; plus timing;
  - **history per maker:** 2 to 64 sessions or blocks.
- **Metric and margin:** top-1 identification accuracy against chance; δ = 5 times chance.
- **Predictions:**
  - Well above chance in CoAuthor and Community Alignment, far below chess.
  - The gap shows how much less a typical writing record carries than a game record.
- **Privacy:** results are reported as aggregates only. No identification model is published, following Maia's choice not to release per-player weights.
- **Gear:** 2.

### F10. Self-reading, blind and knowing

- **Hypothesis:** a model reads its own artifacts' process better than another model does. Run both the blind and the knowing condition (the curator: "just try both").
- **Serves:** "self-reading is self-perception".
- **Datasets:** the model-generated artifact families from Stages 12 and 13, plus fresh generations with logged sampling choices.
- **Arms:**
  - self, blind;
  - self, told the artifacts are its own;
  - another model;
  - the model's own self-report;
  - an LLM-free baseline.
- **Metric:** recovery of logged sampling decisions and stated generation goals.
- **Gear:** 2 for local models; 3 for API models.

### F11. Attention, decomposed

- **Hypothesis:** dwell time on a suggestion decomposes into three terms:
  - **preference:** dwell predicts later acceptance;
  - **information:** longer dwell on novel suggestions at equal acceptance;
  - **cost:** dwell shrinks late in a session at equal novelty.
  - The information term adds prediction beyond the preference term. This is the curator's "another term".
- **Serves:** the attention policy row; the engine's attention frames; the consciousness-traces idea, as traces only.
- **Datasets:** CoAuthor (suggestion open to close or select; reopenings; pauses).
- **Variant axes:** which terms are included; novelty measure (embedding distance, transcriber Q1 and Q2); fatigue proxy (session position, time since start).
- **Metric and margin:** held-out dwell prediction, and acceptance prediction from dwell plus terms; δ = 0.01 half-Brier on acceptance.
- **Gear:** 2.

### F12. Detection, maintained (bounded)

- **Purpose:** keep the bounded detection results alive, using event-level features from the ledger.
- **Rule:** no new family unless F1 to F11 free capacity.
- **Gear:** 2.

### F13. Aesthetic values per person

- **Hypotheses:**
  - **(a)** Personal aesthetic models from ratings beat the population model, with the F1 convergence shape.
  - **(b)** Inferred aesthetic preference vectors predict self-reported traits (Big Five in PARA; art interest in LAPIS) above chance.
  - **(c)** The written explanations in ArtEmis carry preference information beyond the ratings.
- **Serves:** the art thesis ("Art: A Unifying Model"); the core values box for visual artifacts.
- **Datasets:** PARA, LAPIS, ArtEmis.
- **Variant axes:** image features (CLIP-class embeddings; simple color and composition features); pooling structure; history per rater.
- **Metric and margin:**
  - **(a):** rating prediction, δ = 0.02 in correlation.
  - **(b):** AUC δ = 0.05 against demographics.
- **Gear:** 2, with a GPU for embeddings.

---

## Part 5. Schedule, gears and budget

**Order of work, gated:**
1. **Before or right after Friday's packet:** Phase 0 (T0a, T0b, T0c); repairs R5 and R6 (paperwork); data acquisition for Part 3.1 and 3.2.
2. **Week 1:**
   - F1, F2, F3 on CoAuthor;
   - F1 and F9 on Community Alignment and DICES;
   - the chess pipeline (A-lichess, Maia-2 baseline);
   - R1 and R2.
3. **Week 2:**
   - F5 (PRISM, MovieLens Beliefs);
   - F7 and F9 on Lichess;
   - F6 on Wikipedia;
   - F4 local models;
   - F11;
   - R3.
4. **Week 3:** F4 cloud slice (Tranche A); F8; F10 local arms; F13; confirmation runs for promoted variants.

**Gear 2.**
- **Default:** all statistical families are CPU-heavy and cheap. GPU time goes to:
  - Maia inference;
  - embeddings;
  - local transcriber runs (roughly 30 GPU-hours for CoAuthor's unique texts across admitted questions, after successive halving).
- **Coordination:** uses the existing GPU lock and six-hour health cadence.

**Gear 3: no new money up front. Extra tranches unlock only on major positives.**

**Tranche A: the $44.52 already approved** (the remainder of the current $50 campaign). It is spent in this order, stopping when it runs out:
1. **R3, profiles as features.** A pilot on the three discarded pilot writers, then the 31-writer main if the pilot passes. Forecast: a few dollars.
2. **A first F4 slice.** The cloud transcriber on about 2,000 deduplicated CoAuthor texts, for questions that already passed local admission. Forecast: $5 to $15.

**Tranches B, C and D: $35 each, $105 in all.** Each unlocks only when a family produces a **major positive**, and only with the curator's explicit go. A major positive is all four of:
- promoted under the stopping rule: posterior probability above 0.975 of beating zero, passed through e-LOND;
- confirmed on all three locked holdouts (time, makers, second dataset);
- a confirmed effect at least twice the family's useful margin;
- the family's spike-in positive control recovered.

What each tranche buys is decided when it unlocks: more of F4, F10's API arms, or a cloud follow-up on the positive itself.

**So spend reaches about $150 only after three major positives.** With none, it stops at $44.52.

**Cost guards.**
- Every paid run states a forecast before submission.
- Hard stop at the tranche ceiling.
- No automatic retries or model substitutions.
- A run whose forecast exceeds its remaining tranche is split or refused.
- Forecasts are replaced by measured pilot costs as soon as they exist.

---

## Part 6. What the curator sees

- **After every batch:** the family's specification curve, with kills marked.
- **Every three days:** a one-page digest listing:
  - families alive, killed and inconclusive;
  - spike-in recovery per family (blind or seeing);
  - any promotion, with its e-LOND state.
- **At each family's end:** a theory-store afterword in the Confidence vocabulary, and a ToMpathy implication line (module admitted, killed or inconclusive).

---

## Part 7. Pre-mortem

| Failure | What it looks like | Guard |
|---|---|---|
| **Breadth without depth** | Thirteen families, eleven adapters, nothing finished | The stopping rule plus the order of work in Part 5. Each family needs an adapter that already exists or is built in its week. A family without a working adapter by its week waits rather than running half-built |
| **Weak looks like broken** | Every family inconclusive, and no way to tell a blind instrument from a weak world | Spike-in positive controls in every family (Part 0.3). A blind instrument is reported as blind |
| **Shared makers inflate confidence** | Families reuse the same 61 writers, so their results are correlated, and consecutive "independent" findings aren't | Makers as a crossed random effect; e-LOND for dependence; the second-dataset holdout |
| **Pretraining contamination** | LLM features "recognize" public data | Post-cutoff slices for LLM-feature families; statistical families are unaffected; cutoff gap recorded per card |
| **Dataset terms violated** | A derived artifact republishes licensed text or re-identifies people | Raw data local; aggregates only; per-dataset terms checklist before first use; F9 identification models never published |
| **Projection by design** | The engine's defaults leak into what counts as a maker's preference | Population and pooling first; prior-shift calibration; Ghost family N5 |
| **The old forest eats the new program** | Retained Stage 14 cards absorb compute | Repair R6's triage before launch |
| **Holdout overuse** | Repeated confirmation on one holdout overfits it | Three locked holdouts; confirmation needs all three |
| **Margins tuned after the fact** | *δ* drifts to make a family pass | Margins frozen per card before batch 1; Ghost-calibrated |

---

## Part 8. Decisions: resolved, and defaults in force

**Resolved (curator, 14 October, 20:00 PDT).**
1. **Stopping rule:** the pooled rule with a hard cap of seven.
2. **Gear 3:** Tranche A only. Tranches B to D unlock on major positives with the curator's go (Part 5).
3. **Engine pinning:** by ToMpathy commit.

**Defaults in force unless the curator overrides.**
4. **Prompt novelty:** report both versions.
   - **Prequential scoring over all decisions:** primary for engineering.
   - **The prompt-novel subset:** required for any claim.
5. **Dataset access:** request PANDORA, LAPIS and ArtEmis, and accept SWE-chat's terms, when their families come up. Nothing is requested before then.
6. **CoAuthor:** analysis proceeds. Before any public release of derived CoAuthor data, write to its authors.

## Sources

**Repository evidence:** Sounding Line `0a956219c` (FINDINGS: Stage 14 entries; the cloud-reader study report and aggregates; the midweek baselines code). Analyst results read: `RESULTS_AND_ENGINE_PLAN_2026-10-14.md`.

**Methods**
- [Jamieson & Talwalkar (2016), successive halving](https://proceedings.mlr.press/v51/jamieson16.html)
- [Li et al. (2018), Hyperband](https://jmlr.org/papers/v18/16-558.html)
- [Li et al. (2020), ASHA](https://arxiv.org/abs/1810.05934)
- [Ramdas et al. (2023), safe anytime-valid inference](https://arxiv.org/abs/2210.01948)
- [Howard et al. (2021), confidence sequences](https://arxiv.org/abs/1810.08240)
- [Javanmard & Montanari (2018), online FDR](https://arxiv.org/abs/1603.09000)
- [Xu & Ramdas, e-LOND](https://arxiv.org/abs/2311.06412)
- [Saville et al. (2014), predictive probability](https://pmc.ncbi.nlm.nih.gov/articles/PMC4247348)
- [Steegen et al. (2016), multiverse analysis](https://doi.org/10.1177/1745691616658637)
- [Simonsohn, Simmons & Nelson (2020), specification curve analysis](https://doi.org/10.1038/s41562-020-0912-z)
- [Milkman et al. (2021), megastudies](https://doi.org/10.1038/s41586-021-04128-4)
- [Gelman, Hill & Yajima (2012), multiple comparisons and partial pooling](https://arxiv.org/abs/0907.2478)
- [Silberzahn et al. (2018), many analysts](https://doi.org/10.1177/2515245917747646)
- [Russo (2020), top-two Thompson sampling](https://arxiv.org/abs/1602.08448)
- [Rainforth et al. (2024), Bayesian experimental design](https://arxiv.org/abs/2302.14545)
- [Dawid (1984), the prequential approach](https://www.cs.ubc.ca/~murphyk/MLRG/dawid84Prequential.pdf)
- [Saerens et al. (2002), prior adjustment](https://mlanthology.org/neco/2002/saerens2002neco-adjusting)
- [Yao et al. (2018), stacking](https://arxiv.org/abs/1704.02030)
- [Sorensen et al. (2025), value profiles](https://aclanthology.org/2025.emnlp-main.106)

**Datasets**
- [CoAuthor](https://coauthor.stanford.edu/)
- [Lichess database](https://database.lichess.org/)
- [Maia4All](https://openreview.net/forum?id=iw4kjcw319)
- [Maia-2](https://proceedings.neurips.cc/paper_files/paper/2024/hash/250190819ff1dda47cd23cecc0c5a69b-Abstract.html)
- [Wikipedia edit summaries research](https://meta.wikimedia.org/wiki/Research:Wikipedia_Edit_Types/Edit_Summaries)
- [Yang et al. (2017), edit intentions](https://aclanthology.org/D17-1213/)
- [Community Alignment](https://huggingface.co/datasets/facebook/community-alignment-dataset)
- [PRISM](https://huggingface.co/datasets/HannahRoseKirk/prism-alignment)
- [MovieLens Beliefs](https://grouplens.org/datasets/movielens/ml_belief_2024/)
- [MultiPref](https://huggingface.co/datasets/allenai/multipref)
- [DICES](https://github.com/google-research-datasets/dices-dataset)
- [summarize_from_feedback](https://huggingface.co/datasets/openai/summarize_from_feedback)
- [Persuasion for Good](https://convokit.cornell.edu/documentation/persuasionforgood.html)
- [PANDORA](https://psy.takelab.fer.hr/datasets/all/pandora/)
- [Jakesch et al. (2023)](https://arxiv.org/abs/2302.00560)
- [Williams-Ceci et al. (2026) data](https://zenodo.org/records/18048642)
- [SWE-chat](https://huggingface.co/datasets/SALT-NLP/SWE-chat)
- [HALIE](https://github.com/stanford-crfm/halie)
- [CS1 keystroke data (2019)](https://doi.org/10.7910/DVN/6BPCXN)
- [Project CodeNet](https://github.com/IBM/Project_CodeNet)
- [WildChat-4.8M](https://huggingface.co/datasets/allenai/WildChat-4.8M)
- [Hicke & Tomlinson (2026), WildChat skew](https://arxiv.org/abs/2605.29018)
- [DiffusionDB](https://huggingface.co/datasets/poloclub/diffusiondb)
- [Pick-a-Pic v2](https://huggingface.co/datasets/yuvalkirstain/pickapic_v2)
- [PARA](https://arxiv.org/abs/2203.16754)
- [LAPIS](https://arxiv.org/abs/2504.07670)
- [ArtEmis](https://www.artemisdataset.org/)
- [McIlroy-Young et al. (2021), chess stylometry](https://www.cs.toronto.edu/~ashton/pubs/chessembed-neurips2021.pdf)
