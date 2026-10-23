# GEN1: preserve the admitted population when joining the archive

The first corpus input attempt stopped before matching because the full archive
roster contains 1,445 sessions while the completed PMAP and word ledgers contain
1,399. This is the same upstream-only distinction handled by PMAP's source
recovery. The GEN1 fixture incorrectly tested equality of the archive and study
populations. Preserve the failed attempt and original component.

The separate `week_genre_inputs_recovery` authenticates every completed PMAP
session output and its aggregate session count. Its session set must equal the
completed word-ledger set exactly. The archive must cover every admitted session;
its 46 upstream-only sessions remain outside this study with explicit identities
in the private source-population manifest. Every admitted session's writer,
prompt and timestamp must agree across all three sources. No new scientific
selection, imputation or loss of the original cohort is permitted.

The [original matching policy](GEN1_INPUT_MATCHING_20261022.md) is reused unchanged.
The recovery fixture includes an upstream-only archive record and tests missing
primary/word support, altered saved sources, conflicting identities, duplicate
completed sessions, aggregate count disagreement and changed output. Native
execution and fresh replay precede the single engineering corpus retry.

Reserve 240 cumulative wall seconds for both builds, targeted/native checks and
the failed corpus attempt; this replaces the previous 120-second preparation
reserve, not an additional allowance. The retry retains a 600-second combined
execute/replay cap within the original conservative 1,800-second limit. Every
subsequent feature/control run must charge these costs. The one S4 doubling is
unused. Input preparation cannot license a genre result or waive any control.
