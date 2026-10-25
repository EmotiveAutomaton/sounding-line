# CA3 choice and statement separation

CA3 asks whether a person's choices predict the values stated in their own
explanations. `cards/week3_alignment_values_inputs.py` prepares that comparison's
source partition before any value-label outcomes are used. This is a support
census and has no scientific readout.

The reader's fit uses every comparison with no explanation. It excludes every
comparison that has an explanation, including explained comparisons that were
not sampled for VAL. Removing the explanation string while retaining its choice
would leak the target comparison into the direction being evaluated. VAL's
sampled explained comparisons are joined by writer, conversation, turn, prompt,
original half and exact statement bytes. Duplicate or substituted targets refuse.

Every person in the fixed CA1 population remains in the private output. A person
with no unexplained comparisons or no sampled explanation target receives an
explicit unsupported-input disposition. The runner does not shrink the population,
fit a replacement direction, weaken support or interpret an unsupported case as
zero performance. Parent review is required if the complete population lacks
support for the commissioned comparison.

The authenticated VAL source preparation suffices for this preparation; labels
are not read. Complete calibrated labels, full candidate features, actual
population/country/individual refits, leave-person-out value prototypes,
annotator-level uncertainty and the empirical reference bank remain to be built
and admitted. Four constructed checks cover strict fit/target separation,
unsampled explanation exclusion, join corruption and complete fresh replay.
