# SP1 RANK REPAIR

**Hypothesis.** Does exposure to outdoor temperature shift the neutral temperature more in naturally ventilated than in air-conditioned buildings?

**METHOD.** Fit the frozen fully interacted cooling-group model and run all 2,000 building resamples. Diagnose each failed draw using design ranks without discarding or redrawing it. Compare the algebraically equivalent separate-group estimator on constructed full-rank, singular-nuisance and singular-primary examples, followed by actual signed/null full-draw native replay.

**Found.** The original thermal slope contrast has invalid bootstrap uncertainty because an irrelevant mixed-mode nuisance group lost rank in two draws; the unchanged primary has a separately validated exact repair.

The original analysis used 213 eligible buildings; weather-linked fits contained 82 air-conditioned, 51 naturally ventilated and nine mixed-mode buildings. Draws 1,555 and 1,931 retained rank-two primary groups but sampled two mixed-mode rows at one outdoor temperature. The joint fit therefore failed on a nuisance coefficient absent from the requested primary contrast. The original attempt and both failures are retained. No interval or substantive verdict is licensed from that attempt.

**Repair.** SP1.h2 fits the two primary group slopes separately. This equals the original fully interacted contrast whenever that full design has rank. It retains the original sample, seed, every draw and bar; primary-group rank loss still refuses. Three focused checks and the complete signed/null 2,000-draw handler fixture pass. The repair is committed before the new human attempt. This is an instrument correction, not a scientific null or an outcome-selected sample. Source and scientific effects stay unchanged; a new attempt must independently replay before interpretation.
