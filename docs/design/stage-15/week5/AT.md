# AT — writer timing and the engine's attention marks

Prospective implementation of [Week 5 packet](PACKET.md) §2.1. This family is
CPU-only, two numerical threads, no paid calls, no GPU and no Ollama. Its total
ceiling is 750,000 CPU-seconds. Timing/pilot/source/verification costs belong to
the same card, without internal reservations. A model-scoring batch yields
after at most 1,500 seconds of work, retaining immutable word checkpoints.

## Source and estimand

The canonical P6 recovery contains all 1,399 CoAuthor sessions and the complete
production ledger, including occurrences later deleted or modified. The Week 4
timing ruler supplies mechanically corrected per-writer fluent posteriors.
Production identity is exact inserted-character provenance, never spelling.
All source bytes and completion receipts are authenticated before preparation.

A final-document prefix exists only for exact surviving production occurrences.
Deleted or modified occurrences remain in the exposure census and at-typing
bank; they are explicitly unsupported in the final-text contrast. No final
position or pause is borrowed from a repeated/reinserted spelling. Final-text
results therefore describe exact survivors, with the population and supported
counts reported. The at-typing context covers all mapped production occurrences.
The corpus retains prompt/model text as context while only human-produced words
are scored. Onsets without supported timing posteriors or a positive logged
interval are counted and excluded from timing fits, never assigned a fake pause.

The final text is reconstructed by UTF-16 edit replay. At-typing context is the
complete visible prefix at the occurrence's completion event, as in P7. Each
model scores the native tokens overlapping the word: surprisal is their summed
negative log probability; entropy is the predictive entropy at its first token.
A boundary-overlapping subword retains P7's overlap convention. Each context
has an explicit BOS/EOS starter and is left-cropped to the declared token cap.
CPU float32 cache reuse backs off one token, so each new transition is scored.
The fresh verifier reconstructs a seeded 2% of all forwards (at least one per
batch), comparing both token losses and entropy within 1e-4 nats, and checks
all retained IDs, crops, hashes and reductions. Every downstream fit is replayed.

The ten causal models, in initial scoring order, are GPT-2 medium, GPT-2,
GPT-2 large, Pythia 70m/160m/410m/1b/1.4b deduped, SmolLM2-360M and Qwen2.5-0.5B.
The model revision, file hashes, model-card licence, packages and CPU precision
are retained with each model bank. The packet's cache fallback uses the named
non-deduped cached Pythia variants explicitly labelled; it never silently calls
them deduped. P6's frozen leave-writer-out three-gram is the baseline.

Final-prefix scoring runs first for every model. The fixed 20% at-typing sample
is ceil(0.2 × sessions), sampled without replacement from the sorted session
roster with seed 20261107, before model/timing outcomes. Remaining at-typing
sessions run only for the selected AT2 model and both engine models. Preparation
has a declared 3 GiB peak; scoring declares at least model float32 bytes plus
2 GiB activation/runtime reserve (specific plans may declare higher measured
peaks). Chunk files and all text, IDs and individual scores remain ignored.

## Cards, frozen comparisons and routing

| Card | Primary and practical bar | Model and uncertainty | CPU ceiling |
|---|---|---|---:|
| AT1 | own minus donor history coefficient; +0.01 per nat | D33 joint writer-random-intercept model; 2,000 writer-cluster refits with newly drawn equal-budget donor sets | 40,000 |
| AT2 | better engine model's held-out Gaussian log-likelihood gain over P6; +0.002 nats/word | five writer-disjoint folds; paired 2,000 writer resamples; best-of-two selection repeated inside each bootstrap draw | 550,000 |
| AT3 | entropy coefficient controlling chosen-word surprisal; +0.01 per nat | same timing controls; writer-cluster refits; surprisal coefficient secondary | 30,000 |
| AT4 | final-text full minus baseline stop-prediction AUC; +0.02 | five writer-disjoint folds; writer-cluster interval; fluent posterior below 0.5 defines stop | 30,000 |

AT1 preserves D33's population surprise, word length, frequency, sentence start,
punctuation, on-screen reuse and session surprise controls, with prompt excluded
from histories. Five distinct same-genre donors are pooled and then trimmed to
the recipient's exact supported history-session and token budget. Each resample
draws new donor sets per sampled writer; a set without term support is redrawn
at most twenty times. Exhaustion invalidates that draw and suppresses inferential
classification: successful draws are never silently substituted. All redraw and
exhaustion counts are recorded. Its 20-writer floor has a pooled descriptive
fallback. Topical reuse remains a rival, not a resolved causal explanation.

AT2's nuisance features are length, log frequency, sentence/paragraph boundaries,
position and the Week 4 timing controls available for the exact row. Training
statistics and coefficients are learned using training writers only. A held-out
writer contributes no fitted identity intercept; within-writer demeaning is
reported only as a secondary diagnostic because demeaning with held-out pauses
would leak their outcomes. Gaussian noise variance is estimated on training
residuals, never on the evaluation fold. Paired differences use the same rows
for all compared models; missing scores remain a source-support exclusion.
The primary's best-of-two bootstrap accounts for its selection as a descriptive
maximum; no simultaneous or confirmatory significance claim is made. Other
models and model-size curves are secondary, with pairwise score correlations.
Below forty writers a pooled descriptive fit runs. AT2 selects the best final-
context model by held-out mean gain, lexicographic model ID as a deterministic
tie-break. AT3, AT4, GO1's model reader and LA1's surprise await the complete
selected-model receipt and never select using an unfinished score bank.

AT3 reports variance inflation and the residualized-entropy texture. Both
coefficients are included, but only entropy is primary. AT4's baseline uses
length, frequency, boundaries and position; its full model adds selected-model
surprisal and entropy. All classifier standardization and fitting are confined
to training writers. AUC is undefined in a one-class evaluation population and
is retained as unsupported, not replaced by 0.5. The engine's pinned exact
departure function is a separately labelled secondary and cannot inherit the
language model's accuracy or license an engine change by proxy.

## Declared grid and descendants

- AT1: k=1,3,20; matching genre/random/same prompt; hesitancy/log pause/stop;
  genre splits; prompt included. If personal, vocabulary-cache versus bigram
  AT1.p; if shared, genre-adapted population AT1.s.
- AT2: final/at-typing; context 64/256/1,024 tokens; genre; pause measure.
  If either engine model is worse than the selected model beyond the bar,
  score the exact certified-fit-1 (`5f3ad0a`) departure function in AT2.e.
- AT3: every completed AT2 model; genre; sentence-start/inside; residualized
  entropy. AT4: genre; fluent thresholds 0.3/0.7; each engine model alone.

Every declared cell retains the family estimator and support census. Texture
uses 200 cluster resamples, primaries and any supported/against ledger entry
2,000. Rescoring cells take at most a quarter of their parent's ceiling;
other texture cells at most 3,600 CPU seconds. A forecast above 7,200 CPU
seconds triggers the first 5% checkpointed in-slot pilot. Seven consecutive
texture point estimates inside the parent's ±bar stop the lane; primary family
stopping remains the packet's six-null rule. Sample/doubling/family-continuation
rules are Week 5 amendments L and M, not the old D33 sub-allocation.

## DESIGN CHECK

Read LESSONS §3–§5 and CONTROLS §1–§6; relevant theory: THE_TRIPLE_INFERENCE
opening/order/bounds and DECISION_TRACES §6 pauses, information and revision.
Pauses are mixed motor/planning signals; model surprise is not attention by
definition. These tests are descriptive associations/predictions, not causal
attention or devotion measures.

Known-answer fixtures must retain exact occurrence identity after deletion,
repetition and UTF-16 characters; cache and direct loss/entropy must agree in
prefix extension, shortening, divergence and context rollover. Under the null,
paired gains and independently planted null coefficient differences are near
zero; positive and reversed plants recover their signs. Identical prediction
arrays yield exact zero difference and the practical-zero classification.
Train/test writer overlap, nonfinite values, missing forwards, changed hashes,
undefined focal coefficients and incomplete banks refuse a completed claim.
All three outcome bands are exhaustive: interval entirely above +bar supports;
entirely below zero or inside ±bar is against; otherwise inconclusive. Below-
floor fits remain explicitly descriptive and do not silently become nulls.
