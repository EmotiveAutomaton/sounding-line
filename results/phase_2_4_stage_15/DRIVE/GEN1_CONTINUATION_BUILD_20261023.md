# GEN1 extraction checkpoint continuation

**Hypothesis.** A completed matched-feature extraction can be retained across
its verification time limit without admitting an unverified result.
**METHOD.** Copy completed extraction files exactly, reconstruct all features
from their original sources in a fresh process, and deliberately test incomplete,
changed, already-completed and wrongly classified interruption records.
**Found.** Six targeted checks and the complete counted native rehearsal pass.
**Means.** A bounded continuation is prepared if the live feature run reaches its
combined cap during verification. The corpus comparison remains unrun.

The [continuation contract](../../../docs/design/stage-15/drive/GEN1_CONTINUATION_20261023.md)
retains the original module, input population, feature definitions and complete
source checks. It accepts only the recorded combined-wall timeout during verify
after full extraction; other failures and an unfinished extraction are refused.
Every retained output is byte-identical. All native source/output hashes verify.
No scoring method or control is changed.

The first dispatch preparation accidentally included a directory as a file pin.
It stopped before any worker started. The corrected dispatcher pins the contained
files and reuses the already prepared fixture; that preflight refusal is retained.

Actual corpus source throughput projects beyond the current 900-second combined
cap. Its frozen live plan stays unchanged. The one cumulative S4 extension permits
at most 3,600 wall seconds, including all original preparation, failed source
attempts, extraction, replay and statistical work. A further 120-second validation
reservation raises charges before the live attempt to 599.252590 seconds. An
admissible continuation may receive at most 1,200 seconds, with later comparison
admission taking only the measured remainder. No additional budget is created
by a new process or output directory.

The [machine receipt](GEN1_CONTINUATION_BUILD_20261023.json) records exact proof
hashes, native timing and resources. Live progress is operational evidence only;
no unfinished contrast, probability or genre-weighting conclusion is reported.
The existing source-path build is already on remote main at `3f8ac1035`.
