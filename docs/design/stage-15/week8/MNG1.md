# MNG1 · Meaning and happiness in daily activities

The U.S. Bureau of Labor Statistics collected the Well-Being Module in 2010, 2012, 2013 and 2021. The annual activity dictionary binds WUMEANING and WUHAPPY to whole-number ratings from 0 to 6. Join each rated episode to its own year's Basic Activity record on TUCASEID and TUACTIVITY_N. The Who file has multiple records per episode. Reduce these to sets of company indicators before joining. Only the respondent key, episode number, two ratings, activity weight, activity code and company code enter this study. [Well-Being dictionaries](https://www.bls.gov/tus/dictionaries.htm) · [BLS linking and weight guidance](https://www.bls.gov/tus/other-documentation/howto.htm).

| Activity family | Six-digit activity code or prefix |
|---|---|
| Child care | 0301–0303 and 0401–0403, including education and health care |
| Adult care and help | 0304–0305 and 0404–0405 |
| Paid work | 0501 |
| Housework | 0201 |
| Eating and drinking | 11 |
| Socializing and communicating | 1201 |
| Games and participation in sports or exercise | 120307 and 1301 |
| Television and movies | 120303 and 120304 |
| Religious activities | 14 |
| Volunteer activities | 15 |
| Other activities | All other valid codes, including travel |

Company groups use the Who dictionary. Alone is 18 or 19, a partner is 20 or 21, children are 22, 27, 40, 52 or 57, friends are 54, and co-workers are 59–61 including supervisors and supervisees. Children includes one's household children, whose age is unspecified in this field. Other company is a separate category. An episode can enter several company groups, once in each. An absent or wholly unavailable Who report contributes only to the activity table. A contradiction between alone and someone present voids that episode's company information. [Activity lexicons](https://www.bls.gov/tus/lexicons.htm) · [BLS Who dictionary](https://www.bls.gov/tus/dictionaries/atusintcodebk0321.pdf).

Retain episodes with both valid ratings and positive activity weight. Within each person subtract their arithmetic mean meaning rating from each meaning rating, and do the same for happiness. Take the difference between those two departures. A person with one eligible episode contributes zero and is counted. Give each survey year equal total weight, using the corrected WUFNACTWTC in the three earlier years and WUFNACTWT in 2021. Within each activity or company group divide the weighted sum of departures by eligible episode weight. Use 2,000 whole-person resamples within year and report their central 95% interval. Report the number of distinct people, episodes and matched years. The late-activity selection error affects the early surveys, and 2021 covered March to December. [BLS selection correction](https://www.bls.gov/tus/notices/2014/wbnotice.htm).

**Design check.** Invent a caring episode and a work episode for each person, then duplicate a companion and add a second kind of company. Check the centred signs, zero for a constant respondent, missing-company handling and the weight used for each year. Reproduce the complete result from the twelve original ZIPs. The BLS tables are public-domain work. One word, “meaningful,” stands in for the need. People choose what they do, and ordinarily rate only three activities.
