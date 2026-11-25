# SLD2 three-wave purpose projection

The local rehearsal operates on three made wave files. Each has a unique shared person key and the same scored purpose items. The middle wave supplies a documented indicator of role loss since wave one and family linkage. A person must have the role loss and complete observations on every shared scored item at all three waves. The three wave means refer to the same people.

The return includes the wave means and the paired third-minus-first change divided by the first-wave sample standard deviation in that cohort. Recompute the standard deviation in each of 2,000 whole-family draws. A zero standard deviation leaves the standardized difference undefined. The registered recovery criterion requires the full interval to lie between −0.2 and +0.2. The synthetic case drops in the middle and returns to the original level.

## Original survey binding, November 24

The curator approved the cohort at 17:40 Pacific and the scoring rules at 17:42 Pacific before outcomes were opened. The archive receipt in `DC-20261124-02/SLD2_SOURCE.json` pins three original SPSS files for the read-only alias `midus-m1m2m3-surveys`. Match people by M2ID and resample by wave-two M2FAMNUM. Check unique people on each wave and consistency of nonmissing family codes across waves. Each person contributes once to the pooled reading. Someone with both qualifying losses can also contribute to both separate descriptions.

| Release and PDF codebook pages | Has a sense of direction (positively worded item on aimlessness) | Lives day by day | Feels everything is already done |
|---|---|---|---|
| ICPSR 02760 v19 DS 0001, pp. 1323, 1326, 1328 | A1SF1C | A1SF1G | A1SF1J |
| Wave two, pp. 680, 702, 703 | B1SE1OO | B1SE1E | B1SE1QQ |
| Wave three, pp. 1201, 1220, 1221 | C1SE1OO | C1SE1E | C1SE1QQ |

The response range runs from 1 (strongly agree) to 7 (strongly disagree). Score the first item as eight minus the response and retain the other two in their original direction. Require all three responses at every wave. Code 4 is “don't know” at wave one and neutral at the later waves. The primary excludes wave-one 4 and retains later 4. The second reading excludes 4 throughout. The released wave-two and wave-three codebooks give the cross-wave comparability note alongside each item.

The wave-one interview month is A1PI_MO/YR (p. 26), and the wave-two interview month is B1PIDATE_MO/YR (p. 7). Require a complete month and year strictly inside the two interview months. In the wave-two first-marriage branch, use B1PB22 equal to 1 with B1PB23M/Y for a death, or 2 with B1PB25M/Y for a final divorce. In the most-recent-marriage branch, use B1PB19 equal to 4 with B1PB29M/Y for a death, or 3 with B1PB28M/Y for a final divorce (pp. 208–219). The dates when spouses last lived together do not qualify. Only first and most-recent marriages have the reviewed dated fields.

The sealed table codes the pooled reading as group 1, death as 2 and divorce as 3. Reading 1 is primary and reading 2 excludes all midpoints. Measures 1–3 are wave means and measure 4 is the paired standardized change. Read recovery from the two pooled intervals. Disagreement about containment inside the registered band gives an undecided row. An unavailable pooled interval leaves recovery undetermined. Give the two pooled rosters priority when testing membership partitions against the eleven-person disclosure minimum. Replay the analysis from a fresh read before writing any output.

Carry both curator limits with the return. “One kind of role, and divorce may be chosen where a death is not.” “The wave-one scale had no neutral point, so a change from wave one to wave two is partly a change of scale.”
