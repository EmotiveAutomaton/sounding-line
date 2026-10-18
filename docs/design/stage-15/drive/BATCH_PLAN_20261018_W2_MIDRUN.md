# October 18 mid-run W2 amendment

The curator's supplied mid-run errata is operative. The earlier
`BATCH_PLAN_20261018_W2.md` already pins live/completed work; its bytes stay frozen.
This distinct amendment carries the new section 2 verbatim below. Exact source
and handoff: `SOUNDING_LINE_MIDRUN_ERRATA_2026-10-18.md` and `MIDRUN_HANDOFF_20261018.json`.

DESIGN CHECK: LESSONS sections 3-5 reread October 18. Every scientific measure
must pass signed/planted and null controls before observed inference. Same-row
fake controls and real-writer paired bootstrap protect comparisons; 200 or more
within-writer permutations use seed20261018. Missing evidence is blocked/invalid,
never a negative result. Original frozen results and labels remain retained.

## Implementation review

- The idle-state description in the supplied source is historical. D30.s is
  already verified complete and is not rerun. Existing independent workers continue.
- Environmental interruptions may resume the unchanged study. Each execution
  gets a separate operational receipt so original failures, plan and checkpoints
  are retained. This is not a new scientific version. Engineering failures still
  have one retry. D3 and its content companion have exhausted that retry.
- New supervision uses `batch_runtime_v3`; old pinned supervision is immutable.
  Forecast yields require a fresh reviewed runnable waiting card and never occur
  below two projected CPU-hours. Resource guards and cumulative caps remain.
- P7 full-corpus census is superseded; only the scoped D33/Jester pass is admitted.
  The cited word-probability paper's equation25 includes the ratio of boundary
  mass after and before a word, including EOS. Trailing mass alone is insufficient.
  The scorer must establish a common event with the word cache, including case,
  punctuation and whitespace; no unreviewed row exclusions or changed estimand.
  Source read: https://arxiv.org/html/2406.14561v1 (Theorem2 and section5.4).
- V5.d reports literal endpoint-marginal Cohen kappa and the requested pooled-mix
  adjustment separately. Its matched-pair weighted primary is distinct from the
  balanced pure-lean algebraic identity. Across-writer global decision counts are
  descriptive only, not a personal intervening sequence.
- Shared style features are the specified 100 most frequent typed words plus
  punctuation; the pre-mortem's shorthand does not make this a curated function-word list.
- V4.c split averaging needs its own known-null calibration; splitting alone does
  not prove the proposed reference is calibrated. Original V4 labels stay unchanged.
- A newly discovered prepared selected-index/insertion mismatch places affected
  completed comparisons and their follow-ups under source audit. Actual inserted
  text is the validation reference. No frozen result is silently repaired.
- Gear3 is K only, contingent on D31 intake/known-answer readiness before Monday
  noon PDT; P and A-first-look are dropped. Existing first-$10 and K $5 ceilings,
  Monday17:00 cutoff, Wednesday freeze/drain, and20:00 digests remain.

## Frozen supplied card text


Defaults from the 17 October packet hold: one primary contrast with its direction, initial sample, controls, and at most one frozen extension; writer-cluster 95% intervals with 2,000 resamples; descriptive only. Cards here that list no extension have none. Every fake-writer control follows rule 5, and every outcome shuffle follows rule 4.

**Families, for the null counters:** PMAP counts in E, D33.pair and D33.fake in A, D30.v2 and D30.fake in K (D30.v2 counts in K's ladder as usual, though it runs early). V5.d and V4.c are Tier 0 instruments and don't count.

**One word list for all style features:** the 100 most frequent words in all writer-typed text in the corpus (the most-frequent-words convention of stylometry), plus the punctuation marks. PMAP's style channel and D30.v2 both use it.

### 2.1 PMAP. Where the person shows (new, W2 rank 1)

**Question.** In which channels of the logs can a writer be recognized as herself, beyond what any writer on the same prompts shares?

**Channels,** each a per-writer profile computed separately on two halves of her sessions:
- **a. lean:** her rates of each handling class;
- **b. style:** relative frequencies of the shared word list's words and punctuation marks in her own typed text (stylometry's standard features; [Kestemont 2014](https://doi.org/10.3115/v1/W14-0908));
- **c. rhythm:** her median within-word interval, median word-onset interval, and median latency for the 20 most common character bigrams, from TC's logged intervals;
- **d. revision:** content and housekeeping edits per 100 typed words, and the share of accepted suggestion characters she later edits;
- **e. requests:** suggestion requests per 100 typed words;
- **f. length:** final document length relative to the prompt's median;
- **g. content taste:** the mean MiniLM vector of suggestions she accepts minus those she declines.

**Split.** Order her prompts by the start of their first session and assign whole prompts alternately to halves A and B, so every session on a prompt sits in one half and prompt vocabulary can't pose as style. Eligible writers have at least 4 sessions on at least 2 prompts.

**Measures, per channel:**
- writer identification from half A's profile to half B's, by nearest neighbour on standardized profiles (rank-1 accuracy, chance 1/n). The gallery is every eligible writer's half-B profile, held fixed; the bootstrap resamples the probe writers only;
- split-half reliability of each feature (Spearman-Brown corrected).

**Primary contrast:** identification accuracy from style (b) minus from lean (a). Direction: positive. The prediction is that a person shows in what she produces more than in how she handles offers.

**Extension:** rhythm (c) minus lean (a).

**Controls:**
- 200 session reassignments to fake writers, recomputing every channel on the same sessions;
- a known-answer check: identification from a duplicated session is 100%;
- the prompt-balanced split above.

**Report:** the full channel table, with real against fake identification and reliability for each channel.

**Route:**
- **Positive:** the theory's person entry reads production (style and rhythm), not selection. ToMpathy's person entry gets its first measured anchor.
- **Null:** the person shows no more in production than in handling on this corpus.
- **Channel g at chance while a and b aren't:** taste isn't recognizable with our representation, consistent with V4.

**Cost:** under 1 CPU-hour. **Data:** P2, P5, TC, CONTENT_V2.

### 2.2 D33.pair. Own history against matched other history (new, W2 rank 2)

**Question.** Does her own history predict which words come fast, beyond an equally sized history from someone else?

**Design:**
- D33's primary rows exactly: 78,602 words, 41 writers, the same covariates.
- **Add a second personal-surprise term** built from one other writer's sessions completed before the target session. Match it on the number of sessions and typed tokens, and on prompt overlap where possible. The history weight is tuned on the same calibration sessions.
- **Add two covariates** that any reader of the screen would share: whether the word is on screen (in the prompt, in her earlier text this session, or in any suggestion shown earlier this session), and its surprisal under a cache of the current session's earlier text. Repeated words are produced faster whoever said them first, and the advantage of one's own earlier mention fades within seconds ([Bard et al. 2000](https://doi.org/10.1006/jmla.1999.2667); [Trón 2008](https://aclanthology.org/L08-1532)).

**Primary:** the own-history coefficient with the matched-other term in the model. Direction: positive. Extension: none.

**Variant D33.pair2:** both caches restricted to sessions on prompts other than the target session's, which removes topic vocabulary. Same primary.

**Controls:** 200 within-writer permutations of own-history surprise.

**Route:**
- **Own coefficient positive with the other term in the model:** personal fluency, so ToMpathy may score departures against a person's own history where it has one.
- **Only the shared term:** fluency comes from shared history.
- **Both vanish under prompt exclusion:** it was topic vocabulary.

**Cost:** under 1 CPU-hour.

### 2.3 P7-D33. GPT-2 medium on CPU, scoped (amends P7)

- **Admission:** this errata admits P7-D33 at the scope below. Full-corpus P7 isn't needed this campaign, and its census stays paused.
- **Scope:** score only the calibration and evaluation sessions of D33's 41 writers, in their native visible contexts, plus the 150 Jester jokes.
- **Scorer:** the CPU scorer with the cross-group cache, validated against the scalar pilot on all 612 pilot targets (`P7-hybrid-pilot.md`). Its full-corpus extrapolation is about 4 hours, so this scope should take under 2. If its first tenth projects past 4 hours, it continues anyway under rule 1, logging the projection. A GPU run needs a parity check on the same 612 targets first.
- **Word probabilities:** a word's GPT-2 probability is the product of its tokens' probabilities times the probability that the next token starts a new word, the trailing-boundary correction ([Pimentel & Meister 2024](https://arxiv.org/abs/2406.14561)). That makes it a probability of the same event the cache predicts, which is what the pilot's warning against mixing token overlap with a word distribution asks for.
- **Then:** D33's frozen extension runs with that word probability as the population baseline, and D33.pair repeats on that baseline as **D33.pair-g**.
- **D36** runs once builder 2's Jester ratings parser lands.

### 2.4 V5.d. Lean against context (new, W2 rank 3)

**Question.** How much of V5's personal headroom is just her base rates?

**Method,** on V5's saved pairs at each cutoff:
- For a within-writer pair, the agreement her base rates alone predict is Σ over classes of her class rate squared.
- For a cross-writer pair, it's Σ over classes of the two writers' rates multiplied together.
- Rates are estimated leaving out both decisions of the pair.
- **H_lean** is half the difference of those two expectations. **H_context = H − H_lean.** Under a pure lean, within minus between agreement equals the between-writer variance of the class rates, summed over classes; report that check.
- **Chance and kappa.** Report each agreement against the pair sample's own pooled class mix, as Cohen's kappa. Corpus-wide, two random decisions agree about 41% of the time (the population forecast's half-Brier of 0.294 implies it), so the raw 42% and 36% can't be read without it.
- **Time, not session.** Report agreement as a function of the time between the paired decisions and the number of decisions between them, within and across sessions. In repeated choices, consistency falls with the time between repeats, and the session boundary adds nothing once that's modeled ([Spicer, Mullett & Sanborn 2024](https://doi.org/10.1017/jdm.2023.41)).
- The same-session agreement gets the same decomposition.

**Primary:** H_context at cutoff 0.8. Direction: positive. Writer bootstrap as in V5. Extension: none.

**Route:**
- **H_context near zero** (upper bound below 0.005): in handling, the person is a lean. ToMpathy's personal claims stay off handling.
- **Positive:** situation-specific consistency exists beyond the lean, and it's the target for any personal handling reader.

**Cost:** minutes.

### 2.5 V4.c. A calibrated existence test (new, W2 rank 4)

**Why the frozen test most likely failed.** V4 didn't isolate the cause, but its design explains it. The taste directions were estimated from the same outcomes they were tested on, and with no taste present they aren't defined at all. The statistic is then a maximum over directions, not a chi-square with K degrees of freedom ([Davies 1987](https://doi.org/10.1093/biomet/74.1.33); [Kriegeskorte et al. 2009](https://doi.org/10.1038/nn.2303)). A stylized simulation (61 writers, 250 decisions each, no taste) reproduces the failure:
- a fixed direction rejects about 5% at the 5% level;
- the best direction chosen from the same data rejects 60% at 4 dimensions and essentially always from 8 dimensions up;
- choosing the direction on half of each writer's decisions and testing on the other half rejects about 5%.

The variance boundary that the packet's reference handled makes chi-square references too cautious, not too permissive, so it isn't the cause.

**Steps, in order:**
- **a. Quick look, on saved statistics.** Each reader has 50 saved null statistics: 10 zero-effect worlds in each of the three plant families, plus 20 identity-shuffled worlds. Use their 95th percentile as a threshold, and re-read detection at 0.2, 0.4 and 0.8. Descriptive only.
- **b. Split test, the primary.** In every saved world, split each writer's decisions into two halves (alternate decisions within each session). Learn the directions, K and the shrinkage on one half. Test the writer-specific variance along those frozen directions on the other half, swap, and average the two statistics. Refer the result to a simulated chi-bar-square, as the packet did for one variance. Run it on all 110 saved worlds (the 90 calibration worlds and the 20 shuffled nulls), for R-taste, R-both and R-kernel. Cost: about V4's own, near 8 CPU-hours across two slots.
- **c. Predictive criterion, on saved outputs.** A writer-level structure exists in a world when its held-out half-Brier gain has a writer-bootstrap lower bound above 0. Re-read every saved cell.
- **d. Overlap.** For each arm, regress the planted feature on the reader's features and report the R² beside each cell. It should predict the gain: a linear reader can learn only the part of a taste that lies along its own features ([White 1982](https://www.jstor.org/stable/1912526)).
- **e. Monte Carlo reference, if slots free up after W2.** For R-both only, simulate 199 null data sets from the fitted no-taste model, keeping writer intercepts, habit and menu structure, and rerun the whole pipeline on each. The p-value is one plus the number of null statistics at least as large as the observed one, divided by 200 ([Dufour 2006](https://doi.org/10.1016/j.jeconom.2005.06.007)).
- **f. Check.** Report whether the frozen likelihood ratio plugs in fitted writer loadings. If it does, its effective degrees of freedom exceed K.

**Primary contrast:** R-both's split-test detection share at strength 0.4 minus at 0, in the matched-representation arm. Direction: positive. Reported beside it: the same for lexical taste and habit, and for R-taste and R-kernel. Extension: none.

**States:** V4's bands, applied to the split test. The habit reader isn't shown calibrated either: 2 of 10 and 2 of 20 false alarms have upper 95% bounds near 56% and 32%. Step (b) covers it.

**Labels.** V4's frozen labels and route stay exactly as recorded. V4.c is a separate card with its own label, which INDEX shows beside V4's.

**Route:**
- **A calibrated reader sees matched-coordinate taste at 0.4:** V4.c's label is "sees taste only in its own coordinates", and step (d) says how far that falls when coordinates differ.
- **Still blind under the split test:** V4.c's label is blind too. Seeing personal taste would then need more decisions per writer, or reader features that span the taste.

D2's hierarchical extension and any later writer-level taste card run only after V4.c, and use whichever test V4.c calibrates.

### 2.6 Paired re-analyses (rule 5)

- **D30.fake and D30-extension.fake:** the primary's 71,038 occurrences, with marker classes rebuilt for fake writers. Pair on the occurrences classed pervasive or local under both labelings, report how many there are, and report own minus fake on them.
- **D33.fake:** the primary's 78,602 words and its writers' calibration sessions. Each target session's history is rebuilt from the earlier sessions of its reassigned group, matched in number, and the fake history's weight is tuned exactly as the own weight was, on the same calibration sessions. Report own minus fake.

Both run on saved designs, under rule 5's bootstrap.

### 2.7 D30.v2 now (amends the ladder)

Run D30.v2 (the shared word list and punctuation only) as a specificity test now, not after a null, with its fake-writer control paired under rule 5. If the local-against-pervasive gap survives inside one word class and survives pairing, word type isn't the explanation.

Split D30's revision secondary, in D30.v2 and the `.fake` re-analyses, into immediate corrections (a deletion inside the same typing burst, before the next pause of 2 seconds or more) and later edits. Fast typing makes slips, which typists fix at once; only later edits bear on attention catching a habit.

