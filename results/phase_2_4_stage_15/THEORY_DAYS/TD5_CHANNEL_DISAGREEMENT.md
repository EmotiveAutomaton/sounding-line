# TD5 complete comparison

**Hypothesis.** Do disagreements between independent raters preferentially substitute words assigned to the same proposed channel?

**METHOD.** Count exclusive-label disagreements over ordered distinct-rater pairs on each clear comment. Divide by the count expected from rating marginals, and compare each of six assigned pairs against its strongest supported cross-channel rival. Recompute marginals in 2,000 comment-cluster draws. Retain the full-data fixed competitor, add a maximum-reselected companion, compare unassigned categories separately, and repeat on exactly-three-rater comments. Exact scalar counts and an independent-label factorial null validate the arithmetic before human execution.

**Found.** The registered within-channel disagreement comparison remains inconclusive; its complete sensitivity check is limited in balanced constructed worlds and does not establish human-population power (S15-TD5-IC-SENSITIVITY-20261106).

The full primary contains 57,349 comments, 209,971 ratings and 607,458 ordered pairs. The exactly-three-rater companion contains 37,335 comments, 112,005 ratings and 224,010 ordered pairs. Both return the packet's inconclusive outcome: two cross-channel wins, two losses and two unresolved pairs. The against rule requires at least three losses; support requires all six wins. The frozen practical difference is 0.1 lift units in the declared direction.

Each row is a declared pair compared with its strongest cross-channel rival. Difference is within-pair lift minus rival lift. Brackets are 95% comment-bootstrap intervals, conditional on this corpus and annotation allocation; the second interval reselects the maximum within the same eligible competitor pool on each draw.

| Population | Pair | Fixed rival | Difference | Fixed interval | Reselected interval | Decision |
|---|---|---|---:|---|---|---|
| primary | anger / annoyance | anger / disgust | -0.0809312 | [-0.258341, 0.101728] | [-0.258341, 0.101728] | inconclusive |
| primary | fear / nervousness | nervousness / sadness | 2.76959 | [1.97824, 3.54409] | [1.93931, 3.47914] | win |
| primary | grief / sadness | nervousness / sadness | 2.89998 | [2.16741, 3.66237] | [2.16741, 3.66237] | win |
| primary | amusement / joy | excitement / joy | -0.116395 | [-0.324439, 0.0924209] | [-0.324439, 0.0924209] | inconclusive |
| primary | curiosity / excitement | excitement / joy | -1.3128 | [-1.50132, -1.12226] | [-1.50132, -1.12226] | loss |
| primary | caring / love | caring / nervousness | -1.01221 | [-1.29957, -0.735765] | [-1.30106, -0.871336] | loss |
| exactly_three | anger / annoyance | anger / disgust | 0.12683 | [-0.245979, 0.502482] | [-0.245979, 0.502482] | inconclusive |
| exactly_three | fear / nervousness | disgust / fear | 3.19955 | [1.66478, 4.8733] | [1.66478, 4.8733] | win |
| exactly_three | grief / sadness | fear / sadness | 3.94075 | [2.51851, 5.45196] | [2.48114, 5.41974] | win |
| exactly_three | amusement / joy | excitement / joy | -0.105813 | [-0.404167, 0.207809] | [-0.404167, 0.207809] | inconclusive |
| exactly_three | curiosity / excitement | excitement / joy | -1.35923 | [-1.63064, -1.07823] | [-1.63064, -1.07823] | loss |
| exactly_three | caring / love | joy / love | -0.954194 | [-1.12297, -0.781733] | [-1.12297, -0.781733] | loss |

Against unassigned categories, the full-data comparisons win for anger/annoyance and fear/nervousness, are unresolved for grief/sadness, and lose for amusement/joy, curiosity/excitement and caring/love. The exactly-three-rater comparison instead wins for amusement/joy. All unassigned estimates, intervals and expected counts are in the aggregate JSON receipt. These comparisons are separate because the theory treats unassigned categories as mixtures.

The six primary pairs include sparse within-channel expected counts even where their rival passes the 50-count floor. The packet applies that floor to competitors, not to the within-channel pair. A reselected maximum bootstrap is a sensitivity calculation, not guaranteed valid post-selection inference near tied maxima. The comment bootstrap holds the observed rater pool fixed and does not estimate generalization to new raters. The original arithmetic null checks did not establish power. The complete first-generation calibration now shows limited full-rule sensitivity and poor interval coverage under its balanced single-label construction (S15-TD5-IC-SENSITIVITY-20261106), without establishing human-population power. This inconclusive human result is not evidence of channel equivalence or absence. Everyday emotion labels need not identify inherited functions.

**Means.** Keep the mixed pair pattern and the aggregate inconclusive outcome. Retain the completed instrument sensitivity check and its construction limits; do not tune the mappings after these outcomes.


Design commit: `abeee0d8b773fd223bd17771438571698e2ec423`. Complete execution and independent replay used 65.515625 CPU seconds. All pinned sources, output hashes and native exits verify. No p-value is added. Raw text and identities remain private.
