# LA4 COMPLETE 20261113

**Hypothesis.** Are people who share a native language with the person starting a laugh more likely to join it, after accounting for the laugh itself, the individual participant within the meeting, and recent speaking and laughter? Shared background is a proxy for what people might infer together; joining does not directly measure a hidden inference or a channel firing.

**METHOD.** Use the qualified AMI and ICSI human meeting annotations and completed metadata extension. A starter begins after at least three seconds without a laugh; tied distinct starters are excluded and counted. Every other person on the source roster is a possible joiner, with an annotated onset in the next one second defining joining. Fit the preregistered linear probability comparison with laugh and person-within-meeting fixed effects and the frozen situational controls. The sole primary is AMI shared native language, with a two-percentage-point practical threshold. Retain 2,000 whole-meeting resamples, stratified by corpus and paired across variants, plus twenty within-meeting background-label permutations for each declared construct. Reconstruct the complete source features and inference in a fresh process, compare the final result bytes, and authenticate every sealed output and predecessor checkpoint.

**Found.** The shared-native-language association with joining laughter is inconclusive at the preregistered practical threshold; the completed meeting comparison does not establish a shared-inference mechanism.

**Sensitivity first.** This run sees differences of about 5.80 percentage points, compared with the two-point threshold; the approximate effect needed for an interval wholly above that threshold is 7.80 points. These are the preregistered 2.8-standard-error approximations, not a new power campaign. The observed primary is +0.2444 percentage points, with a 95% whole-meeting interval from −3.9082 to +4.1886 points. Its bootstrap standard error is 2.0706 points. The interval neither establishes the proposed positive effect nor confines it to the practical-null band. It is inconclusive, not evidence of equivalence or absence.

**Primary support and selection.** The eligible primary comprises 15,381 possible-joiner observations across 5,226 laugh events and 131 meetings. Another 6,848 roster observations lack the required background label or are unavailable for that specification. Seven simultaneous-starter events are excluded by the frozen rule. Roster membership is not continuous observed attendance; that limitation applies to all denominators. Meeting clustering preserves within-meeting dependence but does not establish independence of repeated global people across meetings.

Table: complete fitted coefficients. Estimates and intervals are percentage-point differences in joining probability; each row's meeting count is its independent-cluster support. The role codes are the source's task-role labels, relative to its reference role, not psychological constructs. Only the primary shared-language row carries the commissioned theory contrast. All other rows are descriptive or scale reports. “Cannot test” retains a point estimate when available but refuses population uncertainty when a target is absorbed or any required bootstrap draw is unsupported; draws are neither omitted nor redrawn.

| Variant | Term | Meetings | Estimate, points | 95% interval, points | Standing |
|---|---|---:|---:|---|---|
| AMI primary: person and laugh effects | Recent laugh count | 131 | 0.2438 | [-0.3030, 0.8039] | descriptive texture |
| AMI primary: person and laugh effects | Shared native language | 131 | 0.2444 | [-3.9082, 4.1886] | Inconclusive primary |
| AMI primary: person and laugh effects | Joiner spoke preceding line | 131 | -5.6520 | [-7.3713, -3.9239] | descriptive texture |
| AMI primary: person and laugh effects | Joiner spoke recently | 131 | 1.2827 | [-0.0289, 2.6635] | descriptive texture |
| AMI: starter did not speak preceding line | Recent laugh count | 131 | 0.3371 | [-0.3054, 0.9982] | descriptive texture |
| AMI: starter did not speak preceding line | Shared native language | 131 | 0.7641 | [-3.6739, 5.2772] | descriptive texture |
| AMI: starter did not speak preceding line | Joiner spoke preceding line | 131 | -4.9708 | [-7.0027, -3.1017] | descriptive texture |
| AMI: starter did not speak preceding line | Joiner spoke recently | 131 | 0.4804 | [-1.3389, 2.4541] | descriptive texture |
| AMI task roles with situational controls | Recent laugh count | 98 | 2.3280 | [1.5035, 3.0229] | scale only |
| AMI task roles with situational controls | Source role me | 98 | -3.1309 | [-5.5674, -0.9947] | scale only |
| AMI task roles with situational controls | Source role pm | 98 | -3.7765 | [-6.3833, -1.2668] | scale only |
| AMI task roles with situational controls | Source role ui | 98 | -1.8301 | [-3.9886, 0.1601] | scale only |
| AMI task roles with situational controls | Shared native language | 98 | 4.6378 | [1.9778, 7.5606] | scale only |
| AMI task roles with situational controls | Joiner spoke preceding line | 98 | -5.9510 | [-7.7176, -4.2664] | scale only |
| AMI task roles with situational controls | Joiner spoke recently | 98 | 1.5970 | [0.0172, 3.1552] | scale only |
| AMI task roles without situational controls | Source role me | 98 | -3.8757 | [-6.5465, -1.5211] | scale only |
| AMI task roles without situational controls | Source role pm | 98 | -4.4866 | [-7.2729, -1.7110] | scale only |
| AMI task roles without situational controls | Source role ui | 98 | -2.4000 | [-4.6924, -0.1472] | scale only |
| AMI task roles without situational controls | Shared native language | 98 | 5.8950 | [2.7220, 9.0612] | scale only |
| AMI: starter spoke preceding line | Recent laugh count | 99 | -0.4806 | [-1.5463, 0.5293] | descriptive texture |
| AMI: starter spoke preceding line | Shared native language | 99 | -0.0761 | Unavailable | Cannot test |
| AMI: starter spoke preceding line | Joiner spoke preceding line | 99 | 4.2876 | [-17.3992, 27.9456] | descriptive texture |
| AMI: starter spoke preceding line | Joiner spoke recently | 99 | 2.8447 | [1.0347, 4.6676] | descriptive texture |
| ICSI English variety | Recent laugh count | 72 | 0.0796 | [-1.7183, 1.6979] | descriptive texture |
| ICSI English variety | Shared English variety | 72 | -1.1607 | Unavailable | Cannot test |
| ICSI English variety | Joiner spoke preceding line | 72 | -4.4052 | [-7.5471, -1.0179] | descriptive texture |
| ICSI English variety | Joiner spoke recently | 72 | 3.9626 | [2.4955, 5.4764] | descriptive texture |
| ICSI region | Recent laugh count | 57 | 2.0215 | [-0.5982, 4.7042] | descriptive texture |
| ICSI region | Shared region | 57 | 0.8583 | Unavailable | Cannot test |
| ICSI region | Joiner spoke preceding line | 57 | -8.4651 | Unavailable | Cannot test |
| ICSI region | Joiner spoke recently | 57 | 7.8761 | [0.0000, 14.8141] | descriptive texture |

**Secondary limits.** ICSI English-variety and region targets and the AMI starter-spoke background stratum have unsupported resamples and no inferential intervals. ICSI earlier co-attendance remains source-held because documentary chronology or global identity is missing. The starter-spoke main effect itself is constant within each laugh and therefore absorbed by the mandatory laugh fixed effect; it is not estimated. The role-based comparisons replace person effects and use 98 meetings, so their larger shared-language associations do not upgrade the primary. Their within-laugh explained-variance fractions are 0.021184 with situational controls and 0.007015 without them; these are scale reports only.

Table: diagnostic background-label permutations. Each row reports all twenty saved fits; summary statistics describe those fits and impose no new acceptance gate. The fixed primary threshold stays two percentage points. The complete vectors are retained in the aggregate receipt.

| Permuted background | Fits | Mean, points | Minimum, points | Maximum, points |
|---|---:|---:|---:|---:|
| AMI native language | 20 | 0.0887 | -4.0379 | 3.0559 |
| ICSI english variety | 20 | -1.4461 | -9.1441 | 3.7451 |
| ICSI region | 20 | 0.2854 | -1.0795 | 1.7772 |

**Validation and integrity.** The carried design's hand-specified events, signed/zero constructed cases and independent dense fixed-effect oracles passed before the corpus run; the repaired clock parser passed its thirteen checks. The language continuation adapter then passed its targeted and native stopped-owner-copy checks. This final continuation completed execution and fresh full source/inference replay with identical result bytes. All 565 final manifest files, input pins, numerical-thread bounds and original checkpoint hashes authenticate. Both children and the supervisor exited and the counted lease is released. Fresh replay is computational verification, not an independent human replication.

**Cost.** The final continuation used 158.281250 native CPU seconds and 191.951314 wall seconds. Including the retained original source failure, repaired source, planned analysis prefix and four supervisor allowances, the LA4 card has used 423.328125 CPU seconds of its 30,000-second ceiling. All prior failures and attempts remain. A setup-separated forecast was used at continuation admission rather than charging source preparation once per draw block; the original conservative upper bound remains in the prefix record.

**Means.** This tests a conditional, observational shared-background association in labeled meetings. The broad primary interval leaves the predicted small association unresolved. Shared native language is not shared hidden knowledge, actual co-presence is incompletely observed, and joining can reflect convention, affiliation or other situational causes. The result therefore neither confirms nor rejects laughter as completed inference. Role-only scale fits, unsupported ICSI contrasts and a source-held co-attendance term cannot fill that gap.

**Activation record.** PLAY is the hypothesis context; no set point or trigger was measured or manipulated. Shared-background labels varied, people could join or not join, and annotated joining was observed. The relation to the trigger table is **says nothing**: channel firing and hidden inference were not identified. This records the observation without treating every laugh as a measured PLAY activation.

**Next and reporting.** Carry the primary interval, sensitivity, all descriptive variants and source holds into the final curator packet. The already commissioned two- and three-second windows remain separate lower-priority 200-draw textures with their own cost admission; no outcome-driven repair of the primary is licensed. Continue the source and review queue in packet order. No new hypothesis was harvested and no p-value is quoted. Scientific detail is filed internally under the final-packet policy. Acknowledge the completion event only after full write-through and generated-view validation.
