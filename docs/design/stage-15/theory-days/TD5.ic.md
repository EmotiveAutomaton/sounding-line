# TD5.ic: complete disagreement-rule sensitivity in balanced constructed worlds

DESIGN CHECK: LESSONS 2-5 and CONTROLS 6-7 read for this design.
Independent, uniformly labelled raters have population lift one for every pair,
and zero within-minus-best-rival contrast. The positive mixture below increases
each of the six target contrasts; the negative mixture reverses all six. Every
competitor is still selected from the full observed world using the original
expected-count floor. Test both signs, the exact population formulas and the full
six-pair decision, not only individual confidence intervals.

First-generation instrument check already registered after TD5's inconclusive
result. Owner rationale: test the consumer's ability to detect its practical
contrast while retaining strongest-rival selection and the six-pair conjunction.
No descendants. This is conditional constructed calibration, not a power estimate
for the actual heterogeneous, multilabel annotation population. The human result
and its original coefficients remain unchanged.

## Fixed construction

Use 37,335 independent comments, the completed parent's exactly-three-rater count.
Each comment has three distinct raters, each with exactly one label among the 14
assigned emotion categories. All 14 marginal probabilities are 1/14. Unassigned
categories are absent and their comparison is unsupported, never a zero rival.
This omits real label imbalance, multilabel responses, rater reuse/dependence,
text variation and the adaptive extra-rater rule. It calibrates the shared rule on
a deliberately simple population; passing does not validate those omissions.

At dose zero all raters independently draw a uniform label. At positive dose d,
with probability b=d/7 a comment draws one of the six original channel pairs or
the two singleton channels, with probability equal to its number of labels/14;
its raters draw independently within that group. Otherwise draw independent
uniform labels. Every target pair has population lift 1+6b, every cross-channel
pair 1-b, hence the target contrast is exactly d.

For negative dose use seven disjoint cross-channel pairs instead of the original
groups: anger/fear, annoyance/nervousness, grief/amusement, sadness/joy,
curiosity/caring, excitement/love, desire/disgust. With b=abs(d)/7 each target
pair has lift 1-b and has a rival at 1+6b, hence contrast d. Label names are not
reassigned to channels. The construction changes co-occurrence, not the mapping.

Freeze doses 0, +0.1, +0.2 and -0.2; 100 independent worlds per dose, with seeds
[20261106, dose index, world index]. Enumerate all 560 unordered three-label
patterns with multinomial multiplicities. Draw pattern counts for each world.
This is exactly the declared three-rater distribution, not a reduced population.

## Original rule and exact grouping

Recompute ordered cross-rater counts and marginal exclusivity. Select each pair's
strongest cross-channel rival using expected count at least 50, with the parent's
canonical label-order tie break. Bootstrap whole comments 2,000 times with seed
20261106, recomputing marginals. Retain both the fixed-rival interval and the
maximum-reselected interval over the full-world eligible rival set. The original
rule wins when the interval lies above zero and the point difference is at least
0.1; it loses below zero with a difference at most -0.1. Everything else is
inconclusive or explicitly invalid uncertainty. The packet supports only if all
six win; it is against if at least three lose; otherwise inconclusive.

Group identical sufficient-statistic comment patterns for the bootstrap: sample
multinomial weights with probabilities equal to their empirical frequencies.
This preserves the empirical whole-comment bootstrap law exactly, although it
does not reproduce the parent's random stream over individual row IDs. Validate
by literal ordered-rater enumeration and exhaustive small-world bootstrap-law
enumeration, plus complete original-consumer point/competitor parity. Keep the
parent code and all original outputs byte-identical.

Report for each dose, for fixed and reselected rules separately: full packet
supports/against/inconclusive counts, each pair's wins/losses/inconclusive/invalid
counts, mean point bias, interval coverage of its known population contrast,
undefined intervals and unsupported competitors. Preserve every world in all
denominators. Wilson 95% count intervals accompany rates.

Adequacy is separate for each rule: upper Wilson bound on *either* decisive
verdict at dose zero at most 10%; lower bound on full-packet supports at +0.2 at
least 80%; lower bound on full-packet against at -0.2 at least 80%. All must pass;
otherwise sensitivity is limited in this construction. The +0.1 boundary dose is
descriptive and has no high-power requirement. An invalid world is inconclusive,
retained and reported, never discarded or replaced.

Case and check: positive and negative mixtures analytically realize all six signed
contrasts with unchanged marginals; expected pair count at this population size
exceeds 50. Native constructed and original-consumer parity checks precede a
two-world-per-dose cost probe at full population and all 2,000 bootstrap draws.
Full forecast is complete cost CPU times 50 times 1.5, including independent
replay. All attempts share 900 CPU seconds within the 54,000-second campaign.
Smaller route: none; no reduced draws, doses or world count. CPU-only Gear 2;
original freeze/drain and final-packet policy apply. Commit before outcomes.
This calibrates an already approved statistic and makes no literature novelty claim.
