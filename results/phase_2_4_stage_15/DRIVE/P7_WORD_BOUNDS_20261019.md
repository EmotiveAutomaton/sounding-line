# Bounded word-event diagnostic: verified complete

**Question.** Can the native reader bound the original next-word event without discarding probability mass from alternate tokenizations, case variants or unfinished paths?
**METHOD.** Validate the enclosure on known finite probability trees and boundary counterexamples, then run the same four fixed pilot words through a pinned CPU GPT-2 medium reader. Save the complete next-token distributions for every expanded prefix. Recompute every distribution and bound in a fresh native process and reconstruct the saved bounds again at landing.
**Found.** Known-answer checks and exact native replay pass, but none of the fixed examples reaches the required precision. **Means.** The enclosure apparatus is validated for this numerical reference distribution; a usable point score and the scientific comparison remain unadmitted. This is not a negative scientific finding or an impossibility result.

The table describes completed instrument validation, not the unfinished corpus comparison.

| Validation item | Completed outcome |
|---|---|
| Known-answer component checks | 24 pass |
| Constructed full-handler checks | 2 pass after two retained fixture setup errors |
| Fixed native examples | 4, chosen before execution |
| Distinct native prefix evaluations | 16, all repeated exactly in fresh replay |
| Point-score precision gate | 0 of 4 reaches the fixed 0.0001-nat width |
| Source and terminal integrity | 125 pins and 31 outputs verified |
| Worker closure | Owner, launcher identities and actual execute child exited; CPU lease released |

The first handler test invocation could not create its system temporary directory. A fresh workspace fixture directory resolved setup; the two original errors remain recorded and charged. No failed scientific attempt is reclassified. The numerical checks include exact rational answers, alternate tokenizations, Unicode casefolding, apostrophes, incomplete UTF-8, impossible conditioning and retained separator/context tails. Two handler checks exercise complete serialization/replay, tamper refusal and saved-boundary yield on a constructed model; they do not substitute for the actual native run.

The native diagnostic ran CPU float32 with two threads, local pinned files only. It expands at most four prefixes per event and retains unexpanded or context-limited mass in an interval. Original canonical context/crop and observed token-overlap bytes remain fixed. Interval arithmetic covers the normalized finite weights emitted by the numerical oracle; it does not certify neural arithmetic or model truth. No midpoint, omitted-mass zero, shortened context or relaxed precision is used. Neither full-population cache compatibility nor a full-corpus runtime forecast has been admitted.

Native owner-to-terminal time was 124.953 seconds. Including earlier diagnostics, all test invocations, launch overhead and 6.990 seconds of saved-evidence verification, the cumulative charge is 458.891 of the unchanged 900 seconds; 441.109 seconds remain. Further refinement requires a measured forecast within that remainder. No automatic doubling, GPU start or paid work follows.

Terminology correction to the earlier diagnostic narrative: the D33 history cache keeps literal casefolded token counts. The population reader's unseen-word mapping is a separate compatibility issue; the cache must not be described as collapsing every unseen word into one event. Original evidence is preserved. The wider scientific question remains open.

[Aggregate receipt](P7_WORD_BOUNDS_20261019.json) · [Frozen contract](../../../docs/design/stage-15/drive/P7_WORD_BOUNDS_20261019.md) · [Earlier native diagnostic](P7_WORD_EVENT_NATIVE_20261019.md).
