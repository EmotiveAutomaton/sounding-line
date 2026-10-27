# TR3 TYPING NATIVE 20261026

**Hypothesis.** Can the writer's edits retain their actual document context and original insertion source, including text deleted later?

**METHOD.** Test a constructed sequence with Unicode user insertions, API text, an unknown source, a later deletion and a cursor edit. Reconstruct every UTF-16 delta and final ownership run, require exact source equality, then execute and independently rebuild the complete fixture through the production native executor.

The table reports source instrument validation, not a carryover effect.

| Check | Complete observation |
|---|---|
| Known-answer fixture | Four edits preserved; five user characters inserted, four survive |
| Unicode and source boundaries | Correct UTF-16 retention/deletion, API and unknown-source exclusion |
| Refusal cases | Changed final document, identity, insertion total, clock, malformed surrogate and repeated initialization refuse |
| Empty source | Empty document and zero-edit session retained |
| Serialized checks | Immutable reentry, complete independent replay and changed-output refusal pass |
| Targeted checks | Nine pass |
| Initial test setup | One temporary-directory access error retained; rerun in a fresh workspace test directory passes |
| Native inputs / outputs authenticated | 36 / 17 |
| Native termination | All exact worker identities exited |
| Cumulative TR3 charge/reserve | 501.546875 of 7,200 CPU seconds, including the additional 60-second construction/test reserve |

**Found.** The exact typing-context instrument passes known-answer and native replay checks; corpus preparation and carryover remain separate gates.

**Means.** The full primary corpus can undergo bounded typing-context preparation under the existing TR3 allocation. The compact stream preserves all edits, including non-user changes and later-deleted characters, so downstream extraction need not concatenate distant user deltas or select only surviving text. It computes no feature, effect, test-half statistic or probability. The exact exposure source and writer split remain unchanged. Discovery feature selection, production-time occurrence definitions, placebos, calibration and whole-study cost admission remain. The ready-card target is not yet met. No new tests were harvested from the wake notices.
