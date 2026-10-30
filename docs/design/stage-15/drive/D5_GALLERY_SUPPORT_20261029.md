# D5: fixed-population gallery support

This completes a prerequisite of the existing D5 commission and Week 3
section 0.4. It introduces no scientific comparison or reduced population.

## DESIGN CHECK

LESSONS sections 3-5 and CONTROLS sections 1-7 reread for this build.
Under null and alternative, keep every original session and all 61 writers
in the census. Use the existing whole-prompt split: first dates order each
writer's prompts; alternating prompts define the two halves. The inherited
minimum is four sessions and two prompts. An unsupported writer remains a
named missing candidate; it is never silently removed from the gallery.

Check final character counts, all six human prefix lengths, selection and
timing separately, and the joint selection/timing channel. Joint support
requires both components in both halves; they need not come from the same
session. Missing evidence remains missing. No length is selected here.

Freeze model-share bin edges at 0, 0.25, 0.5, 0.75 and 1. Use left-closed,
right-open intervals except the last, which includes 1. Missing shares have
their own count. Boundary cases must belong to exactly one bin.

Retain the original leave-writer-out context diagnostic and the separately
approved independent-writer correction. Seed 20261026 assigns sorted writers
to three permuted, alternating role folds. In rotation f, donors are fold f,
probes are fold (f+1) modulo three, and the gallery is both non-donor folds.
Every writer is a probe once. Count missing prompt/component donor support
for every session. Donors never include a scored gallery writer. This checks
necessary support only; it cannot validate identification, featurewise means,
the full reference banks, or a scientific gate.

Authenticate both completed feature producers and their shared source ancestry.
Join exact session/writer/prompt/date/share identities and require word-length
and prefix-support parity. Preserve all existing source modules and outputs.
Known-answer boundaries, ties in dates, multiple sessions per prompt,
missing evidence, role disjointness, complete actual producer integration,
tamper refusal and fresh native replay precede full-source execution.

## Resources and remaining work

Charge a 120 CPU-second build reserve, twice targeted-test elapsed time,
constructed native execution/replay and full execution/replay to the retained
D5 charge of 1071.349375 CPU seconds. Keep the cumulative 3600-second allowance.
Constructed execution/replay is capped at 60 CPU seconds and 90 wall seconds;
full execution/replay at 400 CPU seconds and 600 wall seconds, one counted
slot, two numerical threads, 4 GiB projected RAM and 128 MiB output.

This support inventory does not authorize shrinking the 61-person candidate
set, selecting a successful length, ignoring missing reference support or
making an individual identity claim. Identification, both complete reference
families, the within-writer share shuffle, scientific known-answer admission,
and measured whole-workload cost admission remain separate requirements.
