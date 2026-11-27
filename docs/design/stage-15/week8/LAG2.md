# LAG2 · Independent replay of diary 0057

The first pass in Week 7 finished all 649 selected cells. The previous independent run reproduced 28 before exhausting its allowance. Week 8 checks each historical checkpoint against the complete first pass and replays all 649 in a fresh process from the pinned source. It uses the same-person bootstrap draws, two gap readings, event selection, clock and seed as the original. The original attempt stays on its Week 7 ledger.

**Design check.** A mismatched cell or an altered source withholds the diary from the pool. The constructed qualification checks planted carry-over, missing-answer and clock boundaries, and refusal of an unidentified coefficient. The full fresh output and every cell must match the first pass byte for byte before admission to the pooled table. Week 8 allows 60,000 CPU-seconds for the row. The initial reservation is 59,000.

The ratio is descriptive. An ongoing event can look like a persistent feeling, and missed prompts may widen a gap selectively. [Week 7 clock, selection and fitting rules](../week7/LAG_CLOCK_AND_FIT.md).
