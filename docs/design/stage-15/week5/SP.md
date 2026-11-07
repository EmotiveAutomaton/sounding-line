# SP: comfort location and sensitivity

DESIGN CHECK: LESSONS 2–5; CONTROLS 6–7. Constructed buildings must recover
their assigned neutral-temperature and sensation slopes and the signed group
contrasts. Missing weather or operative temperature cannot be filled from a
convenient surrogate. Zero temperature range cannot identify a slope. Every
bootstrap resamples whole buildings (whole studies in that texture), and rank
or support loss remains an explicit failure. These observational comparisons
do not identify thermal history separately from personal control.

## Source

Zenodo 4993952 is the successful first route. Its metadata explicitly states
CC BY 4.0, retained as the licence of record despite the other sources' licence
differences. Cite Földváry Ličina et al. (2018), ASHRAE Global Thermal Comfort
Database II. Sources remain private and are pinned:

| Source | SHA-256 |
|---|---|
| db_measurements_v2.1.0.csv.gz | 23711ee1cfd988501d1ee77fc2207884e3edcb126cf96c0cd30a5380f39bd5e0 |
| db_metadata.csv | af6770a2b469f079cd172bd6632d1ae726a3a663515126816ff6d2d8f51bfc10 |

The source has 109,033 measurements and 809 unique building metadata rows.
Join is many-to-one on `building_id`; missing metadata refuses. Read only
`top`, `thermal_sensation`, `thermal_acceptability`, `t_mot_isd`, `fan`,
`window`, `clo`, `met`, `vel`, and building key from measurements; cooling type,
climate and publication from metadata. `top` is operative temperature and is
not substituted with air temperature. `t_mot_isd` is the prevailing mean
outdoor-temperature field. Building and publication/study keys are salted.
Participant identifiers and demographic values are not read.

## Frozen estimators

The packet's hypotheses, bars and directions bind: SP1 naturally ventilated
minus air-conditioned location/weather slope, bar 0.1; SP2 air-conditioned
minus naturally ventilated median sensitivity, bar 0.05; SP3 sensitivity slope
on distance from 22°C, predicted negative, bar 0.01.

For each building with at least 30 respondents, OLS fits sensation on operative
temperature. Neutral temperature is mean temperature minus mean sensation
divided by the slope. A slope below 0.1 uses Griffiths' 0.5 divisor; the all-
Griffiths texture applies that divisor everywhere. SP1 fits separate intercepts
and outdoor-temperature slopes for each observed cooling type. SP2 compares
the median building slopes. SP3 groups distance into [0,3), [3,6), … bins and
regresses each building's sensitivity on its bin centre. This is equivalent to
a count-weighted regression on bin means. Outdoor temperature is averaged
over each building's retained measurements; missing weather is counted and
excluded only from weather-dependent comparisons.

The secondary 80%-acceptable band uses a quadratic logistic fit within each
building's observed temperature range. It is the longest contiguous fitted
region above 0.8 on a 501-point grid. At least ten explicit acceptability
answers are required. All-acceptable or all-unacceptable samples give their
observed range or zero respectively, descriptive only. Nonconvergence yields
missing width, never a substituted sensitivity.

Texture fixes these implementations before outcomes: SP2 matches buildings
without replacement by nearest standardized mean temperature and range; its
ordinal probit preserves the source's ordered sensation categories and reports
latent-probit units, not a false application of the linear practical bar.
SP3 range matching uses naturally ventilated buildings in each distance bin,
matching their temperature ranges to the smallest bin without replacement.
Covariate textures include clothing/metabolic rate, air speed or recorded
window/fan controls in the within-building regression and count complete-case
loss. Hot and cold sides remain separate texture. Study-cluster intervals
use the salted source publication key.

Each primary has 2,000 whole-cluster bootstrap refits; textures have 200.
Unsupported bootstrap draws are not dropped or redrawn. The default 20-cluster
floor triggers a descriptive fallback allowing estimable buildings with at
least two respondents; absent variation or missing covariates can still leave
only descriptive source counts. A fallback never becomes a primary support.

`grid()` registers three primaries and eleven declared texture cells. Source
projection and every complete analysis expose execute/verify; the fresh verifier
compares every projected value or replays every fitted bootstrap draw.
Projected peak RAM 0.5 GiB, two CPU threads maximum. Each primary ceiling is
10,000 CPU-seconds; family 40,000. Cost and any pilot are charged inside the
counted run. No GPU, Ollama or provider transfer is used.

Native fixture tests recover a +0.3 location contrast, +0.3 sensitivity contrast
and −0.02 dulling slope. A test initially put a nominal pair in adjacent
distance bins; correcting the fixture temperatures to its intended common bin
made the explicit partition check pass. No human outcome was inspected.
