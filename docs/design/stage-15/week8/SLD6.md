# SLD6 · Traits and the response to different daily stressors

Use the second MIDUS main panel and National Study of Daily Experiences. The survey and diary on the reviewed joined mount retain their source hashes from the wave-two contract. The survey codebook is the January 29, 2021 edition, PDF pages 752–755. The May 5, 2022 daily diary codebook supplies the event categories.

| Diary code | PDF page | Use |
|---|---:|---|
| B2DF1, B2DF2 | 141, 153 | Experienced or avoided interpersonal conflict |
| B2DF3, B2DF4 | 164, 174 | Work, school or home overload |
| B2DF6 | 197 | An event affecting a close friend or relative |
| B2DF5, B2DF7 | 184, 208 | Discrimination and other events count toward excluding mixed days |

The seven occurrence items use 1 for yes and 2 for no. A reference day requires seven known negative responses. A single-kind day requires a positive response in that kind and known negative responses for all events outside it. A known yes establishes the kind even if the other item within that kind is missing. All other days are omitted for the corresponding comparison. Preserve each person's study days 1–4 and 5–8. Each half needs both an exposed and a reference day. The response is the mean of the same fourteen unpleasant daily ratings as SLD3, complete on the retained day.

The survey composites are B1SAGREE, B1SNEURO, B1SEXTRA, B1SCONS1 and B1SOPEN. B1SCONS1 uses the items shared with wave one. Keep the provider's direction and missing-value treatment. Before fitting, the structure job validates the pinned source, a unique person key and the presence of the columns. Its sole output uses the previously released full survey roster as its count. A missing optional composite closes its own branch. A missing required field or a changed source ends the check with its recorded code.

Keep SLD3's half-by-half trait operator, its controls for personal level and spread, family clustering and 2,000 joint bootstrap draws. Compute one contrast per trait from conflict minus the mean of overload and close-person effects. Joint draws preserve the dependence between these estimates. Report the support behind each effect and withhold any linked grouping the disclosure rule rejects. The shuffled-trait control uses a fixed random permutation of whole people before fitting. No demographic variable or MIDUS Refresher data enter.

**Design check.** Exercise pure and mixed days, missing items, absent optional composites, an ambiguous person key, source tampering, historical membership reconstruction, planted trait differences and a small complement. Verify a fresh read and the original gate on constructed SPSS tables before each type of submission.

Rare close-person events leave few people with a slope in an eight-day diary. An interval that includes zero leaves the trait contrast undecided. The preflight found the planted contrast in 13 of 100 constructed diaries of this size.
