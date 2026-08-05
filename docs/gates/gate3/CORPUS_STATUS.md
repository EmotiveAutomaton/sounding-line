# Gate 3 corpus — 41 collected, row 3 is the bottleneck, and one decision is not mine

Target from `docs/STRATEGY.md` §3: **21 per row for 80% power at the observed d = 0.87.**

---

## §1. Where the corpus stands

| row | have | need | status |
|---|---|---|---|
| **2 — real makers** | **~28** | 21 | **done**, with a caveat in §2 |
| **3 — commercial filler** | **8** | 21 | **short by 13** |
| 5 — pre-2020 human | 4 | — | supporting, not a comparison arm |

41 artifacts in the content-addressed store, none of them re-hosted.

---

## §2. The row-2 caveat: domain concentration

Five artifacts are Paul Graham's, three Ciechanowski's, three Martin Fowler's. **Artifacts from one
maker are not independent observations of "a real maker."** Capping at two per domain drops row 2 to
roughly 22–24, which still clears 21 but only just, and the cap should be applied rather than
argued around.

---

## §3. Why row 3 is hard, measured

| row | candidates tested | usable | rate |
|---|---|---|---|
| 2 | 44 | 25 | **57%** |
| 3 | 19 | 5 | **26%** |

**Commercial operators block crawlers at more than twice the rate of individual makers.** Every
`gohighlevel` template page, every HomeAdvisor service page, both roofing sites, MMOExp, and four of
seven affiliate listicles refused.

This is the bias the Gate 2 card predicted, now with numbers on it. It is also self-reinforcing:
the row-3 artifacts obtainable by honest means are the ones whose operators **did not bother to
block**, which plausibly skews toward the less sophisticated end of commercial content — the end
least likely to be optimised, and therefore least likely to be intentless.

At 26%, filling row 3 needs roughly **50 more candidates tested**.

---

## §4. The decision that is not mine to make

**web.archive.org permits crawling, and it holds copies of pages whose live hosts refuse.**
Fetching the archived copy would unblock row 3 immediately — MMOExp, the template pages, the
listicles, all of it.

**It is also circumvention of a stated preference.** SPEC §8 says honour robots.txt "even for
content you find contemptible... the provenance of your own method is part of the argument." A site
saying *do not crawl us* has said that; routing through an archive that says *you may crawl us* is
legal, conventional in research, and still not what the site asked for.

Arguments each way, stated plainly:

**For:** the Internet Archive's own robots policy permits it. The alternative is a corpus
systematically biased against the artifacts the project most needs. The pages are already public
and already archived; no new copy is created. Standard practice in web-corpus research.

**Against:** the spec's commitment was made in absolute terms and this is exactly the case it was
written for — content the project finds contemptible. A methods section that says "we honoured
robots.txt except where it was inconvenient" is weaker than one that says "we honoured it and
accepted the cost."

**I am not deciding this.** It changes what the project can claim about its own conduct, and that
is the curator's call.

---

## §5. What the curator can do that I cannot

**Name row-3 artifacts from memory.** This is the highest-value hour available.

I am finding commercial filler by guessing URL patterns and testing them at a 26% pass rate. A
person who browses the web encounters this material constantly and can produce fifteen examples
faster than I can validate fifty candidates. Specifically useful:

- template local-service pages ("plumber in <city>", "roofing <city>") — the purest specimens
- brand content marketing that answers a question in order to sell a product
- affiliate listicles and "best X of 2026" roundups
- aggregator and directory pages with no author
- AI-written news or guide sites, if any are recognisable

**A URL is enough. No reading required.** If the live page blocks, I will note it and it feeds §4's
decision rather than being lost.

---

## §6. On n = 1, and why it is less of a problem than it looks

The curator raised this and it deserves a real answer rather than a caveat.

**The stated worry:** one reader, and that reader is autistic, so the calibration standard is one
neurodivergent person's judgement.

**The observation that answers most of it — theirs, not mine:** the population that writes Elden
Ring build guides, exhaustive hobbyist comparisons and deep technical postmortems is itself heavily
neurodivergent. So for *this corpus*, the curator is plausibly a **matched** reader rather than a
biased one.

And the theory makes that precise rather than merely reassuring. Line 233: *"It is the language of
expertise that unlocks the ability to observe the hierarchies of decisions in others. Expertise
just means having made lots of similar decisions yourself."* E10 established that reader skill caps
extraction. **A reader matched to the maker population is the correct instrument, not a confounded
one.** A "neurotypical average" reader would recover *less*, not more, and would be a worse
standard.

**What n = 1 genuinely limits:** generalisation to a general-public reader. The project does not
claim that — SPEC §1's claim is about what is recoverable from an artifact, not about what an
average person recovers. The limit is real and narrower than it first appears.

**What would still help:** a second reader, on a subset, purely to bound how much of the standard
is idiosyncratic. Not required for Gate 3, and worth noting as owed. Recorded as **C-20**.
