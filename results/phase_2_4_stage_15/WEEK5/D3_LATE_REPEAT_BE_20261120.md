# D3 LATE REPEAT BE 20261120

**Question.** Does a player’s best previous ending predict choices in a later play better than either the starting score or the previous ending?

**Method.** Amendment BE replaced the in-sample repeat-choice fit with one frozen late-play split. Each player contributed all 30 trials of the last eligible repeat to testing and at least two earlier eligible repeat plays to training. The three models shared eight slopes and one intercept for each informative training player. Each play’s references came from completed earlier attempts. The previous ending required an actual recorded immediately preceding attempt. The best ending used observed earlier completed endings. All models used the original eight choice predictors, forgetting factor 0.65 and the original first-play scale. Choices within a play used trial history available at that time. The score summed the 30 held-out log likelihoods. Each pair was averaged over test plays with unequal references and over all scored test plays. All comparisons used the same 2,000 paired whole-player bootstrap draws, conditional on the training fits. Each primary interval had to be above zero on at least 100 differing players. Fresh replay independently solved the intercept score equations and recomputed all draw cells.

**Found.** The best previous ending outpredicted the starting score. Its advantage over the last ending was inconclusive. The joint prediction is inconclusive.

*Values are increases in held-out log likelihood per play, with paired 95% intervals. Positive favors the first reference named.*

| Comparison | Equal / different, eligible | Equal / different, scored | Different references | All scored plays |
|---|---:|---:|---:|---:|
| Best minus start | 2 / 3,651 | 2 / 3,629 | 0.017182 [0.004378, 0.029798] | 0.017202 [0.004414, 0.029805] |
| Best minus last | 911 / 2,742 | 905 / 2,726 | 0.006436 [-0.012755, 0.025224] | 0.006078 [-0.008403, 0.020251] |
| Last minus start | 12 / 3,641 | 12 / 3,619 | 0.011403 [-0.003840, 0.027057] | 0.011124 [-0.004166, 0.026653] |

**Eligibility.** The repaired Rutledge Great Brain Experiment archive contained 47,067 represented players and 91,046 saved plays. Before any reward or choice was read for the model, the split excluded 42,458 players with too few recorded repeats, 951 who had enough recorded repeats but too few eligible earlier histories, and 5 whose source histories were ambiguous or incomplete. This left 3,653 test plays and 20,268 earlier training plays. Across the roster, 10,900 repeat records lacked their immediately preceding attempt. Included histories contained 6,643 unrecorded attempts across 3,344 gaps. The best reference therefore means best observed earlier ending. A further 22 eligible players always made the same choice in training. Their intercepts could not be estimated. All three models scored the same 3,631 people and had 3,639 free parameters each.

**Meaning.** The test is each player’s latest eligible repeat play and speaks to late plays. A game score is not anyone’s meaning. Conditional prediction in these people leaves open generalization to earlier plays, unobserved personal high scores and other populations. This comparison cannot establish equality of reference models or a mechanism of subjective meaning. The single prospective split was retained throughout.

**Verification and cost.** Seven counted constructed checks passed. The native completion authenticated 175 files. Independent execution and replay retained every paired draw. The study used 24 native CPU seconds, 4.21875 CPU seconds of preparation and the ordinary 30-second coordination charge. All fall within the 10,000 CPU-second card ceiling. The signed results, figure, counts and native hashes are filed with this record.

[Result sheet](D3_LATE_REPEAT_BE_20261120_SHEET.md) · [Signed figure](D3_LATE_REPEAT_BE_20261120.png) · [Figure values](D3_LATE_REPEAT_BE_20261120_CELLS.csv) · [Frozen design](../../../docs/design/stage-15/week6/D3_REFERENCE_20261120.md).
