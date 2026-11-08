# V1 support and conditional uncertainty clarification

This prospective addendum clarifies the implementation in
[BK_CA1_V1.md](BK_CA1_V1.md) before any human V1 fit. The 1,036-person source,
both original sample groups, original model and all prior inputs remain fixed.

An annotator who is the only person from her country has neither a valid
leave-person-out country prior nor a same-country comparator. Save the absence
of a fitted direction explicitly and count her among the no-comparator cases;
do not substitute her own data into a country prior or invent a direction. Her
observations remain in population priors for other people. Missing halves in
otherwise eligible cases still refuse. A group with no eligible paired
comparison has no reliability estimand and receives a descriptive unsupported
record, rather than a numerical zero. A group with 1–19 paired annotators has
its pooled paired contrast reported below-floor descriptive.

The specified 2,000 annotator-cluster resamples resample paired own-minus-matched
gains while keeping the predeclared comparator reference fixed. They quantify
conditional variation among probe annotators, not fresh sampling uncertainty
in the comparator pool. The result names that limit explicitly. The separately
reported 200 within-person label shuffles refit every prior and direction;
they do not license an identification claim or replace this interval.

**DESIGN CHECK.** Known-answer checks require exact-zero paired gains to stay
zero, both positive and negative directions to retain their sign, strict sample
group matching, and no focal choice entering either prior. A singleton-country
fixture must return an explicit missing direction. The null and alternative
use the same support rules; a changed supported set in a control bank refuses.

No added source, model, CPU allowance or paid work is introduced. This belongs
to V1's existing complete control bank and shared CA1/V1 cost accounting.
