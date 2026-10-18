# Sounding Line mid-run errata, 18 October

18 October 2026. **For the Sounding Line agent, from the curator.** Handing this errata over is the curator's authorization for everything in it. It amends the 17 October packet (`PACKET_20261017_PUBLIC.md`) where it says so; everything else in that packet stays in force, including the Wednesday freeze, the paid cutoff and every stone rule. Record the curator's handoff message verbatim, with its date and this file's SHA-256. Nothing here waits on him.

**Why this exists.** Wave 1 landed seven instruments and nine cards between Saturday 13:40 and Sunday 02:15. Since then the CPU has been almost idle. The remaining cards aren't built, one packet rule deadlocked, and another counted two environmental stops as engineering failures. The results also changed what's worth running. The fake-writer controls on both pause cards came back as positive as the primaries, the writer-offset gain survived an outcome shuffle that keeps only base rates, and V4 showed that the fitted taste test raises false alarms in every null world. The rest of the campaign therefore leads with the question the screen can now answer: where, in a writer's logs, does the person show at all?

## 0. How to run this

1. **Apply the rule changes in section 1 now**, time-boxed to 45 minutes.
2. **Dispatch at once:**
   - **CPU:** D30.s's measured continuation; D17's resumed retry; P7-D33 (section 2.3).
   - **GPU:** the P1 suggestion pass, relaunched from its checkpoints as soon as rule 3's floor is met.
3. **Re-commission three builders** with the assignments in section 3, and freeze batch plan `BATCH_PLAN_20261018_W2` with section 2's card text as its body. Dispatch W2 in the order listed. The ranked remainder of the 17 October packet follows, in section 3's order.
4. **Unchanged:** the 20:00 digests, Tuesday's 18:00 talk page, new starts frozen Wednesday 06:00, and the drain by 12:00.

## 1. Rule changes

| # | Amends | Now | Why |
|---|---|---|---|
| 1 | Packet §2 row 12 (forecast yield) | A card whose projection passes twice its forecast yields only if a reviewed card is runnable and waiting for a slot at that moment; otherwise it continues at once, and OPS_LOG records the projection. A card whose whole projected run is under 2 CPU-hours never yields. A measured continuation needs no successor credits. **Apply now:** D30.s continues. The P7 full-corpus census is superseded by section 2.3; keep its checkpoints and don't resume it this campaign | The yield was meant to let waiting cards through. With nothing waiting, it stopped a 21-minute job after 36 seconds |
| 2 | Packet §2 row 9 (one retry) | An **environmental interruption** doesn't count as a failure. That means a memory or temperature guard tripping, an operating-system refusal (file lock, access denied), sleep, power loss or reboot, or disk exhaustion. Resume from validated checkpoints with unchanged inputs, comparators, seeds and contrast, with no new version, as often as the cause recurs. Each resume revalidates every checkpoint and pin and logs the cause with its evidence (the guard's sample, the error code). Scientific and engineering failures (non-convergence, failed known-answer tests, invalid data, code bugs) keep exactly one retry. **Apply now:** the P1 suggestion pass (both stops were guard trips: the second at 912 MiB free with other programs holding GPU memory, the first unrecorded) and D17 (its retry stopped on `WinError 5` before reaching the tested repair) | Neither stop was scientific; both have valid checkpoints. The rule exists to stop rescue by redesign, which a checkpoint resume isn't |
| 3 | GPU starts | A GPU job starts or is relaunched only when free memory is at least the 7,424 MiB cold-start floor and the temperature limit holds. The frozen runner exits when its guard trips; the owner relaunches it from checkpoints under rule 2 once the floor is met again, checking at each planned wake. Waiting is never a failure. The curator's own GPU use takes precedence | Keeps the safety guard and removes the failure path. At 02:45 free memory was 7,357 MiB, with about 4.6 GB held by other programs: 67 MiB under the floor |
| 4 | Packet §3.5, outcome-shuffle controls | Replace each single-draw outcome shuffle with at least 200 within-writer permutations (fixed seed 20261018). Report the primary's one-sided permutation p in its predicted direction, and the permutation distribution's mean, SD and 2.5% and 97.5% points. The daily negative-control check flags a card when its permutation mean lies more than 0.25 of its own SD from zero (a biased pipeline). The three constant-offset positive controls are unchanged. **Apply** to D30, D32 and D34 at the next digest, from saved designs | One shuffled draw is one sample from the null. D32's landed at almost exactly the primary's value; whether by chance or through a biased pipeline is what this check decides |
| 5 | Every writer-label or session-reassignment control | A fake-writer control runs on the **same rows** as its primary wherever the design allows: the same words or occurrences and the same covariates, with only the history, classification or offset rebuilt from reassigned sessions. Where a rebuilt classification leaves some rows unclassified (D30), pair on the rows classed under both labelings and report how many. Report own minus fake with a bootstrap that resamples real writers, taking each writer's rows from both arms together. That difference, not two separate states, carries any person-specific reading. **Apply** to D30, D30's extension and D33 as `.fake` re-analyses (section 2.6) | D33's fake-writer control ran on 86,490 words against the primary's 78,602; D30's on 13,459 occurrences against 71,038. Unpaired, "both positive" can't be compared |
| 6 | Packet §3.5, V5 headroom shares, and D37's report | Don't convert forecast gains on other populations into shares of V5's headroom, D37's included. Report V5 beside them, not as a denominator | P4's writer-offset model already sits at 0.2785 half-Brier, below V5's personal floor of 0.2891, so that floor doesn't bound other populations |
| 7 | Packet §7, Gear 3 | **K** stays authorized only if D31's intake and its known-answer rung can run before Monday 12:00 PDT; otherwise D31 and K move to the post-talk campaign. **P** and **A's first look** are dropped from this campaign; rewrite `.agent-state/drive-20261017/APPROVAL.json` to name only K. The paid cutoff is unchanged | Builder time is the bottleneck. A's content gain (P4) is marginal, so ruling 7 wouldn't extend it, and P's consumers sit low in the order below |

## 2. W2: new and revised cards

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

## 3. Builders, lanes and order

- **builder 1, menus and models:** V5.d, V4.c, D2's diagnostics (below), D4's predictive primary, D12 (within-menu rank of the logged score only, since P8's semantics are unresolved), D37, D2's extension (after V4.c).
- **D2's diagnostics,** before its extension: a model that does worse than uniform out of sample is miscalibrated or overfit, since position alone beats uniform in ranked lists. Fit position-only and length-only baselines on D2's exact splits; count menus whose options were filtered or truncated; report all three against uniform.
- **builder 2, timing and text:** PMAP, D33.pair and its variants, the `.fake` re-analyses, the P7-D33 scope change, the Jester ratings parser, D30.v2, D5, D16.
- **builder 3, corrections and events:** D3, D29, D24, D38, D18, D20, D23, D14.
- **owner:** section 1, the resumes (P1, D17, D30.s), the GPU lane, D31's intake if K can make Monday 12:00, landings and digests.
- **GPU lane:** the P1 suggestion pass relaunched, then P3's classifier, then P1 typed and history, then D10.
- **Dispatch order after W2:** D5, D36, D29, D3, D38, D24, D18, D20, D23, D4, D14, D12, D15, V3, D16, D37, D11, D19, D31, D28, D7, D9, D10.
  - D16 and D37 follow D15 and V3, which they need. If D17 hasn't landed by then, they run without its pause shares, using TC's intervals for timing.
  - The hover-based cards (D28, D7) move to the end, since D6 and D32's extension showed recorded hovers to be a weak and possibly biased proxy for examination.

## 4. Reporting

- **Digests** gain a person-specificity column: own minus fake, with its paired interval, wherever a card has one.
- **The talk page** (Tuesday 18:00) leads with PMAP's channel table, D33 and its pairs, V5.d and V4.c, each in plain words with its numbers.

## 5. Cross-repository

- **To Ghost,** at the first digest after each lands: V5.d's H_lean and H_context, for N13's habit-only matching; and PMAP's channel reliabilities.
- **To ToMpathy:**
  - PMAP's route;
  - D33.pair's route, which decides whether departures may be scored against a person's own history;
  - V4.c's label;
  - Sounding Line keeps ToMpathy pinned at `82789fd`, as in the packet.

## 6. Authorization

1. **Rules:** section 1, from handoff to the Wednesday freeze.
2. **Cards:** section 2 at Gear 2, descriptive, on data held.
3. **Gear 3:** K under rule 7. P and A's first look are dropped.
4. **Return triggers:** unchanged. Come back only with a past-$10 request or a stone rule blocking a required card; record it, skip the card and report it at the digest.

## 7. Pre-mortem

| Failure | Guard |
|---|---|
| Rule 2 becomes a way to rescue science | Only the listed environmental causes qualify, each logged with its evidence; scientific and engineering failures keep one retry |
| The GPU stays busy with the curator's own work | P7-D33 runs on CPU; the P1 relaunch waits rather than fails |
| PMAP "recognizes" writers by their prompts | Prompts stay inside one half, the style features are function words and punctuation, and the fake-writer null runs on the same sessions |
| Identification is high in every channel, so the primary says little | The channel table and fake-writer null are reported in full; the contrast is a ranking, not a claim that lean is absent |
| V4.c's quick look rests on 30 nulls | It's descriptive only; the split test and the predictive criterion carry the label |
| D33.pair's other history differs in size or topic | It's matched on sessions, tokens and prompt overlap; the prompt-excluded variant removes topic outright |
| New cards crowd out the ranked remainder | W2 is about 12 CPU-hours in total, most of it V4.c's split test; four slots clear it in an afternoon while the builders work on the remainder |
