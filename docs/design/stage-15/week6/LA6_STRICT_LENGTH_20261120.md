# Strict laughter onset and utterance length

The parent analysis counted vocal laughter that could already be in progress. LA6.s asks whether the held-out prediction survives when a new laugh must start after the utterance. LA6.sl holds utterance length as well. Both studies use the original meeting source, the same speaker, the same two history arms and the original five meeting folds. Each has an inclusive allowance of 30,000 CPU seconds. [November 20 packet](PACKET_EXTENSION_2026-11-20.md) · [Previously frozen windows](LA6_FOLLOWUPS_20261119.md)

Exclude an utterance from matching if any vocal laugh overlaps the closed interval from one second before its start through its end. Keep its words in subsequent utterances’ eligible history. Score new laugh onsets in two separate windows, strictly after the end through one second and strictly after the end through two seconds. Retain the earlier-start and source-ID tie breaks, minimum 30-second start distance and matching with replacement.

For the length-held comparison, the absolute word-count difference must be at most two words or one fifth of the case utterance’s original word count, whichever permits the larger difference. Search across all eligible controls. The nearest time match can differ from the parent. Count and disclose unmatched cases and reused controls. Apply the retention threshold to all eligible meetings together within each window. Exactly half qualifies. Below half, use the ordinary strict-onset pairs and show both arms with and without the word-count covariate. The parent already includes word count. Removing that column’s variation omits it while preserving every other training feature.

Use the parent’s 20-meeting floor, area bar of 0.60, seed 20261107 and 2,000 whole-meeting draws. Report both windows. The pooled act-class table for LA9 requires each annotation scheme’s published mapping and at least 50 held-out utterances per scored class. Freeze the mappings and their hashes before reading any held-out outcome.

**Design check.** Constructed cases distinguish an ongoing laugh from new onsets at zero, one and two seconds; distinguish vocal events from other annotations; exercise time ties and word-count eligibility; verify the exact half-retention boundary; and keep an overlapping predecessor available as language history. Source admission and complete independent replay precede any scientific landing.

**Limit.** This tests an observable context of laughter, not PLAY or its trigger.
