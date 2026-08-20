"""G160 schema tests: the interface guard must refuse process-informed fields in lower
interfaces, and the claim boundary must be mandatory and vocabulary-checked. Run direct:
./.venv/Scripts/python.exe tools/test_reading_profile.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soundingline.reading_profile import (ReadingProfile, ClaimBoundary, Interface,
                                          InterfaceLeak, RankedCandidate)


def base(interface):
    return ReadingProfile(
        artifact_id="t1", reader_id="qwen3.5:9b", reader_config={"temperature": 0.0},
        interface=interface, declared_context={}, candidate_family="test",
        baseline_family="echo",
        claim_boundary=ClaimBoundary(human_coherent_route_supported=True,
                                     process_correspondence="unavailable",
                                     provenance="not_inferred"))


def expect_raise(fn, exc, name):
    try:
        fn()
    except exc:
        print(f"  ok: {name}")
        return
    raise AssertionError(f"FAILED: {name} did not raise {exc.__name__}")


# 1. a clean I1 reading validates
r = base(Interface.I1_FINAL_ARTIFACT)
r.proximal = [RankedCandidate(label="goal A", rank=1, evidence_spans=["span"])]
r.to_dict()
print("  ok: clean I1 reading validates")

# 2. realization ground truth (a process fact) in an I1 reading must raise
r = base(Interface.I1_FINAL_ARTIFACT)
r.realization_ground_truth = [{"instruction": "x", "state": "realized"}]
expect_raise(r.validate, InterfaceLeak, "process labels leak into I1")

# 3. observed handling (needs deltas) in an I1 reading must raise; fine in I2
r = base(Interface.I1_FINAL_ARTIFACT)
r.anomaly_handling_observed = [{"state": "repaired"}]
expect_raise(r.validate, InterfaceLeak, "delta-observed handling leaks into I1")
r2 = base(Interface.I2_PAIRED_DELTA)
r2.anomaly_handling_observed = [{"state": "repaired"}]
r2.validate()
print("  ok: observed handling allowed in I2")

# 4. everything is allowed in I3
r3 = base(Interface.I3_PROCESS_AWARE)
r3.realization_ground_truth = [{"instruction": "x", "state": "realized"}]
r3.anomaly_handling_observed = [{"state": "concealed"}]
r3.validate()
print("  ok: I3 grants all sections")

# 5. provenance may never be 'inferred'
def bad_boundary():
    ClaimBoundary(human_coherent_route_supported=True,
                  process_correspondence="unavailable",
                  provenance="inferred_from_style").validate()
expect_raise(bad_boundary, ValueError, "inferred provenance refused")

# 6. historical traces demand the lifetime-history disclaimer
r = base(Interface.I1_FINAL_ARTIFACT)
r.historical = {"habit_evidence": ["x"]}
expect_raise(r.validate, ValueError, "missing lifetime-history disclaimer refused")
r.historical["lifetime_history_not_identified"] = True
r.validate()
print("  ok: disclaimer satisfies the historical guard")

print("ALL SCHEMA TESTS PASS")
