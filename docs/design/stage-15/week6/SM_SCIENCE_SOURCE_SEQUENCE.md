# Source sequence for the sealed MIDUS studies

On November 20 the curator confirmed that SM1 proceeds on
`midus-m2-joined`. Its survey and daily tables passed the joined-source
structure checks. The four scientific analyses still require their own
constructed qualification, independent replay and aggregate return.

SM2 tests repeat participants. Its four branches use the corresponding
wave-two eligibility rules, so the sealed process must be able to establish
wave-two eligibility before selecting the wave-three observations. Spark
mounts one source folder per invocation.

The archive supplied `midus-m2m3-joined` in delivery DC-20261120-02. The owner
verified all five metadata files against the manifest. It identifies four
original SPSS files with the same person key, `M2ID`. The wave-two main
survey supplies `M2FAMNUM` by that key for cross-wave family clustering.
The collector reports 53,581,739 source bytes. Joined-population and family
coverage are measured in the sealed process. It retains participant links
and branch-specific eligibility sets. SM2 follows the SM1 return.

Under amendments AW and AX the wave-two science job also returns NT1.s and
D5.s wherever their fields are supported. It records any missing table
separately. When a study source lacks family numbers it resamples whole
people and reports “intervals treat relatives as unrelated.” The installed
gate continues to require actual eligible participant counts.

The original [sealed execution contract](PACKET_EXTENSION_2026-11-19.md)
governs both jobs. The completed [structure record](../../../../results/phase_2_4_stage_15/WEEK5/SM0_JOINED_COMPLETE_20261120.md)
documents the two earlier single-wave mounts.

## Wave-two argument resolution

The MIDUS 2 Daily Diary Project codebook dated May 5, 2022 identifies `B2DF1` as an argument or disagreement since the previous interview (page 141). For a reported argument it asks whether the issue was resolved in `B2DF1WC6` (pages 148–149). Code 1 means yes and code 2 means no. Codes 7, 8 and 9 mean unknown, refused or missing, and inapplicable respectively. The dictionary skips this item when an argument was absent or its occurrence was unknown.

D5.s uses the argument item and its own resolution question. Other stressor blocks ask a similar question. A skipped resolution question cannot supply an unresolved argument. Count next-day observations only where the study-day numbers are consecutive for the same person. Confirm both column names in the authenticated daily table inside the seal before opening this analysis. Its return reports the observed-person counts allowed by the sealed gate and identifies the comparison as a replication. The person's report of resolution and differences between the arguments limit its interpretation.

The dictionary SHA-256 is `48727f67a9c111ebbbebf50729a8d759a565b4021e6b0bece8b1546cf7078b10`. This mapping used the codebook only.

## Trait and daily stressors

NT1.s uses the wave-two survey Neuroticism composite and pairs of consecutive original study days with consecutive weekdays. Compute the support count from the survey trait, clock and seven stressor occurrence items before reading any feeling. A known stressor is sufficient to establish exposure. To establish an event-free day, all seven occurrence items must answer no. The section 4 support floor is 300 eligible pairs with a preceding stressor from at least 150 people.

The binary negative-feeling outcome uses the fourteen ratings in the original MIDUS negative-affect register. A day with any known above-floor rating is positive. Zero requires all fourteen ratings to be observed at floor. The primary logistic fit uses current and previous stressors centered on the person and scaled by their pooled within-person standard deviations. It includes both person means, the standardized survey trait and its interactions with the two stressors. Standardize the trait across people, giving each their draw multiplicity. The day-level fit has no prompt-type covariate, since every record is an evening diary.

Retain both stressor coefficients, the trait coefficient, both interactions, their plain difference and the registered difference of proportional changes. A zero denominator or an unidentified model leaves the affected quantity unavailable. A separate weighted least-squares implementation rechecks the logistic fit. The six interpretation branches and their saturation limits follow the November 20 packet. A day is a coarse interval and the stressor and feeling reports come from the same evening call.
